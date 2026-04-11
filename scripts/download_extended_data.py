"""
Phase 3.2 — Download Extended Price Data (2000-2025) via yfinance 1.2.0

Uses yf.Ticker.history() API (flat columns: Open, High, Low, Close, Volume).
Downloads current S&P 500 first (all should succeed), then historical-only
tickers (many will fail — they're delisted). Failures are documented.

Requires yfinance >= 1.0. Run: .venv/bin/pip install --upgrade yfinance

Usage:
    .venv/bin/python scripts/download_extended_data.py
"""

import json
import time
import warnings
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import yfinance as yf

warnings.filterwarnings('ignore')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONSTITUENTS_DIR = PROJECT_ROOT / 'data_raw' / 'sp500_constituents'
OUTPUT_DIR = PROJECT_ROOT / 'data_raw' / 'extended_prices'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

START_DATE  = '2000-01-01'
END_DATE    = '2024-12-31'
MAX_WORKERS = 4    # conservative to avoid Yahoo Finance rate limiting
MIN_ROWS    = 50   # discard tickers with almost no data


def load_ticker_lists() -> tuple:
    current_csv = CONSTITUENTS_DIR / 'sp500_current.csv'
    current_df  = pd.read_csv(current_csv)
    tcol = [c for c in current_df.columns if c.lower() in ('ticker', 'symbol')][0]
    current_tickers = current_df[tcol].str.strip().tolist()

    all_txt = CONSTITUENTS_DIR / 'sp500_all_unique.txt'
    with open(all_txt) as f:
        all_tickers = [l.strip() for l in f if l.strip()]

    historical_only = [t for t in all_tickers if t not in set(current_tickers)]
    return current_tickers, historical_only


def download_ticker(ticker: str) -> tuple:
    """
    Download one ticker via Ticker.history(). Returns (ticker, df_or_None, status).
    """
    try:
        obj = yf.Ticker(ticker)
        df  = obj.history(start=START_DATE, end=END_DATE, auto_adjust=True)
        if df is None or len(df) < MIN_ROWS:
            return ticker, None, 'insufficient_data'
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df.index.name = 'date'
        df.columns    = [c.lower() for c in df.columns]
        keep = [c for c in ('open', 'high', 'low', 'close', 'volume') if c in df.columns]
        return ticker, df[keep].copy(), 'success'
    except Exception as e:
        return ticker, None, f'error:{type(e).__name__}'


def check_existing() -> set:
    return {f.stem.replace('prices_', '') for f in OUTPUT_DIR.glob('prices_*.parquet')}


def download_group(label: str, tickers: list, existing: set) -> dict:
    to_do = [t for t in tickers if t not in existing]
    manifest = {}
    if not to_do:
        print(f"  [{label}] All {len(tickers)} already downloaded.")
        return manifest

    print(f"\n  [{label}] {len(to_do)} to download "
          f"({len(tickers)-len(to_do)} cached)  [{MAX_WORKERS} workers]")

    ok = fail = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futs = {pool.submit(download_ticker, t): t for t in to_do}
        for i, fut in enumerate(as_completed(futs), 1):
            ticker, df, status = fut.result()
            if df is not None:
                (OUTPUT_DIR / f'prices_{ticker}.parquet').parent.mkdir(exist_ok=True)
                df.to_parquet(OUTPUT_DIR / f'prices_{ticker}.parquet')
                manifest[ticker] = {
                    'status': 'success',
                    'n_rows': len(df),
                    'start':  str(df.index[0].date()),
                    'end':    str(df.index[-1].date()),
                }
                existing.add(ticker)
                ok += 1
            else:
                manifest[ticker] = {'status': status}
                fail += 1

            if i % 25 == 0 or i == len(to_do):
                print(f"    {i:4d}/{len(to_do)} [{i/len(to_do)*100:4.0f}%]  "
                      f"ok={ok}  fail={fail}")

    print(f"  [{label}] succeeded={ok}  failed={fail}")
    return manifest


def build_combined_parquet() -> None:
    print("\n" + "=" * 65)
    print("BUILDING COMBINED PARQUET")
    print("=" * 65)
    files = sorted(OUTPUT_DIR.glob('prices_*.parquet'))
    print(f"  {len(files)} ticker files found...")

    dfs = []
    for f in files:
        ticker = f.stem.replace('prices_', '')
        try:
            df = pd.read_parquet(f)
            if len(df) < MIN_ROWS:
                continue
            df.index = pd.to_datetime(df.index).tz_localize(None)
            df['symbol'] = ticker
            dfs.append(df.reset_index())
        except Exception:
            pass

    if not dfs:
        print("  ERROR: No data to combine!")
        return

    combined = pd.concat(dfs, ignore_index=True)
    combined['date'] = pd.to_datetime(combined['date'])
    combined = combined.sort_values(['date', 'symbol']).reset_index(drop=True)

    out = PROJECT_ROOT / 'data_processed' / 'extended_prices.parquet'
    combined.to_parquet(out, index=False)
    print(f"  Rows:    {len(combined):,}")
    print(f"  Symbols: {combined['symbol'].nunique()}")
    print(f"  Dates:   {combined['date'].min().date()} → {combined['date'].max().date()}")
    print(f"  Saved:   {out}")


def main():
    print("=" * 65)
    print("PHASE 3.2 — DOWNLOAD EXTENDED PRICE DATA (2000-2025)")
    print("=" * 65)
    print(f"  yfinance version: {yf.__version__}")
    print(f"  Date range:  {START_DATE} → {END_DATE}")
    print(f"  Workers:     {MAX_WORKERS}")

    current, historical_only = load_ticker_lists()
    print(f"\n  Current S&P 500:  {len(current)}")
    print(f"  Historical-only:  {len(historical_only)}")
    print(f"  Total:            {len(current) + len(historical_only)}")

    existing  = check_existing()
    if existing:
        print(f"  Already cached:   {len(existing)}")

    t0       = time.time()
    manifest = {}

    # Group A: current S&P 500 — all should succeed
    manifest.update(download_group('Current S&P 500', current, existing))

    # Group B: historical-only — many are delisted, will fail
    manifest.update(download_group('Historical (delisted)', historical_only, existing))

    elapsed = (time.time() - t0) / 60

    # ── Save manifest ─────────────────────────────────────────────────────────
    ok_tickers   = [t for t, v in manifest.items() if v['status'] == 'success']
    fail_tickers = [t for t, v in manifest.items() if v['status'] != 'success']

    with open(OUTPUT_DIR / 'download_manifest.json', 'w') as f:
        json.dump({'n_success': len(ok_tickers), 'n_failed': len(fail_tickers),
                   'failed': fail_tickers, 'details': manifest}, f, indent=2)
    if fail_tickers:
        (OUTPUT_DIR / 'failed_tickers.txt').write_text('\n'.join(fail_tickers))

    print(f"\n{'=' * 65}")
    print(f"DOWNLOAD COMPLETE  ({elapsed:.1f} min)")
    print(f"{'=' * 65}")
    print(f"  Total succeeded: {len(ok_tickers) + len(existing):,}")
    print(f"  Failed/missing:  {len(fail_tickers)}")
    print(f"  Survivorship bias note: {len(fail_tickers)} tickers unavailable "
          f"(mostly delisted companies with no Yahoo Finance data)")

    build_combined_parquet()
    print("\n  NEXT: Run scripts/process_extended_data.py")


if __name__ == '__main__':
    main()
