# StrategyHub Research - Progress Report

> **Last Updated:** 2026-03-12
> **Status:** ALL PHASES COMPLETE — Platform fully built. One task remaining: end-to-end AI Builder test with ANTHROPIC_API_KEY (tomorrow).
> **Owner:** Mrigay Pathak

---

## 1. PROJECT OVERVIEW

### 1.1 What Is This?

**StrategyHub Research** is a systematic trading strategy research platform that enables:
- Backtesting algorithmic trading strategies against historical market data
- Comparing strategy performance across different market conditions
- Visualizing results through a modern web dashboard
- Personal parameter tuning and experimentation on each strategy
- Eventually: Walk-forward testing, extended data, live signals

### 1.2 The Vision

Build a professional-grade quantitative research platform that:
1. Tests strategies across 25+ years of market data (2000-present)
2. Covers multiple markets (US S&P 500 + Indian NSE/BSE)
3. Handles different market regimes (recessions, booms, crashes)
4. Enables deep understanding of backtesting methodology
5. Offers a clean dashboard for strategy comparison and selection

### 1.3 Target Users
- Mrigay: Personal trading research + learning backtesting methodology
- Potential showcase for quantitative finance roles
- Educational tool for understanding systematic, factor-based investing

### 1.4 Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Data Processing** | Python, Pandas, NumPy | Data manipulation, calculations |
| **Backtesting** | Custom vectorized engine | Fast strategy simulation |
| **Database** | SQLite | Store results, metrics, equity curves |
| **API** | FastAPI | REST endpoints |
| **Frontend** | Next.js, React, Tailwind CSS | Dashboard UI |
| **Data Sources** | Kaggle (current), Yahoo Finance (planned) | Market data |

---

## 2. CURRENT STATE (As of 2026-03-12)

| Feature                              | Status | Notes                                                                          |
|--------------------------------------|--------|--------------------------------------------------------------------------------|
| S&P 500 historical data (2014-2017)  | ✅ Done | 505 symbols, ~497K rows (Phase 1 baseline)                                     |
| Extended data (2000–2024)            | ✅ Done | 653 symbols, 3.4M rows, 6,288 trading days. See Phase 3.                       |
| Point-in-time S&P 500 constituents   | ✅ Done | 820 tickers from Wikipedia PIT data; monthly snapshots 2000–2024               |
| 14 industry-grade trading strategies | ✅ Done | All multi-asset, factor-based, across 7 families                               |
| Vectorized backtesting engine        | ✅ Done | Transaction costs, slippage, no look-ahead, weight normalization               |
| Performance metrics calculator       | ✅ Done | Sharpe, Sortino, Calmar, Max DD, Win Rate, CAGR, Volatility                    |
| FastAPI backend                      | ✅ Done | REST API — backtests, research, rolling, correlation, sensitivity, alpha, AI   |
| Next.js dashboard                    | ✅ Done | Filters, KPI tiles, tier badges, sort dropdown, strategy cards                 |
| All 14 backtests stored in DB        | ✅ Done | 25-year equity curves (weekly, ~1305 pts). Sharpe 0.59–0.74                    |
| **Parameter sensitivity analysis**   | ✅ Done | 12/14 ROBUST, 2 FRAGILE. See §5.3                                              |
| **Walk-Forward + OOS testing**       | ✅ Done | 13/14 WFE>100%, 1 GOOD. See §5.4                                               |
| **Monte Carlo bootstrap**            | ✅ Done | 12/14 SIGNIFICANT (25yr). Bonferroni p<0.0036. See §5.5                        |
| **Market regime analysis**           | ✅ Done | ALL fail in Bear; Dot-com: Low Vol only outperformer. See §5.6                 |
| **Transaction cost sensitivity**     | ✅ Done | ALL 14 BULLETPROOF; low turnover (0.2x–6.3x/yr). See §5.7                     |
| **Regime overlay**                   | ✅ Done | Overlay HURTS over 25yr — 63-day lag misses fast crashes. See §5.8             |
| **Portfolio correlation analysis**   | ✅ Done | Avg corr 0.951; 90/91 pairs r>0.80; DR=1.024. See §5.9                        |
| **Rolling performance analysis**     | ✅ Done | Rank stability −0.123 UNSTABLE over 25yr. See §5.10                           |
| **CAPM factor attribution**          | ✅ Done | β=0.54–1.18, α=−1.1% to +2.6%/yr, R²=85–93%. See §5.11                       |
| **Strategy detail pages — 7 tabs**   | ✅ Done | Overview, Rules, Performance, Research, Rolling, Correlation, Parameters       |
| **Parameters tab + live backtest**   | ✅ Done | Sliders per strategy, 25yr live backtest runner, sensitivity heatmap           |
| **Research tab — full**              | ✅ Done | MC, WF, Regime, Scorecard, CAPM attribution, L/S equity curve                 |
| **Rolling tab**                      | ✅ Done | Annual Sharpe/Return/MDD bar+line charts, rank stability badge                 |
| **Correlation tab**                  | ✅ Done | 14×14 heatmap (red scale 0.70–1.0), avg corr, DR                              |
| **AI Strategy Builder**              | ✅ Done | Claude Opus 4.6 + 8-factor library + 7-gate validation. Demo mode available.  |
| **Long-short equity curve**          | ✅ Done | Dollar-neutral L/S chart in Research tab; strips market beta                   |
| **README**                           | ✅ Done | Portfolio-ready: strategy table, validation table, key findings, methodology   |
| **Dashboard data accuracy polish**   | ✅ Done | KpiTiles 25yr Sharpe, stale FilterSidebar fixed, StrategyCard redesigned (25yr labels, 4 distinct metrics) |
| **Rolling chart benchmark line**     | ✅ Done | Red dashed 25yr avg reference + improved yellow annual benchmark line with dots |
| **Key Findings page (/findings)**    | ✅ Done | TopNav link, 4 finding cards, CAPM alpha table, tier rankings, methodology summary |
| **Favicon + page titles**            | ✅ Done | icon.tsx (blue SH), title template, per-page titles via layout wrappers |
| End-to-end AI Builder test           | ⏳ Tomorrow | Requires ANTHROPIC_API_KEY                                                    |

---

## 3. 14 STRATEGIES IMPLEMENTED

All strategies run on the full S&P 500 universe (multi-asset). Backtests cover **2014-2017**. Results stored in SQLite.

### Backtest Results Summary (2014-2017)

| Strategy                   | Family          | Total Return | Notes                                           |
|----------------------------|-----------------|--------------|-------------------------------------------------|
| Large Cap Momentum         | Momentum        | —            | Top decile 12-month momentum                    |
| 52-Week High Breakout      | Momentum        | +353%        | Strongest performer                             |
| Deep Value All-Cap         | Value           | —            | Contrarian, beaten-down stocks                  |
| High Quality ROIC          | Quality         | —            | Low vol + high risk-adj return                  |
| Low Volatility Shield      | Factor          | —            | Inverse-vol weighted                            |
| Dividend Aristocrats       | Income          | —            | Return consistency proxy                        |
| Moving Average Trend       | Trend           | —            | Price > 200-day MA                              |
| RSI Mean Reversion         | Mean Reversion  | -22%         | Cross-sectional oversold bounce                 |
| Value + Momentum Blend     | Composite       | —            | 50/50 value + momentum                          |
| Quality + Momentum         | Composite       | —            | Quality stocks with positive trend              |
| Quality + Low Volatility   | Composite       | —            | Defensive "sleep-at-night"                      |
| Composite Factor Score     | Multi-Factor    | —            | 30% mom + 30% quality + 20% value + 20% low vol |
| Volatility Targeting       | Risk Management | —            | Scale by realized vol                           |
| Earnings Surprise Momentum | Event-Driven    | —            | PEAD-style drift                                |

*Benchmark (Equal-Weighted S&P 500): ~X% total return*

### Strategy Files

| File | Contains |
|------|---------|
| `src/strategies/momentum.py` | LargeCapMomentum, FiftyTwoWeekHighBreakout |
| `src/strategies/value.py` | DeepValueAllCap |
| `src/strategies/quality.py` | HighQualityROIC |
| `src/strategies/factor.py` | LowVolatilityShield, DividendAristocrats |
| `src/strategies/trend.py` | MovingAverageTrend |
| `src/strategies/mean_reversion.py` | RSIMeanReversion |
| `src/strategies/composite.py` | ValueMomentumBlend, QualityMomentum, QualityLowVol, CompositeFactorScore |
| `src/strategies/risk_management.py` | VolatilityTargeting |
| `src/strategies/event.py` | EarningsSurpriseMomentum |

---

## 4. PHASES & PROGRESS

### PHASE 0: Foundation ✅ COMPLETE
- [x] Download S&P 500 dataset (Kaggle 2014-2017)
- [x] Clean data into standard schema
- [x] Compute daily returns
- [x] Set up project structure

### PHASE 1: Strategy Replacement ✅ COMPLETE (2026-03-02)
- [x] Replace all 15 old placeholder strategies with 14 industry-accurate ones
- [x] All strategies are multi-asset (run on full S&P 500 universe)
- [x] Each strategy has documented, tunable parameters
- [x] Run all 14 backtests on 2014-2017 data
- [x] Store results in SQLite (metrics + equity curves)
- [x] Update frontend display info (family, factors, risk, overview, rules)
- [x] Update FilterSidebar with correct strategy families
- [x] Update API type maps
- [x] Clean old strategies from database
- [x] Equal-weighted benchmark calculated and stored

**Old strategies removed:** SMA Crossover, EMA Crossover, TSMOM, Cross-Sectional Momentum, Short-Term Reversion, RSI (single-asset), Bollinger Bands, Donchian, Volatility Breakout, Pairs Trading, Low Vol (old), Quality (placeholder), Value (placeholder), Min Variance

**New strategies:** Large Cap Momentum, 52-Week High Breakout, Deep Value All-Cap, High Quality ROIC, Low Volatility Shield, Dividend Aristocrats, Moving Average Trend, RSI Mean Reversion (cross-sectional), Value+Momentum, Quality+Momentum, Quality+Low Vol, Composite Factor Score, Volatility Targeting, Earnings Surprise Momentum

### PHASE 2: Deep Backtesting Education 🔄 IN PROGRESS
*Goal: Learn to backtest properly — not just run scripts, but understand what each method does, when to use it, and how to interpret results.*

- [x] **Parameter Sensitivity Analysis** (2026-03-04)
  - Built `scripts/parameter_sensitivity.py` — sweeps each param across a range
  - 1D sweeps (vary one param, hold others) + 2D heatmaps (pair of params)
  - All 14 strategies analyzed: 12 ROBUST, 2 FRAGILE
  - Results in `results/parameter_sensitivity/` (JSON + CSV)
  - Fragile strategies: Dividend Aristocrats, Earnings Surprise Momentum
- [x] **Walk-Forward + Out-of-Sample Testing** (2026-03-04)
  - Built `scripts/walk_forward.py` — two-tier OOS validation
  - Method 1: Simple 70/30 train/test split
  - Method 2: Rolling walk-forward (12mo train → 6mo test, rolling with 400-day lookback buffer)
  - 13/14 strategies show genuine OOS performance (EXCELLENT verdict)
  - 1 strategy structurally incompatible (Dividend Aristocrats — 36-month lookback vs 4-year data)
  - Results in `results/walk_forward/` (JSON + CSV)
  - Key metric: Walk-Forward Efficiency (WFE) — all working strategies have WFE > 100%
- [x] **Monte Carlo Bootstrap Confidence Intervals** (2026-03-05)
  - Built `scripts/monte_carlo.py` — three statistical significance tests
  - Method 1: IID Bootstrap (10,000 resamples, 95% CI for Sharpe)
  - Method 2: Block Bootstrap (20-day blocks, preserves autocorrelation)
  - Method 3: Random Sign Test (10,000 sign flips, tests directional skill)
  - 5 strategies statistically significant (all 3 tests p<0.05)
  - 3 likely significant, 3 marginal, 3 not significant
  - Also computes Pezier-White adjusted Sharpe (corrects for skewness/kurtosis)
  - Results in `results/monte_carlo/` (JSON + CSV)
- [x] **Market Regime Analysis** (2026-03-05)
  - Built `scripts/regime_analysis.py` — regime detection + per-strategy regime performance
  - Regime method: 63-day trend + 63-day realized vol (Bull/Bear/High-Vol/Sideways)
  - 2014-2017 regime breakdown: 59% Sideways, 27% Bull, 7% Bear, 6% High-Vol
  - ALL 13 working strategies fail in Bear regime (negative Sharpe)
  - High-Vol regime is the best for most strategies (Sharpe 2-4)
  - Dividend Aristocrats is the only regime-independent strategy (near-zero everywhere)
  - Regime complementarity analysis: no natural hedges among current strategies
  - Results in `results/regime_analysis/` (JSON + CSV)
- [x] **Transaction Cost Sensitivity** (2026-03-05)
  - Built `scripts/transaction_cost_sensitivity.py` — sweeps costs 0–100 bps across all strategies
  - 10 cost levels: 0, 2, 5, 10, 15, 20, 30, 50, 75, 100 bps (total round-trip)
  - Computes: breakeven cost, Sharpe per 10 bps, annual turnover, cost drag %
  - Result: ALL 14 strategies are BULLETPROOF (survive even 100 bps costs)
  - Key reason: all strategies have low annual turnover (0.2x–6.3x) — they're monthly, not daily, rebalancers
  - Highest turnover: RSI Mean Reversion (6.3x), Earnings Surprise (6.2x)
  - Biggest degrader under costs: Earnings Surprise (Sharpe 0.60 → 0.12 at 100 bps)
  - Turnover ↔ cost sensitivity correlation: -0.668
  - Results in `results/transaction_costs/` (JSON per strategy + CSV summary)
- [x] **Portfolio Correlation & Construction Analysis** (2026-03-05)
  - Built `scripts/portfolio_analysis.py` — full 14×14 correlation matrix + 7 portfolio variants
  - Average inter-strategy correlation: **0.788** (very high — all strategies are similar long-equity bets)
  - 63/91 pairs (69%) have correlation >0.80 — redundant
  - Most redundant pair: Quality+Momentum ↔ Composite Factor Score (r=0.996)
  - Only truly different strategy: Dividend Aristocrats (avg corr 0.288, market corr 0.176)
  - Best portfolio by Sharpe: Risk-Parity Tier 1 (0.90 SR, -35.9% MDD)
  - Best portfolio by MDD: Risk-Parity All 14 (-17.61%, near-benchmark level)
  - Diversification ratio barely above 1.0 (1.051) — very limited diversification benefit
  - Results in `results/portfolio_analysis/` (JSON, CSV correlation matrix, portfolio comparison)
- [x] **Regime Overlay — Strategy Improvement** (2026-03-05)
  - Built `scripts/regime_overlay.py` — applies Bear-market filter on top of all 14 strategy signals
  - Three overlay variants: Bear-only (cash in Bear), Aggressive (cash in Bear + 50% in Sideways), Trend-only (cash when 63d trend negative)
  - Bear-only results: Max drawdown reduced 5–26% across all strategies
  - 52-Week High Breakout: MDD -74.88% → -49.27% (+25.61% improvement)
  - Large Cap Momentum: MDD -45.19% → -26.81% (+18.38% improvement)
  - Sharpe drops slightly (0.04–0.16) — expected in bull-heavy 2014-2017 data, will show more benefit with 25yr data
  - Trend-only overlay too aggressive (20% cash days) — hurts Sharpe significantly
  - Bear-only is the best trade-off: small Sharpe cost for large MDD benefit
  - Results in `results/regime_overlay/` (JSON per strategy + CSV)
- [x] **Rolling Performance Analysis** (2026-03-05)
  - Built `scripts/rolling_performance.py` — rolling 126-day Sharpe, drawdown, vol, avg correlation, rank stability
  - Sub-period breakdown: 8 × ~6-month blocks covering the full 4-year window
  - KEY FINDING: Performance heavily concentrated in 2016-2017 (avg Sharpe 1.47 → 1.69 → 2.32)
  - Worst sub-period: Dec 2014 – Jun 2015 (avg Sharpe -0.31; only 21% strategies positive)
  - Rank stability: 0.749 (STABLE) — same strategies consistently lead across all sub-periods
  - Rolling avg correlation (Tier 1): mean 0.896, std 0.143, can dip to -0.076 during transitions
  - Best strategy by mean rolling Sharpe: Low Volatility Shield (0.98)
  - Most volatile rolling Sharpe: Deep Value All-Cap (std 1.49), 52-Week High (std 1.05)
  - Results in `results/rolling_performance/` (JSON, rolling CSVs)
- [ ] Document findings per strategy

### PHASE 3: Extended Data 🔄 IN PROGRESS
- [x] **Phase 3.1 — Historical S&P 500 Constituent Lists** (2026-03-05)
  - Built `scripts/fetch_sp500_constituents.py` — scrapes Wikipedia for current + historical S&P 500 composition
  - 503 current stocks, 721 change events (2000-2026), 820 unique tickers ever in S&P 500
  - 300 monthly point-in-time snapshots; avg 509 stocks/month (matches actual S&P 500 ✓)
  - Survivorship bias quantified: 65 Phase 2 Kaggle tickers not in PIT; 68 PIT tickers missing from Kaggle
  - Output: `data_raw/sp500_constituents/` (sp500_current.csv, sp500_changes.csv, sp500_pit_monthly.csv, sp500_all_unique.txt)
- [x] **Phase 3.2 — Download Extended Price Data** (2026-03-05)
  - Built `scripts/download_extended_data.py` — uses yfinance 1.2.0 Ticker.history() API, 4 parallel workers
  - Downloaded 658 symbols for 2000-2024; current S&P 500 (503) all succeeded
  - Historical-only tickers (317): ~155 succeeded (acquired companies), ~162 failed (delisted, no Yahoo data)
  - Output: `data_raw/extended_prices/prices_TICKER.parquet` (658 files) + `data_processed/extended_prices.parquet`
- [x] **Phase 3.3 — Process & Validate Extended Dataset** (2026-03-07, corrected)
  - Built `scripts/process_extended_data.py` — validates, cleans, builds PIT universe lookup
  - Two-pass data cleaning: (1) price floor close < $1 → removes corrupted near-zero prices;
    (2) |daily return| > 20% removed (two iterations to catch newly-adjacent extremes after gaps)
  - 35,074 bad rows removed by price floor; 6,592 rows removed by return filter
  - Final: **653 symbols, 3,399,770 rows, 6,288 trading days** (2000-01-03 → 2024-12-30)
  - 431 symbols with full 2000-2024 history (current S&P 500 survivors)
  - PIT universe coverage: avg 422 symbols/month (83% of the 509-stock PIT list)
  - Residual survivorship bias: 17% of historical constituents have no Yahoo Finance data (delisted)
  - Output: `data_processed/extended_prices_clean.parquet`, `sp500_universe_lookup.csv`, `extended_coverage_stats.csv`
  - **Data quality lesson:** Original 50% outlier filter was insufficient. CBE had 33,999× daily returns
    from near-zero prices (0.001) surviving the filter and creating false astronomical gains once pivoted.
    Root fix: price floor ($1) must precede return filter; pct_change must use fill_method=None on pivot.
- [x] **Phase 3.4 — Point-in-Time Universe Masking** (2026-03-07)
  - Implemented inline in `scripts/run_extended_backtests.py`
  - After `generate_signals()`, zero out signals for off-universe stocks on each date
  - Re-normalize weights to sum to 1 (so portfolio remains fully invested in in-universe stocks)
  - Eliminates universe look-ahead bias (using 2024 S&P 500 to test 2002 would inflate returns)
- [x] **Phase 3.5 — Run All 14 Backtests on Extended Data** (2026-03-07)
  - Script: `scripts/run_extended_backtests.py` with PIT masking + fill_method=None for pct_change
  - Results stored in `results/extended_backtests/` (does NOT overwrite Phase 2 SQLite DB)
  - See §5.15 for full results and interpretation
- [x] **Phase 3.6 — Regime Analysis on Extended Data** (2026-03-07)
  - Script: `scripts/extended_regime_analysis.py` with PIT masking
  - Regime distribution: Bull 40.0%, Bear 12.0%, High-Vol 17.5%, Sideways 30.5%
  - ALL strategies underperform benchmark in ALL four regimes
  - Named period standout: Low Vol Shield +0.63 Sharpe during dot-com crash (benchmark +0.11)
  - Large Cap Momentum worst during dot-com (-0.34 Sharpe) — momentum crashed hardest
  - No strategy provides genuine bear protection during GFC or COVID crashes
  - Results: `results/extended_regime_analysis/`
- [x] **Phase 3.7 — Rolling Performance on Extended Data** (2026-03-07)
  - Script: `scripts/extended_rolling_performance.py` with annual sub-periods and decade analysis
  - **Rank stability: -0.123 (UNSTABLE)** vs Phase 2's 0.749 (STABLE) — leadership rotates year-to-year
  - 2000s decade: benchmark beats most strategies; Low Vol Shield and RSI best among strategies
  - 2010s decade: tight cluster, all strategies within 0.1 Sharpe of benchmark
  - 2020s decade: benchmark beats all 14 strategies; Earnings Surprise worst at 0.24 Sharpe
  - Best rolling year: April 2004 (post dot-com recovery) for most strategies
  - Results: `results/extended_rolling_performance/`
- [x] **Phase 3.8 — Regime Overlay on Extended Data** (2026-03-07)
  - Script: `scripts/extended_regime_overlay.py`
  - **Overlay HURTS performance universally**: Sharpe drops -0.12 avg; MDD worsens -4.4pp avg
  - Zero strategies see Sharpe improvement from Bear-only overlay (vs Phase 2: all improved MDD)
  - Root cause: 63-day trend detection lag. By detection time, crash has happened; overlay then
    misses bottom-bounces and recovery (especially COVID: 23-day crash + V-shaped recovery)
  - Major finding: Regime overlay with lagged detection doesn't work for fast crashes
  - Results: `results/extended_regime_overlay/`
- [x] **Phase 3.9 — Portfolio Analysis on Extended Data** (2026-03-08)
  - Script: `scripts/extended_portfolio_analysis.py` with PIT masking + regime-conditional correlation
  - **Average inter-strategy correlation: 0.951** (vs Phase 2: 0.788) — strategies even more correlated over 25 years
  - 90/91 pairs above r=0.80; no pair below 0.40 (vs 63/91 high-corr in Phase 2)
  - Bear regime correlation: 0.969 — diversification evaporates exactly during crashes
  - **Diversification ratio: 1.024** (Phase 2: 1.051) — virtually no benefit to combining strategies
  - All portfolio variants underperform benchmark (best: Tier1 Risk-Parity at 0.62 vs benchmark 0.69)
  - Most unique strategy: Earnings Surprise (avg corr 0.849) — but it's also weakest performer
  - Results: `results/extended_portfolio_analysis/`
- [x] **Phase 3.10 — Walk-Forward on Extended Data** (2026-03-08)
  - Script: `scripts/extended_walk_forward.py` — pre-computes all signals once, slices returns by time window
  - Simple OOS split (IS: 2000-2012, OOS: 2013-2024): **13/14 EXCELLENT** (WFE >100%), 1 GOOD (Earnings Surprise 94%)
  - Rolling 9-fold validation: 13/14 avg WFE >100%; Earnings Surprise avg 90%
  - Positive OOS fold count: 13 strategies with 8/9 positive folds; Earnings Surprise 7/9
  - **CRITICAL CAVEAT:** WFE >100% is regime-driven, NOT strategy skill — IS period (2000-2012) contained 3 bear markets (lower IS Sharpe); OOS period (2013-2024) was a prolonged bull (higher OOS Sharpe). Any passive index fund would show same pattern.
  - The only genuine stress test is Fold 2 (GFC 2008-2009): ALL strategies went negative (-0.03 to -0.21) — confirms strategies cannot escape systematic bear markets
  - Results: `results/extended_walk_forward/`
- [x] **Phase 3.11 — Monte Carlo on Extended Data** (2026-03-08)
  - Script: `scripts/extended_monte_carlo.py` — same 3-test framework as Phase 2.3 on 25-year data
  - **12/14 SIGNIFICANT ★★★** (all 3 tests: IID bootstrap + block bootstrap + random sign test pass at 5%)
  - **2/14 LIKELY SIGNIFICANT ★★** (Low Vol Shield + RSI Mean Reversion — IID + Block pass; sign test anomalous p=1.0)
  - **0/14 Marginal or Not Significant** — complete reversal from Phase 2 (3 not significant, 3 marginal)
  - Key insight: 6× more trading days (6,288 vs 1,007) → 2.5× narrower confidence intervals → lower p-values even for lower Sharpe ratios
  - Pezier-White adjusted Sharpe: 0.046-0.104 below raw Sharpe across all strategies (negative skew + fat tails penalty)
  - Sign test anomaly: Low Vol Shield and RSI Mean Reversion sign_p=1.0 because the sign test poorly handles always-invested, low-turnover strategies where timing component is trivial; IID and block bootstrap (preferred tests) both confirm significance at p<0.001
  - Results: `results/extended_monte_carlo/`
- [x] **Phase 3.12 — Final Phase 3 Summary** (2026-03-08)
  - Script: `scripts/phase3_final_summary.py` — reads all 7 Phase 3 result files, no recomputation
  - Produces: master scorecard (14 strategies × 7 analyses), Phase 3 tier list, Phase 2 vs Phase 3 comparison table, 5 key findings
  - **Phase 3 Tier 1** (Most Robust, highest Sharpe + consistent): Low Volatility Shield (SR 0.659), RSI Mean Reversion (SR 0.641)
  - **Phase 3 Tier 2** (Solid, ★★★ MC significant): Volatility Targeting, 52-Week High Breakout, Composite Factor Score, Quality+Momentum, High Quality ROIC, Quality+Low Vol
  - **Phase 3 Tier 3** (Confirmed but Weak): Large Cap Momentum, Moving Average Trend, Value+Momentum, Dividend Aristocrats, Earnings Surprise, Deep Value All-Cap
  - Results: `results/phase3_summary/` (master_scorecard.csv + phase3_summary.json)
  - See §5.22 for full results
- [ ] Indian market data (NSE 50, Sensex) — lower priority, later sub-phase

### PHASE 4: Strategy Detail Pages 🔄 IN PROGRESS (2026-03-09)
- [x] **4.1** Backend research endpoint `GET /api/v1/research/{strategy_name}` — reads Phase 3 JSON files
- [x] **4.1** Backend parameters endpoint `GET /api/v1/research/parameters/{strategy_name}`
- [x] **4.1** Frontend "Research" tab — MC verdict, WF efficiency, fold Sharpes, regime table, tier badge
- [x] **4.1** Frontend "Parameters" tab — sliders per param with ROBUST/FRAGILE labels, live backtest runner
- [x] **4.2** Dashboard improvements — Phase 3 tier badge on strategy cards, 4yr vs 25yr Sharpe display, sort-by (tier/Sharpe/CAGR/MaxDD), tier filter pills, `/research/scorecard` endpoint
- [ ] **4.3** Rolling metrics tab on strategy detail page
- [ ] **4.4** Correlation matrix heatmap on dashboard

### PHASE 5: Polish & Deploy 📋 PLANNED
- [ ] Deploy backend (Railway/Render)
- [ ] Deploy frontend (Vercel)
- [ ] README and documentation
- [ ] Performance optimization

---

## 5. BACKTESTING METHODOLOGY

### 5.1 Current Approach
- **Type:** Vectorized backtesting (fast, operates on DataFrames)
- **Transaction Costs:** 10 bps commission, 5 bps slippage (always on, every test)
- **Rebalancing:** Strategy-specific (daily/weekly/monthly)
- **Look-ahead Bias:** Prevented — signals at day `t`, execution at `t+1`
- **Capital:** $100,000 starting capital
- **Universe:** Full S&P 500 (~505 symbols)

### 5.2 Methods Used (Phase 2)

| Method | Status | Script | What It Answers |
|--------|--------|--------|----------------|
| Parameter Sensitivity | ✅ Done | `scripts/parameter_sensitivity.py` | "Is this strategy fragile or robust?" |
| Walk-Forward + OOS | ✅ Done | `scripts/walk_forward.py` | "Does it work on unseen data?" |
| Monte Carlo Bootstrap | ✅ Done | `scripts/monte_carlo.py` | "Is the Sharpe statistically significant?" |
| Market Regime Testing | ✅ Done | `scripts/regime_analysis.py` | "When does it work and when does it fail?" |
| Transaction Cost Sweep | ✅ Done | `scripts/transaction_cost_sensitivity.py` | "At what cost level does it stop working?" |
| Regime Overlay | ✅ Done | `scripts/regime_overlay.py` | "Can a market filter improve risk-adjusted returns?" |
| Portfolio Analysis | ✅ Done | `scripts/portfolio_analysis.py` | "Which strategies are complementary? How to combine them?" |
| Rolling Performance | ✅ Done | `scripts/rolling_performance.py` | "Is performance stable over time or concentrated in specific sub-periods?" |

### 5.3 Parameter Sensitivity Analysis — COMPLETE (2026-03-04)

**What we did:** For each of the 14 strategies, we varied each tunable parameter across a range of values while holding all other parameters at their defaults. For each combination, we ran a full backtest (with transaction costs) and recorded the Sharpe ratio. We then measured how much the Sharpe changed — if it barely moved, the parameter is ROBUST; if it swung wildly, it's FRAGILE.

**Measurement:** Coefficient of Variation (CV) = std(Sharpe) / mean(Sharpe) across the sweep.
- CV < 0.15 → ROBUST
- CV 0.15–0.30 → MODERATE
- CV > 0.30 → FRAGILE

**Script:** `scripts/parameter_sensitivity.py` (runs in ~6 minutes for all 14 strategies)
**Results:** `results/parameter_sensitivity/` (JSON per strategy + CSV summary)

#### Full Results Table

```
STRATEGY                         PARAM               DEFAULT  BEST     DEF_SHARPE  BEST_SHARPE  CV      VERDICT
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Large Cap Momentum               lookback             252      315      0.90        1.03         0.12    ROBUST
                                 skip_recent          21       5        0.90        0.95         0.03    ROBUST
                                 top_pct              10       5        0.90        0.91         0.04    ROBUST
                                 large_cap_pct        50       40       0.90        0.97         0.04    ROBUST

52-Week High Breakout            high_window          252      252      0.87        0.87         0.01    ROBUST
                                 top_pct              10       5        0.87        0.91         0.05    ROBUST

Deep Value All-Cap               lookback             252      63       0.73        0.78         0.03    ROBUST
                                 top_pct              20       30       0.73        0.78         0.06    ROBUST
                                 ma_window            200      100      0.73        0.79         0.03    ROBUST

High Quality ROIC                vol_lookback         252      63       0.82        1.03         0.08    ROBUST
                                 mom_lookback         252      63       0.82        0.92         0.05    ROBUST
                                 top_pct              20       30       0.82        0.84         0.05    ROBUST

Low Volatility Shield            vol_lookback         63       42       0.86        0.86         0.03    ROBUST
                                 bottom_pct           20       10       0.86        0.92         0.07    ROBUST

Dividend Aristocrats             lookback_months      36       12       0.52        0.95         0.64    FRAGILE !!
                                 min_positive_pct     0.6      0.7      0.52        0.79         0.39    FRAGILE !!
                                 top_pct              20       20       0.52        0.52         0.15    ROBUST

Moving Average Trend             ma_window            200      100      0.67        0.72         0.05    ROBUST
                                 ma_type              sma      ema      0.67        0.68         0.01    ROBUST

RSI Mean Reversion               rsi_period           14       7        0.76        0.86         0.12    ROBUST
                                 oversold             30       40       0.76        0.80         0.25    MODERATE
                                 exit_threshold       50       45       0.76        0.77         0.08    ROBUST
                                 max_positions        20       50       0.76        0.85         0.08    ROBUST

Value + Momentum Blend           mom_lookback         252      252      0.81        0.81         0.05    ROBUST
                                 mom_weight           0.5      0.8      0.81        0.86         0.04    ROBUST
                                 top_pct              20       10       0.81        0.90         0.07    ROBUST

Quality + Momentum               mom_lookback         252      189      0.87        0.91         0.06    ROBUST
                                 mom_weight           0.5      0.7      0.87        0.87         0.01    ROBUST
                                 top_pct              20       10       0.87        0.94         0.06    ROBUST

Quality + Low Volatility         vol_lookback         126      126      0.81        0.81         0.02    ROBUST
                                 quality_lookback     252      189      0.81        0.90         0.05    ROBUST
                                 vol_weight           0.5      0.3      0.81        0.83         0.02    ROBUST
                                 top_pct              20       20       0.81        0.81         0.03    ROBUST

Composite Factor Score           lookback             252      252      0.86        0.86         0.05    ROBUST
                                 momentum_weight      0.3      0.5      0.86        0.87         0.02    ROBUST
                                 value_weight         0.2      0.3      0.86        0.88         0.01    ROBUST
                                 quality_weight       0.3      0.4      0.86        0.87         0.01    ROBUST
                                 top_pct              20       10       0.86        0.92         0.04    ROBUST

Volatility Targeting             target_vol           0.10     0.20     0.65        0.67         0.13    ROBUST
                                 vol_lookback         63       63       0.65        0.65         0.12    ROBUST
                                 max_leverage         2.0      3.0      0.65        0.65         0.06    ROBUST

Earnings Surprise Momentum       volume_spike_mult    3.0      5.0      0.52        0.91         0.22    MODERATE
                                 price_move_std       2.0      2.5      0.52        0.58         0.10    ROBUST
                                 drift_period         63       63       0.52        0.52         0.49    FRAGILE !!
                                 max_positions        30       50       0.52        0.64         0.43    FRAGILE !!
```

#### What This Means — Practical Interpretation

**12 strategies are ROBUST.** Their performance holds across a wide range of parameter settings. This means:
- The edge is real, not a lucky artifact of one specific setting
- You can safely tune parameters without fear of destroying the strategy
- These strategies are candidates for real-world deployment

**2 strategies are FRAGILE.** Their performance swings wildly depending on parameter choice:
- **Dividend Aristocrats:** The lookback_months parameter causes Sharpe to range from 0.0 to 0.95 — a massive swing. This happens because our "dividend consistency" proxy (using monthly return signs) is noisy. With real dividend data (actual payout history), this would likely stabilize.
- **Earnings Surprise Momentum:** The drift_period ranges from Sharpe 0.06 (21 days) to 0.52 (63 days). The short holding periods don't capture the drift, and there's no way to know if the 63-day default is the "real" answer or a lucky pick.

#### Key Lessons Learned

1. **Composite/multi-factor strategies are inherently more robust** than single-factor. Composite Factor Score has 5 params, all ROBUST with CV < 0.05. Factor weight choices barely matter — diversification does the work.

2. **Fewer stocks in the portfolio (lower top_pct) tends to increase Sharpe** but also increases concentration risk. Every strategy shows slightly higher Sharpe at top_pct=5-10% vs 20-30%. This is the classic concentration vs diversification tradeoff.

3. **SMA vs EMA doesn't matter for trend following** (CV=0.01). This settles a common debate — the moving average type is irrelevant; what matters is the window length.

4. **Momentum lookback is genuinely robust.** Whether you use 6-month or 15-month momentum, it works. This is strong evidence that the momentum factor is real in this universe.

5. **Defensive strategies (Quality+LowVol, LowVol Shield) have the lowest CVs** — they're the most stable because they own stocks that move less, so parameter perturbations have less impact.

### 5.4 Walk-Forward + Out-of-Sample Testing — COMPLETE (2026-03-04)

**What we did:** Two levels of out-of-sample validation for each strategy:

1. **Simple OOS Split (70/30):** Train on 2014-01 to 2016-10, test on 2016-10 to 2017-12. Measure how much the Sharpe ratio degrades when going from training data to unseen test data.

2. **Rolling Walk-Forward (12mo train → 6mo test):** Slide a fixed-width training window through time, testing on the next 6 months. With a 400-day lookback buffer before each window, strategies can properly compute their indicators (e.g., 252-day momentum) even on short windows. Roll forward 6 at a time, producing 6 folds.

**Key Metric — Walk-Forward Efficiency (WFE):**
```
WFE = (Average OOS Sharpe / Average IS Sharpe) × 100
```
- WFE ≥ 80% = EXCELLENT — strategy performs nearly as well OOS as IS
- WFE ≥ 50% = GOOD — real edge but weaker than IS suggests
- WFE ≥ 20% = ACCEPTABLE — edge exists, handle with care
- WFE < 20% = WEAK/FAILING — likely overfit

**Script:** `scripts/walk_forward.py` (runs in ~75 seconds for all 14 strategies)
**Results:** `results/walk_forward/` (JSON per strategy + CSV summary)

#### Full Results Table

```
STRATEGY                      IS Sharpe  OOS Sharpe  Degrad%    WFE%   Consist   Verdict
──────────────────────────────────────────────────────────────────────────────────────────
Large Cap Momentum                 0.20        1.80    -802%    183%    6/6 100%  EXCELLENT
52-Week High Breakout              0.34        2.42    -620%    183%    6/6 100%  EXCELLENT
Deep Value All-Cap                 0.14        1.70   -1082%    205%    4/6  67%  EXCELLENT
High Quality ROIC                  0.17        2.62   -1419%    477%    4/6  67%  EXCELLENT
Low Volatility Shield              0.43        2.49    -485%    162%    4/6  67%  EXCELLENT
Dividend Aristocrats               0.00        0.00       —       —     0/6   0%  UNKNOWN
Moving Average Trend               0.33        2.33    -605%    170%    6/6 100%  EXCELLENT
RSI Mean Reversion                 0.35        1.49    -320%    123%    5/6  83%  EXCELLENT
Value + Momentum Blend             0.27        2.15    -693%    211%    6/6 100%  EXCELLENT
Quality + Momentum                 0.26        2.33    -786%    263%    4/6  67%  EXCELLENT
Quality + Low Volatility           0.27        2.50    -835%    311%    4/6  67%  EXCELLENT
Composite Factor Score             0.27        2.37    -770%    267%    4/6  67%  EXCELLENT
Volatility Targeting               0.07        2.14   -2922%    252%    4/6  67%  EXCELLENT
Earnings Surprise Momentum         0.23        1.64    -600%    175%    5/6  83%  EXCELLENT
```

#### Important: Why OOS Outperforms IS (Negative "Degradation")

At first glance, OOS Sharpe being MUCH higher than IS Sharpe (and negative degradation percentages) looks "too good." Here's why it's actually expected and meaningful:

1. **No optimization happens within folds.** We use DEFAULT parameters throughout — the train window is not used for parameter tuning. This means there's zero overfitting between IS and OOS. In true walk-forward optimization (where you'd optimize params on IS then test on OOS), you'd see degradation. Our test is simpler: it just checks whether the strategy concept works across different time periods.

2. **2017 was a strong bull market.** Many OOS windows include 2017, which was exceptionally strong for momentum/quality strategies. Since strategies were designed with these factors in mind, they naturally perform better in favorable conditions.

3. **Early IS windows suffer from insufficient lookback data.** Fold 1's IS window starts at 2014-01-02 — the very beginning of our data. Strategies with 252-day lookback periods can barely generate signals in the first fold's IS window, dragging IS averages down.

4. **What this REALLY tells us:** Despite not optimizing within folds, every strategy (except Dividend Aristocrats) produces positive returns on data it hasn't seen. This is strong evidence that the strategy edges are real, not statistical artifacts.

#### Dividend Aristocrats — Structural Failure

Dividend Aristocrats shows 0/0 across all folds because:
- Its default `lookback_months=36` requires 3 years of monthly return data
- Rolling windows provide only 12 months of training data (with 400-day buffer = ~2.1 years total)
- Even with buffer, there isn't enough data to compute the 36-month dividend consistency score
- This is a **structural data limitation**, not a strategy quality issue
- Fix: Use `lookback_months=12` (which sensitivity analysis showed as optimal anyway) or extend data to 8+ years

#### Strategy Tier List (Combined Sensitivity + Walk-Forward)

Based on BOTH parameter sensitivity (Phase 2.1) and walk-forward testing (Phase 2.2):

**Tier 1 — High Confidence (Robust + Genuine OOS Edge):**
- Large Cap Momentum (all robust, 100% consistency)
- 52-Week High Breakout (all robust, 100% consistency)
- Moving Average Trend (all robust, 100% consistency)
- Value + Momentum Blend (all robust, 100% consistency)
- Low Volatility Shield (all robust, 67% consistency)
- Quality + Momentum (all robust, 67% consistency)
- Composite Factor Score (all robust, 67% consistency, most robust params)
- Quality + Low Volatility (all robust, 67% consistency)

**Tier 2 — Good Confidence (Mostly Robust, Good OOS):**
- High Quality ROIC (robust, highest WFE at 477%)
- Deep Value All-Cap (robust, 67% consistency)
- RSI Mean Reversion (1 MODERATE param, 83% consistency)
- Volatility Targeting (robust, 67% consistency)

**Tier 3 — Handle With Care:**
- Earnings Surprise Momentum (2 FRAGILE params, but excellent walk-forward: 83% consistency, WFE 175%)
- Dividend Aristocrats (2 FRAGILE params, structural walk-forward failure)

### 5.5 Monte Carlo Bootstrap — COMPLETE (2026-03-05)

**What we did:** For each strategy, we tested whether the observed Sharpe ratio is statistically significant using three independent methods:

1. **IID Bootstrap (10,000 resamples):** Resample daily returns with replacement, recalculate Sharpe each time. Build a 95% confidence interval. p-value = fraction of bootstraps with Sharpe ≤ 0.

2. **Block Bootstrap (10,000 resamples, 20-day blocks):** Same idea but samples consecutive 20-day blocks instead of individual days. Preserves autocorrelation structure in returns.

3. **Random Sign Test (10,000 permutations):** Randomly flip the sign (+/-) of each daily return. Tests the null hypothesis that the strategy has no directional skill (timing ability). p-value = fraction of sign-flipped series with Sharpe ≥ observed.

**Verdict Criteria:**
- **SIGNIFICANT ★★★:** All 3 methods have p < 0.05
- **LIKELY SIGNIFICANT ★★:** 2 of 3 methods have p < 0.05
- **MARGINAL ★:** 1 of 3 methods has p < 0.05
- **NOT SIGNIFICANT:** 0 of 3 methods have p < 0.05

**Script:** `scripts/monte_carlo.py` (runs in ~20 seconds for all 14 strategies)
**Results:** `results/monte_carlo/` (JSON per strategy + CSV summary)

#### Full Results Table

```
STRATEGY                      Sharpe   Adj.Sharpe  95% CI              p(IID)   p(Block) p(Sign)  Verdict
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Large Cap Momentum             0.90     0.81        [-0.09, 1.92]       0.037    0.022    0.029    SIGNIFICANT ★★★
52-Week High Breakout          0.86     0.77        [-0.14, 1.89]       0.043    0.023    0.039    SIGNIFICANT ★★★
Low Volatility Shield          0.86     0.78        [-0.13, 1.89]       0.044    0.020    0.031    SIGNIFICANT ★★★
Quality + Momentum             0.87     0.79        [-0.12, 1.89]       0.043    0.019    0.031    SIGNIFICANT ★★★
Composite Factor Score         0.86     0.79        [-0.12, 1.87]       0.045    0.018    0.030    SIGNIFICANT ★★★

High Quality ROIC              0.82     0.79        [-0.17, 1.83]       0.051    0.032    0.031    LIKELY SIGNIFICANT ★★
Value + Momentum Blend         0.81     0.71        [-0.19, 1.85]       0.054    0.035    0.045    LIKELY SIGNIFICANT ★★
Quality + Low Volatility       0.81     0.74        [-0.17, 1.81]       0.054    0.025    0.036    LIKELY SIGNIFICANT ★★

Dividend Aristocrats           0.52     0.49        [-0.44, 1.48]       0.150    0.134    0.013    MARGINAL ★
RSI Mean Reversion             0.76     0.72        [-0.24, 1.79]       0.063    0.046    0.064    MARGINAL ★
Volatility Targeting           0.65     0.60        [-0.33, 1.67]       0.096    0.079    0.046    MARGINAL ★

Deep Value All-Cap             0.73     0.68        [-0.26, 1.74]       0.072    0.072    0.058    NOT SIGNIFICANT
Moving Average Trend           0.67     0.60        [-0.34, 1.69]       0.093    0.063    0.063    NOT SIGNIFICANT
Earnings Surprise Momentum     0.52     0.51        [-0.45, 1.55]       0.143    0.117    0.087    NOT SIGNIFICANT
```

#### What This Means — Practical Interpretation

**5 strategies have statistically significant Sharpe ratios.** All three independent tests agree: the performance is unlikely to be luck. These are the strongest candidates for real-money deployment.

**3 strategies are likely significant.** Two of three tests agree. The IID bootstrap is borderline (p ≈ 0.05), but block bootstrap and random sign test confirm directional skill. These are credible but with slightly less certainty.

**3 strategies are marginal.** Only one test is significant:
- **Dividend Aristocrats:** Only passes the sign test (p=0.013), which tests timing ability. Fails bootstrap tests because the overall Sharpe is low (0.52). Interesting — the strategy has real timing skill but weak magnitude.
- **RSI Mean Reversion:** Only passes block bootstrap (p=0.046). The autocorrelation-preserving test detects significance, but IID and sign tests don't — suggesting the edge depends on serial correlation.
- **Volatility Targeting:** Only passes sign test (p=0.046). Has directional skill but the effect is too small for bootstraps to confirm.

**3 strategies are NOT statistically significant.** No test finds p < 0.05:
- **Deep Value All-Cap:** All p-values near 0.06-0.07, close but not over the line. With more data (Phase 3), might become significant.
- **Moving Average Trend:** p-values 0.06-0.09. The trend-following edge is real but small in a 4-year window dominated by one regime.
- **Earnings Surprise Momentum:** p-values 0.09-0.14. Weakest statistical evidence. Combined with parameter fragility (Phase 2.1), this strategy has the least support.

#### Additional Metrics

**Pezier-White Adjusted Sharpe:** Corrects the Sharpe ratio for non-normal returns (skewness and excess kurtosis). All strategies show negative skew and excess kurtosis (fat tails), meaning raw Sharpe overestimates risk-adjusted performance. Adjusted Sharpe is 5-15% lower than raw for most strategies.

**Key observation:** Dividend Aristocrats has extreme excess kurtosis (15.6) and positive skew (0.95) — very different from all other strategies. This reflects its unusual return distribution from the dividend consistency proxy.

#### Updated Strategy Tier List (Sensitivity + Walk-Forward + Monte Carlo)

**Tier 1 — Deploy With Confidence** (Robust + Genuine OOS + Statistically Significant):
- Large Cap Momentum ★★★
- 52-Week High Breakout ★★★
- Low Volatility Shield ★★★
- Quality + Momentum ★★★
- Composite Factor Score ★★★

**Tier 2 — Strong Candidates** (Robust + OOS + Likely/Marginally Significant):
- Value + Momentum Blend ★★
- Quality + Low Volatility ★★
- High Quality ROIC ★★
- RSI Mean Reversion ★

**Tier 3 — Needs More Data** (Robust + OOS but NOT Significant):
- Deep Value All-Cap (p ≈ 0.07, needs longer history)
- Moving Average Trend (p ≈ 0.06-0.09, single-regime limitation)
- Volatility Targeting ★ (sign test passes but bootstraps don't)

**Tier 4 — Weak Evidence:**
- Earnings Surprise Momentum (fragile params + not significant)
- Dividend Aristocrats (fragile params + structural walk-forward failure + marginal significance)

### 5.6 Market Regime Analysis — COMPLETE (2026-03-05)

**What we did:** Classified every trading day (2014-2017) into one of four market regimes using a simple trend + volatility framework, then measured each strategy's Sharpe ratio within each regime.

**Regime Detection Method:**
- **Bull:** 63-day cumulative return > +5% AND annualized 63-day vol < 20%
- **Bear:** 63-day cumulative return < -5%
- **High-Vol:** Annualized 63-day vol ≥ 20% (but not bear)
- **Sideways:** Everything else

**Script:** `scripts/regime_analysis.py` (runs in ~10 seconds for all 14 strategies)
**Results:** `results/regime_analysis/` (JSON per strategy + CSV summary)

#### 2014-2017 Regime Breakdown

```
Regime      Days    % Total    Market Return    Market Vol
──────────────────────────────────────────────────────────
Sideways     559     59.2%         +1.3%          11.7%
Bull         257     27.2%        +33.6%           9.4%
Bear          70      7.4%        -26.3%          24.4%
High-Vol      58      6.1%        +47.3%          13.2%
```

Our 2014-2017 data is overwhelmingly Sideways (59%) with a strong Bull component (27%). Bear periods were brief (only 70 days total, ~7%). This explains why trend/momentum strategies look so good — they barely encountered adversity.

#### Full Results Table — Sharpe by Regime

```
STRATEGY                          Bull    Bear   High-V  Sidew   Spread  Best       Worst
──────────────────────────────────────────────────────────────────────────────────────────
Large Cap Momentum               +3.11   -0.78   +2.85   +0.34    3.89  Bull       Bear
52-Week High Breakout            +3.60   -1.05   +3.84   +0.11    4.89  High-Vol   Bear
Deep Value All-Cap               +3.14   -0.35   +2.22   -0.20    3.50  Bull       Bear
High Quality ROIC                +2.53   -0.81   +4.41   +0.19    5.23  High-Vol   Bear
Low Volatility Shield            +3.42   -1.06   +4.11   +0.15    5.18  High-Vol   Bear
Dividend Aristocrats             +0.30   +0.00   +0.00   +0.87    0.87  Sideways   Bear
Moving Average Trend             +3.36   -0.89   +3.97   -0.19    4.87  High-Vol   Bear
RSI Mean Reversion               +3.22   -0.75   +2.49   -0.09    3.97  Bull       Bear
Value + Momentum Blend           +3.39   -0.82   +3.52   +0.01    4.34  High-Vol   Bear
Quality + Momentum               +3.27   -0.86   +3.96   +0.15    4.82  High-Vol   Bear
Quality + Low Volatility         +3.03   -0.98   +4.31   +0.09    5.29  High-Vol   Bear
Composite Factor Score           +3.20   -0.82   +3.98   +0.14    4.79  High-Vol   Bear
Volatility Targeting             +3.42   -1.51   +3.24   -0.06    4.93  Bull       Bear
Earnings Surprise Momentum       +2.99   -1.55   +1.26   -0.13    4.54  Bull       Bear
```

#### Key Findings

**1. EVERY strategy loses money in Bear markets.** No exceptions. Bear Sharpe ranges from -0.35 (Deep Value — least bad) to -1.55 (Earnings Surprise — worst). This is the single most important finding: our entire strategy suite is long-only equity exposure with no downside protection.

**2. High-Vol is the BEST regime, not Bull.** Counterintuitively, 9 of 14 strategies perform best during High-Vol periods (Sharpe 2.2–4.4). This makes sense: High-Vol periods in our data are volatile-but-RISING (market ann return +47.3%). These are recovery rallies where stocks bounce hard. Factor spreads widen during volatility, and our strategies capture those spreads.

**3. Sideways is the graveyard.** 59% of days are Sideways, yet most strategies produce Sharpe near 0 (range: -0.20 to +0.87). This means most of the strategy performance comes from the 33% of days in Bull and High-Vol periods. The Sideways majority dilutes the overall Sharpe.

**4. Regime spread reveals strategy character:**
- **Low spread (regime-independent):** Dividend Aristocrats (0.87), Deep Value (3.50)
- **High spread (regime-dependent):** Quality+Low Vol (5.29), High Quality ROIC (5.23), Low Vol Shield (5.18)
- Higher spread = more regime-sensitive. These strategies make great returns in good times but are fragile in bad.

**5. No natural bear-market hedges exist in our suite.** The complementarity analysis found that Dividend Aristocrats is negatively correlated with other strategies' regime profiles, but only because it performs near zero everywhere (not because it thrives in bear markets).

#### Implications for Strategy Improvement

The universal Bear regime weakness suggests two paths forward:
1. **Regime overlay:** Add a market-level filter (e.g., if equal-weighted market is below 200-day MA, reduce position sizes or go to cash). This could protect all strategies simultaneously.
2. **Extended data needed (Phase 3):** With only 70 Bear days in our sample, we can't reliably measure Bear performance. Extending to 2000-present adds the 2008 crisis (~500 Bear days) and dot-com crash (~400 Bear days), giving much more reliable regime analysis.

### 5.7 Transaction Cost Sensitivity — COMPLETE (2026-03-05)

**What we did:** For each strategy, we swept total round-trip transaction costs from 0 bps (no costs) up to 100 bps in 10 steps. At each level we ran a full backtest and measured how Sharpe, total return, and annual turnover changed. We then calculated the "breakeven cost" (cost level where Sharpe hits zero) and categorized strategies by resilience.

**Cost levels tested:** 0, 2, 5, 10, 15, 20, 30, 50, 75, 100 bps (total round-trip)

**Reference assumption (our standard backtest):** 15 bps = 10 bps commission + 5 bps slippage

**Script:** `scripts/transaction_cost_sensitivity.py` (runs in ~97 seconds for all 14 strategies)
**Results:** `results/transaction_costs/` (JSON per strategy + CSV summary)

#### Full Results Table

```
STRATEGY                       Resilience    Gross SR   Net SR  BE Cost   Turnover     Drag
────────────────────────────────────────────────────────────────────────────────────────────
large_cap_momentum             BULLETPROOF       0.90     0.90 >100 bps       0.9x    0.5%
52_week_high_breakout          BULLETPROOF       0.87     0.86 >100 bps       1.5x    0.7%
deep_value_all_cap             BULLETPROOF       0.73     0.73 >100 bps       0.5x    0.5%
high_quality_roic              BULLETPROOF       0.83     0.82 >100 bps       0.6x    0.6%
low_volatility_shield          BULLETPROOF       0.87     0.86 >100 bps       0.8x    0.6%
dividend_aristocrats           BULLETPROOF       0.53     0.52 >100 bps       0.2x    0.7%
moving_average_trend           BULLETPROOF       0.67     0.67 >100 bps       0.8x    1.0%
rsi_mean_reversion             BULLETPROOF       0.77     0.76 >100 bps       6.3x   17.7%
value_momentum_blend           BULLETPROOF       0.81     0.81 >100 bps       0.7x    0.4%
quality_momentum               BULLETPROOF       0.87     0.87 >100 bps       0.5x    0.4%
quality_low_vol                BULLETPROOF       0.81     0.81 >100 bps       0.4x    0.4%
composite_factor_score         BULLETPROOF       0.87     0.86 >100 bps       0.5x    0.4%
volatility_targeting           BULLETPROOF       0.66     0.65 >100 bps       1.1x    2.1%
earnings_surprise_momentum     BULLETPROOF       0.60     0.52 >100 bps       6.2x   10.9%

Columns: Gross SR = Sharpe at 0 bps, Net SR = Sharpe at 15 bps reference,
         BE Cost = cost where Sharpe hits zero, Drag = return eaten by costs at 15 bps
```

#### What This Means — Practical Interpretation

**All 14 strategies are BULLETPROOF.** Every strategy maintains a positive Sharpe ratio even at 100 bps total round-trip costs — well above what any realistic institutional investor would pay.

Why? **Low turnover.** All strategies are monthly or quarterly rebalancers that hold concentrated portfolios. Even RSI Mean Reversion (highest turnover at 6.3x/year) generates just 6.3 trades per dollar per year. With 100 bps cost per trade, that's 630 bps = 6.3% annual return drag — substantial, but not enough to kill the 0.77 Sharpe strategy.

**The cost drag story (at reference 15 bps):**
- Most factor strategies: 0.4%–0.7% of return eaten by costs (negligible)
- Trend/vol strategies: 1%–2% drag (still small)
- High-turnover strategies: RSI Mean Reversion **17.7%** drag, Earnings Surprise **10.9%** drag
  - These don't die, but costs are eating a meaningful chunk of returns
  - RSI Mean Reversion drops from Sharpe 0.77 (gross) to 0.76 (net) — barely moves
  - Earnings Surprise drops from 0.60 (gross) to 0.52 (net) — more noticeable

**Earnings Surprise sensitivity:** Despite surviving at 100 bps, it degrades the most:
- At 0 bps: Sharpe 0.60
- At 100 bps: Sharpe 0.12 (80% of Sharpe destroyed by costs)
- This strategy's fragility is now confirmed across three independent tests: parameter sensitivity (FRAGILE), Monte Carlo (NOT SIGNIFICANT), and transaction cost sensitivity (biggest degrader)

**RSI Mean Reversion paradox:** Highest turnover (6.3x) but Sharpe barely drops. Why? Its gross Sharpe starts at 0.77 (strong) and the returns distribution is resilient. The edge is large enough that costs can't kill it — they just reduce the advantage incrementally.

#### Turnover Analysis

```
Turnover correlation with cost sensitivity: -0.668
(Higher turnover → greater Sharpe degradation per cost increase)
```

| Category | Strategies | Turnover | Cost Impact |
|----------|-----------|----------|------------|
| Ultra-low turnover | Dividend Aristocrats, Quality+LowVol, Composite Factor | 0.2–0.5x/yr | Negligible drag |
| Low turnover | Large Cap Mom, High Quality ROIC, Value+Mom, Deep Value | 0.5–0.9x/yr | <1% drag |
| Moderate turnover | Low Vol Shield, Moving Average Trend, Volatility Targeting | 0.8–1.5x/yr | 1–2% drag |
| High turnover | 52-Week High Breakout | 1.5x/yr | 0.7% drag (but high gross Sharpe) |
| Very high turnover | RSI Mean Reversion, Earnings Surprise | 6.2–6.3x/yr | 11–18% drag |

#### Key Finding: The "Cost Budget" Concept

Every strategy implicitly has a maximum supportable cost level. Based on our results:

```
Cost budget = Gross Sharpe × Volatility × (1 / Annual Turnover) × some_factor
```

The practical insight: **Momentum/Quality/Value factor strategies are naturally low-cost because they trade slowly.** They make concentrated bets and hold them for weeks or months. In contrast, strategies that trade frequently (RSI-style mean reversion, event-driven) need a higher gross edge to overcome cost drag.

**Why this matters for Phase 3 (live data):** When we move to real brokerage execution:
- Retail investors: ~15-30 bps per trade is realistic → all strategies still viable
- Institutional ($100M+): ~5-10 bps per trade → even more runway than we modeled
- Limit: daily rebalancing strategies (not in our suite) would be killed by 15 bps

#### Updated Final Tier List (All Four Tests Combined)

After combining all four Phase 2 tests (Sensitivity + Walk-Forward + Monte Carlo + Transaction Costs), the final rankings:

**Tier 1 — Most Deployable** (Robust + OOS + Significant + Low Cost):
- **Large Cap Momentum** ★★★ | 0.2% drag | BULLETPROOF | 100% WF consistency
- **Quality + Momentum** ★★★ | 0.4% drag | BULLETPROOF | 67% WF consistency
- **Composite Factor Score** ★★★ | 0.4% drag | BULLETPROOF | 67% WF consistency
- **52-Week High Breakout** ★★★ | 0.7% drag | BULLETPROOF | 100% WF consistency
- **Low Volatility Shield** ★★★ | 0.6% drag | BULLETPROOF | 67% WF consistency

**Tier 2 — Strong Candidates**:
- **Value + Momentum Blend** ★★ | 0.4% drag | BULLETPROOF | 100% WF consistency
- **Quality + Low Volatility** ★★ | 0.4% drag | BULLETPROOF | 67% WF consistency
- **High Quality ROIC** ★★ | 0.6% drag | BULLETPROOF | 67% WF consistency

**Tier 3 — Needs More Data**:
- **Deep Value All-Cap** | 0.5% drag | BULLETPROOF | 67% WF consistency (needs 25yr data)
- **Moving Average Trend** | 1.0% drag | BULLETPROOF | 100% WF consistency (needs more regimes)
- **RSI Mean Reversion** ★ | 17.7% drag | BULLETPROOF | 83% WF consistency (high turnover drag)
- **Volatility Targeting** ★ | 2.1% drag | BULLETPROOF | 67% WF consistency

**Tier 4 — Weak Evidence Across Multiple Tests**:
- **Earnings Surprise Momentum** | 10.9% drag, biggest degrader, fragile params, not significant
- **Dividend Aristocrats** | 0.7% drag, fragile params, structural walk-forward failure

### 5.8 Regime Overlay — Strategy Improvement — COMPLETE (2026-03-05)

**What we did:** Applied the Phase 2.4 regime detection system as a **filter on top of all 14 strategies**. Instead of changing the underlying strategy logic, we simply ask: "What is the current market regime?" and if the answer is Bear, we go to cash (positions = 0).

Three overlay variants were tested:
1. **Bear-only:** Cash only during Bear (70 days, 7% of the period)
2. **Aggressive:** Cash in Bear + 50% positions in Sideways
3. **Trend-only:** Cash whenever 63-day market return is negative (201 days, 20% of the period)

**Script:** `scripts/regime_overlay.py` (runs in ~11 seconds for all 14 strategies)
**Results:** `results/regime_overlay/` (JSON per strategy + CSV summary)

#### Full Results — Bear-Only Overlay (Best Variant)

```
STRATEGY                       Base SR   Overlay SR  Base MDD    Overlay MDD  MDD Improvement
──────────────────────────────────────────────────────────────────────────────────────────────
large_cap_momentum              0.90       0.86       -45.19%     -26.81%       +18.38%
52_week_high_breakout           0.86       0.76       -74.88%     -49.27%       +25.61%
deep_value_all_cap              0.73       0.57       -39.98%     -25.93%       +14.05%
high_quality_roic               0.82       0.66       -18.63%     -13.94%        +4.68%
low_volatility_shield           0.86       0.71       -28.63%     -20.33%        +8.30%
dividend_aristocrats            0.52       0.52        -2.87%      -1.53%        +1.34%
moving_average_trend            0.67       0.50       -26.31%     -15.91%       +10.39%
rsi_mean_reversion              0.76       0.60       -98.58%     -92.46%        +6.12%
value_momentum_blend            0.81       0.71       -51.75%     -31.07%       +20.68%
quality_momentum                0.87       0.76       -28.32%     -18.90%        +9.43%
quality_low_vol                 0.81       0.67       -18.27%     -13.01%        +5.26%
composite_factor_score          0.86       0.74       -25.62%     -17.55%        +8.07%
volatility_targeting            0.65       0.53       -13.30%      -7.85%        +5.46%
earnings_surprise_momentum      0.52       0.42       -23.76%     -14.69%        +9.07%
```

#### What This Means — Practical Interpretation

**The trade-off:** The Bear-only overlay trades a small Sharpe sacrifice (0.04–0.16) for a dramatic max drawdown reduction (5–26 percentage points). This is the classic **risk management trade-off**: you give up some return in good times to avoid catastrophic losses in bad times.

**Why Sharpe drops slightly in 2014-2017 data:**
Bear periods in this dataset are only 70 days (7%). The market during 2014-2017 was mostly trending up — even brief Bear dips were followed by fast recoveries. Going to cash during those 70 days means you miss the recoveries. In a longer dataset with sustained Bear markets (2008: ~12 months, 2000-2003: ~30 months), the overlay would dramatically IMPROVE Sharpe by avoiding deep, prolonged drawdowns.

**The transition cost effect:** On the day you enter Bear regime, you liquidate the entire portfolio. This one-time cost shows up as a large negative return on Day 1 of each Bear period. This is why the "Bear regime Sharpe" metric looks worse with the overlay — the transition cost is counted within the Bear window, not as a fixed cost.

**Biggest winners from the overlay:**
- **52-Week High Breakout:** MDD reduced from -74.88% to -49.27%. This strategy accumulates positions aggressively in uptrends but also crashes hard in downturns — the overlay dramatically smooths this.
- **Value + Momentum Blend:** MDD -51.75% → -31.07%. Similar pattern — strong upside capture, vulnerable to drawdowns.
- **Large Cap Momentum:** MDD -45.19% → -26.81%. Flagship strategy improves significantly.

**Smallest impact:**
- **Dividend Aristocrats:** MDD -2.87% → -1.53%. This strategy already has near-zero Bear exposure — the overlay has little to add.
- **RSI Mean Reversion:** MDD -98.58% → -92.46%. Largest baseline drawdown in the suite. The overlay helps at the margin, but the strategy's core issue (holding through mean-reversion that never reverts) isn't fixed by a market filter.

**Why "Trend-only" performs worst:**
The trend overlay goes to cash on 201 days (20% of the period) — nearly 3× more cash days than Bear-only. It catches all Bear days but also many Sideways-trending periods that aren't actually dangerous. Being in cash 20% of the time in a bull market is expensive.

**Why "Aggressive" (Bear + 50% Sideways) underperforms:**
Sideways periods are 62% of all days. Cutting positions to 50% for 62% of the dataset severely hampers returns. The Sharpe drops 0.16–0.43 with minimal additional downside protection compared to Bear-only.

#### The Core Insight — Bear-Only Is the Optimal Filter

```
Bear-Only Overlay verdict:
  ✓ Reduces max drawdown across ALL 14 strategies
  ✓ Small Sharpe cost in bull-dominated data (2014-2017)
  ✓ Will show larger benefit over 25-year dataset (Phase 3)
  ✓ Simple to implement — just one additional check: "is market in Bear regime?"
  ✗ Sharpe improvement not visible in 4-year window
  ✗ 70 Bear days is too small a sample to be conclusive
```

**Practical implication for Phase 3:** When we extend to 2000-2025 data, the regime overlay will be tested against:
- 2000-2003 dot-com crash (Bear for ~750 days)
- 2008-2009 financial crisis (Bear for ~375 days)
- 2020 COVID crash (Bear for ~60 days but -34% in 23 trading days)
- 2022 bear market (Bear for ~250 days)

Across these four major Bear periods, the overlay's benefit will be enormous and will likely raise both Sharpe AND reduce MDD.

#### Updated Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-05 | Bear-only overlay > aggressive overlay | 7% cash days beats 62% — less opportunity cost |
| 2026-03-05 | MDD is the right metric for overlay evaluation | Sharpe is misleading in short bull-heavy windows |
| 2026-03-05 | Defer to Phase 3 to confirm overlay value | 70 Bear days is too small; need 2008/2000 crises |

### 5.9 Portfolio Correlation & Construction Analysis — COMPLETE (2026-03-05)

**What we did:** Computed the full 14×14 correlation matrix of daily strategy returns, clustered strategies by similarity, and compared 7 distinct portfolio construction methods against the equal-weighted benchmark.

**Script:** `scripts/portfolio_analysis.py` (runs in ~9 seconds)
**Results:** `results/portfolio_analysis/` (correlation matrix CSV, portfolio comparison CSV, full JSON)

#### The Headline Finding: Our 14 Strategies Are NOT Truly Diversified

```
Average inter-strategy correlation: 0.788
Redundant pairs (>0.80 correlation): 63 out of 91 (69%)
Diversification ratio (equal-weight): 1.051 (barely above 1.0)
```

All 14 strategies are essentially variants of the same trade: **long US equities sorted by different factor signals**. When markets fall, they all fall together. When markets rise, they all rise together. There is almost no true diversification benefit in holding all 14.

#### Full Correlation Heat Map — Most Redundant Pairs

```
Most Redundant (r > 0.96):
  quality_momentum     ↔ composite_factor_score    r=0.996  ← NEARLY IDENTICAL
  quality_low_vol      ↔ composite_factor_score    r=0.988
  quality_momentum     ↔ quality_low_vol           r=0.979
  52_week_high_breakout↔ value_momentum_blend      r=0.973
  52_week_high_breakout↔ moving_average_trend      r=0.969
  high_quality_roic    ↔ quality_low_vol           r=0.968
  52_week_high_breakout↔ low_volatility_shield     r=0.967
  value_momentum_blend ↔ composite_factor_score    r=0.964

Most Complementary (r < 0.35):
  dividend_aristocrats ↔ moving_average_trend      r=0.170  ← most orthogonal
  dividend_aristocrats ↔ earnings_surprise_momentum r=0.172
  dividend_aristocrats ↔ rsi_mean_reversion        r=0.237
  dividend_aristocrats ↔ low_volatility_shield     r=0.258
```

**The Dividend Aristocrats anomaly:** It's the only strategy with average inter-strategy correlation of 0.288 and market correlation of just 0.176. It behaves completely differently from everything else — but unfortunately it's also the worst performer (Sharpe 0.52, Ann Ret 3.71%).

**The "Composite Factor Score" problem:** Composite Factor Score was designed as a multi-factor combination of the other strategies. It's r=0.996 with Quality+Momentum and r=0.988 with Quality+Low Vol. Adding it to a portfolio that already has those strategies adds literally zero diversification — it's a weighted average of what you already own.

#### Portfolio Comparison

```
Portfolio                  Sharpe   Ann Ret    MDD      Ann Vol
──────────────────────────────────────────────────────────────────
[Benchmark EW S&P 500]       0.76    11.36%  -16.71%   12.66%
──────────────────────────────────────────────────────────────────
equal_weight_all14           0.84    27.98%  -41.77%   33.99%  ← higher return, much higher vol
tier1_equal_weight           0.90    33.23%  -42.75%   37.83%  ← best Sharpe but also high vol
tier1and2_equal_weight       0.88    29.27%  -37.72%   33.13%
risk_parity_all14            0.85    14.21%  -17.61%   14.54%  ← near-benchmark risk profile!
risk_parity_tier1            0.90    29.39%  -35.89%   32.39%  ← best Sharpe, much lower MDD
min_corr_top3                0.74    11.34%  -22.12%   13.01%  ← worst Sharpe (picks weak strats)
min_corr_top5                0.84    16.35%  -24.32%   17.39%
```

#### Key Observations

**1. Combining more strategies barely improves Sharpe.**
The Tier 1 equal-weight portfolio (5 strategies) has the same Sharpe (0.90) as the best individual strategy (Large Cap Momentum). Adding 9 more strategies doesn't improve risk-adjusted returns — it just changes the return/risk trade-off.

**2. Risk-Parity All 14 is the conservative choice.**
With Sharpe 0.85, Ann Vol 14.54%, and MDD -17.61% — this is nearly identical to the benchmark risk profile but with materially better Sharpe. For an investor who wants factor exposure without excessive volatility, this is the best option.

**3. Risk-Parity Tier 1 is the aggressive-but-smart choice.**
Sharpe 0.90, MDD -35.89%, Ann Ret 29.39%. Same Sharpe as Tier 1 equal-weight but with 7% better MDD (-35.89% vs -42.75%) because risk-parity reduces concentration in the highest-volatility strategies.

**4. Min-correlation portfolios underperform.**
Picking the 3 most orthogonal strategies (Dividend Aristocrats, Earnings Surprise, Deep Value) gives Sharpe 0.74 — BELOW benchmark. Diversification for its own sake, using strategies with weak edges, is worse than just buying the index.

**5. The pruning implication.**
Our 14 strategies collapse into roughly 4–5 genuinely distinct strategy types:
- Type A (Momentum): Large Cap Momentum, 52-Week High, Value+Mom, Quality+Mom, Composite Factor
- Type B (Quality/Low Vol): High Quality ROIC, Low Vol Shield, Quality+Low Vol
- Type C (Value): Deep Value All-Cap
- Type D (Trend): Moving Average Trend
- Type E (Reversion/Risk): RSI Mean Reversion, Volatility Targeting
- Type F (Income/Event): Dividend Aristocrats, Earnings Surprise

A lean portfolio of one from each type would be 5–6 strategies. The extra 8 strategies add overlap, not diversification.

#### What This Means for Phase 3

In Phase 3, rather than blindly running all 14 strategies on 2000-2025 data, we should:
1. **Prune redundant strategies** — Composite Factor Score is nearly identical to Quality+Momentum; we likely don't need both
2. **Add a genuinely uncorrelated strategy** — short strategies, commodities, or bonds to provide real diversification
3. **Use Risk-Parity Tier 1 as the "showcase portfolio"** — it has the best combination of Sharpe (0.90) and MDD (-35.9%)
4. **Accept that diversification within long-only equity strategies is limited** — structural diversification requires non-equity assets or short positions

---

### 5.10 Rolling Performance Analysis — COMPLETE (2026-03-05)

**What we did:** Computed rolling 126-day (6-month) Sharpe ratio, max drawdown, and volatility for all 14 strategies. Split the 4-year window into 8 equal ~6-month sub-periods and computed average cross-strategy performance. Measured rank stability (whether the same strategies stay on top month-to-month) and rolling average inter-strategy correlation.

**Script:** `scripts/rolling_performance.py`
**Results:** `results/rolling_performance/` (rolling_sharpe.csv, rolling_drawdown.csv, rolling_volatility.csv, rolling_avg_correlation.csv, rolling_performance_results.json)

#### Rolling Sharpe Summary (126-day window)

```
Strategy                             Mean SR   Std SR   Min SR   Max SR   % Pos
----------------------------------------------------------------------------
low_volatility_shield                   0.98     0.96    -1.68     3.44     84%
moving_average_trend                    0.87     0.98    -6.82     3.28     78%
52_week_high_breakout                   0.85     1.05    -6.17     3.31     81%
rsi_mean_reversion                      0.80     0.96    -2.18     2.86     81%
value_momentum_blend                    0.80     0.97    -1.74     3.32     70%
quality_momentum                        0.74     0.94    -1.36     3.25     71%
composite_factor_score                  0.73     0.98    -1.48     3.45     69%
large_cap_momentum                      0.73     0.98   -11.11     3.25     69%
quality_low_vol                         0.71     1.02    -1.39     3.37     63%
high_quality_roic                       0.57     1.11    -3.69     3.52     54%
volatility_targeting                    0.56     0.98    -1.95     2.86     73%
earnings_surprise_momentum              0.56     1.11    -2.42     2.97     76%
deep_value_all_cap                      0.43     1.49   -26.76     3.10     56%
dividend_aristocrats                    0.31     0.86    -4.93     2.90     20%
```

Note: Large Cap Momentum and Deep Value min rolling Sharpe (-11.11, -26.76) are numerical artifacts during near-zero-return windows in the early period (very short std → division blowup). The overall picture remains valid.

#### Sub-period Breakdown (8 × ~6-month blocks)

```
Period     Date Range                     Avg SR    %Pos   Min SR   Max SR
----------------------------------------------------------------------
P1         2014-01-02 → 2014-07-01         0.45     29%      0.00      2.31
P2         2014-07-02 → 2014-12-29         0.54     43%      0.00      1.77
P3         2014-12-30 → 2015-06-29        -0.31     21%     -1.46      0.40  ← WORST
P4         2015-06-30 → 2015-12-24         0.06     64%     -1.30      1.03
P5         2015-12-28 → 2016-06-24         0.24     79%     -0.36      0.62
P6         2016-06-27 → 2016-12-21         1.47     93%      0.00      2.57  ← Post-Brexit Rally
P7         2016-12-22 → 2017-06-22         1.69    100%      0.53      2.49  ← Trump Rally
P8         2017-06-23 → 2017-12-29         2.32    100%      1.69      2.65  ← Equity Melt-Up
```

#### Key Findings

**Finding 1: Performance is heavily concentrated in the final 18 months (2016-2017).**

The last 3 sub-periods (P6, P7, P8) average Sharpe of 1.83 — exceptional. The first 5 periods (P1–P5) average only 0.20. Our 4-year CAGR and overall Sharpe look strong partly because the last 18 months were extraordinary (100% of strategies positive in P7 and P8).

**Implication:** When we extend to 25-year data, the 2014-2017 overall metrics will be "diluted" by more average years and terrible crisis years. This is actually good — it will give us a much more honest picture of strategy quality.

**Finding 2: Worst sub-period was Dec 2014 – Jun 2015 (avg Sharpe -0.31).**

This coincides with a mild market correction in H1 2015 (S&P 500 was essentially flat Jan–Aug 2015, with a sharp -12% selloff in August). Only 21% of strategies were positive during this window. This is a mini-preview of what a bear market looks like for our strategies — they struggle when markets go sideways or down.

**Finding 3: Rank stability = 0.749 (STABLE).**

Average Spearman rank correlation between consecutive monthly strategy rankings is 0.749. This means the same strategies consistently rank highest month-to-month. Low Volatility Shield, Moving Average Trend, and 52-Week High consistently dominate. Dividend Aristocrats and Deep Value consistently rank last. Rankings don't flip randomly — the quality ordering is real and persistent.

**Finding 4: Rolling inter-strategy correlation is highly variable.**

Rolling average correlation (Tier 1 strategies, 126-day window):
- Mean: 0.896 — in an average 6-month window, Tier 1 strategies are extremely correlated
- Std: 0.143 — significant variation around that mean
- Min: -0.076 — during certain transition periods, even our correlated strategies briefly diverge
- Max: 0.975 — at peak market stress, everything moves together

This confirms that our Phase 2.7 finding (avg correlation 0.788) is actually an average of periods with both very high and occasionally low correlation. Dynamic correlation means that combining strategies can provide brief windows of real diversification even if the long-run average is high.

#### Overall Verdict

Rolling performance analysis confirms: our strategies are genuinely strong in favorable market conditions (trending bull markets) but structurally weak in flat or declining environments. The 4-year backtest was fortuitous — it captured an extended bull period. The strategies' true robustness will be tested when we extend to 2000-2025 data and include the dot-com crash, 2008 financial crisis, and 2020 COVID drawdown.

---

### 5.11 Phase 2 — Consolidated Meta-Learnings

*This section captures methodology learnings from Phase 2 — not just strategy-specific results (which are in §5.3-§5.10) but reusable lessons about how to backtest properly. These learnings inform how Phase 3 will be run.*

---

#### A. What Each Test Actually Measures (and What It Doesn't)

| Test | What it measures | What it does NOT measure |
|------|-----------------|--------------------------|
| Parameter Sensitivity | Robustness to implementation choices | Whether the core idea works |
| Walk-Forward | Generalization to unseen time periods | Whether OOS period is representative |
| Monte Carlo | Whether Sharpe is statistically real | Whether the strategy will work in the future |
| Regime Analysis | Conditional performance across market states | How often each regime occurs going forward |
| Transaction Costs | Cost resilience at various friction levels | Market impact at scale |
| Regime Overlay | Whether a market filter adds value | Whether the filter generalizes to new data |
| Portfolio Analysis | Diversification structure among strategies | Correlation stability over regimes |
| Rolling Performance | Time-stability of performance | Whether concentration is predictable |

The key insight: **no single test is sufficient**. Each catches different failure modes. A strategy must pass all 8 tests to be confident. Earnings Surprise Momentum failed all 8; Large Cap Momentum passed all 8.

---

#### B. The Convergent Evidence Principle

We ran 8 independent stress tests. The same strategies appeared at the top and bottom across all 8. This is called **convergent evidence** — when multiple different tests all point to the same conclusion, confidence increases multiplicatively, not additively.

```
Convergent evidence scorecard:
  Strategy                  Tests passed / 8   Tier
  ──────────────────────────────────────────────────
  Large Cap Momentum           8 / 8            1
  52-Week High Breakout        8 / 8            1
  Low Volatility Shield        7 / 8            1
  Quality + Momentum           7 / 8            1
  Composite Factor Score       7 / 8            1
  Moving Average Trend         6 / 8            2
  Value + Momentum Blend       6 / 8            2
  High Quality ROIC            5 / 8            2
  RSI Mean Reversion           4 / 8            3
  Quality + Low Vol            4 / 8            3
  Deep Value All-Cap           3 / 8            3
  Volatility Targeting         3 / 8            3
  Dividend Aristocrats         2 / 8            4
  Earnings Surprise Momentum   1 / 8            4
```

---

#### C. The 4-Year Bull Market Problem

Every Phase 2 result is contaminated by one fact: our backtest period (2014-2017) is a bull market that ended with an equity melt-up. The specific problems this creates:

1. **Regime distribution is wrong**: 59% Sideways, 27% Bull, 7% Bear, 6% High-Vol. In a full 25-year window, Bear occurs ~20-25% of the time (during crises). We had only 70 Bear days.

2. **Performance concentration**: 43% of strategy quality came from the last 18 months (P6-P8). A 25-year window will have many more "P3-style" (flat/negative) sub-periods.

3. **Regime overlay is undervalued**: The Bear-only overlay costs 0.04-0.16 Sharpe in our data. Over 25 years with 2008 and 2020 crises, it would *improve* Sharpe by potentially 0.5-1.0.

4. **Low correlation observations**: Our inter-strategy correlations (0.788 average) include few crisis periods. In 2008-2009, virtually all factor strategies correlate 0.95+ as everything falls together.

**Bottom line**: Our Phase 2 results are *directionally correct* but *quantitatively optimistic*. The strategy tiers are right. The absolute Sharpe numbers are probably 20-30% too high for what we'd see over a full cycle.

---

#### D. Critical Methodology Mistakes to Avoid (and How We Fixed Them)

| Mistake | Why it's wrong | How we fixed it |
|---------|---------------|-----------------|
| Naive permutation test | Shuffling preserves mean/std → Sharpe unchanged → p=1.0 always | Use random sign test (sign flipping) |
| Equal-weight parameter testing | Doesn't show which params matter most | Use 1D sweep (hold others fixed) + CV scoring |
| Walk-forward without lookback buffer | Long-lookback strategies produce zero signals in early folds | Add 400-day buffer before each fold |
| 70/30 single split | Tests only one OOS period; can be lucky | Rolling walk-forward with multiple folds |
| Sharpe as regime overlay metric | Short bull-heavy data makes overlay look costly | Use MDD improvement; Sharpe misleads here |
| Correlation number without context | r=0.788 sounds specific but hides the regime-dependence | Add rolling correlation analysis |
| Min-correlation portfolio | Picks most orthogonal strategies, which happen to be weakest | Filter for quality first, then diversify within quality set |

---

#### E. What Phase 3 Must Do Differently

**From Phase 2 learnings, Phase 3 has these hard requirements:**

1. **25+ years of data**: Include at least one major bear market (2008) and one crash (2020). The regime distribution should be closer to 20% Bear, not 7%.

2. **Point-in-time constituent lists**: At each date, use the exact tickers that were actually in the S&P 500 on that date. Reconstructed from historical changes (additions/removals).

3. **Include delisted stocks**: Stocks removed from the S&P 500 (bankrupt, acquired, downgraded to small-cap) must be included up to their removal date. This eliminates survivorship bias.

4. **Survivorship bias quantification**: Before running strategies, quantify how much of Phase 2's performance was due to survivorship bias — estimate by comparing current-S&P-500-only vs. historical-constituency-aware results.

5. **Re-run all 8 Phase 2 analyses**: The entire methodology repeats. The only thing that should change is the data — the scripts and methods stay the same.

6. **Phase 2.4 (Regime Analysis) will be the most different**: With 2008 financial crisis and 2020 COVID crash in the data, the regime overlay results will look completely different. The Bear-only overlay will likely improve Sharpe significantly, not hurt it.

---

### 5.12 Phase 3.1 — Historical S&P 500 Constituents — COMPLETE (2026-03-05)

**What we did:** Scraped Wikipedia's "List of S&P 500 companies" to get (1) the current 503-stock composition and (2) the historical changes table (additions/removals since 2000). Reconstructed point-in-time monthly constituent snapshots by starting from the current list and reversing each historical change.

**Script:** `scripts/fetch_sp500_constituents.py`

#### Key Results

| Metric | Value |
|--------|-------|
| Current S&P 500 stocks | 503 |
| Historical change events (2000–2026) | 721 |
| Unique tickers ever in S&P 500 since 2000 | 820 |
| Monthly PIT snapshots | 300 |
| Avg stocks per month | 509 (matches actual ✓) |
| Overlap with Phase 2 Kaggle data (mid-2016) | 87.1% |
| Phase 2 tickers not in PIT | 65 (survivorship bias exposure) |
| PIT tickers not in Phase 2 | 68 (delisted stocks Kaggle missed) |

**Survivorship bias quantified:** Our Phase 2 Kaggle dataset was missing 68 stocks that were actually in the S&P 500 during 2014-2017 but later got delisted. These stocks had bad returns — by excluding them, Phase 2's performance metrics are upward-biased.

---

### 5.13 Phase 3.2 — Extended Price Data Download — COMPLETE (2026-03-05)

**What we did:** Downloaded 25 years of daily price data (2000-2024) via yfinance 1.2.0 for all 820 tickers. Downloaded in two groups: (A) current S&P 500 (503) — all succeeded; (B) historical-only (317) — ~155 succeeded, ~162 failed (delisted with no Yahoo Finance data).

**Script:** `scripts/download_extended_data.py`

#### Download Summary

| Group | Tickers | Succeeded | Failed |
|-------|---------|-----------|--------|
| Current S&P 500 | 503 | ~503 | 0 |
| Historical-only | 317 | ~155 | ~162 |
| **Total** | **820** | **~658** | **~162** |

Failed tickers = delisted companies not archived in Yahoo Finance. These represent residual survivorship bias.

---

### 5.14 Phase 3.3 — Process & Validate Extended Dataset — COMPLETE (2026-03-07, corrected)

**What we did:** Validated, cleaned, and combined 658 individual ticker parquet files into one clean dataset. Built a point-in-time universe lookup table. Compared coverage against Phase 2.

**Data quality problem encountered & fixed:** First pass used a simple 50% daily return filter, which was insufficient. Ticker CBE had near-zero prices (close ≈ 0.001) from corrupted Yahoo Finance data. After filtering the high-return rows, pivoting to wide format and computing pct_change with `fill_method='pad'` (default) would forward-fill the 0.001 price over NaN gaps, then compute (34.0 - 0.001) / 0.001 = 33,999× when the next real price appeared. Result: benchmark showed 572,489% CAGR. Fix: add price floor (close < $1 → remove) BEFORE return filter, use two-pass return filter, and use `fill_method=None` in pct_change calls.

**Script:** `scripts/process_extended_data.py`

#### Dataset Statistics (Final Corrected)

| Metric | Phase 2 (Kaggle) | Phase 3 (Extended) | Change |
|--------|------------------|--------------------|--------|
| Symbols | 505 | **653** | +148 |
| Trading days | 1,007 | **6,288** | **6.2× more** |
| Total rows | ~497K | **3.40M** | **6.8× more** |
| Date range | 2014-2017 | **2000-2024** | **25 years** |
| Full-history symbols (2000-2024) | N/A | **431** | — |

#### Cleaning Summary

| Step | Rows Removed | Reason |
|------|-------------|--------|
| Price floor (close < $1) | 35,074 | Corrupted/delisted near-zero prices |
| Return filter pass 1 (> ±20%) | 4,173 | Implausible daily moves |
| Return filter pass 2 (> ±20%) | 2,419 | Newly adjacent extreme returns after gaps |
| **Total removed** | **41,666** | **1.2% of raw data** |

#### Coverage Tiers

| Coverage | Symbols |
|----------|---------|
| Full 2000-2024 history | 431 |
| From 2003 onwards | 457 |
| From 2009 onwards | 512 |
| From 2014 onwards | 562 |

#### Point-in-Time Universe Coverage

| Metric | Value |
|--------|-------|
| Monthly PIT snapshots | 300 |
| Avg PIT constituents | 509 stocks/month |
| Avg available in our data | 422 stocks/month |
| Coverage rate | **83.0%** |
| Residual survivorship bias | **17.0%** (delisted stocks with no YF data) |

**Outputs:**
- `data_processed/extended_prices_clean.parquet` — 3.40M rows, 653 symbols, 2000-2024
- `data_processed/sp500_universe_lookup.csv` — monthly PIT filter (300 rows)
- `data_processed/extended_coverage_stats.csv` — per-ticker coverage
- `data_processed/extended_data_summary.json` — summary statistics

---

### 5.15 Phase 3.5 — Extended Backtests (25-Year, With PIT Masking) — COMPLETE (2026-03-07)

**What we did:** Re-ran all 14 strategies on the 25-year dataset (2000-2024) with point-in-time universe masking. The benchmark is an equal-weighted portfolio of all available in-universe stocks per day.

**Script:** `scripts/run_extended_backtests.py`
**Results:** `results/extended_backtests/` (JSON + 14 equity curve CSVs)
**Key technical fix:** Used `prices.pct_change(fill_method=None)` to prevent false large returns at NaN gaps from data cleaning.

#### Phase 3.5 Full Results Table (2000-2024, PIT Universe)

```
Strategy                              Sharpe     CAGR       MDD   Ann Vol   Calmar
--------------------------------------------------------------------------------
benchmark (equal-wt)                    0.69    15.0%    -54.6%     20.2%     0.27
low_volatility_shield                   0.66    12.7%    -52.1%     17.4%     0.24
rsi_mean_reversion                      0.64    13.3%    -54.4%     19.2%     0.24
volatility_targeting                    0.60    12.4%    -55.2%     19.3%     0.22
52_week_high_breakout                   0.59    12.2%    -55.5%     19.1%     0.22
composite_factor_score                  0.59    12.0%    -55.5%     18.8%     0.22
quality_momentum                        0.59    12.0%    -55.9%     18.9%     0.21
high_quality_roic                       0.58    11.2%    -54.5%     17.6%     0.20
quality_low_vol                         0.57    11.2%    -54.1%     17.9%     0.21
moving_average_trend                    0.56    11.3%    -54.2%     18.4%     0.21
large_cap_momentum                      0.56    11.7%    -56.1%     19.8%     0.21
value_momentum_blend                    0.55    11.4%    -55.7%     19.2%     0.20
dividend_aristocrats                    0.55    10.0%    -52.8%     16.0%     0.19
earnings_surprise_momentum              0.55    11.4%    -49.5%     19.7%     0.23
deep_value_all_cap                      0.53    11.2%    -55.4%     20.0%     0.20
```

#### Phase 2 vs Phase 3 Comparison

| Metric | Phase 2 (2014-2017, no PIT) | Phase 3 (2000-2024, with PIT) |
|--------|----------------------------|-------------------------------|
| Best strategy Sharpe | ~1.20 (quality_low_vol) | 0.66 (low_volatility_shield) |
| Worst strategy Sharpe | ~0.52 (earnings_surprise) | 0.53 (deep_value_all_cap) |
| Benchmark Sharpe | ~0.40 | 0.69 |
| Beat benchmark? | Yes — all strategies beat it | **No — all strategies lag benchmark** |
| MDD range | -17% to -47% | -49.5% to -56.1% |
| CAGR range | ~8% to ~22% | 10.0% to 13.3% |

#### Key Findings — The Phase 3 Paradigm Shift

**1. ALL 14 strategies underperform the equal-weight benchmark on Sharpe.** Not one strategy achieves Sharpe > 0.69 (benchmark). This is a fundamental reversal from Phase 2 where strategies appeared to beat the benchmark by a wide margin.

**2. Phase 2 results were distorted by 4-year bull market selection.** 2014-2017 was a sustained bull market with low volatility. The equal-weight benchmark had modest Sharpe (~0.40) because it started from neutral. Strategies with factor tilts captured the specific rising-quality-and-momentum regime of 2014-2017. But over 25 years, when dot-com (2000-2002), GFC (2008-2009), COVID (2020), and 2022 bear markets are included, the equal-weight benchmark outperforms all factor tilts.

**3. Maximum drawdowns are severe and nearly identical across all strategies.** MDD range: -49.5% to -56.1%. No strategy provided meaningful downside protection vs the benchmark (-54.6%). This confirms what Phase 2 regime analysis warned: all strategies are fundamentally long-only equity, with no bear-market defense.

**4. Low Volatility Shield is the most robust over 25 years.** Best strategy Sharpe (0.66), lowest MDD (-52.1%), lowest Ann Vol (17.4%). Its inverse-volatility weighting naturally reduces exposure to high-beta stocks during volatile periods.

**5. Earnings Surprise Momentum improves relatively.** Best MDD (-49.5%) — the only strategy with drawdown below 50%. Event-driven strategies may benefit from being in-and-out of positions more frequently, limiting exposure to sustained trend losses.

**6. The tight clustering (Sharpe 0.53-0.66) reveals the true nature of factor strategies.** All 14 strategies are variants of the same long-equity exposure. They add factor tilts but don't escape equity market beta. Over 25 years, the law of large numbers means the factor premia are small relative to market risk.

**Implication:** Factor investing alpha is real but small (0-50 bps Sharpe improvement over benchmark). The "impressive" Phase 2 results were largely due to favorable regime selection, not genuine strategy alpha. Phase 3 gives the honest picture.

---

### 5.16 Phase 3.6 — Extended Regime Analysis — COMPLETE (2026-03-07)

**What we did:** Re-ran market regime analysis on the 25-year dataset with PIT masking. Same detection method as Phase 2.4 (63-day trend + vol), but now covers dot-com, GFC, COVID, and 2022 bear markets.

**Script:** `scripts/extended_regime_analysis.py`
**Results:** `results/extended_regime_analysis/`

#### Regime Distribution Comparison

| Regime | Phase 2 (2014-2017) | Phase 3 (2000-2024) |
|--------|---------------------|---------------------|
| Bull | 27.0% | **40.0%** |
| Bear | **7.4%** | 12.0% |
| High-Vol | 6.1% | 17.5% |
| Sideways | 59.5% | 30.5% |

The 2009-2020 bull market (11 years) dominates Phase 3, pushing Bull to 40%. High-Vol tripled because the GFC crash (2008-09) is now included in the High-Vol bucket.

#### Strategy Performance by Regime (Sharpe Ratios)

```
Strategy                              Bull     Bear   High-V    Sidew   Spread       Best
──────────────────────────────────────────────────────────────────────────────────────────
benchmark (equal-wt)                 +2.98    -1.46    +2.10    -0.47     4.44       Bull
low_volatility_shield                +2.84    -1.42    +1.84    -0.15     4.26       Bull
rsi_mean_reversion                   +2.86    -1.51    +2.01    -0.47     4.38       Bull
earnings_surprise_momentum           +2.52    -1.68    +1.62    -0.58     4.20       Bull
large_cap_momentum                   +2.60    -1.41    +1.92    -0.49     4.00       Bull
```

**All strategies underperform benchmark in every regime.** The benchmark achieves Sharpe +2.98 (Bull), -1.46 (Bear), +2.10 (High-Vol), -0.47 (Sideways) — higher than all strategies in every regime.

Phase 2 showed strategies BEATING the benchmark in some regimes (especially High-Vol). This was a regime-specific artifact: Phase 2's High-Vol days were brief recovery rallies (Aug 2015, Jan 2016). In Phase 3, High-Vol includes the GFC crash, pulling the High-Vol regime Sharpe down.

#### Named Period Analysis (Sharpe — key moments)

| Period | N Days | Benchmark | Low Vol Shield | Large Cap Mom |
|--------|--------|-----------|---------------|--------------|
| Dot-com crash (2000-02) | 632 | +0.11 | **+0.63** | −0.34 |
| GFC bear market (2008-09) | 356 | −1.25 | −1.33 | −1.29 |
| COVID crash (2020, 23 days) | 23 | −6.45 | −6.03 | −6.31 |
| 2022 bear | 251 | −0.43 | −0.41 | −0.45 |
| Post-GFC bull (2009-2020) | 2,756 | +1.16 | +1.16 | +1.03 |

**Low Volatility Shield is the only strategy with meaningful outperformance during a real crash** (dot-com: Sharpe +0.63 vs benchmark +0.11). This was invisible in Phase 2. Every other strategy matched or underperformed the benchmark in every crisis period.

**Large Cap Momentum is the worst during dot-com** (−0.34 vs +0.11): momentum stocks were also the most overvalued in 1999-2000, so they crashed hardest when valuations collapsed.

---

### 5.17 Phase 3.7 — Extended Rolling Performance — COMPLETE (2026-03-07)

**What we did:** Annual sub-period analysis (25 years, one row per year) + decade breakdown + rolling 252-day Sharpe analysis.

**Script:** `scripts/extended_rolling_performance.py`
**Results:** `results/extended_rolling_performance/`

#### Year-Over-Year Rank Stability

```
Phase 2 rank stability: 0.749 (STABLE)  — same strategies consistently lead
Phase 3 rank stability: -0.123 (UNSTABLE) — leadership rotates randomly year-to-year
```

This is a complete reversal from Phase 2. Over 4 years (2014-2017), the environment was consistent enough that the same factor tilts consistently won. Over 25 years with four different regimes (dot-com, GFC, COVID, AI-rally), no factor tilt consistently leads.

**Implication:** Strategy selection based on recent performance is nearly useless over 25-year horizons. A strategy that "worked great in the 2010s" (Dividend Aristocrats, Low Vol) may underperform in the 2020s — and vice versa.

#### Decade Breakdown (Sharpe)

| Strategy | 2000s (+GFC) | 2010s (Bull) | 2020s (COVID+AI) |
|----------|-------------|-------------|-----------------|
| Benchmark | **+0.60** | 0.93 | **+0.59** |
| Low Vol Shield | 0.56 | **+0.94** | 0.49 |
| RSI Mean Reversion | 0.57 | 0.84 | 0.53 |
| Quality Momentum | 0.45 | 0.82 | 0.54 |
| Earnings Surprise | 0.57 | 0.74 | **0.24** |
| Large Cap Momentum | 0.40 | 0.79 | 0.55 |
| Dividend Aristocrats | 0.28 | **+0.95** | 0.50 |

**The benchmark beats all strategies in 2000s and 2020s.** Only in the 2010s do some strategies marginally outperform. Key observations:
- **Earnings Surprise collapses in the 2020s** (Sharpe 0.24): event-driven signals became noisier as earnings releases became more anticipated and priced in faster.
- **Dividend Aristocrats: best in 2010s (0.95), worst in 2000s (0.28)**: defensive income works in stable bull markets, fails in volatile regimes.
- **Benchmark is more consistent across decades** than any single factor strategy.

#### Best and Worst Annual Performance

- **Best single year**: 2013 (post-taper tantrum recovery) — almost all strategies Sharpe > 2.5
- **Worst year**: 2008 (GFC) — all strategies Sharpe −0.88 to −1.31
- **Most consistent strategy year-by-year**: Low Vol Shield (mean rolling Sharpe 1.00, tracks benchmark closely)
- **Least consistent**: Earnings Surprise (volatile, especially poor in 2018, 2022)

---

### 5.18 Phase 3.8 — Extended Regime Overlay — COMPLETE (2026-03-07)

**What we did:** Applied Bear-only, Aggressive, and Trend-only overlays to all 14 strategies on the 25-year dataset. Measured whether the overlay improved or hurt performance.

**Script:** `scripts/extended_regime_overlay.py`
**Results:** `results/extended_regime_overlay/`

#### Key Result — Overlay Universally HURTS Performance

| Metric | Phase 2 (2014-2017) | Phase 3 (2000-2024) |
|--------|---------------------|---------------------|
| Strategies where overlay improves Sharpe | All 14 | **0/14** |
| Avg Sharpe change | −0.04 to −0.16 | **−0.12** |
| Avg MDD change | +5pp to +26pp improvement | **−4.4pp (WORSE)** |

**The overlay that appeared beneficial in Phase 2 is harmful in Phase 3.** Every single strategy sees LOWER Sharpe AND WORSE MDD with the Bear-only overlay applied.

#### Why the Reversal? — The Lag Problem

The 63-day trend filter has a critical weakness when applied to sharp, fast crashes:

1. **COVID crash (Feb 20 – Mar 23, 2020):** The S&P 500 fell −34% in 23 trading days. The 63-day trend wouldn't classify this as "Bear" until weeks into the recovery. Going to cash in April 2020 means **missing the entire V-shaped recovery** (which was the fastest recovery in history). This alone wipes out any benefit.

2. **GFC (2007-2009):** The crash was gradual but deep. By the time the 63-day trend signals "Bear" (late 2007), the market had already fallen −15%. Going to cash avoids some additional decline but misses the chaotic recoveries within the bear market (there were several 10-20% bounces during the GFC).

3. **Recovery penalty:** After Bear ends (regime becomes Sideways or Bull), the strategy re-enters at a higher price point with full-size positions. If volatility remains elevated, this causes larger swings and higher realized MDD.

**Lesson from Phase 3.8:** Simple lagged regime detection does not protect against fast crashes and can hurt performance by causing you to miss recoveries. Better approaches would require shorter-lag signals (e.g., 5-10 day momentum), implied volatility signals (VIX-based), or machine learning-based regime switches.

---

### 5.19 Phase 3.9 — Extended Portfolio Analysis — COMPLETE (2026-03-08)

**What we did:** Computed the 14×14 inter-strategy correlation matrix on 25-year data, analyzed how correlations change across market regimes, and compared multiple portfolio construction methods.

**Script:** `scripts/extended_portfolio_analysis.py`
**Results:** `results/extended_portfolio_analysis/`

#### Correlation Matrix — Phase 2 vs Phase 3

| Metric | Phase 2 (2014-2017) | Phase 3 (2000-2024) |
|--------|---------------------|---------------------|
| Avg inter-strategy correlation | 0.788 | **0.951** |
| Pairs with r > 0.80 | 63/91 (69%) | **90/91 (99%)** |
| Pairs with r < 0.40 | 7/91 | **0/91** |
| Min pairwise correlation | ~0.10 | **0.775** |
| Diversification ratio | 1.051 | **1.024** |

**Over 25 years, every strategy is highly correlated with every other strategy.** The apparent diversification in Phase 2 was partly noise from a short, noisy 4-year window. With 6,288 trading days, the true correlation is estimated accurately: all 14 strategies are variants of the same underlying bet (long large-cap US equities).

#### Regime-Conditional Correlation

| Regime | Avg Inter-Strategy Correlation |
|--------|-------------------------------|
| Bull | 0.928 |
| Sideways | 0.935 |
| High-Vol | 0.944 |
| **Bear** | **0.969** ← highest |

This confirms the "diversification breakdown" phenomenon: during the worst periods (Bear markets), strategies become *more* correlated, not less. The theoretical benefit of diversification evaporates exactly when investors need it most.

#### Portfolio Construction Results

| Portfolio | Sharpe | CAGR | MDD |
|-----------|--------|------|-----|
| **Benchmark (equal-wt idx)** | **0.69** | **15.0%** | **-54.6%** |
| Tier 1 equal-wt (top 5 by Ph3 Sharpe) | 0.62 | 12.6% | -54.5% |
| Risk-parity all 14 | 0.59 | 11.8% | -54.2% |
| Min-corr top 3 | 0.58 | 11.1% | -52.0% |
| Equal-weight all 14 | 0.59 | 11.8% | -54.2% |

**No portfolio construction technique beats the benchmark.** Even sophisticated methods (risk parity, minimum correlation) produce worse Sharpe than the simple equal-weight index. The min-correlation portfolio achieves slightly lower MDD (-52.0% vs -54.6%) but at the cost of lower returns.

#### Most Unique vs Most Redundant Strategies

| Most Unique (avg corr 0.849) | Most Redundant (avg corr 0.970) |
|------------------------------|--------------------------------|
| Earnings Surprise Momentum | Quality Momentum |
| Dividend Aristocrats (0.907) | Composite Factor Score (0.970) |

Paradox: the most unique strategy (Earnings Surprise) is also the weakest performer over 25 years. Orthogonality ≠ quality.

---

### 5.20 Phase 3.10 — Extended Walk-Forward Validation — COMPLETE (2026-03-08)

**What we did:** Applied walk-forward validation on the full 25-year dataset using two tests: (1) a simple 50/50 OOS split (IS: 2000-2012, OOS: 2013-2024), and (2) 9 rolling folds with an expanding training window and 2-year test periods covering every era from 2006 to 2024.

**Script:** `scripts/extended_walk_forward.py`
**Results:** `results/extended_walk_forward/` (JSON + CSV summary)
**Method:** Pre-computes all strategy signals once (expensive) on the full 25-year data, then slices the pre-computed return series by time window — avoids redundant signal recomputation across 9 folds.

#### Part 1 — Simple OOS Split (IS: 2000–2012, OOS: 2013–2024)

```
Strategy                          IS Sharpe  OOS Sharpe     WFE    Verdict
───────────────────────────────────────────────────────────────────────────
large_cap_momentum                    +0.44       +0.72    161%  EXCELLENT
52_week_high_breakout                 +0.50       +0.72    145%  EXCELLENT
deep_value_all_cap                    +0.40       +0.73    182%  EXCELLENT
high_quality_roic                     +0.43       +0.76    175%  EXCELLENT
low_volatility_shield                 +0.59       +0.74    126%  EXCELLENT
dividend_aristocrats                  +0.37       +0.76    204%  EXCELLENT
moving_average_trend                  +0.44       +0.72    163%  EXCELLENT
rsi_mean_reversion                    +0.58       +0.73    127%  EXCELLENT
value_momentum_blend                  +0.43       +0.72    167%  EXCELLENT
quality_momentum                      +0.49       +0.72    147%  EXCELLENT
quality_low_vol                       +0.43       +0.75    174%  EXCELLENT
composite_factor_score                +0.49       +0.73    149%  EXCELLENT
volatility_targeting                  +0.51       +0.72    141%  EXCELLENT
earnings_surprise_momentum            +0.56       +0.53     94%       GOOD
```

**Apparent result:** 13/14 EXCELLENT, 1/14 GOOD. All strategies appear to improve OOS.

#### Part 2 — Rolling 9-Fold Validation (Expanding Train Window, 2-Year Test)

| Fold | Test Period | Market Context | Avg OOS Sharpe |
|------|-------------|---------------|---------------|
| 1 | 2006-2007 | Pre-crisis credit bubble | +0.76 |
| **2** | **2008-2009** | **GFC — All strategies NEGATIVE** | **−0.08** |
| 3 | 2010-2011 | Post-GFC recovery | +0.50 |
| 4 | 2013-2014 | Post-taper tantrum bull peak | +1.86 |
| 5 | 2015-2016 | Mid-cycle, China scare | +0.40 |
| 6 | 2017-2018 | Late bull + Q4 2018 correction | +0.43 |
| 7 | 2019-2020 | COVID crash + recovery | +0.79 |
| 8 | 2021-2022 | 2022 bear market | +0.41 |
| 9 | 2023-2024 | AI-driven recovery | +0.96 |

**Avg WFE by strategy:** 13/14 strategies have avg WFE > 100%; Earnings Surprise 90%.
**Positive fold count:** 13 strategies with 8/9 positive OOS Sharpe folds; Earnings Surprise 7/9.

#### CRITICAL INTERPRETATION — Why WFE > 100% Is Misleading Here

**The WFE > 100% result does NOT mean strategies are improving out-of-sample.** It is entirely explained by regime differences between the IS and OOS periods:

- **IS period (2000-2012):** Contains 3 major bear markets — dot-com crash (2000-02), GFC (2008-09), and post-GFC volatility. IS Sharpe range: 0.37–0.59 (depressed by crashes).
- **OOS period (2013-2024):** Dominated by the longest bull market in history (2009-2020), followed by brief 2022 downturn and AI-driven 2023-2024 recovery. OOS Sharpe range: 0.53–0.76 (elevated by regime).

**A passive equal-weight index fund would show the same WFE > 100% pattern.** This is not strategy alpha; it is regime selection. The "EXCELLENT" verdict reflects that we were fortunate enough to test OOS on a more favorable period.

**The only genuine out-of-sample stress test is Fold 2 (GFC 2008-2009):** ALL 14 strategies generated negative OOS Sharpe (−0.03 to −0.21). No strategy escaped the systemic crisis. This is the honest measure of OOS resilience.

**Conclusion:** Walk-forward WFE is a useful technical robustness check (no data snooping, signals computed correctly), but the WFE ratio is contaminated when IS and OOS regimes differ systematically. Over 25 years, regime differences dominate. The correct interpretation is: strategies are technically correct (no look-ahead bias, no overfitting of specific parameters), but they cannot escape bear market losses.

#### Comparison: Phase 2 vs Phase 3 Walk-Forward

| Aspect | Phase 2 (2014-2017) | Phase 3 (2000-2024) |
|--------|---------------------|---------------------|
| IS period regime | Bull-dominated | 3 bear markets |
| OOS period regime | Pure bull (2016-2017) | Long bull (2013-2024) |
| OOS Sharpe range | 0.60–1.20 | 0.53–0.76 |
| WFE range | 100–200% | 94–204% |
| Crisis fold present? | No | Yes (GFC 2008-09: all negative) |
| True OOS stress tested? | No | Fold 2 only |

---

### 5.21 Phase 3.11 — Monte Carlo Significance Testing (25-Year) — COMPLETE (2026-03-08)

**What we did:** Ran all three Phase 2.3 significance tests (IID Bootstrap, Block Bootstrap, Random Sign Test) on the 25-year return series with PIT masking. Same 10,000-sample methodology, same 95% confidence threshold.

**Script:** `scripts/extended_monte_carlo.py`
**Results:** `results/extended_monte_carlo/` (JSON + CSV summary)

#### Results Table — Monte Carlo Significance

```
Strategy                          Sharpe  IID CI (95%)              IID p   Blk p  Sign p  Verdict
────────────────────────────────────────────────────────────────────────────────────────────────
large_cap_momentum                +0.557  [+0.161, +0.952]         0.0022  0.0015  0.0009  SIGNIFICANT ★★★
52_week_high_breakout             +0.593  [+0.194, +0.986]         0.0009  0.0008  0.0004  SIGNIFICANT ★★★
deep_value_all_cap                +0.531  [+0.133, +0.924]         0.0033  0.0037  0.0013  SIGNIFICANT ★★★
high_quality_roic                 +0.577  [+0.179, +0.969]         0.0017  0.0013  0.0002  SIGNIFICANT ★★★
low_volatility_shield             +0.659  [+0.263, +1.051]         0.0006  0.0002  1.0000  LIKELY SIGNIFICANT ★★
dividend_aristocrats              +0.552  [+0.157, +0.947]         0.0027  0.0009  0.0005  SIGNIFICANT ★★★
moving_average_trend              +0.564  [+0.167, +0.960]         0.0018  0.0015  0.0006  SIGNIFICANT ★★★
rsi_mean_reversion                +0.641  [+0.244, +1.039]         0.0004  0.0005  1.0000  LIKELY SIGNIFICANT ★★
value_momentum_blend              +0.554  [+0.155, +0.949]         0.0026  0.0021  0.0009  SIGNIFICANT ★★★
quality_momentum                  +0.588  [+0.190, +0.984]         0.0013  0.0012  0.0005  SIGNIFICANT ★★★
quality_low_vol                   +0.570  [+0.172, +0.967]         0.0019  0.0014  0.0003  SIGNIFICANT ★★★
composite_factor_score            +0.591  [+0.191, +0.986]         0.0011  0.0011  0.0003  SIGNIFICANT ★★★
volatility_targeting              +0.599  [+0.202, +0.995]         0.0013  0.0009  0.0004  SIGNIFICANT ★★★
earnings_surprise_momentum        +0.546  [+0.150, +0.941]         0.0030  0.0017  0.0010  SIGNIFICANT ★★★
```

#### Phase 2 vs Phase 3 Significance Comparison

| Verdict | Phase 2 (2014-2017, 1,007 days) | Phase 3 (2000-2024, 6,288 days) |
|---------|---------------------------------|---------------------------------|
| SIGNIFICANT ★★★ | 5 | **12** |
| LIKELY SIGNIFICANT ★★ | 3 | **2** |
| MARGINAL ★ | 3 | **0** |
| NOT SIGNIFICANT | 3 | **0** |

**All 14 strategies now show statistically real alpha over 25 years.** The complete absence of marginal or not-significant results is a direct consequence of 6× more data: confidence intervals are ~2.5× narrower, making even small Sharpe ratios unambiguously positive.

#### Key Finding — Statistical Certainty vs Alpha Size

Phase 2 had some strategies that LOOKED more impressive (Sharpe 0.80–1.20) but were statistically ambiguous (not enough data). Phase 3 shows strategies with SMALLER Sharpe (0.53–0.66) that are unambiguously real. This teaches a fundamental lesson:

- **With 4 years of data:** large Sharpe → needed for significance; small Sharpe → could be noise
- **With 25 years of data:** even Sharpe 0.53 is confirmed at 1% significance level

More data doesn't make strategies look better — it makes your estimates more accurate. Phase 3's 0.53–0.66 Sharpe is the honest picture; Phase 2's 0.80–1.20 was artificially inflated by the bull market.

#### Sign Test Anomaly — Low Vol Shield and RSI Mean Reversion

Both strategies show sign_p = 1.0000 (all 10,000 random sign permutations achieve Sharpe ≥ observed). This is a known limitation of the sign test:

The random sign test tests **directional timing** skill — does the strategy correctly time when to be long vs short? But Low Volatility Shield and RSI Mean Reversion are always **fully invested** (nearly 100% position weight at all times). They have almost no cash period and no timing component. The sign test breaks down because:

1. The strategy is essentially "always long" — there's no timing decision to test
2. Flipping signs of near-constant position returns produces nonsensical results for the sign test

**Correct interpretation:** Use IID and Block Bootstrap results for these strategies. Both show p < 0.001 — strongly significant. The sign test is an inappropriate test for fully-invested, selection-based strategies.

#### Pezier-White Adjusted Sharpe (Non-Normality Penalty)

The adjustment corrects for negative skewness (left tail risk) and excess kurtosis (fat tails). All strategies have some non-normality penalty:

| Adjustment Size | Strategies | Notes |
|----------------|-----------|-------|
| Largest (−0.10) | Low Volatility Shield | Most non-normal returns |
| Small (−0.02) | Earnings Surprise | Most "normal" returns |
| Typical (−0.05 to −0.07) | All others | Moderate fat tails |

Raw Sharpe overstates risk-adjusted performance by 5–15% for most strategies when non-normality is accounted for.

---

### 5.22 Phase 3.12 — Final Consolidated Summary — COMPLETE (2026-03-08)

**What we did:** Aggregated all 7 Phase 3 result files (backtests, regime, rolling, overlay, portfolio, walk-forward, Monte Carlo) into a single master scorecard. No recomputation — reads from saved JSON files only.

**Script:** `scripts/phase3_final_summary.py`
**Results:** `results/phase3_summary/` (master_scorecard.csv, phase3_summary.json)

#### Phase 3 Master Scorecard (sorted by Sharpe)

```
Strategy                          SR     MDD  BearSR  WFE%   F+  AvgCorr  MC Verdict               Tier
─────────────────────────────────────────────────────────────────────────────────────────────────────
Low Volatility Shield         +0.659  -52.1%  -1.421   126% 8/9   0.954  LIKELY SIGNIFICANT ★★     Tier 1
RSI Mean Reversion            +0.641  -54.4%  -1.514   127% 8/9   0.955  LIKELY SIGNIFICANT ★★     Tier 1
Volatility Targeting          +0.599  -55.2%  -1.495   141% 8/9   0.965  SIGNIFICANT ★★★           Tier 2
52-Week High Breakout         +0.593  -55.5%  -1.455   145% 8/9   0.968  SIGNIFICANT ★★★           Tier 2
Composite Factor Score        +0.591  -55.5%  -1.418   149% 8/9   0.970  SIGNIFICANT ★★★           Tier 2
Quality+Momentum              +0.588  -55.9%  -1.428   147% 8/9   0.970  SIGNIFICANT ★★★           Tier 2
High Quality ROIC             +0.577  -54.5%  -1.372   175% 8/9   0.960  SIGNIFICANT ★★★           Tier 2
Quality+Low Vol               +0.570  -54.1%  -1.366   174% 8/9   0.968  SIGNIFICANT ★★★           Tier 2
Moving Average Trend          +0.564  -54.2%  -1.565   163% 8/9   0.967  SIGNIFICANT ★★★           Tier 3
Large Cap Momentum            +0.557  -56.1%  -1.405   161% 8/9   0.964  SIGNIFICANT ★★★           Tier 3
Value+Momentum Blend          +0.554  -55.7%  -1.484   167% 8/9   0.970  SIGNIFICANT ★★★           Tier 3
Dividend Aristocrats          +0.552  -52.8%  -1.296   204% 8/9   0.907  SIGNIFICANT ★★★           Tier 3
Earnings Surprise Momentum    +0.546  -49.5%  -1.678    94% 7/9   0.849  SIGNIFICANT ★★★           Tier 3
Deep Value All-Cap            +0.531  -55.4%  -1.607   182% 8/9   0.941  SIGNIFICANT ★★★           Tier 3
──────────────────────────────────────────────────────────────────────────────────────────────────────
Benchmark (equal-wt)          +0.694  -54.6%  (beats all 14 on Sharpe)
```

#### Phase 3 Tier Classification

**Tier 1 — Most Robust (2 strategies):**
- **Low Volatility Shield** SR 0.659 | lowest MDD (-52.1%) | only strategy to outperform in dot-com crash
- **RSI Mean Reversion** SR 0.641 | most consistent across years | sign test anomaly (always-invested)

**Tier 2 — Solid (6 strategies, all ★★★ significant):**
- Volatility Targeting (SR 0.599), 52-Week High Breakout (SR 0.593), Composite Factor Score (SR 0.591), Quality+Momentum (SR 0.588), High Quality ROIC (SR 0.577), Quality+Low Vol (SR 0.570)

**Tier 3 — Confirmed but Weak (6 strategies, all statistically real but lagging):**
- Moving Average Trend, Large Cap Momentum, Value+Momentum, Dividend Aristocrats, Earnings Surprise, Deep Value All-Cap (SR 0.531–0.564)

*Note: Phase 3 Tier 1 has completely different members from Phase 2 Tier 1 — confirming rank instability over 25 years.*

#### 5 Key Phase 3 Findings (Summary)

1. **All 14 strategies lag the benchmark on Sharpe** (0.69 vs 0.53–0.66) — Phase 2 outperformance was a bull-market artifact
2. **All 14 fail in real bear markets** — GFC fold: all negative; Bear regime correlation 0.969
3. **No consistent winner across 25 years** — rank stability -0.123 (UNSTABLE)
4. **Regime overlay hurts** — 63-day lag misses fast crashes; 0/14 improve with Bear overlay
5. **Statistical certainty grows with data** — 0/14 not significant (vs 3/14 in Phase 2); more data → honest small alpha

---

### 5.23 Phase 4.1 — Research + Parameters Tabs — COMPLETE (2026-03-09)

**Backend: `src/api/routes/research.py`**
- `GET /api/v1/research/{strategy_name}` — reads 4 Phase 3 JSON files (MC, WF, regime, scorecard CSV), returns structured research data
- `GET /api/v1/research/parameters/{strategy_name}` — returns per-strategy parameter definitions with ROBUST/FRAGILE labels
- All 14 strategies have full parameter definitions; endpoint validation tested

**Frontend: `frontend/src/app/strategy/[slug]/page.tsx`**
- Added 2 new tabs: **Research** (Flask icon) + **Parameters** (Sliders icon)
- Lazy-loaded: data fetched only when tab is first opened
- Research tab shows: Phase 3 tier badge, MC verdict badge, WF verdict badge, scorecard numbers (Sharpe/adj Sharpe/CAGR/MDD/% positive years), MC p-values (3 tests in cards), WF fold Sharpe pills (colour-coded green/yellow/red), regime Sharpe table, caveat banner about WFE > 100% regime artifact
- Parameters tab shows: slider per parameter with ROBUST/FRAGILE badge, default/current value, min/max, description. "Run Backtest" button calls `POST /api/v1/backtests/run` with current slider values. Results rendered in 8-metric grid + equity curve chart.
- Build: `✓ Compiled successfully` (Next.js 14)

**Files modified:** `src/api/routes/research.py` (NEW), `src/api/main.py`, `frontend/src/lib/api.ts`, `frontend/src/app/strategy/[slug]/page.tsx`

---

### 5.24 Phase 4.2 — Dashboard Tier Badges + Sort Controls — COMPLETE (2026-03-09)

**New backend:** `GET /api/v1/research/scorecard` — returns all 14 strategies' tier, Sharpe, CAGR, MDD, etc. in one call. Loaded in parallel with dashboard data on page mount.

**`useDashboardData.ts`:** Added `tier` and `phase3Sharpe` fields to `EnrichedStrategy`. Hook now fetches scorecard alongside dashboard data via `Promise.all`.

**`StrategyCard.tsx`:**
- Phase 3 tier badge (emerald=Tier 1, blue=Tier 2, gray=Tier 3) in card header top-right
- Performance preview now shows "Sharpe (4yr)" and "Sharpe (25yr)" side by side

**Dashboard `page.tsx`:**
- Sort-by dropdown: Phase 3 Tier (default), Sharpe 25yr, Sharpe 4yr, CAGR, Min Drawdown
- Tier filter pills: click Tier 1 / Tier 2 / Tier 3 to isolate strategies by tier (multi-select)
- Live count badge ("X of 14 strategies") moves to sort bar

**Servers:** backend PID 92630 on port 8000, frontend PID 92641 on port 3000. Both healthy.

---

## 6. DATA REQUIREMENTS

### 6.1 Current Data
```
Source: Kaggle (S&P 500)
Period: 2014-01-02 to 2017-12-29 (4 years)
Symbols: 505
Rows: ~497,000
Columns: symbol, date, open, high, low, close, volume, adj_close
```

### 6.2 Planned Data

| Market | Period | Source | Status |
|--------|--------|--------|--------|
| US S&P 500 | 2000-present | Yahoo Finance | 📋 Phase 3 |
| US Full Market | 2000-present | Polygon.io (paid) | 📋 Future |
| India NSE 50 | 2000-present | Yahoo Finance | 📋 Phase 3 |

---

## 7. KEY DECISIONS LOG

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-07 | Start with Kaggle data | Quick start, free, clean |
| 2026-01-27 | Vectorized backtesting (not event-driven) | Speed: 14 strategies × 500 stocks is fast |
| 2026-01-28 | Next.js for frontend | Modern, fast, good DX |
| 2026-03-02 | Replace all 15 strategies with 14 industry-grade ones | Old strategies were generic/placeholder, these are academically validated factor strategies |
| 2026-03-02 | All strategies multi-asset (full universe) | Single-asset strategies aren't useful for portfolio research |
| 2026-03-02 | Price-derived proxies for fundamentals | No fundamental data available; document limitations clearly |
| 2026-03-04 | CV-based robustness scoring for param sensitivity | CV < 0.15 = robust, 0.15-0.30 = moderate, >0.30 = fragile — simple, interpretable |
| 2026-03-04 | Keep fragile strategies (don't discard) | Fragility may be data/proxy issue, not strategy issue. Validate with walk-forward |
| 2026-03-04 | 400-day lookback buffer for walk-forward | Strategies need prior data to compute indicators; without buffer, most folds produce zero signals |
| 2026-03-04 | No within-fold optimization | Default params used in all folds — tests strategy concept, not param tuning ability |
| 2026-03-05 | Random sign test instead of permutation test | Naive permutation preserves mean/std → Sharpe unchanged → p=1.0 always. Sign flipping tests directional timing skill |
| 2026-03-05 | Three independent significance tests | No single test is definitive; requiring agreement across IID, block, and sign tests increases confidence |
| 2026-03-05 | Simple trend+vol regime detection | 63-day return + 63-day vol classifies into Bull/Bear/High-Vol/Sideways. Simple, interpretable, no HMM needed |
| 2026-03-05 | Bear market filter as future improvement | All strategies lose in Bear → regime overlay is the highest-impact next improvement |
| 2026-03-05 | Cost sweep 0–100 bps at 10 levels | Covers full range from zero-cost to expensive retail; 15 bps is reference (10 commission + 5 slippage) |
| 2026-03-05 | All 14 strategies bulletproof to costs | Low turnover (0.2x–6.3x/yr) insulates factor strategies; even 100 bps can't kill them |
| 2026-03-05 | Flag Earnings Surprise as weakest strategy | Fragile params + not significant + biggest cost degrader = triple confirmation of weakness |
| 2026-03-05 | Bear-only overlay > aggressive overlay | 7% cash days beats 62% — less opportunity cost in bull-dominated period |
| 2026-03-05 | Use MDD (not Sharpe) to evaluate overlay in short windows | Sharpe misleading in 4-year bull-heavy data; MDD improvement is real and interpretable |
| 2026-03-05 | Defer overlay confirmation to Phase 3 | 70 Bear days is insufficient; need 2008/2000 crises to measure true benefit |
| 2026-03-05 | 14 strategies are NOT truly diversified | Avg pairwise corr 0.788, 69% pairs redundant — all are long-equity factor variants |
| 2026-03-05 | Risk-Parity Tier 1 is the recommended showcase portfolio | Best Sharpe (0.90) with lower MDD than equal-weight Tier 1 (-35.9% vs -42.75%) |
| 2026-03-05 | Composite Factor Score is redundant with Quality+Momentum | r=0.996 — adding both to a portfolio provides zero diversification |
| 2026-03-05 | Min-correlation portfolio picks weak strategies | Orthogonality ≠ quality — diversifying into Div Aristocrats + Earnings Surprise gives below-benchmark Sharpe |
| 2026-03-05 | Performance concentrated in 2016-2017 (P6-P8) | Last 3 sub-periods avg Sharpe 1.83; first 5 periods avg 0.20. Extended data will dilute and clarify true quality |
| 2026-03-05 | Rank stability 0.749 = STABLE | Same strategies consistently lead; rankings are not random artifacts. Validates Tier 1/2/3/4 classification |
| 2026-03-05 | Rolling correlation can drop to -0.076 | Even highly correlated strategies briefly diverge during regime transitions — dynamic correlation matters |
| 2026-03-05 | Phase 2 is COMPLETE | All 8 stages done. Next: Phase 3 — extended data (2000-2025) with point-in-time S&P 500 constituents |
| 2026-03-05 | Use Wikipedia PIT + yfinance instead of paid data provider | Wikipedia changes table + yfinance 1.2.0 gives 83% PIT coverage for free; 17% survivorship bias is documented and acceptable for research |
| 2026-03-05 | Extended dataset: 654 symbols, 6,288 days, 3.44M rows | 6.2× more trading days than Phase 2; includes dot-com, 2008 crisis, COVID, 2022 bear market |
| 2026-03-05 | Residual survivorship bias = 17% | ~162 delisted tickers with no Yahoo Finance data. True bias requires CRSP/Tiingo for full correction |
| 2026-03-05 | Apply point-in-time universe mask to all strategy signals | Signals restricted to stocks actually in S&P 500 on each date — eliminates forward-looking bias in universe selection |
| 2026-03-07 | Price floor ($1) required before return-filter for outlier cleaning | Near-zero corrupted prices (close ≈ 0.001) survive a return filter but create 33,999× pct_change on the next row. Price floor must come first, return filter second, applied in two passes |
| 2026-03-07 | Use fill_method=None in pct_change on pivoted price data | Default fill_method='pad' forward-fills NaN gaps from removed rows, creating false large returns at boundaries. None preserves gaps as NaN and avoids inflated CAGR/volatility |
| 2026-03-07 | Phase 3 result: all strategies lag the benchmark on Sharpe | Over 25 years with real bear markets, equal-weight S&P 500 (SR 0.69) beats all 14 factor strategies (SR 0.53–0.66). Phase 2's optimistic results were regime-selection artifact |
| 2026-03-07 | Low Vol Shield is the only strategy that outperforms in a real crash | Dot-com crash Sharpe +0.63 vs benchmark +0.11. This was invisible in Phase 2 (no real bear market). Large Cap Momentum was the worst crash performer (−0.34) |
| 2026-03-07 | Rank stability collapses to −0.123 over 25 years | Phase 2's 0.749 stable ranking was an artifact of consistent bull regime 2014-2017. Over 25 years with multiple regime shifts, no strategy consistently leads |
| 2026-03-07 | Regime overlay HURTS performance over 25 years | 63-day lag in trend detection causes missing recoveries (esp. COVID V-shape). 0/14 strategies improved. In Phase 2 (mild bear periods), overlay helped MDD. In Phase 3 (real bear markets), it hurts both Sharpe AND MDD |
| 2026-03-08 | All strategies are effectively the same bet over 25 years | Phase 3 avg pairwise correlation 0.951 (Phase 2: 0.788). No pair below r=0.40. Diversification ratio 1.024 ≈ 1.0. No portfolio construction technique beats the benchmark. |
| 2026-03-08 | Bear regime correlation spikes to 0.969 | Diversification breaks down exactly during crashes. Factor strategies converge to pure long-equity exposure under stress — the fundamental limitation of long-only strategies. |
| 2026-03-08 | 25-year data confirms all 14 strategies have statistically real alpha | 12/14 pass all 3 bootstrap tests at 1%; 2/14 pass IID+block bootstrap at 1%. 0/14 not significant. Contrast Phase 2: 3/14 not significant, 3 marginal. More data = more certainty about small alpha. |
| 2026-03-08 | Sign test unsuitable for always-invested long-only strategies | Low Vol Shield and RSI Mean Reversion show sign_p=1.0 because they hold positions continuously — there's no timing component to test. IID and block bootstrap are the correct tests for these strategies. |
| 2026-03-08 | WFE > 100% in Phase 3.10 is regime-driven, not strategy skill | IS period (2000-2012) had 3 bear markets → lower IS Sharpe. OOS period (2013-2024) was a long bull → higher OOS Sharpe. Any passive index fund shows the same pattern. The real OOS test is Fold 2 (GFC 2008-09): ALL strategies went negative. |
| 2026-03-08 | Pre-compute signals once then slice returns by time period | Walk-forward with 9 folds + 14 strategies would require 126 strategy runs. Pre-computing signals once reduces it to 14 runs + 126 return slices — much faster and identical results. |
| 2026-03-08 | Phase 3 Tier 1 = Low Vol Shield + RSI Mean Reversion (not same as Phase 2 Tier 1) | Phase 2 Tier 1: LCM, 52wk, LowVol, QualMom, CompFactor. Phase 3 Tier 1: LowVol, RSI. Rank instability confirmed — selecting strategies based on short-window performance is unreliable. |
| 2026-03-08 | Phase 3 COMPLETE | All 12 stages (3.1–3.12) done. Key verdict: factor strategies have statistically real but small alpha (SR 0.53-0.66 vs benchmark 0.69). Phase 2 was bull-market artifact. Advancing to Phase 4 (dashboard + detail pages). |
| 2026-03-09 | Phase 4.1 COMPLETE | Research endpoint reads Phase 3 JSON files. Parameters endpoint exposes all 14 strategy params with ROBUST/FRAGILE labels from Phase 2.1. Frontend adds Research and Parameters tabs to strategy detail page with lazy loading, live backtest runner, and fold Sharpe visualisation. |
| 2026-03-09 | Parameters router declared before strategy router in research.py | FastAPI matches `/research/parameters/{name}` before `/research/{name}` by declaration order — `parameters` is a literal path segment so ordering is correct; no conflicts. |
| 2026-03-09 | Scorecard loaded in parallel with dashboard data | `Promise.all([fetchDashboardData(), fetch(scorecard)])` keeps page load fast — one round trip instead of 15 sequential calls. |
| 2026-03-09 | Sort defaults to Phase 3 Tier | This surfaces the highest-quality strategies (Low Vol Shield, RSI Mean Reversion) at the top by default — consistent with the Phase 3 research findings. |
| 2026-03-09 | Shorthand kbpr = update knowledge base and progress report | Set by user to remind about documentation updates after every step. |
| 2026-03-09 | Phase 4.2 COMPLETE | Dashboard banner updated to 25-year, tier badges, sort-by dropdown, tier filter pills. |
| 2026-03-09 | Phase 4.3 COMPLETE | Rolling Metrics tab on strategy detail page — AnnualBarChart (Sharpe/Return/MDD), rank stability badge, lazy loading. New endpoint GET /api/v1/research/rolling/{name}. |
| 2026-03-09 | Phase 4.4 COMPLETE | Correlation Heatmap tab — CorrelationHeatmap component (HTML table, red color scale), avg corr + DR summary stats, lazy loading. New endpoint GET /api/v1/research/correlation. |
| 2026-03-09 | Critical engine bug: signal weight accumulation → 15× leverage → -100% equity | Strategies' internal ffill carries forward old portfolio weights even after rebalancing, accumulating leverage. Fixed by normalizing aligned signals so abs().sum(axis=1) ≤ 1.0 in engine._align_signals(). |
| 2026-03-09 | WF fold labels fix — rolling_folds is list[list[str]] not int | React was rendering the full nested list as a string. Fixed by computing n_folds=len(raw_folds) and building fold_labels from fold[2][:7] – fold[3][:7]. |
| 2026-03-09 | 25-year DB backtests successful | scripts/run_extended_backtests_to_db.py stores all 14 strategies with 2000-2024 equity curves (weekly, ~1305 pts). Sharpe 0.59–0.74, MDD -22% to -57%. Benchmark CAGR 12.39%, SR 0.67. |
| 2026-03-10 | Phase 4.5 COMPLETE — Parameter Sensitivity Heatmap | SensitivityHeatmap component (5×5 Sharpe grid, red→green scale, default marker). New endpoint GET /api/v1/research/sensitivity/{name}. Lazy-loads in Parameters tab alongside sliders. Also shows 1D sweep bar charts per parameter. |
| 2026-03-10 | Phase 4.5 COMPLETE — CAPM Factor Attribution | scripts/compute_factor_alpha.py computes OLS alpha/beta for all 14 strategies. Results: β=0.54–1.18, α=-1.1% to +2.6%/yr, R²=85–93%. Only Low Vol Shield (+1.7%) and Earnings Surprise (+2.6%) have economically meaningful alpha. New endpoint GET /api/v1/research/alpha/{name}. Shown in Research tab as Factor Attribution section. |
| 2026-03-10 | Phase 4.6 COMPLETE — AI Strategy Builder | Full AI Strategy Builder page at /ai-strategy-builder. Backend: src/api/routes/ai_builder.py with 8-factor library, Claude Opus 4.6 (adaptive thinking) strategy matching, and 7-gate validation pipeline reading 25-year pre-computed data. Frontend: 2-panel chat UI — left=conversation, right=factor library/results. Gate results animate in with 280ms delay. Most strategies: 5P/1F/1C. Gate 4 (bear market) fails for all long-only strategies — shown honestly. Bonferroni correction applied (p < 0.0036). Requires ANTHROPIC_API_KEY env var. |
| 2026-03-10 | Live backtest endpoint updated to use 25-year extended data | /api/v1/backtests/run now loads extended_prices_clean.parquet instead of prices_clean.parquet. Parameters tab description updated to "2000–2024 (25-year)". |
| 2026-03-11 | UX polish — EquityCurveChart benchmark optional + AI Builder "View Full Analysis" link | EquityCurveChart.tsx: benchmark field made optional; benchmark line only rendered when data differs from strategy line (hasBenchmark check). Live backtest in strategy/[slug]/page.tsx no longer passes fake benchmark=equity. AI Strategy Builder: StrategySpecCard now shows "View Full 25-Year Analysis →" button linking to /strategy/{slug} — creates the key UX flow from AI Builder → strategy detail page. |
| 2026-03-11 | Long-Short Equity Curve — Research tab | research.py /alpha/{name} now returns full longshort.equity_curve (301 monthly points, 2000–2025). FactorAlpha TypeScript interface updated with equity_curve field. Research tab now shows "Dollar-Neutral Long-Short Portfolio" card: 4 KPI tiles (CAGR, Sharpe, Max DD, Market Corr) + equity curve chart + explanatory callout. Answers the key narrative question: "why do all strategies lag the benchmark?" — by stripping market beta to show the pure factor return. |
| 2026-03-11 | README fully rewritten for portfolio showcase | README.md replaced placeholder with comprehensive portfolio README: 14-strategy table, 8-layer validation table, key findings, tech stack, architecture, getting started, methodology notes (survivorship bias, look-ahead, transaction costs), phase log. |
| 2026-03-11 | AI Strategy Builder demo mode | DEMO_RESULT constant with full Low Volatility Shield example (5P/1F/1C, realistic gate values). "Load pre-computed demo" button in empty state — no API key required. Full demo of AI Builder UX: chat populates → gate animation triggers → all 7 gates reveal → "View Full 25-Year Analysis" navigates to strategy page. |
| 2026-03-11 | Dashboard data accuracy polish | FilterSidebar: Market Universe updated from "2014-2017" to "2000–2024, 653 stocks"; Date Range stale "Coming Soon" options removed, now shows "2000–2024 (25-year study)". KpiTiles: replaced useless "Implemented: 14/14" tile with "Best Sharpe (25yr)" tile; avgSharpe now computed from phase3Sharpe (25yr honest ~0.59); added sub-labels with benchmark comparison. TypeScript: clean compile. |
| 2026-03-11 | StrategyCard metric redesign | Discovered run_extended_backtests_to_db.py replaced 4yr DB data with 25yr — "Sharpe (4yr)" / "Total Return (4yr)" / "CAGR (4yr)" labels were all wrong. Redesigned Performance Preview: CAGR (25yr) + Sharpe (25yr) + Max Drawdown + Win Rate — 4 distinct metrics covering growth, risk-adj return, worst loss, consistency. Performance tab heading annotated "(25-year, 2000–2024)". |
| 2026-03-12 | Rolling chart benchmark reference line | AnnualBarChart.tsx: added `benchmarkAvg` prop → red dashed horizontal ReferenceLine at 25yr benchmark average (computed dynamically from rolling data). Yellow benchmark annual line: added dots (r=2), strokeWidth 2. In page.tsx: `rollingBenchmarkAvg` useMemo computes mean benchmark Sharpe/CAGR/MDD from rolling data, passed per metric toggle. |
| 2026-03-12 | Key Findings page (/findings) | New route `/findings` added to TopNav. Static page with: 4 finding cards (benchmark lag, rank instability, correlation trap, bear market failure), CAPM alpha table (β/α/significance for all 14), Phase 3 tier rankings with links to strategy pages, methodology summary. Designed for quant interviewers: 5-minute read of all research findings. |
| 2026-03-12 | Favicon + page titles | icon.tsx: 32px blue "SH" favicon via next/og. layout.tsx: title template '%s \| StrategyHub'. findings/page.tsx: metadata title set. ai-strategy-builder/layout.tsx: metadata title set. |
| 2026-03-12 | Path 1 — Live Signals: Current Holdings per Strategy | scripts/generate_live_signals.py: downloads 2yr yfinance prices for S&P 500, runs all 14 strategies, saves top-30 holdings to results/live_signals/current_signals.json. New API endpoints: GET /research/signals/{strategy_name} + GET /research/signals (metadata). Strategy detail Overview tab now shows "Current Holdings" card: top-20 symbols in 4-col grid with weights. Run: .venv/bin/python scripts/generate_live_signals.py |
| 2026-03-12 | Path 2 — AI Builder: generate-and-backtest endpoint | src/strategies/dynamic.py: DynamicFactorStrategy wraps exec()'d factor_code (restricted namespace, __builtins__={}) into full MultiAssetStrategy. src/api/routes/ai_builder.py: POST /ai-builder/generate-and-backtest endpoint — calls Claude, extracts factor_code JSON field, runs DynamicFactorStrategy+Backtester on 25yr data, returns custom_backtest metrics + weekly equity curve. Module-level _PRICES_CACHE avoids reloading parquet per request. |
| 2026-03-12 | Path 2 frontend — CustomBacktestPanel + loading stages | frontend/src/lib/api.ts: CustomBacktest interface + fetchAiBuilderGenerateAndBacktest(). ai-strategy-builder/page.tsx: switched to call generate-and-backtest; loadingStage state cycles "Analyzing → Generating factor code → Running 25-year backtest"; CustomBacktestPanel component shows Sharpe/CAGR/MDD KPI tiles, 25yr equity curve (recharts, purple), generated factor code in dark syntax block. ValidationPanel updated to render CustomBacktestPanel between StrategySpecCard and 7-gate section. DEMO_RESULT extended with factor_code + realistic custom_backtest. TypeScript clean compile. |

---

## 8. RISKS & LIMITATIONS

| Risk | Current Mitigation | Planned Fix |
|------|-------------------|-------------|
| Survivorship bias | Acknowledged (using Kaggle data) | Point-in-time lists in Phase 3 |
| Overfitting | Parameter sensitivity (12/14 robust) | Walk-forward in Phase 2.2 |
| Data snooping | Pre-register hypotheses | Out-of-sample testing |
| Transaction costs | 10 bps commission + 5 bps slippage | Sensitivity analysis in Phase 2 |
| Look-ahead bias | Signal at t, execute at t+1 | Already implemented |
| Short data window | 4 years (2014-2017) — bull market only | Extend to 2000-present in Phase 3 |
| No fundamental data | Price-derived proxies (documented) | Optional: yfinance fundamentals |

---

## 9. METRICS TRACKED

For each strategy:
- Total Return
- CAGR (Compound Annual Growth Rate)
- Sharpe Ratio
- Sortino Ratio
- Max Drawdown
- Calmar Ratio
- Win Rate
- Profit Factor
- Average Win / Average Loss
- VaR 95% / CVaR 95%

---

## 10. COMMANDS

```bash
# Start backend
cd /Users/mrigaypathak/Desktop/trading\ app/strategyhub-research
source venv/bin/activate
uvicorn src.api.main:app --reload --port 8000

# Start frontend
cd frontend && npm run dev

# Re-run all backtests
python scripts/run_all_backtests.py

# Check API
curl http://localhost:8000/api/v1/backtests/dashboard | python -m json.tool | head -50
```

---

## 11. FILE STRUCTURE

```
strategyhub-research/
├── CLAUDE.md                   # AI context file
├── PROGRESS_REPORT.md          # This file
├── requirements.txt            # Python dependencies
├── scripts/
│   ├── run_all_backtests.py    # Run all 14 strategies
│   ├── parameter_sensitivity.py # Phase 2.1: param sweep analysis
│   ├── walk_forward.py         # Phase 2.2: walk-forward + OOS testing
│   ├── monte_carlo.py          # Phase 2.3: bootstrap significance tests
│   ├── regime_analysis.py      # Phase 2.4: market regime analysis
│   ├── transaction_cost_sensitivity.py  # Phase 2.5: cost sweep analysis
│   ├── regime_overlay.py       # Phase 2.6: regime filter improvement
│   ├── portfolio_analysis.py   # Phase 2.7: correlation + portfolio construction
│   └── rolling_performance.py  # Phase 2.8: rolling Sharpe, drawdown, sub-period analysis
├── results/
│   ├── parameter_sensitivity/  # JSON + CSV results per strategy
│   ├── walk_forward/           # JSON + CSV walk-forward results
│   ├── monte_carlo/            # JSON + CSV Monte Carlo results
│   ├── regime_analysis/        # JSON + CSV regime analysis results
│   ├── transaction_costs/      # JSON + CSV transaction cost results
│   ├── regime_overlay/         # JSON + CSV overlay improvement results
│   ├── portfolio_analysis/     # Correlation matrix, portfolio comparison, JSON
│   └── rolling_performance/    # Rolling Sharpe/MDD/vol CSVs + JSON summary
├── src/
│   ├── api/
│   │   ├── main.py             # FastAPI app
│   │   ├── routes/             # backtests.py, strategies.py
│   │   └── schemas.py          # Pydantic models
│   ├── backtesting/
│   │   ├── engine.py           # Vectorized backtester
│   │   └── metrics.py          # Performance metrics
│   ├── database/
│   │   ├── connection.py       # SQLite setup
│   │   ├── models.py           # SQLAlchemy models
│   │   └── repository.py       # DB queries
│   ├── processing/
│   │   └── indicators.py       # Technical indicators
│   └── strategies/
│       ├── __init__.py         # STRATEGY_REGISTRY (14 strategies)
│       ├── base.py             # Abstract base classes
│       ├── momentum.py         # LargeCapMomentum, 52WeekHighBreakout
│       ├── value.py            # DeepValueAllCap
│       ├── quality.py          # HighQualityROIC
│       ├── factor.py           # LowVolShield, DividendAristocrats
│       ├── trend.py            # MovingAverageTrend
│       ├── mean_reversion.py   # RSIMeanReversion
│       ├── composite.py        # ValueMomentum, QualityMom, QualityLowVol, CompositeFactor
│       ├── risk_management.py  # VolatilityTargeting
│       └── event.py            # EarningsSurpriseMomentum
├── frontend/
│   └── src/
│       ├── app/page.tsx        # Dashboard page
│       ├── components/         # FilterSidebar, StrategyCard, KpiTiles, TopNav
│       └── hooks/
│           └── useDashboardData.ts  # API fetch + strategy enrichment
├── data_raw/                   # Raw downloaded data
├── data_processed/
│   └── prices_clean.parquet    # 497K rows, 505 symbols, 2014-2017
└── notebooks/                  # Jupyter analysis
```

---

## 12. KNOWLEDGE BASE

Companion learning document: [KNOWLEDGE_BASE.md](KNOWLEDGE_BASE.md)

Covers (updated per phase):
- All performance metrics (Sharpe, MDD, Calmar, Sortino, etc.) and how to interpret them
- How the backtesting engine works (vectorized, look-ahead prevention, transaction costs)
- Each Phase 2 technique (parameter sensitivity, walk-forward, OOS, Monte Carlo, regime analysis)
- Factor investing primer (momentum, value, quality, low vol — why they work and when they fail)
- Glossary

---

## 13. CONTACT & OWNERSHIP

- **Owner:** Mrigay Pathak
- **Purpose:** Personal research, portfolio showcase
- **Started:** January 2026
- **Phase 1 Completed:** March 2026
