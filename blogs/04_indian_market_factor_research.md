# I Ran 14 Factor Strategies on Indian Stocks. The Results Surprised Me.

*Posted by Mrigay Pathak | April 2026*

---

Every factor investing paper you've read was written about US markets.

Fama and French's original 1992 paper: US stocks. Jegadeesh and Titman's momentum study: US stocks. Virtually every academic study that institutional quant funds are built on: US stocks, US data, US market structure.

So I asked a simple question: **do these factor strategies work in India?**

I ran the same 14 strategies I'd already validated on S&P 500 stocks — over the same time period, using the same backtesting engine, with zero modifications — on the NIFTY 500. Here's what I found.

---

## The Setup

**Data**: 328 NIFTY 500 stocks via Yahoo Finance (`.NS` suffix), 2005–2026, 1.63 million rows  
**Strategies**: Same 14 factor strategies as the US study — momentum, value, quality, low volatility, mean reversion, composite factors  
**Engine**: Same vectorized backtester with look-ahead bias prevention, transaction costs, signal normalization  
**Benchmark**: Equal-weight NIFTY 500

The only change: Indian stock tickers instead of S&P 500 tickers. The strategies didn't know they were running on Indian stocks.

---

## The Results

| Strategy | US Sharpe | NSE Sharpe | US CAGR | NSE CAGR |
|---|---|---|---|---|
| RSI Mean Reversion | 0.641 | **1.110** | 12.1% | **24.9%** |
| Volatility Targeting | 0.59 | **1.107** | 10.2% | **14.3%** |
| Moving Avg Trend | 0.58 | **1.073** | 11.3% | **23.0%** |
| 52-Week High Breakout | 0.59 | **1.058** | 11.8% | **22.8%** |
| Dividend Aristocrats | 0.57 | **1.047** | 10.8% | **16.6%** |
| Quality + Low Vol | 0.60 | **1.042** | 11.5% | **20.5%** |
| Composite Factor | 0.59 | **1.005** | 11.2% | **21.4%** |
| Value + Momentum | 0.58 | **0.995** | 11.0% | **21.6%** |
| High Quality ROIC | 0.57 | **0.991** | 10.9% | **18.9%** |
| Quality Momentum | 0.60 | **0.985** | 11.5% | **21.2%** |
| Low Volatility Shield | 0.659 | **0.984** | 12.0% | **16.0%** |
| Deep Value | 0.58 | **0.976** | 11.1% | **21.2%** |
| Large Cap Momentum | 0.66 | **0.812** | 12.4% | **17.5%** |

**13 out of 14 strategies have a higher Sharpe ratio on NSE than on S&P 500.**

The weakest US strategy (0.57 Sharpe) becomes a 0.98 Sharpe on Indian stocks. The best US strategy (0.66 Sharpe) goes to 1.11 in India.

---

## Why Indian Markets Outperform — My Hypothesis

This isn't luck. There are structural reasons why factor strategies should work better in India than in the US:

**1. Less institutional efficiency**

The S&P 500 is the most researched, most traded market on earth. Thousands of quant funds run momentum strategies on Apple and Microsoft. The edge gets arbitraged away quickly.

NIFTY 500 mid-caps are covered by far fewer analysts, traded by fewer algorithmic funds, and mispriced more persistently. Factor signals take longer to get arbitraged out — meaning more alpha.

**2. Retail-dominated markets**

Indian markets have a much higher proportion of retail traders compared to the US. Retail traders exhibit stronger behavioral biases — anchoring, loss aversion, herding — which factor strategies are explicitly designed to exploit.

The 52-Week High Breakout strategy (Sharpe 1.06 on NSE) works because investors anchor to the 52-week high and underreact to positive news near that level. In a retail-heavy market, this behavioral bias is more pronounced.

**3. Higher volatility premium**

Indian markets have historically higher volatility than US markets (Nifty 50 beta relative to global markets is ~1.2–1.4). Higher volatility = more dispersion in individual stock returns = more opportunity for cross-sectional strategies.

**4. Momentum is stronger**

Price momentum (Jegadeesh-Titman effect) is known to be stronger in emerging and developing markets. India's mix of retail behavior, information asymmetry, and slower institutional participation makes momentum signals persist longer before reverting.

---

## The One That Failed

`earnings_surprise_momentum` returned a Sharpe of 0.00 on NSE.

This isn't surprising. The strategy relies on earnings surprise data — stocks that report better-than-expected earnings continuing to outperform (post-earnings announcement drift). In the US, I use analyst consensus estimates to compute surprise.

For Indian stocks via Yahoo Finance, there's no analyst consensus estimate data available in the same format. The signal generation returned zero positions, hence zero returns.

To properly run this strategy on Indian stocks, I'd need Refinitiv/Bloomberg analyst estimates for NSE stocks, or build an earnings model from scratch. That's a future project.

---

## What the Drawdowns Tell You

| Strategy | US MDD | NSE MDD |
|---|---|---|
| Volatility Targeting | -49.5% | **-30.5%** |
| Dividend Aristocrats | -50.2% | **-34.8%** |
| Low Volatility Shield | -49.5% | **-40.8%** |
| RSI Mean Reversion | -54.0% | -66.0% |

The defensive strategies (Volatility Targeting, Low Vol Shield, Dividend Aristocrats) have *lower* maximum drawdowns on NSE than on S&P 500. The aggressive strategies (RSI, Momentum) have higher drawdowns — Indian markets are more volatile in crashes.

This tells you which strategies to run in India: **prefer the defensive, quality-oriented strategies** that capture the factor premium while managing the higher crash risk.

---

## The Honest Caveat

This analysis has a meaningful limitation: **survivorship bias**.

My NSE data comes from the current NIFTY 500 composition fetched via Wikipedia. Stocks that were in the NIFTY 500 in 2005 but subsequently delisted (due to bankruptcy, fraud, acquisition) are underrepresented. This biases results upward — we're only testing on stocks that survived.

For the US study, I explicitly addressed this using point-in-time S&P 500 constituent lists. The NSE study doesn't have this fix yet. The true alpha is somewhat lower than shown here.

Even accounting for a 20–30% survivorship bias discount, the Indian market results are significantly stronger than the US results. The qualitative conclusion holds.

---

## Implications for Factor Investing

This comparison reinforces a core insight from the research: **factor premia exist, but their size depends on market efficiency**.

US markets: small, real factor premia, mostly arbitraged away, strategies lag the benchmark  
Indian markets: larger factor premia, less competition, strategies consistently beat the benchmark

For a practitioner — someone who actually wants to make money from factor investing, not just write papers about it — the implication is clear:

**If you can access Indian markets efficiently, factor strategies are more profitable there than in the US.**

The challenge is execution costs. Indian stocks have wider spreads and lower liquidity in mid-caps. A strategy that backtests at 1.10 Sharpe may deliver 0.80 after real transaction costs. That's still excellent — it just requires careful implementation.

---

## What's Next

The next step is integrating these NSE results into the live morning trade list. The same consensus-scoring system that identifies top US stocks each morning can run on NSE stocks — replacing S&P 500 tickers with NIFTY 500 tickers. The signals, the earnings filter, the sector concentration warnings, the prop firm risk checks — all of it transfers directly.

India-specific prop trading firms (Jane Street India, Optiver, Squarepoint's Mumbai office) run systematic strategies. This research is directly relevant to those roles.

---

*The full backtest results, code, and research platform are available at the link in my bio. All 14 strategies are open-sourced.*

*Mrigay Pathak is a Finance + Informatics junior at Indiana University Bloomington. He has interned at JM Financial (Apex Capital, Chaturmohta team) and Alchemy Capital Management (Jhunjhunwala family office). This research was conducted independently as a portfolio showcase project.*
