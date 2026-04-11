# StrategyHub Research - Project Context

## What This Is
Systematic trading strategy research and backtesting platform for S&P 500 stocks.

## Current Priority Order (Phase 2)
1. Deep backtesting methodology (walk-forward, out-of-sample, Monte Carlo)
2. Parameter sensitivity analysis for each strategy
3. Extend data to 2000-present (Yahoo Finance)
4. Strategy detail pages with interactive charts

## Architecture
- **Backend**: Python, FastAPI, SQLAlchemy (port 8000)
- **Frontend**: Next.js, React, Tailwind CSS (port 3000)
- **Data**: S&P 500 stocks, 2014-2017 (505 symbols, ~497K rows)
- **Database**: SQLite (backtest results, metrics, equity curves)

## 14 Strategies Implemented (all multi-asset, factor-based)
- Momentum: Large Cap Momentum, 52-Week High Breakout
- Value: Deep Value All-Cap
- Quality: High Quality ROIC
- Factor: Low Volatility Shield, Dividend Aristocrats
- Trend: Moving Average Trend
- Mean Reversion: RSI Mean Reversion (cross-sectional)
- Composite: Value+Momentum, Quality+Momentum, Quality+Low Vol, Composite Factor Score
- Risk Management: Volatility Targeting
- Event-Driven: Earnings Surprise Momentum

## Key Paths
- Backend API: `src/api/main.py`
- Strategies: `src/strategies/` (momentum, value, quality, factor, trend, mean_reversion, composite, risk_management, event)
- Backtester: `src/backtesting/engine.py`
- Frontend: `frontend/src/app/page.tsx`
- Data: `data_processed/prices_clean.parquet`
- Strategy Registry: `src/strategies/__init__.py`

## Commands
- Start backend: `source venv/bin/activate && uvicorn src.api.main:app --reload --port 8000`
- Start frontend: `cd frontend && npm run dev`
- Re-run backtests: `python scripts/run_all_backtests.py`
