"""
Repository Layer

Provides high-level data access methods for strategies and backtests.
Implements the Repository pattern for clean separation of concerns.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np

from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from loguru import logger

from src.database.models import (
    Strategy,
    BacktestRun,
    BacktestMetrics,
    EquityCurve,
    Trade,
)
from src.database.connection import session_scope


def _convert_numpy_types(obj: Any) -> Any:
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_numpy_types(v) for v in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return obj.to_pydatetime()
    return obj


class StrategyRepository:
    """
    Repository for Strategy entities.

    Handles CRUD operations and queries for strategies.
    """

    def __init__(self, session: Session = None):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session. If None, creates new sessions as needed.
        """
        self._session = session

    def _get_session(self) -> Session:
        """Get session, creating one if needed."""
        if self._session is not None:
            return self._session
        from src.database.connection import get_session
        return get_session()

    def create(
        self,
        name: str,
        strategy_type: str,
        description: str = None,
        default_params: Dict[str, Any] = None,
        param_grid: Dict[str, List] = None,
    ) -> Dict[str, Any]:
        """
        Create a new strategy.

        Args:
            name: Strategy name
            strategy_type: Type (trend, momentum, mean_reversion, factor)
            description: Strategy description
            default_params: Default parameters
            param_grid: Parameter grid for optimization

        Returns:
            Dictionary with strategy data
        """
        strategy = Strategy(
            name=name,
            strategy_type=strategy_type,
            description=description,
            default_params=_convert_numpy_types(default_params),
            param_grid=_convert_numpy_types(param_grid),
        )

        with session_scope() as session:
            session.add(strategy)
            session.flush()
            strategy_id = strategy.id
            result = strategy.to_dict()
            logger.info(f"Created strategy: {name} (id={strategy_id})")

        return result

    def get_by_id(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        """Get strategy by ID."""
        with session_scope() as session:
            strategy = session.query(Strategy).filter(Strategy.id == strategy_id).first()
            return strategy.to_dict() if strategy else None

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get strategy by name."""
        with session_scope() as session:
            strategy = session.query(Strategy).filter(Strategy.name == name).first()
            return strategy.to_dict() if strategy else None

    def get_all(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all strategies."""
        with session_scope() as session:
            query = session.query(Strategy)
            if active_only:
                query = query.filter(Strategy.is_active == True)
            strategies = query.order_by(Strategy.name).all()
            return [s.to_dict() for s in strategies]

    def get_by_type(self, strategy_type: str) -> List[Dict[str, Any]]:
        """Get strategies by type."""
        with session_scope() as session:
            strategies = session.query(Strategy).filter(
                Strategy.strategy_type == strategy_type,
                Strategy.is_active == True
            ).all()
            return [s.to_dict() for s in strategies]

    def update(self, strategy_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        """Update strategy fields."""
        with session_scope() as session:
            strategy = session.query(Strategy).filter(Strategy.id == strategy_id).first()
            if strategy is None:
                return None

            for key, value in kwargs.items():
                if hasattr(strategy, key):
                    if key in ('default_params', 'param_grid'):
                        value = _convert_numpy_types(value)
                    setattr(strategy, key, value)

            strategy.updated_at = datetime.utcnow()
            logger.info(f"Updated strategy {strategy_id}")

        return self.get_by_id(strategy_id)

    def delete(self, strategy_id: int) -> bool:
        """Soft delete strategy (set is_active=False)."""
        with session_scope() as session:
            strategy = session.query(Strategy).filter(Strategy.id == strategy_id).first()
            if strategy is None:
                return False

            strategy.is_active = False
            strategy.updated_at = datetime.utcnow()
            logger.info(f"Deleted strategy {strategy_id}")
            return True

    def get_or_create(
        self,
        name: str,
        strategy_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get existing strategy or create new one.

        Args:
            name: Strategy name
            strategy_type: Strategy type
            **kwargs: Additional fields for creation

        Returns:
            Dictionary with strategy data
        """
        existing = self.get_by_name(name)
        if existing:
            return existing
        return self.create(name, strategy_type, **kwargs)


class BacktestRepository:
    """
    Repository for BacktestRun entities.

    Handles CRUD operations and queries for backtest runs and their results.
    """

    def __init__(self, session: Session = None):
        """Initialize repository."""
        self._session = session

    def save_backtest_result(
        self,
        strategy_id: int,
        result,  # BacktestResult from engine
        symbol: str = None,
        notes: str = None,
        tags: List[str] = None,
        save_equity_curve: bool = True,
        equity_sample_freq: str = 'W',  # Weekly sampling
    ) -> Dict[str, Any]:
        """
        Save a complete backtest result to the database.

        Args:
            strategy_id: ID of the strategy
            result: BacktestResult from backtester
            symbol: Symbol for single-asset strategies
            notes: Optional notes
            tags: Optional tags
            save_equity_curve: Whether to save equity curve data
            equity_sample_freq: Sampling frequency for equity curve ('D', 'W', 'M')

        Returns:
            Dictionary with backtest run data
        """
        with session_scope() as session:
            # Create backtest run
            run = BacktestRun(
                strategy_id=strategy_id,
                params=_convert_numpy_types(result.params),
                symbol=symbol or result.params.get('symbol'),
                start_date=pd.Timestamp(result.start_date).to_pydatetime() if result.start_date else None,
                end_date=pd.Timestamp(result.end_date).to_pydatetime() if result.end_date else None,
                initial_capital=result.initial_capital,
                final_capital=float(result.equity_curve.iloc[-1]) if len(result.equity_curve) > 0 else None,
                commission_bps=result.commission_bps,
                status='completed',
                notes=notes,
                tags=tags,
            )
            session.add(run)
            session.flush()

            # Create metrics
            metrics = BacktestMetrics.from_metrics_dict(
                backtest_run_id=run.id,
                metrics=_convert_numpy_types(result.metrics)
            )
            session.add(metrics)

            # Save equity curve (sampled)
            if save_equity_curve and len(result.equity_curve) > 0:
                equity_df = result.equity_curve.to_frame('equity')

                # Sample at specified frequency
                if equity_sample_freq != 'D':
                    equity_df = equity_df.resample(equity_sample_freq).last()

                # Calculate drawdown
                running_max = equity_df['equity'].expanding().max()
                equity_df['drawdown'] = equity_df['equity'] / running_max - 1

                for date, row in equity_df.iterrows():
                    point = EquityCurve(
                        backtest_run_id=run.id,
                        date=date.to_pydatetime() if hasattr(date, 'to_pydatetime') else date,
                        equity=float(row['equity']),
                        drawdown=float(row['drawdown']),
                    )
                    session.add(point)

            run_id = run.id
            run_dict = run.to_dict()
            logger.info(f"Saved backtest run {run_id} for strategy {strategy_id}")

        return run_dict

    def get_by_id(self, run_id: int) -> Optional[Dict[str, Any]]:
        """Get backtest run by ID."""
        with session_scope() as session:
            run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
            return run.to_dict() if run else None

    def get_by_strategy(
        self,
        strategy_id: int,
        limit: int = None,
        symbol: str = None
    ) -> List[Dict[str, Any]]:
        """Get backtest runs for a strategy."""
        with session_scope() as session:
            query = session.query(BacktestRun).filter(
                BacktestRun.strategy_id == strategy_id
            )

            if symbol:
                query = query.filter(BacktestRun.symbol == symbol)

            query = query.order_by(desc(BacktestRun.run_timestamp))

            if limit:
                query = query.limit(limit)

            runs = query.all()
            return [r.to_dict() for r in runs]

    def get_metrics(self, run_id: int) -> Optional[Dict[str, Any]]:
        """Get metrics for a backtest run."""
        with session_scope() as session:
            metrics = session.query(BacktestMetrics).filter(
                BacktestMetrics.backtest_run_id == run_id
            ).first()
            return metrics.to_dict() if metrics else None

    def get_equity_curve(self, run_id: int) -> pd.DataFrame:
        """Get equity curve as DataFrame."""
        with session_scope() as session:
            points = session.query(EquityCurve).filter(
                EquityCurve.backtest_run_id == run_id
            ).order_by(EquityCurve.date).all()

            if not points:
                return pd.DataFrame()

            data = {
                'date': [p.date for p in points],
                'equity': [p.equity for p in points],
                'drawdown': [p.drawdown for p in points],
            }
            df = pd.DataFrame(data)
            df.set_index('date', inplace=True)
            return df

    def get_top_strategies(
        self,
        metric: str = 'sharpe_ratio',
        limit: int = 10,
        min_return: float = None,
    ) -> List[Dict[str, Any]]:
        """
        Get top performing backtest runs by a metric.

        Args:
            metric: Metric to sort by (sharpe_ratio, cagr, etc.)
            limit: Number of results
            min_return: Minimum total return filter

        Returns:
            List of dictionaries with strategy and metrics info
        """
        with session_scope() as session:
            query = session.query(
                BacktestRun,
                BacktestMetrics
            ).join(
                BacktestMetrics,
                BacktestRun.id == BacktestMetrics.backtest_run_id
            ).join(
                Strategy,
                BacktestRun.strategy_id == Strategy.id
            )

            if min_return is not None:
                query = query.filter(BacktestMetrics.total_return >= min_return)

            # Sort by metric
            metric_col = getattr(BacktestMetrics, metric, BacktestMetrics.sharpe_ratio)
            query = query.order_by(desc(metric_col)).limit(limit)

            results = []
            for run, metrics in query.all():
                results.append({
                    'run_id': run.id,
                    'strategy_id': run.strategy_id,
                    'strategy_name': run.strategy.name if run.strategy else None,
                    'symbol': run.symbol,
                    'params': run.params,
                    'sharpe_ratio': metrics.sharpe_ratio,
                    'cagr': metrics.cagr,
                    'max_drawdown': metrics.max_drawdown,
                    'total_return': metrics.total_return,
                    'run_timestamp': run.run_timestamp,
                })

            return results

    def compare_runs(self, run_ids: List[int]) -> pd.DataFrame:
        """
        Compare metrics across multiple backtest runs.

        Args:
            run_ids: List of backtest run IDs

        Returns:
            DataFrame with metrics comparison
        """
        with session_scope() as session:
            results = []

            for run_id in run_ids:
                run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
                if run is None:
                    continue

                metrics = session.query(BacktestMetrics).filter(
                    BacktestMetrics.backtest_run_id == run_id
                ).first()

                if metrics is None:
                    continue

                results.append({
                    'run_id': run_id,
                    'strategy': run.strategy.name if run.strategy else None,
                    'symbol': run.symbol,
                    'total_return': metrics.total_return,
                    'cagr': metrics.cagr,
                    'volatility': metrics.volatility,
                    'sharpe_ratio': metrics.sharpe_ratio,
                    'sortino_ratio': metrics.sortino_ratio,
                    'max_drawdown': metrics.max_drawdown,
                    'calmar_ratio': metrics.calmar_ratio,
                    'win_rate': metrics.win_rate,
                })

            return pd.DataFrame(results)

    def delete_run(self, run_id: int) -> bool:
        """Delete a backtest run and all related data."""
        with session_scope() as session:
            run = session.query(BacktestRun).filter(BacktestRun.id == run_id).first()
            if run is None:
                return False

            session.delete(run)
            logger.info(f"Deleted backtest run {run_id}")
            return True

    def get_run_count_by_strategy(self) -> Dict[int, int]:
        """Get count of runs for each strategy."""
        with session_scope() as session:
            results = session.query(
                BacktestRun.strategy_id,
                func.count(BacktestRun.id)
            ).group_by(BacktestRun.strategy_id).all()

            return {strategy_id: count for strategy_id, count in results}


if __name__ == '__main__':
    # Test repositories
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from src.database.connection import init_db, reset_db

    # Configure logging
    logger.remove()
    logger.add(lambda msg: print(msg, end=''), format='{message}\n', level='INFO')

    # Reset database for clean test
    reset_db()

    # Test strategy repository
    print("\n--- Testing StrategyRepository ---")
    strategy_repo = StrategyRepository()

    # Create strategies
    sma = strategy_repo.create(
        name='SMA Crossover',
        strategy_type='trend',
        description='Simple moving average crossover strategy',
        default_params={'fast': 20, 'slow': 100},
        param_grid={'fast': [10, 20, 50], 'slow': [100, 150, 200]}
    )
    print(f"Created: {sma}")

    rsi = strategy_repo.create(
        name='RSI Mean Reversion',
        strategy_type='mean_reversion',
        description='RSI-based mean reversion',
        default_params={'period': 14, 'oversold': 30, 'overbought': 70}
    )
    print(f"Created: {rsi}")

    # Query strategies
    print(f"\nAll strategies: {strategy_repo.get_all()}")
    print(f"Trend strategies: {strategy_repo.get_by_type('trend')}")

    # Test backtest repository
    print("\n--- Testing BacktestRepository ---")
    backtest_repo = BacktestRepository()

    # We would normally save a real backtest result here
    # For now, just verify the repository methods exist
    print(f"BacktestRepository methods: {[m for m in dir(backtest_repo) if not m.startswith('_')]}")

    print("\nDatabase test completed!")
