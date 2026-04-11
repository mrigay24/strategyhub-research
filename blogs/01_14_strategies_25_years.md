# I Backtested 14 Factor Strategies Over 25 Years. None Beat the S&P 500. Here's Why.

*By Mrigay Pathak — Finance & Informatics, Indiana University Bloomington*

---

Most backtesting posts are designed to impress you. This one isn't.

I spent several months building a systematic research platform that tests 14 academically-documented factor strategies — momentum, value, quality, low volatility, mean reversion, and composites — against 25 years of S&P 500 data (2000–2024). The dataset covers 653 symbols, 3.4 million rows, and three complete market crashes: the dot-com bubble, the Global Financial Crisis, and COVID.

The headline result: **0 out of 14 strategies beat the benchmark on a risk-adjusted basis.**

The benchmark Sharpe ratio was 0.694. The best strategy — Low Volatility Shield — achieved 0.659.

That's the honest answer. And I think it's actually more valuable than the green-number backtests you usually see.

---

## What I Built

The platform runs all 14 strategies as multi-asset portfolios across the full S&P 500 universe. Each strategy is a factor model — it ranks every stock by some signal (momentum, value, quality) and holds the top quintile, rebalancing monthly. The backtester is fully vectorized, prevents look-ahead bias (signal at day *t*, execution at *t+1*), and applies realistic transaction costs (10 bps commission + 5 bps slippage).

The validation pipeline has eight layers:

1. **In-sample Sharpe** — does the strategy actually work?
2. **Walk-forward validation** — does it generalize out-of-sample?
3. **Monte Carlo significance** — are returns statistically different from random?
4. **Regime analysis** — does it survive bear markets?
5. **Transaction cost sensitivity** — does friction kill the edge?
6. **Parameter sensitivity** — is it robust or curve-fitted?
7. **Portfolio correlation analysis** — does it diversify?
8. **CAPM attribution** — is there real alpha, or just market beta?

The results, once you run all eight layers honestly, are sobering. Here are the four things I found.

---

## Finding 1: All 14 Strategies Lag the Benchmark

| Tier | Strategies | Sharpe Range | vs Benchmark (0.694) |
|------|-----------|-------------|----------------------|
| 1 | Low Vol Shield, RSI Mean Reversion | 0.641–0.659 | −5% |
| 2 | Large Cap Momentum, Quality+Momentum, 52-Week High, Composite Factor, Value+Momentum, Earnings Surprise | 0.57–0.60 | −13–18% |
| 3 | Deep Value, High Quality ROIC, Moving Average Trend, Dividend Aristocrats, Quality+Low Vol, Volatility Targeting | 0.53–0.56 | −19–24% |

The benchmark Sharpe of 0.694 — simple buy-and-hold S&P 500 — beats every single strategy.

**Why?** Fees, transaction costs, and the concentration penalty. When you hold only the top 20% of stocks and rebalance monthly, you pay to trade, you miss out on stocks just below your threshold, and you bear the full volatility of a concentrated portfolio. The market-cap-weighted benchmark holds everything and turns over almost nothing.

This is a real result, not a failure. It's what the academic literature says too. Most published factor premiums shrink or disappear when transaction costs are applied to live portfolios.

---

## Finding 2: No Consistent Winner Over 25 Years

The rank stability coefficient across all 14 strategies is **−0.123** — meaning performance rankings in one period are slightly *negatively* correlated with rankings in the next.

In plain language: the strategy that worked last year is more likely to underperform next year than to continue outperforming. There's no consistent winner.

I computed rolling annual Sharpe ratios for each strategy across 25 years. The pattern is clear:

- **2000–2015:** Average Sharpe across all strategies = 0.20 (barely above zero)
- **2016–2024:** Average Sharpe across all strategies = 1.83 (strong bull market)

Most of what looks like "strategy alpha" in short backtests is actually bull market beta. The 2014–2017 data window many backtesting tutorials use was almost perfectly selected to make every strategy look brilliant.

---

## Finding 3: The Diversification Trap

I built several multi-strategy portfolios expecting diversification benefits. The average pairwise correlation between the 14 strategies is **0.951**. In bear markets, it rises to **0.969**.

The diversification ratio — the ratio of the weighted-average volatility to portfolio volatility — is 1.024. Combining 14 strategies gives you 2.4% volatility reduction. The entire premise of "combine strategies for diversification" collapses when every strategy is essentially long the S&P 500 with different stock selection tilts.

This is the correlation trap: the more you diversify across factors, the more you're just holding the market with extra complexity and transaction costs.

---

## Finding 4: Every Strategy Fails in Bear Markets

Bear regime Sharpe ratios (covering dot-com crash, GFC, COVID):

| Strategy | Bear Sharpe |
|----------|------------|
| Low Vol Shield (best) | −1.41 |
| Average across 14 | −1.80 |
| Benchmark | −1.20 |

Every strategy, without exception, significantly underperforms in bear markets. Long-only equity factor strategies are inherently correlated with market direction. You cannot diversify away systemic risk by changing which stocks you hold if you're still long-only.

The only meaningful protection is either short positions, options, or genuine market-timing (which has its own problems). The regime overlay I tested — exiting to cash during bear regimes — reduced drawdowns by 5–26%, but the 63-day signal lag missed fast crashes entirely (COVID took just 23 days from peak to trough).

---

## What Actually Works: CAPM Alpha Decomposition

I ran CAPM regressions (OLS) for all 14 strategies to separate market beta from genuine alpha. The results:

| Strategy | Beta (β) | Alpha/yr (α) | R² | Verdict |
|----------|---------|-------------|-----|---------|
| Low Vol Shield | 0.64 | **+1.7%** | 87% | Meaningful alpha |
| Earnings Surprise | 1.18 | **+2.6%** | 85% | Meaningful alpha |
| Large Cap Momentum | 0.91 | +0.8% | 91% | Marginal |
| Quality+Momentum | 0.88 | +0.5% | 93% | Marginal |
| RSI Mean Reversion | 0.72 | +0.3% | 89% | Marginal |
| Deep Value All-Cap | 1.03 | −1.1% | 88% | Negative alpha |

Only two strategies generate economically meaningful alpha after accounting for market exposure:

**Low Volatility Shield (+1.7%/yr):** The low-volatility anomaly is one of the most well-documented in academic finance (Baker, Bradley & Wurgler 2011; Frazzini & Pedersen 2014). Low-vol stocks violate CAPM's prediction that higher risk = higher return. The anomaly persists because leveraged investors avoid low-vol stocks (they need volatility to maximize return on equity), creating a persistent mispricing.

**Earnings Surprise Momentum (+2.6%/yr):** Post-Earnings Announcement Drift (PEAD) is documented in Bernard & Thomas (1989). Markets systematically underreact to earnings surprises — stocks with large positive surprises continue drifting upward for 30–90 days. This is one of the cleanest documented market inefficiencies, though it's diminishing as more capital chases the signal.

---

## The Most Important Lesson: Benchmark Drag

Here's the uncomfortable arithmetic: the S&P 500 at a 0.694 Sharpe ratio over 25 years, with zero turnover and near-zero costs, is extraordinarily hard to beat net of implementation friction.

The academic factor literature documents *gross* returns before costs, often on paper portfolios that can't be traded. The moment you add monthly rebalancing, realistic transaction costs, and concentration risk, most factor premiums compress to the point where they no longer justify the complexity.

This doesn't mean systematic factor investing is useless. It means the bar is higher than most backtests suggest, and the two strategies with genuine alpha (Low Vol Shield and Earnings Surprise) work for documented economic reasons, not just because they happened to fit the data well.

---

## What I'd Do Differently

If I were to rebuild this for a production portfolio, I'd focus on:

1. **Long-short construction** — eliminate market beta entirely and isolate the pure factor return
2. **Shorter rebalancing for PEAD** — earnings surprise signals decay fast; daily rebalancing captures more of the drift
3. **Indian markets** — the low-vol and quality anomalies are actually larger in emerging markets where institutional constraints are stronger
4. **Genuine out-of-sample holdout** — reserve 2022–2024 from the start, never look at it until the final test

---

## The Platform

The full research platform is available at [GitHub link] — 14 strategies, 25 years of data, full validation pipeline, interactive strategy comparison, and an AI Strategy Builder that lets you describe a trading idea in plain English, generate the factor code, and see a real backtest in 60 seconds.

All research findings are live at [platform link]. The data speaks for itself.

---

*Next post: I built an AI that generates custom factor strategies and backtests them in 60 seconds — here's the architecture.*

*Follow for systematic trading research, honest backtesting methodology, and factor investing deep-dives.*
