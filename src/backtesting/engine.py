"""
Vectorized Backtesting Engine

Provides fast, vectorized backtesting with transaction cost support.
Carefully avoids look-ahead bias by shifting signals before applying.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union
from loguru import logger

from src.strategies.base import Strategy
from src.backtesting.metrics import calculate_metrics


@dataclass
class BacktestResult:
    """Container for backtest results"""

    # Core results
    equity_curve: pd.Series
    returns: pd.Series
    positions: pd.DataFrame
    signals: pd.DataFrame

    # Metrics
    metrics: Dict[str, float]

    # Trade analysis
    trades: Optional[pd.DataFrame] = None
    turnover: Optional[pd.Series] = None

    # Metadata
    strategy_name: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    initial_capital: float = 1_000_000
    commission_bps: float = 10
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    def summary(self) -> str:
        """Return formatted summary string"""
        lines = [
            f"{'=' * 60}",
            f"BACKTEST RESULTS: {self.strategy_name}",
            f"{'=' * 60}",
            f"Period: {self.start_date} to {self.end_date}",
            f"Initial Capital: ${self.initial_capital:,.0f}",
            f"Final Value: ${self.equity_curve.iloc[-1]:,.0f}",
            f"Commission: {self.commission_bps} bps",
            f"",
            f"PERFORMANCE METRICS:",
            f"-" * 40,
        ]

        for name, value in self.metrics.items():
            if 'return' in name.lower() or 'drawdown' in name.lower():
                lines.append(f"  {name}: {value:.2%}")
            elif 'ratio' in name.lower():
                lines.append(f"  {name}: {value:.3f}")
            elif 'rate' in name.lower() or 'turnover' in name.lower():
                lines.append(f"  {name}: {value:.2%}")
            else:
                lines.append(f"  {name}: {value:,.2f}")

        lines.append(f"{'=' * 60}")
        return "\n".join(lines)


class Backtester:
    """
    Vectorized Backtesting Engine

    Key Features:
    - Vectorized for speed
    - Transaction cost modeling
    - Strict avoidance of look-ahead bias
    - Support for single and multi-asset strategies

    Look-Ahead Bias Prevention:
    - Signals generated at time t are applied at time t+1
    - Returns are calculated as: signal[t-1] * return[t]
    """

    def __init__(
        self,
        strategy: Strategy,
        data: pd.DataFrame,
        initial_capital: float = 1_000_000,
        commission_bps: float = 10,
        slippage_bps: float = 5,
    ):
        """
        Initialize backtester

        Args:
            strategy: Strategy instance with generate_signals() method
            data: Price data (same format as passed to strategy)
            initial_capital: Starting capital
            commission_bps: Round-trip commission in basis points
            slippage_bps: Slippage in basis points
        """
        self.strategy = strategy
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.commission_bps = commission_bps
        self.slippage_bps = slippage_bps

        # Total transaction cost per round-trip
        self.total_cost_bps = commission_bps + slippage_bps

        self._preprocess_data()

    def _preprocess_data(self) -> None:
        """Prepare data for backtesting"""
        # Convert to wide format if needed
        if 'symbol' in self.data.columns:
            self.prices = self.data.pivot(
                index='date',
                columns='symbol',
                values='close'
            )
        else:
            self.prices = self.data[['close']].copy()
            self.prices.columns = ['asset']

        # Calculate returns (fill_method=None prevents false returns at NaN boundaries
        # where a symbol enters or exits the universe — critical for extended data)
        self.returns = self.prices.pct_change(fill_method=None)

        # Clip extreme single-day returns to prevent cumprod hitting zero permanently
        # A single -100% daily return zeroes the equity curve forever — clip to [-95%, +200%]
        self.returns = self.returns.clip(lower=-0.95, upper=2.0)

    def run(self) -> BacktestResult:
        """
        Execute backtest

        Returns:
            BacktestResult with equity curve, metrics, and analysis
        """
        logger.info(f"Running backtest: {self.strategy.name}")

        # Generate signals
        signals = self.strategy.generate_signals()

        # Align signals with price data
        signals = self._align_signals(signals)

        # CRITICAL: Shift signals by 1 day to avoid look-ahead bias
        # Signal at t determines position for t+1
        shifted_signals = signals.shift(1).fillna(0)

        # Calculate strategy returns
        # Return at t = position at t (from signal at t-1) * asset return at t
        if signals.shape[1] == 1 or 'signal' in signals.columns:
            # Single asset
            if 'signal' in signals.columns:
                position = shifted_signals['signal']
            else:
                position = shifted_signals.iloc[:, 0]
            asset_returns = self.returns.iloc[:, 0]
            strategy_returns = position * asset_returns
        else:
            # Multi-asset: weighted sum of returns
            strategy_returns = (shifted_signals * self.returns).sum(axis=1)

        # Calculate turnover (for transaction costs)
        turnover = self._calculate_turnover(shifted_signals)

        # Apply transaction costs
        transaction_costs = turnover * (self.total_cost_bps / 10000)
        strategy_returns = strategy_returns - transaction_costs

        # Fill NaN values with 0 (no return on days without valid data)
        strategy_returns = strategy_returns.fillna(0)

        # Clip portfolio-level daily returns to prevent cumprod zeroing permanently
        # A single -100% day makes cumprod = 0 forever — cap at -50% per day
        strategy_returns = strategy_returns.clip(lower=-0.50)

        # Build equity curve
        equity_curve = self.initial_capital * (1 + strategy_returns).cumprod()

        # Calculate metrics
        metrics = calculate_metrics(
            returns=strategy_returns,
            equity_curve=equity_curve,
            turnover=turnover,
            risk_free_rate=0.02
        )

        # Create result
        result = BacktestResult(
            equity_curve=equity_curve,
            returns=strategy_returns,
            positions=shifted_signals,
            signals=signals,
            metrics=metrics,
            turnover=turnover,
            strategy_name=self.strategy.name,
            params=self.strategy.params,
            initial_capital=self.initial_capital,
            commission_bps=self.commission_bps,
            start_date=str(equity_curve.index[0].date()) if len(equity_curve) > 0 else None,
            end_date=str(equity_curve.index[-1].date()) if len(equity_curve) > 0 else None,
        )

        logger.info(f"Backtest complete: Sharpe={metrics['sharpe_ratio']:.2f}, "
                   f"Return={metrics['total_return']:.2%}")

        return result

    def _align_signals(self, signals: pd.DataFrame) -> pd.DataFrame:
        """Align signals with price data index"""
        # Ensure signals have same index as prices
        aligned = signals.reindex(self.prices.index)

        # Forward fill any missing signals
        aligned = aligned.ffill().fillna(0)

        # Normalize row weights so they sum to at most 1.0 in absolute terms.
        # This prevents leverage accumulation when strategies ffill without resetting
        # non-selected stocks (which causes weights to accumulate across rebalancing periods).
        row_sums = aligned.abs().sum(axis=1)
        needs_norm = row_sums > 1.001
        if needs_norm.any():
            aligned.loc[needs_norm] = aligned.loc[needs_norm].div(
                row_sums[needs_norm], axis=0
            )

        return aligned

    def _calculate_turnover(self, positions: Union[pd.DataFrame, pd.Series]) -> pd.Series:
        """
        Calculate portfolio turnover

        Turnover = sum(|position_change|) / 2
        (Divide by 2 because a trade involves both buy and sell)
        """
        if isinstance(positions, pd.Series):
            position_change = positions.diff().abs()
        else:
            position_change = positions.diff().abs().sum(axis=1)

        # Turnover is half of total position changes
        # (buying 100% and selling 100% = 100% turnover, not 200%)
        turnover = position_change / 2

        return turnover.fillna(0)


def run_backtest(
    strategy_name: str,
    data: pd.DataFrame,
    params: Optional[Dict[str, Any]] = None,
    initial_capital: float = 1_000_000,
    commission_bps: float = 10,
    slippage_bps: float = 5,
    symbol: Optional[str] = None,
) -> BacktestResult:
    """
    Convenience function to run a backtest

    Args:
        strategy_name: Name of strategy (from STRATEGY_REGISTRY)
        data: Price data
        params: Strategy parameters
        initial_capital: Starting capital
        commission_bps: Commission in basis points
        slippage_bps: Slippage in basis points
        symbol: Symbol for single-asset strategies

    Returns:
        BacktestResult

    Example:
        result = run_backtest(
            'sma_crossover',
            data,
            params={'fast': 50, 'slow': 200},
            symbol='AAPL'
        )
        print(result.summary())
    """
    from src.strategies import get_strategy

    # Add symbol to params for single-asset strategies
    if params is None:
        params = {}
    if symbol is not None:
        params['symbol'] = symbol

    # Create strategy
    strategy = get_strategy(strategy_name, data, params)

    # Create and run backtester
    backtester = Backtester(
        strategy=strategy,
        data=data,
        initial_capital=initial_capital,
        commission_bps=commission_bps,
        slippage_bps=slippage_bps,
    )

    return backtester.run()


def compare_strategies(
    strategy_results: Dict[str, BacktestResult],
) -> pd.DataFrame:
    """
    Compare multiple strategy backtest results

    Args:
        strategy_results: Dict mapping strategy names to BacktestResult

    Returns:
        DataFrame with metrics comparison
    """
    comparison = {}

    for name, result in strategy_results.items():
        comparison[name] = result.metrics

    df = pd.DataFrame(comparison).T

    # Sort by Sharpe ratio
    df = df.sort_values('sharpe_ratio', ascending=False)

    return df


if __name__ == "__main__":
    # Test the backtester
    import sys
    sys.path.insert(0, str(__file__).split('/src/')[0])

    # Configure logging
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), format="{message}\n", level="INFO")

    # Load sample data
    data = pd.read_parquet('data_processed/prices_clean.parquet')

    # Test single-asset strategy
    from src.strategies.trend import SMAStrategy

    # Get AAPL data
    aapl = data[data['symbol'] == 'AAPL'].copy()

    strategy = SMAStrategy(aapl, {'fast': 50, 'slow': 200})
    backtester = Backtester(strategy, aapl)
    result = backtester.run()

    print(result.summary())
