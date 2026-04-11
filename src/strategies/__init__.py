"""
Trading Strategies Module

Contains implementations of 14 systematic trading strategies.
All strategies inherit from the base Strategy class.
"""

from src.strategies.base import Strategy, StrategyType

# Import all strategy implementations
from src.strategies.momentum import (
    LargeCapMomentumStrategy,
    FiftyTwoWeekHighBreakoutStrategy,
)
from src.strategies.value import DeepValueAllCapStrategy
from src.strategies.quality import HighQualityROICStrategy
from src.strategies.factor import (
    LowVolatilityShieldStrategy,
    DividendAristocratsStrategy,
)
from src.strategies.trend import MovingAverageTrendStrategy
from src.strategies.mean_reversion import RSIMeanReversionStrategy
from src.strategies.composite import (
    ValueMomentumBlendStrategy,
    QualityMomentumStrategy,
    QualityLowVolStrategy,
    CompositeFactorScoreStrategy,
)
from src.strategies.risk_management import VolatilityTargetingStrategy
from src.strategies.event import EarningsSurpriseMomentumStrategy

# Strategy Registry - maps names to classes
STRATEGY_REGISTRY = {
    # Momentum
    'large_cap_momentum': LargeCapMomentumStrategy,
    '52_week_high_breakout': FiftyTwoWeekHighBreakoutStrategy,

    # Value
    'deep_value_all_cap': DeepValueAllCapStrategy,

    # Quality
    'high_quality_roic': HighQualityROICStrategy,

    # Factor
    'low_volatility_shield': LowVolatilityShieldStrategy,
    'dividend_aristocrats': DividendAristocratsStrategy,

    # Trend
    'moving_average_trend': MovingAverageTrendStrategy,

    # Mean Reversion
    'rsi_mean_reversion': RSIMeanReversionStrategy,

    # Composite / Multi-Factor
    'value_momentum_blend': ValueMomentumBlendStrategy,
    'quality_momentum': QualityMomentumStrategy,
    'quality_low_vol': QualityLowVolStrategy,
    'composite_factor_score': CompositeFactorScoreStrategy,

    # Risk Management
    'volatility_targeting': VolatilityTargetingStrategy,

    # Event-Driven
    'earnings_surprise_momentum': EarningsSurpriseMomentumStrategy,
}


def get_strategy(name: str, data, params: dict = None):
    """
    Factory function to instantiate strategies by name

    Args:
        name: Strategy name (from STRATEGY_REGISTRY)
        data: Price data DataFrame
        params: Strategy parameters (optional, uses defaults if None)

    Returns:
        Strategy instance

    Example:
        strategy = get_strategy('large_cap_momentum', data, {'lookback': 126})
    """
    if name not in STRATEGY_REGISTRY:
        available = ', '.join(sorted(STRATEGY_REGISTRY.keys()))
        raise ValueError(f"Unknown strategy: '{name}'. Available: {available}")

    strategy_class = STRATEGY_REGISTRY[name]

    if params is None:
        params = {}

    return strategy_class(data, params)


def list_strategies():
    """List all available strategies"""
    return list(STRATEGY_REGISTRY.keys())


__all__ = [
    'Strategy',
    'StrategyType',
    'STRATEGY_REGISTRY',
    'get_strategy',
    'list_strategies',
    # Individual strategies
    'LargeCapMomentumStrategy',
    'FiftyTwoWeekHighBreakoutStrategy',
    'DeepValueAllCapStrategy',
    'HighQualityROICStrategy',
    'LowVolatilityShieldStrategy',
    'DividendAristocratsStrategy',
    'MovingAverageTrendStrategy',
    'RSIMeanReversionStrategy',
    'ValueMomentumBlendStrategy',
    'QualityMomentumStrategy',
    'QualityLowVolStrategy',
    'CompositeFactorScoreStrategy',
    'VolatilityTargetingStrategy',
    'EarningsSurpriseMomentumStrategy',
]
