# Count Groups, Not Stocks: Business-Group Contagion and Hidden Concentration in India

*Mrigay Pathak, Indiana University. Research summary, 12 Nov 2026. Pilot results; the full
pre-registered portfolio test is not yet run.*

**The question.** Indian investors think in stocks. But many listed companies share a
promoter group: the same family, holding company or parent. Does sharing an owner create
crash risk that ordinary, correlation-based risk tools miss?

**Why it matters.** Diversification is measured by how many *independent* things can go
wrong. If companies with the same owner fall together when one of them cracks, then
counting tickers overstates diversification. And standard risk models, which estimate
co-movement from calm-period prices, would not see it coming.

**1. Contagion beyond correlation (pre-registered pilot).**
- **Setup:** 113 crash events in 49 Indian business groups, 2006–2025. Groups were mapped
  for 1,700 NSE stocks and checked against shareholding filings. The rules and the map
  were committed publicly before any return was computed.
- **Comparison:** each "sibling", a same-group company in an *unrelated* industry, is
  compared with unrelated stocks that normally move *just as closely* with the crashing
  firm.

| What happens to… | Extra loss over the next month | *t* |
|---|---|---|
| Same-group siblings in other industries | **−4.7 pp** | −2.66 (permutation *p* < 0.001) |
| Industry rivals in other groups | −0.4 pp | −0.38 |
| Siblings on the crash day itself | −2.2 pp | −3.39 |

Sharing an owner predicts losses that sharing an industry does not, beyond what calm-period
correlation shows.

**Honest limits:**
- The month-long effect is concentrated in stressed, leveraged groups (Adani, Anil Ambani,
  Indiabulls). Strong groups such as Tata show none.
- Without the most famous episodes, the month-long effect is not significant
  (*t* −1.71). The crash-day effect survives every check.

**2. How concentrated is the market by owner? (descriptive)**
- India's 500 largest listed companies (about 90% of market value) behave like **231**
  equal-sized companies by market cap, but only **156 independent owner groups**.
- Counting the Government of India as one owner, the figure is **82**.
- For the top 100: 73 companies, 51 owner groups, or 30 with the state as one owner.
- **But active funds mostly avoid it.** Across 25 equity funds from 7 fund houses
  (Oct 2026), the median fund holds only about 10% fewer owner groups than stocks. Owner
  concentration sits in the cap-weighted market and in specific fund positions, not in
  the typical active portfolio.

**What it could mean:**
- **For investors and index-tracking products:** report exposure by promoter group, and
  watch groups under financial stress.
- **For research:** this is an ownership-based diversification measure ("effective number
  of owner groups"), set against covariance-based measures, in a market where business
  groups are pervasive.

**Next (pre-registered, not yet run):**
- **Portfolio test:** do portfolios concentrated in fewer owner groups lose more in six
  Indian crises, with stock count, industry mix and correlation-based diversification
  all held equal?
- **Moderator:** promoter share pledges as a "fragile group" signal.

**Code, data and pre-registrations:** `docs/group_dependency/` and
`results/group_dependency/` in the StrategyHub research repository. Companion paper:
*Market Share Is Not Importance* (`docs/entropy_research/PAPER_SHORT.md`).
