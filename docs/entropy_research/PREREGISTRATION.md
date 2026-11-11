# Pre-registration: out-of-sample "death test"

**Paper:** *Market Share Is Not Importance: What Happens to Rivals When a Firm Dies (US and
India)* · **Author:** Mrigay Pathak · **Written:** 11 November 2026

## 0. Why this file exists, and how it is time-stamped

The eight case studies in `RESEARCH_NOTE.md` §4b were picked *after* we knew what
happened, so the "shared dependency" labels could be story-fitting. This file fixes the
rules **before** the new cases are seen. It is committed to git in two steps, and the
commit timestamps are the proof:

1. **Part 1 (this commit): the rules.** Committed before the selection code has run, so
   before anyone has seen which firms qualify.
2. **Part 2: the case list.** Every selected case with its news description, label, day 0
   and rival list (§9 below and `oos_cases.csv`). Committed after Mrigay has checked the
   labels and **before any rival's return is computed**. The analysis code
   (`scripts/death_test_oos.py run`) is committed with it.

Nothing in §1–§8 may change after Part 1. Anything that has to change later goes into
the deviation log (§10), with the reason, and both versions are reported.

## 1. Hypotheses

- **H1 (primary).** When a firm collapses for reasons of its own, its rivals do worse over
  the next 20 trading days if they share a critical dependency with it (a funding market,
  a depositor base, or a legal liability) than if they do not.
- **H2 (secondary: is it only finance?).** H1 holds separately for financial and for
  non-financial failed firms.
- **H3 (secondary: the owner channel, India).** Listed firms controlled by the same
  business group as the failed firm do badly over the next 20 trading days.
- **H4 (secondary: market share).** The failed firm's share of its rival group does *not*
  predict the rivals' 20-day reaction once the label is known.

## 2. Data

- **India:** daily returns from the same combined panel as `scripts/death_test.py`:
  - adjusted Yahoo closes (`nse_prices_clean.parquet`) first;
  - the corporate-action-corrected bhavcopy panel (`nse_survivorship_free_adj.parquet`)
    as the fallback;
  - the universe is the top 300 stocks by 63-day average traded value, lagged one day.
- **US:** raw `extended_prices.parquet` with the $1 price floor; universe = S&P 500
  point-in-time members (`sp500_universe_lookup.csv`).
- **Both:** one-day returns beyond ±95% are removed, and so are returns above +100%. The
  market is the equal-weighted average return of the universe.
- **India data hole:** the panel has a hole from 22 June 2011 to 30 December 2011, and
  the return on 2 January 2012 spans 195 days (KNOWLEDGE_BASE §42). Any window that
  touches 22 June 2011 – 31 January 2012 is skipped.

## 3. Selection rule (a)

**Route 1: a collapse in price.** A stock qualifies on day *t* if:
- it is in the universe on day *t* or day *t*−1;
- its 20-trading-day abnormal buy-and-hold return over days *t* … *t*+19 is below −50%.
  This is the stock's compounded return minus the market's compounded return. Missing
  stock returns count as zero, and at least 10 of the 20 returns must exist;
- the window starts on or after 2 January 2006 (India) or 3 January 2000 (US), and at
  least 21 trading days of data follow it.

**Route 2: the stock stops trading (suspension, default, forced delisting).** A stock is a
route-2 candidate if:
- its last return in the panel comes more than 60 trading days before the panel ends;
- it was in the universe at some point in the 60 trading days before its last return;
- its abnormal buy-and-hold return over those 60 days is below −30%.

Route-2 candidates enter only if the news check (below) shows a default, insolvency,
suspension or forced delisting. They are dropped for a merger, a voluntary delisting
offer, an index exit or a data artefact.

**One event per episode.** A stock's first qualifying day starts an episode. The same
stock cannot start another one for 250 trading days. If a route-1 window ends within 60
trading days before a route-2 last return, they are the same episode.

**Exclusions.**
- **The eight cases already used.** A candidate is dropped if its firm was the failed
  firm, a rival or a group firm in one of those eight cases, *and* its window lies
  within 60 trading days of that case's day 0. The cases are Satyam, Jet Airways,
  IL&FS, DHFL, Yes Bank, Adani, PG&E and SVB, with the dates and lists in
  `scripts/death_test.py`.
- **Size cap.** If more than **60** candidates remain in a market after the exclusions, a
  random sample of 60 is drawn (seed 20261111) and only those are news-checked. This
  keeps the news work feasible, and the rule is fixed in advance.

**News check (every candidate).** A web search establishes what happened. The candidate is
dropped if:
1. the fall is a data artefact: a split, bonus, demerger, ISIN change or bad print,
   confirmed by the news or the price path;
2. no public news explains the fall, so no day 0 can be set;
3. the cause is industry-wide or market-wide (§5, step 1). These cases are listed and
   their outcomes reported, but they are not in the primary test.

**At least 3 rivals.** A case needs at least 3 rivals (§4) with at least 100 valid
returns in the 250 trading days before day 0. Otherwise it is dropped.

**Day 0.** The first trading day on or after the date the news that started the collapse
became public. If the news came out after the market closed, day 0 is the next trading
day. If the time is unclear, use the date of the first press report. The news must fall
within 20 trading days before the window starts or inside the window. Day 0 is **never**
"the worst day nearby".

## 4. Rival sets

- **US:** the failed firm's GICS sub-industry from `sp500_subindustry.csv`. If the firm
  is missing from that file (most delisted firms are), the sub-industry is assigned by
  hand from its business description, choosing among the sub-industry names in the
  file. This is done before any rival return is computed. Rivals are all firms in the
  file with that sub-industry that are S&P 500 members on day 0. There is no fallback to
  a wider group: fewer than 3 rivals means the case is dropped.
- **India:** there is no industry file, so rivals are chosen by hand. They are picked from
  the stocks in the universe on day 0, using only names and line of business: firms that
  sell the same product or service to the same kind of customer.
  - Example: private banks for a private bank; NBFCs and housing-finance companies for an
    NBFC; real-estate developers for a developer.
  - Firms in the failed firm's own business group are **not** rivals.
  - If more than 10 qualify, keep the 10 largest by 63-day traded value on day 0.
- **India group sets (for H3):** listed firms controlled by the same promoter or group
  that are in the universe on day 0. At least 2 are needed.

## 5. Classification rule (b)

For each case we write **one paragraph describing the shock as it was known on day 0**:
- what happened and why;
- what the firm does;
- how it was funded, where that matters.

The paragraph uses **no information about how rivals' stocks moved and no later events**.
The label is decided from that paragraph alone, in two steps.

**Step 1: was it the firm's own crash?**
- **Firm-specific triggers:**
  - fraud or accounting problems;
  - a default or liquidity failure of this firm;
  - a management or governance event;
  - a regulatory action against this firm;
  - its own product, plant, contract or lawsuit;
  - a short-seller report about it or its group.
- **Industry-wide triggers:** a policy, court ruling, tax, price war, new entrant,
  commodity-price move or demand collapse that hits the whole industry at the same time.
  These are labelled **"industry shock"** and kept out of the primary test, because the
  question is about a firm's *own* crash.

**Step 2: is there a shared dependency?** The label is **"shared dependency" (SD)** if at
least one of these holds; otherwise it is **"output-replaceable" (OR)**.

- **(F) Funding.**
  - All three must hold:
    - the failed firm is a financial intermediary (bank, NBFC, housing-finance company,
      broker, insurer);
    - the trigger is a funding or solvency failure (a missed payment, a default, a
      rating cut below investment grade, a failure to roll over debt, creditors pulling
      money, or news that it may not be able to pay creditors without a rescue);
    - the rivals are financial intermediaries that fund themselves in the same market
      (commercial paper, bonds, money-market or debt mutual funds, interbank loans, or
      uninsured deposits).
  - **Non-financial failed firm:** (F) applies only if the day-0 news names a specific
    lender or financier that the failure puts at risk *and* the rivals rely on that same
    lender.
- **(D) Depositors.** All three must hold:
  - the failed firm takes deposits;
  - the trigger involves withdrawals, a withdrawal limit, a moratorium or a regulator's
    takeover;
  - the rivals take deposits too.
- **(L) Liability or regulation.**
  - The trigger is a legal liability or a regulatory finding whose legal basis applies to
    the rivals too: the same law, rule, licence condition or liability regime, so the
    rivals could face the same claim.
  - A penalty for this firm's own misconduct does **not** count.
- **(O) Owner.** Tested through the group sets (H3), not the rival sets, because the rival
  sets exclude the failed firm's group.

**Tie-break:** if the paragraph does not clearly establish (F), (D) or (L), the label is
**OR**.

**Financial or not (for H2).** "Financial" means the failed firm is a bank, NBFC,
housing-finance company, insurer, broker or asset manager. Real estate is not
financial.

**Who labels.** Claude writes the paragraphs and the labels. Mrigay checks them before any
rival return is computed. Phase 6 of the project later asks an LLM to label the same
paragraphs on its own.

## 6. Outcome and predictions (c)

- **Rival outcome.** For each rival: its compounded return over days 0–20 (21 trading
  days) minus the market's compounded return over the same days. This is the 20-day
  buy-and-hold abnormal return, **BHAR**. Missing returns count as zero.
- **Rival filter.** One-day rival returns beyond ±45% are removed as probable unadjusted
  corporate actions, and every removal is logged, as in `death_test.py`.
- **Market for the outcome.** The equal-weighted universe, excluding the failed firm, its
  rivals and its group firms.
- **Case outcome.** The equal-weighted mean of its rivals' BHARs.
- **Prediction:**
  - **SD cases:** case outcome **< 0**.
  - **OR cases:** case outcome **≥ 0**.
  - **Group sets (H3):** mean group-firm BHAR **< 0**.

## 7. Tests (d) and what counts as success

One case = one failed firm and its rival set. US and India cases are pooled.

- **T1 (primary): the difference in means.** Mean outcome of SD cases minus mean outcome
  of OR cases.
  - One-sided permutation p-value: shuffle the labels across cases 20,000 times (seed
    20261111), keeping the number of SD and OR cases fixed. *p* is the share of shuffles
    with a difference at least as negative as the real one.
- **T2: the hit rate.** The share of cases whose sign matches the prediction, overall and
  within each label. A one-sided Fisher exact test of label against sign (outcome < 0)
  goes with it.

**Verdict on H1 (fixed now):**
- **Supported:** T1 *p* < 0.05 **and** the hit rate is above 50% in both the SD and the OR
  group.
- **Partly supported:** T1 *p* < 0.05, but one group's hit rate is 50% or below. For
  example, rivals fall in both groups, only more after SD cases.
- **Not supported:** T1 *p* ≥ 0.05.
- **Too few cases to test:** either label has fewer than 5 cases. T1 is then reported as
  description only.

**T3 (H2): financial versus non-financial failed firms.**
- For each subgroup, report:
  - the number of cases by label;
  - the hit rate by label;
  - the mean difference with its permutation *p*, if each label has at least 3 cases.
- **"Works" in a subgroup** means:
  - the difference in means has the predicted sign, and the hit rate is above 50% in
    both labels; or
  - if one label has fewer than 3 cases, the hit rate in the other label is at least 2/3.
- **What each outcome means, decided now:**
  - **Works in both subgroups:** the general claim stands. What rivals share with the
    failed firm predicts their reaction inside and outside finance.
  - **Works only within financials:** the claim **narrows to financial contagion**.
    Shared funding and depositors spread a failure, but outside finance the rule does
    not predict rivals' reactions. The title and abstract will say so.
  - **Works only outside financials:** the general claim survives outside finance, and
    the financial cases need another explanation. (Not expected.)
  - **Works in neither:** the rule fails out of sample.

**T4 (H3): group sets.** Report the mean group-set BHAR, the share of group sets below
zero, and a sign test.

**T5 (H4): market share.**
- **Share** = the failed firm's 63-day traded value divided by the total for itself and
  its rivals, measured the day before day 0.
- Report the Spearman correlation between share and the case outcome, and an OLS of the
  outcome on an SD dummy plus share, with heteroskedasticity-robust t-statistics.
- **Prediction:** the SD coefficient is negative and |t| ≥ 2; share has |t| < 2.
- If share is significant and the label is not, H4 fails and the paper says so.

## 8. Robustness checks (reported, but they do not change the verdict)

- Market-model abnormal returns: each rival's beta is estimated on days −260 to −11, and
  its compounded return is compared with the compounded beta-scaled market return.
- Median rival instead of mean; the share of rivals with BHAR < 0.
- Day-0 and days 0–5 windows.
- Excluding events in 2008–09 and February–April 2020.
- US and India separately.
- The outcomes of the "industry shock" cases, described separately.

## 9. Case list

*To be added in Part 2, before any rival return is computed.* It will contain each
case's firm, market, route, day 0, financial yes/no, the one-paragraph description, the
label and channel, the rival list, the group list (India), and the dropped candidates
with reasons.

## 10. Deviation log

*Empty at Part 1.*
