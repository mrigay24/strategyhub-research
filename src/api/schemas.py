"""
Pydantic Schemas for API Request/Response Models

Defines the data structures for API inputs and outputs.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# STRATEGY SCHEMAS
# =============================================================================

class StrategyBase(BaseModel):
    """Base schema for strategy data."""
    name: str = Field(..., description="Strategy name", min_length=1, max_length=100)
    strategy_type: str = Field(..., description="Strategy type: trend, momentum, mean_reversion, factor")
    description: Optional[str] = Field(None, description="Strategy description")
    default_params: Optional[Dict[str, Any]] = Field(None, description="Default parameters")
    param_grid: Optional[Dict[str, List]] = Field(None, description="Parameter grid for optimization")


class StrategyCreate(StrategyBase):
    """Schema for creating a new strategy."""
    pass


class StrategyUpdate(BaseModel):
    """Schema for updating a strategy."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    default_params: Optional[Dict[str, Any]] = None
    param_grid: Optional[Dict[str, List]] = None
    is_active: Optional[bool] = None


class StrategyResponse(StrategyBase):
    """Schema for strategy response."""
    id: int
    is_active: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StrategyListResponse(BaseModel):
    """Schema for list of strategies."""
    strategies: List[StrategyResponse]
    total: int


# =============================================================================
# BACKTEST SCHEMAS
# =============================================================================

class BacktestRequest(BaseModel):
    """Schema for running a backtest."""
    strategy_name: str = Field(..., description="Name of the strategy to run")
    symbol: Optional[str] = Field(None, description="Symbol for single-asset strategies (e.g., 'AAPL')")
    params: Optional[Dict[str, Any]] = Field(None, description="Strategy parameters (overrides defaults)")
    initial_capital: float = Field(1_000_000, description="Starting capital", gt=0)
    commission_bps: float = Field(10, description="Commission in basis points", ge=0)
    slippage_bps: float = Field(5, description="Slippage in basis points", ge=0)
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    save_to_db: bool = Field(True, description="Whether to save results to database")
    notes: Optional[str] = Field(None, description="Optional notes for this run")
    tags: Optional[List[str]] = Field(None, description="Optional tags")


class MetricsResponse(BaseModel):
    """Schema for backtest metrics."""
    total_return: Optional[float] = None
    cagr: Optional[float] = None
    volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    calmar_ratio: Optional[float] = None
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    var_95: Optional[float] = None
    cvar_95: Optional[float] = None

    class Config:
        from_attributes = True


class BacktestRunResponse(BaseModel):
    """Schema for backtest run response."""
    id: int
    strategy_id: int
    strategy_name: Optional[str] = None
    symbol: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_capital: float
    final_capital: Optional[float] = None
    commission_bps: float
    run_timestamp: Optional[datetime] = None
    status: str
    metrics: Optional[MetricsResponse] = None

    class Config:
        from_attributes = True


class BacktestResultResponse(BaseModel):
    """Schema for complete backtest result (includes equity curve)."""
    run: BacktestRunResponse
    metrics: MetricsResponse
    equity_curve: Optional[List[Dict[str, Any]]] = Field(None, description="List of {date, equity, drawdown}")


class BacktestListResponse(BaseModel):
    """Schema for list of backtest runs."""
    runs: List[BacktestRunResponse]
    total: int


class TopStrategiesResponse(BaseModel):
    """Schema for top performing strategies."""
    results: List[Dict[str, Any]]
    metric_used: str


class ComparisonResponse(BaseModel):
    """Schema for strategy comparison."""
    comparison: List[Dict[str, Any]]
    run_ids: List[int]


# =============================================================================
# EQUITY CURVE SCHEMAS
# =============================================================================

class EquityPointResponse(BaseModel):
    """Schema for single equity curve point."""
    date: datetime
    equity: float
    drawdown: Optional[float] = None


class EquityCurveResponse(BaseModel):
    """Schema for equity curve."""
    run_id: int
    points: List[EquityPointResponse]


# =============================================================================
# AVAILABLE STRATEGIES SCHEMAS
# =============================================================================

class AvailableStrategyInfo(BaseModel):
    """Schema for available strategy info."""
    name: str
    class_name: str
    strategy_type: str
    default_params: Dict[str, Any]
    param_grid: Optional[Dict[str, List]] = None
    description: Optional[str] = None


class AvailableStrategiesResponse(BaseModel):
    """Schema for list of available strategies."""
    strategies: List[AvailableStrategyInfo]
    total: int


# =============================================================================
# SYMBOLS SCHEMAS
# =============================================================================

class SymbolInfo(BaseModel):
    """Schema for symbol info."""
    symbol: str
    name: Optional[str] = None
    sector: Optional[str] = None
    data_start: Optional[str] = None
    data_end: Optional[str] = None
    num_rows: Optional[int] = None


class SymbolsResponse(BaseModel):
    """Schema for list of symbols."""
    symbols: List[SymbolInfo]
    total: int


# =============================================================================
# GENERAL SCHEMAS
# =============================================================================

class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str
    detail: Optional[str] = None


class SuccessResponse(BaseModel):
    """Schema for success responses."""
    message: str
    data: Optional[Dict[str, Any]] = None
