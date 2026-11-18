# Paper 3, next level: "How many bets should you make?"

*Written 17 Nov 2026. Paste everything below the line into a new Claude Code session
opened in `~/Desktop/trading app/strategyhub-research`. Suggested model: Opus at high
effort. Use a Sonnet subagent only for mechanical downloads.*

---

You are working with Mrigay Pathak (he/him), an IU finance and informatics senior, on
the next stage of paper 3.

**Read first, don't redo:**
- `docs/entropy_portfolio/NOTE.md`, `THEORY.md`, `PROPOSAL.md`, `REFEREE_RESPONSE.md`;
- KNOWLEDGE_BASE §46.

**Paper 3 so far:**
- **Theory.** A signal tilts 1/N along one direction, so the investor estimates one
  unknown. The knowledge share is c = t²/(1+t²), where t is the t-statistic of the
  signal's IC. Mapped through the Gibbs (maximum-entropy) dial, this gives a predicted
  optimal effective N.
- **Real data** (3 signals, top-100 India, S&P 500 US):
  - the direction held (Spearman −0.89, descriptive);
  - the amount over-concentrated in 6 of 6 cases;
  - nothing beat 1/N significantly;
  - the simulation says 300–1,000 months are needed;
  - the holdout signals lost their information.

## The upgrade (why this stage exists)

Paper 3 tested one rule on 3 signals in 2 small universes. That is too narrow and too
underpowered to interest a finance professor.

**This stage's question:** *every quant makes the same choice at two levels: how many
stocks to hold inside a strategy, and how many strategies to hold in a fund. Does one
evidence-matched rule ("hold as much entropy as you have ignorance") get both right
across the whole published factor zoo?*

**Why this is stronger:**
1. **Generality.** It covers about 200 published strategies of every type, not 3.
2. **A natural experiment.** Academic publication is a dated, outside shock to a
   signal's information: McLean & Pontiff (2016) find returns fall after publication.
   The rule predicts *how much* more diversified an investor should become after
   publication. That fixes paper 3's weakest point, that information was measured
   after the fact.
3. **Power.** It comes from the cross-section of signals and from history back to the
   1960s or earlier, not from 124 months.
4. **Applications:**
   - multi-strategy funds: how much capital to concentrate in the best-evidenced
     strategies;
   - multi-factor products: how many factors to hold;
   - backtest sizing: turning "t = 2.5" into "hold about X names";
   - crowding: how far to de-concentrate once a strategy is known.

**Market focus: the US is primary.** India is a replication market reported alongside.

## Phases (commit after each; push at the end of each phase)

**Deadline.** By **Thursday 19 Nov 2026, 6 pm**, the "Friday pack" (Phase 5) must exist,
even if some runs are unfinished. Order the work so that it does.

### Phase 0: novelty check (short; stop condition)

Write `docs/entropy_portfolio/LITERATURE_2.md`, verifying each item against a primary
source:
- McLean & Pontiff 2016;
- Harvey, Liu & Zhu 2016;
- Kozak, Nagel & Santosh 2020;
- Feng, Giglio & Xiu 2020;
- DeMiguel, Martín-Utrera, Nogales & Uppal 2020;
- Jensen, Kelly & Pedersen 2023;
- Chen & Zimmermann 2022;
- Gupta & Kelly 2019;
- Ehsani & Linnainmaa 2022;
- Haddad, Kozak & Santosh 2020;
- anything on 1/N across factors or strategies.

If either of these already exists, **stop and report to Mrigay**:
- a rule mapping a signal's evidence to the number of bets held;
- a test of post-publication de-concentration.

Otherwise, state the gap in one paragraph.

### Phase 1: raw data (free first)

1. **Chen & Zimmermann, Open Source Asset Pricing** (openassetpricing.com, release Oct
   2025, data to Dec 2024): long-short **and decile** portfolio returns for each
   predictor, plus `SignalDoc.csv` (publication year, original sample end). Verify that
   decile-level returns are published.
2. **Jensen, Kelly & Pedersen Global Factor Data** (jkpfactors.com; zipped CSVs on a
   public bucket): US factors (primary), India and other markets (replication).
3. **Kenneth French library** 1926+ as a cross-check.

Rules for the download:
- Record URL, date and SHA-256 for every file in `results/entropy_portfolio_2/DATA.md`.
- Store raw files under a git-ignored `data_raw/` folder. Commit the download script and
  derived results, not the raw files.
- If both free sources fail, fall back to French portfolios (49 industries, 100
  size/book-to-market, momentum deciles) and say so.

**WRDS pull spec.** Write `docs/entropy_portfolio/WRDS_PULL_SPEC.md` for the stock-level
version, which needs CRSP through Kelley's WRDS access. List:
- the exact tables and variables:
  - CRSP monthly stock file with delisting returns;
  - S&P 500 membership history;
  - Compustat annual;
  - the CRSP–Compustat link.
- filters, date ranges and expected sizes, so Mrigay can pull everything in one
  sitting.
- whether CRSP's legacy tables or the newer CIZ format is current.

### Phase 2: theory v2 and power

Extend `THEORY.md` (new sections; never rewrite the frozen ones):
- **Within-strategy level:** the Gibbs dial over a predictor's decile portfolios (a free
  pilot of the stock-level test), with the predicted optimal effective N by the
  predictor's ex-ante IC t-stat.
- **Across-strategy level:** N predictors as assets, with the signal being each
  predictor's ex-ante evidence (its own past t-stat, or the published t-stat with a
  stated haircut). The IC is the cross-predictor link between past evidence and future
  return (see the factor-momentum literature).
- **Publication shock:**
  - take the post-publication decay from McLean–Pontiff as an *ex-ante* input;
  - derive the predicted change in optimal effective N at publication, as a number.
- **Paper 3's blind spot:** add a sector- or factor-residual concentration cost. Predict
  how much it removes the over-concentration bias, and check that against paper 3's
  frozen results, labelled post hoc.
- **Power:**
  - recalibrate the simulation to the *measured* IC noise (about 4× paper 3's σ_ρ);
  - compute the power of each planned test;
  - any test with power below 0.5 becomes descriptive in the pre-registration.

### Phase 3: pre-registration

Commit `docs/entropy_portfolio/PREREGISTRATION_2.md` before any result. It must fix:
- hypotheses at both levels, plus the publication test;
- signals, windows, costs and tests:
  - Sharpe tests with Jobson–Korkie–Memmel and Ledoit–Wolf;
  - Hansen SPA and PBO for multiple testing;
  - a TOST equivalence test against 1/N;
  - clustering by month and by predictor.
- **Holdouts**, chosen before seeing any result:
  - prefer a *geographic* holdout (non-US markets from the Jensen–Kelly–Pedersen data,
    India reported separately);
  - add a US time holdout only if it doesn't leave the publication test underpowered.
- **What has already been seen:** paper 3's 2021–2025 stock-level holdout. List it in
  the pre-registration.

### Phase 4: US run (in-sample), then holdouts once

- Report everything, including nulls.
- Log any unavoidable change as a dated deviation.

### Phase 5: the Friday pack (by Thursday 6 pm)

1. **`docs/entropy_portfolio/PROPOSAL_2.md`**: two pages, US first, readable by a
   non-specialist in the first half. Two figures (load the dataviz skill first):
   1. "How many bets?": out-of-sample utility against effective N by evidence level,
      with the theory's optimum marked;
   2. before vs after publication.
   
   It ends with what a semester would add:
   - the CRSP stock-level test;
   - supervision;
   - the specific ask: WRDS access under a faculty sponsor.
2. **`docs/entropy_portfolio/MEETING_BRIEF.md`**: one page. Three sentences on the idea,
   the strongest honest result, what is still unknown, and the ask.
3. **Private drafts.** Update the meeting and email drafts in `docs/outreach/`. That
   folder is git-excluded: **never commit it, and send nothing.**

### Phase 6 (after Friday)

- Holdout runs.
- India and international replication.
- A CRSP-ready stock-level script, tested on French data, so it runs the day the WRDS
  files land.
- A fresh-subagent referee report on the NOTE, with fixes.
- Traceability: every number checked against `results/`.
- kbpr: a new KB section and your own PROGRESS_REPORT lines only.
- `STUDY_GUIDE.md` Part 11, covering the factor zoo, post-publication decay, the
  two-level rule, and professor Q&A.

## What will show the result is right (not you, not Mrigay)

- The predicted publication shift, matched in the data.
- The rule working at both levels with one formula.
- A geographic holdout.
- Power computed before the run.
- One-command reproducibility from the public repo.

## Ground rules

- **Git:**
  - commit locally as often as useful;
  - push only at the end of each phase and before stopping, never after every commit;
  - commit your own files by explicit path; other sessions share this checkout;
  - never add or touch CI or GitHub Actions.
- **The repo is public:**
  - nothing from `docs/outreach/` or `~/Desktop/NIAIF/`;
  - no personal details in any committed file;
  - no raw third-party data files.
- **Python:** `~/.venvs/strategyhub/bin/python` (numpy 1.24, pandas 2.0.3 with `M`/`Q`
  resample codes, scipy 1.11). The project `.venv` is iCloud-evicted. sklearn, cvxpy
  and statsmodels are absent, and pip installs have hung before, so reuse
  `scripts/ep_lib.py`. Use fixed seeds.
- **iCloud:** check big files with `ls -lO` and skip "dataless" stubs.
- **Usage:**
  - at most one subagent at a time;
  - no Workflow tool or ultracode;
  - commit before each long step so a usage cap loses nothing.
- **Honesty:**
  - pre-register before results;
  - say "consistent with", never "proves";
  - a failed prediction is a result.
- **Stop and ask Mrigay only if:**
  - Phase 0 finds the idea taken;
  - all free data sources fail.
- **Finish with** a plain-language summary for Mrigay:
  - what the work now claims, what held and what failed;
  - the one sentence to say at Friday's meeting.
