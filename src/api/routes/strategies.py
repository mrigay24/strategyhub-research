"""
Strategy API Routes

Endpoints for managing strategies and querying available strategies.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from src.api.schemas import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    StrategyListResponse,
    AvailableStrategiesResponse,
    AvailableStrategyInfo,
    SuccessResponse,
)
from src.database.repository import StrategyRepository
from src.strategies import STRATEGY_REGISTRY

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("/available", response_model=AvailableStrategiesResponse)
async def get_available_strategies():
    """
    Get list of all available strategy implementations.

    These are the built-in strategies that can be used for backtesting.
    """
    strategies = []

    for name, strategy_class in STRATEGY_REGISTRY.items():
        # Create a temporary instance to get metadata
        info = AvailableStrategyInfo(
            name=name,
            class_name=strategy_class.__name__,
            strategy_type=strategy_class.DEFAULT_PARAMS.get('strategy_type', 'unknown')
                if hasattr(strategy_class, 'DEFAULT_PARAMS') else 'unknown',
            default_params=strategy_class.DEFAULT_PARAMS if hasattr(strategy_class, 'DEFAULT_PARAMS') else {},
            param_grid=None,  # Would need instance to get this
            description=strategy_class.__doc__.split('\n')[0].strip() if strategy_class.__doc__ else None,
        )
        strategies.append(info)

    return AvailableStrategiesResponse(
        strategies=strategies,
        total=len(strategies)
    )


@router.get("", response_model=StrategyListResponse)
async def list_strategies(
    strategy_type: Optional[str] = Query(None, description="Filter by type"),
    active_only: bool = Query(True, description="Only return active strategies"),
):
    """
    Get list of registered strategies from the database.

    These are strategies that have been registered for tracking backtest results.
    """
    repo = StrategyRepository()

    if strategy_type:
        strategies = repo.get_by_type(strategy_type)
    else:
        strategies = repo.get_all(active_only=active_only)

    return StrategyListResponse(
        strategies=[StrategyResponse(**s) for s in strategies],
        total=len(strategies)
    )


@router.post("", response_model=StrategyResponse, status_code=201)
async def create_strategy(strategy: StrategyCreate):
    """
    Register a new strategy in the database.

    This creates a record for tracking backtest results.
    """
    repo = StrategyRepository()

    # Check if strategy already exists
    existing = repo.get_by_name(strategy.name)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Strategy '{strategy.name}' already exists"
        )

    result = repo.create(
        name=strategy.name,
        strategy_type=strategy.strategy_type,
        description=strategy.description,
        default_params=strategy.default_params,
        param_grid=strategy.param_grid,
    )

    return StrategyResponse(**result)


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: int):
    """
    Get a specific strategy by ID.
    """
    repo = StrategyRepository()
    strategy = repo.get_by_id(strategy_id)

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    return StrategyResponse(**strategy)


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(strategy_id: int, update: StrategyUpdate):
    """
    Update a strategy's metadata.
    """
    repo = StrategyRepository()

    # Filter out None values
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = repo.update(strategy_id, **update_data)

    if not result:
        raise HTTPException(status_code=404, detail="Strategy not found")

    return StrategyResponse(**result)


@router.delete("/{strategy_id}", response_model=SuccessResponse)
async def delete_strategy(strategy_id: int):
    """
    Soft delete a strategy (marks as inactive).
    """
    repo = StrategyRepository()
    success = repo.delete(strategy_id)

    if not success:
        raise HTTPException(status_code=404, detail="Strategy not found")

    return SuccessResponse(message=f"Strategy {strategy_id} deleted")


@router.post("/register-all", response_model=SuccessResponse)
async def register_all_strategies():
    """
    Register all available built-in strategies in the database.

    This is a convenience endpoint to set up all strategies at once.
    """
    repo = StrategyRepository()
    registered = []

    strategy_type_map = {
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

    for name, strategy_class in STRATEGY_REGISTRY.items():
        strategy_type = strategy_type_map.get(name, 'other')

        result = repo.get_or_create(
            name=name,
            strategy_type=strategy_type,
            description=strategy_class.__doc__.split('\n')[0].strip() if strategy_class.__doc__ else None,
            default_params=strategy_class.DEFAULT_PARAMS if hasattr(strategy_class, 'DEFAULT_PARAMS') else {},
        )
        registered.append(result['name'])

    return SuccessResponse(
        message=f"Registered {len(registered)} strategies",
        data={'strategies': registered}
    )
