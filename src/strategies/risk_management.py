"""
Risk Management Strategies

Volatility Targeting strategy.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

from src.strategies.base import MultiAssetStrategy, StrategyType
from src.processing.indicators import rolling_volatility


class VolatilityTargetingStrategy(MultiAssetStrategy):
    """
    Volatility Targeting Strategy

    Maintains a constant portfolio volatility by dynamically adjusting
    position sizes based on realized volatility:
    - When vol is low → increase exposure (leverage up)
    - When vol is high → decrease exposure (de-risk)

    The base portfolio is an equal-weighted universe. The strategy
    scales the entire portfolio by (target_vol / realized_vol),
    capped at a maximum leverage.

    This approach is used by many institutional investors and
    risk-parity funds (Bridgewater, AQR).

    Tunable Parameters:
    - target_vol: Annualized target volatility (default 0.10 = 10%)
    - vol_lookback: Window for estimating realized vol (default 63)
    - max_leverage: Maximum leverage allowed (default 2.0)
    - min_leverage: Minimum leverage / exposure (default 0.1)
    - rebalance_freq: How often to adjust (default W)
    - vol_floor: Minimum realized vol to prevent division issues (default 0.02)
    """

    DEFAULT_PARAMS = {
        'target_vol': 0.10,
        'vol_lookback': 63,
        'max_leverage': 2.0,
        'min_leverage': 0.1,
        'rebalance_freq': 'W',
        'vol_floor': 0.02,
    }

    @property
    def name(self) -> str:
        return "Volatility Targeting"

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.PORTFOLIO

    def _validate_params(self) -> None:
        if self.params['target_vol'] <= 0:
            raise ValueError("target_vol must be positive")
        if self.params['max_leverage'] < 1:
            raise ValueError("max_leverage must be >= 1")

    def generate_signals(self) -> pd.DataFrame:
        target = self.params['target_vol']
        vol_lb = self.params['vol_lookback']
        max_lev = self.params['max_leverage']
        min_lev = self.params['min_leverage']
        vol_floor = self.params['vol_floor']

        # Equal-weighted portfolio returns
        n_stocks = self.returns.count(axis=1)
        portfolio_returns = self.returns.mean(axis=1)

        # Realized portfolio volatility
        realized_vol = rolling_volatility(
            portfolio_returns, vol_lb, annualize=True
        )

        # Scaling factor: target / realized
        realized_vol_floored = realized_vol.clip(lower=vol_floor)
        scale = target / realized_vol_floored
        scale = scale.clip(lower=min_lev, upper=max_lev)

        rebal_dates = self._get_rebalance_dates(self.params['rebalance_freq'])
        signals = pd.DataFrame(0.0, index=self.prices.index, columns=self.prices.columns)

        for date in rebal_dates:
            if date not in scale.index or pd.isna(scale.loc[date]):
                continue

            s = scale.loc[date]
            available = self.prices.loc[date].dropna().index
            n = len(available)
            if n < 5:
                continue

            # Equal weight, scaled by vol targeting
            weight = s / n
            signals.loc[date, available] = weight

        signals = signals.replace(0, np.nan).ffill().fillna(0)
        return signals

    def get_param_grid(self) -> Dict[str, List[Any]]:
        return {
            'target_vol': [0.05, 0.10, 0.15, 0.20],
            'vol_lookback': [21, 63, 126],
            'max_leverage': [1.5, 2.0],
            'rebalance_freq': ['W', 'M'],
        }
