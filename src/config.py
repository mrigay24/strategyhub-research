"""
Configuration settings for StrategyHub Research Platform
"""

from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent.parent
DATA_RAW_DIR = BASE_DIR / "data_raw"
DATA_PROCESSED_DIR = BASE_DIR / "data_processed"
DATABASE_DIR = BASE_DIR / "database"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
DATA_PROCESSED_DIR.mkdir(exist_ok=True)
DATABASE_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Data cleaning settings
MIN_PRICE = 1.0  # Filter out penny stocks below $1
MAX_MISSING_PCT = 0.10  # Max 10% missing data per symbol (relaxed for longer timeframes)
MAX_FILL_DAYS = 5  # Forward fill missing values up to 5 days
SPLIT_DETECTION_THRESHOLD = 0.5  # Detect splits if price changes >50% overnight

# Backtest default settings
DEFAULT_INITIAL_CAPITAL = 1_000_000
DEFAULT_COMMISSION = 0.001  # 10 basis points (0.1%)
DEFAULT_SLIPPAGE = 0.0005  # 5 basis points (0.05%)
DEFAULT_REBALANCE_FREQ = 'monthly'

# Risk-free rate for Sharpe ratio calculation
RISK_FREE_RATE = 0.02  # 2% annual

# Database settings
DATABASE_PATH = DATABASE_DIR / "strategyhub.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
API_RELOAD = os.getenv("API_RELOAD", "true").lower() == "true"

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
LOG_FILE = LOGS_DIR / "strategyhub.log"

# Data source paths
# Kaggle dataset (2014-2017)
SP500_KAGGLE_RAW_PATH = DATA_RAW_DIR / "sp500_stock_prices" / "SP 500 Stock Prices 2014-2017.csv"

# YFinance dataset (2000-present)
YFINANCE_RAW_DIR = DATA_RAW_DIR / "yfinance"
YFINANCE_RAW_DIR.mkdir(exist_ok=True, parents=True)
YFINANCE_RAW_PATH = YFINANCE_RAW_DIR / "sp500_2000_present.parquet"
YFINANCE_TICKERS_PATH = DATA_RAW_DIR / "yfinance" / "sp500_tickers.txt"

# Processed data paths
PROCESSED_DATA_PATH = DATA_PROCESSED_DIR / "prices_clean.parquet"
METADATA_PATH = DATA_PROCESSED_DIR / "metadata.json"
RETURNS_DATA_PATH = DATA_PROCESSED_DIR / "returns_daily.parquet"

# YFinance download settings
YFINANCE_START_DATE = "2000-01-01"
YFINANCE_END_DATE = None  # None = present day
YFINANCE_CHUNK_SIZE = 50  # Download N tickers at a time to avoid rate limits
YFINANCE_RETRY_ATTEMPTS = 3
YFINANCE_RETRY_DELAY = 5  # seconds

# Strategy parameters defaults
STRATEGY_DEFAULTS = {
    'sma_crossover': {
        'fast_period': 50,
        'slow_period': 200,
        'allow_short': False
    },
    'ema_crossover': {
        'fast_period': 12,
        'slow_period': 26,
        'allow_short': False
    },
    'tsmom': {
        'lookback_period': 252,
        'hold_period': 21,
        'allow_short': True
    },
    'cross_sectional_momentum': {
        'lookback_period': 252,
        'top_pct': 20,
        'bottom_pct': 20,
        'rebalance_freq': 'monthly'
    },
    'rsi': {
        'period': 14,
        'oversold_threshold': 30,
        'overbought_threshold': 70,
        'allow_short': False
    },
    'bollinger_bands': {
        'period': 20,
        'num_std': 2,
        'allow_short': False
    },
    'donchian': {
        'entry_window': 55,
        'exit_window': 20
    },
    'low_volatility': {
        'vol_lookback': 63,
        'num_long': 20,
        'rebalance_freq': 'monthly'
    }
}
