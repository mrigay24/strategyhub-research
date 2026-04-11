"""
FastAPI Main Application

REST API for the StrategyHub trading research platform.
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api.routes.strategies import router as strategies_router
from src.api.routes.backtests import router as backtests_router
from src.api.routes.research import router as research_router
from src.api.routes.ai_builder import router as ai_builder_router
from src.database.connection import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.

    Initializes database on startup and closes connections on shutdown.
    """
    # Startup
    logger.info("Starting StrategyHub API...")
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down StrategyHub API...")
    close_db()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title="StrategyHub Research API",
    description="""
    REST API for systematic trading strategy research platform.

    ## Features

    - **Strategies**: Register and manage trading strategies
    - **Backtests**: Run backtests and analyze results
    - **Metrics**: Compare performance across strategies

    ## Quick Start

    1. Get available strategies: `GET /strategies/available`
    2. Run a backtest: `POST /backtests/run`
    3. View results: `GET /backtests/{run_id}`

    ## Available Strategies

    - **Trend Following**: SMA Crossover, EMA Crossover, TSMOM
    - **Momentum**: Cross-Sectional Momentum, Short-Term Reversion
    - **Mean Reversion**: RSI, Bollinger Bands, Donchian Breakout
    - **Factor**: Pairs Trading, Low Volatility, Min Variance
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


# Include routers
app.include_router(strategies_router, prefix="/api/v1")
app.include_router(backtests_router, prefix="/api/v1")
app.include_router(research_router, prefix="/api/v1")
app.include_router(ai_builder_router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint - API health check.
    """
    return {
        "name": "StrategyHub Research API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}


@app.get("/api/v1")
async def api_info():
    """
    API version info.
    """
    return {
        "version": "1.0.0",
        "endpoints": {
            "strategies": "/api/v1/strategies",
            "backtests": "/api/v1/backtests",
        }
    }


if __name__ == "__main__":
    import uvicorn

    # Configure logging
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO"
    )

    # Run server
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
