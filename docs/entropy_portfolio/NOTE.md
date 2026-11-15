# Hold as much entropy as you have ignorance? Signal information and the optimal departure from 1/N

*Paper 3 research note. Mrigay Pathak, with Claude. Pre-holdout sections written on 13 Nov
2026 before the holdout was touched; §7 was added after the single holdout run. Every
number below is checked against `results/entropy_portfolio/` by
`scripts/ep_traceability.py`.*

> **Revised 14 Nov 2026 after a fresh-referee report** (`REFEREE_REPORT.md`; point-by-point
> answers in `REFEREE_RESPONSE.md`). The corrections fix an SPA bug and several overclaims. Every
> number below comes from `results/entropy_portfolio/{real,holdout}/` (`summary.json`,
> `h3_extra.json`, `postfix.json`). Nothing was re-run on the holdout.

## 1. The answer in plain language

**The question.** An equal-weight portfolio (1/N) has the most entropy a portfolio can
have: it spreads money as evenly as possible. Optimising moves you away from it, toward
the stocks your signal likes, and lowers the "effective number" of stocks you hold.
DeMiguel, Garlappi & Uppal (2009) found that, out of sample, no optimiser reliably beats
1/N. We asked whether the right amount of entropy to give up depends on **how much
information your signal really carries**, and whether estimation-risk theory can predict
that amount as a number.

**What held:**
1. **The direction (descriptive).**
   - Across six signal–market cases (three signals, India and the US), the higher a
     signal's average information coefficient (IC) over the evaluation period, the fewer
     effective stocks the best portfolio held.
   - Rank correlation −0.89; exact permutation p = 0.033.
   - **Caveat.** Both quantities are measured after the fact, so the link is partly
     mechanical: a signal that paid more makes tilting look better in the same window.
   - The six cases also fall into two clusters, because every India IC exceeds every US
     IC. Within India ρ = −1.0; within the US ρ = −0.5. In the holdout ρ = −0.51
     (p = 0.33).
   - So this is consistent with the thesis, not a test of *ex-ante* information.
2. **No significant loss to 1/N, but "matches" only means "could not tell apart".**
   - Before the holdout, the pre-registered entropy rule was never significantly worse
     than 1/N after costs. In India its point estimates beat 1/N on all three signals.
   - In the US its certainty equivalent was below 1/N's for two of three signals. In the
     2021–2025 holdout it trailed 1/N in all six cases, though not significantly.
   - The intervals are wide. India "none", for example, beats 1/N by a Sharpe difference
     of 0.029 with p = 0.60.
   - It did beat plug-in Markowitz, which on 100 Indian stocks turned over 1,426 times
     its capital *per month*.
3. **The theory's structure.**
   - In a simulation with known truth, the theory found the optimal effective N to
     within one step of a 10-step dial.
   - In real data all six predictions fell inside the bootstrap intervals for the best
     level. The intervals are so wide, though, that almost any prediction would pass:
     this test has no power.

**What failed:**
1. **The amount.**
   - In all six real cases the best portfolio held *more* effective stocks than the
     theory predicted, by 0.28 of N on average.
   - A sign test gives p = 0.031, but it was chosen after seeing the data and treats
     related cases as independent. The holdout gives 4 of 4 non-tied cases, p = 0.125.
   - We named this direction of failure in advance (THEORY §7.2): stock-specific noise
     is correlated, so concentration costs more than the theory charges. But the
     simulation already had sector factors and showed no such bias. The more specific
     suspect is that real signals load on sectors and on volatility, which the simulated
     signal did not. **That is a hypothesis, not a finding.**
2. **Timing.** Using the past 36 months' IC to decide *when* to tilt more did not work.
   Next month's payoff to the signal was unrelated to the ex-ante estimate (calibration
   slope −0.75 in India, uninformative in the US).
3. **Significance.**
   - No rule beat 1/N at the 5% level once we controlled for trying twelve rules.
     Hansen SPA consistent p = 0.117 (India) and 0.897 (US). These are corrected values;
     the first version of the test was mis-centred.
   - The simulation had warned that about 300–1,000 months would be needed; we had 124
     and 191. That warning is itself optimistic, because the simulated IC was less noisy
     than the real one (§5).
   - H1, the 1/N puzzle in India, is economically overwhelming but does not reach the
     pre-registered significance test, because the Sharpe ratio of a portfolio with
     exploding leverage is itself extremely noisy.
4. **The proportional shrinkage rule.**
   - Theory says to act on a fraction t²/(1+t²) of the signal (t = the IC's
     t-statistic). It did not beat acting on the whole estimate in any statistically
     detectable way.
   - In the simulation it was clearly too cautious. In real data it won 4 of 6 cases
     before the holdout and 4 of 6 in the holdout (one tie), but no difference was
     significant.

**The one-sentence version.** Signal information decides how far to move from 1/N, in the
direction the thesis predicts, but the textbook formulas overstate how far. Real data
call for more diversification than independent-noise theory allows, and a short IC
history is too noisy to time the tilt.

**The holdout (2021–2025, run once).**
- Every signal's information disappeared (mean ICs between −0.03 and +0.02), and 1/N won
  in both markets.
- The entropy rule shrank its information-driven tilt toward zero, as designed. It still
  trailed 1/N in all six cases (not significantly), because its unshrunk risk-reduction
  tilt toward low-volatility stocks lost money.
- In India it beat every optimiser that ignores information. In the US, the momentum and
  low-volatility versions roughly matched long-only minimum variance, and the "none"
  version lost to it.
- Shrinking by the knowledge share beat acting on the full estimate in 4 of 6 holdout
  cases (one tie). The holdout is consistent with the threshold idea ("when your
  information is gone, go back to maximum entropy") only in a limited sense. The
  information part of the tilt did switch off, but the rule as a whole still trailed
  1/N. And R1 and R2 differ in more than the threshold, so this comparison cannot isolate
  it.

## 2. Why this question

DGU (2009) is one of the most cited results in portfolio choice. Kan & Zhou (2007) and Tu
& Zhou (2011) explain it with estimation risk: a plug-in mean–variance investor must
estimate **N** expected returns from **T** months, and the loss grows with N/T. Allen,
Lizieri & Satchell (2019) show that a forecast with enough skill beats 1/N. Pflug,
Pichler & Wozabal (2012) show that 1/N is optimal under extreme ambiguity.

Two parts of our argument are already known:
- collapsing N unknown means into a few coefficients on a characteristic is Brandt,
  Santa-Clara & Valkanov's (2009) parametric portfolio policy, and Grinold–Kahn's
  α = IC·σ·z;
- the knowledge share t²/(1+t²) is the precision weight of a single Black–Litterman view.

What we could not find (LITERATURE.md §3) is the mapping of that share through the
maximum-entropy dial into a *numeric* optimal effective N, tested out of sample under
pre-registration. The entropy penalty itself is not new. Near 1/N it is exactly
DeMiguel–Garlappi–Nogales–Uppal's (2009) 2-norm constraint: Σwᵢ² = ‖w − 1/N‖² + 1/N
(THEORY §1). So the contribution can only be the **information-matching rule**.

## 3. Theory in brief (THEORY.md)

1. **A signal turns N unknowns into one.** A cross-sectional score tilts 1/N along a
   single direction. The only unknown is how much the tilt pays, so Kan–Zhou's ignorance
   term N/T becomes 1/T. The optimal fraction of the estimated tilt to take is
   c = t²/(1 + t²), where t is the population t-statistic of the mean IC.
2. **The dial.** The long-only portfolio with signal exposure m and maximum entropy is
   the Gibbs tilt wᵢ ∝ exp(βzᵢ) (Jaynes 1957). It is the solution of entropy-regularised
   optimisation, solved by mirror descent and checked by KKT. For normal scores,
   N_eff/N = exp(−β²/2).
3. **The prediction.** Maximise mean–variance utility along the dial, charging two
   costs: signal-factor risk, and the idiosyncratic risk of concentration, which grows
   like e^{β²}. This gives β\* and so a **number** for the optimal effective N. Example:
   with IC 0.03, N = 100 and T = 36, about 39–45 of 100 effective stocks. That example
   assumes little true variation in the IC (σ²_ρ ≤ 0.01). The measured σ²_ρ is
   0.03–0.07, which pushes the prediction toward more diversification.

## 4. Replication of DeMiguel–Garlappi–Uppal (results/entropy_portfolio/replication.md)

- **Data.** Kenneth French data, rolling 120-month windows, July 1963 – November 2004.
  **8 of 10 checks within tolerances set before running.**
- **Industry dataset.** 1/N matches the authors' own number to five decimals
  (0.1353 vs 0.13531); minimum variance within 0.0016; mean–variance within 0.0177.
- **The two misses are data, not code:**
  - SMB/HML have since been revised, so 1/N on MKT/SMB/HML differs by 0.0107, against a
    tolerance of 0.010;
  - one mean–variance figure moves by up to 0.03 when a single month is dropped.
- **Caveat.** The printed RFS table is paywalled. We matched the authors' 2006 working
  paper and Kan, Wang & Zhou's (2016) replication of the published datasets.

## 5. Simulation with known truth (results/entropy_portfolio/simulation.md)

- **Set-up.** A 100-stock factor market (normal and fat-tailed), with a noisy-oracle
  signal of chosen IC, 20,000 months per setting.
- **Q1, structure.** The full-information prediction landed within one dial step of the
  true optimum for IC ≥ 0.02.
- **Q2, shrinkage.** Applied through the concave Gibbs dial, the shrinkage
  c = t²/(1+t²) was **too cautious**. Acting on the whole estimate did better whenever
  the signal was real. Shrinkage only helped when IC = 0.
- **Q3, power.** Separating an IC-0.03 rule from 1/N at t = 2 takes about 320 months
  (normal) to 490 (fat tails).
- All of this was recorded (THEORY §8) and fed into the pre-registration **before** any
  real-data run.
- **Calibration caveat (from the referee).** The simulation's IC noise (σ_ρ = 0.05, an IC
  sd of about 0.11) is well below the data's (IC sd 0.20–0.28, so σ_ρ ≈ 0.2). Real IC
  t-statistics are therefore about 2.5× smaller than simulated ones at the same mean IC.
  The power numbers and the R1-vs-R2 lesson transfer only loosely.

## 6. Real data, before the holdout

**Design (PREREGISTRATION.md):**
- the top 100 stocks by 63-day traded value each month;
- India: survivorship-free NSE data, evaluation February 2010 – December 2020, 124
  months (the NSE file has no data for July–December 2011; deviation D7);
- US: point-in-time S&P 500 lookup, February 2005 – December 2020, 191 months. **This
  lookup is survivorship-filtered:** it keeps only members present in the price file
  (387–496 of 503–515 at year-ends) and lacks LEH, BSC, MER, FNM and FRE, so 2008 is
  understated;
- signals: rolling 36-month mean ("none"), 12–1 momentum, low volatility;
- all real-time rules use only past data;
- costs: India's statutory charges plus market impact by liquidity tercile; US 10 bp per
  side, with 25 and 50 bp shown.
- Monthly Sharpe ratios; multiply by √12 ≈ 3.46 for annual. CEQ is in % a month at
  γ = 2.5.

### 6.1 India: 1/N versus optimisation (net of costs)

| Strategy | Gross Sharpe | Net Sharpe | Net CEQ | Turnover / month | N_eff / N |
|---|---|---|---|---|---|
| 1/N | 0.018 | 0.009 | −0.455 | 0.19 | 1.00 |
| Sample mean–variance | −0.110 | −0.092 | (−157,005) | 1,425.92 | 0.01 |
| Sample minimum variance | 0.172 | 0.047 | 0.032 | 1.46 | 0.03 |
| Min-variance, Ledoit–Wolf | 0.179 | 0.082 | 0.134 | 1.17 | 0.08 |
| Min-variance, 2-norm (CV) | 0.130 | 0.071 | 0.101 | 0.63 | 0.12 |
| Min-variance, long-only | 0.155 | 0.123 | 0.273 | 0.43 | 0.10 |
| Mean–variance, long-only | 0.153 | 0.130 | 0.112 | 0.86 | 0.02 |
| Kan–Zhou three-fund | 0.139 | −0.041 | −0.261 | 2.26 | 0.03 |
| Tu–Zhou | −0.012 | −0.126 | −0.902 | 2.18 | 0.08 |
| **Entropy rule R1, none** | 0.054 | 0.038 | −0.271 | 0.40 | 0.46 |
| **Entropy rule R1, momentum** | 0.078 | 0.054 | −0.321 | 0.71 | 0.25 |
| **Entropy rule R1, low volatility** | 0.169 | **0.143** | **0.378** | 0.41 | 0.15 |

How to read this table:
- **The plug-in Markowitz portfolio is a disaster,** as DGU found for small N; with 100
  stocks it is extreme. Its gross CEQ is −37.4% a month.
- **Every rule that ignores or shrinks the means beats 1/N before costs, except
  Tu–Zhou.** India 2010–2020 rewarded low-risk stocks, and 1/N barely beat the 6.5%
  risk-free proxy.
- **Costs reorder the field.** Unconstrained minimum variance falls from 0.172 to 0.047
  because it trades 146% of the portfolio a month.
- **The low-volatility entropy rules were the best strategies net of costs.** The
  no-shrinkage R2 version was marginally ahead (net Sharpe 0.145, CEQ 0.387) of R1 (0.143,
  0.378), at about a third of minimum variance's turnover.
- **The other two entropy rules did not do well.** R1 "none" and R1 momentum lose to
  every minimum-variance variant net of costs. Matching a 1/N whose net Sharpe is 0.009
  is weak evidence of safety.

### 6.2 United States (net of 10 bp per side)

| Strategy | Gross Sharpe | Net Sharpe | Net CEQ | Turnover | N_eff / N |
|---|---|---|---|---|---|
| 1/N | 0.174 | 0.171 | 0.538 | 0.13 | 1.00 |
| Sample mean–variance | 0.091 | 0.064 | (−13,508) | 328.06 | 0.00 |
| Sample minimum variance | 0.125 | 0.056 | 0.027 | 2.72 | 0.02 |
| Min-variance, Ledoit–Wolf | 0.147 | 0.103 | 0.208 | 1.52 | 0.06 |
| Min-variance, 2-norm (CV) | 0.173 | 0.144 | 0.337 | 0.92 | 0.14 |
| Min-variance, long-only | 0.143 | 0.131 | 0.295 | 0.40 | 0.11 |
| Mean–variance, long-only | 0.091 | 0.081 | −0.287 | 0.87 | 0.02 |
| Kan–Zhou three-fund | 0.081 | 0.060 | (−77.3) | 20.45 | 0.02 |
| Tu–Zhou | 0.036 | −0.034 | −3.066 | 9.15 | 0.09 |
| Entropy rule R1, none | 0.176 | 0.170 | 0.552 | 0.29 | 0.78 |
| Entropy rule R1, momentum | 0.174 | 0.168 | 0.526 | 0.33 | 0.77 |
| Entropy rule R1, low volatility | 0.187 | 0.181 | 0.476 | 0.21 | 0.42 |

In the US, 1/N is hard to beat. The entropy rules mostly stay near it: momentum and the
historical mean carried almost no ex-ante information in 2005–2020 (mean t ≈ 0.4–0.65),
so the rule held 77–78% of N.

**Cost sensitivity, US net Sharpe:**

| Cost per side | 1/N | Low-volatility rule | Ledoit–Wolf min-variance |
|---|---|---|---|
| 10 bp | 0.171 | 0.181 | 0.103 |
| 25 bp | 0.167 | 0.172 | 0.038 |
| 50 bp | 0.160 | 0.156 | −0.072 |

Low-turnover rules survive realistic costs; minimum variance does not.

### 6.3 The pre-registered hypotheses

**H1: the 1/N puzzle with plug-in mean–variance.**
- *India:* Sharpe 0.018 for 1/N vs −0.110 for mean–variance (gross). The difference
  −0.128 has LW bootstrap p = 0.33. **Not supported at the pre-registered 5% level.**
- Economically the case is overwhelming: a CEQ gap of 37 percentage points a month,
  turnover of 1,426.
- The Sharpe test lacks power because the mean–variance return series is dominated by
  a few months of exploding leverage. In our replication of DGU on 377 months, by
  contrast, mean–variance's losses *were* significant in 3 of 4 datasets (JKM p
  0.00–0.04). Here we have 124 months.
- *US:* difference −0.083, p = 0.43. Same reading.

**H2: the entropy rule matches or beats 1/N and mean–variance, net of costs.**
- *India:* R1 matches 1/N on all three signals:
  - net CEQ higher by 0.18 (none), 0.13 (momentum) and 0.83 (low volatility) % a month;
  - Sharpe differences +0.029, +0.045, +0.134, with LW p = 0.60, 0.39, 0.13.
  - "Beats 1/N" is not significant.
  - "Beats mean–variance" is significant only for low volatility (p = 0.025; 0.23 and
    0.14 for the others).
- *US:* Sharpe ratios within 0.01 of 1/N (p ≥ 0.80). Net CEQ is at or below 1/N's (0.552,
  0.526 and 0.476 vs 0.538), so by the strict pre-registered CEQ criterion R1 matches 1/N
  for one of three signals.
- **Verdict.** "Matches 1/N" holds in India (3 of 3), but only in the weak sense that we
  cannot tell the rule apart from 1/N. "Beats" is not shown anywhere.
- India low volatility (IC 0.078) is a case where the simulation said about 50 months
  would suffice, yet p = 0.13. So the null is not just low power; the simulation's IC
  noise was too small.
- *Multiple testing:*
  - Hansen SPA over 12 real-time rules vs 1/N: consistent p = 0.117 (India), 0.897 (US).
    These are corrected values; the first version mis-centred the bootstrap and reported
    0.63 and 0.81.
  - PBO over the 31 distinct dial variants (the three identical 1/N columns counted
    once): 0.24 in India, a moderate overfitting risk; **0.78 in the US**, where the
    in-sample best variant usually lands below the median out of sample.

**H3a: direction (descriptive, as pre-registered).**
- Spearman correlation between a case's evaluation-period mean IC and its best dial
  level: **−0.89, exact permutation p = 0.033.**
- Both axes are ex post, so this is consistent with the thesis but partly mechanical,
  and it does not use the *ex-ante* IC (which failed in H3d).
- Within India ρ = −1.0, within the US −0.5; holdout −0.51 (p = 0.33).

| Case | Mean IC | Best N_eff/N (gross CEQ) | 90% bootstrap interval | Full-information prediction |
|---|---|---|---|---|
| India, low volatility | 0.078 | 0.1 | [0.05, 0.4] | 0.06 |
| India, momentum | 0.049 | 0.2 | [0.05, 0.7] | 0.12 |
| India, none | 0.044 | 0.6 | [0.05, 0.9] | 0.12 |
| US, none | 0.027 | 0.4 | [0.1, 1.0] | 0.21 |
| US, momentum | 0.011 | 0.8 | [0.05, 1.0] | 0.34 |
| US, low volatility | −0.012 | 0.7 | [0.05, 1.0] | 0.30 |

**H3b: amount.**
- **6 of 6 predictions fall inside the 90% intervals, so the pre-registered rule says
  supported.** The test has almost no power, though:
  - the intervals average 0.78 wide on a 0-to-1 scale;
  - *any* constant prediction between 0.1 and 0.4 would also score 6 of 6.
- The more informative (but post hoc) fact is the **sign**. In all 6 cases the theory
  predicts *more concentration* than was best, by 0.28 of N on average. A sign test gives
  p = 0.031, but it was not pre-registered, the cases are not independent, and the 0.05
  floor of the dial lets low predictions miss mainly upward. The holdout has 4 of 4
  non-tied cases (p = 0.125).
- THEORY §7.2 named this direction in advance (correlated residuals). It remains a
  hypothesis (§1).
- For US low volatility, the predicted tilt comes entirely from risk reduction
  (covariance with 1/N), because its IC was negative.

**H3c: does shrinking by the knowledge share help in real time?**
- Net CEQ of R1 (theory, κ = 1) vs R2 (act on the whole estimate) vs R3 (cross-validated
  dial):
  - India: none −0.271 / −0.438 / −0.320; momentum −0.321 / −0.267 / −0.196;
    low volatility 0.378 / 0.387 / 0.332;
  - US: none 0.552 / 0.538 / 0.604; momentum 0.526 / 0.408 / 0.417;
    low volatility 0.476 / 0.450 / 0.371.
- R1 beats R2 in 4 of 6 cases, the reverse of the simulation.
- **No R1–R2 difference is significant** (LW p 0.23–0.91). **Not decided.**
- Real signals decay and flip, which is when shrinkage pays. But the simulation's lower
  IC noise (§5) is an equally good explanation of why the simulation favoured R2.

**H3d: calibration.**
- Pooled over signals, the realised unit-tilt return regressed on the shrunk ex-ante
  forecast gives slope −0.75 (95% CI −1.99 to 0.49) in India and 0.09 (−5.28 to 5.45) in
  the US.
- **Not supported.** The 36-month IC does not forecast next month's signal payoff.
- The ex-ante information measure is useless for timing a given signal. (H3a uses ex-post
  ICs, so it says nothing either way about the ex-ante measure.)
- Caveat: the pooled regression stacks the three signals and uses Newey–West errors
  without clustering by month. In the US holdout, ĉ is zero in every momentum and
  low-volatility month, so that slope rests on about 7 nonzero points.

## 7. Holdout (2021–2025): run once, unchanged

- **Run.** Code commit `6ac9821`, run once with no changes.
- **Window.** India January 2021 – June 2025 (54 months; data end); US January 2021 –
  December 2024 (48 months).

**The signals stopped carrying information.** The holdout mean ICs were:
- India: none −0.011, momentum 0.019, low volatility 0.003;
- US: none −0.027, momentum −0.011, low volatility 0.003.

India's 2021–2024 small- and mid-cap rally punished low-risk stocks, and momentum
whipsawed. This is a real out-of-sample test of what a rule does when its information
vanishes.

| Net Sharpe (monthly) | 1/N | R1 none | R1 momentum | R1 low volatility | Min-var, long-only | Min-var, Ledoit–Wolf | Sample mean–variance |
|---|---|---|---|---|---|---|---|
| India | **0.248** | 0.169 | 0.193 | 0.106 | −0.128 | −0.014 | −0.093 |
| US | **0.150** | 0.026 | 0.094 | 0.097 | 0.095 | 0.019 | −0.318 |

1. **1/N won in both markets.**
   - The entropy rules lost to it, though no difference is significant (LW p 0.13–0.58).
   - In India they beat every optimiser that ignores information.
   - In the US, R1 momentum and low volatility (0.094, 0.097) roughly matched long-only
     minimum variance (0.095), and R1 "none" (0.026) lost to it.
2. **The rule did move toward 1/N, but not all the way.** The knowledge share averaged
   only 0.00–0.12, so the *information* part of the tilt switched off as theory says.
   What kept the portfolios at 32–82% of N was the **covariance (risk-reduction) term**,
   which the theory does not shrink. That tilt is the low-volatility exposure, and it
   lost money in 2021–2025. Not shrinking covariances turned out to be the costly
   assumption.
3. **Shrinkage helped when information died.**
   - R1 (shrink by the knowledge share) beat R2 (act on the whole estimate) in 4 of 6
     holdout cases, with one tie: for example India momentum 0.731 vs 0.440 net CEQ, and
     US low volatility 0.187 vs 0.070 (p = 0.051).
   - None is significant at 5%.
   - R1 still trailed 1/N, so this supports "shrink when the signal is weak" over "act
     on the full estimate". It does not show that the rule is a good strategy.
4. **H3 in the holdout:**
   - the direction has the same sign but is not significant (Spearman −0.51, exact
     p = 0.33);
   - 4 of 6 predictions fall inside the intervals;
   - the theory again never predicted *less* concentration than was best: 4 of 4
     non-tied cases, post hoc p = 0.125.
   - Calibration (H3d) turned significantly **negative** (India slope −3.93, US −8.25):
     a signal that had worked over the past 36 months tended to fail next. The ex-ante
     IC is not a timing tool.
5. **H1 in the holdout.** Plug-in mean–variance lost to 1/N again: Sharpe gap −0.247 in
   India (p = 0.17) and −0.335 in the US (p = 0.060). Same sign, not significant.

## 8. Scorecard

| Claim | Result |
|---|---|
| DGU replicated | Yes: 8 of 10 within pre-set tolerance; the misses are explained by data revisions |
| Theory recovers known truth (simulation) | Yes for the structure; the shrinkage factor is too cautious |
| H1, 1/N puzzle in India | Economically yes; the pre-registered Sharpe test is not significant (p = 0.33) |
| H2, entropy rule matches 1/N net of costs | Not distinguishable from 1/N in India (3 of 3) or the US; never significantly better (SPA p 0.117 / 0.897) |
| H3a, more information → fewer effective stocks | Consistent, descriptive and ex post (ρ = −0.89, exact p = 0.033; holdout −0.51) |
| H3b, the predicted amount | Inside the intervals 6 of 6, but the test has no power; post hoc: over-concentrated in 6 of 6 |
| H3c, the shrinkage rule | Undecided |
| H3d, timing by the ex-ante IC | No (significantly negative in the holdout) |
| Holdout 2021–2025 | Signals lost their information; 1/N won; the entropy rules trailed 1/N in 6 of 6 (not significant); shrinkage beat no shrinkage in 4 of 6 (one tie) |

## 9. Limitations

1. **Power.**
   - 124 and 191 months.
   - The simulation says a significant win over 1/N needs 300–1,000 months at realistic
     ICs.
   - The six-case cross-section behind H3a is small.
2. **The risk-free rate in India** is a constant 6.5% proxy (deviation D1). It shifts
   Sharpe levels, but cancels exactly in CEQ differences between strategies.
3. **India's cost model** uses the approximate statutory schedule plus an assumed impact
   by liquidity tercile; the real impact for the bottom third of the top 100 may be
   larger.
4. **Signal choice.** Three textbook signals. Low volatility dominates the India result,
   so the "information" there is partly risk reduction that the theory routes through
   covariance, not IC.
5. **Model misspecification.** Independent residuals, a stationary IC within 36 months,
   and a linear shrinkage applied through a nonlinear dial. The first is the likely
   source of the H3b bias.
6. **Data fixes.**
   - D7 (the July–December 2011 NSE gap) was found from the evaluation-month count,
     before any India result was read.
   - D8 (data-error returns in the raw US file) was triggered by an impossible result
     (US 1/N CEQ −267% a month), and its thresholds were set afterwards.
   - Earlier runs were not archived.
7. **Universe and plumbing:**
   - the US membership lookup is survivorship-filtered (§6);
   - month-end closes were forward-filled for all stocks, not only across the NSE gap.
     The referee counts 82 India and 4 US stock-months admitted without a close on the last trading
     day, against the pre-registration;
   - the baselines fill missing daily returns with zero, which slightly understates
     variance;
   - there is no India cost-sensitivity case.
8. **The simulation's IC noise is about 4× too small** (§5).
9. **A risk term left unshrunk.** The rule shrinks the signal's mean but not its
   36-month covariance with 1/N. That unshrunk term drove the holdout loss (THEORY §9).

## 10. Reproduce

Python 3.9 with numpy 1.24, pandas 2.0.3 and scipy 1.11. No sklearn, cvxpy or
statsmodels: Ledoit–Wolf, mirror descent, Newey–West, SPA and PBO are implemented in
`scripts/ep_lib.py` and unit-tested in `scripts/ep_tests.py`.

```
python scripts/ep_tests.py
python scripts/ep_replicate_dgu.py
python scripts/ep_simulate.py
OMP_NUM_THREADS=1 python scripts/ep_real_data.py --markets india
OMP_NUM_THREADS=1 python scripts/ep_real_data.py --markets us
python scripts/ep_h3_extra.py real
OMP_NUM_THREADS=1 python scripts/ep_real_data.py --holdout --markets india
OMP_NUM_THREADS=1 python scripts/ep_real_data.py --holdout --markets us
python scripts/ep_h3_extra.py holdout
python scripts/ep_traceability.py
```

All seeds are fixed. The French CSVs download automatically.

**Provenance.**
- `real/summary.json` records commit `6346a96`. It was actually produced by that commit
  plus the D7/D8 edits, which were committed in `1b71fe9` right after the run.
- The holdout's recorded commit `6ac9821` is exact.
- `scripts/ep_postfix.py` recomputes SPA, PBO, H3a and H3b from the saved return files.
  It re-runs no portfolio. The NSE and US price files
are local (`data_processed/`), not in the public repository.
