# [SUPERSEDED by PREREGISTRATION_2.md, 12 Nov 2026] DRAFT pre-registration 2: does counting groups predict crisis losses? (portfolio test)

**Status: DRAFT for Mrigay to approve. Nothing here has been run.** Written 11 Nov 2026,
after the pilot's GO (`NOTE.md` §5–6). Once approved, it gets committed unchanged as
`PREREGISTRATION_2.md` *before* any portfolio is built. The pilot's group map and code are
reused.

## 0. What the pilot does and does not license

The pilot found, at the level of single stocks:
- After a group firm's own crash, its siblings in **other** industries lost about 4.5 pp
  more over 21 days than unrelated stocks with the same calm-period correlation.
- Industry rivals lost about 0.4 pp more. The sibling effect is significant
  (*t* −2.64, permutation *p* < 0.001).
- On the crash day it is −2.2 pp (*t* −3.5).

It also found that the 20-day effect is **concentrated**:
- 10 of 74 events (stressed, leveraged groups: Adani 2023, Indiabulls, Anil Ambani,
  Future) carry most of it.
- Tata siblings show nothing.
- Without the four episodes already used in paper 1, it falls to −1.9 pp (*t* −1.83).

So the portfolio test must:
- (a) look at the **left tail** (crisis drawdowns), not average returns;
- (b) ask whether the measure helps **outside** the famous episodes;
- (c) keep the label-quality checks.

## 1. Hypothesis

**H-P1 (primary).** Among portfolios with the same number of stocks, the same industry
weights and the same covariance-based diversification, those concentrated in **fewer
business groups** lose more in crisis windows.

**H-P2 (secondary).** Group-level effective N adds predictive power for crisis drawdowns
beyond:
- stock-level effective N;
- industry-level effective N;
- Meucci's effective number of bets (ENB) from the trailing covariance matrix;
- trailing portfolio volatility.

## 2. Measures (at the formation date, from holdings and trailing data only)

- **Stock-level effective N:** exp(H) with H = −Σ w_i ln w_i.
- **Industry-level effective N:** the same over industry weights (41 industries).
- **Group-level effective N:** the same over group weights. Standalone firms count as their
  own group, and so do firms of type MNC, State, PE, Professional or Unknown (as in the
  pilot's primary definition; the widened definition is a robustness check).
- **Meucci ENB:** exp of the entropy of the portfolio's variance split across the
  principal components of the trailing 252-day covariance matrix. The minimum-torsion
  version (Meucci, Santangelo & Deguest 2015) is a robustness check.
- **Trailing volatility** of the portfolio over 252 days.

## 3. Portfolios

**Main design: matched twins.** At each formation date:
1. Draw a random base portfolio of *N* stocks (*N* = 30 and 60) from the top-500 universe,
   equal weights.
2. Build its **twin** by swapping up to half of its stocks, one at a time, for stocks in
   the **same industry** that belong to a group already in the portfolio. Each swap must
   keep the twin's Meucci ENB and trailing volatility within ±5% of the base.
3. Keep only pairs where the twin's group effective N is at least 15% lower than the
   base's.
4. Draw 2,000 such pairs per formation date (seed 20261112).

Twins differ in group concentration but match on stock count, industry weights and
covariance-based diversification. Any crisis-loss difference is what "counting groups"
adds.

**Secondary design: plain random portfolios.** 10,000 random portfolios per date
(*N* = 20, 50, 100; equal and random Dirichlet weights). A regression of crisis drawdown on
all five measures (H-P2).

## 4. Crisis windows (fixed now)

Formation = 126 trading days before the window starts. Holdings are bought and held
through the window. Each window starts at the high of the equal-weighted top-500 index
inside the stated month and ends at its low inside the stated end month (the rule picks
the exact days mechanically):

| Window | From (high in) | To (low in) |
|---|---|---|
| Global financial crisis | Jan 2008 | Mar 2009 |
| Taper tantrum | May 2013 | Aug 2013 |
| IL&FS / NBFC and small-cap fall | Aug 2018 | Oct 2018 |
| COVID | Jan 2020 | Mar 2020 |
| Hindenburg / Adani | Jan 2023 | Feb 2023 |
| 2024–25 small-cap fall | Sep 2024 | Feb 2025 |

**Outcome:** the portfolio's maximum drawdown within the window, and its window return
minus the equal-weighted market's.

## 5. Tests and decision rule

- **T1 (H-P1).** The mean twin-minus-base drawdown, pooled over windows and per window.
  Inference uses **placebo groups**: rerun the whole twin construction 500 times with
  group labels shuffled across stocks (keeping group sizes), and take the share of
  placebo means at or below the real one.
- **Support** if the pooled placebo *p* < 0.05 **and** the sign is right in at least 4
  of the 6 windows.
- **Pre-stated exclusions** (the pilot showed why):
  - **T1-x:** drop the Hindenburg window and every group whose events drove the pilot
    (Adani, Reliance ADAG, Indiabulls, Future), then rerun.
  - **If T1 holds only with them,** the claim narrows to "group concentration matters
    when a group is under stress", and the paper says so.
- **T2 (H-P2).** OLS of drawdown on the five log measures with window fixed effects,
  plus a placebo-group *p* for the group coefficient.
  - Also report the out-of-sample R² gain from adding group effective N, with
    leave-one-window-out folds.
- **Label quality.** Before any run, every multi-company group in the map is re-verified
  against an opened source (shareholding pattern or annual report), and the confidence
  column is updated. The test is repeated on high-confidence labels only.

## 6. Illustration (descriptive, not a test)

**Nippon India Small Cap Fund, monthly 2019–2025.**
- Rebuild the holdings from **Nippon India MF's free public monthly portfolio files**,
  *not* the NIAIF/ICRA exports, which must not be published.
- Map the holdings to groups and industries, and plot the three effective-N series
  against the fund's drawdowns in 2020 and 2024–25 (NAVs from AMFI's free NAV history).

## 7. Known limits, stated now

- **Not out of sample in time.** The pilot used 2006–2025, and this test uses the same
  years with a different design and outcome. A true out-of-sample check needs another
  market with business groups (Korea's chaebols are the natural one) or post-2025 data.
- **Six crisis windows.** Portfolios share each window's shock, so the effective sample
  is small. The placebo-group inference is the guard.
- **Stress is not measured.** The pilot suggests the channel works through stressed,
  leveraged promoters (pledged shares, group debt). A promoter-pledge moderator needs
  SEBI shareholding-pattern pledge data, which we do not have yet. It is listed as
  the next data task, not as a test.

## 8. What Mrigay needs to decide

1. Approve, change or reject this design (twins as the main test; six windows; T1-x).
2. Whether to spend the effort on re-verifying the group map first (recommended; about
   one session).
3. Whether to add Korea as the out-of-sample market (needs a chaebol map and KRX prices).
