# Paper 3 session prompt: "Hold as much entropy as you have ignorance"

*Written 13 Nov 2026. Paste everything below the line into a new Claude Code session
opened in `~/Desktop/trading app/strategyhub-research`. Suggested model: Opus at high
effort (theory and design); use a Sonnet subagent only for data fetching.*

---

You are working with Mrigay Pathak, an IU finance and informatics senior, on paper 3 of a
research track. It must be **deep, not big**: one question, answered to the standard a
portfolio-choice referee would accept. Mrigay is learning, so explain every result in
plain language as well as technically.

## Context (read, don't redo)

- Papers 1 and 2 are finished:
  - `docs/entropy_research/PAPER_SHORT.md`;
  - `docs/group_dependency/PAPER2_DRAFT.md`;
  - `KNOWLEDGE_BASE.md` §41–§45.
- Lesson from both: entropy *described* things but never *decided* anything. A professor
  told Mrigay to work on portfolio optimization and the efficient frontier.
- **The question for this paper:** the equal-weight portfolio (1/N) is the
  maximum-entropy portfolio. Markowitz optimization trades entropy for estimated return.
  DeMiguel, Garlappi & Uppal (2009) found that no optimizer reliably beats 1/N out of
  sample, and the debate is still open. **Does the optimal amount of entropy to give up
  depend on how much information the investor's signal actually carries, and does it
  match what estimation-risk theory predicts?**
- **Thesis to test:** *hold as much entropy as you have ignorance.*

## What makes this deep (do these; they are the point)

1. **Derive before you test.**
   - Use the estimation-risk results of Kan & Zhou (2007) and Tu & Zhou (2011): the
     optimal mix of 1/N and the estimated mean-variance portfolio, as a function of N
     (assets), T (estimation months) and θ² (squared Sharpe ratio available).
   - Link θ² to a signal's information coefficient (IC) with Grinold's fundamental law:
     IR ≈ IC·√N.
   - The result: a **numeric prediction** of the out-of-sample-optimal effective N
     (exp of portfolio entropy) as a function of IC, N and T. The test is whether the
     data match that number, not just whether "a peak moves".
   - Write it in `docs/entropy_portfolio/THEORY.md`, with every step shown and a
     plain-language version.
2. **Replicate before you innovate.**
   - Reproduce DeMiguel–Garlappi–Uppal on their original data: Kenneth French Data
     Library portfolios (e.g. 10 industry; 25 size/book-to-market) with their protocol
     (rolling M = 120-month estimation window, monthly rebalancing).
   - Match their published Sharpe ratios for 1/N, sample mean-variance and minimum
     variance within a stated tolerance.
   - **If the replication fails, stop and fix it before anything else.**
3. **Simulate with known truth.**
   - Build a market with known μ and Σ (factor structure, normal and fat-tailed), plus a
     "noisy oracle" signal of chosen IC.
   - Show the method recovers the theory's optimal entropy, and how many months it needs.
4. **Choose the entropy level ex ante, never ex post.**
   - An entropy dial picked by looking at the out-of-sample curve is in-sample. Evaluate
     only rules decided in real time:
     - the theory-implied rule from (1);
     - nested rolling cross-validation using past data only.
   - Show the full curve only as a labelled diagnostic.
5. **Use proper inference.**
   - Sharpe-ratio differences: Jobson–Korkie with Memmel's correction, and the Ledoit–Wolf
     (2008) bootstrap test.
   - The dial creates many variants, so control multiple testing with Hansen's (2005) SPA
     test or the probability of backtest overfitting (Bailey, Borwein, López de Prado &
     Zhu 2017).
   - Report certainty-equivalent return and turnover, and results net of realistic costs.
6. **Use honest baselines.** The entropy rule must be compared with:
   - 1/N;
   - sample mean-variance;
   - minimum variance with Ledoit–Wolf shrinkage;
   - Kan–Zhou three-fund;
   - Tu–Zhou combination;
   - norm-constrained portfolios (DeMiguel, Garlappi, Nogales & Uppal 2009);
   - long-only constraints (Jagannathan & Ma 2003 show constraints act like shrinkage).
   
   If entropy regularization turns out to be mathematically equivalent to one of these,
   say so plainly. The contribution then becomes the information-matching rule, not the
   penalty.

## Raw material (start here, not from anything pre-digested)

- **Replication:** the raw Kenneth French Data Library CSVs. Download them; don't use a
  wrapper's cached copy.
- **India:**
  - daily prices from `data_processed/nse_survivorship_free_adj_nohole.parquet` (long
    format: date, symbol, OHLCV; corporate actions already audited, see KB §42);
  - a point-in-time top-100 universe by 63-day traded value, rebuilt monthly;
  - risk-free rate: RBI 91-day T-bill yields (RBI DBIE). If that fetch fails, document it
    and use a stated proxy.
- **US (second market):** `data_processed/extended_prices.parquet` (raw; $1 floor;
  `pct_change(fill_method=None)`), with the point-in-time S&P 500 mask from
  `scripts/entropy_research.py` (`us_pit_mask`). Don't read
  `data_raw/sp500_constituents/sp500_pit_monthly.csv` (an iCloud stub).
- **Signals:** textbook definitions computed from prices only:
  - none (rolling historical mean);
  - 12–1 momentum;
  - low volatility.
  
  Measure each signal's information **ex ante**: rolling Spearman IC over the past 36
  months. **Do not use the StrategyHub composites as signals.** They were selected by
  in-sample t-stats, so their strength is inflated.
- **Costs:**
  - India: securities transaction tax and exchange charges from the official schedule,
    plus a stated market-impact assumption by liquidity bucket;
  - US: 10 / 25 / 50 bps sensitivity.
- **Holdout:** reserve **2021-01 to 2025-12** in both markets. Nothing touches it until a
  final run that is pre-registered and done once.

## Tools

- **Python only:** `~/.venvs/strategyhub/bin/python` (numpy 1.24, pandas 2.0.3, scipy
  1.11).
  - The project `.venv` is iCloud-evicted and hangs on import.
  - sklearn, cvxpy and statsmodels are NOT installed, and pip installs have hung before.
    Implement them yourself:
    - Ledoit–Wolf shrinkage from its formula, unit-tested against a hand-computed
      example;
    - the entropy-regularized long-only optimizer by mirror descent (exponentiated
      gradient), with a KKT-condition check;
    - Newey–West standard errors.
- **pandas 2.0.3:** use `M`/`Q` resample codes, not `ME`/`QE`.
- **Seeds:** fixed seeds everywhere, so one command reproduces every number.

## Phases (commit after each; push at the end of each phase)

1. **Literature.** Write `docs/entropy_portfolio/LITERATURE.md`. Verify every citation
   (authors, year, journal, the result used, and the key equation) against a primary
   source:
   - Markowitz 1952;
   - Chopra & Ziemba 1993;
   - Jagannathan & Ma 2003;
   - Ledoit & Wolf 2004 and 2008;
   - Kan & Zhou 2007;
   - Garlappi, Uppal & Wang 2007;
   - DeMiguel, Garlappi & Uppal 2009;
   - DeMiguel, Garlappi, Nogales & Uppal 2009;
   - Kritzman, Page & Turkington 2010;
   - Tu & Zhou 2011;
   - Pflug, Pichler & Wozabal 2012;
   - Allen, Lizieri & Satchell 2019;
   - Grinold 1989;
   - Meucci 2009;
   - Jaynes 1957;
   - Hansen 2005;
   - Bailey et al. 2017;
   - any emerging-market 1/N study (e.g. China).
   
   Then state honestly what exists and what would be new. If an India 1/N study or an
   "entropy matched to signal information" result already exists, say so and stop for
   Mrigay's decision.
2. **Theory.** Write `THEORY.md` (deliverable 1 above).
3. **Replication.** `scripts/ep_replicate_dgu.py` and
   `results/entropy_portfolio/replication.md`: a table of ours vs published.
4. **Simulation.** `scripts/ep_simulate.py` and `results/entropy_portfolio/simulation.md`.
5. **Pre-registration.** Commit `docs/entropy_portfolio/PREREGISTRATION.md` **before any
   real-data result**. It fixes:
   - hypotheses (H1: the 1/N puzzle holds in India with plug-in mean-variance; H2: the
     ex-ante entropy rule beats or matches 1/N and mean-variance net of costs; H3: the
     optimal effective N falls as ex-ante IC rises, *by the amount theory predicts*);
   - universes, windows, costs, tests, decision rules, and the holdout.
6. **Real-data run** on 2000/2005–2020 data only:
   - India primary, US secondary;
   - report everything, including nulls.
7. **Holdout run** (2021–2025): once, unchanged.
8. **Deliverables:**
   - `docs/entropy_portfolio/NOTE.md`: the full record, in plain language;
   - `docs/entropy_portfolio/PROPOSAL.md`: two pages for Mrigay's professor, with two
     figures:
     1. the 1/N-vs-optimization table for India;
     2. the "entropy frontier", i.e. out-of-sample Sharpe against effective N by
        signal IC, with the theory-predicted optimum marked. Load the dataviz skill
        first.
   - the proposal ends with one specific question for the professor: which
     estimation-risk framing he prefers;
   - a fresh-subagent referee report on the NOTE, with fixes;
   - a traceability check script (every number in the NOTE against `results/`);
   - kbpr: a new KNOWLEDGE_BASE section and your own PROGRESS_REPORT lines only;
   - a "Part 10" for `docs/entropy_research/STUDY_GUIDE.md`: the ideas Mrigay must
     own (estimation risk, the 1/N puzzle, shrinkage, the fundamental law, entropy
     regularization) and professor Q&A.

## What will show the result is right (not you, not Mrigay)

1. The DeMiguel–Garlappi–Uppal published numbers, reproduced.
2. The simulation recovering the known truth and the theory's numbers.
3. A numeric theory prediction checked against data.
4. The untouched 2021–2025 holdout.
5. A second market (the US) as a replication sample.
6. Bootstrap and multiple-testing-controlled inference.
7. One-command reproducibility from the public repo, so a professor can rerun it.

## Ground rules

- **Git:** commit locally as often as useful. Push only at the end of each phase, never
  after every commit, and always before stopping. Never add or touch CI or GitHub
  Actions. Commit only your own files, by explicit path; other sessions may share this
  checkout.
- **The repo is public.** Never commit anything from `docs/outreach/` (private,
  git-excluded) or from `~/Desktop/NIAIF/`.
- **iCloud:** the Desktop is iCloud-synced. Check big files with `ls -lO` and skip
  "dataless" stubs.
- **Usage:** at most one subagent at a time; Sonnet only for mechanical fetching. No
  Workflow tool, no fan-outs.
- **Honesty:**
  - Pre-register before real data.
  - Never change a rule after seeing results; log any unavoidable change as a dated
    deviation.
  - Say "consistent with", never "proves".
  - If the theory prediction fails, that is the result.
- **Stop and ask Mrigay only if:**
  - the literature check finds the question already answered;
  - the replication cannot be made to match.
  
  Otherwise run all phases to the end.
- **Finish with:** a short plain-language summary for Mrigay covering what the paper now
  claims, what held, what failed, and the one thing to say to his professor.
