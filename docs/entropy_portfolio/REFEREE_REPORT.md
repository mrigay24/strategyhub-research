# Referee report: "Hold as much entropy as you have ignorance?"

*13 Nov 2026. Checked against `results/entropy_portfolio/` and `scripts/ep_*.py`.*

## Summary

The note applies Kan–Zhou to a one-dimensional signal tilt to get a knowledge share c = t²/(1+t²). It maps c into effective N through a Gibbs (maximum-entropy) dial and tests the result, pre-registered, on 100 liquid Indian and US stocks, with a one-shot holdout for 2021–2025. The pre-registration, the DGU replication and the known-truth simulation are unusually careful. But the findings are mostly null, and several headline claims contradict the authors' own json files:
- the SPA bootstrap is mis-centred;
- H3b cannot reject almost any prediction;
- H3a is close to mechanical;
- the US universe is filtered for survivorship.

## Recommendation

**Reject in current form (major revision / reject-and-resubmit).** The design is worth rescuing; the claims are not.

## Major issues

**1. The SPA p-values are wrong (§1 "What failed" 3; §6.3 H2).**
- *Problem.* `ep_lib.spa_test` centres the bootstrap at the alternative, using √T(d̄* − d̄ + μ) with μ = max(d̄,0) or d̄. Hansen's null is Z* = d̄* − g(d̄).
- *Symptom.* In the US, p_lower is 0.911 and p_upper 0.813. Hansen's ordering guarantees the reverse.
- *Corrected values.* Recentring the saved net returns gives **0.117** for India (0.63 reported) and 0.897 for the US (0.81 reported). "Not significant" still holds.
- *Fix.* Correct the function, add a unit test with a known-superior model, and re-report.

**2. The holdout and "safety" claims contradict the json (§1; §7.1–7.3; §8 last row).**
- "Beat every optimiser that ignores information." In the US holdout, R1-none has a net Sharpe of 0.026. Long-only minimum variance has 0.095 and 2-norm minimum variance 0.068 (net CEQ −0.320 vs 0.180 and 0.075). The note's own §7 table shows this.
- "R1 beat R2 in 5 of 6." It is 4 of 6. R2 wins India-none (−0.044 %/month), and US-mom is a tie (−0.00007).
- "Knowledge share 0.04–0.12." It is 0.00 for US momentum and US low-vol.
- "Never meaningfully worse than 1/N." Before the holdout, R1 fails the pre-registered CEQ criterion for 2 of the 3 US signals. In the holdout it trails 1/N in all 6 cases, by 0.18–0.76 %/month of CEQ. "Matches" only means a failure to reject: India-none's Sharpe difference of 0.029 (p = 0.60) has a 90% interval of about [−0.06, +0.12].
- "The threshold survived everything." The rule lost to 1/N everywhere. R1 and R2 differ in the threshold *and* in the scaling, so comparing them cannot isolate the threshold. PREREG §7 ties the threshold reading to R1 *losing* H3c, which did not happen.
- *Fix.* Correct each statement. Define "matches" by an equivalence margin (TOST), and report confidence intervals.

**3. H3a is close to mechanical and does not test ex-ante information (§1; §6.3 H3a, H3d).**
- *Problem.* Both axes are ex-post quantities from the evaluation window. A higher realised IC raises the in-sample payoff of tilting by construction; the prediction alone has ρ = −0.94 with the IC. Yet the text says "the more a signal knew" and "the ex-ante measure is good at telling signals apart (H3a)". H3a never uses the ex-ante measure, and that measure failed in H3d.
- *Clustering.* Every India IC is above every US IC, so the six cases form two clusters.
- *Inference.* p = 0.019 is a t-approximation; the exact permutation p is **0.033**. The pre-registration called H3a descriptive. In the holdout, ρ = −0.51 (p = 0.30).
- *Fix.* Test the ex-ante IC against the out-of-sample optimum within each market.

**4. H3b has no power, and its sign test is post hoc (§1; §6.3 H3b; §8).**
- *Power.* The intervals are [0.05,0.9], [0.05,0.7], [0.05,0.4], [0.1,1] and [0.05,1] twice. Every constant on the grid except 1.0 passes the ≥ 4/6 rule, and any constant in [0.1, 0.4] scores 6/6.
- *Sign test.* The 6/6 sign test (p = 0.031) was not pre-registered, and it assumes independent cases.
- *Grid floor.* The floor at 0.05 lets the predictions 0.065, 0.117 and 0.120 miss almost only upward.
- *Holdout count.* `h3_extra.json` counts two floating-point ties (1.3e−15) as positive. The correct result is 4/4, p = 0.125.
- *Fix.* Label the test exploratory, and use a continuous loss (the CEQ shortfall at the predicted level, with a CI) against naive predictions.

**5. The simulation is mis-calibrated (§1; §5; §6.3).**
- *IC noise.* The simulation uses σ_ρ = 0.05 (IC sd ≈ 0.11). The real IC sd is 0.20–0.28, which implies σ_ρ ≈ 0.18–0.26.
- *t-statistics.* Real t-statistics are therefore about 2.5× smaller: India low-vol has a mean t̂ of 1.52, against about 4.2 under the simulated noise. This, more than "signals decay and flip", explains why R1 vs R2 reversed.
- *Power.* India low-vol (IC 0.078, 124 months) exceeds the simulation's 50-month requirement, yet R1 vs 1/N gives p = 0.13. "What the power analysis predicted" is false here.
- *Mechanism.* The simulation already includes sector factors without over-concentration (at IC 0.01 the optimum is 0.30 and the theory gives 0.42). Its oracle signal is sector-neutral; real low-vol and momentum are not. "Correlated residuals" is an untested hypothesis.
- *Fix.* Recalibrate the simulation, and compare the realised active variance at each dial level with m²D²σ²_ρ + D²q(β).

**6. The theory's algebra is correct, but its assumptions are unstated (§3; THEORY §2–5).**
I verified the Wishart moments, k, h and c\*, Tu–Zhou's π₂ and c₁, the dial moments (1.1), (1.2) and (4.2), equations (5.1) and (5.2), and the table at IC 0.03 (0.764, 1.38, 0.39). However:
- (a) "N unknowns become one" holds only by assumption (μ ∝ z). The rule estimates ρ̄, σ²_ρ, σ_ef and D̄ but shrinks only μ_f, and the holdout loss came from the unshrunk 36-month σ_ef.
- (b) Kan–Zhou and Tu–Zhou assume a riskless asset, whereas the baselines use relative weights x/|1′x| (the Kan–Wang–Zhou 2016 case).
- (c) Equation (5.1) assumes homoskedastic, independent residuals, which fails by construction for low-vol.
- (d) At small β the entropy given up scales with c², not with 1 − c, so the slogan misstates the algebra.

**7. The US universe is not a point-in-time S&P 500 (§6; PREREG §1).**
- *Problem.* `sp500_universe_lookup.csv` lists 388 (2004) to 470 (2020) names per year-end: 637 distinct names, all present in the price file. LEH, BSC, MER, FNM and FRE are missing.
- *Stale prices.* `load_market` forward-fills month-end closes for all stocks. This admits stocks with no close on day t (82 of 21,400 India slots), against the pre-registration.
- *Fix.* Use full constituent histories with delisting returns, or relabel the universe.

**8. Some decisions came after the results, and provenance is incomplete (§9.6; D7–D8).**
- D8 was triggered by a result (US 1/N CEQ of −267%), so "logged before results were read" is inaccurate.
- The earlier runs are not archived.
- `real/summary.json` records commit 6346a96, but its log reflects the later D7 code.
- Switching H3b to c = 1 after the simulation leaves no pre-registered test of the *amount* of shrinkage.
- *Fix.* Archive the earlier runs, record the dirty-tree state, and label post-hoc analyses.

**9. Novelty is overstated (§2).**
- Brandt–Santa-Clara–Valkanov (2009), which is uncited, already reduce N unknowns to one via a characteristic.
- t²/(1+t²) is the Black–Litterman precision weight of a single view.
- Tu–Zhou's δ\* already maps estimation risk into a distance from 1/N.
- Lassance–Vanderveken–Vrins (2026) choose the number of assets.
- *Fix.* Reposition the contribution as the Gibbs-dial mapping plus its pre-registered test.

## Minor issues

1. §6.1, "best of all strategies": low-vol R2 (0.145 / 0.387) beats R1 (0.143 / 0.378).
2. §6.1, "every rule that ignores or shrinks the means beats 1/N": Tu–Zhou's gross Sharpe is −0.012, below 1/N's 0.018.
3. §6.3 H1, "DGU report the same pattern": DGU's losses are significant in 3 of 4 datasets (JKM p 0.00–0.04).
4. §1, "within one step": this holds only for IC ≥ 0.02.
5. H3d: NW(6) on the stacked signals ignores same-month correlation. The US holdout slope (−8.25) rests on about 7 nonzero points. Cluster by month.
6. §6.2: the US table omits sample min-variance (0.056), Kan–Zhou (0.060), Tu–Zhou (−0.034) and long-only mean–variance (0.081).
7. §3, "39–45 of 100": this assumes σ²_ρ ≤ 0.01, while the measured value is 0.03–0.07.
8. `baselines` fills missing daily returns with 0, which biases min-variance.
9. India has no cost sensitivity; add a 2× impact case.
10. In India, R1-none and R1-mom lose to every min-variance variant net (CEQ −0.271 and −0.321, against 0.273).

## What is done well

- A genuine pre-registration with a dated deviation log, a holdout run once and stamped with its hash, and nulls reported as nulls.
- A DGU replication against pre-set tolerances, with 1/N matching to five decimals.
- A known-truth simulation and power analysis completed before any real data.
- Survivorship-free NSE data and an itemised Indian cost model.
- Correct derivations, and a candid admission that the entropy penalty is locally the 2-norm constraint.
- Unit-tested, traceable code.
