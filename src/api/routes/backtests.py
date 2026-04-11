"""
Backtest API Routes

Endpoints for running backtests and querying results.
"""

from typing import Optional, List
import pandas as pd
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from loguru import logger

from src.api.schemas import (
    BacktestRequest,
    BacktestRunResponse,
    BacktestResultResponse,
    BacktestListResponse,
    MetricsResponse,
    EquityCurveResponse,
    EquityPointResponse,
    TopStrategiesResponse,
    ComparisonResponse,
    SymbolsResponse,
    SymbolInfo,
    SuccessResponse,
    ErrorResponse,
)
from src.database.repository import StrategyRepository, BacktestRepository
from src.strategies import get_strategy, STRATEGY_REGISTRY
from src.backtesting.engine import Backtester

router = APIRouter(prefix="/backtests", tags=["backtests"])

# Cache for price data
_price_data_cache = None


def _get_price_data() -> pd.DataFrame:
    """Load and cache price data."""
    global _price_data_cache
    if _price_data_cache is None:
        _price_data_cache = pd.read_parquet('data_processed/extended_prices_clean.parquet')
    return _price_data_cache


@router.get("/symbols", response_model=SymbolsResponse)
async def get_available_symbols():
    """
    Get list of available symbols in the dataset.
    """
    data = _get_price_data()

    symbols_info = []
    for symbol in sorted(data['symbol'].unique()):
        symbol_data = data[data['symbol'] == symbol]
        symbols_info.append(SymbolInfo(
            symbol=symbol,
            data_start=str(symbol_data['date'].min().date()),
            data_end=str(symbol_data['date'].max().date()),
            num_rows=len(symbol_data),
        ))

    return SymbolsResponse(
        symbols=symbols_info,
        total=len(symbols_info)
    )


@router.post("/run", response_model=BacktestResultResponse)
async def run_backtest(request: BacktestRequest):
    """
    Run a backtest for a given strategy.

    This executes the backtest synchronously and returns the results.
    For long-running backtests, consider using the async endpoint.
    """
    # Validate strategy exists
    if request.strategy_name not in STRATEGY_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown strategy: {request.strategy_name}. "
                   f"Available: {list(STRATEGY_REGISTRY.keys())}"
        )

    # Load data
    data = _get_price_data()

    # Filter by symbol if specified
    if request.symbol:
        if request.symbol not in data['symbol'].unique():
            raise HTTPException(
                status_code=400,
                detail=f"Unknown symbol: {request.symbol}"
            )
        data = data[data['symbol'] == request.symbol].copy()

    # Filter by date range if specified
    if request.start_date:
        data = data[data['date'] >= request.start_date]
    if request.end_date:
        data = data[data['date'] <= request.end_date]

    if len(data) < 50:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient data: {len(data)} rows. Need at least 50."
        )

    # Build params
    params = request.params or {}
    if request.symbol:
        params['symbol'] = request.symbol

    try:
        # Create strategy
        strategy = get_strategy(request.strategy_name, data, params)

        # Run backtest
        backtester = Backtester(
            strategy=strategy,
            data=data,
            initial_capital=request.initial_capital,
            commission_bps=request.commission_bps,
            slippage_bps=request.slippage_bps,
        )
        result = backtester.run()

    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # Save to database if requested
    run_id = None
    if request.save_to_db:
        strategy_repo = StrategyRepository()
        backtest_repo = BacktestRepository()

        # Get or create strategy record
        strategy_record = strategy_repo.get_or_create(
            name=request.strategy_name,
            strategy_type=_get_strategy_type(request.strategy_name),
        )

        # Save result
        run_data = backtest_repo.save_backtest_result(
            strategy_id=strategy_record['id'],
            result=result,
            symbol=request.symbol,
            notes=request.notes,
            tags=request.tags,
        )
        run_id = run_data['id']

    # Build response
    metrics = MetricsResponse(
        total_return=result.metrics.get('total_return'),
        cagr=result.metrics.get('cagr'),
        volatility=result.metrics.get('volatility'),
        sharpe_ratio=result.metrics.get('sharpe_ratio'),
        sortino_ratio=result.metrics.get('sortino_ratio'),
        max_drawdown=result.metrics.get('max_drawdown'),
        calmar_ratio=result.metrics.get('calmar_ratio'),
        win_rate=result.metrics.get('win_rate'),
        profit_factor=result.metrics.get('profit_factor'),
        var_95=result.metrics.get('var_95'),
        cvar_95=result.metrics.get('cvar_95'),
    )

    run_response = BacktestRunResponse(
        id=run_id or 0,
        strategy_id=0,
        strategy_name=request.strategy_name,
        symbol=request.symbol,
        params=params,
        start_date=result.start_date,
        end_date=result.end_date,
        initial_capital=result.initial_capital,
        final_capital=float(result.equity_curve.iloc[-1]) if len(result.equity_curve) > 0 else None,
        commission_bps=result.commission_bps,
        status='completed',
        metrics=metrics,
    )

    # Sample equity curve for response (every 5th point)
    equity_curve = []
    step = max(1, len(result.equity_curve) // 200)  # Max 200 points
    for i in range(0, len(result.equity_curve), step):
        equity_curve.append({
            'date': str(result.equity_curve.index[i].date()),
            'equity': float(result.equity_curve.iloc[i]),
        })

    return BacktestResultResponse(
        run=run_response,
        metrics=metrics,
        equity_curve=equity_curve,
    )


@router.get("", response_model=BacktestListResponse)
async def list_backtests(
    strategy_id: Optional[int] = Query(None, description="Filter by strategy ID"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    limit: int = Query(50, description="Max results", le=100),
):
    """
    Get list of past backtest runs.
    """
    backtest_repo = BacktestRepository()

    if strategy_id:
        runs = backtest_repo.get_by_strategy(strategy_id, limit=limit, symbol=symbol)
    else:
        # Get all runs (would need a new method, for now just return empty)
        runs = []

    return BacktestListResponse(
        runs=[BacktestRunResponse(**r) for r in runs],
        total=len(runs)
    )


@router.get("/top", response_model=TopStrategiesResponse)
async def get_top_strategies(
    metric: str = Query("sharpe_ratio", description="Metric to rank by"),
    limit: int = Query(10, description="Number of results", le=50),
    min_return: Optional[float] = Query(None, description="Minimum total return filter"),
):
    """
    Get top performing backtest runs by a specified metric.

    Available metrics: sharpe_ratio, cagr, sortino_ratio, calmar_ratio, total_return
    """
    valid_metrics = ['sharpe_ratio', 'cagr', 'sortino_ratio', 'calmar_ratio', 'total_return', 'win_rate']
    if metric not in valid_metrics:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric. Choose from: {valid_metrics}"
        )

    backtest_repo = BacktestRepository()
    results = backtest_repo.get_top_strategies(
        metric=metric,
        limit=limit,
        min_return=min_return,
    )

    return TopStrategiesResponse(
        results=results,
        metric_used=metric
    )


@router.get("/dashboard")
async def get_dashboard_data():
    """
    Get all backtest results formatted for the dashboard.

    Returns strategies with their latest backtest metrics and equity curves,
    plus the market benchmark data.
    """
    from src.database.connection import session_scope
    from src.database.models import Strategy, BacktestRun, BacktestMetrics, EquityCurve
    from sqlalchemy import desc

    strategies_data = []
    benchmark_data = None

    with session_scope() as session:
        # Get all strategies (excluding benchmark)
        strategies = session.query(Strategy).filter(
            Strategy.is_active == True,
            Strategy.name != '_benchmark_'
        ).all()

        for strategy in strategies:
            # Get the latest backtest run for this strategy
            latest_run = session.query(BacktestRun).filter(
                BacktestRun.strategy_id == strategy.id
            ).order_by(desc(BacktestRun.run_timestamp)).first()

            if not latest_run:
                continue

            # Get metrics
            metrics = session.query(BacktestMetrics).filter(
                BacktestMetrics.backtest_run_id == latest_run.id
            ).first()

            if not metrics:
                continue

            # Get equity curve
            equity_points = session.query(EquityCurve).filter(
                EquityCurve.backtest_run_id == latest_run.id
            ).order_by(EquityCurve.date).all()

            equity_curve = [
                {'date': str(p.date.date()), 'equity': p.equity, 'drawdown': p.drawdown}
                for p in equity_points
            ]

            strategies_data.append({
                'id': strategy.id,
                'name': strategy.name,
                'strategy_type': strategy.strategy_type,
                'description': strategy.description,
                'symbol': latest_run.symbol,
                'run_id': latest_run.id,
                'start_date': str(latest_run.start_date.date()) if latest_run.start_date else None,
                'end_date': str(latest_run.end_date.date()) if latest_run.end_date else None,
                'initial_capital': latest_run.initial_capital,
                'final_capital': latest_run.final_capital,
                'metrics': {
                    'total_return': metrics.total_return,
                    'cagr': metrics.cagr,
                    'volatility': metrics.volatility,
                    'sharpe_ratio': metrics.sharpe_ratio,
                    'sortino_ratio': metrics.sortino_ratio,
                    'max_drawdown': metrics.max_drawdown,
                    'calmar_ratio': metrics.calmar_ratio,
                    'win_rate': metrics.win_rate,
                    'profit_factor': metrics.profit_factor,
                },
                'equity_curve': equity_curve,
            })

        # Get benchmark data
        benchmark_strategy = session.query(Strategy).filter(
            Strategy.name == '_benchmark_'
        ).first()

        if benchmark_strategy:
            benchmark_run = session.query(BacktestRun).filter(
                BacktestRun.strategy_id == benchmark_strategy.id
            ).first()

            if benchmark_run:
                benchmark_metrics = session.query(BacktestMetrics).filter(
                    BacktestMetrics.backtest_run_id == benchmark_run.id
                ).first()

                benchmark_equity = session.query(EquityCurve).filter(
                    EquityCurve.backtest_run_id == benchmark_run.id
                ).order_by(EquityCurve.date).all()

                benchmark_data = {
                    'name': 'S&P 500 Proxy (Equal-Weighted)',
                    'symbol': benchmark_run.symbol,
                    'start_date': str(benchmark_run.start_date.date()) if benchmark_run.start_date else None,
                    'end_date': str(benchmark_run.end_date.date()) if benchmark_run.end_date else None,
                    'initial_capital': benchmark_run.initial_capital,
                    'final_capital': benchmark_run.final_capital,
                    'metrics': {
                        'total_return': benchmark_metrics.total_return if benchmark_metrics else None,
                        'cagr': benchmark_metrics.cagr if benchmark_metrics else None,
                        'volatility': benchmark_metrics.volatility if benchmark_metrics else None,
                        'sharpe_ratio': benchmark_metrics.sharpe_ratio if benchmark_metrics else None,
                        'max_drawdown': benchmark_metrics.max_drawdown if benchmark_metrics else None,
                    },
                    'equity_curve': [
                        {'date': str(p.date.date()), 'equity': p.equity}
                        for p in benchmark_equity
                    ],
                }

    return {
        'strategies': strategies_data,
        'benchmark': benchmark_data,
        'total_strategies': len(strategies_data),
    }


@router.get("/{run_id}", response_model=BacktestResultResponse)
async def get_backtest(run_id: int):
    """
    Get details of a specific backtest run.
    """
    backtest_repo = BacktestRepository()

    run = backtest_repo.get_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Backtest run not found")

    metrics_data = backtest_repo.get_metrics(run_id)
    equity_df = backtest_repo.get_equity_curve(run_id)

    metrics = MetricsResponse(**metrics_data) if metrics_data else MetricsResponse()

    run_response = BacktestRunResponse(
        **run,
        metrics=metrics
    )

    # Convert equity curve to list
    equity_curve = []
    if not equity_df.empty:
        for date, row in equity_df.iterrows():
            equity_curve.append({
                'date': str(date.date()) if hasattr(date, 'date') else str(date),
                'equity': row['equity'],
                'drawdown': row.get('drawdown'),
            })

    return BacktestResultResponse(
        run=run_response,
        metrics=metrics,
        equity_curve=equity_curve,
    )


@router.get("/{run_id}/equity", response_model=EquityCurveResponse)
async def get_equity_curve(run_id: int):
    """
    Get the equity curve for a backtest run.
    """
    backtest_repo = BacktestRepository()
    equity_df = backtest_repo.get_equity_curve(run_id)

    if equity_df.empty:
        raise HTTPException(status_code=404, detail="Equity curve not found")

    points = []
    for date, row in equity_df.iterrows():
        points.append(EquityPointResponse(
            date=date,
            equity=row['equity'],
            drawdown=row.get('drawdown'),
        ))

    return EquityCurveResponse(run_id=run_id, points=points)


@router.post("/compare", response_model=ComparisonResponse)
async def compare_backtests(run_ids: List[int]):
    """
    Compare metrics across multiple backtest runs.
    """
    if len(run_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 runs to compare")
    if len(run_ids) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 runs for comparison")

    backtest_repo = BacktestRepository()
    comparison_df = backtest_repo.compare_runs(run_ids)

    if comparison_df.empty:
        raise HTTPException(status_code=404, detail="No valid runs found")

    return ComparisonResponse(
        comparison=comparison_df.to_dict('records'),
        run_ids=run_ids
    )


@router.delete("/{run_id}", response_model=SuccessResponse)
async def delete_backtest(run_id: int):
    """
    Delete a backtest run and all associated data.
    """
    backtest_repo = BacktestRepository()
    success = backtest_repo.delete_run(run_id)

    if not success:
        raise HTTPException(status_code=404, detail="Backtest run not found")

    return SuccessResponse(message=f"Backtest run {run_id} deleted")


def _get_strategy_type(strategy_name: str) -> str:
    """Get strategy type from strategy name."""
    type_map = {
        'large_cap_momentum': 'momentum',
        '52_week_high_breakout': 'momentum',
        'deep_value_all_cap': 'value',
        'high_quality_roic': 'quality',
        'low_volatility_shield': 'factor',
        'dividend_aristocrats': 'factor',
        'moving_average_trend': 'trend',
        'rsi_mean_reversion': 'mean_reversion',
        'value_momentum_blend': 'composite',
        'quality_momentum': 'composite',
        'quality_low_vol': 'composite',
        'composite_factor_score': 'multi_factor',
        'volatility_targeting': 'risk_management',
        'earnings_surprise_momentum': 'event',
    }
    return type_map.get(strategy_name, 'other')
