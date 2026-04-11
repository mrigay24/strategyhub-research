# StrategyHub Research

A systematic trading research platform that tests **14 professional-grade factor strategies** against **25 years of S&P 500 data (2000–2024)** and rigorously validates whether they actually work — or just *appear* to work.

Built as a personal portfolio project for quantitative finance, this is not a toy backtest. Every strategy is stress-tested through 8 layers of statistical validation including walk-forward efficiency analysis, Monte Carlo permutation tests, market regime decomposition, and Bonferroni-corrected significance testing.

---

## Live Platform

| Service | URL |
|---------|-----|
| Frontend Dashboard | `http://localhost:3000` |
| FastAPI Backend | `http://localhost:8000` |
| API Docs (Swagger) | `http://localhost:8000/docs` |

---

## What It Does

### 14 Factor Strategies
All strategies run on the full S&P 500 universe (multi-asset, factor-based). Backtested over 25 years including three full market crises: dot-com crash (2000–2002), Global Financial Crisis (2008–2009), and COVID crash (2020).

| Family | Strategies |
|--------|-----------|
| Momentum | Large Cap Momentum, 52-Week High Breakout |
| Value | Deep Value All-Cap |
| Quality | High Quality ROIC |
| Factor | Low Volatility Shield, Dividend Aristocrats |
| Trend | Moving Average Trend |
| Mean Reversion | RSI Mean Reversion |
| Composite | Value+Momentum, Quality+Momentum, Quality+Low Vol, Composite Factor Score |
| Risk Management | Volatility Targeting |
| Event-Driven | Earnings Surprise Momentum |

### 8-Layer Validation Pipeline

| # | Method | What it tests |
|---|--------|---------------|
| 1 | **Parameter Sensitivity** | Is the strategy robust across param ranges, or overfit to one value? |
| 2 | **Walk-Forward Efficiency** | Do in-sample params generalize to out-of-sample periods? |
| 3 | **Monte Carlo Bootstrap** | Is the Sharpe ratio statistically significant or luck? |
| 4 | **Market Regime Analysis** | How does the strategy behave in Bull / Bear / High-Vol / Sideways? |
| 5 | **Transaction Cost Sensitivity** | Does it survive realistic brokerage costs and slippage? |
| 6 | **Regime Overlay** | Can a bear-market filter meaningfully reduce drawdowns? |
| 7 | **Portfolio Correlation Analysis** | Which strategies are genuinely complementary vs. redundant? |
| 8 | **Rolling Performance** | Is performance concentrated in one period, or consistent over 25 years? |

### AI Strategy Builder
Describe a strategy in plain English. Claude Opus 4.6 maps it to the closest academically-documented factor strategy and runs the full 7-gate validation pipeline against pre-computed 25-year research data.

Every factor signal is sourced from peer-reviewed finance literature (Jegadeesh & Titman 1993, Fama & French 1992, Baker et al. 2011, etc.). No black-box signals.

---

## Key Findings (25-Year Study)

- **All 14 strategies lag the equal-weight S&P 500 benchmark** (Sharpe 0.53–0.66 vs 0.69). Phase 2's impressive results were a 4-year bull-market artifact — the real test is 25 years with crashes included.
- **Every strategy fails in bear markets** (all long-only strategies, Sharpe ≈ −1.4 in bear regimes). No exceptions. The "defensive" strategies (Low Vol, Quality+Low Vol) are relatively less bad, not actual hedges.
- **Factor strategies have statistically significant but economically small alpha** — 12/14 strategies pass Monte Carlo significance at p < 0.05, and 12/14 pass Bonferroni correction (p < 0.0036 for 14 simultaneous tests).
- **Average pairwise correlation: 0.951** across the 14 strategies — 90/91 pairs have r > 0.80. They are effectively the same long-equity bet with different labels.
- **Rank stability is unstable over 25 years** (Spearman rank stability −0.123). No strategy consistently leads over all market decades.
- **Tier 1 strategies**: Low Volatility Shield (Sharpe 0.659) and RSI Mean Reversion (Sharpe 0.641).

---

## Tech Stack

```
Backend:   Python · FastAPI · SQLAlchemy · SQLite
Frontend:  Next.js · React · Tailwind CSS · Recharts
Data:      yfinance · Pandas · NumPy
AI:        Claude Opus 4.6 (Anthropic) with adaptive thinking
```

### Architecture

```
data_raw/               Raw downloaded price data (yfinance, ~820 S&P 500 tickers)
data_processed/         Cleaned parquet files (653 symbols, 3.4M rows, 2000-2024)
src/
  strategies/           14 strategy implementations (signals as DataFrame weights)
  backtesting/          Vectorized engine + metrics calculator
  api/                  FastAPI app + routes (backtests, research, ai-builder)
  database/             SQLAlchemy models + connection management
scripts/                One-off analysis scripts (sensitivity, walk-forward, Monte Carlo…)
results/                Pre-computed research results (JSON/CSV per analysis)
frontend/               Next.js app (dashboard, strategy detail pages, AI builder)
```

---

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+

### Backend

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start API server (port 8000)
python -m uvicorn src.api.main:app --reload --port 8000
```

For the AI Strategy Builder, set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### Frontend

```bash
cd frontend
npm install
npm run dev     # starts on port 3000
```

### Re-run All Backtests (optional)

```bash
# Run all 14 strategies on 25-year data and store to DB
python scripts/run_extended_backtests_to_db.py
```

---

## Research Methodology Notes

**Survivorship bias:** The data uses point-in-time S&P 500 constituent lists (sourced from Wikipedia's historical index composition). However, delisted/bankrupt stocks that Yahoo Finance cannot provide (~17% of historical tickers) are missing — partially survivorship-biased. CRSP database would eliminate this entirely.

**Look-ahead bias prevention:** Signal computed at day *t* → position applied at day *t+1*. All signals use only information available at the signal date.

**Transaction costs:** 10 bps commission + 5 bps slippage = 15 bps round-trip on all position changes. Applied throughout all analyses.

**Walk-forward efficiency (WFE):** Defined as OOS Sharpe / IS Sharpe. WFE > 100% means out-of-sample performance exceeded in-sample — but in this study this is partly explained by regime differences (IS periods included GFC bear markets, OOS periods caught bull markets).

---

## Project Structure Deep Dive

### Strategy Signals
Each strategy implements `generate_signals() → pd.DataFrame` where columns are stock tickers and values are portfolio weights (0 to 1/n for long-only). The backtesting engine shifts signals by 1 day before execution.

### Key Engine Fixes (documented for reproducibility)
1. `pct_change(fill_method=None)` on pivoted data — prevents false >100% returns when a symbol enters the universe
2. Signal weight normalization in `_align_signals` — `abs().sum() ≤ 1.0` prevents leverage accumulation
3. Portfolio-level return clip at −50% daily — prevents `cumprod()` hitting zero permanently from a single extreme event

---

## Phase Log

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | 14 strategies, backtesting engine, SQLite DB | ✅ Complete |
| Phase 2 | 8-layer validation on 4-year data (2014–2017) | ✅ Complete |
| Phase 3 | Extended to 25-year data + point-in-time constituents | ✅ Complete |
| Phase 4 | Strategy detail pages, interactive charts, AI Builder | ✅ Complete |

---

*Built by Mrigay Pathak · March 2026*
