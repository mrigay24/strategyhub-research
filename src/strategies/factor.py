"""
Factor Strategies

Low Volatility Shield and Dividend Aristocrats strategies.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

from src.strategies.base import MultiAssetStrategy, StrategyType
from src.processing.indicators import rolling_volatility


class LowVolatilityShieldStrategy(MultiAssetStrategy):
    """
    Low Volatility Shield Strategy

    Each rebalancing period:
    - Calculate trailing volatility for each stock
    - Go long the lowest volatility quintile
    - Weight by inverse volatility (lower vol = higher weight)

    Based on the "low volatility anomaly" — lower risk stocks have
    historically delivered comparable or better returns than high risk stocks,
    violating the CAPM prediction. Documented by Baker, Bradley & Wurgler (2011).

    Tunable Parameters:
    - vol_lookback: Volatility calculation window (default 63 = ~3 months)
    - bottom_pct: Percentage of lowest vol stocks to buy (default 20)
    - rebalance_freq: Rebalance frequency (default M)
    - weighting: 'equal' or 'inverse_vol' (default inverse_vol)
    """

    DEFAULT_PARAMS = {
        'vol_lookback': 63,
        'bottom_pct': 20,
        'rebalance_freq': 'M',
        'weighting': 'inverse_vol',
    }

    @property
    def name(self) -> str:
        return "Low Volatility Shield"

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.FACTOR

    def generate_signals(self) -> pd.DataFrame:
        volatility = rolling_volatility(
            self.returns, self.params['vol_lookback'], annualize=True
        )

        rebal_dates = self._get_rebalance_dates(self.params['rebalance_freq'])
        signals = pd.DataFrame(0.0, index=self.prices.index, columns=self.prices.columns)

        bottom_pct = self.params['bottom_pct'] / 100

        for date in rebal_dates:
            if date not in volatility.index:
                continue

            vol = volatility.loc[date].dropna()
            if len(vol) < 10:
                continue

            # Select lowest volatility stocks
            ranks = vol.rank(pct=True, ascending=True)
            low_vol = ranks[ranks <= bottom_pct].index

            n = len(low_vol)
            if n > 0:
                if self.params['weighting'] == 'inverse_vol':
                    inv_vol = 1.0 / vol[low_vol]
                    weights = inv_vol / inv_vol.sum()
                    signals.loc[date, low_vol] = weights
                else:
                    signals.loc[date, low_vol] = 1.0 / n

        signals = signals.replace(0, np.nan).ffill().fillna(0)
        return signals

    def get_param_grid(self) -> Dict[str, List[Any]]:
        return {
            'vol_lookback': [21, 63, 126],
            'bottom_pct': [10, 20, 30],
            'weighting': ['equal', 'inverse_vol'],
            'rebalance_freq': ['M', 'Q'],
        }


class DividendAristocratsStrategy(MultiAssetStrategy):
    """
    Dividend Aristocrats Strategy

    Each rebalancing period:
    - Identify stocks with consistent positive returns (proxy for dividend growers)
    - Go long the most consistent performers

    Consistency Proxy (from price data only):
    - Count the number of positive monthly returns over the lookback
    - Higher count = more consistent = proxy for reliable dividend payer

    NOTE: With fundamental data, this strategy would:
    - Filter for 25+ years of consecutive dividend increases
    - Rank by dividend yield, payout ratio, and dividend growth rate
    - Use actual dividend payment history

    Tunable Parameters:
    - lookback_months: How many months to evaluate consistency (default 36)
    - min_positive_pct: Minimum fraction of positive months (default 0.6)
    - top_pct: Percentage of most consistent stocks to buy (default 20)
    - rebalance_freq: Rebalance frequency (default Q)
    """

    DEFAULT_PARAMS = {
        'lookback_months': 36,
        'min_positive_pct': 0.6,
        'top_pct': 20,
        'rebalance_freq': 'Q',
    }

    @property
    def name(self) -> str:
        return "Dividend Aristocrats"

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.FACTOR

    def generate_signals(self) -> pd.DataFrame:
        # Calculate monthly returns
        monthly_prices = self.prices.resample('M').last()
        monthly_returns = monthly_prices.pct_change()

        rebal_dates = self._get_rebalance_dates(self.params['rebalance_freq'])
        signals = pd.DataFrame(0.0, index=self.prices.index, columns=self.prices.columns)

        lb = self.params['lookback_months']
        min_pos = self.params['min_positive_pct']
        top_pct = self.params['top_pct'] / 100

        for date in rebal_dates:
            # Find the closest monthly return date
            monthly_dates = monthly_returns.index[monthly_returns.index <= date]
            if len(monthly_dates) < lb:
                continue

            recent_monthly = monthly_returns.loc[monthly_dates[-lb:]].dropna(axis=1, how='any')
            if len(recent_monthly.columns) < 10:
                continue

            # Consistency score: fraction of positive months
            positive_months = (recent_monthly > 0).sum()
            consistency = positive_months / lb

            # Also factor in low volatility of monthly returns (stability)
            monthly_vol = recent_monthly.std()
            vol_rank = monthly_vol.rank(pct=True, ascending=True)
            stability = 1 - vol_rank  # Lower vol = higher stability

            # Composite score
            score = (consistency + stability) / 2

            # Filter: at least min_positive_pct positive months
            eligible = consistency[consistency >= min_pos].index
            if len(eligible) < 5:
                eligible = score.index  # Relax filter if too few

            score_eligible = score[eligible]
            ranks = score_eligible.rank(pct=True)
            winners = ranks[ranks >= (1 - top_pct)].index

            n = len(winners)
            if n > 0:
                signals.loc[date, winners] = 1.0 / n

        signals = signals.replace(0, np.nan).ffill().fillna(0)
        return signals

    def get_param_grid(self) -> Dict[str, List[Any]]:
        return {
            'lookback_months': [24, 36, 48],
            'min_positive_pct': [0.5, 0.6, 0.7],
            'top_pct': [10, 20],
            'rebalance_freq': ['Q'],
        }
