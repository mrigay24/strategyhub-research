# Hold as much entropy as you have ignorance? Signal information and the optimal departure from 1/N

*Paper 3 research note. Mrigay Pathak, with Claude. Pre-holdout sections written on 13 Nov
2026 before the holdout was touched; §7 was added after the single holdout run. Every
number below is checked against `results/entropy_portfolio/` by
`scripts/ep_traceability.py`.*

## 1. The answer in plain language

**The question.** An equal-weight portfolio (1/N) has the most entropy a portfolio can
have: it spreads money as evenly as possible. Optimising moves you away from it, toward
the stocks your signal likes, and lowers the "effective number" of stocks you hold.
DeMiguel, Garlappi & Uppal (2009) found that, out of sample, no optimiser reliably beats
1/N. We asked whether the right amount of entropy to give up depends on **how much
information your signal really carries**, and whether estimation-risk theory can predict
that amount as a number.

**What held:**
1. **The direction.**
   - Across six signal–market cases (three signals, India and the US), the more a signal
     knew (its average information coefficient, IC), the fewer effective stocks the best
     portfolio held.
   - Rank correlation −0.89 (p = 0.019, six cases).
   - Information and diversification trade off as the thesis says.
2. **Safety.**
   - The pre-registered entropy rule never did meaningfully worse than 1/N after costs.
   - In India it beat 1/N on all three signals, on both Sharpe ratio and certainty
     equivalent, though not by statistically significant margins.
   - It beat plug-in Markowitz by enormous margins: plug-in Markowitz on 100 Indian
     stocks turned over 1,426 times its capital *per month*.
3. **The theory's structure.**
   - In a simulation with known truth, the theory found the optimal effective N to
     within one step of a 10-step dial.
   - In real data, all six predictions fell inside the (wide) bootstrap intervals for the
     best level.

**What failed:**
1. **The amount.** In all six real cases the best portfolio held *more* effective stocks
   than the theory predicted, by 0.28 of N on average (6 of 6, sign test p = 0.031). The
   theory assumes that the noise in stock returns is independent across stocks. It is not
   (sectors move together), so concentration costs more than the theory charges. We
   named this direction of failure in advance (THEORY §7.2).
2. **Timing.** Using the past 36 months' IC to decide *when* to tilt more did not work.
   Next month's payoff to the signal was unrelated to the ex-ante estimate (calibration
   slope −0.75 in India, uninformative in the US).
3. **Significance.**
   - No rule beat 1/N at the 5% level once we controlled for trying twelve rules (SPA
     p = 0.63 India, 0.81 US).
   - The simulation had warned that about 300–1,000 months would be needed; we had 124
     and 191.
   - H1, the 1/N puzzle in India, is economically overwhelming but does not reach the
     pre-registered significance test, because the Sharpe ratio of a portfolio with
     exploding leverage is itself extremely noisy.
4. **The proportional shrinkage rule.** Theory says to act on a fraction t²/(1+t²) of the
   signal (t = the IC's t-statistic). This did not beat acting on the whole estimate in a
   way that was statistically detectable. In simulation it was clearly too cautious. In
   real data it won 4 of 6 cases, but no difference was significant.

**The one-sentence version.** Signal information decides how far to move from 1/N, in the
direction the thesis predicts, but the textbook formulas overstate how far. Real data
call for more diversification than independent-noise theory allows, and a short IC
history is too noisy to time the tilt.

## 2. Why this question

DGU (2009) is one of the most cited results in portfolio choice. Kan & Zhou (2007) and Tu
& Zhou (2011) explain it with estimation risk: a plug-in mean–variance investor must
estimate **N** expected returns from **T** months, and the loss grows with N/T. Allen,
Lizieri & Satchell (2019) show that a forecast with enough skill beats 1/N. Pflug,
Pichler & Wozabal (2012) show that 1/N is optimal under extreme ambiguity.

What we could not find (LITERATURE.md §3) is a rule that maps a signal's *measured*
information into a *numeric* optimal effective N, and that tests the number out of sample
under pre-registration. The entropy penalty itself is not new. Near 1/N it is exactly
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
   with IC 0.03, N = 100 and T = 36, about 39–45 of 100 effective stocks.

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

## 6. Real data, before the holdout

**Design (PREREGISTRATION.md):**
- the top 100 stocks by 63-day traded value each month;
- India: survivorship-free NSE data, evaluation February 2010 – December 2020, 124
  months (the NSE file has no data for July–December 2011; deviation D7);
- US: point-in-time S&P 500, February 2005 – December 2020, 191 months;
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
- **Every rule that ignores or shrinks the means beats 1/N before costs.** India
  2010–2020 rewarded low-risk stocks, and 1/N barely beat the 6.5% risk-free proxy.
- **Costs reorder the field.** Unconstrained minimum variance falls from 0.172 to 0.047
  because it trades 146% of the portfolio a month.
- **The low-volatility entropy rule had the best net Sharpe ratio and the best net CEQ of
  all strategies,** at a quarter of minimum variance's turnover.

### 6.2 United States (net of 10 bp per side)

| Strategy | Gross Sharpe | Net Sharpe | Net CEQ | Turnover | N_eff / N |
|---|---|---|---|---|---|
| 1/N | 0.174 | 0.171 | 0.538 | 0.13 | 1.00 |
| Sample mean–variance | 0.091 | 0.064 | (−13,508) | 328.06 | 0.00 |
| Min-variance, Ledoit–Wolf | 0.147 | 0.103 | 0.208 | 1.52 | 0.06 |
| Min-variance, 2-norm (CV) | 0.173 | 0.144 | 0.337 | 0.92 | 0.14 |
| Min-variance, long-only | 0.143 | 0.131 | 0.295 | 0.40 | 0.11 |
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
  a few months of exploding leverage. DGU report the same pattern.
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
- **Verdict: "matches 1/N" holds in India (3 of 3); "beats" is not shown anywhere.** That
  is what the power analysis predicted.
- *Multiple testing:*
  - Hansen SPA over 12 real-time rules vs 1/N: consistent p = 0.63 (India), 0.81 (US).
  - PBO over the 33 dial variants: 0.23 in India, a moderate overfitting risk;
    **0.76 in the US**, where the in-sample best variant usually lands below the median
    out of sample.

**H3a: direction.** Spearman correlation between a case's evaluation-period mean IC and
its best dial level: **−0.89 (p = 0.019)**. **Supported.**

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
  supported.** But this is weak: the intervals average 0.78 wide on a 0-to-1 scale.
- The informative fact is the **sign**. In all 6 cases the theory predicts *more
  concentration* than was best, by 0.28 of N on average (sign test p = 0.031). This is
  the failure THEORY §7.2 named in advance: correlated residuals make concentration
  costlier than independent-noise theory charges.
- For US low volatility, the predicted tilt comes entirely from risk reduction
  (covariance with 1/N), because its IC was negative.

**H3c: does shrinking by the knowledge share help in real time?**
- Net CEQ of R1 (theory, κ = 1) vs R2 (act on the whole estimate) vs R3 (cross-validated
  dial):
  - India: none −0.271 / −0.438 / −0.320; momentum −0.321 / −0.267 / −0.196;
    low volatility 0.378 / 0.387 / 0.332;
  - US: none 0.552 / 0.538 / 0.604; momentum 0.526 / 0.408 / 0.417;
    low volatility 0.476 / 0.450 / 0.371.
- R1 beats R2 in 4 of 6 cases, the reverse of the simulation. In real data signals decay
  and flip, which is exactly when shrinkage pays. **But no R1–R2 difference is
  significant** (LW p 0.23–0.91). **Not decided.**

**H3d: calibration.**
- Pooled over signals, the realised unit-tilt return regressed on the shrunk ex-ante
  forecast gives slope −0.75 (95% CI −1.99 to 0.49) in India and 0.09 (−5.28 to 5.45) in
  the US.
- **Not supported.** The 36-month IC does not forecast next month's signal payoff.
- The ex-ante information measure is good at telling signals apart (H3a) but useless for
  timing a given signal.

## 7. Holdout (2021–2025)

*To be filled in after the single pre-registered holdout run.*

## 8. Scorecard

| Claim | Result |
|---|---|
| DGU replicated | Yes: 8 of 10 within pre-set tolerance; the misses are explained by data revisions |
| Theory recovers known truth (simulation) | Yes for the structure; the shrinkage factor is too cautious |
| H1, 1/N puzzle in India | Economically yes; the pre-registered Sharpe test is not significant (p = 0.33) |
| H2, entropy rule matches 1/N net of costs | Yes in India (3 of 3); US within 0.01 Sharpe; never significantly better |
| H3a, more information → fewer effective stocks | Yes (ρ = −0.89, p = 0.019) |
| H3b, the predicted amount | Inside the intervals 6 of 6, but biased toward over-concentration in 6 of 6 (p = 0.031) |
| H3c, the shrinkage rule | Undecided |
| H3d, timing by the ex-ante IC | No |

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
6. **Data fixes, logged before results were read:**
   - D7: the July–December 2011 NSE gap;
   - D8: data-error returns in the raw US file.

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

All seeds are fixed. The French CSVs download automatically. The NSE and US price files
are local (`data_processed/`), not in the public repository.
