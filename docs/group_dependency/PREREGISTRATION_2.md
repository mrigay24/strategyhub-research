# Pre-registration 2: does concentration in few business groups predict crisis losses? (Phase 5)

**Author:** Mrigay Pathak · **Approved:** 12 Nov 2026, relayed by the parent session (Mrigay:
"continue working … finish everything you have left in mind"), with one design change: a
**dispersed twin**. · **Replaces:** `PREREGISTRATION_2_DRAFT.md`.
**Code:** `scripts/group_dependency_phase5.py`, committed together with this file.
**Map:** the filing-verified `results/group_dependency/group_map_v2.csv`.

This file is committed **before any portfolio outcome is computed**. Construction was timed
beforehand with no outcomes (`results/group_dependency/phase5/construction_timing.csv`), and
that timing fixed the sizes in §6. The analysis runs once. Any later change goes in §10 with
a date and a reason, and both versions are reported.

## 0. What the pilot does and does not license

The pilot (v1 and v2) found that a crashing group firm's siblings in other industries lose
about 4.5–4.7 pp more over 21 days than equally correlated unrelated stocks. The effect is
concentrated in a few stressed groups (Adani, Indiabulls, Anil Ambani, Future), and Tata
shows nothing. So this test looks at crisis drawdowns. It isolates *concentration in few
groups* from *being in groups at all*, and it pre-states what happens without the pilot's
groups.

## 1. Hypotheses

- **H-P1 (primary).** Two portfolios with the same stock count, the same industries, the
  same group-affiliated weight, and the same covariance-based diversification and trailing
  volatility: the one concentrated in **fewer** business groups loses more in crisis
  windows.
- **H-P2 (secondary).** Group-level effective N adds predictive power for crisis drawdowns
  beyond stock-level and industry-level effective N, Meucci's effective number of bets,
  and trailing volatility.

## 2. Data and labels

- **Prices.** The same panel and cleaning as the pilot (`Panel` in
  `group_dependency_pilot.py`):
  - corrected NSE panel;
  - ETFs removed;
  - ±45% one-day moves removed;
  - 2011 hole set to missing;
  - universe = top 500 by lagged 63-day traded value.
- **Business group.** A stock is in a business group if its v2 label at the formation date
  is of type Family or Corporate. Every other stock (MNC, State, PE, Professional, Unknown)
  is its own one-stock group. A business group with two or more members in the date's
  universe is **multi-company**.
- **Industry.** The map's 41 industries.

## 3. Windows and formation dates

Each window starts at the high of the equal-weighted universe index inside the start month,
and ends at its low inside the end month. **Formation = 126 trading days before the window
start.** Holdings are bought at the formation close with equal weights and held, with no
rebalancing; a missing return counts as zero. The dates below come mechanically from the
market index, and no portfolio outcome was looked at:

| Window | Formation | Start (high) | End (low) | Formation universe* |
|---|---|---|---|---|
| Global financial crisis | 2007-07-09 | 2008-01-07 | 2009-03-09 | 347 |
| Taper tantrum | 2012-11-12 | 2013-05-17 | 2013-08-06 | 226 |
| IL&FS / NBFC | 2018-02-28 | 2018-08-31 | 2018-10-09 | 366 |
| COVID | 2019-07-18 | 2020-01-24 | 2020-03-24 | 398 |
| Hindenburg / Adani | 2022-07-01 | 2023-01-03 | 2023-02-27 | 391 |
| 2024–25 small-cap fall | 2024-03-18 | 2024-09-23 | 2025-02-28 | 378 |

\*Top-500 stocks with at least 200 valid returns in the 252 days before formation. Taper is
small because the 2011 data hole falls in its covariance window.

**Outcomes:**
- the portfolio's **maximum drawdown inside the window** (from the window start; negative);
- secondarily, its window return minus the equal-weighted market's.

## 4. Measures (at formation, holdings and trailing data only)

- **Stock effective N:** exp(−Σ w ln w).
- **Industry effective N:** the same over industry weights.
- **Group effective N:** the same over group weights (§2 definition).
- **Meucci ENB:** exp of the entropy of the portfolio's variance split across the principal
  components of the trailing 252-day covariance of its own stocks (pairwise-complete,
  negative eigenvalues set to zero).
- **Trailing volatility:** annualised, from the same covariance.

## 5. Tests and decision rules

### 5.1 Matched portfolios: three per draw

1. **B (base):** *N* stocks drawn at random from the formation universe, equal weights.
2. **Swaps.** Take B's stocks in random order and swap them one at a time, until N/2 swaps
   are done or the list runs out. A base stock *s* is swapped **only if both** of these
   exist:
   - **C candidate:** a stock in *s*'s industry, not already in C, belonging to a
     multi-company business group that **another stock of C already belongs to**;
   - **D candidate:** a stock in *s*'s industry, not already in D, belonging to a
     multi-company business group that is in **neither B nor D**.

   Each twin takes, at random, one of the 3 candidates whose trailing volatility is closest
   to *s*'s.
3. **C (concentrated twin)** and **D (dispersed twin)** therefore replace the **same** base
   stocks, each with a group-affiliated stock. That makes their group-affiliated weight
   identical: the change Mrigay approved.
4. **A draw is kept only if:**
   - C and D each match B's Meucci ENB within ±5%;
   - C and D each match B's trailing volatility within ±5%;
   - C's group effective N is at most 85% of B's.

   Otherwise it is discarded and redrawn, up to 40 × the target per cell.
5. **Sizes:** *N* = 30 and 60.

### 5.2 T1 (primary, H-P1)

- **Statistic:** T1 = mean over all kept draws, pooled over windows and *N*, of
  **DD(C) − DD(D)**. It is negative if the concentrated twin loses more.
- **Inference (placebo groups):** rerun the whole construction with each stock's (group
  label, business-group flag) reassigned at random across the universe stocks, separately
  at each formation date. That keeps the number and size of groups and the industries. The
  one-sided *p* is the share of placebo T1 values ≤ the real T1.
- **Support** if placebo *p* < 0.05 **and** the window-level T1 (pooled over *N*) is
  negative in at least 4 of the 6 windows.

### 5.3 Registered secondaries (reported; they do not change H-P1's verdict except T1-x)

- **T1b:** DD(C) − DD(B), concentrated minus base, with its own placebo *p*. This is the
  draft's original comparison.
- **T1-x:** rerun without the Hindenburg window and without every stock of the pilot's
  driver groups (Adani, Reliance ADAG, Indiabulls, Future), with its own placebos. If T1
  is supported but T1-x fails (placebo *p* ≥ 0.05, or negative in fewer than 3 of 5
  windows), the verdict narrows to: **"group concentration matters when a group is under
  stress"**.
- **T1-hc:** rerun counting only **high-confidence** v2 labels as business groups; others
  become one-stock groups. Placebos at half the main count.
- **T1 on returns:** the same comparison on window excess return.

### 5.4 T2 (H-P2)

- **Portfolios.** 10,002 random portfolios per window: 3,334 each of *N* = 20, 50 and 100,
  alternating equal weights with Dirichlet(1) random weights.
- **Model.** OLS of the drawdown on log stock effective N, log industry effective N, log
  group effective N, log ENB and trailing volatility, with window fixed effects.
- **Supported** if all three hold:
  - the group coefficient is **> 0** (more groups, shallower drawdown);
  - its placebo *p* is **< 0.05** (200 reshuffles of group labels across stocks, sizes kept,
    same portfolios);
  - the leave-one-window-out out-of-sample R² rises when log group effective N is added.
    This is within-window demeaned, since a left-out window has no fixed effect.

## 6. Budget, fixed from the timing run

**Construction-only timing** (50 draws per cell, no outcomes):
- 1–4 ms per kept draw, except Taper at *N* = 60 (23 ms, 6% acceptance).
- About 26 s for 500 draws in all 12 cells.
- Swaps per draw: 4–12 on average. The candidate rules, not N/2, are the binding limit.
- Group effective N for B / C / D ≈ 28 / 19–22 / 28–29 at *N* = 30.
- C and D affiliated weight is equal by construction (0.28–0.45).

**Fixed sizes:**

| Run | Draws per window × *N* cell | Placebo reruns |
|---|---|---|
| T1 / T1b | **500** | **200** |
| T1-x | 500 | **200** |
| T1-hc | 500 | **100** |
| T2 | 10,002 portfolios per window | **200** |

Seed 20261112. Placebos run in parallel (fork, 7 workers).

## 7. Things considered and not done

- **Promoter-pledge moderator: skipped.** `promoter_pledges.csv` has 0 pledge figures
  within 100 days of any formation date. The cached filings are the 2020/21-earliest and
  2026-latest quarters only, and before 2019 there are none. Coverage is too thin to test.
- **Nippon India Small Cap illustration: deferred.** A monthly series needs Nippon's public
  monthly portfolio files for 2019–2025, which are not fetched. The parent session's
  `results/group_concentration/` has an Oct-2026 public-file snapshot only. The NIAIF/ICRA
  exports are never used.

## 8. Known limits, stated now

- **Not out of sample in time:** the same years as the pilot, with a different design and
  outcome.
- **Six windows:** portfolios within a window share its shock. The placebo-group
  inference is the guard.
- **No delisting returns:** a stock that stops trading is held at its last price.
- **Matching is on trailing covariance:** if group siblings co-move more only in crises,
  ENB at formation cannot see it. That is the hypothesis, not a flaw.

## 9. What gets reported

Everything, nulls included:
- T1, T1b, T1-x, T1-hc and T1 on returns, overall, by window and by *N*, each with its
  placebo distribution summary;
- acceptance rates and swap counts;
- the B / C / D group effective N, ENB and affiliated weights;
- the T2 coefficients, placebo *p* and out-of-sample R².

Files go to `results/group_dependency/phase5/` and the write-up to `NOTE.md` §9.

## 10. Deviation log

*(empty)*
