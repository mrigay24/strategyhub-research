"""
Composite / Multi-Factor Strategies

Strategies that blend multiple factors together:
- Value + Momentum
- Quality + Momentum
- Quality + Low Volatility
- Composite Factor Score (all factors combined)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

from src.strategies.base import MultiAssetStrategy, StrategyType
from src.processing.indicators import rolling_returns, rolling_volatility


class ValueMomentumBlendStrategy(MultiAssetStrategy):
    """
    Value + Momentum Blend Strategy

    Combines value and momentum signals to find stocks that are
    both cheap AND have positive price trends. This avoids "value traps"
    (cheap stocks that keep getting cheaper).

    Signals:
    - Value: Low trailing return (contrarian) + low price/MA ratio
    - Momentum: High recent 6-12 month return (skip last month)

    Combining these two negatively-correlated factors provides
    significant diversification benefits (Asness, Moskowitz & Pedersen 2013).

    Tunable Parameters:
    - mom_lookback: Momentum lookback (default 252)
    - value_lookback: Value lookback (default 252)
    - mom_weight: Weight on momentum signal (default 0.5)
    - value_weight: Weight on value signal (default 0.5)
    - top_pct: Percentage of stocks to buy (default 20)
    - rebalance_freq: Rebalance frequency (default M)
    """

    DEFAULT_PARAMS = {
        'mom_lookback': 252,
        'value_lookback': 252,
        'mom_weight': 0.5,
        'value_weight': 0.5,
        'top_pct': 20,
        'rebalance_freq': 'M',
    }

    @property
    def name(self) -> str:
        return "Value + Momentum Blend"

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.FACTOR

    def generate_signals(self) -> pd.DataFrame:
        mom_lb = self.params['mom_lookback']
        val_lb = self.params['value_lookback']

        # Momentum signal: 12-month return, skip last month
        ret_start = self.prices.shift(mom_lb)
        ret_end = self.prices.shift(21)
        momentum = ret_end / ret_start - 1

        # Value signal: inverse momentum (contrarian)
        value_mom = -rolling_returns(self.prices, val_lb)

        # Value signal 2: low price relative to MA
        ma = self.prices.rolling(200, min_periods=100).mean()
        price_to_ma = self.prices / ma

        rebal_dates = self._get_rebalance_dates(self.params['rebalance_freq'])
        signals = pd.DataFrame(0.0, index=self.prices.index, columns=self.prices.columns)

        mw = self.params['mom_weight']
        vw = self.params['value_weight']
        top_pct = self.params['top_pct'] / 100

        for date in rebal_dates:
            if date not in momentum.index:
                continue

            mom = momentum.loc[date].dropna()
            val = value_mom.loc[date].dropna()
            pma = price_to_ma.loc[date].dropna()

            common = mom.index.intersection(val.index).intersection(pma.index)
            if len(common) < 10:
                continue

            # Rank each signal (higher = better)
            mom_rank = mom[common].rank(pct=True)
            val_rank = val[common].rank(pct=True)
            pma_rank = (1 - pma[common].rank(pct=True))  # Low price/MA = high value

            value_composite = (val_rank + pma_rank) / 2
            composite = mw * mom_rank + vw * value_composite

            # Select top stocks
            winners = composite[composite >= composite.quantile(1 - top_pct)].index
            n = len(winners)
            if n > 0:
                signals.loc[date, winners] = 1.0 / n

        signals = signals.replace(0, np.nan).ffill().fillna(0)
        return signals

    def get_param_grid(self) -> Dict[str, List[Any]]:
        return {
            'mom_lookback': [126, 252],
            'value_lookback': [126, 252],
            'mom_weight': [0.3, 0.5, 0.7],
            'top_pct': [10, 20],
            'rebalance_freq': ['M', 'Q'],
        }


class QualityMomentumStrategy(MultiAssetStrategy):
    """
    Quality + Momentum Strategy

    Combines quality and momentum signals to find stocks that are
    both high-quality AND trending up. This targets "compounders" —
    great businesses with positive price momentum.

    Signals:
    - Quality: Low volatility, high risk-adjusted returns, low drawdown
    - Momentum: High trailing return (skip last month)

    Tunable Parameters:
    - mom_lookback: Momentum lookback (default 252)
    - vol_lookback: Volatility lookback for quality (default 252)
    - mom_weight: Weight on momentum (default 0.5)
    - quality_weight: Weight on quality (default 0.5)
    - top_pct: Percentage of stocks to buy (default 20)
    - rebalance_freq: Rebalance frequency (default M)
    """

    DEFAULT_PARAMS = {
        'mom_lookback': 252,
        'vol_lookback': 252,
        'mom_weight': 0.5,
        'quality_weight': 0.5,
        'top_pct': 20,
        'rebalance_freq': 'M',
    }

    @property
    def name(self) -> str:
        return "Quality + Momentum"

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.FACTOR

    def generate_signals(self) -> pd.DataFrame:
        mom_lb = self.params['mom_lookback']
        vol_lb = self.params['vol_lookback']

        # Momentum: 12-month return, skip last month
        ret_start = self.prices.shift(mom_lb)
        ret_end = self.prices.shift(21)
        momentum = ret_end / ret_start - 1

        # Quality signals
        volatility = rolling_volatility(self.returns, vol_lb, annualize=True)
        risk_adj_return = momentum / volatility

        rebal_dates = self._get_rebalance_dates(self.params['rebalance_freq'])
        signals = pd.DataFrame(0.0, index=self.prices.index, columns=self.prices.columns)

        mw = self.params['mom_weight']
        qw = self.params['quality_weight']
        top_pct = self.params['top_pct'] / 100

        for date in rebal_dates:
            if date not in momentum.index:
                continue

            mom = momentum.loc[date].dropna()
            vol = volatility.loc[date].dropna()
            rar = risk_adj_return.loc[date].dropna()

            common = mom.index.intersection(vol.index).intersection(rar.index)
            if len(common) < 10:
                continue

            # Ranks
            mom_rank = mom[common].rank(pct=True)
            vol_rank = 1 - vol[common].rank(pct=True)  # Low vol = high quality
            rar_rank = rar[common].rank(pct=True)

            quality_composite = (vol_rank + rar_rank) / 2
            composite = mw * mom_rank + qw * quality_composite

            winners = composite[composite >= composite.quantile(1 - top_pct)].index
            n = len(winners)
            if n > 0:
                signals.loc[date, winners] = 1.0 / n

        signals = signals.replace(0, np.nan).ffill().fillna(0)
        return signals

    def get_param_grid(self) -> Dict[str, List[Any]]:
        return {
            'mom_lookback': [126, 252],
            'vol_lookback': [126, 252],
            'mom_weight': [0.3, 0.5, 0.7],
            'top_pct': [10, 20],
        }


class QualityLowVolStrategy(MultiAssetStrategy):
    """
    Quality + Low Volatility Strategy

    Combines quality and low volatility to build a defensive portfolio
    of stable, high-quality stocks. This is a "sleep-at-night" strategy
    that aims to minimize drawdowns while maintaining steady returns.

    Signals:
    - Quality: High risk-adjusted returns, low max drawdown
    - Low Vol: Low trailing volatility

    Tunable Parameters:
    - vol_lookback: Volatility lookback (default 126)
    - quality_lookback: Quality signal lookback (default 252)
    - vol_weight: Weight on low volatility (default 0.5)
    - quality_weight: Weight on quality (default 0.5)
    - top_pct: Percentage of stocks to buy (default 20)
    - rebalance_freq: Rebalance frequency (default M)
    """

    DEFAULT_PARAMS = {
        'vol_lookback': 126,
        'quality_lookback': 252,
        'vol_weight': 0.5,
        'quality_weight': 0.5,
        'top_pct': 20,
        'rebalance_freq': 'M',
    }

    @property
    def name(self) -> str:
        return "Quality + Low Volatility"

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.FACTOR

    def generate_signals(self) -> pd.DataFrame:
        vol_lb = self.params['vol_lookback']
        q_lb = self.params['quality_lookback']

        # Low vol signal
        volatility = rolling_volatility(self.returns, vol_lb, annualize=True)

        # Quality signals
        momentum = self.prices.pct_change(q_lb)
        risk_adj_return = momentum / volatility

        # Max drawdown
        rolling_max = self.prices.rolling(q_lb, min_periods=q_lb // 2).max()
        drawdown = self.prices / rolling_max - 1
        max_dd = drawdown.rolling(q_lb, min_periods=q_lb // 2).min().abs()

        rebal_dates = self._get_rebalance_dates(self.params['rebalance_freq'])
        signals = pd.DataFrame(0.0, index=self.prices.index, columns=self.prices.columns)

        vw = self.params['vol_weight']
        qw = self.params['quality_weight']
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

            # Ranks (higher = better)
            vol_rank = 1 - vol[common].rank(pct=True)    # Low vol = good
            rar_rank = rar[common].rank(pct=True)          # High risk-adj = good
            dd_rank = 1 - dd[common].rank(pct=True)        # Low drawdown = good

            quality = (rar_rank + dd_rank) / 2
            composite = vw * vol_rank + qw * quality

            winners = composite[composite >= composite.quantile(1 - top_pct)].index
            n = len(winners)
            if n > 0:
                signals.loc[date, winners] = 1.0 / n

        signals = signals.replace(0, np.nan).ffill().fillna(0)
        return signals

    def get_param_grid(self) -> Dict[str, List[Any]]:
        return {
            'vol_lookback': [63, 126],
            'quality_lookback': [126, 252],
            'vol_weight': [0.3, 0.5, 0.7],
            'top_pct': [10, 20],
        }


class CompositeFactorScoreStrategy(MultiAssetStrategy):
    """
    Composite Factor Score Strategy

    Combines ALL major factors into a single composite score:
    - Momentum
    - Value (contrarian)
    - Quality (stability + risk-adjusted returns)
    - Low Volatility

    Each stock gets ranked on each factor, then a weighted average
    produces the final composite score. This is essentially a
    multi-factor "smart beta" portfolio.

    Tunable Parameters:
    - lookback: Lookback period for all signals (default 252)
    - momentum_weight: Weight on momentum factor (default 0.3)
    - value_weight: Weight on value factor (default 0.2)
    - quality_weight: Weight on quality factor (default 0.3)
    - low_vol_weight: Weight on low vol factor (default 0.2)
    - top_pct: Percentage of stocks to buy (default 20)
    - rebalance_freq: Rebalance frequency (default M)
    """

    DEFAULT_PARAMS = {
        'lookback': 252,
        'momentum_weight': 0.30,
        'value_weight': 0.20,
        'quality_weight': 0.30,
        'low_vol_weight': 0.20,
        'top_pct': 20,
        'rebalance_freq': 'M',
    }

    @property
    def name(self) -> str:
        return "Composite Factor Score"

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.FACTOR

    def generate_signals(self) -> pd.DataFrame:
        lb = self.params['lookback']

        # Momentum: 12-month return, skip last month
        ret_start = self.prices.shift(lb)
        ret_end = self.prices.shift(21)
        momentum = ret_end / ret_start - 1

        # Value: inverse momentum (contrarian)
        value = -rolling_returns(self.prices, lb)

        # Quality: risk-adjusted return
        volatility = rolling_volatility(self.returns, lb, annualize=True)
        quality = momentum / volatility

        rebal_dates = self._get_rebalance_dates(self.params['rebalance_freq'])
        signals = pd.DataFrame(0.0, index=self.prices.index, columns=self.prices.columns)

        mw = self.params['momentum_weight']
        vw = self.params['value_weight']
        qw = self.params['quality_weight']
        lw = self.params['low_vol_weight']
        top_pct = self.params['top_pct'] / 100

        for date in rebal_dates:
            if date not in momentum.index:
                continue

            mom = momentum.loc[date].dropna()
            val = value.loc[date].dropna()
            qual = quality.loc[date].dropna()
            vol = volatility.loc[date].dropna()

            common = mom.index.intersection(val.index).intersection(qual.index).intersection(vol.index)
            if len(common) < 10:
                continue

            # Rank each factor (higher = better)
            mom_rank = mom[common].rank(pct=True)
            val_rank = val[common].rank(pct=True)
            qual_rank = qual[common].rank(pct=True)
            vol_rank = 1 - vol[common].rank(pct=True)  # Low vol = good

            composite = mw * mom_rank + vw * val_rank + qw * qual_rank + lw * vol_rank

            winners = composite[composite >= composite.quantile(1 - top_pct)].index
            n = len(winners)
            if n > 0:
                signals.loc[date, winners] = 1.0 / n

        signals = signals.replace(0, np.nan).ffill().fillna(0)
        return signals

    def get_param_grid(self) -> Dict[str, List[Any]]:
        return {
            'lookback': [126, 252],
            'momentum_weight': [0.2, 0.3, 0.4],
            'value_weight': [0.1, 0.2, 0.3],
            'quality_weight': [0.2, 0.3, 0.4],
            'low_vol_weight': [0.1, 0.2, 0.3],
            'top_pct': [10, 20],
        }
