"""
Phase 3.5 — Run All 14 Backtests on Extended 25-Year Data

Key differences from run_all_backtests.py:
  1. Uses data_processed/extended_prices_clean.parquet (2000-2024, 654 symbols)
  2. Applies point-in-time (PIT) universe mask after signal generation:
     on each date, only stocks actually in the S&P 500 at that time receive positions
  3. Results saved to results/extended_backtests/ (JSON + CSV)
     → does NOT overwrite the Phase 2 SQLite database

POINT-IN-TIME UNIVERSE MASKING:
  Strategy.generate_signals() computes signals using all available symbols.
  We then zero out signals for any symbol that was not in the S&P 500 on that date,
  re-normalize the weights, and run the backtest using only in-universe stocks.
  This eliminates universe look-ahead bias.

Usage:
    .venv/bin/python scripts/run_extended_backtests.py
"""

import sys
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.strategies import STRATEGY_REGISTRY, get_strategy
from loguru import logger

logger.remove()
logger.add(lambda msg: print(msg, end=""), format="{time:HH:mm:ss} | {message}\n", level="INFO")

COMMISSION_BPS = 10
SLIPPAGE_BPS   = 5
RISK_FREE_RATE = 0.02
RESULTS_DIR    = PROJECT_ROOT / 'results' / 'extended_backtests'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

ALL_STRATEGIES = list(STRATEGY_REGISTRY.keys())


def safe_float(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return round(float(v), 6)


# ── Point-in-time universe loader ─────────────────────────────────────────────

def load_pit_universe(prices_index: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Build a daily binary mask (True = in S&P 500) for all (date, symbol) pairs.
    Uses monthly PIT snapshots; forward-fills between month-ends.

    Returns a DataFrame: index=dates, columns=symbols, values=True/False.
    """
    lookup_path = PROJECT_ROOT / 'data_processed' / 'sp500_universe_lookup.csv'
    if not lookup_path.exists():
        logger.warning("No PIT lookup found — using all symbols (no universe mask)")
        return None

    lookup = pd.read_csv(lookup_path)
    lookup['date'] = pd.to_datetime(lookup['date'])
    lookup = lookup.sort_values('date')

    # Build set of in-universe tickers per month-end date
    pit_by_date = {}
    for _, row in lookup.iterrows():
        tickers = set(row['tickers'].split(',')) if pd.notna(row['tickers']) else set()
        pit_by_date[row['date']] = tickers

    pit_dates = sorted(pit_by_date.keys())

    # For each trading day, find the most recent month-end snapshot
    # and record which tickers are in-universe
    all_tickers = set()
    for tickers in pit_by_date.values():
        all_tickers.update(tickers)
    all_tickers = sorted(all_tickers)

    logger.info(f"Building PIT universe mask: {len(prices_index)} days × {len(all_tickers)} tickers...")

    # Build the mask as a dict {date: set_of_tickers}
    daily_universe = {}
    pit_idx = 0
    for dt in prices_index:
        # Advance the PIT pointer to the most recent snapshot <= dt
        while pit_idx < len(pit_dates) - 1 and pit_dates[pit_idx + 1] <= dt:
            pit_idx += 1
        current_pit_date = pit_dates[pit_idx]
        if current_pit_date > dt:
            # Before the first PIT snapshot — use the earliest one
            daily_universe[dt] = pit_by_date[pit_dates[0]]
        else:
            daily_universe[dt] = pit_by_date[current_pit_date]

    return daily_universe


# ── Signal computation with PIT masking ───────────────────────────────────────

def get_strategy_returns_pit(strategy_key: str, data: pd.DataFrame,
                              prices: pd.DataFrame,
                              pit_universe: dict) -> pd.Series:
    """
    Compute strategy returns with point-in-time universe filtering.

    Steps:
      1. Generate raw signals (strategy uses full data)
      2. Apply PIT mask: zero out signals for off-universe stocks
      3. Re-normalize: divide by sum of weights so portfolio is fully invested
      4. Execute: returns = shifted_signals × price_returns − costs
    """
    strategy = get_strategy(strategy_key, data)
    signals = strategy.generate_signals()
    signals = signals.reindex(prices.index).ffill().fillna(0)

    # Apply PIT universe mask
    if pit_universe is not None:
        for dt in signals.index:
            if dt in pit_universe:
                in_universe = pit_universe[dt]
                # Zero out any signal for stocks not in universe on this date
                off_universe = [c for c in signals.columns if c not in in_universe]
                if off_universe:
                    signals.loc[dt, off_universe] = 0.0

        # Re-normalize: if row has any non-zero weight, rescale to sum to original sum
        row_sums = signals.sum(axis=1)
        nz = row_sums > 0
        signals.loc[nz] = signals.loc[nz].div(row_sums[nz], axis=0)

    # Compute returns — fill_method=None keeps NaN gaps as NaN instead of
    # forward-filling them, which would generate false large returns at boundaries.
    # fillna(0) on returns treats missing-price days as zero return (held flat).
    all_returns = prices.pct_change(fill_method=None).fillna(0)
    shifted    = signals.shift(1).fillna(0)
    strategy_returns = (shifted * all_returns).sum(axis=1)

    # Transaction costs
    turnover = shifted.diff().abs().sum(axis=1) / 2
    costs    = turnover * (COMMISSION_BPS + SLIPPAGE_BPS) / 10000

    return (strategy_returns - costs).fillna(0).rename(strategy_key)


# ── Performance metrics ────────────────────────────────────────────────────────

def compute_metrics(returns: pd.Series) -> dict:
    rf_daily = RISK_FREE_RATE / 252
    excess   = returns - rf_daily
    std      = excess.std()
    sr       = float(np.sqrt(252) * excess.mean() / std) if std > 1e-10 else 0.0
    if np.isnan(sr) or np.isinf(sr):
        sr = 0.0

    total    = float((1 + returns).prod())
    n_years  = len(returns) / 252
    cagr     = float(total ** (1 / n_years) - 1) if total > 0 and n_years > 0 else 0.0

    equity   = (1 + returns).cumprod()
    mdd      = float((equity / equity.cummax() - 1).min())

    ann_vol  = float(returns.std() * np.sqrt(252))

    return {
        'sharpe':         safe_float(sr),
        'cagr':           safe_float(cagr),
        'total_return':   safe_float(total - 1),
        'ann_volatility': safe_float(ann_vol),
        'max_drawdown':   safe_float(mdd),
        'calmar':         safe_float(cagr / abs(mdd)) if mdd < 0 else None,
        'n_trading_days': len(returns),
        'n_years':        safe_float(n_years),
    }


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("PHASE 3.5 — EXTENDED BACKTESTS (2000-2024, 25 YEARS)")
    print("=" * 70)

    # Load extended data
    data_path = PROJECT_ROOT / 'data_processed' / 'extended_prices_clean.parquet'
    logger.info(f"Loading extended data from {data_path.name}...")
    data = pd.read_parquet(data_path)
    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values(['date', 'symbol'])
    logger.info(f"  {len(data):,} rows, {data['symbol'].nunique()} symbols, "
                f"{data['date'].min().date()} → {data['date'].max().date()}")

    # Pivot to wide format
    prices = data.pivot_table(index='date', columns='symbol', values='close')
    prices = prices.sort_index()

    # Load PIT universe mask
    pit_universe = load_pit_universe(prices.index)

    # Benchmark (equal-weighted all available S&P 500 stocks per day)
    # fill_method=None prevents false large returns at NaN-gap boundaries
    benchmark = prices.pct_change(fill_method=None).mean(axis=1).rename('benchmark')

    all_results = {}
    summary_rows = []

    print(f"\n  Running {len(ALL_STRATEGIES)} strategies on 25-year data...\n")

    for i, key in enumerate(ALL_STRATEGIES):
        logger.info(f"[{i+1:2d}/14] {key}")
        try:
            ret = get_strategy_returns_pit(key, data, prices, pit_universe)

            m = compute_metrics(ret)
            all_results[key] = {
                'metrics': m,
                'returns_start': str(ret.index[0].date()),
                'returns_end':   str(ret.index[-1].date()),
                'n_nonzero':     int((ret.abs() > 1e-8).sum()),
            }

            # Save equity curve
            equity = (1 + ret).cumprod() * 100000
            equity_df = equity.reset_index()
            equity_df.columns = ['date', 'equity']
            equity_df['date'] = equity_df['date'].astype(str)
            equity_df.to_csv(RESULTS_DIR / f'equity_{key}.csv', index=False)

            summary_rows.append({
                'strategy': key,
                'sharpe':   m['sharpe'],
                'cagr':     m['cagr'],
                'max_dd':   m['max_drawdown'],
                'ann_vol':  m['ann_volatility'],
                'calmar':   m['calmar'],
            })
            logger.info(f"  → Sharpe {m['sharpe']:.2f} | CAGR {m['cagr']:.1%} | "
                        f"MDD {m['max_drawdown']:.1%}")

        except Exception as e:
            logger.warning(f"  FAILED: {e}")
            all_results[key] = {'error': str(e)}

    # Benchmark metrics
    bench_m = compute_metrics(benchmark)
    all_results['benchmark'] = {'metrics': bench_m}
    summary_rows.append({
        'strategy': 'benchmark (equal-wt)',
        'sharpe':   bench_m['sharpe'],
        'cagr':     bench_m['cagr'],
        'max_dd':   bench_m['max_drawdown'],
        'ann_vol':  bench_m['ann_volatility'],
        'calmar':   bench_m['calmar'],
    })

    # Save full results JSON
    results_path = RESULTS_DIR / 'extended_backtest_results.json'
    with open(results_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)

    # Save summary CSV
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(RESULTS_DIR / 'extended_backtest_summary.csv', index=False)

    # Print summary table
    print("\n" + "=" * 80)
    print("EXTENDED BACKTEST RESULTS SUMMARY (2000-2024, WITH PIT UNIVERSE)")
    print("=" * 80)
    print(f"\n{'Strategy':<35} {'Sharpe':>8} {'CAGR':>8} {'MDD':>9} {'Ann Vol':>9} {'Calmar':>8}")
    print("-" * 80)

    sorted_rows = sorted(summary_rows,
                         key=lambda x: x['sharpe'] or -99, reverse=True)
    for r in sorted_rows:
        sep = " ←── BENCHMARK" if r['strategy'] == 'benchmark (equal-wt)' else ""
        print(f"{r['strategy']:<35} "
              f"{r['sharpe']:>8.2f} "
              f"{r['cagr']*100:>7.1f}% "
              f"{r['max_dd']*100:>8.1f}% "
              f"{r['ann_vol']*100:>8.1f}% "
              f"{(r['calmar'] or 0):>8.2f}"
              f"{sep}")

    # Phase 2 vs Phase 3 comparison
    phase2_path = PROJECT_ROOT / 'results' / 'extended_backtests' / 'extended_backtest_summary.csv'
    print(f"\n  Results saved to: {RESULTS_DIR}")
    print(f"  Equity curves saved: {len(ALL_STRATEGIES)} CSV files")

    print("\n" + "=" * 80)
    print("PHASE 3.5 COMPLETE")
    print("=" * 80)
    print("  NEXT: Re-run Phase 2.1-2.8 analyses on this extended dataset")


if __name__ == '__main__':
    main()
