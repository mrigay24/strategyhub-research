# Pre-registration: out-of-sample test of the "shared dependency" hypothesis

**Stage 1 (rules) written and committed:** 10 November 2026 · **Author:** Mrigay Pathak
**Paper:** *Market Share Is Not Importance* (`RESEARCH_NOTE.md` §6) · **Red-team that shaped this design:** `RESEARCH_NOTE.md` §4c

The git commit that adds this file is the proof of when the rules were fixed. Nothing in
this file may be edited after Stage 2 is committed. Later corrections go in the
"Deviations" table of the paper, with results shown both ways.

---

## 0. What this is, and what was already known

**The weakness being fixed.** The eight case studies in `RESEARCH_NOTE.md` §4b were chosen
after the fact, and their "shared dependency" labels were written by someone who could see
how the rivals' prices moved. This test fixes the cases and the labels first and looks at
rivals' prices last.

**Three stages, three commits:**

| Stage | What happens | What may be looked at |
|---|---|---|
| 1. Rules (this file) | Selection rule, classification checklist, predictions, tests | Nothing new |
| 2. Cases | Run the screen, research each collapse, date it, label it, list its rivals. Commit. | The failed firm's own returns and the market average only |
| 3. Test | Compute rivals' returns and run the tests in §7 | Everything |

**Why two commits before the test.** Stage 1 was written in a session that had no price
files, so the list of collapses could not be produced. The rules are fixed here; the cases
are fixed in the Stage 2 commit. Both come before any rival return.

**Disclosure: what had been seen when these rules were written.**
- The eight in-sample cases and their rivals' returns (`results/death_test/cases*.csv`).
  The checklist in §4 was written knowing them, so its fit to those eight is not evidence.
- The Part A summary tables for the US. `results/death_test/us_events.csv` holds rival
  returns for 266 US crashes at firms still in the index. Its rows were not read one by
  one, but some out-of-sample US events may also sit in that file. They are flagged
  (`in_part_a`) and dropped in a robustness check (§8).
- `results/nse_data_audit/corporate_action_suspects.csv`, which lists large one-day moves
  of Indian stocks. It contains each stock's own return only.
- No rival return for any out-of-sample event has been computed.
- Whoever writes the labels knows recent financial history. §9 deals with that.

---

## 1. Hypotheses

Plain version: **when a firm collapses for its own reasons, rivals who share its funding
market or its legal liability fall; rivals who only sell the same product do not.**

| | Hypothesis | Prediction |
|---|---|---|
| **H1** (main) | The label predicts the rivals' 20-day return | Mean rival return is lower for "shared dependency" (SD) events than for "output-replaceable" (OR) events |
| **H1a** | Sign in the SD class | Mean rival return below 0 |
| **H1b** | Sign in the OR class | Mean rival return at or above 0 |
| **H2** | The label is more than "financial firm" | The SD–OR gap is negative inside the non-financial half and inside the financial half, and the label beats the rule "financial ⇒ rivals fall" |
| **H3** (India) | Ownership is a dependency | For the same collapse, group affiliates do worse than same-industry rivals |
| **H4** | Market share does not explain it | The failed firm's share of its industry has no reliable relation to the rivals' 20-day return |

H1b cannot be "proved" by a test: a return of zero looks like a pass. The weight is on H1
(the gap) and H1a (the sign).

---

## 2. Data

Use the loaders in `scripts/death_test.py` unchanged, except for the one switch below.

**India**
- Returns: adjusted Yahoo closes (`data_processed/nse_prices_clean.parquet`) first; the
  bhavcopy panel as fallback. The fallback is switched to the corrected panel
  `data_processed/nse_survivorship_free_adj.parquet` (KNOWLEDGE_BASE §42).
- The return on 2012-01-02 is set to missing for every stock (it is a 195-day return).
- **Universe:** the 300 largest stocks by 63-day average traded value, lagged one day, as
  in `death_test.py`.
- **Period:** day 0 from 2006-04-01 to 2024-12-31, with 20 trading days of data after it.
- Day 0 from 2011-05-23 to 2012-01-31 is excluded: the panel has a hole there.

**US**
- Returns: raw `data_processed/extended_prices.parquet` with the $1 floor, as in
  `death_test.py`.
- **Universe:** S&P 500 point-in-time members (`us_pit_mask`).
- **Period:** day 0 from 2000-04-01 to 2024-11-30.
- The screen runs over **all** members, including those with no entry in the current
  sub-industry file. This is how firms that later died enter the sample.

**Market return** `m_t`: the equal-weighted mean return of the universe on day *t*.

---

## 3. Selection rule (Stage 2a: the screen)

The screen uses only each stock's own return and `m_t`. It must not compute, print or plot
the return of any other individual stock.

### 3.1 Two ways in

**Arm P, price collapse.**
- For stock *i* on day *t*, the 20-day buy-and-hold abnormal return is
  `B_i(t) = Π(1 + r_i,s) − Π(1 + m_s)` over the 20 trading days ending on *t*. Missing own
  returns count as 0; at least 10 of the 20 must be present.
- The stock triggers on the first day `t*` with `B_i(t*) ≤ −0.50`, if it was in the
  universe on day `t* − 20`.
- After a trigger, the same stock cannot trigger again for 250 trading days.

**Arm X, exit.** For firms that stop trading (suspension, delisting after failure, or in
the US a fall below $1).
- The stock's prices stop, or pause for 20 or more trading days, at least 60 trading days
  before the end of the panel.
- It was in the universe at some point in the 20 trading days before its last price.
- Its buy-and-hold abnormal return over the 60 trading days ending at its last price is
  −30% or worse. This keeps out takeovers and renamings.

If both arms fire for one firm within 60 trading days, it is one event.

### 3.2 Workload cap

- Rank each country's candidates by the failed firm's traded-value rank in the universe at
  the start of its window (largest first).
- Research them in that order. Stop when 30 events per country have passed every exclusion
  in §3.4, or when the list ends.
- The cap may be raised to 60 per country, by continuing down the same list, only before
  Stage 3.
- All candidates, researched or not, are saved in `candidates_india.csv` and
  `candidates_us.csv`.

### 3.3 Day 0 (Stage 2b, from news only)

- Find the **trigger**: the first public report of the event that set off the collapse,
  dated within the 40 trading days up to the trigger day (`t*` for Arm P, the last price
  day for Arm X).
- **Day 0 is the first trading day on which the market could trade on that report.** News
  after the close moves day 0 to the next trading day.
- Day 0 is never chosen as "the worst day nearby".
- If no datable report can be found, day 0 is the first day in the 20-day window on which
  the firm's own abnormal return was −10% or worse. Mark `price_dated = True`.
- If the collapse was slow and the first report is older than 40 trading days, use the
  earliest report inside the window that sources link to the acceleration. Mark
  `ambiguous_date = True`.

### 3.4 Exclusions (each one logged with its reason)

| Code | Excluded because | Decided from |
|---|---|---|
| E1 | Not a real collapse: split, bonus, demerger, rights issue, renaming, takeover, voluntary delisting, bad data | Corporate-action records and news. For India also check `corporate_action_suspects.csv` |
| E2 | Part of an in-sample case (list below) | Dates and tickers |
| E3 | **Industry-wide trigger** (definition below) | News |
| E4 | Day 0 falls in the India data hole | Dates |
| E5 | Fewer than 3 rivals with data (§5) | Industry map and data coverage, not returns |
| E6 | Overlap: another retained event in the same industry had day 0 in the previous 20 trading days. Keep the earlier one | Dates |

If two firms in one industry collapse on the same news, the one with the larger traded
value is the failed firm. The other stays in the rival set, and its return counts as a
rival's outcome.

**E3, industry-wide trigger.** The paper's question is about a firm's *own* crash.
- A trigger is industry-wide when sources describe something that happened to the whole
  industry or market: a law, ruling, tax or regulation aimed at the industry; a commodity,
  currency, interest-rate or demand shock; a pandemic, war or natural disaster; a general
  crash.
- And they report **no** event specific to this firm (its own default, fraud, accident,
  product failure, action by a regulator against it, lost contract, management event,
  earnings shock) as the reason it fell more than the others.
- If sources report both, the firm-specific event decides and the case is kept.
- Reason for the rule: if the shock hits every rival directly, "rivals fall" is true by
  definition and tests nothing (`RESEARCH_NOTE.md` §4c, objection 1).
- E3 cases are listed in a separate table in the paper, with their rival returns, for
  reference. They are not in any test.

**E2, in-sample windows.**

| Case | Excluded tickers | Excluded trigger dates |
|---|---|---|
| Satyam | SATYAMCOMP, Maytas Infra | 2008-12-01 to 2009-03-31 |
| Jet Airways | JETAIRWAYS | 2019-01-01 to 2019-07-31 |
| IL&FS | Any bank, NBFC or housing-finance stock; listed IL&FS companies | 2018-09-01 to 2018-12-31 |
| DHFL | DHFL | Any date to 2019-12-31 |
| Yes Bank | YESBANK and any Indian bank | 2020-02-01 to 2020-06-30 |
| Adani | Any Adani-group stock | 2023-01-01 to 2023-06-30 |
| PG&E | PCG, EIX, SRE | 2018-11-01 to 2019-06-30 |
| SVB | Any US bank | 2023-03-01 to 2023-06-30 |

A different collapse of one of these firms outside its window is allowed. It is flagged
`same_firm_as_in_sample` and dropped in a robustness check.

---

## 4. Classification rule (Stage 2b, from news only)

**Never from rivals' returns.** Use sources dated up to one trading day after day 0 where
possible. A later source may be used only to establish a fact that was public by then.

For each retained event, write one paragraph on the shock (what happened, when it became
public, sources with dates), then answer the checklist. The label belongs to the **rival
set** (§5).

### 4.1 Checklist

**A. Funding channel.** Label **SD-funding** if all of these hold:
- **A1.** The failed firm is a leveraged financial intermediary: bank, NBFC,
  housing-finance company, microfinance lender, broker-dealer or investment bank, insurer,
  mortgage agency, consumer or commercial finance company.
- **A2.** By day 0 (+1), sources report at least one **funding failure** at that firm:
  1. a missed or delayed payment, or a default, on its debt or deposits;
  2. a deposit run, unusual withdrawals, or a limit on withdrawals;
  3. a moratorium, seizure, receivership or conservatorship, a board replaced by the
     regulator on solvency grounds, or a forced or emergency sale, merger or rescue;
  4. failure to roll over short-term funding, emergency liquidity support, or back-up
     credit lines drawn under stress;
  5. a credit rating cut to default, or to below investment grade with funding or
     liquidity given as a reason;
  6. a bankruptcy or insolvency filing.
- **A3.** The rival set consists of intermediaries of the same broad kind.

A financial firm hit by something else (a fraud by staff, a promoter dispute, a conduct
fine, a failed merger, an earnings miss, a trading loss absorbed without funding stress)
does **not** pass A.

**B. Liability or regulatory channel.** Label **SD-liability** if both hold:
- **B1.** The trigger itself is a legal, regulatory or liability event at this firm: a
  court judgment, a liability claim, an accident it is held liable for, a regulator's
  order, a licence or tariff decision, or a bankruptcy caused by such liabilities.
- **B2.** **Rivals are in scope.** Sources at day 0 (+1) report that the same action,
  investigation, liability doctrine, ruling or regime applies to rivals or is being
  extended to them. Examples: rivals named as co-defendants or under the same
  investigation; a liability rule covering every operator in the jurisdiction; a tariff
  or licence regime applied to the whole industry; joint liability.
- Not B2: a sanction for this firm's own conduct (one contaminated plant, one firm's
  mis-selling, one firm's safety breach) with no report on day 0 (+1) that rivals are in
  scope.

**C. Otherwise: OR (output-replaceable).** This includes fraud and accounting scandals,
governance failures, debt distress of a non-financial firm, product failures and recalls,
accidents, lost customers, firm-specific sanctions, forced selling of pledged shares, and
earnings collapses.

**Group affiliates (India) are always SD-owner.** They form their own peer set (§5.2).

### 4.2 Bright lines chosen on purpose

- **Funding dependence counts only between financial intermediaries.** Indian firms almost
  all borrow from the same banks, so "shared lender" would label everything SD. If a
  non-financial firm's default hurts its rivals' access to credit, that case counts
  against the hypothesis.
- **Fraud is OR**, although Gleason, Jenkins & Johnson (2008) show restatements can hurt
  industry peers. If fraud news spreads, that also counts against the hypothesis.

### 4.3 Flags

- `ambiguous = True` when sources disagree, when a criterion rests only on a source dated
  after day 0 (+1), or when B2 is arguable. Give the reason in one line.
- `fin = 1` when the failed firm's sector is financial: GICS Financials in the US (banks,
  capital markets, consumer finance, insurance, exchanges, asset managers; not real
  estate); NSE "Financial Services" in India. `fin` is a sector flag. It is broader than
  A1.
- `rank_news`: the failed firm's size rank in its industry as stated in news at the time
  (`leader`, `top3`, `other`, `unknown`).

---

## 5. Peer sets (Stage 2b, fixed before any rival return)

### 5.1 Rival set R

Same industry, same universe, no hand-picking.

**US.**
- All S&P 500 point-in-time members on day −1 with the failed firm's GICS sub-industry.
- Source: `data_raw/sp500_constituents/sp500_subindustry.csv` for current members.
- For members missing from that file (most dead firms), build
  `docs/entropy_research/prereg/us_subindustry_supplement.csv` from public sources: the
  sub-industry the firm's main business would have under today's GICS.
- For each US event, every unmapped member on day −1 gets at least a sector. Those in the
  failed firm's sector get a sub-industry. Without this step the rival sets would contain
  survivors only.

**India.**
- All stocks with data in the combined India panel (§2) on day −1 with the failed firm's
  industry.
- Source, in order: NSE "Basic Industry"; else Yahoo Finance "industry"; else the main
  business in exchange filings (for delisted firms). The failed firm and its rivals must
  be classified from the same source.
- Save the map as `docs/entropy_research/prereg/nse_industry_map.csv`.
- If more than 10 rivals qualify, keep the 10 with the highest 63-day average traded value
  on day −1.

**Both.**
- A rival needs more than 100 valid returns in the 250 trading days before day 0.
- Group affiliates, parents and subsidiaries of the failed firm are removed from R.
- Fewer than 3 rivals: widen once to the next level up (GICS industry; NSE "Industry") and
  mark `widened = True`. Still fewer than 3: exclude (E5).

### 5.2 Group set G (India)

- All stocks in the panel on day −1 that belong to the failed firm's promoter group: named
  as promoter-group companies, parent, subsidiaries or fellow subsidiaries in shareholding
  filings or annual reports, or failing those, in news dated before day 0 (+1).
- One affiliate is enough. Record the source.

---

## 6. Outcome

For each event and each peer set:

- **Primary outcome `y`:** the mean, across peers, of the 20-day buy-and-hold abnormal
  return over days 0 to +20: `Π(1 + r_peer) − Π(1 + m)`. Computed exactly as `bhar` in
  `death_test.py::run_case`, with the market built from universe members on day 0,
  excluding the failed firm and every stock in R or G.
- **Second benchmark (beta-adjusted):** the same with `m` replaced by `β·m`, where each
  peer's β comes from a regression of its return on `m` over days −260 to −21 (at least
  100 observations).
- **India only:** a peer's one-day move beyond ±45% is set to missing and logged, as in
  `run_case`. Any such removal inside days 0 to +20 is listed, and the result is shown
  with the move restored.
- **Descriptive only:** day 0; days 0 to +5; days −20 to −1 (was it priced in early?);
  days −20 to +20.

---

## 7. Tests and verdicts

**Primary sample:** all retained events, India and US pooled, rival sets only. `L` is SD
(SD-funding or SD-liability) or OR. Random seed 20261110.

| Test | Statistic | How the p-value is computed |
|---|---|---|
| **T1** (H1) | `D` = mean `y` of SD events − mean `y` of OR events; predicted negative | One-sided permutation test: shuffle labels across events (100,000 shuffles, or every arrangement if fewer) |
| **T2** (hit rate) | Share of events with the predicted sign (SD: `y < 0`; OR: `y ≥ 0`) | Same shuffles. This allows for the base rate; in Part A rivals were down after 20 days in 55% of crashes |
| **T3** (H1a, H1b) | Mean and median `y` in each class | Bootstrap 90% interval (10,000 resamples of events) |
| **T4** (H2) | See §7.1 | Shuffles within the financial and non-financial halves |
| **T5** (H3) | `y_G − y_R` for Indian events with a group set; predicted negative | Sign-flip permutation test and a sign test. Also mean `y_G` |
| **T6** (H4) | Spearman correlation of `y` with the failed firm's share; mean `y` by `rank_news` | Two-sided permutation test |

Share for T6: the failed firm's 63-day average traded value on day −1, divided by that of
the firm plus all same-industry stocks.

### 7.1 The financial versus non-financial split (H2)

The worry: SD-funding can only occur at financial firms, so "shared dependency" may be
"financial firm" renamed.

1. **The 2×2 table.** Count and mean `y` for each of SD/OR × financial/non-financial.
2. **Inside each half.** `D_fin` and `D_nonfin`, each with its own permutation p-value.
   - Financial half: SD-funding events against financial firms that collapsed for other
     reasons (fraud, governance, conduct).
   - Non-financial half: SD-liability events against OR events.
3. **Stratified test.** The weighted average of `D_fin` and `D_nonfin`, weights
   `n_SD × n_OR / n` in each half. Labels are shuffled only within a half, so the test
   cannot be passed by the financial flag alone.
4. **Horse race.** The hit rate of the label against the hit rate of the dumb rule
   "`fin = 1` ⇒ rivals fall, `fin = 0` ⇒ they do not". Also the regression
   `y = a + b·SD + c·fin`, with a permutation p-value for `b`.
5. **Non-financial evidence from groups.** T5 restricted to non-financial failed firms
   whose rival set is OR: affiliates predicted below 0, rivals at or above 0.

A half counts as **informative** only if it has at least 4 events of each label.

### 7.2 Verdict wording, fixed now

Each verdict uses the **larger** (less favourable) of the two p-values from the
market-adjusted and beta-adjusted outcomes.

| Result | The paper will say |
|---|---|
| T1: `D < 0`, p ≤ 0.05 | "Supported out of sample" |
| T1: `D < 0`, 0.05 < p ≤ 0.15 | "Weakly supported" |
| T1: p > 0.15, or `D ≥ 0` | "Not supported out of sample" |
| Fewer than 5 events in either class | "Too few cases to test"; numbers reported without significance claims |
| T4 stratified: p ≤ 0.10 and `D_nonfin < 0` with the non-financial half informative | "The label adds to 'financial firms are special'" |
| T1 passes but that does not | "In this sample the dependency label cannot be told apart from a financial-sector flag" |
| T6: p ≤ 0.10 | "Market share is related to the rival reaction", with the sign. The title claim is weakened to match |
| T6: p > 0.10 | "No evidence that market share, as measured here, explains the rival reaction" |

Every result is reported, including nulls and results with the opposite sign.

---

## 8. Robustness checks, fixed now

All are reported in one table, whatever they show. None can change a verdict in §7.2.

1. India only; US only.
2. Without 2008–09 and 2020.
3. Without events whose days 0 to +20 saw the market fall more than 10%.
4. Without `price_dated` and `ambiguous_date` events.
5. Without `ambiguous` labels; then with those labels flipped.
6. With the blind second coder's labels (§9).
7. Without `in_part_a` and `same_firm_as_in_sample` events.
8. Arm P only.
9. Medians, and `y` capped at ±50%.
10. At most one event per sector per 20 trading days.
11. `widened` rival sets removed.
12. Windows of days 0 to +5 and days 0 to +40.

---

## 9. Safeguards

**The script enforces the order.** `scripts/death_test_oos.py` has two commands:
- `screen` writes `results/death_test_oos/candidates_{india,us}.csv`. It reads only the
  candidate's own returns and `m_t`.
- `test` refuses to run unless `PREREGISTRATION.md` and everything in
  `docs/entropy_research/prereg/` are committed and unmodified. It writes the commit hash
  and the SHA-256 of `cases.csv` into `results/death_test_oos/summary.json`.

**What counts as peeking.** Computing, plotting or reading the return of any individual
rival or affiliate, from day −20 of a candidate event onward, before the Stage 2 commit.
The market average is allowed.

**Hindsight in the labels.** The coder knows how famous collapses ended. Three defences:
1. The checklist asks for facts that were public on day 0, each with a dated source.
2. **Blind second coder.** Each shock paragraph is stripped of names, tickers, places,
   dates and currency, and given with §4 to a second coder who sees nothing else: a
   language model in a fresh context, and Mrigay if he has time. Their labels are
   committed before Stage 3. The paper reports the agreement rate and Cohen's kappa, and
   robustness check 6 reruns the tests on their labels.
3. A model may still recognise an anonymised case. This is stated as a limitation.

**Who labels.** Labelling is judgement, not mechanical work. If a smaller model drafts the
labels, a stronger model or Mrigay reviews them before the Stage 2 commit, also without
rival returns.

**Stage 2 files** (all in `docs/entropy_research/prereg/` unless noted):

| File | Content |
|---|---|
| `cases.csv` | One row per retained event (columns below) |
| `PREREGISTRATION_CASES.md` (one level up) | The shock paragraph, sources and checklist answers for each event; the E1–E6 log; the E3 list |
| `us_subindustry_supplement.csv`, `nse_industry_map.csv` | Industry maps used for rival sets |
| `second_coder_labels.csv` | Blind labels |

`cases.csv` columns: `event_id, market, firm, arm, trigger_day, day0, news_date, trigger_summary, source_urls, price_dated, ambiguous_date, fin, a1, a2, a2_fact, b1, b2, label_R, ambiguous, ambiguous_reason, rank_news, industry, industry_source, widened, rivals, affiliates, affiliate_source, in_part_a, same_firm_as_in_sample, coder`.

---

## 10. What this test can and cannot show

- **Power.** In Part A the 20-day rival return had a standard deviation of 7.6% across
  events. Collapses are noisier; assume about 10%. With about 10 SD and 30 OR events, the
  test finds a true gap of 10 percentage points roughly four times in five. A gap of 5
  points would be found less than half the time.
- The in-sample gaps were 20 points or more, but those cases were hand-picked.
- **So a null result means "no large effect", not "no effect".**
- **A positive result shows prediction, not cause.** It cannot say whether the collapse
  damaged the rivals or revealed a weakness they shared.
- Rivals that stop trading inside the window are held at their last price, which
  understates their loss. This works against H1a.
- "Market share" in T6 is a share of trading value, not of revenue. `rank_news` is a
  second, coarse measure.

---

## 11. Where this differs from the sketch in `NEXT_SESSION_PROMPT.md`

| Sketch | Here | Why |
|---|---|---|
| "…or defaulted, or was suspended" | Defaults and suspensions enter only through Arm P or Arm X | There is no default database. A hand-made list would bring back after-the-fact selection |
| All collapses | Industry-wide triggers excluded (E3) | Otherwise SD is true by definition |
| One label per case | The label belongs to the rival set; group affiliates are a separate set | It allows the contrast inside one event (H3) and stops the peer group being chosen to fit |
| Prediction: SD < 0, OR ≥ 0 | Main test is the gap; the OR sign cannot be proved | A zero return would count as a pass |
| One benchmark | Verdict needs both market-adjusted and beta-adjusted results | Collapses cluster in crashes, when bank stocks fall more than the market anyway |
| One commit | Rules now, cases in a second commit | No price files in the drafting session |
| All cases | Capped at 30 per country, largest first | Each case needs research; the cap is mechanical and fixed in advance |

---

## 12. The checklist applied to the eight in-sample cases (illustration only)

These show how the checklist reads. They are not evidence: the checklist was written
knowing these outcomes.

| Case | `fin` | Checklist | Label for rivals | Rivals' 20-day return in §4b |
|---|---|---|---|---|
| Satyam 2009 | 0 | Fraud confession: not A1, not B1 | OR | +12.6% |
| Jet Airways 2019 | 0 | Grounded when cash ran out: non-financial debt distress | OR | about 0 |
| IL&FS 2018 | 1 | A1 lender; A2 default | SD-funding | −14.8% |
| DHFL 2019 | 1 | A1 lender; A2 missed payment | SD-funding | −0.8% |
| Yes Bank 2020 | 1 | A1 bank; A2 moratorium | SD-funding | −19.5% |
| Adani 2023 | 0 | Short-seller fraud allegations: not A1, not B1 | OR (group set: SD-owner) | +7.7% (group −42%) |
| PG&E 2019 | 0 | B1 bankruptcy over fire liability; B2 the doctrine covers every California utility | SD-liability | −6.7% |
| SVB 2023 | 1 | A1 bank; A2 run and seizure | SD-funding | −24.5% |

Note the two weak in-sample fits under the mechanical rule: DHFL 2019 and Jet Airways are
both close to zero.

---

## 13. Order of work from here

1. Switch the bhavcopy fallback in `death_test.py` to the `_adj` panel, re-run it, and
   note any change in the eight in-sample cases (a data ground rule, still open).
2. Write `scripts/death_test_oos.py` with the `screen` command only. Run it. Commit the
   candidate lists.
3. Research candidates in rank order (§3.2): E1–E6, day 0, shock paragraph, checklist,
   rivals, affiliates. Build the two industry maps.
4. Get the blind second coder's labels.
5. Have the labels reviewed (§9), then commit and push everything in §9's file table.
   **This is the Stage 2 commit.**
6. Only now add the `test` command, run it, and report every number in §7 and §8.

