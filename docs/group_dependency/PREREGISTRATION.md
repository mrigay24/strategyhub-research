# Pre-registration: do business-group siblings crash together beyond what correlation predicts? (India pilot)

**Project:** paper 2 pilot, "count groups, not stocks" · **Author:** Mrigay Pathak ·
**Written:** 11 November 2026 · **Plan:** `PILOT_PLAN.md` · **Group map:**
`results/group_dependency/group_map.csv` (committed before this file)

## 0. How this file is time-stamped

Same protocol as paper 1 (`docs/entropy_research/PREREGISTRATION.md`). The git commits are
the proof of order:

1. **The group map** (`results/group_dependency/group_map.csv`, rules in
   `GROUP_MAP_README.md`) was committed first, before any return was computed for this
   pilot.
2. **Part 1 (this commit): the rules (§1–§9).** Committed before any event is selected and
   before any test statistic exists.
3. **Part 2: the event list.** `scripts/group_dependency_pilot.py events` selects the crash
   events from the *trigger firms' own* returns only, and a news check is run on a random
   sample of them (§3.4). The event list and the news labels are committed **before any
   comparison stock's return, correlation or outcome is computed**.
4. **Part 3: the run.** `scripts/group_dependency_pilot.py run`, once, with the code as
   committed in Part 2.

Nothing in §1–§9 may change after Part 1. Anything that must change goes into the deviation
log (§10) with a date and a reason, and both versions are reported.

## 1. Hypotheses

- **H1 (primary).** After a business-group firm suffers its own crash, its group siblings
  **in other industries** do worse over the next 20 trading days than unrelated stocks
  with the **same calm-period correlation** with the crashing firm.
- **H2 (primary comparison).** After the same control, those siblings do **at least as badly
  as the crashing firm's industry rivals** that are not in its group.
- **H3 (secondary: tails).** Pairs of stocks in the same group are jointly in their worst 5%
  of days more often than their calm-period correlation predicts, and more so than pairs in
  the same industry.

In words: if ownership only matters through what past prices already show, a
correlation-based risk model captures it and the group label adds nothing (H1 fails). If the
group label adds a shock channel that correlation misses, counting groups reveals hidden
concentration (H1 holds), and Phase 5 designs the portfolio test.

## 2. Data

- **Prices:** `data_processed/nse_survivorship_free_adj.parquet` (survivorship-free NSE
  bhavcopy panel, splits and bonuses corrected; KNOWLEDGE_BASE §42). Close-to-close returns
  with `pct_change(fill_method=None)` on the wide panel, so a return after a missing day is
  missing, never a multi-day return.
- **Corporate actions:** a one-day return beyond ±45% is removed as a probable unadjusted
  corporate action, for every stock including triggers, and every removal is logged
  (`results/group_dependency/removed_returns.csv`).
- **The 2011 hole:** the panel has no dates from 22 June 2011 to 30 December 2011. A return
  whose previous panel date is more than 10 calendar days earlier is set to missing (this
  removes the 195-day "return" on 2 January 2012). No event window (day −1 to day +20) may
  touch 22 June 2011 – 31 January 2012.
- **Universe on day *t*:** the top 500 stocks by 63-day average traded value (close ×
  volume), measured the day before (lagged one day), with a valid return on day *t*.
  ETFs and fund units (group `ETF (not a company)` in the map) are removed from the panel
  before the ranking.
- **Market return:** the equal-weighted mean return of the universe.
- **Abnormal return (AR):** stock return minus market return.
- **Group and industry:** from the committed group map. Group membership is read on day 0
  (the map's `start`/`end`). Industry is one fixed label per symbol (41 industries).
  Symbols flagged as the same company (`same_company_as`) are never paired with each other.
- **Group definition used in the primary test:** two firms are in the **same group** if
  they share a `group` label of type **Family** or **Corporate** on day 0. MNC, State, PE,
  Professional and Unknown labels do not make a group in the primary test (robustness §8
  adds MNC, State and PE).

## 3. Events (who crashes)

### 3.1 Selection rule

A **trigger** is a stock *i* on day *t* (day 0) such that:
1. *i* is in the universe on day *t*;
2. *i*'s group on day *t* is of type Family or Corporate, and at least one other stock of
   the same group is in the universe on day *t*;
3. *i*'s day-0 return is **≤ −15%**;
4. its day-0 AR (versus the market) is **≤ −12%**;
5. its day-0 return minus the equal-weighted return of the universe stocks in its industry
   that are *not* in its group is **≤ −12%** (applied only when that set has at least 3
   stocks; otherwise condition 4 alone applies);
6. its return on day +1 is **not above +25%** (a reversal that size is treated as a bad
   print, as in `death_test.py`);
7. (symbol, day 0) is **not** in `results/nse_data_audit/corporate_action_suspects.csv`
   with verdict UNCERTAIN, BAD_TICK, CA_LIKELY_NICE or CA_CONFIRMED_YAHOO;
8. day 0 lies between 2 January 2006 and 30 May 2025, and the event window obeys the 2011
   hole rule (§2).

Conditions 1–8 use only the trigger's own return, its industry's and the market's returns
on day 0, and its own return on day +1. Thresholds −15% / −12% are paper 1's Part A rule;
condition 5 replaces paper 1's sub-industry adjustment with an industry adjustment that
excludes the trigger's group (so the trigger's siblings never decide whether it is an
event).

### 3.2 One event per group episode

Within each group, qualifying days are taken in date order. The first one starts an
**episode**; any qualifying day of *any* firm in the same group within the next 20 trading
days belongs to that episode and is not a new event. If two or more firms of one group
qualify on the same day, the trigger is the one with the largest lagged 63-day traded value
(a size rule, not an outcome rule); the others are outcome stocks like any sibling.

### 3.3 Comparison stocks for each event

All other stocks *j* in the universe on day −1 that have:
- at least 150 days with valid ARs for both *i* and *j* in the **calm window** (the 252
  trading days ending 10 trading days before day 0, i.e. days −261 … −10);
- at least 15 valid returns in days 0 … +20.

Each comparison stock falls in exactly one class:
- **S, group sibling, other industry:** same group as *i*, different industry;
- **SI, group sibling, same industry:** same group, same industry (kept separate);
- **R, industry rival:** same industry, different group (another group, or any non-group
  label);
- **B, baseline:** different group and different industry.

An event enters the test only if it has at least one S or SI stock.

### 3.4 News check on a random sample (descriptive)

The mechanical rule can let in corporate actions that the ±45% filter and the audit list
miss (mainly demergers of 15–45%). Before any comparison stock's return is computed, a
random sample of **30 events** (seed 20261111; all events if there are fewer) is checked by
web search and labelled: (a) firm- or group-specific bad news; (b) corporate action or data
artefact; (c) market- or industry-wide news; (d) no news found. The labels are committed
with the event list. They do not change the primary sample. They give the contamination
rate, and robustness §8 R7 re-runs the test on the checked events without (b).

## 4. Outcomes

For each comparison stock *j* in event *e*:
- **Primary: BHAR(0,20)** — *j*'s compounded return over days 0 … +20 minus the
  compounded market return over the same days. Missing returns count as zero (paper 1).
  For the reported means, the market here excludes the trigger's group and industry. (In
  the regression the event fixed effect absorbs the market term, so this choice does not
  change any coefficient.)
- **Secondary:** day-0 AR; CAR(0,20) = the sum of ARs over days 0 … +20.

## 5. The control

- **Calm correlation ρ_ij:** Pearson correlation of *i*'s and *j*'s daily ARs over the calm
  window (days −261 … −10).
- **Size:** log of *j*'s 63-day average traded value on day −11.
- **Liquidity:** log of *j*'s Amihud illiquidity over the calm window (mean of |return| /
  traded value).

## 6. The primary test (decides go / no-go)

Pair-level OLS over all events and comparison stocks:

  BHAR_ej = α_e + β_S·S_ej + β_SI·SI_ej + β_R·R_ej + γ·ρ_ij + δ1·size_j + δ2·liquidity_j + ε_ej

- α_e is an **event fixed effect** (it absorbs the trigger's crash size, the date and the
  market). The baseline class B is the omitted category, so β_S is how much worse a
  sibling in another industry does than an unrelated stock with the same calm correlation,
  size and liquidity, in the same event.
- **Standard errors:** clustered by event and by date, as the plan asks. Because each event
  has one day 0, date clusters nest event clusters, and overlapping 20-day windows make
  nearby dates dependent, so the verdict uses the stricter **clustering by the calendar
  month of day 0**. Clustering by event, by day-0 date and by the trigger's group is
  reported too.
- **Permutation by event (2,000 draws, seed 20261111):** within each event, the S label is
  reassigned at random to the same number of stocks drawn from that event's S ∪ B stocks;
  SI and R stay fixed; β_S is re-estimated. One-sided *p* = share of draws with β_S at or
  below the real one.

**Go / no-go rule (fixed now):**
- **Too few events to test** if fewer than **30 events have at least one S stock**, or
  those events come from fewer than **10 distinct groups**. Then the verdict is **STOP**
  (no Phase 5), and the note says the pilot could not test the idea.
- **GO** if all three hold:
  1. β_S < 0 with month-clustered *t* ≤ −1.96;
  2. permutation *p* < 0.05;
  3. β_S ≤ β_R (point estimates: siblings in other industries do at least as badly as
     industry rivals, after the control). The *t*-statistic of β_S − β_R is reported.
- **STOP** otherwise, with the reason named:
  - "**calm correlation explains it**" if β_S is significant (rules 1–2) in the same
    regression *without* ρ but not with it;
  - "**no group effect**" if β_S is not significant with or without ρ;
  - "**group effect smaller than industry**" if rules 1–2 hold but rule 3 fails.

## 7. Secondary measure: excess tail dependence (H3; reported, no verdict)

- Pairs: all pairs of universe stocks with at least 750 overlapping days of valid ARs
  over 2005–2025.
- **Calm days:** days on which the market return is between its own 10th and 90th
  percentiles (full sample). **Calm correlation** = the pair's AR correlation on calm days.
- **Tail day for a stock:** a day on which its AR is in its own worst 5%.
- **Excess tail dependence** = the pair's observed share of overlapping days on which both
  are in their tail, minus the share a bivariate normal with the calm correlation predicts
  (orthant probability at z = −1.645).
- Pair classes: **same group** if the pair shares a Family/Corporate group on at least 80%
  of its overlapping valid days; pairs that share a group on 1–80% of days are left out;
  **same industry**, **both**, **neither**.
- Report the mean excess by class, a pair-level OLS of excess on the class dummies plus the
  calm correlation, and a permutation *p* for the same-group, other-industry mean: the
  multi-member group labels are reshuffled across universe stocks 1,000 times (seed
  20261111), keeping group sizes. Pairs share stocks, so this permutation is the inference;
  OLS *t*-statistics are not used.

## 8. Robustness (reported; they do not change the verdict)

- **R1:** without events whose day 0 is in 2008–2009 or February–April 2020.
- **R2:** without the group episodes used in paper 1: events of the Adani group within 60
  trading days of 25 Jan 2023, of Reliance ADAG within 60 trading days of 4 Feb 2019 or
  12 Jun 2019, and of the Indiabulls group within 60 trading days of 6 Sep 2019.
- **R3:** secondary outcomes (day-0 AR, CAR 0–20); and an extra control, the
  calm-implied move = (calm beta of *j* on *i*) × (trigger's own BHAR 0–20; day-0 AR for
  the day-0 outcome).
- **R4:** the group definition widened to include MNC, State and PE labels.
- **R5:** clustering by event, by day-0 date and by the trigger's group.
- **R6:** only high-confidence group labels (pairs where either label is medium or low are
  dropped).
- **R7:** the news-checked events only, without corporate-action or artefact events.
- **R8:** each event weighted equally: per event, the mean residual of its S stocks (from
  the regression with event fixed effects and controls fitted on B stocks only); then a
  one-sample *t*-test and a sign test across events.
- **R9:** ρ entered as ten decile dummies instead of linearly.
- **R10:** the same regression without ρ (needed for the STOP reason in §6).

## 9. What gets reported

Every number above, including those against the hypothesis: counts of events, groups and
pairs by class; mean outcomes by class (raw and residualised); all coefficients with every
standard error; the permutation distribution; the tail measure; and the list of removed
returns. Results go to `results/group_dependency/` and the write-up to `NOTE.md`.

## 10. Deviation log

*(empty)*

## 11. Part 2 record: the event list (committed before any comparison stock's return)

`scripts/group_dependency_pilot.py events` (code as of 133c5c9), run 11 Nov 2026:
- The panel without 20 ETF symbols; 1 hole date (2 Jan 2012) set to missing; 25 one-day
  returns beyond ±45% removed (`removed_returns.csv`).
- 997 universe stock-days with a return ≤ −15% and AR ≤ −12%. Dropped:
  - 668: no other firm of the group in the universe that day;
  - 138: not a Family/Corporate group firm;
  - 18: industry-adjusted return above −12%;
  - 1 each: outside the date range, touching the 2011 hole, or next-day reversal.
- That leaves 170 qualifying days. **115 events from 50 groups** (`events.csv`), after
  folding 14 same-day co-qualifiers and 41 later days inside an episode. The largest
  groups are Reliance ADAG 11, Indiabulls 8, Tata 8, Adani 6 and Jaypee 6. 91 trigger
  labels are high confidence and 24 medium.
- News check on the random 30 (`news_sample.csv`; a Sonnet subagent, web search, told not
  to look at other stocks' moves):

  | a (firm/group news) | b (corporate action or artefact) | c (market or industry crash day) | d (no news found) |
  |---|---|---|---|
  | 14 | 2 | 8 | 6 |

  - The two b cases are Harrisons Malayalam (31 Aug 2010, demerger ex-date) and Lloyds
    Engineering (28 Apr 2025, rights-issue ex-date).
  - So about 7% of events are probably artefacts. They add noise to every class and bias
    the test toward finding nothing.
  - About a quarter of events fall on market-wide crash days. R1 drops 2008–09 and
    February–April 2020.
