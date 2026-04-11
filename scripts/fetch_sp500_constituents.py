"""
Phase 3.1 — Historical S&P 500 Constituent Lists (Point-in-Time)

WHY THIS MATTERS:
  Our Phase 2 backtest used the *current* S&P 500 stock list applied to 2014-2017 data.
  This creates survivorship bias: every stock we tested "survived" to be in the current S&P 500.
  Stocks that went bankrupt, were delisted, or were removed from the index don't appear in our data.
  This biases returns upward — bankrupt companies had bad returns we never counted.

WHAT WE BUILD HERE:
  A point-in-time constituent database: for each date, which stocks were actually
  in the S&P 500 at that time? Built from two sources:
    1. Wikipedia "List of S&P 500 companies" — current composition
    2. Wikipedia "List of S&P 500 companies" changes table — all additions/removals since ~2000
    3. A pre-compiled GitHub dataset as backup/validation

OUTPUT:
  data_raw/sp500_constituents/
    sp500_changes.csv         — all additions/removals with dates
    sp500_pit_monthly.csv     — point-in-time monthly constituent list (date, [tickers])
    sp500_all_unique.txt      — all unique tickers that ever appeared in S&P 500 since 2000

Usage:
    .venv/bin/python scripts/fetch_sp500_constituents.py
"""

import sys
import json
import time
import warnings
from pathlib import Path
from io import StringIO

import requests
import pandas as pd

warnings.filterwarnings('ignore')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / 'data_raw' / 'sp500_constituents'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}


# ── Step 1: Fetch current S&P 500 composition from Wikipedia ──────────────────

def fetch_current_sp500() -> pd.DataFrame:
    """Fetch current S&P 500 components from Wikipedia."""
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    print("Fetching current S&P 500 composition from Wikipedia...")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    tables = pd.read_html(StringIO(resp.text))
    # First table is the current components
    current = tables[0]
    print(f"  Current S&P 500: {len(current)} stocks")
    print(f"  Columns: {list(current.columns)}")

    # Standardize
    ticker_col = [c for c in current.columns if 'tick' in c.lower() or 'symbol' in c.lower()][0]
    name_col   = [c for c in current.columns if 'name' in c.lower() or 'security' in c.lower()][0]
    sector_col = [c for c in current.columns if 'sector' in c.lower()][0] if any('sector' in c.lower() for c in current.columns) else None

    result = pd.DataFrame({
        'ticker': current[ticker_col].str.strip().str.replace('.', '-', regex=False),
        'name': current[name_col].str.strip(),
    })
    if sector_col:
        result['sector'] = current[sector_col].str.strip()

    return result


# ── Step 2: Fetch historical changes from Wikipedia ───────────────────────────

def fetch_sp500_changes() -> pd.DataFrame:
    """
    Fetch S&P 500 historical changes (additions/removals) from Wikipedia.
    The changes table contains: Date Added, Ticker Added, Ticker Removed, Reason.
    """
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    print("\nFetching S&P 500 historical changes from Wikipedia...")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    tables = pd.read_html(StringIO(resp.text))
    # Second table is the historical changes
    if len(tables) < 2:
        raise ValueError("Could not find changes table on Wikipedia")

    changes = tables[1]
    print(f"  Changes table shape: {changes.shape}")
    print(f"  Columns: {list(changes.columns)}")
    print(f"  Sample rows:\n{changes.head(3)}")

    return changes


def parse_changes(changes: pd.DataFrame) -> pd.DataFrame:
    """
    Parse the Wikipedia changes table into a clean format:
    date | action (added/removed) | ticker | name
    """
    # Flatten multi-level columns if needed
    if isinstance(changes.columns, pd.MultiIndex):
        changes.columns = [' '.join(str(c) for c in col).strip() for col in changes.columns]

    print(f"\n  Parsing changes table (cols: {list(changes.columns)})...")

    rows = []
    for _, row in changes.iterrows():
        # Try to extract date — usually first column
        date_val = str(row.iloc[0]).strip()
        if not date_val or date_val.lower() in ('nan', 'date', ''):
            continue

        # Parse date
        try:
            date = pd.to_datetime(date_val)
        except Exception:
            continue

        # Extract added ticker — varies by column name
        added_ticker = None
        removed_ticker = None

        for col in changes.columns:
            col_lower = col.lower()
            val = str(row[col]).strip()
            if val.lower() in ('nan', '', '-', '—'):
                val = None

            # Must match BOTH the action (added/removed) AND be the Ticker column
            # This prevents picking up company names from the 'Security' column
            is_ticker_col = 'ticker' in col_lower or 'symbol' in col_lower
            if val and is_ticker_col and ('added' in col_lower or 'add' in col_lower):
                if val not in ('Date', 'Added', 'Ticker', 'Symbol'):
                    added_ticker = val.replace('.', '-').split()[0]
            elif val and is_ticker_col and ('removed' in col_lower or 'remov' in col_lower):
                if val not in ('Date', 'Removed', 'Ticker', 'Symbol'):
                    removed_ticker = val.replace('.', '-').split()[0]

        if added_ticker:
            rows.append({'date': date, 'action': 'added', 'ticker': added_ticker})
        if removed_ticker:
            rows.append({'date': date, 'action': 'removed', 'ticker': removed_ticker})

    df = pd.DataFrame(rows).sort_values('date').reset_index(drop=True)
    # Filter to 2000 onwards
    df = df[df['date'] >= '2000-01-01'].copy()
    print(f"  Parsed {len(df)} change events from 2000 onwards")
    print(f"  Date range: {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"  Additions: {(df['action']=='added').sum()}  |  Removals: {(df['action']=='removed').sum()}")
    return df


# ── Step 3: Build point-in-time monthly constituent lists ─────────────────────

def build_point_in_time(current_tickers: list, changes: pd.DataFrame,
                        start_date: str = '2000-01-01',
                        end_date: str = '2024-12-31') -> pd.DataFrame:
    """
    Reconstruct the S&P 500 composition at each month-end from 2000 to 2024.

    Method: start from current composition and walk BACKWARDS through the
    changes table, reversing each change. At each step we know the composition
    at that point in time.

    Returns:
        DataFrame with columns: date, tickers (comma-separated)
    """
    print("\nBuilding point-in-time monthly constituent lists...")

    # Generate month-end dates from start to end
    dates = pd.date_range(start=start_date, end=end_date, freq='M')

    # Start from current composition
    current_set = set(current_tickers)

    # Sort changes in reverse chronological order for backward reconstruction
    changes_rev = changes.sort_values('date', ascending=False).reset_index(drop=True)

    # Process each month-end date (going backwards in time)
    records = []
    change_idx = 0

    for dt in reversed(dates):
        # Apply changes that happened AFTER this date (reversing them)
        while change_idx < len(changes_rev):
            chg = changes_rev.iloc[change_idx]
            if chg['date'] > dt:
                # This change happened after our target date — reverse it
                if chg['action'] == 'added':
                    current_set.discard(chg['ticker'])
                elif chg['action'] == 'removed':
                    current_set.add(chg['ticker'])
                change_idx += 1
            else:
                break

        records.append({
            'date': dt.strftime('%Y-%m-%d'),
            'n_stocks': len(current_set),
            'tickers': ','.join(sorted(current_set)),
        })

    pit_df = pd.DataFrame(sorted(records, key=lambda x: x['date']))
    print(f"  Built {len(pit_df)} monthly snapshots from {pit_df['date'].iloc[0]} to {pit_df['date'].iloc[-1]}")
    print(f"  Avg stocks per month: {pit_df['n_stocks'].mean():.0f}")
    print(f"  Min: {pit_df['n_stocks'].min()}  Max: {pit_df['n_stocks'].max()}")
    return pit_df


def get_all_unique_tickers(pit_df: pd.DataFrame) -> list:
    """Get all unique tickers that ever appeared in the S&P 500."""
    all_tickers = set()
    for _, row in pit_df.iterrows():
        all_tickers.update(row['tickers'].split(','))
    tickers = sorted(all_tickers)
    print(f"\n  Total unique tickers (2000-2024): {len(tickers)}")
    return tickers


# ── Step 4: Validate against known composition ────────────────────────────────

def validate_against_phase2(pit_df: pd.DataFrame, phase2_dir: Path) -> None:
    """
    Compare our point-in-time list with the Phase 2 Kaggle data (2014-2017).
    The Kaggle dataset had 505 tickers. Our 2014-2017 PIT list should be similar.
    """
    print("\nValidating against Phase 2 data...")

    # Get Phase 2 tickers from parquet
    parquet_path = PROJECT_ROOT / 'data_processed' / 'prices_clean.parquet'
    if parquet_path.exists():
        phase2_data = pd.read_parquet(parquet_path)
        phase2_tickers = set(phase2_data['symbol'].unique())
        print(f"  Phase 2 (Kaggle) tickers: {len(phase2_tickers)}")

        # Get PIT tickers for 2016 (middle of Phase 2 period)
        pit_2016 = pit_df[pit_df['date'].str.startswith('2016')]
        if len(pit_2016) > 0:
            pit_2016_tickers = set(pit_2016.iloc[6]['tickers'].split(','))
            print(f"  PIT tickers (mid-2016):   {len(pit_2016_tickers)}")
            overlap = phase2_tickers & pit_2016_tickers
            print(f"  Overlap:                  {len(overlap)} ({100*len(overlap)/max(len(phase2_tickers),1):.1f}% of Phase 2)")
            only_phase2 = phase2_tickers - pit_2016_tickers
            only_pit    = pit_2016_tickers - phase2_tickers
            print(f"  In Phase 2 but not PIT:   {len(only_phase2)} (survivorship bias tickers)")
            print(f"  In PIT but not Phase 2:   {len(only_pit)} (replaced/historical)")
            if only_phase2 and len(only_phase2) < 30:
                print(f"  Phase2-only: {sorted(only_phase2)[:20]}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("PHASE 3.1 — HISTORICAL S&P 500 CONSTITUENT LISTS")
    print("=" * 65)

    # ── Fetch current composition ──────────────────────────────────────────────
    try:
        current_df = fetch_current_sp500()
        current_df.to_csv(OUTPUT_DIR / 'sp500_current.csv', index=False)
        print(f"  Saved sp500_current.csv ({len(current_df)} stocks)")
    except Exception as e:
        print(f"  ERROR fetching current composition: {e}")
        raise

    # ── Fetch changes ──────────────────────────────────────────────────────────
    time.sleep(1)
    try:
        changes_raw = fetch_sp500_changes()
        changes = parse_changes(changes_raw)
        changes.to_csv(OUTPUT_DIR / 'sp500_changes.csv', index=False)
        print(f"  Saved sp500_changes.csv ({len(changes)} events)")
    except Exception as e:
        print(f"  ERROR parsing changes: {e}")
        print(f"  Continuing with current composition only (reduced PIT accuracy)")
        changes = pd.DataFrame(columns=['date', 'action', 'ticker'])

    # ── Build point-in-time ────────────────────────────────────────────────────
    current_tickers = current_df['ticker'].tolist()
    pit_df = build_point_in_time(current_tickers, changes)
    pit_df.to_csv(OUTPUT_DIR / 'sp500_pit_monthly.csv', index=False)
    print(f"  Saved sp500_pit_monthly.csv ({len(pit_df)} monthly snapshots)")

    # ── Get all unique tickers ─────────────────────────────────────────────────
    all_tickers = get_all_unique_tickers(pit_df)
    with open(OUTPUT_DIR / 'sp500_all_unique.txt', 'w') as f:
        f.write('\n'.join(all_tickers))
    print(f"  Saved sp500_all_unique.txt ({len(all_tickers)} unique tickers)")

    # ── Validate ───────────────────────────────────────────────────────────────
    validate_against_phase2(pit_df, PROJECT_ROOT)

    # ── Summary ────────────────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("CONSTITUENT FETCH COMPLETE")
    print("=" * 65)
    print(f"  Current S&P 500 tickers:    {len(current_tickers)}")
    print(f"  Change events (2000-2024):  {len(changes)}")
    print(f"  Monthly PIT snapshots:      {len(pit_df)}")
    print(f"  All unique tickers:         {len(all_tickers)}")
    print(f"\n  Outputs saved to: {OUTPUT_DIR}")
    print("\n  NEXT STEP: Run scripts/download_extended_data.py to fetch prices")


if __name__ == '__main__':
    main()
