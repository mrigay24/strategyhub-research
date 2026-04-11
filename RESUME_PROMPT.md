# RESUME PROMPT - StrategyHub Research

> **Created:** 2026-02-25
> **Purpose:** Handoff document for fresh Claude Code session
> **Owner:** Mrigay Pathak

---

## CRITICAL CONTEXT FOR NEW SESSION

This document contains everything needed to continue development of the StrategyHub Research trading platform. Read this FIRST before doing anything.

---

## 1. PROJECT OVERVIEW

**StrategyHub Research** is a systematic trading strategy research platform with:
- Python backend (FastAPI) on port 8000
- Next.js frontend dashboard on port 3000
- SQLite database with SQLAlchemy ORM
- S&P 500 historical data (currently 2014-2017 only)
- Vectorized backtesting engine with transaction costs

### Quick Start Commands
```bash
# Start backend
cd /Users/mrigaypathak/Desktop/trading\ app/strategyhub-research
python -m uvicorn src.api.main:app --reload --port 8000

# Start frontend (in separate terminal)
cd frontend
npm run dev
```

---

## 2. THE PROBLEM - WRONG STRATEGIES IMPLEMENTED

### What Currently Exists (WRONG)
The codebase has these 14 generic strategies:
1. sma_crossover
2. ema_crossover
3. tsmom (BUGGY - shows astronomical numbers like 1.65e+35%)
4. cross_sectional_momentum
5. short_term_reversion
6. rsi
7. bollinger_bands
8. donchian_breakout
9. volatility_breakout
10. pairs_trading
11. low_volatility
12. quality_factor (placeholder)
13. value_factor (placeholder)
14. min_variance

### What User Actually Wanted (CORRECT - IMPLEMENT THESE)

The user's original request was for these 14 specific strategies:

| # | Strategy Name | Type | Description |
|---|---------------|------|-------------|
| 1 | **Large Cap Momentum** | Momentum | Top decile momentum in large caps |
| 2 | **Deep Value All-Cap** | Value | Low P/E, P/B, P/S across market caps |
| 3 | **High Quality ROIC** | Quality | High return on invested capital |
| 4 | **Low Volatility Shield** | Factor | Lowest volatility quintile |
| 5 | **Dividend Aristocrats** | Income | Consistent dividend growers |
| 6 | **Moving Average Trend** | Trend | Price above moving average |
| 7 | **RSI Mean Reversion** | Mean Reversion | Buy oversold, sell overbought |
| 8 | **52-Week High Breakout** | Breakout | Near 52-week high momentum |
| 9 | **Value + Momentum Blend** | Composite | Combine value and momentum |
| 10 | **Quality + Momentum** | Composite | Combine quality and momentum |
| 11 | **Quality + Low Volatility** | Composite | Combine quality and low vol |
| 12 | **Composite Factor Score** | Multi-Factor | All factors combined |
| 13 | **Volatility Targeting** | Risk Management | Adjust position by volatility |
| 14 | **Earnings Surprise Momentum** | Event | Post-earnings drift |

---

## 3. KNOWN BUGS TO FIX

1. **TSMOM Strategy Bug**: Shows astronomical returns (1.65e+35%), clearly broken calculation
2. **Duplicate Entries**: Two SMA Crossover showing in dashboard
3. **Dashboard Shows 12 Strategies**: Should show 14 (or the correct 14 above)

---

## 4. DATA REQUIREMENTS

### Current Data (INSUFFICIENT)
- Source: Kaggle S&P 500
- Period: 2014-01-02 to 2017-12-29 (only 4 years)
- Location: `data_processed/prices_clean.parquet`

### Required Data (TO DO)
1. **Extended US Data**: 2000-present from Yahoo Finance
   - Need to cover recession (2008), recovery, COVID crash, etc.
   - Should have 25+ years of market history

2. **Indian Market Data** (future):
   - NSE Nifty 50
   - BSE Sensex

### Data Download Approach
```python
# Use yfinance for S&P 500 constituents
import yfinance as yf

# Get historical S&P 500 list (point-in-time to avoid survivorship bias)
# Download OHLCV data for each symbol
# Store in parquet format
```

---

## 5. ARCHITECTURE

### Key Files
```
strategyhub-research/
├── src/
│   ├── api/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── routes/
│   │   │   ├── backtests.py     # Backtest endpoints
│   │   │   └── strategies.py    # Strategy endpoints
│   │   └── schemas.py           # Pydantic models
│   ├── backtesting/
│   │   ├── engine.py            # Backtester class
│   │   └── metrics.py           # Performance calculations
│   ├── strategies/
│   │   ├── __init__.py          # STRATEGY_REGISTRY
│   │   ├── base.py              # Abstract base class
│   │   ├── trend.py             # Trend strategies
│   │   ├── momentum.py          # Momentum strategies
│   │   ├── mean_reversion.py    # Mean reversion strategies
│   │   └── factor.py            # Factor strategies
│   └── database/
│       ├── connection.py        # DB session management
│       ├── models.py            # SQLAlchemy models
│       └── repository.py        # Data access layer
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── page.tsx         # Dashboard page
│       │   └── strategies/      # Strategy detail pages
│       └── components/          # React components
├── scripts/
│   └── run_all_backtests.py     # Batch backtest runner
├── data_processed/
│   └── prices_clean.parquet     # Cleaned price data
└── strategyhub.db               # SQLite database
```

### API Endpoints
- `GET /api/v1/strategies/available` - List all strategies
- `POST /api/v1/backtests/run` - Run a backtest
- `GET /api/v1/backtests/dashboard` - Dashboard data
- `GET /api/v1/backtests/{run_id}` - Specific backtest result

---

## 6. PRIORITY TASKS (IN ORDER)

### Immediate Tasks
1. **Replace Existing Strategies** with the 14 correct ones listed above
2. **Fix TSMOM Bug** or remove it entirely
3. **Remove Duplicates** in dashboard
4. **Run Backtests** for all new strategies
5. **Verify Dashboard** shows correct data

### Short-Term Tasks
6. **Extend Data Pipeline** - Download 2000-present from Yahoo Finance
7. **Handle Survivorship Bias** - Use point-in-time constituent lists
8. **Re-run Backtests** on extended data

### Medium-Term Tasks
9. **Walk-Forward Optimization** - Train/test splits
10. **Out-of-Sample Testing** - Reserve 30% of data
11. **Market Regime Detection** - Bull/bear/sideways
12. **Indian Market Data** - NSE/BSE integration

---

## 7. TECHNICAL NOTES

### Strategy Implementation Pattern
```python
from src.strategies.base import BaseStrategy

class LargeCapMomentumStrategy(BaseStrategy):
    """Large Cap Momentum - Top decile by 12-month momentum."""

    DEFAULT_PARAMS = {
        'lookback': 252,  # 12 months
        'top_pct': 0.1,   # Top 10%
        'rebalance_freq': 'monthly',
    }

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # Calculate 12-month momentum
        # Filter to large caps
        # Select top decile
        # Return position weights
        pass
```

### Backtester Usage
```python
from src.backtesting.engine import Backtester
from src.strategies import get_strategy

strategy = get_strategy('large_cap_momentum', data, params)
backtester = Backtester(
    strategy=strategy,
    data=data,
    initial_capital=100000,
    commission_bps=10,
    slippage_bps=5
)
result = backtester.run()
```

### Database Models
- `Strategy` - Strategy metadata
- `BacktestRun` - Individual backtest execution
- `BacktestMetrics` - Performance metrics
- `EquityCurve` - Daily equity values

---

## 8. FIXES ALREADY APPLIED

1. **Module Import Error** - Fixed `src/api/__init__.py` to avoid circular imports
2. **Route Ordering** - Moved `/dashboard` before `/{run_id}` in `backtests.py`
3. **Created Documentation** - CLAUDE.md, PROGRESS_REPORT.md

---

## 9. USER PREFERENCES

- Owner: Mrigay Pathak
- Purpose: Personal trading research + portfolio showcase
- Style: Professional, clean code, proper testing
- Timeline: MVP by March 2026
- Data sources: Free/cheap options preferred (Yahoo Finance)

---

## 10. FIRST ACTIONS FOR NEW SESSION

1. Read this file completely
2. Verify backend/frontend can start
3. Review current strategy implementations in `src/strategies/`
4. Plan the new strategy implementations
5. Ask user to confirm the 14 strategies before coding

---

## QUICK COMMAND REFERENCE

```bash
# Navigate to project
cd "/Users/mrigaypathak/Desktop/trading app/strategyhub-research"

# Start backend
python -m uvicorn src.api.main:app --reload --port 8000

# Start frontend
cd frontend && npm run dev

# Run backtests
python scripts/run_all_backtests.py

# Check API
curl http://localhost:8000/api/v1/backtests/dashboard | jq
```

---

**END OF RESUME PROMPT**
