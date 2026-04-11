"""
Quality Strategies

High Quality ROIC strategy using price-derived quality proxies.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

from src.strategies.base import MultiAssetStrategy, StrategyType
from src.processing.indicators import rolling_volatility


class HighQualityROICStrategy(MultiAssetStrategy):
    """
    High Quality ROIC Strategy

    Each rebalancing period:
    - Calculate a composite quality score from price-derived proxies
    - Rank all stocks by quality
    - Go long the highest quality quintile

    Quality Proxies (from price data only):
    1. Low return volatility (stable earnings -> stable price)
    2. Positive and stable momentum (consistent performance)
    3. Low max drawdown (resilience)

    NOTE: With fundamental data, this strategy would use:
    - Return on Invested Capital (ROIC)
    - Return on Equity (ROE)
    - Gross profit margin stability
    - Low debt-to-equity
    - Earnings growth consistency

    Tunable Parameters:
    - vol_lookback: Volatility calculation window (default 252)
    - mom_lookback: Momentum calculation window (default 252)
    - top_pct: Percentage of highest quality stocks to buy (default 20)
    - rebalance_freq: Rebalance frequency (default Q)
    """

    DEFAULT_PARAMS = {
        'vol_lookback': 252,
        'mom_lookback': 252,
        'top_pct': 20,
        'rebalance_freq': 'Q',
    }

    @property
    def name(self) -> str:
        return "High Quality ROIC"

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.FACTOR

    def generate_signals(self) -> pd.DataFrame:
        vol_lb = self.params['vol_lookback']
        mom_lb = self.params['mom_lookback']

        # Quality signal 1: Low volatility (stable business)
        volatility = rolling_volatility(self.returns, vol_lb, annualize=True)

        # Quality signal 2: Risk-adjusted returns (Sharpe-like)
        momentum = self.prices.pct_change(mom_lb)
        risk_adj_return = momentum / volatility

        # Quality signal 3: Low max drawdown over lookback
        rolling_max = self.prices.rolling(vol_lb, min_periods=vol_lb // 2).max()
        drawdown = self.prices / rolling_max - 1
        max_dd = drawdown.rolling(vol_lb, min_periods=vol_lb // 2).min().abs()

        rebal_dates = self._get_rebalance_dates(self.params['rebalance_freq'])
        signals = pd.DataFrame(0.0, index=self.prices.index, columns=self.prices.columns)

        top_pct = self.params['top_pct'] / 100

        for date in rebal_dates:
            if date not in volatility.index:
                continue

            vol = volatility.loc[date].dropna()
            rar = risk_adj_return.loc[date].dropna()
            dd = max_dd.loc[date].dropna()

            common = vol.index.intersection(rar.index).intersection(dd.index)
            if len(common) < 10:
                continue

            # Rank each quality signal (higher rank = higher quality)
            vol_rank = vol[common].rank(pct=True, ascending=True)      # Low vol = low rank, invert below
            rar_rank = rar[common].rank(pct=True, ascending=True)      # High risk-adj return = high rank
            dd_rank = dd[common].rank(pct=True, ascending=True)        # Low drawdown = low rank, invert

            # Invert vol and drawdown so higher = better quality
            vol_quality = 1 - vol_rank
            dd_quality = 1 - dd_rank

            # Composite quality score (higher = better)
            quality_score = (vol_quality + rar_rank + dd_quality) / 3

            # Select highest quality stocks
            winners = quality_score[quality_score >= (1 - top_pct)].index
            n = len(winners)
            if n > 0:
                signals.loc[date, winners] = 1.0 / n

        signals = signals.replace(0, np.nan).ffill().fillna(0)
        return signals

    def get_param_grid(self) -> Dict[str, List[Any]]:
        return {
            'vol_lookback': [126, 252],
            'mom_lookback': [126, 252],
            'top_pct': [10, 20],
            'rebalance_freq': ['M', 'Q'],
        }
