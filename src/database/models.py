"""
Database Models

SQLAlchemy ORM models for the trading research platform.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import json

from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Strategy(Base):
    """
    Strategy definition and metadata.

    Stores the strategy type, parameters, and description.
    A strategy can have multiple backtest runs.
    """
    __tablename__ = 'strategies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    strategy_type = Column(String(50), nullable=False)  # trend, momentum, mean_reversion, factor
    description = Column(Text, nullable=True)

    # Parameters stored as JSON
    default_params = Column(JSON, nullable=True)
    param_grid = Column(JSON, nullable=True)  # For optimization

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    backtest_runs = relationship('BacktestRun', back_populates='strategy', cascade='all, delete-orphan')

    # Indexes
    __table_args__ = (
        Index('idx_strategy_name', 'name'),
        Index('idx_strategy_type', 'strategy_type'),
    )

    def __repr__(self) -> str:
        return f"<Strategy(id={self.id}, name='{self.name}', type='{self.strategy_type}')>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'strategy_type': self.strategy_type,
            'description': self.description,
            'default_params': self.default_params,
            'param_grid': self.param_grid,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
        }


class BacktestRun(Base):
    """
    Individual backtest execution.

    Records the specific parameters used, time period,
    and links to metrics and equity curve.
    """
    __tablename__ = 'backtest_runs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, ForeignKey('strategies.id'), nullable=False)

    # Run configuration
    params = Column(JSON, nullable=True)  # Actual params used
    symbol = Column(String(20), nullable=True)  # For single-asset strategies

    # Time period
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    # Capital and costs
    initial_capital = Column(Float, default=1_000_000)
    final_capital = Column(Float, nullable=True)
    commission_bps = Column(Float, default=10)
    slippage_bps = Column(Float, default=5)

    # Run metadata
    run_timestamp = Column(DateTime, default=datetime.utcnow)
    run_duration_seconds = Column(Float, nullable=True)
    status = Column(String(20), default='completed')  # completed, failed, running
    error_message = Column(Text, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # ['optimization', 'final', etc.]

    # Relationships
    strategy = relationship('Strategy', back_populates='backtest_runs')
    metrics = relationship('BacktestMetrics', back_populates='backtest_run', uselist=False, cascade='all, delete-orphan')
    equity_curve = relationship('EquityCurve', back_populates='backtest_run', cascade='all, delete-orphan')
    trades = relationship('Trade', back_populates='backtest_run', cascade='all, delete-orphan')

    # Indexes
    __table_args__ = (
        Index('idx_backtest_strategy', 'strategy_id'),
        Index('idx_backtest_symbol', 'symbol'),
        Index('idx_backtest_timestamp', 'run_timestamp'),
    )

    def __repr__(self) -> str:
        return f"<BacktestRun(id={self.id}, strategy_id={self.strategy_id}, symbol='{self.symbol}')>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'strategy_id': self.strategy_id,
            'params': self.params,
            'symbol': self.symbol,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'initial_capital': self.initial_capital,
            'final_capital': self.final_capital,
            'commission_bps': self.commission_bps,
            'run_timestamp': self.run_timestamp.isoformat() if self.run_timestamp else None,
            'status': self.status,
        }


class BacktestMetrics(Base):
    """
    Performance metrics for a backtest run.

    Stores all calculated metrics for easy querying and comparison.
    """
    __tablename__ = 'backtest_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    backtest_run_id = Column(Integer, ForeignKey('backtest_runs.id'), nullable=False, unique=True)

    # Return metrics
    total_return = Column(Float, nullable=True)
    cagr = Column(Float, nullable=True)

    # Risk metrics
    volatility = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    var_95 = Column(Float, nullable=True)
    cvar_95 = Column(Float, nullable=True)

    # Risk-adjusted metrics
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    calmar_ratio = Column(Float, nullable=True)

    # Trade metrics
    win_rate = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)
    avg_win = Column(Float, nullable=True)
    avg_loss = Column(Float, nullable=True)
    win_loss_ratio = Column(Float, nullable=True)

    # Distribution metrics
    skewness = Column(Float, nullable=True)
    kurtosis = Column(Float, nullable=True)
    best_day = Column(Float, nullable=True)
    worst_day = Column(Float, nullable=True)

    # Turnover
    avg_turnover = Column(Float, nullable=True)
    total_turnover = Column(Float, nullable=True)

    # All metrics as JSON (for flexibility)
    all_metrics = Column(JSON, nullable=True)

    # Relationship
    backtest_run = relationship('BacktestRun', back_populates='metrics')

    # Indexes for common queries
    __table_args__ = (
        Index('idx_metrics_sharpe', 'sharpe_ratio'),
        Index('idx_metrics_cagr', 'cagr'),
        Index('idx_metrics_drawdown', 'max_drawdown'),
    )

    def __repr__(self) -> str:
        return f"<BacktestMetrics(id={self.id}, sharpe={self.sharpe_ratio:.2f})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_return': self.total_return,
            'cagr': self.cagr,
            'volatility': self.volatility,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'calmar_ratio': self.calmar_ratio,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'var_95': self.var_95,
            'cvar_95': self.cvar_95,
        }

    @classmethod
    def from_metrics_dict(cls, backtest_run_id: int, metrics: Dict[str, float]) -> 'BacktestMetrics':
        """Create BacktestMetrics from a metrics dictionary."""
        return cls(
            backtest_run_id=backtest_run_id,
            total_return=metrics.get('total_return'),
            cagr=metrics.get('cagr'),
            volatility=metrics.get('volatility'),
            max_drawdown=metrics.get('max_drawdown'),
            var_95=metrics.get('var_95'),
            cvar_95=metrics.get('cvar_95'),
            sharpe_ratio=metrics.get('sharpe_ratio'),
            sortino_ratio=metrics.get('sortino_ratio'),
            calmar_ratio=metrics.get('calmar_ratio'),
            win_rate=metrics.get('win_rate'),
            profit_factor=metrics.get('profit_factor'),
            avg_win=metrics.get('avg_win'),
            avg_loss=metrics.get('avg_loss'),
            win_loss_ratio=metrics.get('win_loss_ratio'),
            skewness=metrics.get('skewness'),
            kurtosis=metrics.get('kurtosis'),
            best_day=metrics.get('best_day'),
            worst_day=metrics.get('worst_day'),
            avg_turnover=metrics.get('avg_turnover'),
            total_turnover=metrics.get('total_turnover'),
            all_metrics=metrics,
        )


class EquityCurve(Base):
    """
    Equity curve data points.

    Stores the daily equity values for visualization and analysis.
    Only stores sampled points to save space (e.g., weekly or end-of-month).
    """
    __tablename__ = 'equity_curves'

    id = Column(Integer, primary_key=True, autoincrement=True)
    backtest_run_id = Column(Integer, ForeignKey('backtest_runs.id'), nullable=False)

    date = Column(DateTime, nullable=False)
    equity = Column(Float, nullable=False)
    drawdown = Column(Float, nullable=True)  # Current drawdown at this point
    position = Column(Float, nullable=True)  # Current position (-1 to 1)

    # Relationship
    backtest_run = relationship('BacktestRun', back_populates='equity_curve')

    # Indexes
    __table_args__ = (
        Index('idx_equity_run_date', 'backtest_run_id', 'date'),
    )

    def __repr__(self) -> str:
        return f"<EquityCurve(date={self.date}, equity={self.equity:.2f})>"


class Trade(Base):
    """
    Individual trade records.

    For strategies that generate discrete trades, this stores
    entry/exit information for analysis.
    """
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    backtest_run_id = Column(Integer, ForeignKey('backtest_runs.id'), nullable=False)

    symbol = Column(String(20), nullable=True)

    # Entry
    entry_date = Column(DateTime, nullable=False)
    entry_price = Column(Float, nullable=False)
    entry_signal = Column(Float, nullable=True)  # Signal strength at entry

    # Exit
    exit_date = Column(DateTime, nullable=True)
    exit_price = Column(Float, nullable=True)
    exit_signal = Column(Float, nullable=True)

    # Position
    direction = Column(String(10), nullable=False)  # 'long' or 'short'
    size = Column(Float, default=1.0)  # Position size (fraction of portfolio)

    # Results
    pnl = Column(Float, nullable=True)  # Profit/Loss
    pnl_pct = Column(Float, nullable=True)  # PnL as percentage
    holding_days = Column(Integer, nullable=True)

    # Relationship
    backtest_run = relationship('BacktestRun', back_populates='trades')

    # Indexes
    __table_args__ = (
        Index('idx_trade_run', 'backtest_run_id'),
        Index('idx_trade_symbol', 'symbol'),
        Index('idx_trade_entry', 'entry_date'),
    )

    def __repr__(self) -> str:
        return f"<Trade(symbol='{self.symbol}', direction='{self.direction}', pnl={self.pnl})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'direction': self.direction,
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'entry_price': self.entry_price,
            'exit_date': self.exit_date.isoformat() if self.exit_date else None,
            'exit_price': self.exit_price,
            'pnl': self.pnl,
            'pnl_pct': self.pnl_pct,
            'holding_days': self.holding_days,
        }
