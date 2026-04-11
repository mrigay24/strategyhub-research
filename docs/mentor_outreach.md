# Mentor Outreach — Research Platform Update

*Use this as a template for reaching out to former internship mentors at JM Financial (Apex Capital) and Alchemy. Personalize the opening based on your relationship with each person.*

---

## Template A — For Equity Research Analysts (JM Financial / Apex Capital)

**Subject:** Systematic factor research platform — wanted to share what I've been building

---

Hi [Name],

Hope you're doing well. I've been thinking about the work we did together at Apex on [mention specific project/sector you worked on] — it gave me a much clearer sense of how rigorous fundamental research actually gets done, and I've been trying to apply that same standard to the quantitative side.

I spent the last few months building a systematic trading research platform from scratch — backtesting 14 academic factor strategies (momentum, value, quality, low volatility, mean reversion, and composites) against 25 years of S&P 500 data. The most honest result: **none of them beat the benchmark on a risk-adjusted basis.** Sharpe ratios ranged from 0.53 to 0.66 vs the index at 0.69.

What I found interesting from a research perspective:
- The two strategies with genuine alpha (+1.7%/yr and +2.6%/yr after CAPM regression) both have documented behavioral explanations — the low-vol anomaly and post-earnings announcement drift
- Every long-only strategy fails in bear markets — the diversification people claim from combining factors essentially disappears (avg pairwise correlation 0.95 in bear regimes)
- Most "outperforming" backtests in the literature are implicitly running on 2014–2018 data, which was a nearly uninterrupted bull market

The platform is built in Python (FastAPI backend, React frontend) with a full statistical validation pipeline — walk-forward, Monte Carlo significance, parameter sensitivity, CAPM attribution. I also built an AI strategy generator that takes a plain-English description, generates the factor code, and runs a live 25-year backtest.

I'd love to get your perspective on it — especially whether you think the methodology is sound, and whether there are aspects of the fundamental research process at Apex that a quantitative model could realistically capture. I'm also thinking about extending this to Indian markets (NSE 500) over the summer and would value your thoughts on whether that angle has any practical interest for firms like yours.

Would you have 20–30 minutes sometime in the next few weeks for a call?

Best,
Mrigay

[Platform link]
[GitHub link]
[LinkedIn]

---

## Template B — For Alchemy (more senior relationship, slightly more formal)

**Subject:** Building on the research foundation — wanted to share a project

---

Hi [Name],

I hope you're well. My time at Alchemy was genuinely formative — the way [mention something specific: how they approached stock selection, position sizing, risk management] shaped how I think about markets. I've been trying to bring that same analytical rigor to a quantitative project I've been working on at university.

Over the past several months, I built a systematic factor research platform that backtests 14 academic trading strategies across 25 years of S&P 500 data (2000–2024), with a full 8-layer statistical validation pipeline. The central finding is uncomfortable but honest: in a properly controlled study — with realistic transaction costs, point-in-time data, and statistical significance testing — no factor strategy consistently beats a simple buy-and-hold S&P 500 index fund.

This mirrors something I observed during my time at Alchemy: the edge in investing isn't in the signals most people use, it's in the depth of fundamental work and the conviction to act when others don't. The quantitative world is arriving at the same conclusion by a different route.

The platform includes:
- 14 strategies across momentum, value, quality, low-vol, and composite factors
- Walk-forward, Monte Carlo, and CAPM attribution analysis
- An AI-powered strategy builder (Claude Opus 4.6) that generates and backtests custom factor code in 60 seconds
- Full frontend dashboard with interactive strategy comparison

I'm spending this summer in India and thinking seriously about extending this to Indian markets. The NSE 500 universe would be particularly interesting for the low-volatility and quality anomalies, which tend to be larger in markets with stronger institutional constraints.

I'd value your perspective on whether there's genuine research merit in this direction, and whether the systematic approach might complement fundamental research at firms like Alchemy. Would love to reconnect if you have time.

Best regards,
Mrigay Pathak

[Platform link]
[GitHub link]
[LinkedIn]

---

## What to Customize

**Before sending either template:**

1. **Opening reference** — mention something specific from your internship (a sector you covered, a company you researched, a method you learned). Generic openers get ignored.

2. **The ask** — be specific. "20–30 minutes for a call" is better than "would love to catch up." You're not just updating them, you're asking for feedback and signaling continued interest in the industry.

3. **Indian market extension** — this is your genuine differentiator for this summer. If they're still at the firm, they may have actual interest in systematic approaches to Indian equities. NSE data is more accessible than US data (Zerodha Kite API is free, Quandl NSE data is available).

4. **LinkedIn connection** — if not already connected, connect before emailing. It makes the outreach warmer.

---

## Talking Points If They Respond

**If they ask what tools you used:**
Python (pandas, NumPy, FastAPI), React/Next.js frontend, SQLite database, yfinance for historical data, Anthropic Claude API for the AI builder. The backtester is custom-built (not QuantLib or backtrader) — this matters because you understand every line of it.

**If they ask about your findings:**
Lead with the honest negative result — it signals intellectual integrity. Then pivot to the two strategies with genuine alpha and the economic explanations behind them. The CAPM attribution work (beta/alpha decomposition) is the most technically impressive part to a research-oriented audience.

**If they ask about career direction:**
You're targeting quant research roles (systematic portfolio management, factor investing research). The Indian market extension over the summer is both intellectually interesting and strategically timed — you can show them something new when you're back in India. You're also exploring prop trading (funded account programs) as a parallel track to build a live track record.

**If they ask about the AI builder:**
The key point: it doesn't just classify strategies, it generates the actual factor code and runs a real backtest. The AI is a research assistant, not a black box — every decision it makes is explained, the validation is rigorous, and negative results are surfaced explicitly. This is the opposite of most AI investment tools.

---

## Follow-Up Timeline

- Send initial outreach: Day 1
- If no response after 10 days: one brief follow-up ("Just checking in — happy to share the platform link if easier")
- After reconnecting: offer to show the live platform on a screen share — it lands much better as a demo than a GitHub link

---

*Last updated: April 2026*
