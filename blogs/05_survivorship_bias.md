# Why Most Backtests Lie: The Survivorship Bias Problem

*By Mrigay Pathak — Finance & Informatics, Indiana University Bloomington*

---

If you've ever read a backtesting study with a Sharpe ratio above 1.5 and annualized returns of 25%+, there's a good chance you're looking at a lie.

Not a deliberate lie. Most quant researchers don't set out to deceive. But backtesting has a structural flaw that inflates results automatically, without anyone trying — and the majority of published research, retail backtesting tools, and strategy showcases fail to correct for it.

That flaw is called **survivorship bias**.

---

## What Survivorship Bias Actually Means

Here's a simple version: imagine you're testing a "buy stocks in the S&P 500" strategy.

You download the current S&P 500 constituent list — 503 companies — and backtest them from 2000 to today. Your results look great. The S&P 500 has crushed every other asset class over 25 years.

The problem? The list you downloaded is the **2024 S&P 500**. These companies *already survived* 25 years of market selection. The ones that went bankrupt, merged, or got ejected from the index aren't in your dataset.

You tested the winners, retroactively.

---

## The Numbers Behind the Bias

This isn't a theoretical concern. The effect is large and measurable.

Between 2000 and 2024, hundreds of companies were removed from the S&P 500:
- **Delisted entirely**: Enron, Lehman Brothers, Bear Stearns, Washington Mutual, hundreds of smaller bankruptcies
- **Acquired**: Compaq, Sprint, Time Warner, Motorola, Wachovia
- **Downgraded out**: Thousands more that shrank below the index threshold

If you backtest only the current constituents from 2000, you've already excluded every company that failed during your study period. Your dataset has a systematic upward bias built in.

Academic estimates put the survivorship bias effect at **1-2% per year** in annualized returns. Over a 25-year backtest, that's the difference between a Sharpe ratio of 0.5 and 0.9. It's the difference between "this strategy is marginal" and "this strategy looks promising."

---

## How I Found This in My Own Research

When I built StrategyHub, I started with a dataset of current S&P 500 stocks — 505 symbols with clean data from 2014-2017.

The results were impressive. 14 strategies, all producing Sharpe ratios well above 0.8. Some above 1.0.

Then I extended the data to 25 years (2000-2024) and switched to **historical constituent lists** — meaning at each date, I only included stocks that were *actually in the S&P 500 at that time*, including companies that were later delisted or went bankrupt.

What happened?

**The average Sharpe ratio dropped from ~0.95 to ~0.59.**

That's the survivorship bias penalty in real data. ~40% of the apparent "alpha" evaporated the moment I used the right dataset.

The strategies didn't get worse. They were never as good as the biased dataset suggested.

---

## Three Types of Bias Working Against You

Survivorship bias is the most famous, but it's part of a broader family of data problems:

**1. Survivorship bias** (who's in the dataset)  
Only survivors are included. Companies that went bankrupt between your backtest start and today are missing from your data.

**2. Look-ahead bias** (when information is available)  
Using today's financial statements to calculate "what a ratio would have been in 2003." In reality, 2003 investors had 2003 filings — which were sometimes restated, delayed, or outright fraudulent.

**3. Index inclusion effect** (why stocks entered the dataset)  
Stocks often rise when they're added to major indices (due to forced buying by index funds), creating an artificial boost at the start of their index membership. If your backtest begins at the date a stock joined the S&P 500, you're capturing that entry premium.

Each of these inflates results. In combination, they can turn a market-lag strategy into a market-beater on paper.

---

## The Right Way to Backtest

Getting this right is harder than it looks, but the principles are clear:

**Use point-in-time constituent lists.**  
For each date in your backtest, the eligible universe should only include stocks that were in the index *at that date*, not stocks that are in the index now.

I built this for StrategyHub using historical S&P 500 membership data. At each trading date, the backtest runs on whatever 400-600 stocks were actually eligible that day — including companies that later failed.

**Include delisted stocks.**  
If a company delisted in 2008, you need to hold it until its last trading date and take the loss. Dropping it from the dataset is equivalent to pretending the loss didn't happen.

**Use point-in-time fundamentals.**  
Valuation ratios (P/E, P/B) should use the financial data *available at the time*, not data that was later revised. This is harder — it requires a point-in-time fundamental database, which is expensive (Bloomberg, Compustat, or manual reconstruction).

**Verify your data cleaning pipeline.**  
When I extended StrategyHub to 25 years, I discovered that price data for micro-cap stocks and illiquid names had extreme returns caused by data errors — stocks showing +5000% in a day because of adjusted price miscalculations. Each cleaning step required careful sequencing: price floors first, then return filters, then NaN handling. Order matters.

---

## Why This Matters for Retail Quants

Most retail backtesting platforms don't fix survivorship bias. They can't — they don't have historical constituent data, and delisted stocks often aren't in their databases.

This means:

- **Zipline** (Yahoo Finance data): survivorship-biased by default unless you add your own delisted data
- **Backtrader**: depends on your data source; most free sources are biased
- **QuantConnect**: partially addressed via their alternative data partnerships, but not guaranteed
- **Excel backtests**: almost certainly survivorship-biased

When someone publishes "I made 30% annually from 2010 to 2024 using this momentum strategy," the first question to ask is: **what universe did you test on?**

If the answer is "current S&P 500 constituents" or "stocks on my broker's platform," the results are almost certainly inflated.

---

## The Honest Conclusion

After fixing survivorship bias in StrategyHub, none of my 14 strategies beat the S&P 500 benchmark on a risk-adjusted basis over 25 years. The benchmark Sharpe ratio was 0.694. The best strategy achieved 0.659.

That sounds like failure. I think it's actually the right answer.

The benchmark itself is a hard-to-beat, well-diversified, cheap-to-implement strategy. A factor strategy that genuinely beats it after transaction costs, realistic data, and 25-year out-of-sample validation would be exceptional — not the norm.

The strategies still have value: they provide diversified factor exposure, some perform better in specific regimes, and the long-short implementations show genuine factor premia. But none of them are the "30% annual returns with a 1.5 Sharpe" stories that fill Twitter and Reddit.

Those stories are usually survivorship bias in action.

---

## What I Built Instead

Rather than paper over the bias, StrategyHub publishes the honest numbers:
- 25-year backtests using historical constituents
- Delisted stocks included through their last trading date
- Walk-forward validation (IS vs OOS performance comparison)
- Monte Carlo significance testing
- Regime analysis (how strategies perform in bull, bear, high-vol, sideways markets)
- Transaction cost sensitivity analysis

If a strategy survives all those filters and still produces a positive alpha — like the Earnings Surprise strategy's +2.6% annual CAPM alpha — then it's worth paying attention to.

Everything else is noise, most of which survivorship bias created.

---

*StrategyHub Research is an open-source systematic trading research platform. All research, data methodology, and source code are published at [github.com/mrigay24/strategyhub-research](https://github.com/mrigay24/strategyhub-research).*
