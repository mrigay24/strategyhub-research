# Paper 2 pilot: business groups and hidden concentration (India)

*Written 11 Nov 2026. A Claude session follows this plan; Mrigay reads it to follow along.*

## The idea in one paragraph

Paper 1 (`docs/entropy_research/PAPER_DRAFT.md`) found two things:
- A failed firm's **market share** does not predict how its rivals react.
- The one channel that kept showing up was **shared ownership**. All 3 Indian
  business-group sets fell together after a group firm collapsed (Anil Ambani group
  −37.5% and −9.9%, Indiabulls −36.5%), and the Adani group fell −42% while outside
  rivals gained. Three sets were too few to prove anything.

Separately, a real Indian small-cap fund (Nippon India Small Cap, from the NIAIF
portfolio-analytics project) holds 186 effective stocks but only ~53 effective
industries and ~12 sectors, and moves about 1:1 with the market. It is diversified
across names, not across shocks.

The hypothesis:

> **Count groups, not stocks.** Stocks that share a promoter group crash together *more
> than their calm-period price correlation predicts*. If so, an entropy measure built
> from **who owns what** (group-level effective N) reveals hidden concentration that
> correlation-based risk tools miss in calm markets.

This brings entropy back to the centre. The main variable is effective N = exp(H),
H = −Σ w ln w, at the stock, industry and business-group levels, compared with the
standard correlation-based measure (Meucci's "effective number of bets").

Pilot Test 2 (`docs/entropy_research/RESEARCH_NOTE.md`) already found that calm,
high-entropy periods came before deeper drawdowns. That is why a structural,
non-price measure might add something.

## Go / no-go

The pilot answers one question before any bigger paper is built:

> **Do same-group stocks share crashes more than same-industry stocks that are not in
> a group, after controlling for their calm-period correlation?**

- **Go:** the same-group effect is negative and significant after the calm-correlation
  control, by the rule fixed in the pre-registration. Then design the portfolio-level
  test (Phase 5).
- **Stop:** calm correlation explains the co-crashes, so ownership adds nothing. Write a
  short honest note and stop. That is a useful result too.

## Phases (commit after each step)

**Phase 0 — Read (no code).**
- `docs/entropy_research/PAPER_DRAFT.md`: abstract, §6.3 (H3, business groups), §9.
- `docs/entropy_research/RESEARCH_NOTE.md`: Test 2 and §5 (literature).
- `scripts/death_test.py`: reuse its loaders and event logic.
- The NIAIF inventory: `~/Desktop/NIAIF/portfolio analytics/docs/ENTROPY_DATA_INVENTORY.md`.
  This is read-only; that project belongs to Mrigay. **Never open
  `Cashflow_June 26_Final.xlsx`**, which is confidential.

**Phase 1 — Literature check (web search).**
Find what already exists on:
- (a) business-group stock comovement and contagion: India (Khanna & Palepu 2000;
  Bertrand, Mehta & Mullainathan 2002), Korean chaebols, and others;
- (b) entropy and effective-N diversification measures, including Meucci (2009),
  "Managing Diversification";
- (c) ownership-based fragility (Greenwood & Thesmar 2011; Coval & Stafford 2007).

Write a short "Is this new?" section. **If someone has already run this exact test,
stop and tell Mrigay before continuing.**

**Phase 2 — Build the group map, before computing any returns.**
- Universe: NSE stocks in the top 500 by 63-day traded value at any month-end
  2005–2025. Use the corrected panel `data_processed/nse_survivorship_free_adj.parquet`.
- The panel has only `date, symbol, OHLCV`: no ISIN and no names. Watch for symbol
  renames.
- Map each symbol to its promoter group, with a source per group:
  - NSE/BSE shareholding-pattern filings (promoter and promoter-group names);
  - group websites and annual reports;
  - Wikipedia lists of group companies.
- Record membership changes with dates where known: splits (Reliance 2005), sales,
  acquisitions. "Standalone" is a valid label.
- Use at most one subagent at a time; Sonnet is fine for this lookup work. Spot-check
  its output.
- Save `results/group_dependency/group_map.csv` with columns symbol, group, start, end,
  source, and notes.
- Also attach an industry to each symbol (NSE/AMFI industry, or GICS-like where
  available).
- **Commit the map before Phase 4.**

**Phase 3 — Pre-registration.**
Write `docs/group_dependency/PREREGISTRATION.md` and commit it before computing any test
statistic. Follow the protocol used for paper 1. It must fix:
1. **Events:** idiosyncratic crashes of a group firm, using the death-test rule
   (`death_test.py` Part A thresholds adapted to India).
2. **Comparison sets:**
   - **group siblings** in *other* industries;
   - **industry rivals** in *other* groups or standalone;
   - optionally, siblings in the same industry, kept separate.
3. **The control:** each pair's calm-period correlation, meaning the trailing 252-day
   abnormal-return correlation ending 10 days before the event, plus size and
   liquidity.
4. **Outcomes:** day-0 and days 0–20 abnormal return (CAR and BHAR), as in paper 1.
5. **The test:** a regression of the outcome on a same-group dummy, a same-industry
   dummy and the calm correlation.
   - Standard errors clustered by event and by date.
   - A permutation or bootstrap by event.
   - The **go/no-go rule** stated in advance.
6. **A secondary measure:** excess tail dependence, i.e. how often a pair is jointly in
   the worst 5% of days, against what a model with the calm correlation predicts.
7. **Exclusions and robustness**, stated in advance:
   - with and without 2008–09 and 2020;
   - with and without the Adani / Anil Ambani episodes already used in paper 1.

**Phase 4 — Run the pilot.**
- Use the new `scripts/group_dependency_pilot.py`, reusing the `death_test.py`
  functions.
- Report every number, including the ones against the hypothesis.
- Apply the go/no-go rule exactly as registered.

**Phase 5 — Only if GO: design the portfolio test (design only, no results).**
- **Portfolios:** random portfolios from the universe.
- **Compare:** effective N at the stock, industry and group levels, and Meucci's
  effective number of bets from trailing covariance.
- **Outcome:** drawdowns in crisis windows (2008, 2013, 2018 IL&FS, 2020, 2024 small-cap).
- **Illustration:** the Nippon India Small Cap Fund, using holdings rebuilt from Nippon's
  free public monthly portfolio files. The NIAIF copies are paid ICRA exports and must
  not be published.
- Write it as a second pre-registration draft for Mrigay to approve.

**Phase 6 — Write-up.**
- Add `docs/group_dependency/NOTE.md` covering the idea, literature, data, group map,
  pre-registered test, result, the go/no-go decision and limitations, in plain language.
- Update KNOWLEDGE_BASE.md and PROGRESS_REPORT.md (kbpr).
  - Commit only your own hunks of PROGRESS_REPORT.md. Mrigay has older uncommitted
    edits there.
- Then give Mrigay a short plain-language summary: the result, the decision, and what
  he should do next.

## Rules

- **Git:** commit locally as often as is useful, and push only at the end of a phase,
  never after every commit. **The repo is public and this is new research, so ask
  Mrigay before the first push.** After he agrees, push at the end of each phase and
  always before stopping. Never touch CI or GitHub Actions.
- **Data:**
  - Use the corrected NSE panel (`_adj`, or `_adj_nohole` for anything touching
    2011-H2).
  - Never use NIAIF's unadjusted `market_cache.db`.
  - Use `pct_change(fill_method=None)`; drop one-day moves beyond ±45% as likely
    corporate actions, and log them.
  - Day 0 = the first trading day after the news.
- **iCloud:** the Desktop is iCloud-synced. Check files with `ls -lO <dir> | grep
  dataless` and skip cloud-only stubs. Known stubs:
  `data_raw/nse_bhavcopy_panel.parquet`, `data_raw/nifty500_index.parquet`,
  `data_raw/sp500_constituents/sp500_pit_monthly.csv`.
- **Honesty:** report nulls and opposite results. Never change the group map or the
  rules after seeing returns; if a change is unavoidable, log it as a dated deviation.
- **Usage:** at most one subagent at a time. Use Sonnet for mechanical lookups and Opus
  for design and logic. No workflow tools or fan-outs.
- **Mrigay is learning:** explain each result in plain words.
