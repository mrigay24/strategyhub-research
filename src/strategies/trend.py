"""
Trend Following Strategies

Moving Average Trend strategy.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

from src.strategies.base import MultiAssetStrategy, StrategyType
from src.processing.indicators import sma, ema


class MovingAverageTrendStrategy(MultiAssetStrategy):
    """
    Moving Average Trend Strategy

    Each rebalancing period:
    - For each stock, check if price is above its N-day moving average
    - Go long stocks that are in an uptrend (price > MA)
    - Equal-weight all stocks in uptrend

    This is a simple but powerful trend filter used by many systematic
    funds (Meb Faber's "Ivy Portfolio" approach). It acts as a binary
    risk-on/risk-off signal per stock.

    Tunable Parameters:
    - ma_type: 'sma' or 'ema' (default sma)
    - ma_window: Moving average period (default 200)
    - rebalance_freq: Rebalance frequency (default M)
    - min_stocks: Minimum stocks in uptrend to stay invested (default 10)
    - use_slope: Also require MA slope to be positive (default False)
    - slope_window: Window for measuring MA slope (default 21)
    """

    DEFAULT_PARAMS = {
        'ma_type': 'sma',
        'ma_window': 200,
        'rebalance_freq': 'M',
        'min_stocks': 10,
        'use_slope': False,
        'slope_window': 21,
    }

    @property
    def name(self) -> str:
        return "Moving Average Trend"

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.TREND_FOLLOWING

    def generate_signals(self) -> pd.DataFrame:
        win = self.params['ma_window']

        if self.params['ma_type'] == 'ema':
            moving_avg = ema(self.prices, win)
        else:
            moving_avg = sma(self.prices, win)

        # Price above MA = uptrend
        above_ma = (self.prices > moving_avg).astype(float)

        # Optional: also require positive slope
        if self.params['use_slope']:
            slope_win = self.params['slope_window']
            ma_slope = moving_avg.diff(slope_win) / moving_avg.shift(slope_win)
            positive_slope = (ma_slope > 0).astype(float)
            above_ma = above_ma * positive_slope

        rebal_dates = self._get_rebalance_dates(self.params['rebalance_freq'])
        signals = pd.DataFrame(0.0, index=self.prices.index, columns=self.prices.columns)

        for date in rebal_dates:
            if date not in above_ma.index:
                continue

            trend_at_date = above_ma.loc[date].dropna()
            uptrend_stocks = trend_at_date[trend_at_date == 1.0].index

            n = len(uptrend_stocks)
            if n >= self.params['min_stocks']:
                signals.loc[date, uptrend_stocks] = 1.0 / n

        signals = signals.replace(0, np.nan).ffill().fillna(0)
        return signals

    def get_param_grid(self) -> Dict[str, List[Any]]:
        return {
            'ma_type': ['sma', 'ema'],
            'ma_window': [50, 100, 200],
            'use_slope': [False, True],
            'rebalance_freq': ['M', 'Q'],
        }
