"""
Value Strategies

Deep Value All-Cap strategy using price-derived valuation proxies.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

from src.strategies.base import MultiAssetStrategy, StrategyType
from src.processing.indicators import rolling_returns


class DeepValueAllCapStrategy(MultiAssetStrategy):
    """
    Deep Value All-Cap Strategy

    Each rebalancing period:
    - Calculate a composite value score from price-derived proxies
    - Rank all stocks by value score
    - Go long the cheapest quintile

    Value Proxies (from price data only):
    1. Contrarian signal: Negative 12-month momentum (beaten-down stocks)
    2. Low price-to-moving-average ratio (price below long-term trend)
    3. High dividend yield proxy: low recent price appreciation

    NOTE: With fundamental data (P/E, P/B, P/S, EV/EBITDA), this strategy
    would use proper valuation ratios. Current implementation uses
    price-based contrarian signals as a proxy.

    Tunable Parameters:
    - lookback: Period for calculating value signals (default 252)
    - top_pct: Percentage of cheapest stocks to buy (default 20)
    - rebalance_freq: Rebalance frequency (default Q for quarterly)
    - ma_window: Moving average window for price/MA ratio (default 200)
    """

    DEFAULT_PARAMS = {
        'lookback': 252,
        'top_pct': 20,
        'rebalance_freq': 'Q',
        'ma_window': 200,
    }

    @property
    def name(self) -> str:
        return "Deep Value All-Cap"

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.FACTOR

    def generate_signals(self) -> pd.DataFrame:
        lb = self.params['lookback']
        ma_win = self.params['ma_window']

        # Value signal 1: Negative momentum (contrarian — lower return = cheaper)
        momentum = rolling_returns(self.prices, lb)

        # Value signal 2: Price / 200-day MA ratio (lower = more beaten down)
        ma = self.prices.rolling(ma_win, min_periods=ma_win // 2).mean()
        price_to_ma = self.prices / ma

        rebal_dates = self._get_rebalance_dates(self.params['rebalance_freq'])
        signals = pd.DataFrame(0.0, index=self.prices.index, columns=self.prices.columns)

        top_pct = self.params['top_pct'] / 100

        for date in rebal_dates:
            if date not in momentum.index:
                continue

            mom = momentum.loc[date].dropna()
            p_ma = price_to_ma.loc[date].dropna()

            common = mom.index.intersection(p_ma.index)
            if len(common) < 10:
                continue

            # Composite value score: average rank of value signals
            # Lower momentum rank = cheaper, lower price/MA rank = cheaper
            mom_rank = mom[common].rank(pct=True, ascending=True)   # Low return = low rank = cheap
            pma_rank = p_ma[common].rank(pct=True, ascending=True)  # Low price/MA = low rank = cheap

            # Value score = average of ranks (lower = cheaper = better value)
            value_score = (mom_rank + pma_rank) / 2

            # Select cheapest stocks (lowest value score)
            cheapest = value_score[value_score <= top_pct].index
            n = len(cheapest)
            if n > 0:
                signals.loc[date, cheapest] = 1.0 / n

        signals = signals.replace(0, np.nan).ffill().fillna(0)
        return signals

    def get_param_grid(self) -> Dict[str, List[Any]]:
        return {
            'lookback': [126, 252],
            'top_pct': [10, 20, 30],
            'rebalance_freq': ['M', 'Q'],
            'ma_window': [100, 200],
        }
