"""
Mean Reversion Strategies

RSI Mean Reversion strategy (cross-sectional, multi-asset version).
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

from src.strategies.base import MultiAssetStrategy, StrategyType
from src.processing.indicators import rsi as calc_rsi


class RSIMeanReversionStrategy(MultiAssetStrategy):
    """
    RSI Mean Reversion Strategy (Cross-Sectional)

    Each rebalancing period:
    - Calculate RSI for all stocks
    - Go long stocks with RSI below oversold threshold (buy the dip)
    - Exit when RSI recovers above exit threshold

    Unlike a single-stock RSI strategy, this operates across the full
    universe, buying the most oversold stocks with equal weighting.

    Tunable Parameters:
    - rsi_period: RSI calculation period (default 14)
    - oversold: RSI threshold to enter long (default 30)
    - exit_threshold: RSI threshold to exit (default 50)
    - max_positions: Maximum number of positions (default 20)
    - rebalance_freq: How often to check for new signals (default W)
    - hold_min_days: Minimum holding period in days (default 5)
    """

    DEFAULT_PARAMS = {
        'rsi_period': 14,
        'oversold': 30,
        'exit_threshold': 50,
        'max_positions': 20,
        'rebalance_freq': 'W',
        'hold_min_days': 5,
    }

    @property
    def name(self) -> str:
        return "RSI Mean Reversion"

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.MEAN_REVERSION

    def generate_signals(self) -> pd.DataFrame:
        period = self.params['rsi_period']

        # Calculate RSI for each stock
        rsi_values = pd.DataFrame(index=self.prices.index, columns=self.prices.columns)
        for col in self.prices.columns:
            rsi_values[col] = calc_rsi(self.prices[col], period)

        rebal_dates = self._get_rebalance_dates(self.params['rebalance_freq'])
        signals = pd.DataFrame(0.0, index=self.prices.index, columns=self.prices.columns)

        oversold = self.params['oversold']
        exit_thresh = self.params['exit_threshold']
        max_pos = self.params['max_positions']

        current_holdings = set()

        for date in rebal_dates:
            if date not in rsi_values.index:
                continue

            rsi_at_date = rsi_values.loc[date].dropna()
            if len(rsi_at_date) < 10:
                continue

            # Exit positions where RSI has recovered
            exits = set()
            for stock in current_holdings:
                if stock in rsi_at_date.index and rsi_at_date[stock] > exit_thresh:
                    exits.add(stock)
            current_holdings -= exits

            # Find new oversold stocks
            oversold_stocks = rsi_at_date[rsi_at_date < oversold].sort_values()

            # Add new positions up to max
            available_slots = max_pos - len(current_holdings)
            if available_slots > 0:
                new_entries = oversold_stocks.index[:available_slots]
                current_holdings.update(new_entries)

            # Set signals
            n = len(current_holdings)
            if n > 0:
                for stock in current_holdings:
                    if stock in signals.columns:
                        signals.loc[date, stock] = 1.0 / n

        # Forward fill between rebalance dates
        signals = signals.replace(0, np.nan).ffill().fillna(0)
        return signals

    def get_param_grid(self) -> Dict[str, List[Any]]:
        return {
            'rsi_period': [7, 14, 21],
            'oversold': [20, 30, 40],
            'exit_threshold': [45, 50, 60],
            'max_positions': [10, 20, 30],
            'rebalance_freq': ['D', 'W'],
        }
