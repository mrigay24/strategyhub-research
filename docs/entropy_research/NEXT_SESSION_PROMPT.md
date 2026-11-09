# Prompt for the next session (paste everything below the line)

---

You are continuing a research project in `~/Desktop/trading app/strategyhub-research`
(Python 3, pandas 2.0.3, venv at `.venv/` — always run `.venv/bin/python`).
Read these first, in this order:

1. `docs/entropy_research/RESEARCH_NOTE.md` — the idea, the literature map, and the
   results of the first pilot (2026-11-09).
2. `scripts/entropy_research.py` — the three pilot tests and their known limitations.
3. `results/entropy_research/` — the pilot outputs (`summary.json`, CSVs, `run.log`).

## The idea in two sentences

Entropy of a distribution of shares measures how much any single firm's identity
matters to a market: high entropy means firms are interchangeable, low entropy means a
few firms carry the system. The interesting version is not market share but
**replaceability**: when a firm is hit, do its rivals and customers absorb the loss, or
does something that can't be rebuilt disappear with it? (Mrigay calls this the "death test".)

## The one narrow question for the paper

> Does a firm's **market-implied replaceability** (how the stock prices of its peers and
> customers respond when it suffers a firm-specific shock) contain information that its
> market share / industry HHI does not — about risk, returns and resilience — in the US
> and in India?

## Ground rules

- Git: commit locally as often as useful; push only at the end of a phase or at the end
  of the session, never after every commit. The repo is PUBLIC on GitHub: do not push
  anything under `docs/entropy_research/` unless Mrigay has said in chat that it's fine.
- Never touch CI or GitHub Actions.
- Keep the existing data conventions: trade/measure on t+1, `pct_change(fill_method=None)`,
  $1 price floor before any return filter. For crash/event studies use the RAW file
  `data_processed/extended_prices.parquet` (the clean file's 20% filter deletes real
  crashes). Treat moves beyond ±50% as bad ticks.
- The Desktop is iCloud-synced and some files are cloud-only stubs ("dataless" in
  `ls -lO`). Reading one hangs while it downloads. Known stubs:
  `data_raw/nse_bhavcopy_panel.parquet`, `data_raw/nifty500_index.parquet`,
  `data_raw/sp500_constituents/sp500_pit_monthly.csv`, `data_processed/metadata.json`.
  Use `data_processed/nse_survivorship_free.parquet` and
  `data_processed/sp500_universe_lookup.csv` instead. Run anything that loads the big
  parquets in the background.
- Honesty over results: report every null or negative finding in the note, like the
  repo already does. State limitations next to each number.
- Explain each step in plain language for Mrigay (he is learning the methodology),
  then put the details in the note.
- Update `docs/entropy_research/RESEARCH_NOTE.md` after every phase, plus
  `KNOWLEDGE_BASE.md` and `PROGRESS_REPORT.md` ("kbpr").

## Work, in order (commit after each phase)

**Phase 1 — Literature check (web search).** For each reference in the note's literature
map, confirm authors, year, journal and the one-line finding; fix any that are wrong.
Then search specifically for whether a *market-implied, firm-level replaceability /
substitutability measure from peer price reactions* already exists (search terms:
"intra-industry contagion competitive effect", "Lang Stulz bankruptcy", "peer firm
reaction idiosyncratic shock", "input specificity Barrot Sauvagnat", "firm
substitutability stock returns", "text-based network industries"). Write what exists and
what the gap is into the note's "Is this new?" section. No code in this phase.

**Phase 2 — Better peer groups for the US death test.** The pilot used 11 GICS sectors
(far too coarse: Apple and Oracle are not substitutes). Get GICS *sub-industry* for the
current S&P 500 (Wikipedia's "List of S&P 500 companies" table has a GICS Sub-Industry
column) and save it to `data_raw/sp500_constituents/sp500_subindustry.csv`. Re-run Test 3
at sub-industry level. Add: (a) a control for industry-wide news (drop events where the
sub-industry ETF-like average moved more than X% on day 0, or require the shocked firm's
abnormal return to dominate), (b) separate results for true deaths (last trading day
after a >70% decline over the prior year) vs ordinary crashes, (c) bootstrap confidence
intervals. Report the competitive (+) vs contagion (−) split by sub-industry.

**Phase 3 — India natural experiments.** Using `nse_survivorship_free.parquet`, run event
studies on famous Indian "deaths" and near-deaths: Satyam (7 Jan 2009), IL&FS default
(Sept 2018), DHFL (2019), Yes Bank moratorium (5 Mar 2020), Adani–Hindenburg
(24 Jan 2023). For each: abnormal return of the firm, of its direct rivals, and of the
rest of the market over [0,+5] and [0,+20] days. Peer sets must be built by hand from
NSE industry classifications (cite the source in the CSV). The question each case
answers: was the firm replaceable (rivals gained or were unaffected) or structurally
important (rivals/customers/the system fell)? Save to `results/entropy_research/india_cases.csv`.

**Phase 4 — A firm-level replaceability score.** For each S&P 500 firm with enough
shocks, estimate how much its sub-industry peers move per 1% of its own idiosyncratic
shock (a "peer sensitivity" beta, estimated only on past data, rolling). Then test, out
of sample and point-in-time: does this score explain future peer co-movement, firm
volatility, drawdowns or returns beyond the firm's dollar-volume share and its
sub-industry's HHI? Use Newey–West t-stats. If it adds nothing, say so plainly — that is
a valid result.

**Phase 5 — AI equity research pilot (design + small test).** Write
`docs/entropy_research/AI_DEATH_TEST.md`: a structured "death test" prompt an LLM answers
for a company (What would disappear if this firm vanished tomorrow? Who absorbs its
customers? How long to rebuild its capability? Score 0–10 with reasons). Explain the
look-ahead problem (LLMs already know what happened historically) and how to avoid it
(only score events after the model's training cutoff, or anonymise the firm). If
`ANTHROPIC_API_KEY` is set, score 30 S&P 500 firms and correlate with the Phase 4 score;
if not, stop at the design.

**Phase 6 — Paper skeleton and one-pager.** Write
`docs/entropy_research/PAPER_DRAFT.md` (10–15 page structure: introduction, framework,
data, three tests, India cases, AI section, limitations, conclusion — fill in what the
results support, mark gaps as TODO) and `docs/entropy_research/ONE_PAGER.md` (one page,
plain English, one table, for emailing a professor).

Finish by updating the note, running kbpr, committing, and giving Mrigay a plain-language
summary of what was found and what's still open. Push only if he has said the public repo
is fine for this work.
