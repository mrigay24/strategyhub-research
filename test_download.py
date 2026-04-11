import sys
sys.path.insert(0, '.')

from src.ingest.download_yfinance import download_sp500_data, save_to_parquet
from src.config import YFINANCE_RAW_PATH
from loguru import logger

# Configure logging
logger.remove()
logger.add(
    lambda msg: print(msg, end=""),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}\n",
    level="INFO"
)

# Test with just 10 tickers
test_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'JPM', 'V', 'WMT']

logger.info("Testing download with 10 tickers...")
df = download_sp500_data(tickers=test_tickers, start_date='2000-01-01', chunk_size=5)

# Save sample
test_path = YFINANCE_RAW_PATH.parent / "sp500_sample_10stocks.parquet"
save_to_parquet(df, test_path)

logger.info(f"\nTest complete! Downloaded {len(df):,} rows for {df['symbol'].nunique()} stocks")
logger.info(f"Saved to: {test_path}")
