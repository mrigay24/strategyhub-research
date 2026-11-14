# Simulation with known truth (paper 3, Phase 4)

*Script: `scripts/ep_simulate.py`, fixed seed, about 70 s. Numbers: `simulation.json`. Run
on 13 Nov 2026, before any real-data result.*

## Set-up

- **Market.** N = 100 stocks:
  - one market factor (mean 0.6%, sd 5% a month);
  - four sector factors (sd 3%);
  - idiosyncratic risk (sd 8%);
  - two cases: normal shocks, and multivariate-t with 5 degrees of freedom scaled to the
    same variances (fat tails).
- **Signal.** A "noisy oracle" score is redrawn every month. Its true IC is
  ρₜ = ρ̄ + 0.05ηₜ, so the IC has true time variation (σ_ρ = 0.05) plus sampling noise
  (≈1/√N).
- **Size.** Six IC levels ρ̄ ∈ {0, 0.01, 0.02, 0.03, 0.05, 0.08}, each run for 20,000 months.
- **Pipeline.** It is the same code the real data will use:
  - each month, the past 36 realised Spearman ICs give the t-statistic and the knowledge
    share ĉ = (31/36)·max(0, 1 − 1/t̂²);
  - the theory gives β\* (THEORY.md eq. 5.1);
  - the Gibbs dial is computed at fixed effective-N levels (100%, 90%, …, 10%, 5% of N).
- **Criterion.** Out-of-sample CEQ at γ = 2.5 (monthly, %).

## Q1. Does the theory find the right entropy? Yes, when it knows the IC.

The ex-post best *fixed* dial level over 20,000 months is the optimum for an investor who
knows the true IC, because with that many months no estimation is left. Compare it with
the theory at full information (c = 1, true parameters):

| True IC | Ex-post optimum N_eff/N (normal) | Full-information theory | Ex-post optimum (t5) | Theory (t5) |
|---|---|---|---|---|
| 0.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| 0.01 | 0.30 | 0.42 | 0.40 | 0.41 |
| 0.02 | 0.20 | 0.25 | 0.30 | 0.24 |
| 0.03 | 0.20 | 0.18 | 0.20 | 0.17 |
| 0.05 | 0.10 | 0.11 | 0.10 | 0.10 |
| 0.08 | 0.05 | 0.07 | 0.05 | 0.06 |

- For IC ≥ 0.02 the structural theory (Gibbs dial, idiosyncratic concentration cost
  D²q(β), signal-factor risk) lands within one grid step (0.1) of the truth.
- At IC = 0.01 the CEQ curve is nearly flat, so the argmax is poorly defined.
- **Fat tails do not change this.**

## Q2. Does the estimation-risk shrinkage help? Only when there is no signal.

Real-time rules each month use the 36-month estimates and a multiplier on the knowledge
share. CEQ in % a month, normal case:

| True IC | 1/N | κ = 0.5 | **κ = 1 (theory)** | κ = 2 | Threshold (t > 1 → c = 1) | No shrinkage (c = 1 if IC > 0) | Best fixed level (ex post) |
|---|---|---|---|---|---|---|---|
| 0.00 | 0.303 | 0.297 | **0.292** | 0.286 | 0.280 | 0.271 | 0.303 |
| 0.01 | 0.198 | 0.238 | **0.238** | 0.237 | 0.243 | 0.260 | 0.288 |
| 0.02 | 0.234 | 0.335 | **0.345** | 0.347 | 0.349 | 0.392 | 0.435 |
| 0.03 | 0.206 | 0.435 | **0.461** | 0.467 | 0.479 | 0.539 | 0.577 |
| 0.05 | 0.224 | 0.762 | **0.825** | 0.846 | 0.854 | 0.871 | 0.888 |
| 0.08 | 0.265 | 1.354 | **1.443** | 1.457 | 1.457 | 1.458 | 1.458 |

The t5 case gives the same ordering.

**What this means.**
- **The Kan–Zhou shrinkage factor t²/(1+t²), applied through the Gibbs dial, is too
  cautious.** Whenever the signal is real, acting on the full estimate does better, and
  the rule leaves roughly 15–40% of the attainable gain on the table at IC 0.02–0.03.
- **Why.** Kan–Zhou's c is derived for a *linear* rule, where estimation noise passes
  one-for-one into the weights. The Gibbs dial is strongly concave: the concentration cost
  grows like e^{β²}, so a large estimate of the IC moves β only a little. The dial's own
  curvature already does most of the protecting, and shrinking again on top over-shrinks.
- **Where shrinkage does help.** At IC = 0 the shrunk rule gives up 0.011%/month against
  1/N, while the no-shrinkage rule gives up 0.032%/month. Shrinkage protects against
  acting on noise.
- **Caution.** The simulated signal always has the right sign and a constant mean. In
  real data, signals decay and flip (momentum crashes), and then shrinkage could look
  better.

**Consequence for the pre-registration, decided before any real data.**
- The theory rule (κ = 1) stays the primary test of the thesis as derived.
- The no-shrinkage plug-in (c = 1 when the mean IC > 0) is pre-registered as a second rule.
- The real data decide between them.
- THEORY.md §8 records this.

## Q3. How many months does it take to see it?

Shares of non-overlapping evaluation windows (normal case):
- "hit" = the empirical best level is within ±0.1 of the true optimum;
- "beat" = the theory rule's CEQ exceeds 1/N's.

| True IC | 60 months: hit / beat | 120 months | 240 months | 480 months | Months for t = 2 (rule vs 1/N) |
|---|---|---|---|---|---|
| 0.00 | 0.50 / 0.33 | 0.47 / 0.37 | 0.53 / 0.31 | 0.59 / 0.29 | — |
| 0.01 | 0.16 / 0.53 | 0.30 / 0.59 | 0.42 / 0.64 | 0.51 / 0.73 | ≈ 4,000 |
| 0.02 | 0.30 / 0.67 | 0.49 / 0.74 | 0.51 / 0.78 | 0.56 / 0.88 | ≈ 970 |
| 0.03 | 0.35 / 0.77 | 0.51 / 0.89 | 0.63 / 0.94 | 0.76 / 1.00 | ≈ 320 (t5: 490) |
| 0.05 | 0.73 / 0.92 | 0.82 / 0.98 | 0.88 / 1.00 | 1.00 / 1.00 | ≈ 115 (t5: 135) |
| 0.08 | 0.74 / 0.98 | 0.82 / 1.00 | 0.88 / 1.00 | 0.98 / 1.00 | ≈ 50 (t5: 60) |

**Read this before the real data.**
- India gives about 140 evaluation months before the holdout and the US about 200.
- With textbook signals (IC 0.02–0.04), that is enough to tell *roughly* where the
  optimum lies (hit rate about 0.5), and the rule beats 1/N in 75–90% of windows that
  long.
- It is **not** enough for a statistically significant win over 1/N, which needs
  300–1,000 months.
- So for H2 the realistic outcome is "matches 1/N, not significantly better", unless the
  signal's IC is near 0.05 or higher.
- That is a power statement, fixed now, so that a null cannot later be spun as "no
  effect".
