"""
Base Strategy Class

Abstract base class that all trading strategies must inherit from.
Enforces a consistent interface for signal generation and backtesting.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np


class StrategyType(Enum):
    """Types of trading strategies"""
    TREND_FOLLOWING = "trend_following"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    FACTOR = "factor"
    PORTFOLIO = "portfolio"
    VALUE = "value"
    QUALITY = "quality"
    COMPOSITE = "composite"
    RISK_MANAGEMENT = "risk_management"
    EVENT = "event"


class Strategy(ABC):
    """
    Abstract Base Class for Trading Strategies

    All strategies must implement:
    - generate_signals(): Returns target positions/weights
    - get_param_grid(): Returns parameter grid for optimization

    Attributes:
        data: Price data DataFrame (columns: symbol, date, open, high, low, close, volume)
        params: Strategy parameters dictionary
        name: Strategy name
        strategy_type: Type of strategy (trend, momentum, etc.)
    """

    # Default parameters (override in subclasses)
    DEFAULT_PARAMS: Dict[str, Any] = {}

    def __init__(self, data: pd.DataFrame, params: Optional[Dict[str, Any]] = None):
        """
        Initialize strategy

        Args:
            data: Price data DataFrame with columns:
                  [symbol, date, open, high, low, close, volume]
                  OR pivot format with date index and symbol columns
            params: Strategy parameters (uses defaults if None)
        """
        self.data = data.copy()
        self.params = {**self.DEFAULT_PARAMS, **(params or {})}
        self._validate_params()
        self._preprocess_data()

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name"""
        pass

    @property
    @abstractmethod
    def strategy_type(self) -> StrategyType:
        """Strategy type"""
        pass

    @abstractmethod
    def generate_signals(self) -> pd.DataFrame:
        """
        Generate trading signals/target weights

        Returns:
            DataFrame with:
            - Index: dates
            - Columns: symbols (for multi-asset) or single 'signal' column
            - Values: target weights/positions
              - 1 = fully long
              - 0 = neutral/flat
              - -1 = fully short
              - Fractional values allowed for position sizing

        IMPORTANT: Signals should be generated using data available at time t
                   to determine position for time t+1 (no look-ahead bias)
        """
        pass

    def get_param_grid(self) -> Dict[str, List[Any]]:
        """
        Get parameter grid for optimization

        Override this method to define parameter ranges for backtesting optimization.

        Returns:
            Dictionary mapping parameter names to lists of values to test

        Example:
            return {
                'fast': [10, 20, 50],
                'slow': [100, 150, 200]
            }
        """
        return {}

    def _validate_params(self) -> None:
        """
        Validate strategy parameters

        Override to add custom validation logic.
        Raises ValueError if parameters are invalid.
        """
        pass

    def _preprocess_data(self) -> None:
        """
        Preprocess data before signal generation

        Override to add custom preprocessing (e.g., pivot data, calculate returns).
        Called automatically during __init__.
        """
        # Ensure date is datetime
        if 'date' in self.data.columns:
            self.data['date'] = pd.to_datetime(self.data['date'])

        # Sort by symbol and date if in long format
        if 'symbol' in self.data.columns:
            self.data = self.data.sort_values(['symbol', 'date']).reset_index(drop=True)

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get strategy metadata for logging/storage

        Returns:
            Dictionary with strategy info
        """
        return {
            'name': self.name,
            'type': self.strategy_type.value,
            'params': self.params,
            'description': self.__doc__,
        }

    def _pivot_prices(self, price_col: str = 'close') -> pd.DataFrame:
        """
        Convert long-format data to wide format (pivot)

        Args:
            price_col: Price column to pivot

        Returns:
            DataFrame with date index and symbol columns
        """
        if 'symbol' not in self.data.columns:
            # Already in wide format
            return self.data

        return self.data.pivot(
            index='date',
            columns='symbol',
            values=price_col
        )

    def _pivot_all_prices(self) -> Dict[str, pd.DataFrame]:
        """
        Pivot all OHLCV columns to wide format

        Returns:
            Dictionary mapping column names to pivoted DataFrames
        """
        pivoted = {}
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in self.data.columns:
                pivoted[col] = self._pivot_prices(col)
        return pivoted

    def _get_rebalance_dates(self, freq: str = 'M') -> pd.DatetimeIndex:
        """
        Get rebalancing dates based on frequency

        Args:
            freq: Rebalancing frequency
                  'D' = daily
                  'W' = weekly (Friday)
                  'M' = monthly (end of month)
                  'Q' = quarterly

        Returns:
            DatetimeIndex of rebalancing dates
        """
        prices = self._pivot_prices()

        if freq == 'D':
            return prices.index

        # Group by period and get last date
        if freq == 'W':
            grouped = prices.groupby(pd.Grouper(freq='W-FRI'))
        elif freq == 'M':
            grouped = prices.groupby(pd.Grouper(freq='M'))
        elif freq == 'Q':
            grouped = prices.groupby(pd.Grouper(freq='Q'))
        else:
            raise ValueError(f"Unknown frequency: {freq}")

        # Get last date of each period that exists in our data
        rebal_dates = []
        for period, group in grouped:
            if len(group) > 0:
                rebal_dates.append(group.index[-1])

        return pd.DatetimeIndex(rebal_dates)

    def _calculate_returns(self, prices: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate daily returns from prices

        Args:
            prices: Price DataFrame (wide format)

        Returns:
            Returns DataFrame
        """
        return prices.pct_change()

    def _rank_cross_sectional(self, data: pd.DataFrame, ascending: bool = True) -> pd.DataFrame:
        """
        Cross-sectional percentile rank (rank across assets for each date)

        Args:
            data: DataFrame with date index, symbol columns
            ascending: If True, lowest values get lowest rank

        Returns:
            Percentile ranks (0 to 1)
        """
        return data.rank(axis=1, pct=True, ascending=ascending)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(params={self.params})"


class SingleAssetStrategy(Strategy):
    """
    Base class for single-asset strategies

    Use this as a base for strategies that operate on one symbol at a time.
    """

    def __init__(self, data: pd.DataFrame, params: Optional[Dict[str, Any]] = None,
                 symbol: Optional[str] = None):
        """
        Initialize single-asset strategy

        Args:
            data: Price data (long or wide format)
            params: Strategy parameters
            symbol: Symbol to trade (required if data has multiple symbols)
        """
        self.symbol = symbol
        super().__init__(data, params)

    def _preprocess_data(self) -> None:
        super()._preprocess_data()

        # If multiple symbols, filter to target symbol
        if 'symbol' in self.data.columns:
            symbols = self.data['symbol'].unique()
            if len(symbols) > 1:
                if self.symbol is None:
                    raise ValueError(f"Data has {len(symbols)} symbols. "
                                     f"Please specify which symbol to use.")
                self.data = self.data[self.data['symbol'] == self.symbol].copy()
            else:
                self.symbol = symbols[0]


class MultiAssetStrategy(Strategy):
    """
    Base class for multi-asset/cross-sectional strategies

    Use this as a base for strategies that operate on multiple symbols
    simultaneously (e.g., cross-sectional momentum, factor strategies).
    """

    def __init__(self, data: pd.DataFrame, params: Optional[Dict[str, Any]] = None):
        super().__init__(data, params)

    def _preprocess_data(self) -> None:
        super()._preprocess_data()

        # Pivot to wide format for easier cross-sectional operations
        self.prices = self._pivot_prices('close')
        self.returns = self._calculate_returns(self.prices)

        # Store all OHLCV in wide format if available
        self._all_prices = self._pivot_all_prices()
