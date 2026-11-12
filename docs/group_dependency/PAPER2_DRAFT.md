# Count Groups, Not Stocks: Business-Group Contagion and Hidden Concentration in India

**Mrigay Pathak** · Indiana University Bloomington · Working paper draft, November 2026

*Pre-registration: `docs/group_dependency/PREREGISTRATION.md` (pilot) and
`PREREGISTRATION_2_DRAFT.md` (portfolio test, design). Results: `results/group_dependency/`
and `results/group_concentration/`. Every headline number traces to a file listed in
Appendix C. This paper uses share prices and public filings only and makes no claim about
any firm's conduct.*

---

## Abstract

Investors count diversification in stocks, and risk models measure it from past
co-movement. In India, many listed firms share a controlling promoter group. We ask
whether that shared owner adds crash risk that calm-period correlation does not show. In a
pre-registered event study of 113 one-day crashes of group firms (2006–2025), using a
promoter-group map checked against NSE shareholding filings, siblings in unrelated
industries lost 4.7 percentage points more over the next month than unrelated stocks that
were just as correlated with the crashing firm (*t* = −2.66; placebo *p* < 0.001). Industry
rivals lost 0.4 points (*t* = −0.38). On the crash day the sibling effect is −2.2 points
and survives every check. The month-long effect is concentrated: ten of 72 events carry
almost all of it, and without the best-known episodes it is −1.9 points (*t* = −1.71). By
market capitalisation, India's top 500 companies behave like 231 equal-sized stocks but only
156 owner groups (82 with the state as one owner). Active funds hold only about 10% fewer
owner groups than stocks.

---

## 1. Introduction

A portfolio manager who holds 50 Indian stocks thinks she holds 50 bets. A risk model that
estimates a covariance matrix from the past year agrees, give or take the correlations it
sees. Neither asks who owns the companies. In India, a large share of listed market value
sits in business groups: families or holding companies that control several listed firms
across unrelated industries. If those firms fall together when one of them cracks, then
counting tickers overstates diversification. Correlation-based tools would also miss it,
because siblings in unrelated industries need not move together on ordinary days.

This is a practical problem for three kinds of decision-makers.
- **Investors and index providers** must decide how many independent exposures a
  portfolio or an index really contains.
- **Fund boards and regulators** must decide whether to report and limit exposure by
  issuer only, or also by promoter group.
- **Risk managers** must decide whether a covariance estimate from calm markets is enough
  to size a crash.

The question this paper answers is narrow: **after a business-group firm's own crash, do
its group siblings in other industries fall more than unrelated stocks with the same
calm-period correlation, and more than the crashing firm's industry rivals?** And how much
does counting owners instead of stocks change the measured diversification of the Indian
market and of real funds?

**The answer, in three parts.**

1. **Contagion beyond correlation exists, and is concentrated.** In a pre-registered test,
   siblings in unrelated industries lose about 2.2 points more than their calm correlation
   predicts on the crash day, and 4.5–4.7 points over the next month. Industry rivals lose
   almost nothing extra. The crash-day effect survives every check. The month-long effect
   comes mainly from a handful of episodes in groups under visible financial or market
   stress. Without the best-known of them, it is no longer significant. Tata's siblings,
   for example, show nothing.
2. **The cap-weighted market is concentrated by owner.** The top 500 companies have an
   effective number of 231 stocks but 156 owner groups. Treating state-owned firms as one
   owner gives 82.
3. **Active funds mostly avoid it.** Across 25 equity funds, the median fund holds only
   10% fewer effective owner groups than effective stocks. The concentration sits in the
   cap-weighted market that index funds buy, and in specific large positions.

### Contribution

The pieces of this argument exist separately. What this paper adds:

- **An event-level test against industry rivals, controlling for each pair's calm
  correlation** (versus Kwon, Jung, Sunwoo and Yim 2019). Kwon et al. show that crash risk
  spreads among Korean chaebol members, using firm-year crash measures. We work at the
  event level in India and compare siblings in *other* industries with the crashing
  firm's *industry rivals*. We control directly for how correlated each pair already was.
  That directly tests whether a correlation-based risk model already sees the risk.
- **The crash-time price consequence of known group links** (versus Khanna and Thomas
  2009, and Gopalan, Nanda and Seru 2007). Khanna and Thomas show that shared owners raise
  stock synchronicity on average days in Chile. Gopalan et al. show that Indian groups
  support weak members with intragroup loans, and that the first bankruptcy in a group is
  followed by lower financing, investment and profits at the other members. We show what
  the link does to siblings' prices when one member crashes, beyond calm co-movement, and
  that it is concentrated in stressed groups.
- **An ownership-based diversification measure** (versus Meucci 2009, and Greenwood and
  Thesmar 2011). Meucci's effective number of bets is built from the covariance matrix,
  so it sees only what past prices show. Greenwood and Thesmar show that concentrated or
  correlated *investors* make prices fragile. We build an effective number of *owner
  groups* from holdings and a filing-checked promoter map. We measure it for the Indian
  market and for 25 funds. As far as we found, no paper builds diversification measures
  on promoter-group ownership.

What the paper does not add: that group firms are linked (Gopalan et al.), that they
co-move (Kim, Kim and Lee 2015), or that crash risk spreads inside groups (Kwon et al.).
The novelty is the combination: the event design, the correlation control, the
pre-registration and the ownership-based measure.

---

## 2. Framework

**Effective N.** For portfolio weights *w* over *n* items, the entropy is
H = −Σ wᵢ ln wᵢ, and the effective number is N_eff = exp(H). A portfolio of 50 equal
weights has N_eff = 50. A portfolio dominated by a few names has N_eff far below its count.
We compute N_eff over three units:
- **stocks:** the usual reading;
- **owner groups:** weights summed within each promoter group;
- for comparison, **industries.**

The ratio N_eff(stocks) / N_eff(groups) says how much counting tickers overstates the
number of independent owners. A ratio of 1 means every stock has its own owner.

**Who counts as one owner?** Three definitions, fixed before any result:
- **G1 (primary):** Family and Corporate groups are groups. Everything else (multinational
  subsidiaries, state-owned firms, professionally managed and private-equity-controlled
  firms, unmatched names) is standalone.
- **G2:** G1, plus all state-owned firms as one owner (the Government of India).
- **G3:** G1, plus multinational subsidiaries grouped by parent.

**Why owners might matter beyond correlation.** Siblings can fall together after one
member's crash for three reasons.
- **Shared finance:** intragroup loans and guarantees, and shared lenders.
- **Shared promoter wealth:** pledged promoter shares can trigger forced sales across the
  group.
- **Shared information:** news about the promoter is news about every member.

On calm days, siblings in unrelated industries need not co-move much, so a covariance
matrix estimated in calm markets understates their joint crash risk. Prices cannot tell
these channels apart. The question here is only whether the shared owner predicts
siblings' losses beyond what calm correlation shows.

---

## 3. Data

**Prices.** We use a survivorship-free NSE panel: 1,620 symbols, January 2005 – June 2025,
with splits and bonuses corrected and delisted firms included. The universe is every
symbol that was in the top 500 by 63-day traded value at any month-end (1,609 symbols). It
was built from traded value alone, before any return was computed.

**The promoter-group map, v1.** Each symbol is labelled with its controlling promoter
group (with dates for changes of control), a group type and one of 41 industries. An AI
labeller built it from NSE's symbol lists, its own knowledge and some web searches, and
spot checks fixed 14 errors. It has 1,695 rows, and 110 Family/Corporate groups have two
or more listed companies (379 companies).

**The verified map, v2.** Because v1 rested on an AI's memory, it was checked against
filings before the paper:
- NSE shareholding-pattern filings (XBRL, 2020/21 onward; 11,106 filings) were parsed for
  750 priority symbols: every firm in a sibling event, every member of a multi-company
  group and every low-confidence row. Each firm was checked for a shared promoter entity
  with its group.
- The 135 firms in the sibling events were checked at their event dates against news,
  annual reports and group lists. Every flagged row was reviewed, and the decision was
  recorded with its source.
- **21 symbols (26 rows) changed.** For example, Great Offshore had been wrongly merged
  with Bharati Shipyard's group before Bharati took control. Some control dates and group
  assignments were corrected, and missed members were added.
- **Limits:** 230 symbols have no 2020+ filing and no confirming document, and 858, mostly
  standalone firms, were not checked. Low-confidence rows fell from 209 to 117.

Appendix B has the details. A name check found no duplicate group names; family branches
(Bajaj, Jindal, TVS, the two Ambani groups) are kept as separate owners.

**Market capitalisation.** AMFI publishes half-yearly average market caps for every listed
company: 18 half-years from December 2017 to June 2026, each with 4,792–5,427 companies.
The top 500 hold about 90% of total market cap. The map matches between 93% and over 99% of
top-500 market cap, depending on the half-year.

**Fund holdings.** The official monthly portfolio files of 7 asset managers, as of 31
October 2026: 25 equity funds across small-, mid-, large-, flexi- and multi-cap and value
categories. The equity holdings are mapped from ISIN to NSE symbol to group. HDFC, Kotak,
ICICI Prudential, Franklin and Quant could not be downloaded and are not covered.

---

## 4. How concentrated is the market by owner?

![Figure 1. Effective number of stocks vs owner groups, top 500](../../results/group_dependency/figures/fig_effn_market.png)

*Figure 1. Effective number of stocks and of owner groups (G1, G2) among India's top 500
companies by AMFI average market cap, December 2017 – June 2026, verified map.*

**Table 1. Effective N by stocks and by owner groups, top 500 and top 100**

| | Dec 2017 | Jun 2026 |
|---|---|---|
| Top 500: effective N of stocks | 191.9 | 230.7 |
| Top 500: effective N of owner groups (G1) | 134.1 | 155.6 |
| Top 500: owner groups, state as one owner (G2) | 70.7 | 82.3 |
| Top 500: stocks / groups (G1) | 1.43 | 1.48 |
| Top 100: stocks / G1 / G2 | 70.8 / 52.2 / 29.6 | 73.4 / 50.6 / 30.5 |

*Source: `results/group_concentration/v2/headline_by_period.csv`. G3 (multinationals by
parent) is within 1.5 of G1 in every period.*

**The market.** By market cap, India's 500 largest companies behave like 231 equal-sized
stocks but only 156 independent owner groups. Treating the state as one owner gives 82. The
ratio of stocks to groups has stayed between 1.43 and 1.63 since 2017, peaking in December
2022. The largest owner groups by share of top-500 market cap are Tata (5.4%), Mukesh
Ambani's Reliance (4.9%), Adani (3.7%), HDFC (3.7%), Bajaj (3.2%) and Bharti (3.1%). A
cap-weighted index investor therefore holds about a third fewer independent owners than
independent stocks.

**Funds: an honest negative.** We expected funds to show the same gap. They mostly do not.

**Table 2. Owner concentration in 25 equity funds, October 2026**

| | Median | Range |
|---|---|---|
| Effective N of stocks | 51.2 | 22.3 – 189.3 |
| Effective N of owner groups (G1) | 47.2 | 20.9 – 171.7 |
| Ratio stocks / groups (G1) | **1.10** | 1.00 – 1.24 |
| Equity weight matched to the map | 90.2% | |

*Source: `results/group_concentration/fund_level_latest_v2map.csv`; all 25 funds are in
Appendix D.*

The median fund holds only about 10% fewer effective owner groups than effective stocks.
Large-cap funds have the highest ratios (1.11–1.23), and their largest group exposures are
financial groups with several listed companies, such as HDFC and ICICI. Small-cap funds
are close to 1 (1.00–1.10). Active managers
already spread across owners. The owner concentration sits in the cap-weighted market,
which index funds buy, and in specific large positions. One example is the HDFC group's
9.8% of the Parag Parikh Flexi Cap Fund. The "your fund owns 50 stocks but far fewer
families" story does not hold for the typical active fund, and the paper does not make it.

---

## 5. The pre-registered crash test

### 5.1 Design

The rules (`PREREGISTRATION.md`) were committed before the event list was built, and the
event list before any comparison stock's return was computed. One run followed. The commit
sequence is in Appendix A.

- **Events (triggers).** A trigger is a firm of a Family/Corporate group that, on one day:
  - falls at least 15%;
  - falls at least 12 points more than the market and than its industry's non-group firms;
  - has at least one other group firm in the top-500 universe that day.

  Each group gets one event per 20-day episode, and windows run from 2006 to 2025.
- **Classes.** Every other top-500 stock that day is classed as:
  - **S:** a sibling in another industry (the key class);
  - **SI:** a sibling in the same industry;
  - **R:** an industry rival outside the group;
  - **B:** an unrelated stock (the baseline).
- **Outcome.** Each stock's buy-and-hold return over the 21 trading days from the crash
  day, minus the market's (BHAR 0–20).
- **Control.** Each stock's daily return correlation with the trigger over a calm year
  ending two weeks before the crash. If siblings fall only because they always move
  together, this control absorbs it.
- **Regression.** The outcome on S, SI and R dummies, the calm correlation, log size and
  log illiquidity, with one fixed effect per event and standard errors clustered by month.
- **Go / no-go rule (fixed in advance).** All three must hold:
  - β_S < 0 with *t* ≤ −1.96;
  - an event-level permutation *p* < 0.05;
  - β_S ≤ β_R.

  Fewer than 30 sibling events, or fewer than 10 groups, means "too few to test".

**Two versions.** The registered run used the v1 map. Before any return was computed on
v2, a deviation (D1) re-ran the identical code once on the verified map. **v1 remains the
registered result. v2 is reported alongside it** and is the version we lead with, because
its labels are checked against filings.

### 5.2 Sample

Under v2, 113 events come from 49 groups. 96 have usable comparison data, and 72 have a
sibling in another industry (29 groups), which clears the "too few" bar. There are 39,345
stock pairs: 37,703 unrelated, 1,374 rivals, 227 siblings in other industries and 41
siblings in the same industry.

**Table 3. Raw averages by class (v2, before any control)**

| Class | Calm correlation with the trigger | Crash-day abnormal return | 21-day BHAR, mean / median |
|---|---|---|---|
| B: unrelated | −0.01 | +0.07% | −0.07% / −0.68% |
| R: industry rivals | 0.06 | −0.31% | −0.94% / −1.42% |
| **S: siblings, other industry** | **0.15** | **−2.63%** | **−5.47% / −3.20%** |
| SI: siblings, same industry | 0.28 | −3.51% | −5.77% / −0.60% |

*Source: `results/group_dependency/v2/tests.json` (`class_means`).*

Siblings normally move *more* closely with the trigger than rivals do (0.15 against 0.06).
That is why the correlation control matters.

### 5.3 Results

**Table 4. The registered test: BHAR 0–20, event fixed effects, clustered by month**

| | **v2: verified map (D1)** | v1: registered map |
|---|---|---|
| Events / with a sibling in another industry / groups | 113 / 72 / 29 | 115 / 74 / 30 |
| **β_S: sibling, other industry** | **−4.70 pp (*t* −2.66)** | −4.49 pp (*t* −2.64) |
| β_SI: sibling, same industry | −3.63 pp (*t* −1.29) | −3.65 pp (*t* −1.29) |
| β_R: industry rival | −0.35 pp (*t* −0.38) | −0.40 pp (*t* −0.44) |
| Calm correlation (per unit) | −7.05 pp (*t* −2.81) | −6.93 pp (*t* −2.78) |
| β_S − β_R | −4.35 pp (*t* −2.26) | −4.09 pp (*t* −2.17) |
| Permutation by event (2,000 draws) | 0 as negative; *p* < 0.0005 | 0 as negative; *p* < 0.0005 |
| β_S without the correlation control | −5.80 pp (*t* −3.10) | −5.55 pp (*t* −3.12) |
| **Go / no-go** | **GO** | **GO** |

*Source: `results/group_dependency/v2/tests.json` and `tests.json` (`primary`, `R10_no_rho`).*

![Figure 2. Pilot coefficients](../../results/group_dependency/figures/fig_pilot_coefficients.png)

*Figure 2. Extra loss of siblings in other industries, siblings in the same industry and
industry rivals, relative to unrelated stocks with the same calm correlation: crash day
(left) and days 0–20 (right). Filled: verified map; hollow: original map. Bars are 95%
intervals.*

By the rule fixed in advance, the verdict is **GO** in both versions. A firm in an
unrelated industry that shares an owner with the crashing firm loses about 4.7 points more
over the next month than an unrelated stock that normally moves just as closely with the
crashing firm. Industry rivals lose almost nothing extra. The placebo distribution of β_S
from shuffled event assignments has a mean of 0.0, a standard deviation of 0.9 points and a
5th percentile of −1.4 points. The correlation control explains about 1 point of the
sibling effect, not most of it.

### 5.4 Robustness (registered list; none changes the verdict)

**Table 5. Registered robustness checks (β_S, BHAR 0–20 unless stated)**

| Check | v2 | v1 |
|---|---|---|
| R1: no 2008–09, no Feb–Apr 2020 | −5.01 pp (*t* −2.22) | −4.68 pp (*t* −2.13) |
| **R2: without the companion paper's episodes (7 events)** | **−1.85 pp (*t* −1.71)** | −1.87 pp (*t* −1.83) |
| R3: crash-day abnormal return | −2.16 pp (*t* −3.39) | −2.21 pp (*t* −3.51) |
| R3: CAR 0–20 | −5.51 pp (*t* −2.29) | −5.26 pp (*t* −2.25) |
| R5: clustered by trigger group | *t* −1.93 | *t* −1.97 |
| **R6: high-confidence labels only** | **−7.00 pp (*t* −2.53), 71 events** | −3.54 pp (*t* −1.67), 78 events |
| R7: news-checked, no artefacts | −10.33 pp (*t* −1.80), 24 events | −10.96 pp (*t* −2.01), 26 events |
| **R8: events weighted equally** | **mean −4.1, median −2.4 pp; 56% negative (sign *p* 0.205)** | −4.4 / −2.9 pp; 57% (0.148) |
| R9: correlation as ten decile dummies | −5.14 pp (*t* −2.90) | −4.92 pp (*t* −2.90) |

*Source: `tests.json` (`robustness`), both versions. R4 (wider group definitions) is
mis-specified, because triggers come only from Family/Corporate groups. It is identical to
the primary result and uninformative; this is disclosed, not re-run. Clustering by event or
by date gives t of −2.64 and −2.63 (v2).*

Three findings matter:
- **The crash-day effect is robust.** Siblings in unrelated industries fall about 2.2
  points more than their calm correlation predicts on the crash day, with *t* above 3 in
  both versions.
- **The labels were not what made v1 look fragile.** With high-confidence labels only, the
  v1 effect weakened to *t* −1.67. With the verified map, the same check *strengthens* it
  (−7.0 points, *t* −2.53).
- **The month-long effect depends on a few episodes.** Without the seven events that a companion paper had already studied (Pathak 2026) (Adani 2023, the Anil Ambani group in 2019, Indiabulls in
  2019), it falls to −1.9 points with *t* −1.71, below the 1.96 bar. Clustered by trigger
  group, *t* is −1.93. Weighting events equally, only 56% of events have a negative
  sibling residual.

### 5.5 Tails (H3; registered, no verdict)

Across 195,900 stock pairs with at least 750 overlapping days, we count how often both
stocks are in their worst 5% of days on the same day. We then subtract what a normal model
with their calm correlation predicts.

**Table 6. Excess joint-crash frequency (share of days, v2)**

| Pair type | Pairs | Excess joint-crash frequency |
|---|---|---|
| Unrelated | 188,656 | 0.155% |
| Same industry, different group | 6,872 | 0.207% |
| **Same group, different industry** | **329** | **0.218%** (placebo-group *p* < 0.001) |
| Same group and same industry | 43 | 0.277% |

*Source: `results/group_dependency/v2/tests.json` (`tail_dependence`).*

In the tails, sharing an owner adds about as much joint-crash risk as sharing an industry,
beyond what calm correlation shows.

### 5.6 What drives the month-long effect (NOT pre-registered diagnostics)

These diagnostics were computed after the registered run and are labelled as such
(`results/group_dependency/v2/diagnostics_not_preregistered.json`).
- **No single group drives it.** Dropping any one of the 29 groups leaves β_S between −3.3
  points (without Adani, *t* −2.29) and −7.1 points (without Tata, *t* −2.95). It is
  significant in all 29 cases.
- **A minority of events does.** The 10 worst of 72 events carry essentially all (99%) of
  the total sibling loss, and the 5 worst carry 60%. Without the worst 5, the mean event
  residual is −1.8 points. The worst events are:
  - Adani Enterprises after the January 2023 short-seller report;
  - Future Consumer (February 2020);
  - Indiabulls firms in 2009 and 2019–20;
  - IndusInd Bank (March 2020);
  - Reliance Petroleum (November 2007);
  - Ujjivan (2021);
  - Reliance Capital (February 2019).
- **Groups differ sharply.** The average sibling residual is −20.8 points for Indiabulls
  (7 events), −16.9 for Adani (6), −6.1 for the Anil Ambani group (10) and −0.3 for Tata
  (6 events, 77 sibling pairs). It is +1.0 for Aditya Birla (3 events).
- **The crash-day effect survives without the companion paper's episodes:** −1.3 points (*t* −2.40),
  with a sibling-minus-rival difference of *t* −2.01.

**Reading.** On the crash day, sharing an owner predicts a loss that calm correlation and
industry membership do not. Over the following month, the extra loss is large in groups
under visible financial or market stress at the time and absent in strong groups such as
Tata. "Count groups, not stocks" matters most when the group itself is fragile. The
pre-registered portfolio test (Section 6) is designed around that reading.

---

## 6. The portfolio test (pre-registered design)

> **PLACEHOLDER: Phase 5 results are not yet in this draft.** The design below follows
> `PREREGISTRATION_2_DRAFT.md`. The results will be filled in only from committed files in
> `results/group_dependency/phase5/` (with `NOTE.md` §9), exactly as reported there, nulls
> included.

**Question.** Do portfolios concentrated in fewer owner groups lose more in crises than
otherwise-identical portfolios?
- **H-P1:** they do, holding constant the number of stocks, industry weights and
  covariance-based diversification.
- **H-P2:** group-level effective N predicts crisis drawdowns beyond:
  - stock-level and industry-level effective N;
  - Meucci's effective number of bets;
  - trailing volatility.

**Main design: matched twins.** At each formation date (126 trading days before a crisis
window):
1. Draw a random equal-weighted base portfolio of 30 or 60 top-500 stocks.
2. Build its twin by swapping up to half of its stocks for same-industry stocks that belong
   to groups already in the portfolio. Each swap must keep the twin's Meucci effective
   number of bets and trailing volatility within ±5% of the base.
3. Keep pairs whose group effective N is at least 15% lower than the base's.

The twins then differ in owner concentration only. The outcome is the maximum drawdown
within six crisis windows, fixed in advance: the global financial crisis (2008–09), the
2013 taper tantrum, the 2018 IL&FS episode, COVID (2020), the January 2023 Adani episode
and the 2024–25 small-cap fall.

**Tests and decision rule.**
- **Inference** uses placebo group labels, shuffled 500 times with group sizes kept.
- **Support** requires a pooled placebo *p* < 0.05 and the right sign in at least 4 of the
  6 windows.
- **A pre-stated exclusion (T1-x)** drops the Adani window and the groups that drove the
  pilot (Adani, Anil Ambani, Indiabulls, Future). If the result holds only with them, the
  claim narrows to "owner concentration matters when a group is under stress".

**Results.** *[To be filled from `results/group_dependency/phase5/` once committed.]*

---

## 7. Implications

**For passive and index investors.** A cap-weighted Indian index has about a third fewer
independent owners than independent stocks. The pilot suggests that owner links matter
most in a crash, and most in stressed groups. Index users and providers could report
exposure by promoter group alongside sector exposure. Doing so needs only public
shareholding filings.

**For fund reporting.** Funds already report holdings by issuer and sector. Adding the top
promoter-group exposures would show positions like a single group at nearly 10% of a fund,
which issuer limits do not reveal. For most active funds the summary number would be
unremarkable (a ratio near 1.1), and that is itself useful information.

**For regulators and risk managers.** Covariance-based measures, including Meucci's
effective number of bets, see only what calm prices show. The evidence here is that a
shared owner predicts crash-day losses those measures miss. A group-level exposure
measure, or a stress scenario that shocks all members of a group together, is a simple
complement. This paper uses prices and public filings only. It makes no claim about why any
group's firms fell, or about any firm's conduct.

---

## 8. Limitations

- **The month-long effect is concentrated.** Ten of 72 events carry it. Without the companion paper's
  episodes it is not significant (*t* −1.71), and clustered by trigger group *t* is −1.93.
  It is a property of stressed groups, not a general law.
- **Transmission or revelation.** When news concerns a whole group, all its firms fall
  because the news is about all of them. The test shows that owner-level risk exists and
  that calm correlation misses it. It does not show that one firm's crash causes the
  others' falls.
- **The map.** It was checked against filings for 750 priority symbols. But 230 symbols are
  unverifiable and 858 were not checked, and most pre-2020 labels rest on group-company
  lists rather than dated filings. Family-branch boundaries are judgement calls.
- **R4 was mis-specified,** so nothing is learned about multinational, state or
  private-equity groups.
- **Event quality.** In a random news-checked sample of 28 events (v2), 14 had firm- or
  group-specific bad news, 2 were corporate-action artefacts, 7 coincided with market- or
  industry-wide news and 5 had no news found. Artefacts and market-wide days add noise,
  not bias toward finding an effect.
- **Day 0 is the crash day,** not the news day. Where the news came out earlier, earlier
  sibling losses are not counted, which understates the effect. For example, the Adani
  short-seller report came out on 24 January 2023, but the first −15% day was 27 January,
  so siblings' losses on 25 January are not counted.
- **Universe.** Only top-500 stocks are seen, so smaller siblings are missed.
- **Funds.** One month, 25 funds, 7 managers; several large managers could not be
  downloaded. Unmatched weight counts as standalone, which biases the ratio toward 1.
- **Not out of sample in time.** The portfolio test reuses the same years. A clean check
  needs another market with business groups (Korea) or post-2025 data.

---

## 9. Conclusion

Counting stocks overstates how many independent owners an Indian investor holds. By market
cap, the top 500 companies behave like 231 stocks but 156 owner groups. In a pre-registered
event study, siblings in unrelated industries fall about 2 points more than their calm
correlation predicts on the day a group firm crashes. That is a risk that correlation-based
tools miss and industry membership does not explain. Over the following month the extra
loss is about 4.7 points on average, but it comes from a few episodes in stressed groups
and is not significant without the best-known ones. Most active funds already spread across
owners. The concentration sits in the cap-weighted market. The portfolio test, whose
design is fixed in advance, will say whether counting groups helps predict crisis losses
once stock count, industry mix and covariance-based diversification are held equal.

---

## Appendix A. Pre-registration and commit record

| Commit | What it fixed |
|---|---|
| 3e6155f | Literature check and universe (traded value only) |
| 5d74939 | The group map (v1) |
| 133c5c9 | Rules and go/no-go test (pre-registration Part 1) |
| be33f0c | Event list and news labels, before any comparison stock's return (Part 2) |
| 8b08f04 | The single registered run, plus diagnostics labelled as not pre-registered |
| D1 (12 Nov 2026) | Verified map v2 committed before any return was computed on it; identical re-run |

Rules: `docs/group_dependency/PREREGISTRATION.md` (§1 hypotheses, §6 primary test, §8
robustness, §10 deviation D1). Portfolio test design: `PREREGISTRATION_2_DRAFT.md`.

## Appendix B. Map verification (v1 → v2)

- **Checked:** 750 priority symbols against NSE shareholding-pattern XBRL filings (2020/21
  onward). The 135 sibling-event firms were checked at their event dates against news,
  annual reports and group lists. There were 95 reviewed decisions.
- **Changed (21 symbols, 26 rows), for example:**
  - Great Offshore separated from Bharati Shipyard before 2009–10.
  - Corrected control dates: Avaya GlobalConnect left Tata in 2004; UB kept Mangalore
    Chemicals to end-2014; the Indiabulls promoter was declassified at Sammaan Capital in
    2023; Orient Cement, Reliance Naval and Religare changed control in 2024–25.
  - Corrected groups: Maharashtra Seamless and Jindal Drilling are DP Jindal; Mangalam
    Cement is BK Birla.
  - Missed members added: Yaari Digital (Indiabulls), Sonata Software (Rajan Raheja).
- **Confidence:** high-confidence rows rose from 1,017 to 1,149, and low-confidence rows
  fell from 209 to 117.
- **Not verified:** 230 symbols have no filing or confirming document, and 858 were not
  checked.
- **Files:** `results/group_dependency/group_map_v2.csv`, `group_map_v2_changes.csv`,
  `verify/`.

## Appendix C. Traceability

Run `~/.venvs/strategyhub/bin/python scripts/group_dependency_paper_check.py` to recompute
every number below from its file and check that it appears in the text.

| Headline number | Value | Source |
|---|---|---|
| Top 500 effN stocks, Dec 2017 / Jun 2026 | 191.9 / 230.7 | `results/group_concentration/v2/headline_by_period.csv` |
| Top 500 effN groups G1 | 134.1 / 155.6 | `results/group_concentration/v2/headline_by_period.csv` |
| Top 500 effN groups G2 | 70.7 / 82.3 | `results/group_concentration/v2/headline_by_period.csv` |
| Top 500 ratio stocks/G1 | 1.43 / 1.48 | `results/group_concentration/v2/headline_by_period.csv` |
| Top 500 ratio, min and max over periods | 1.43 / 1.63 | `results/group_concentration/v2/headline_by_period.csv` |
| Top 100 stocks / G1 / G2, Jun 2026 | 73.4 / 50.6 / 30.5 | `results/group_concentration/v2/headline_by_period.csv` |
| Headline rounded: 231 / 156 / 82 | 231 / 156 / 82 | `results/group_concentration/v2/headline_by_period.csv` |
| Group shares of top-500 cap: Tata / Reliance / Adani | 5.4% / 4.9% / 3.7% | `results/group_concentration/v2/top_groups_latest.csv` |
| Funds: count / median ratio | 25 funds / 1.10 | `results/group_concentration/fund_level_latest_v2map.csv` |
| Funds: median effN stocks / G1 | 51.2 / 47.2 | `results/group_concentration/fund_level_latest_v2map.csv` |
| Funds: ratio range | 1.00 / 1.24 | `results/group_concentration/fund_level_latest_v2map.csv` |
| Funds: median matched weight | 90.2% | `results/group_concentration/fund_level_latest_v2map.csv` |
| v2 events / groups | 113 / 49 | `results/group_dependency/v2/events_summary.json` |
| v2 events with S / groups with S | 72 / 29 | `results/group_dependency/v2/tests.json` |
| v2 pairs | 39,345 | `results/group_dependency/v2/tests.json` |
| v2 class means S: rho / day-0 AR / BHAR mean / median | 0.15 / −2.63% / −5.47% / −3.20% | `results/group_dependency/v2/tests.json` |
| v2 beta_S / t | −4.70 pp / −2.66 | `results/group_dependency/v2/tests.json` |
| v2 beta_R / t | −0.35 pp / −0.38 | `results/group_dependency/v2/tests.json` |
| v2 beta_SI / t | −3.63 pp / −1.29 | `results/group_dependency/v2/tests.json` |
| v2 beta_S - beta_R / t | −4.35 pp / −2.26 | `results/group_dependency/v2/tests.json` |
| v2 beta_S without rho / t | −5.80 pp / −3.10 | `results/group_dependency/v2/tests.json` |
| v2 permutation draws as negative | 0 as negative | `results/group_dependency/v2/tests.json` |
| v2 R1_no_crises: beta_S / t | −5.01 pp / −2.22 | `results/group_dependency/v2/tests.json` |
| v2 R2_no_paper1_episodes: beta_S / t | −1.85 pp / −1.71 | `results/group_dependency/v2/tests.json` |
| v2 R3_day0_AR: beta_S / t | −2.16 pp / −3.39 | `results/group_dependency/v2/tests.json` |
| v2 R3_car_0_20: beta_S / t | −5.51 pp / −2.29 | `results/group_dependency/v2/tests.json` |
| v2 R6_high_confidence: beta_S / t | −7.00 pp / −2.53 | `results/group_dependency/v2/tests.json` |
| v2 R7_news_checked_clean: beta_S / t | −10.33 pp / −1.80 | `results/group_dependency/v2/tests.json` |
| v2 R9_rho_deciles: beta_S / t | −5.14 pp / −2.90 | `results/group_dependency/v2/tests.json` |
| v2 R8: share negative / sign p | 56% / 0.205 | `results/group_dependency/v2/tests.json` |
| v2 R5: t clustered by trigger group | −1.93 | `results/group_dependency/v2/tests.json` |
| v1 beta_S / t | −4.49 pp / −2.64 | `results/group_dependency/tests.json` |
| v1 beta_R / t | −0.40 pp / −0.44 | `results/group_dependency/tests.json` |
| v1 beta_SI / t | −3.65 pp / −1.29 | `results/group_dependency/tests.json` |
| v1 beta_S - beta_R / t | −4.09 pp / −2.17 | `results/group_dependency/tests.json` |
| v1 beta_S without rho / t | −5.55 pp / −3.12 | `results/group_dependency/tests.json` |
| v1 permutation draws as negative | 0 as negative | `results/group_dependency/tests.json` |
| v1 R1_no_crises: beta_S / t | −4.68 pp / −2.13 | `results/group_dependency/tests.json` |
| v1 R2_no_paper1_episodes: beta_S / t | −1.87 pp / −1.83 | `results/group_dependency/tests.json` |
| v1 R3_day0_AR: beta_S / t | −2.21 pp / −3.51 | `results/group_dependency/tests.json` |
| v1 R3_car_0_20: beta_S / t | −5.26 pp / −2.25 | `results/group_dependency/tests.json` |
| v1 R6_high_confidence: beta_S / t | −3.54 pp / −1.67 | `results/group_dependency/tests.json` |
| v1 R7_news_checked_clean: beta_S / t | −10.96 pp / −2.01 | `results/group_dependency/tests.json` |
| v1 R9_rho_deciles: beta_S / t | −4.92 pp / −2.90 | `results/group_dependency/tests.json` |
| v1 R8: share negative / sign p | 57% / 0.148 | `results/group_dependency/tests.json` |
| v1 R5: t clustered by trigger group | −1.97 | `results/group_dependency/tests.json` |
| Tail pairs (v2) | 195,900 | `results/group_dependency/v2/tests.json` |
| Tail excess: unrelated / same industry / same group / both | 0.155% / 0.207% / 0.218% / 0.277% | `results/group_dependency/v2/tests.json` |
| Leave-one-group-out: without Adani / without Tata | −3.3 / −7.1 | `results/group_dependency/v2/diagnostics_not_preregistered.json` |
| Worst 10 / worst 5 share of total sibling loss | 99% / 60% | `results/group_dependency/v2/diagnostics_not_preregistered.json` |
| Mean without worst 5 | −1.8 | `results/group_dependency/v2/diagnostics_not_preregistered.json` |
| Crash day without companion episodes: beta_S / t | −1.3 / −2.40 | `results/group_dependency/v2/diagnostics_not_preregistered.json` |

## Appendix D. The 25 funds (October 2026, verified map)

| Fund | Category | Holdings | effN stocks | effN groups (G1) | Ratio | Matched weight |
|---|---|---|---|---|---|---|
| Axis Flexi Cap Fund | Flexi cap | 69 | 46.3 | 42.1 | 1.10 | 93% |
| DSP Flexi Cap Fund | Flexi cap | 67 | 42.0 | 34.0 | 1.24 | 96% |
| Parag Parikh Flexi Cap Fund | Flexi cap | 51 | 22.3 | 20.9 | 1.07 | 100% |
| SBI Flexicap Fund | Flexi cap | 61 | 46.6 | 44.6 | 1.04 | 85% |
| Tata Flexi Cap Fund | Flexi cap | 66 | 51.2 | 42.4 | 1.21 | 91% |
| Axis Large Cap Fund | Large cap | 48 | 32.1 | 26.9 | 1.19 | 99% |
| DSP Large Cap Fund | Large cap | 42 | 28.0 | 25.2 | 1.11 | 99% |
| Nippon India Large Cap Fund | Large cap | 68 | 44.6 | 36.2 | 1.23 | 97% |
| SBI Large Cap Fund (formerly Bluechip) | Large cap | 54 | 35.0 | 29.3 | 1.19 | 94% |
| Tata Large Cap Fund | Large cap | 45 | 36.2 | 30.2 | 1.20 | 93% |
| Axis Midcap Fund | Mid cap | 85 | 66.5 | 61.2 | 1.09 | 86% |
| DSP Mid Cap Fund | Mid cap | 63 | 54.1 | 47.8 | 1.13 | 94% |
| Nippon India Growth Mid Cap Fund | Mid cap | 100 | 79.9 | 67.8 | 1.18 | 94% |
| SBI Midcap Fund | Mid cap | 56 | 50.1 | 46.7 | 1.07 | 90% |
| Tata Mid Cap Fund | Mid cap | 57 | 51.4 | 47.5 | 1.08 | 92% |
| Canara Robeco Multi Cap Fund | Multi cap | 111 | 91.1 | 81.4 | 1.12 | 88% |
| Nippon India Multi Cap Fund | Multi cap | 123 | 85.7 | 75.8 | 1.13 | 88% |
| Axis Small Cap Fund | Small cap | 129 | 105.6 | 102.2 | 1.03 | 84% |
| Canara Robeco Small Cap Fund | Small cap | 98 | 83.5 | 80.1 | 1.04 | 82% |
| DSP Small Cap Fund | Small cap | 85 | 66.9 | 66.9 | 1.00 | 68% |
| Nippon India Small Cap Fund | Small cap | 259 | 189.3 | 171.7 | 1.10 | 80% |
| SBI Small Cap Fund | Small cap | 63 | 51.2 | 48.5 | 1.06 | 71% |
| Tata Small Cap Fund | Small cap | 62 | 48.2 | 47.2 | 1.02 | 75% |
| Canara Robeco Value Fund | Value | 57 | 44.9 | 43.1 | 1.04 | 90% |
| Nippon India Value Fund | Value | 88 | 57.8 | 51.5 | 1.12 | 90% |

*Source: `results/group_concentration/fund_level_latest_v2map.csv` (portfolios as on 31 Oct 2026).*

---

## References

- Antón, M. and C. Polk (2014). Connected stocks. *Journal of Finance* 69(3), 1099–1127.
- Bertrand, M., P. Mehta and S. Mullainathan (2002). Ferreting out tunneling: An
  application to Indian business groups. *Quarterly Journal of Economics* 117(1), 121–148.
- Coval, J. and E. Stafford (2007). Asset fire sales (and purchases) in equity markets.
  *Journal of Financial Economics* 86(2), 479–512.
- Faccio, Morck and Yavuz (2021). Business groups and the incorporation of
  firm-specific shocks into stock prices. *Journal of Financial Economics* 139(3), 852–871.
- Gopalan, R., V. Nanda and A. Seru (2007). Affiliated firms and financial support:
  Evidence from Indian business groups. *Journal of Financial Economics* 86(3), 759–795.
- Greenwood, R. and D. Thesmar (2011). Stock price fragility. *Journal of Financial
  Economics* 102(3), 471–490.
- Khanna, T. and K. Palepu (2000). Is group affiliation profitable in emerging markets? An
  analysis of diversified Indian business groups. *Journal of Finance* 55(2), 867–891.
- Khanna, T. and C. Thomas (2009). Synchronicity and firm interlocks in an emerging market.
  *Journal of Financial Economics* 92(2), 182–204.
- Kim, Kim and Lee (2015). Stock return commonality within business groups:
  Fundamentals or sentiment? *Pacific-Basin Finance Journal* 35A, 198–224.
- Kwon, Jung, Sunwoo and Yim (2019). Does stock price crash of firms in the
  same business group cause stock price crash in other member firms? Evidence from Korea.
  *Emerging Markets Finance and Trade* 55(7), 1566–1592.
- Meucci, A. (2009). Managing diversification. *Risk*.
- Pathak, M. (2026). Market share is not importance: What happens to rivals when a firm
  dies (US and India). Working paper, Indiana University.
