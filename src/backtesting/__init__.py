"""
Backtesting Module

Provides vectorized backtesting engine and performance metrics.
"""

from src.backtesting.engine import Backtester, BacktestResult
from src.backtesting.metrics import calculate_metrics, MetricResult

__all__ = [
    'Backtester',
    'BacktestResult',
    'calculate_metrics',
    'MetricResult',
]
