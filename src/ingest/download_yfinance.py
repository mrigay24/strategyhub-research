"""
Download S&P 500 stock data from Yahoo Finance (2000-present)

Uses yfinance to download historical OHLCV data with adjusted close prices.
Much better than Kaggle data because:
- Includes adjusted close (accounts for dividends and splits)
- Covers 25+ years (2000-present) vs 4 years
- Up-to-date data
- Free and reliable
"""

import yfinance as yf
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import time
from loguru import logger
from tqdm import tqdm

from src.config import (
    YFINANCE_RAW_PATH,
    YFINANCE_TICKERS_PATH,
    YFINANCE_START_DATE,
    YFINANCE_END_DATE,
    YFINANCE_CHUNK_SIZE,
    YFINANCE_RETRY_ATTEMPTS,
    YFINANCE_RETRY_DELAY
)


def get_sp500_tickers() -> List[str]:
    """
    Get current S&P 500 tickers

    First tries to load from local file, then falls back to Wikipedia if needed.

    Returns:
        List of ticker symbols
    """
    # Try loading from local file first
    if YFINANCE_TICKERS_PATH.exists():
        logger.info(f"Loading S&P 500 tickers from {YFINANCE_TICKERS_PATH}")
        with open(YFINANCE_TICKERS_PATH, 'r') as f:
            tickers = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(tickers)} tickers from file")
        return tickers

    # Fallback: Try fetching from Wikipedia
    logger.info("Fetching S&P 500 tickers from Wikipedia")
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'

    try:
        # Read the first table on the page (S&P 500 constituents)
        tables = pd.read_html(url)
        sp500_table = tables[0]

        tickers = sp500_table['Symbol'].tolist()

        # Clean ticker symbols (replace . with - for yfinance)
        tickers = [ticker.replace('.', '-') for ticker in tickers]

        logger.info(f"Found {len(tickers)} S&P 500 tickers from Wikipedia")

        # Save to file for future use
        YFINANCE_TICKERS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(YFINANCE_TICKERS_PATH, 'w') as f:
            f.write('\n'.join(tickers))
        logger.info(f"Saved tickers to {YFINANCE_TICKERS_PATH}")

        return tickers

    except Exception as e:
        logger.error(f"Failed to fetch S&P 500 tickers from Wikipedia: {e}")
        logger.error("Please create a ticker list file at: " + str(YFINANCE_TICKERS_PATH))
        raise


def download_ticker_data(
    ticker: str,
    start_date: str,
    end_date: Optional[str] = None,
    retry_attempts: int = YFINANCE_RETRY_ATTEMPTS
) -> Optional[pd.DataFrame]:
    """
    Download historical data for a single ticker

    Args:
        ticker: Stock ticker symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD), None for today
        retry_attempts: Number of retry attempts on failure

    Returns:
        DataFrame with OHLCV + Adj Close data, or None if failed
    """
    for attempt in range(retry_attempts):
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(
                start=start_date,
                end=end_date,
                auto_adjust=False,  # Keep both Close and Adj Close
                actions=True  # Include dividends and splits
            )

            if df.empty:
                logger.warning(f"{ticker}: No data available")
                return None

            # Reset index to get date as column
            df = df.reset_index()

            # Rename columns to match our schema
            df = df.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume',
                'Adj Close': 'adj_close',
                'Dividends': 'dividends',
                'Stock Splits': 'stock_splits'
            })

            # Add ticker symbol
            df['symbol'] = ticker

            # Select and reorder columns
            columns = ['symbol', 'date', 'open', 'high', 'low', 'close', 'adj_close', 'volume', 'dividends', 'stock_splits']
            df = df[columns]

            # Convert date to datetime
            df['date'] = pd.to_datetime(df['date'])

            return df

        except Exception as e:
            if attempt < retry_attempts - 1:
                logger.warning(f"{ticker}: Attempt {attempt + 1} failed ({e}), retrying...")
                time.sleep(YFINANCE_RETRY_DELAY)
            else:
                logger.error(f"{ticker}: Failed after {retry_attempts} attempts: {e}")
                return None

    return None


def download_sp500_data(
    tickers: Optional[List[str]] = None,
    start_date: str = YFINANCE_START_DATE,
    end_date: Optional[str] = YFINANCE_END_DATE,
    chunk_size: int = YFINANCE_CHUNK_SIZE
) -> pd.DataFrame:
    """
    Download historical data for all S&P 500 stocks

    Args:
        tickers: List of tickers (if None, fetches current S&P 500)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD), None for today
        chunk_size: Number of tickers to download at once

    Returns:
        DataFrame with all ticker data combined
    """
    logger.info("=" * 60)
    logger.info("DOWNLOADING S&P 500 DATA FROM YFINANCE")
    logger.info("=" * 60)
    logger.info(f"Date range: {start_date} to {end_date or 'present'}")

    # Get tickers if not provided
    if tickers is None:
        tickers = get_sp500_tickers()

    logger.info(f"Downloading data for {len(tickers)} tickers")
    logger.info(f"Chunk size: {chunk_size} tickers at a time")

    all_data = []
    failed_tickers = []

    # Download in chunks to avoid rate limits
    for i in tqdm(range(0, len(tickers), chunk_size), desc="Downloading chunks"):
        chunk = tickers[i:i + chunk_size]

        logger.info(f"Processing chunk {i//chunk_size + 1}/{(len(tickers)-1)//chunk_size + 1}: {len(chunk)} tickers")

        for ticker in chunk:
            df = download_ticker_data(ticker, start_date, end_date)

            if df is not None and not df.empty:
                all_data.append(df)
            else:
                failed_tickers.append(ticker)

        # Small delay between chunks to be respectful to yfinance
        if i + chunk_size < len(tickers):
            time.sleep(1)

    # Combine all data
    if not all_data:
        raise ValueError("No data was successfully downloaded!")

    combined_df = pd.concat(all_data, ignore_index=True)

    # Sort by symbol and date
    combined_df = combined_df.sort_values(['symbol', 'date']).reset_index(drop=True)

    logger.info("=" * 60)
    logger.info("DOWNLOAD COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total rows: {len(combined_df):,}")
    logger.info(f"Successful tickers: {len(all_data)}/{len(tickers)}")
    logger.info(f"Failed tickers: {len(failed_tickers)}")
    if failed_tickers:
        logger.warning(f"Failed: {', '.join(failed_tickers[:10])}" + (" ..." if len(failed_tickers) > 10 else ""))
    logger.info(f"Date range: {combined_df['date'].min()} to {combined_df['date'].max()}")
    logger.info(f"Symbols: {combined_df['symbol'].nunique()}")
    logger.info("=" * 60)

    return combined_df


def save_to_parquet(df: pd.DataFrame, path: Path) -> None:
    """Save DataFrame to parquet with compression"""
    logger.info(f"Saving data to {path}")

    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Save to parquet
    df.to_parquet(path, index=False, compression='snappy')

    file_size_mb = path.stat().st_size / (1024 * 1024)
    logger.info(f"Saved {len(df):,} rows ({file_size_mb:.2f} MB)")


def main():
    """Main function to download and save S&P 500 data"""

    # Configure logging
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}\n",
        level="INFO"
    )

    # Download data
    df = download_sp500_data()

    # Save to parquet
    save_to_parquet(df, YFINANCE_RAW_PATH)

    # Print summary statistics
    logger.info("\nDATA SUMMARY:")
    logger.info(f"  File: {YFINANCE_RAW_PATH}")
    logger.info(f"  Rows: {len(df):,}")
    logger.info(f"  Symbols: {df['symbol'].nunique()}")
    logger.info(f"  Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    logger.info(f"  Years: {(df['date'].max() - df['date'].min()).days / 365.25:.1f}")
    logger.info(f"  Columns: {df.columns.tolist()}")
    logger.info(f"\nPRICE STATISTICS:")
    logger.info(f"  Min close: ${df['close'].min():.2f}")
    logger.info(f"  Max close: ${df['close'].max():.2f}")
    logger.info(f"  Mean close: ${df['close'].mean():.2f}")
    logger.info(f"\nVOLUME STATISTICS:")
    logger.info(f"  Min volume: {df['volume'].min():,.0f}")
    logger.info(f"  Max volume: {df['volume'].max():,.0f}")
    logger.info(f"  Mean volume: {df['volume'].mean():,.0f}")
    logger.info(f"\nCORPORATE ACTIONS:")
    logger.info(f"  Dividends paid: {(df['dividends'] > 0).sum():,} instances")
    logger.info(f"  Stock splits: {(df['stock_splits'] != 0).sum():,} instances")

    logger.info("\n" + "=" * 60)
    logger.info("DOWNLOAD COMPLETE - Ready for cleaning pipeline")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
