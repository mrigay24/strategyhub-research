# Prompt for the next session (paste everything below the line)

---

You are continuing a research paper project in `~/Desktop/trading app/strategyhub-research`
(Python 3, pandas 2.0.3, venv at `.venv/`; always run `.venv/bin/python`). The goal is a
finished **10–15 page working paper** within 2–3 days, good enough to send to professors.
It is not a journal submission.

Read first, in order:
1. `docs/entropy_research/RESEARCH_NOTE.md`. Sections §4b and §6 hold the decided paper
   question and the current results. Everything before them is background.
2. `scripts/death_test.py`: the US sub-industry death test (Part A) and the 8 case
   studies (Part B).
3. `results/death_test/` (`run.log`, `cases.csv`, `cases_peers.csv`,
   `us_replaceability_map.csv`, `summary.json`).
4. `scripts/entropy_research.py` and `results/entropy_research/`: the earlier pilot,
   which becomes appendix material.

## The paper (decided — do not reopen the question)

**Working title:** *Market Share Is Not Importance: What Happens to Rivals When a Firm
Dies (US and India).*

**Question:** when a company suffers its own crash, do its rivals gain or lose, and does
its market share explain which?

**Current evidence:**
- In the US, peers share the day-0 hit (−1.2%, t −7.6), more so when the crashing firm
  has a large share, but it fades within 20 days.
- Industry identity explains about 10× more than share or HHI.
- In 8 famous collapses (Satyam, Jet Airways, Adani, IL&FS, DHFL, Yes Bank, PG&E, SVB),
  damage spread only where peers shared a **critical dependency** with the failed firm:
  funding, deposits, owner, or liability/regulator. Where the firm's output was
  replaceable (IT services, airline seats, cement/power), rivals gained or were
  unaffected.

**Weakness to fix:** the 8 cases were chosen after the fact, so the dependency labels
could be story-fitting.

## Ground rules

- **Git:** commit locally as often as useful. Push only at the end of each phase, never
  after every commit, and always push before stopping. The repo is public; Mrigay has
  approved pushing this work.
- Never touch CI or GitHub Actions.
- **Data:**
  - US crashes: use the RAW `data_processed/extended_prices.parquet` with the $1 floor.
    The clean file's 20% filter deletes real crashes.
  - India: the original `nse_survivorship_free.parquet` is missing split/bonus
    adjustments (CHOLAFIN 2019 shows −80%, INFY bonuses show −50%). A corrected panel now
    exists: `data_processed/nse_survivorship_free_adj.parquet` (built by
    `scripts/build_nse_adjusted_panels.py`; see KNOWLEDGE_BASE §42). First switch the
    bhavcopy fallback in `death_test.py`'s combined loader to the `_adj` file, re-run
    `death_test.py`, and note any change in the 8 India/US case numbers. Keep the loader
    order (adjusted Yahoo closes first, bhavcopy as the fallback) and the ±45% peer filter
    with logging. INFY is still missing before 2012 and SPICEJET before 2020.
  - Day 0 = the first trading day after the news is public, never "the worst day nearby".
- **iCloud:** the Desktop is iCloud-synced, and some files are cloud-only stubs that hang
  when read (check with `ls -lO | grep dataless`). Avoid
  `data_raw/nse_bhavcopy_panel.parquet`, `data_raw/nifty500_index.parquet` and
  `data_raw/sp500_constituents/sp500_pit_monthly.csv`.
- **Honesty:** report every null or opposite result in the note and in the paper.
  Mrigay is learning, so explain each result in plain language.
- **Usage:** use at most one subagent at a time. Use Sonnet for mechanical work and Opus
  for design and logic.
- After each phase, update `RESEARCH_NOTE.md`, plus `KNOWLEDGE_BASE.md` and
  `PROGRESS_REPORT.md` ("kbpr").

## Phases (commit after each; push at the end of each)

**Phase 1 — Literature check (web search, no code).**
- Verify every reference in the note's §5 table: authors, year, journal and the
  one-line finding. Fix what's wrong.
- Then search for work on:
  - contagion through *shared dependencies* (common funding, common creditor, deposit
    runs, business groups / tunnelling in India);
  - Indian studies of IL&FS, Yes Bank and Adani spillovers.
- Write an honest "Is this new?" paragraph: what exists, and what this paper adds.

**Phase 2 — Pre-registered out-of-sample test (the most important phase).**

Before computing any peer returns, write `docs/entropy_research/PREREGISTRATION.md` and
**commit it**; the git timestamp is the proof. It must contain:
- **(a) Selection rule.** Every India collapse 2006–2024 in the NSE panel: a stock in
  the top 300 by traded value that fell more than 50% abnormally within 20 trading days,
  or defaulted, or was suspended, and that has at least 3 identifiable listed rivals.
  Add a US equivalent from S&P 500 members. Exclude the 8 cases already used.
- **(b) Classification rule.** Decide from news descriptions only, never from peer
  returns. Label the case **"shared dependency"** if the peers share with the failed
  firm a funding source or depositor base, an owner (business group), or a
  liability/regulatory event. Otherwise label it **"output-replaceable"**. Write a
  one-paragraph description of each shock (web search for the cause), then label it.
- **(c) Prediction.** Peer 20-day buy-and-hold abnormal return is below 0 for
  "shared dependency" cases and at least 0 for "output-replaceable" cases.
- **(d) Test.** Hit rate, the difference in means, and a permutation p-value.

Then run it with a new `scripts/death_test_oos.py`, reusing the functions in
`death_test.py`. Report the result whatever it is.

**Phase 3 — Robustness of Part A.**
- Crash thresholds of −10% and −20%.
- Standard errors clustered by date, and bootstrap confidence intervals.
- Excluding 2008–09 and 2020.
- Sector-level peers instead of sub-industry.
- Try to add sub-industries for delisted S&P firms (yfinance `.info`, where it works), so
  that true deaths enter the sample.

Put a robustness table in `results/death_test/robustness.csv`.

**Phase 4 — Figures.** Load the `dataviz` skill first. Make:
1. event-time cumulative abnormal return lines (days −20 to +20), one small panel per
   case, rivals vs group/dependent peers;
2. a replaceability-map bar chart by sub-industry;
3. the market-share tercile chart.

Save them as PNGs in `results/death_test/figures/`.

**Phase 5 — Write the paper.**
- `docs/entropy_research/PAPER_DRAFT.md`, 10–15 pages:
  - abstract;
  - introduction (the Zero to One motivation in two sentences, then the question);
  - framework (entropy, HHI, replaceability, the death test, the dependency
    hypothesis);
  - data;
  - US evidence;
  - case studies;
  - pre-registered out-of-sample test;
  - robustness;
  - implications for investors (the high-entropy portfolio of low-entropy firms);
  - limitations;
  - conclusion;
  - appendix (Tests 1–2 from `entropy_research.py`);
  - references.
- Export it to `.docx` using the docx skill.
- Then write `docs/entropy_research/ONE_PAGER.md`: one page, plain English, one table,
  one figure reference.
- Then write `docs/entropy_research/EMAIL_DRAFTS.md`: three short draft emails (to a
  Kelley finance professor, a Tsinghua professor at IU, and Mrigay's uncle at NTU, whose
  field is sustainability). Each leads with one finding and asks one specific question.
  **Drafts only: never send anything.**

**Phase 6 (only if time remains) — AI "death test".**
- Give an LLM only the shock descriptions from Phase 2 and ask it to classify each case
  with the same rule.
- Compare its labels with the human labels and with the outcomes.
- Explain the look-ahead problem: the model may already know what happened.

Finish by updating the note, running kbpr, committing and pushing, then give Mrigay a
plain-language summary: what the paper now claims, what held up, what didn't, and what
he should read or do before emailing anyone.
