"""
Momentum Strategies

Large Cap Momentum and 52-Week High Breakout strategies.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

from src.strategies.base import MultiAssetStrategy, StrategyType
from src.processing.indicators import rolling_returns


class LargeCapMomentumStrategy(MultiAssetStrategy):
    """
    Large Cap Momentum Strategy

    Each rebalancing period:
    - Filter to large-cap stocks (top N% by market cap proxy)
    - Rank by trailing 12-month return (skip most recent month)
    - Go long the top decile (highest momentum)

    Based on Jegadeesh & Titman (1993) momentum effect,
    filtered to large caps for lower turnover and better liquidity.

    Tunable Parameters:
    - lookback: Momentum calculation period (default 252 = 12 months)
    - skip_recent: Days to skip to avoid short-term reversal (default 21)
    - top_pct: Percentage of large-cap universe to go long (default 10)
    - large_cap_pct: Percentage of stocks considered "large cap" by market cap proxy (default 50)
    - rebalance_freq: How often to rebalance (M, Q, W)
    """

    DEFAULT_PARAMS = {
        'lookback': 252,
        'skip_recent': 21,
        'top_pct': 10,
        'large_cap_pct': 50,
        'rebalance_freq': 'M',
    }

    @property
    def name(self) -> str:
        return "Large Cap Momentum"

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.MOMENTUM

    def _validate_params(self) -> None:
        if self.params['lookback'] < 1:
            raise ValueError("Lookback must be positive")
        if not 0 < self.params['top_pct'] <= 50:
            raise ValueError("top_pct must be between 0 and 50")
        if not 0 < self.params['large_cap_pct'] <= 100:
            raise ValueError("large_cap_pct must be between 0 and 100")

    def generate_signals(self) -> pd.DataFrame:
        # Market cap proxy: average dollar volume over recent 63 days
        if 'volume' in self._all_prices:
            volume = self._all_prices['volume']
            dollar_volume = self.prices * volume
            avg_dollar_volume = dollar_volume.rolling(63, min_periods=21).mean()
        else:
            # Fallback: use price level as rough cap proxy
            avg_dollar_volume = self.prices.rolling(63, min_periods=21).mean()

        # Momentum: return from t-lookback to t-skip_recent
        skip = self.params['skip_recent']
        lb = self.params['lookback']
        ret_start = self.prices.shift(lb)
        ret_end = self.prices.shift(skip) if skip > 0 else self.prices
        trailing_momentum = ret_end / ret_start - 1

        rebal_dates = self._get_rebalance_dates(self.params['rebalance_freq'])
        signals = pd.DataFrame(0.0, index=self.prices.index, columns=self.prices.columns)

        large_cap_pct = self.params['large_cap_pct'] / 100
        top_pct = self.params['top_pct'] / 100

        for date in rebal_dates:
            if date not in trailing_momentum.index:
                continue

            mom = trailing_momentum.loc[date].dropna()
            dv = avg_dollar_volume.loc[date].dropna()

            # Intersection of stocks with both signals
            common = mom.index.intersection(dv.index)
            if len(common) < 10:
                continue

            mom = mom[common]
            dv = dv[common]

            # Filter to large caps
            dv_rank = dv.rank(pct=True, ascending=True)
            large_caps = dv_rank[dv_rank >= (1 - large_cap_pct)].index

            if len(large_caps) < 5:
                continue

            # Rank large caps by momentum
            mom_large = mom[large_caps]
            mom_rank = mom_large.rank(pct=True)

            # Long top decile
            winners = mom_rank[mom_rank >= (1 - top_pct)].index
            n = len(winners)
            if n > 0:
                signals.loc[date, winners] = 1.0 / n

        signals = signals.replace(0, np.nan).ffill().fillna(0)
        return signals

    def get_param_grid(self) -> Dict[str, List[Any]]:
        return {
            'lookback': [126, 252],
            'skip_recent': [0, 21],
            'top_pct': [10, 20],
            'large_cap_pct': [30, 50],
            'rebalance_freq': ['M', 'Q'],
        }


class FiftyTwoWeekHighBreakoutStrategy(MultiAssetStrategy):
    """
    52-Week High Breakout Strategy

    Each rebalancing period:
    - Calculate each stock's proximity to its 52-week high
    - Go long stocks closest to or above their 52-week high

    Based on George & Hwang (2004) — stocks near their 52-week high
    tend to continue outperforming, as investors anchor to the high
    and underreact to positive information.

    Tunable Parameters:
    - high_window: Window for calculating the high (default 252)
    - proximity_threshold: Min ratio to 52-week high (default 0.95 = within 5%)
    - top_pct: Percentage of stocks to go long (default 10)
    - rebalance_freq: Rebalance frequency (default M)
    """

    DEFAULT_PARAMS = {
        'high_window': 252,
        'proximity_threshold': 0.95,
        'top_pct': 10,
        'rebalance_freq': 'M',
    }

    @property
    def name(self) -> str:
        return "52-Week High Breakout"

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.MOMENTUM

    def generate_signals(self) -> pd.DataFrame:
        rolling_high = self.prices.rolling(self.params['high_window'], min_periods=126).max()
        proximity = self.prices / rolling_high  # 1.0 = at the high

        rebal_dates = self._get_rebalance_dates(self.params['rebalance_freq'])
        signals = pd.DataFrame(0.0, index=self.prices.index, columns=self.prices.columns)

        top_pct = self.params['top_pct'] / 100

        for date in rebal_dates:
            if date not in proximity.index:
                continue

            prox = proximity.loc[date].dropna()
            if len(prox) < 10:
                continue

            # Rank by proximity to 52-week high (higher = closer to high)
            ranks = prox.rank(pct=True)
            winners = ranks[ranks >= (1 - top_pct)].index
            n = len(winners)
            if n > 0:
                signals.loc[date, winners] = 1.0 / n

        signals = signals.replace(0, np.nan).ffill().fillna(0)
        return signals

    def get_param_grid(self) -> Dict[str, List[Any]]:
        return {
            'high_window': [126, 252],
            'top_pct': [10, 20],
            'proximity_threshold': [0.90, 0.95],
            'rebalance_freq': ['M', 'Q'],
        }
