# How I'm Using 25 Years of Backtested Factor Research to Trade Prop Firm Accounts

*Posted by Mrigay Pathak | April 2026*

---

Most people who build backtesting platforms stop at the backtest. They publish a Sharpe ratio, call it research, and move on.

I wanted to actually use mine.

This is the story of how I connected a 25-year, 14-strategy factor research platform to a morning trade list that tells me exactly what to buy, how much to allocate, and whether I'm inside FTMO's risk rules — before the market opens.

---

## What Prop Trading Actually Is

If you're not familiar: prop firms (FTMO, Apex Funding, TopStep) give you their capital to trade. You keep 80-90% of profits. In exchange, you have to pass a "challenge" — a demo account where you prove you can make money without violating their risk rules:

- **FTMO**: Max daily loss 5%, max total drawdown 10%, profit target 10%
- **Apex**: Max daily loss 3%, trailing drawdown varies by account size
- **TopStep**: Max daily loss 2%, max trailing drawdown 3-6%

The hard part isn't making money. It's making money *without a single bad day blowing your account*.

That's where systematic strategies have a massive edge over discretionary traders.

---

## Why Factor Strategies Fit Prop Trading Rules

After 25 years of backtesting, the single most important stat I found wasn't Sharpe ratio. It was **turnover**.

My 14 strategies have annual turnover of 0.2x to 6.3x. For context:
- A day trader might turn their portfolio over 100x per year
- A momentum strategy rebalances monthly (12x at most)
- My Low Volatility Shield rebalances quarterly (0.2x per year)

Low turnover means:
- Positions are held for weeks or months, not minutes
- A single bad day doesn't wipe out a position — the strategy has time to recover
- You're never scrambling to meet a daily P&L target

This is structurally aligned with how prop firms work. They *want* consistent, measured risk-taking. They don't want you swinging for the fences every morning.

---

## The Morning Trade List

Each morning before 9:30am ET, I run one command:

```bash
.venv/bin/python scripts/morning_trade_list.py --refresh --account 10000
```

Here's what happens in ~3 minutes:

1. **Fresh data pull**: 2 years of S&P 500 price data downloaded from Yahoo Finance
2. **14 strategies run simultaneously**: Each generates its current holdings
3. **Consensus scoring**: Stocks appearing across multiple strategies get higher scores
   - Tier 1 strategy (Low Vol Shield, RSI): 3 points per appearance
   - Tier 2 strategy (Large Cap Momentum, 52-Week High, etc.): 2 points
   - Other strategies: 1 point
4. **Three filters applied**:
   - **Earnings filter**: Any stock reporting in the next 3 days is blacklisted
   - **Sector concentration**: Warns if any sector exceeds 40% of portfolio
   - **News sentiment**: Headlines scored positive/negative per stock
5. **Position sizing**: Score-proportional, capped at 10% per stock, 80% deployment (20% cash)
6. **Prop firm check**: Estimated max daily loss calculated against FTMO/Apex/TopStep limits

This morning's output (April 2026, $10k account):

```
════════════════════════════════════════════════════════════════════════════════
  STRATEGYHUB — MORNING TRADE LIST
  April 16, 2026  |  Account: $10,000  |  Signal Date: 2026-04-09

  PROP FIRM COMPATIBILITY
  FTMO    (5% daily limit):   ✅ SAFE
  Apex    (3% daily limit):   ✅ SAFE
  TopStep (2% daily limit):   ✅ SAFE
  Est. max daily loss:  1.60%   |   Cash buffer: 20.1%

  TOP BUY CANDIDATES
    1  AEE    24.2   9 ★★    7.5%  $    746
    2  AEP    20.6   8 ★★    6.4%  $    638
    3  ATO    20.6   7 ★★    6.4%  $    635
    4  AFL    19.1   7 ★★    5.9%  $    590
    5  ABT    19.0   7 ★★    5.9%  $    587    ⚠️ EARNINGS
```

ABT (Abbott Labs) was automatically flagged — earnings report in the next 3 days. Skip it regardless of the signal score.

---

## What the Consensus Score Actually Means

AEE (Ameren Corp) scoring 24.2 with 9 strategy confirmations isn't luck.

These 9 strategies use completely different logic:
- **52-Week High Breakout**: AEE is trading near its 52-week high → price momentum signal
- **Low Volatility Shield**: AEE has below-average volatility → defensive quality signal  
- **Composite Factor Score**: AEE ranks in the top decile on combined value + quality + momentum
- **Dividend Aristocrats**: AEE has a consistent dividend growth history
- ...and five more independent strategies agreeing

When you have 9 independent algorithms built on different academic papers, different data, different logic — and they all say "hold this stock right now" — that's genuine conviction. Not one algorithm's noise.

This is the core insight of factor investing: no single signal is reliable. But when you stack them, you filter out the noise.

---

## The Honest Limitations

I'm not going to pretend this is a guaranteed money machine. After 25 years of rigorous testing, here's what the data actually shows:

**All 14 strategies lag the S&P 500 benchmark (0.694 Sharpe) on a risk-adjusted basis.** The best strategy (Low Volatility Shield) achieves 0.659 Sharpe. That's 95% of benchmark performance — close, but not better.

**In bear markets, everything fails.** Average Sharpe across all 14 strategies in bear regimes is below -1.0. These are long-only strategies. When the market sells off, they sell off too.

**Rank instability: -0.123 Spearman correlation year-over-year.** This year's best strategy has essentially no predictive power for next year's ranking.

So why use it?

Because "slightly below benchmark with lower volatility and a systematic process" is still vastly better than most discretionary traders. And in prop trading, it's the *process* that keeps you from blowing your account on a bad week.

---

## What's Coming Next

I'm extending this to **NSE 500 (Indian market)** — running the same 14 strategies on Nifty 500 stocks using yfinance data. If factor premia are real, they should appear across markets. If Indian markets show different factor exposures than US markets, that's genuinely interesting research no US undergrad has published.

The morning trade list will get an **Indian market mode** next.

---

## The Platform

Everything described here — the backtesting engine, all 14 strategies, the research analysis, the AI Strategy Builder — is live at the link in my bio.

The morning trade list script is open source in the GitHub repo.

---

*Mrigay Pathak is a Finance + Informatics junior at Indiana University Bloomington with internship experience at JM Financial (Apex Capital) and Alchemy Capital (Jhunjhunwala family office). Building StrategyHub Research as a systematic trading research platform.*
