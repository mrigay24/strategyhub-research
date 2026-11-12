# Paper 2 pilot note: business groups and hidden concentration (India)

*11 Nov 2026. Plan: `PILOT_PLAN.md`. Rules: `PREREGISTRATION.md`. Phase 5 design (draft):
`PREREGISTRATION_2_DRAFT.md`. Verdict: **GO** (§6), with a narrow reading.*

> **Status, 12 Nov 2026.**
> - The group map has been checked against NSE filings (v2, §8): 500 symbols confirmed,
>   21 changed, 230 could not be checked against a filing, and 858 were not checked.
> - The registered test was re-run unchanged on v2, and **GO holds**.
> - Not done: Phase 5 (it waits for Mrigay's approval) and verification of the 858
>   unchecked symbols (mostly standalone firms).

## 1. The idea

Paper 1 found that a failed firm's market share does not predict how its rivals react, and
that the one channel that kept showing up was **shared ownership**: in all three Indian
business-group sets, the group's other firms fell together after one of them collapsed.
Three sets prove nothing, so this pilot asks the question properly.

The hypothesis is **"count groups, not stocks"**:
- Firms that share a promoter group crash together *more than their normal (calm-period)
  price correlation predicts*.
- If so, a portfolio's risk is concentrated in a way that correlation-based tools miss in
  calm markets. An entropy measure built from *who owns what* (the effective number of
  groups, exp(H) with H = −Σ w ln w over group weights) would show it.

A real example: the Nippon India Small Cap Fund holds about 186 "effective" stocks, but only
about 53 effective industries. If business groups add a hidden common shock on top, its true
diversification is lower still.

**The go / no-go question.** Do same-group stocks share crashes more than same-industry
stocks that are not in the group, after controlling for their calm-period correlation? If
yes, design a portfolio-level test (Phase 5). If no, write this note and stop.

## 2. Is this new? Literature check (Phase 1, 11 Nov 2026)

The pilot asks one narrow question: **after a group firm's own crash, do its group siblings
in *other* industries fall more than its industry rivals in *other* groups, once each pair's
calm-period correlation is controlled for?** And, if so, does an entropy measure built from
ownership (effective number of groups) show risk that correlation-based tools miss?

Searches were run on 11 Nov 2026 (web search, abstracts and bibliographic records; full texts
were not read, so details below are from abstracts and must be checked before citing).

### 2a. What already exists

**Business groups and stock comovement (average days, not crashes).**
- Khanna & Thomas (2009), "Synchronicity and firm interlocks in an emerging market", *JFE*
  92(2), 182–204. Chile: synchronicity rises with equity cross-holdings and shared owners,
  and most strongly with interlocking directors.
- Kim, Kim & Lee (2015), "Stock return commonality within business groups: Fundamentals or
  sentiment?", *Pacific-Basin Finance Journal* 35A, 198–224. Korea: comovement within a
  group *beyond what industry explains*, rising after 1997–98; part of it is non-fundamental
  ("habitat") trading.
- Faccio, Morck & Yavuz (2021), "Business groups and the incorporation of firm-specific
  shocks into stock prices", *JFE* 139(3), 852–871. Group affiliates' idiosyncratic returns
  respond *less* to their own commodity shocks than similar standalone firms' do.
- An Indian synchronicity study (*Emerging Markets Finance and Trade* 51(5), 2015;
  doi 10.1080/1540496X.2015.1061381) finds synchronicity with the market is *lower* for
  group-affiliated NSE firms. (That is comovement with the market, not with siblings.)

**Contagion inside groups (events).**
- Kwon, Jung, Sunwoo & Yim (2019), "Does stock price crash of firms in the same business
  group cause stock price crash in other member firms? Evidence from Korea", *EMFT* 55(7),
  1566–1592. **The closest paper.** A firm's crash risk (firm-year crash measures) is
  positively associated with crash risk at other members of its chaebol; crashes *spread*
  rather than arrive together; stronger with more intra-group trade.
- Joe & Oh (2018), "Spillover effects within business groups: the case of Korean chaebols",
  *Management Science* (doi 10.1287/mnsc.2016.2596), and Han & Lee (2016), *Pacific-Basin
  Finance Journal* 39, 84–100: credit-rating changes at one chaebol affiliate move its
  siblings' stock prices, mostly negatively.
- Cumming, Jain & Jindal (working paper, SSRN 5024025): in India, the market's reaction to
  one group firm's equity issue spills over, with the same sign, to its non-issuing siblings.
- Gopalan, Nanda & Seru (2007), "Affiliated firms and financial support: evidence from
  Indian business groups", *JFE* 86(3), 759–795: intragroup loans flow to weak affiliates,
  and **the first bankruptcy in a group is followed by lower financing, investment and
  profits at the other members** (abstract). This settles paper 1's "check before citing"
  item on Gopalan et al.
- Ganguly, Mishra & Platt (2025), *Applied Economics Letters*: after the Hindenburg report,
  Indian indices fell, firms with pledged shares fell more, politically connected firms rose.
  It studies indices and pledging, not siblings versus industry rivals.
- Bertrand, Mehta & Mullainathan (2002, *QJE*) and Khanna & Palepu (2000, *J. Finance*)
  give the background: Indian groups move resources between members (tunnelling) and group
  affiliation matters for value.

**Ownership-based fragility and diversification measures.**
- Antón & Polk (2014), "Connected stocks", *J. Finance* 69(3), 1099–1127: the number of
  shared active mutual-fund owners predicts a pair's future return correlation after
  controlling for industry and style. The same "ownership beyond industry" logic, for
  *institutional* owners and *average* correlation.
- Greenwood & Thesmar (2011), "Stock price fragility", *JFE* 102(3), 471–490: concentrated
  or correlated owners make prices fragile. Coval & Stafford (2007): fire sales by common
  mutual-fund holders.
- Meucci (2009), "Managing diversification", *Risk*: the effective number of bets is the
  exponential of the entropy of the portfolio's variance split across uncorrelated
  (principal-component) bets. It is built from the covariance matrix, so it only sees what
  past prices show.

### 2b. Is this exact test already done?

**No paper found runs this exact test.** The pieces exist separately:
- "Group firms comove beyond industry" is known (Korea, Chile), but on *average* days.
- "Crashes spread inside groups" is known for Korea (Kwon et al. 2019), with firm-year crash
  measures, and without a control for how correlated each pair already was.
- Indian intra-group spillovers are documented for equity issues (Cumming et al.) and for
  financing (Gopalan et al.), not for crash events against industry rivals.

What the pilot would add, if it holds:
1. **India, event level, siblings vs industry rivals.** Who falls with a crashing group firm:
   its owner's other firms in unrelated industries, or its competitors?
2. **"Beyond correlation" is tested directly.** Each pair's calm-period correlation is the
   control. If ownership only matters through what correlation already shows, a
   correlation-based risk model already captures it and the group label adds nothing.
3. **The entropy link.** Effective number of *groups* as a holdings-based concentration
   measure, compared with Meucci's covariance-based effective number of bets. No paper was
   found that builds diversification measures on promoter-group ownership.

**What it would not add:** that group firms are linked (Gopalan et al.), that groups comove
(Kim et al.), or that crash risk spreads inside groups (Kwon et al.). The note must cite
these as the starting point. **Decision: continue.** The test is new in its combination,
not in its parts.

Sources (searched 11 Nov 2026):
[Khanna & Thomas 2009](https://ideas.repec.org/a/eee/jfinec/v92y2009i2p182-204.html) ·
[Kim, Kim & Lee 2015](https://ideas.repec.org:443/a/eee/pacfin/v35y2015ipap198-224.html) ·
[Faccio, Morck & Yavuz 2021](https://econpapers.repec.org/RePEc:eee:jfinec:v:139:y:2021:i:3:p:852-871) ·
[EMFT 2015 India synchronicity](https://www.tandfonline.com/doi/full/10.1080/1540496X.2015.1061381) ·
[Kwon et al. 2019](https://ideas.repec.org/a/mes/emfitr/v55y2019i7p1566-1592.html) ·
[Joe & Oh 2018](https://pubsonline.informs.org/doi/references/10.1287/mnsc.2016.2596) ·
[Han & Lee 2016](https://ideas.repec.org/a/eee/pacfin/v39y2016icp84-100.html) ·
[Cumming, Jain & Jindal WP](https://doi.org/10.2139/ssrn.5024025) ·
[Gopalan, Nanda & Seru 2007](https://www.sciencedirect.com/science/article/abs/pii/S0304405X07001341) ·
[Antón & Polk 2014](https://econpapers.repec.org/RePEc:bla:jfinan:v:69:y:2014:i:3:p:1099-1127) ·
[Greenwood & Thesmar 2011](https://econpapers.repec.org/RePEc:eee:jfinec:v:102:y:2011:i:3:p:471-490) ·
[Meucci 2009](https://risk.net/node/1500233) ·
[Ganguly, Mishra & Platt 2025](https://research.jgu.edu.in/market-perceptions-and-reactions-the-ripple-effect-of-the-hindenburg-report-on-indian-companies/)

## 3. Data and the group map (Phase 2, 11 Nov 2026)

**Prices.** The corrected survivorship-free NSE panel
(`data_processed/nse_survivorship_free_adj.parquet`: 1,620 symbols, Jan 2005 – Jun 2025,
splits and bonuses fixed, delisted firms included).

**Universe.** Every symbol that was in the top 500 by 63-day traded value at any month-end
2005–2025: **1,609 symbols** (`results/group_dependency/universe.csv`). This list was built
from traded value alone, before any return was computed.

**The group map** (`results/group_dependency/group_map.csv`, rules in
`GROUP_MAP_README.md`).
- **Labels.** Each symbol is labelled with its controlling promoter group, with dates for
  changes of control, plus one of 41 industries.
- **Who labelled it.** A Sonnet subagent, working from NSE's public symbol lists, its own
  knowledge and a few web searches. Its raw output is kept in `map_raw/`.
- **Spot checks** found 14 problems, each fixed and logged in `group_map_fixes.csv`.
  Examples: the JK Organisation firms had been split across three brothers' names; one ETF
  was linked to Nippon Life AMC; three pairs of separate companies that later merged had
  been marked "same company".
- **Result.** 1,695 rows. By group type:

  | Family | MNC | State | Professional | Unknown (mostly ETFs) | PE | Corporate |
  |---|---|---|---|---|---|---|
  | 1,329 | 131 | 117 | 46 | 28 | 22 | 22 |

- **Groups.** **110 Family/Corporate groups have two or more distinct listed companies**
  (379 companies). The largest:

  | Group | Listings |
  |---|---|
  | Tata | 33 |
  | Aditya Birla | 15 |
  | Anil Ambani (ADAG) | 12 |
  | Adani | 11 (ACC and Ambuja from Sep 2022) |
  | Mukesh Ambani | 11 |
  | Mahindra | 11 |
  | Murugappa | 11 |
  | Indiabulls | 11 |

- **Confidence.** 1,017 rows are high, 469 medium and 209 low. Low rows are mostly obscure
  small firms whose "group" is just their own promoters. Robustness R6 drops every pair
  that touches a medium or low label.
- **Known weaknesses.**
  - Most source URLs were written from memory, not opened.
  - Family-branch boundaries are judgement calls: TVS, Bajaj, Jindal, Birla and Lalbhai
    are each split by branch.
  - A wrong label most likely puts a true sibling in the "baseline" class. That dilutes
    the group effect, so the test is biased *against* finding one.

## 4. The pre-registered test (Phase 3; full rules in `PREREGISTRATION.md`)

The order of commits is the proof that the rules came first:

| Commit | What it fixed |
|---|---|
| 3e6155f | Literature check and universe (traded value only) |
| 5d74939 | The group map |
| 133c5c9 | The rules and the go/no-go test (pre-registration Part 1) |
| be33f0c | The event list and the news labels, before any comparison stock's return (Part 2) |
| 8b08f04 | The single registered run, plus diagnostics labelled as not pre-registered |

**In plain words.**
1. **Find the crashes.** A *trigger* is a group firm that falls at least 15% in one day.
   It must fall at least 12 points more than the market, and at least 12 points more than
   its industry's non-group firms. A firm can trigger only if another firm of its group is
   in the top 500 that day. Each group gets one event per 20-day episode.
2. **Sort every other top-500 stock into four classes:**
   - **S:** a sibling in another industry (the key class);
   - **SI:** a sibling in the same industry;
   - **R:** an industry rival outside the group;
   - **B:** an unrelated stock.
3. **Measure how each stock did** over the 21 trading days from the crash day, against the
   market (BHAR).
4. **Control for "normal" co-movement.** For each stock and the crashing firm, compute
   their correlation over a calm year ending two weeks before the crash. If siblings fall
   only because they always move together, this control absorbs it.
5. **Regress the outcome** on S, SI and R, with that correlation, size and liquidity as
   controls, plus one fixed effect per event.
   - β_S answers: *does a sibling in an unrelated industry do worse than an unrelated stock
     that was just as correlated with the crashing firm?*
   - β_R answers the same question for industry rivals.
6. **GO** only if all three hold:
   - β_S < 0 with *t* ≤ −1.96 (standard errors clustered by month);
   - a permutation test by event gives *p* < 0.05;
   - β_S ≤ β_R.
   Fewer than 30 events with a sibling, or fewer than 10 groups, means "too few to test",
   which is a STOP.

## 5. Result (registered run, 11 Nov 2026, commit 8b08f04)

Sources: `results/group_dependency/tests.json` (registered) and
`diagnostics_not_preregistered.json` (labelled as not registered).

### 5a. What went in

- 115 events from 50 groups. 98 have at least one sibling with enough data, and **74 have
  a sibling in another industry (S), from 30 groups**. That clears the "too few" bar of
  30 events and 10 groups.
- 40,258 stock pairs:

  | Class | Pairs |
  |---|---|
  | B (unrelated) | 38,601 |
  | R (industry rivals) | 1,388 |
  | S (siblings, other industry) | 228 |
  | SI (siblings, same industry) | 41 |

### 5b. Raw averages (before any control)

| Class | Calm correlation with the crashing firm | Crash-day abnormal return | 21-day BHAR (mean / median) |
|---|---|---|---|
| B: unrelated stocks | −0.01 | +0.1% | −0.1% / −0.7% |
| R: industry rivals | 0.06 | −0.3% | −1.0% / −1.4% |
| **S: siblings, other industry** | **0.15** | **−2.7%** | **−5.2% / −3.1%** |
| SI: siblings, same industry | 0.28 | −3.5% | −5.8% / −0.6% |

Siblings normally move *more* closely with the crashing firm than its industry rivals do
(0.15 against 0.06). That is why the correlation control matters.

### 5c. The registered test (BHAR 0–20, event fixed effects, clusters by month)

| | Coefficient | *t* |
|---|---|---|
| **β_S, sibling in another industry** | **−4.5 pp** | **−2.64** |
| β_SI, sibling in the same industry | −3.7 pp | −1.29 |
| β_R, industry rival | −0.4 pp | −0.44 |
| calm correlation (per unit) | −6.9 pp | −2.78 |
| **β_S − β_R** | **−4.1 pp** | **−2.17** |

- **Permutation by event:** none of 2,000 placebo draws was as negative as the real β_S
  (*p* < 0.0005). Placebo β_S has mean 0.0 pp, standard deviation 0.9 pp and 5th
  percentile −1.5 pp.
- **Without the correlation control:** β_S = −5.6 pp (*t* −3.12). The control explains
  about 1 pp of the sibling effect, not most of it.

In plain words: a firm in an *unrelated* industry that shares an owner with the crashing
firm loses about 4½% more over the next month than an unrelated stock that normally moves
just as closely with the crashing firm. Industry rivals lose almost nothing extra.

### 5d. Robustness (registered; none changes the verdict)

| Check | β_S | *t* | Reading |
|---|---|---|---|
| R1: no 2008–09, no Feb–Apr 2020 (69 events) | −4.7 pp | −2.13 | holds |
| **R2: no paper-1 episodes (7 events dropped)** | **−1.9 pp** | **−1.83** | **weakens below 1.96** |
| R3: crash-day AR | −2.2 pp | −3.51 | holds (S − R *t* −3.26) |
| R3: CAR 0–20 | −5.3 pp | −2.25 | holds |
| R3: + calm-implied move (BHAR / day 0) | −4.1 / −2.2 pp | −2.67 / −3.52 | holds |
| R4: widened groups | identical to primary | | **not informative** (see §7) |
| R5: clusters by event / date / trigger group | | −2.61 / −2.60 / −1.97 | borderline by group |
| **R6: high-confidence labels only (78 events)** | **−3.5 pp** | **−1.67** | **weakens below 1.96** |
| R7: news-checked, no artefacts (26 events) | −11.0 pp | −2.01 | holds (few events) |
| R8: each event weighted equally (74) | mean −4.4 pp, median −2.9 pp | −2.77 | **only 57% of events negative (sign *p* 0.15)** |
| R9: correlation as ten decile dummies | −4.9 pp | −2.90 | holds |

### 5e. Tails (H3, registered, no verdict)

- 195,898 pairs with at least 750 overlapping days.
- **Excess joint-crash frequency** is how often both stocks are in their worst 5% on the
  same day, minus what a normal model with their calm correlation predicts:

  | Pair type | Excess joint-crash frequency |
  |---|---|
  | Unrelated | 0.155% of days |
  | Same industry | 0.207% |
  | **Same group, other industry** | **0.219%** (placebo-group *p* < 0.001) |
  | Same group and same industry | 0.277% (43 pairs) |

- In the tails, sharing an owner adds about as much joint-crash risk as sharing an
  industry, beyond what calm correlation shows.

### 5f. What drives it (NOT pre-registered diagnostics)

- **No single group drives it.** Dropping any one of the 30 groups leaves β_S between
  −3.1 pp (without Adani) and −6.8 pp (without Tata), and significant every time.
- **But a minority of events does.** The 10 worst of 74 events give 93% of the total
  sibling loss, and the 5 worst give 54%. Without the worst 5, the mean is −2.2 pp. The
  worst are:
  - Adani after Hindenburg (Jan 2023);
  - Future Consumer (Feb 2020);
  - IndusInd (Mar 2020);
  - Reliance Petroleum (Nov 2007);
  - Indiabulls (2009 and 2019);
  - Anil Ambani firms (Feb 2019).
- **Groups differ.** Average sibling residual by group:

  | Group | Events | Average sibling residual |
  |---|---|---|
  | Tata | 6 (78 sibling pairs) | −0.3 pp, nothing |
  | Aditya Birla | 3 | +0.9 pp |
  | Anil Ambani | 10 | −6.2 pp |
  | Adani | 6 | −17 pp |
  | Indiabulls | 7 | −17 pp |

  Contagion shows up in stressed, leveraged, pledge-heavy groups, not in strong ones.
- **The crash-day effect survives without paper 1's episodes:** β_S −1.4 pp (*t* −2.57),
  β_S − β_R *t* −2.19. The 21-day effect without them is −1.9 pp (*t* −1.83).

## 6. Go / no-go decision

**GO, by the rule registered before the run.** All three conditions hold:
- β_S < 0 with *t* ≤ −1.96 (−2.64);
- permutation *p* < 0.05 (< 0.0005);
- β_S ≤ β_R (−4.5 against −0.4 pp).

**The honest reading is narrower than the headline:**
1. **Solid:** on the crash day, siblings in unrelated industries fall about 2 pp more than
   their normal correlation predicts. This survives every check, including dropping
   paper 1's episodes.
2. **Real but concentrated:** over the next month the average is −4.5 pp, but it comes from
   a handful of episodes in stressed groups. It is not significant without paper 1's
   episodes or with high-confidence labels only. "Count groups, not stocks" matters most
   when the group itself is fragile.
3. Phase 5 is written to test exactly that: crisis drawdowns, the known episodes excluded
   as a pre-stated check, and promoter stress as the next data task. See
   `PREREGISTRATION_2_DRAFT.md`, **design only and awaiting Mrigay's approval**.

## 7. Limitations

- **The map was built by an AI labeller.** Most source URLs were written from memory,
  and 209 of 1,695 rows are low confidence. With high-confidence labels only, β_S weakens
  to *t* −1.67. The map needs source-verified checking before any paper.
- **R4 was mis-specified.** Events are selected only from Family/Corporate groups, so
  widening the group definition at the pair level cannot change any trigger's siblings.
  The registered R4 is therefore identical to the primary result and tells us nothing
  about MNC, State or PE groups. This is our design error, disclosed rather than
  re-run.
- **Overlap with paper 1.** 7 events (Adani 2023, Anil Ambani 2019 ×2, Indiabulls 2019)
  are episodes already used in paper 1. Without them the 21-day result is not significant.
- **Dependence.** Events cluster in a few groups. Clustering by trigger group gives
  *t* −1.97, and the event-level sign test is not significant (57% negative).
- **Event quality.** In the news-checked sample, about 7% of events are corporate-action
  artefacts and about 27% are market-wide crash days. Both add noise, not bias toward
  finding an effect.
- **Transmission or revelation?** When news is about the whole group (Hindenburg), all
  its firms fall together because the news is about all of them. The test shows that
  owner-level risk exists and that correlation misses it. It cannot say whether one
  firm's crash *causes* the others' fall.
- **Day 0 is the crash day.** The plan defines day 0 as the first trading day after the
  news; for mechanically selected crashes, the crash day is the market's reaction day.
  - Adani: the report came out on 24 Jan 2023, but day 0 is 27 Jan, the first −15% day.
  - Siblings' losses on 25 Jan are therefore not counted, which understates the effect
    there.
- **Universe.** Top-500 stocks only, so siblings outside the top 500 are not seen.
- **Calm correlation is a noisy one-year estimate.** That weakens the control. Controlling
  for the calm-implied move instead, or entering correlation as deciles, does not change
  the result.

## 8. Map verification and re-run (v2, 12 Nov 2026; deviation D1)

**Why.** The v1 map came from an AI's memory. With high-confidence labels only, β_S fell to
*t* −1.67, so the labels were the obvious weak point.

**What was checked:**
1. **NSE shareholding-pattern filings** (XBRL, 2020/21 onward; 11,106 filings listed,
   promoter names parsed). These covered 750 priority symbols:
   - every firm in the 74 sibling events;
   - every member of a multi-company group;
   - every low-confidence row.

   For each firm we asked whether it shares a promoter entity (a family member, holding
   company or trust, or the sibling company itself) with the other members of its group.
2. **A source check at the event dates** for the 135 firms in those events, which matters
   because most events fall before 2020 (news, annual reports, group lists;
   `verify/p1_history.csv`).
3. **Review of every flagged row,** with a written decision and its source
   (`verify/decisions.csv`, 95 rows).

**What changed.** 21 symbols, 26 label rows (`group_map_v2_changes.csv`):
- **Great Offshore and Bharati Shipyard had been merged into one group.** Great Offshore
  was still run by its own promoter (Vijay Sheth) in 2008, and Bharati took control only
  in 2009–10. This removes two 2008 events, one of them among the ten biggest in v1.
- **Control dates corrected:**
  - Avaya GlobalConnect left Tata in 2004.
  - UB kept Mangalore Chemicals until end-2014.
  - Sameer Gehlaut was declassified at Sammaan Capital in Feb 2023.
  - Orient Cement moved to Adani (2025), Reliance Naval to Swan (2024) and Religare to
    the Burmans (2025).
- **Wrong group:**
  - Maharashtra Seamless and Jindal Drilling are DP Jindal.
  - Consolidated Finvest is BC Jindal.
  - Mangalam Cement is BK Birla.
  - Muthoot Microfin is the Muthoot Pappachan group.
  - Nuvama is PAG.
  - VIP Clothing is the Pathare family.
- **Missed members:**
  - Yaari Digital belongs to Indiabulls.
  - Sonata Software belongs to Rajan Raheja.
  - Hercules Hoists belongs to the Rahul Bajaj family.
  - Avadh Sugar belongs to the Nopany branch.
  - Sequent Scientific belonged to Strides (Arun Kumar) before Carlyle.
- **Joint or cross-family promoters were noted, not relabelled:** Vodafone Idea, Supreme
  Petrochem, Sterling & Wilson, United Breweries, the Jindal branches and the Birla
  branches.
- **Confidence:** low-confidence rows fell from 209 to 117, and high rose from 1,017 to
  1,149.

**Limits of the check:**
- 230 symbols have no NSE filing in the 2020+ window (delisted earlier) and no
  confirming document, so they are "unverifiable".
- Most pre-2020 "yes" answers rest on group-company lists, not dated filings. Rows that
  rest *only* on an undated list are medium confidence in v2.
- 858 symbols, mostly standalone firms, were not checked.

**The re-run** (`results/group_dependency/v2/`, same code and rules, run once):

| | v1 (registered) | v2 (verified map) |
|---|---|---|
| Events / with a sibling in another industry / groups | 115 / 74 / 30 | 113 / 72 / 29 |
| **β_S, BHAR 0–20** | **−4.5 pp (*t* −2.64)** | **−4.7 pp (*t* −2.66)** |
| β_R (industry rivals) | −0.4 pp (*t* −0.44) | −0.4 pp (*t* −0.38) |
| β_S − β_R | −4.1 pp (*t* −2.17) | −4.4 pp (*t* −2.26) |
| Permutation *p* | < 0.0005 | < 0.0005 |
| **Go / no-go** | **GO** | **GO** |
| R1 without 2008–09 and Feb–Apr 2020 | −4.7 pp (*t* −2.13) | −5.0 pp (*t* −2.22) |
| **R2 without paper-1 episodes** | −1.9 pp (*t* −1.83) | **−1.9 pp (*t* −1.71)** |
| R3 crash day | −2.2 pp (*t* −3.51) | −2.2 pp (*t* −3.39) |
| **R6 high-confidence labels only** | −3.5 pp (*t* −1.67) | **−7.0 pp (*t* −2.53)** |
| R5 clustered by trigger group | *t* −1.97 | *t* −1.93 |
| R8 events weighted equally (share negative, sign *p*) | −4.4 pp (57%, 0.15) | −4.1 pp (56%, 0.20) |
| Crash day without paper-1 episodes (not registered) | −1.4 pp (*t* −2.57) | −1.3 pp (*t* −2.40) |
| Tail: excess joint-crash frequency, same group vs unrelated | 0.219% vs 0.155% | 0.218% vs 0.155% |

**What it means, in plain words:**
- **The labels were not what made the result look fragile.** Fixing them removed one wrong
  big event and left the main number where it was. When we keep only labels backed by
  documents, the effect gets stronger (*t* −2.53), not weaker. So the main robustness
  worry about v1 is answered.
- **The other worry stays.** The month-long effect still comes from a handful of stressed
  groups. The 10 worst of 72 events carry essentially all of it; without paper 1's
  episodes it is −1.9 pp with *t* −1.71; and only about half of events are negative.
  Tata's siblings still show nothing.
- **The crash-day effect is the robust part.** Siblings in unrelated industries fall about
  1.3–2.2 pp more than their normal correlation predicts, in every version.
- **Promoter pledges** are now saved for later (`promoter_pledges.csv`, from the same
  filings, no analysis). They are the natural "fragile group" variable for Phase 5.
