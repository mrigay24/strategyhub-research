# Shared Owners, Shared Crashes? Business Groups and Portfolio Risk in India

*Mrigay Pathak, Indiana University. Research summary, 12 Nov 2026.*
- Two pre-registered tests: the rules were committed before any result was computed.
- Draft: `PAPER2_DRAFT.md` (retitled from *Count Groups, Not Stocks* to match the
  results below).

**The question.** Indian investors think in stocks. But many listed companies share a
promoter group: the same family, holding company or parent. Does sharing an owner create
crash risk that ordinary, correlation-based risk tools miss? And does it matter for
diversified portfolios?

**1. Stocks: owner-level crash co-movement beyond correlation (pre-registered).**
- **Setup:** 113 crash events in 49 Indian business groups, 2006–2025. Groups were mapped
  for about 1,700 NSE stocks and checked against shareholding filings.
- **Comparison:** each "sibling", a same-group company in an *unrelated* industry, is
  compared with unrelated stocks that normally move *just as closely* with the crashing
  firm.

| What happens to… | Extra loss over the next month | Evidence |
|---|---|---|
| Same-group siblings in other industries | **−4.7 pp** | *t* −2.66; bootstrap by group *p* = 0.03–0.04 |
| Industry rivals in other groups | −0.4 pp | *t* −0.38 |

Sharing an owner predicts losses that sharing an industry does not, beyond calm-period
correlation.

**Honest limits:**
- It is concentrated in a few financially stressed groups. Strong groups such as Tata
  show none. Without the best-known episodes it is weak (*t* −1.71).
- The crash-day part does not survive group-level inference. Much of it is news that hits
  the whole group at once.
- Prices can't separate one firm's fall *causing* the others' from news *revealing* a
  group-wide problem.

**2. How concentrated is the market by owner? (descriptive)**
- India's 500 largest listed companies (about 90% of market value) behave like **231**
  equal-sized companies by market cap, but only **156 independent owner groups**.
- Counting the Government of India as one owner, the figure is **82**.
- **Active funds mostly avoid it:** across 25 equity funds (Oct 2026), the median fund
  holds only about 10% fewer owner groups than stocks.

**3. Portfolios: does owner concentration deepen crisis losses? (pre-registered) No.**
- **Design:** 6,000 matched portfolio pairs (30 or 60 stocks) across six Indian crises,
  2008–2025. A "concentrated" twin and a "dispersed" twin have the same industries, the
  same share of group stocks, the same volatility and the same correlation-based
  diversification. They differ only in how many owners they spread across: 31 vs 43
  effective groups.
- **Result:** the concentrated twin lost only **0.3 pp more** at its worst point
  (placebo *p* = 0.125). It did slightly worse in 2008–09 and COVID, but within chance.
  In 60,000 random portfolios, owner-based effective N added nothing beyond volatility.

**What it means:**
- **For stocks and single-group positions:** shared ownership is a real crash channel,
  especially in stressed groups, and correlation-based tools understate it.
- **For diversified portfolios:** at realistic levels, owner concentration does not add
  measurable crisis risk. "Count groups, not stocks" is *not* a general portfolio rule.
- **For index investors:** the cap-weighted market is concentrated by owner. Whether that
  matters in an owner-specific crisis is untested, since Hindenburg 2023 was too mild a
  market fall to tell.

**Code, data and pre-registrations:** `docs/group_dependency/` and
`results/group_dependency/` in the StrategyHub research repository. Companion paper:
*Market Share Is Not Importance* (`docs/entropy_research/PAPER_SHORT.md`).
