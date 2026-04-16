"""
NSE 500 Data Download
=====================
Downloads historical price data for NIFTY 500 stocks from Yahoo Finance
and saves to data_processed/nse_prices_clean.parquet

Run:
    .venv/bin/python scripts/download_nse_data.py

Takes ~15-20 minutes for full 500 stock universe.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import yfinance as yf
import urllib.request

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

OUTPUT_PATH  = Path("data_processed/nse_prices_clean.parquet")
START_DATE   = "2005-01-01"
END_DATE     = datetime.now().strftime("%Y-%m-%d")
MIN_COVERAGE = 0.60    # drop symbols with >40% missing data
PRICE_FLOOR  = 1.0     # INR floor (pennystocks excluded)
MAX_DAILY_RET = 0.75   # 75% max single-day return (filter bad data)
BATCH_SIZE   = 50      # symbols per yfinance batch download


def get_nse500_symbols() -> list:
    """Fetch NIFTY 500 symbols from Wikipedia, add .NS suffix for yfinance."""
    log.info("Fetching NIFTY 500 symbols from Wikipedia...")
    req = urllib.request.Request(
        "https://en.wikipedia.org/wiki/NIFTY_500",
        headers={"User-Agent": "Mozilla/5.0 (compatible; StrategyHub/1.0)"},
    )
    with urllib.request.urlopen(req) as r:
        tables = pd.read_html(r.read().decode("utf-8"))

    t = tables[4]
    t.columns = t.iloc[0]
    t = t.iloc[1:].reset_index(drop=True)
    symbols_nse = t["Symbol"].dropna().str.strip().tolist()

    # yfinance needs .NS suffix for NSE stocks
    symbols_yf = [s + ".NS" for s in symbols_nse]
    log.info(f"Found {len(symbols_yf)} NIFTY 500 symbols")
    return symbols_yf


def download_batch(symbols: list, start: str, end: str) -> pd.DataFrame:
    """Download adjusted close prices for a batch of symbols."""
    raw = yf.download(
        symbols,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        threads=True,
    )
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw.rename(columns={raw.columns[0]: symbols[0]})
    return prices.astype(float)


def clean_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Apply data quality filters:
    1. Price floor: drop rows where close < 1 INR
    2. Coverage filter: drop symbols with >40% missing data
    3. Return filter: mask single-day returns > 75% (bad data)
    """
    log.info(f"Raw price matrix: {prices.shape}")

    # 1. Price floor
    prices = prices.where(prices >= PRICE_FLOOR)

    # 2. Coverage filter
    min_rows = int(len(prices) * MIN_COVERAGE)
    prices = prices.dropna(axis=1, thresh=min_rows)
    log.info(f"After coverage filter: {prices.shape[1]} symbols")

    # 3. Two-pass return filter
    for _ in range(2):
        rets = prices.pct_change(fill_method=None).abs()
        mask = rets > MAX_DAILY_RET
        prices = prices.where(~mask)

    # 4. Drop rows where all values are NaN
    prices = prices.dropna(how="all")
    log.info(f"Clean price matrix: {prices.shape[0]} days × {prices.shape[1]} symbols")
    return prices


def to_long_format(prices: pd.DataFrame) -> pd.DataFrame:
    """Convert wide price DataFrame to long format matching strategy engine."""
    df = prices.reset_index().melt(id_vars="Date", var_name="symbol", value_name="close")
    df = df.rename(columns={"Date": "date"})
    df["symbol"] = df["symbol"].str.replace(".NS", "", regex=False)
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["close"])
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)

    # Add dummy OHLV columns (strategies only use close for signal generation)
    df["open"]   = df["close"]
    df["high"]   = df["close"]
    df["low"]    = df["close"]
    df["volume"] = 1_000_000  # placeholder — strategies use price-based signals

    return df[["date", "symbol", "open", "high", "low", "close", "volume"]]


def main():
    log.info("=" * 60)
    log.info("NSE 500 Data Download — StrategyHub")
    log.info(f"Period: {START_DATE} → {END_DATE}")
    log.info("=" * 60)

    symbols = get_nse500_symbols()

    # Download in batches to avoid yfinance rate limits
    all_prices = []
    total_batches = (len(symbols) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(symbols), BATCH_SIZE):
        batch = symbols[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        log.info(f"Downloading batch {batch_num}/{total_batches} ({len(batch)} symbols)...")
        try:
            prices_batch = download_batch(batch, START_DATE, END_DATE)
            all_prices.append(prices_batch)
        except Exception as e:
            log.warning(f"Batch {batch_num} failed: {e}")

    if not all_prices:
        log.error("No data downloaded.")
        sys.exit(1)

    # Merge all batches
    prices_wide = pd.concat(all_prices, axis=1)
    prices_wide = prices_wide.loc[:, ~prices_wide.columns.duplicated()]

    # Clean
    prices_clean = clean_prices(prices_wide)

    # Convert to long format
    log.info("Converting to long format...")
    df_long = to_long_format(prices_clean)

    # Save
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_long.to_parquet(OUTPUT_PATH, index=False)

    log.info(f"\n{'=' * 60}")
    log.info(f"Saved → {OUTPUT_PATH}")
    log.info(f"Symbols:    {df_long['symbol'].nunique()}")
    log.info(f"Date range: {df_long['date'].min().date()} → {df_long['date'].max().date()}")
    log.info(f"Rows:       {len(df_long):,}")
    log.info(f"{'=' * 60}")
    log.info("Next: .venv/bin/python scripts/run_nse_backtests.py")


if __name__ == "__main__":
    main()
