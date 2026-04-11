"""
Phase 3.3 — Process & Validate Extended Dataset

Takes the raw downloaded price files and produces a clean, validated
`extended_prices_clean.parquet` that strategies can use directly.

What we do:
  1. Load all per-ticker parquet files from data_raw/extended_prices/
  2. Validate coverage: flag tickers missing early history (pre-2003)
  3. Align to a shared trading-day calendar (NYSE trading days)
  4. Apply basic quality checks: remove outliers (>50% daily return)
  5. Build point-in-time universe lookup: for any date, which tickers
     were in the S&P 500 according to our constituent database?
  6. Save cleaned combined parquet + universe lookup CSV
  7. Print full coverage statistics

Usage:
    .venv/bin/python scripts/process_extended_data.py
"""

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

PROJECT_ROOT   = Path(__file__).resolve().parent.parent
RAW_DIR        = PROJECT_ROOT / 'data_raw' / 'extended_prices'
CONSTITUENTS   = PROJECT_ROOT / 'data_raw' / 'sp500_constituents'
PROCESSED_DIR  = PROJECT_ROOT / 'data_processed'
PROCESSED_DIR.mkdir(exist_ok=True)

MIN_ROWS          = 100       # min trading days to keep a ticker
OUTLIER_THRESHOLD = 0.20      # daily return > 20% treated as bad data point
MIN_PRICE         = 1.0       # close < $1 treated as bad data (delisted/corrupt)


# ── Step 1: Load raw files ─────────────────────────────────────────────────────

def load_raw_prices() -> pd.DataFrame:
    files = sorted(RAW_DIR.glob('prices_*.parquet'))
    print(f"  Loading {len(files)} raw parquet files...")

    dfs = []
    for f in files:
        ticker = f.stem.replace('prices_', '')
        try:
            df = pd.read_parquet(f)
            if len(df) < MIN_ROWS:
                continue
            df.index = pd.to_datetime(df.index).tz_localize(None)
            df.index.name = 'date'
            df.columns = [c.lower() for c in df.columns]

            # Standardise to close + volume only (all strategies use these)
            if 'close' not in df.columns:
                continue
            df['symbol'] = ticker
            dfs.append(df.reset_index()[['date', 'symbol', 'open', 'high', 'low',
                                          'close', 'volume']]
                       if all(c in df.columns for c in ('open','high','low','volume'))
                       else df.reset_index()[['date', 'symbol', 'close']])
        except Exception as e:
            print(f"    Skip {ticker}: {e}")

    combined = pd.concat(dfs, ignore_index=True)
    combined['date'] = pd.to_datetime(combined['date'])
    print(f"  Loaded: {len(combined):,} rows, {combined['symbol'].nunique()} symbols")
    return combined


# ── Step 2: Validate coverage ──────────────────────────────────────────────────

def coverage_report(df: pd.DataFrame) -> dict:
    """Per-ticker date coverage statistics."""
    stats = df.groupby('symbol')['date'].agg(['min', 'max', 'count']).reset_index()
    stats.columns = ['symbol', 'first_date', 'last_date', 'n_rows']
    stats['years_coverage'] = (stats['last_date'] - stats['first_date']).dt.days / 365.25

    tiers = {
        'full_history (2000-2024)': (stats['first_date'] <= '2001-01-01') & (stats['last_date'] >= '2023-01-01'),
        'post_2003 (2003-2024)':    (stats['first_date'] <= '2003-12-31') & (stats['last_date'] >= '2023-01-01'),
        'post_crisis (2009-2024)':  (stats['first_date'] <= '2009-12-31') & (stats['last_date'] >= '2023-01-01'),
        'recent_only (2014-2024)':  (stats['first_date'] <= '2014-12-31') & (stats['last_date'] >= '2023-01-01'),
    }

    print("\n  Coverage tiers:")
    for name, mask in tiers.items():
        n = mask.sum()
        print(f"    {name:<35} {n:4d} symbols")

    return {'stats': stats, 'tiers': tiers}


# ── Step 3: Quality filter ─────────────────────────────────────────────────────

def remove_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Two-pass quality filter:
      Pass 1 — price floor: drop rows where close < MIN_PRICE ($1).
               Eliminates corrupted near-zero prices that cause astronomical
               pct_change spikes in the next row (e.g. CBE: 0.001 → 34 = 33,999x).
      Pass 2 — return cap: drop rows where |daily return| > OUTLIER_THRESHOLD (20%).
    """
    df = df.sort_values(['symbol', 'date'])

    # Pass 1: price floor
    n_price = (df['close'] < MIN_PRICE).sum()
    if n_price:
        print(f"  Removed {n_price} rows with close < ${MIN_PRICE:.0f} (bad/delisted data)")
    df = df[df['close'] >= MIN_PRICE].copy()

    # Pass 2: return cap (iterate twice to catch newly-adjacent extremes after removals)
    for _ in range(2):
        ret = df.groupby('symbol')['close'].pct_change()
        bad = ret.abs() > OUTLIER_THRESHOLD
        n_bad = bad.sum()
        if n_bad:
            print(f"  Removed {n_bad} outlier rows (|daily return| > {OUTLIER_THRESHOLD*100:.0f}%)")
        df = df[~bad].copy()

    return df


# ── Step 4: Align to trading days ─────────────────────────────────────────────

def build_trading_calendar(df: pd.DataFrame) -> pd.DatetimeIndex:
    """Infer trading days from the data itself (dates where at least 200 symbols have prices)."""
    date_counts = df.groupby('date')['symbol'].count()
    trading_days = date_counts[date_counts >= 200].index
    return pd.DatetimeIndex(sorted(trading_days))


# ── Step 5: Point-in-time universe lookup ─────────────────────────────────────

def build_universe_lookup(price_symbols: set) -> pd.DataFrame:
    """
    Load the monthly PIT snapshots and create a lookup table:
      date | tickers_in_universe (comma-separated)
    Only includes tickers for which we actually have price data.
    """
    pit_path = CONSTITUENTS / 'sp500_pit_monthly.csv'
    if not pit_path.exists():
        print("  WARNING: PIT data not found — universe = all available tickers")
        return None

    pit = pd.read_csv(pit_path)
    pit['date'] = pd.to_datetime(pit['date'])

    # Filter to tickers we have price data for
    rows = []
    for _, row in pit.iterrows():
        all_tickers = set(row['tickers'].split(','))
        available   = all_tickers & price_symbols
        rows.append({
            'date':              row['date'],
            'n_pit_total':       len(all_tickers),
            'n_available':       len(available),
            'coverage_pct':      round(100 * len(available) / max(len(all_tickers), 1), 1),
            'tickers':           ','.join(sorted(available)),
        })

    lookup = pd.DataFrame(rows)
    avg_cov = lookup['coverage_pct'].mean()
    print(f"\n  Point-in-time universe coverage:")
    print(f"    Monthly snapshots:     {len(lookup)}")
    print(f"    Avg PIT symbols/month: {lookup['n_pit_total'].mean():.0f}")
    print(f"    Avg available/month:   {lookup['n_available'].mean():.0f}")
    print(f"    Avg coverage:          {avg_cov:.1f}%")
    print(f"    Residual survivorship: {100-avg_cov:.1f}% of constituents missing (delisted, no YF data)")

    return lookup


# ── Step 6: Save outputs ───────────────────────────────────────────────────────

def save_outputs(df: pd.DataFrame, lookup: pd.DataFrame, stats: pd.DataFrame) -> None:
    # Main clean parquet (same schema as prices_clean.parquet)
    clean_path = PROCESSED_DIR / 'extended_prices_clean.parquet'
    df.to_parquet(clean_path, index=False)
    print(f"\n  Saved: {clean_path}")
    print(f"    {len(df):,} rows, {df['symbol'].nunique()} symbols")
    print(f"    {df['date'].min().date()} → {df['date'].max().date()}")

    # Universe lookup
    if lookup is not None:
        lookup.to_csv(PROCESSED_DIR / 'sp500_universe_lookup.csv', index=False)
        print(f"  Saved: sp500_universe_lookup.csv")

    # Coverage stats
    stats.to_csv(PROCESSED_DIR / 'extended_coverage_stats.csv', index=False)
    print(f"  Saved: extended_coverage_stats.csv")

    # Summary JSON
    summary = {
        'total_rows':         len(df),
        'n_symbols':          df['symbol'].nunique(),
        'date_start':         str(df['date'].min().date()),
        'date_end':           str(df['date'].max().date()),
        'n_trading_days':     df['date'].nunique(),
        'symbols_pre2003':    int((stats['first_date'] <= '2001-01-01').sum()),
        'symbols_pre2009':    int((stats['first_date'] <= '2003-12-31').sum()),
        'symbols_full_range': int(((stats['first_date'] <= '2001-01-01') &
                                   (stats['last_date']  >= '2023-01-01')).sum()),
    }
    (PROCESSED_DIR / 'extended_data_summary.json').write_text(
        json.dumps(summary, indent=2)
    )
    print(f"  Saved: extended_data_summary.json")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("PHASE 3.3 — PROCESS & VALIDATE EXTENDED DATASET")
    print("=" * 65)

    # Load
    df = load_raw_prices()

    # Coverage report
    cov = coverage_report(df)
    stats = cov['stats']

    # Quality filter
    df = remove_outliers(df)

    # Trading calendar
    cal = build_trading_calendar(df)
    print(f"\n  Trading days detected: {len(cal)} ({cal[0].date()} → {cal[-1].date()})")

    # Universe lookup
    price_symbols = set(df['symbol'].unique())
    lookup = build_universe_lookup(price_symbols)

    # Save
    save_outputs(df, lookup, stats)

    # Final comparison vs Phase 2
    print("\n" + "=" * 65)
    print("PHASE 2 vs PHASE 3 DATA COMPARISON")
    print("=" * 65)
    phase2 = pd.read_parquet(PROJECT_ROOT / 'data_processed' / 'prices_clean.parquet')
    p2_symbols = phase2['symbol'].nunique() if 'symbol' in phase2.columns else phase2.columns.nunique()
    p3_symbols = df['symbol'].nunique()
    print(f"  Phase 2 (Kaggle 2014-2017):  {p2_symbols:4d} symbols, "
          f"{phase2['date'].nunique() if 'date' in phase2.columns else 1007} trading days")
    print(f"  Phase 3 (YFinance 2000-2024): {p3_symbols:4d} symbols, {df['date'].nunique()} trading days")
    print(f"  Data increase:  {df['date'].nunique() / 1007:.1f}× more trading days")
    print(f"  Symbol change:  {p3_symbols - p2_symbols:+d} symbols")

    phase2_sym = set(phase2['symbol'].unique() if 'symbol' in phase2.columns else [])
    overlap = phase2_sym & price_symbols
    print(f"\n  Overlap with Phase 2:   {len(overlap)} symbols")
    print(f"  In Phase 2, not Phase 3: {len(phase2_sym - price_symbols)} (missing — delisted)")
    print(f"  In Phase 3, not Phase 2: {len(price_symbols - phase2_sym)} (new additions)")

    print(f"\n  Phase 3.3 COMPLETE.")
    print(f"  NEXT: Run scripts/run_extended_backtests.py")


if __name__ == '__main__':
    main()
