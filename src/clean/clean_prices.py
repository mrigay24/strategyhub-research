"""
Data cleaning module for stock price data

Handles both Kaggle and YFinance data sources.
Transforms raw data into clean parquet format with standardized schema.
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from loguru import logger

from src.config import (
    YFINANCE_RAW_PATH,
    SP500_KAGGLE_RAW_PATH,
    PROCESSED_DATA_PATH,
    METADATA_PATH,
    MIN_PRICE,
    MAX_MISSING_PCT,
    MAX_FILL_DAYS,
    SPLIT_DETECTION_THRESHOLD
)


def load_yfinance_data() -> pd.DataFrame:
    """Load YFinance parquet data (preferred source)"""
    logger.info(f"Loading YFinance data from {YFINANCE_RAW_PATH}")

    if not YFINANCE_RAW_PATH.exists():
        raise FileNotFoundError(f"YFinance data not found at {YFINANCE_RAW_PATH}")

    df = pd.read_parquet(YFINANCE_RAW_PATH)
    logger.info(f"Loaded {len(df):,} rows with columns: {df.columns.tolist()}")

    return df


def load_kaggle_data() -> pd.DataFrame:
    """Load Kaggle CSV data (fallback source)"""
    logger.info(f"Loading Kaggle data from {SP500_KAGGLE_RAW_PATH}")

    if not SP500_KAGGLE_RAW_PATH.exists():
        raise FileNotFoundError(f"Kaggle data not found at {SP500_KAGGLE_RAW_PATH}")

    df = pd.read_csv(SP500_KAGGLE_RAW_PATH)
    df['date'] = pd.to_datetime(df['date'])

    # Kaggle data doesn't have adj_close, create approximation
    df['adj_close'] = df['close']  # Approximation (no dividend/split adjustment)
    df['dividends'] = 0.0
    df['stock_splits'] = 0.0

    logger.info(f"Loaded {len(df):,} rows (Kaggle source - no true adj_close)")

    return df


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure standard column order and types
    """
    logger.info("Standardizing columns")

    # Required columns
    required_cols = ['symbol', 'date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']

    # Optional columns
    optional_cols = ['dividends', 'stock_splits']

    # Check required columns exist
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Add optional columns if missing
    for col in optional_cols:
        if col not in df.columns:
            df[col] = 0.0

    # Select and reorder columns
    final_cols = required_cols + [col for col in optional_cols if col in df.columns]
    df = df[final_cols].copy()

    # Ensure proper types
    df['date'] = pd.to_datetime(df['date'])
    df['symbol'] = df['symbol'].astype(str)

    # Sort by symbol and date
    df = df.sort_values(['symbol', 'date']).reset_index(drop=True)

    logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
    logger.info(f"Unique symbols: {df['symbol'].nunique()}")

    return df


def handle_missing_values(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Handle missing values in OHLCV data

    Strategy:
    1. Forward fill missing values up to MAX_FILL_DAYS
    2. Drop symbols with >MAX_MISSING_PCT missing data
    3. Drop any remaining rows with missing values
    """
    logger.info("Handling missing values")

    initial_rows = len(df)
    initial_symbols = df['symbol'].nunique()

    # Track missing data by symbol
    missing_stats = []

    for symbol in df['symbol'].unique():
        symbol_df = df[df['symbol'] == symbol]
        missing_count = symbol_df[['open', 'high', 'low', 'close', 'volume']].isnull().any(axis=1).sum()
        missing_pct = missing_count / len(symbol_df) if len(symbol_df) > 0 else 0

        if missing_pct > MAX_MISSING_PCT:
            logger.warning(f"Dropping {symbol}: {missing_pct:.2%} missing data")
            missing_stats.append({
                'symbol': symbol,
                'missing_pct': float(missing_pct),
                'action': 'dropped'
            })
            df = df[df['symbol'] != symbol]

    # Forward fill remaining missing values (grouped by symbol)
    df = df.groupby('symbol', group_keys=False).apply(
        lambda group: group.ffill(limit=MAX_FILL_DAYS)
    ).reset_index(drop=True)

    # Drop any rows still having missing values in price columns
    price_cols = ['open', 'high', 'low', 'close', 'adj_close', 'volume']
    rows_before = len(df)
    df = df.dropna(subset=price_cols)
    rows_dropped = rows_before - len(df)

    if rows_dropped > 0:
        logger.info(f"Dropped {rows_dropped} rows with remaining missing values")

    final_rows = len(df)
    final_symbols = df['symbol'].nunique()

    stats = {
        'initial_rows': int(initial_rows),
        'final_rows': int(final_rows),
        'rows_dropped': int(initial_rows - final_rows),
        'initial_symbols': int(initial_symbols),
        'final_symbols': int(final_symbols),
        'symbols_dropped': int(initial_symbols - final_symbols),
        'symbols_with_issues': missing_stats
    }

    logger.info(f"Missing value handling complete: {initial_rows:,} → {final_rows:,} rows")
    logger.info(f"Symbols: {initial_symbols} → {final_symbols}")

    return df, stats


def filter_penny_stocks(df: pd.DataFrame) -> pd.DataFrame:
    """Remove penny stocks (price < MIN_PRICE)"""
    logger.info(f"Filtering stocks with price < ${MIN_PRICE}")

    initial_rows = len(df)

    # Remove rows where close price is below threshold
    df = df[df['close'] >= MIN_PRICE].copy()

    rows_removed = initial_rows - len(df)
    pct_removed = rows_removed / initial_rows if initial_rows > 0 else 0
    logger.info(f"Removed {rows_removed:,} rows ({pct_removed:.2%}) with price < ${MIN_PRICE}")

    return df


def validate_data_quality(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Run data quality checks"""
    logger.info("Running data quality validation")

    issues = []

    # Check for duplicate rows
    duplicates = df.duplicated(subset=['symbol', 'date']).sum()
    if duplicates > 0:
        logger.warning(f"Found {duplicates} duplicate rows (symbol-date combinations)")
        issues.append(f"{duplicates} duplicate rows")
        df = df.drop_duplicates(subset=['symbol', 'date'], keep='first')

    # Check for price anomalies
    for col in ['open', 'high', 'low', 'close', 'adj_close']:
        negative_prices = (df[col] < 0).sum()
        if negative_prices > 0:
            logger.error(f"Found {negative_prices} negative {col} prices!")
            issues.append(f"{negative_prices} negative {col} prices")

    # Check for high < low violations
    violations = (df['high'] < df['low']).sum()
    if violations > 0:
        logger.warning(f"Found {violations} rows where high < low")
        issues.append(f"{violations} high < low violations")

    # Check for zero volume
    zero_volume = (df['volume'] == 0).sum()
    if zero_volume > 0:
        logger.warning(f"Found {zero_volume} rows with zero volume")
        issues.append(f"{zero_volume} zero volume rows")

    validation = {
        'total_checks': 4,
        'issues_found': len(issues),
        'issues': issues,
        'duplicates_removed': int(duplicates)
    }

    logger.info(f"Validation complete: {len(issues)} issues found")

    return df, validation


def create_metadata(df: pd.DataFrame, cleaning_stats: Dict[str, Any],
                   validation: Dict[str, Any], data_source: str) -> Dict[str, Any]:
    """Create metadata JSON for the cleaned dataset"""

    metadata = {
        'dataset_name': 'sp500_stock_prices',
        'source': data_source,
        'processing_date': pd.Timestamp.now().isoformat(),
        'data_info': {
            'total_rows': int(len(df)),
            'total_symbols': int(df['symbol'].nunique()),
            'date_range': {
                'start': df['date'].min().strftime('%Y-%m-%d'),
                'end': df['date'].max().strftime('%Y-%m-%d'),
                'trading_days': int(df['date'].nunique()),
                'years': round((df['date'].max() - df['date'].min()).days / 365.25, 1)
            },
            'columns': df.columns.tolist(),
            'schema': {
                col: str(dtype) for col, dtype in df.dtypes.items()
            }
        },
        'cleaning_stats': cleaning_stats,
        'validation': validation,
        'limitations': [
            'Survivorship bias (only includes stocks that are/were in S&P 500)',
            'May have data gaps for delisted or merged companies'
        ],
        'symbols': sorted(df['symbol'].unique().tolist()),
        'price_stats': {
            'min_close': float(df['close'].min()),
            'max_close': float(df['close'].max()),
            'mean_close': float(df['close'].mean()),
            'median_close': float(df['close'].median())
        },
        'adj_close_stats': {
            'min_adj_close': float(df['adj_close'].min()),
            'max_adj_close': float(df['adj_close'].max()),
            'mean_adj_close': float(df['adj_close'].mean())
        },
        'volume_stats': {
            'min_volume': int(df['volume'].min()),
            'max_volume': int(df['volume'].max()),
            'mean_volume': int(df['volume'].mean())
        }
    }

    # Add corporate actions stats if available
    if 'dividends' in df.columns:
        metadata['corporate_actions'] = {
            'dividend_payments': int((df['dividends'] > 0).sum()),
            'stock_splits': int((df['stock_splits'] != 0).sum())
        }

    return metadata


def clean_data(source: str = 'yfinance') -> None:
    """
    Main function to clean stock price data

    Args:
        source: 'yfinance' (preferred) or 'kaggle' (fallback)

    Pipeline:
    1. Load raw data
    2. Standardize columns
    3. Handle missing values
    4. Filter penny stocks
    5. Validate data quality
    6. Export to parquet
    7. Create metadata JSON
    """
    logger.info("=" * 60)
    logger.info(f"CLEANING {source.upper()} DATA")
    logger.info("=" * 60)

    # Step 1: Load data
    if source == 'yfinance':
        df = load_yfinance_data()
        data_source = f"YFinance (2000-present)"
    elif source == 'kaggle':
        df = load_kaggle_data()
        data_source = "Kaggle (2014-2017)"
    else:
        raise ValueError(f"Unknown source: {source}")

    # Step 2: Standardize columns
    df = standardize_columns(df)

    # Step 3: Handle missing values
    df, cleaning_stats = handle_missing_values(df)

    # Step 4: Filter penny stocks
    df = filter_penny_stocks(df)

    # Step 5: Validate data quality
    df, validation = validate_data_quality(df)

    # Step 6: Export to parquet
    logger.info(f"Exporting clean data to {PROCESSED_DATA_PATH}")
    PROCESSED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROCESSED_DATA_PATH, index=False, compression='snappy')
    file_size_mb = PROCESSED_DATA_PATH.stat().st_size / (1024 * 1024)
    logger.info(f"Exported {len(df):,} rows to parquet ({file_size_mb:.2f} MB)")

    # Step 7: Create metadata
    metadata = create_metadata(df, cleaning_stats, validation, data_source)

    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata saved to {METADATA_PATH}")

    # Print summary
    logger.info("=" * 60)
    logger.info("DATA CLEANING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Clean data:     {PROCESSED_DATA_PATH}")
    logger.info(f"Metadata:       {METADATA_PATH}")
    logger.info(f"Total rows:     {len(df):,}")
    logger.info(f"Total symbols:  {df['symbol'].nunique()}")
    logger.info(f"Date range:     {df['date'].min().date()} to {df['date'].max().date()}")
    logger.info(f"Years covered:  {metadata['data_info']['date_range']['years']}")
    logger.info(f"File size:      {file_size_mb:.2f} MB")
    logger.info("=" * 60)


if __name__ == "__main__":
    import sys

    # Configure logging
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}\n",
        level="INFO"
    )

    # Determine source (default to yfinance if available)
    source = sys.argv[1] if len(sys.argv) > 1 else 'yfinance'

    # If yfinance file doesn't exist, fall back to kaggle
    if source == 'yfinance' and not YFINANCE_RAW_PATH.exists():
        logger.warning(f"YFinance data not found at {YFINANCE_RAW_PATH}")
        logger.info("Falling back to Kaggle data")
        source = 'kaggle'

    clean_data(source=source)
