# I Built an AI That Generates Custom Trading Strategies and Backtests Them in 60 Seconds

*By Mrigay Pathak — Finance & Informatics, Indiana University Bloomington*

---

Here's a question I kept asking while building my factor research platform: *what if you could describe any trading idea in plain English, and immediately see whether it would have worked over 25 years?*

Not "here are five pre-built strategies, pick one." Actually generate the factor math from your description, run it against real data, and tell you where it passes and fails.

That's what I built. Here's how it works.

---

## The Problem With Existing Tools

Most backtesting platforms give you a menu. You pick from momentum, RSI, moving averages. If your idea doesn't fit the menu, you're writing code from scratch — which means knowing Python, pandas, and the backtesting framework, often spending hours debugging before you get a single result.

The research platform I built already had 14 validated strategies and 25 years of pre-computed results. What it didn't have: a way for someone to bring a *new* idea and test it rigorously in the same framework.

The AI Strategy Builder solves this.

---

## How It Works

### Step 1: You describe the strategy

You type something like:

> *"I want to buy stocks that have been beaten down but are starting to recover — oversold but with improving momentum"*

or:

> *"Build a low-risk strategy that avoids volatile stocks and protects capital in downturns"*

### Step 2: Claude Opus 4.6 analyzes it

The model (using adaptive thinking) does four things simultaneously:

1. **Maps** your description to the closest academically-documented factor from an 8-factor library (momentum, value, quality, low volatility, RSI mean reversion, volatility targeting, 52-week high, PEAD)
2. **Decomposes** it into factor weights — how much of your idea is momentum vs. quality vs. mean reversion
3. **Writes an economic hypothesis** — *why should this edge exist?* What's the behavioral or structural reason the market misprices these stocks?
4. **Generates Python factor code** — a self-contained scoring function that, given a price matrix, outputs a stock ranking

The factor code output looks like this for a momentum-mean-reversion blend:

```python
momentum = prices.pct_change(252).shift(21)
rsi_delta = returns.copy()
gain = rsi_delta.clip(lower=0).rolling(14).mean()
loss = (-rsi_delta.clip(upper=0)).rolling(14).mean()
rsi = 100 - (100 / (1 + gain / loss.replace(0, np.nan)))
oversold_score = -rsi  # lower RSI = higher score
m_rank = momentum.rank(axis=1, pct=True)
r_rank = oversold_score.rank(axis=1, pct=True)
return 0.6 * m_rank + 0.4 * r_rank
```

### Step 3: The code runs against 25 years of real data

The backend wraps the generated code into a `DynamicFactorStrategy` — a class that:
- Compiles the factor code in a restricted namespace (`__builtins__: {}` — no arbitrary imports)
- Runs it across the full 653-symbol S&P 500 universe, 2000–2024
- Selects the top 20% of stocks by score each month
- Executes trades through the same vectorized backtester used for all 14 pre-built strategies

The output: Sharpe ratio, CAGR, max drawdown, volatility, and a 25-year equity curve — for the exact strategy you described.

### Step 4: The 7-gate validation pipeline

The generated strategy's *matched pre-built counterpart* is also run through rigorous validation:

| Gate | What It Tests | Typical Result |
|------|-------------|----------------|
| 1 | In-sample Sharpe > 0.5 | 14/14 pass |
| 2 | Walk-forward efficiency ≥ 100% | 13/14 pass |
| 3 | Monte Carlo p < 0.05 | 12/14 pass |
| 4 | Bear market Sharpe > −0.5 | **0/14 pass** |
| 5 | Transaction cost resilience | 14/14 pass |
| 6 | Out-of-sample holdout Sharpe > 0 | 13/14 pass |
| 7 | Bonferroni bias audit | 12/14 pass |

Gate 4 fails for every long-only strategy. That's intentional and honest — it's what the data shows. All long-only equity strategies lose money in bear markets. Any tool that tells you otherwise is hiding the truth.

---

## The Technical Architecture

```
User input (plain English)
        ↓
Claude Opus 4.6 (adaptive thinking)
        ↓
JSON: matched_strategy + factors + hypothesis + factor_code
        ↓
DynamicFactorStrategy(factor_code)
  └─ exec() in restricted namespace
  └─ top-quintile signal generation
  └─ monthly rebalancing
        ↓
Backtester (vectorized, 653 symbols × 6,288 days)
        ↓
Sharpe / CAGR / MDD / equity_curve
        ↓
7-gate validation pipeline
        ↓
Full results returned to frontend
```

The full roundtrip — Claude API call + 25-year backtest — takes about 15–30 seconds.

### The module-level prices cache

One engineering decision worth explaining: the 25-year price matrix is 3.4 million rows. Loading and pivoting it takes 2–3 seconds. To avoid doing this on every request, the backend caches it in a module-level variable `_PRICES_CACHE` — loaded once when the server starts, reused for every subsequent generate-and-backtest call.

---

## What Makes This Different

A few things I haven't seen combined elsewhere:

**1. It generates and executes, not just classifies.**
Most AI finance tools classify your idea ("this sounds like a momentum strategy"). This one writes the actual scoring function, runs it, and returns real numbers. The strategy you described is the strategy that gets backtested.

**2. The validation is genuinely rigorous.**
The 7-gate pipeline includes a Bonferroni correction for multiple comparison bias, Monte Carlo significance testing with 10,000 permutations, and honest disclosure of survivorship bias. It's designed to be harder to pass than easier.

**3. Negative results are surfaced, not hidden.**
Gate 4 (bear market resilience) fails for every long-only strategy, displayed prominently with the explanation: *"All 14 long-only strategies fail in bear markets. This is the academic truth of long-only equity factor strategies."* Most investment tools are incentivized to make results look good. This one isn't.

**4. The economic hypothesis is required.**
Claude must articulate *why* the edge should exist before it generates the factor code. This isn't decorative — it forces the reasoning to be grounded in market structure, not just data fitting.

---

## Limitations I'm Honest About

**The sandbox is minimal.** The `exec()` call uses `__builtins__: {}` to prevent arbitrary imports, but this is not a true sandbox. It's adequate for a single-user research platform; it would need a proper isolated container for multi-tenant production use.

**The matched strategy validation is a proxy.** The 7-gate validation uses pre-computed data for the closest pre-built strategy, not the custom code. Gate 1–7 are accurate for the matched strategy; the custom backtest is run separately. For custom strategies with no close match, the validation is less meaningful.

**Survivorship bias remains.** The dataset uses historical S&P 500 constituent lists (partially correcting for survivorship) but doesn't include all delisted or bankrupt stocks, which would require commercial data (CRSP). Estimated residual bias: 1–2% CAGR.

---

## What I Learned Building This

The most interesting part wasn't the AI integration — it was designing the `factor_code` specification. The function body receives `prices`, `returns`, `pd`, and `np`. It must return a DataFrame of scores with higher values meaning more attractive stocks. No helper functions, no imports, single return statement.

Constraining Claude to that interface — while making the examples varied enough that it could express any factor logic — took more iteration than I expected. The key was showing five diverse examples (momentum, low-vol, 52-week high, RSI, composite) that covered the full range of pandas operations it would need.

The other thing I learned: code generation only works when you know exactly what the generated code will be handed to. The `DynamicFactorStrategy` wrapper, the restricted namespace, the monthly rebalancing logic — all of this had to exist and be robust before I could design the prompt that would generate code for it. You can't prompt-engineer your way around engineering infrastructure.

---

## What's Next

The natural extension is Indian markets. The same 14 strategies, the same 7-gate validation, the same AI builder — but running on NSE 500 data. The low-volatility anomaly is actually larger in emerging markets where institutional leverage constraints are stronger. PEAD (earnings surprise drift) is larger in markets with less analyst coverage.

That's the next phase: StrategyHub India.

---

*The platform is live at [platform link]. The AI Strategy Builder is at [link]. Try describing any strategy — the honest answer is always more useful than the optimistic one.*

*Previous post: [I backtested 14 strategies over 25 years — none beat the index](./01_14_strategies_25_years.md)*
