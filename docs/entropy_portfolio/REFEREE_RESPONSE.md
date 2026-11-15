# Response to the referee report (paper 3)

*14 Nov 2026. Each point lists what we changed and where. "Accepted" means we agree and
fixed it. "Future work" means a fix that needs new analysis and is listed in the NOTE
(§9) and the PROPOSAL (next steps) but not done here. No portfolio was re-run. The
corrected statistics are recomputed from the saved monthly returns by
`scripts/ep_postfix.py` and written to `results/entropy_portfolio/{real,holdout}/postfix.json`.*

## Major

1. **SPA mis-centred.** Accepted, fixed.
   - `ep_lib.spa_test` now recentres at d̄ − g(d̄) (Hansen 2005).
   - Unit tests cover a superior model, a null, and the p-ordering.
   - Corrected consistent p: India **0.117**, US **0.897**; holdout 1.00 and 1.00.
   - NOTE §1, §6.3 and §8; KB §46; study guide Part 10.
2. **Holdout and safety claims.** Accepted. The NOTE §1 and §7 claims now read:
   - R1 vs R2 is **4 of 6 with one tie** (pre-holdout 4 of 6);
   - the US holdout does *not* beat the information-free optimisers;
   - the knowledge share is 0.00–0.12;
   - R1 trails 1/N in 6 of 6 holdout cases.
   - "Matches" is now stated as "cannot be told apart". The "threshold survived" reading
     is limited, and we say R1 vs R2 cannot isolate it.
   - TOST equivalence margins: future work.
3. **H3a mechanical and ex post.** Accepted.
   - Relabelled descriptive, with the exact permutation p = 0.033.
   - Within-market ρ (India −1.0, US −0.5) and holdout ρ −0.51 (p = 0.33) are reported.
   - It is no longer described as evidence on ex-ante information.
   - An ex-ante-IC vs out-of-sample-optimum design: future work.
4. **H3b no power; sign test post hoc; tie bug.** Accepted.
   - The NOTE says the interval test has no power: any constant in [0.1, 0.4] scores 6/6.
   - The sign test is labelled post hoc and non-independent.
   - `ep_h3_extra.py` treats |gap| < 1e-9 as a tie; holdout 4/4, p = 0.125.
   - A continuous-loss comparison against naive predictions and a finer grid: future work.
5. **Simulation mis-calibrated.** Accepted.
   - NOTE §5 and §6.3 now say the simulation's σ_ρ = 0.05 is well below the data's (about
     0.2), so the power and R1/R2 lessons transfer loosely.
   - India low volatility is flagged as a case the simulation said should be detectable.
   - "Correlated residuals" is restated as a hypothesis. The more specific suspect is the
     signals' sector and volatility loadings, since the simulation had sector factors and
     showed no bias.
   - Recalibration and a direct active-variance check: future work.
6. **Unstated assumptions.** Accepted. THEORY §9 adds:
   - (a) μ ∝ z, with only the mean shrunk and σ_ef unshrunk;
   - (b) a riskless asset vs fully invested weights;
   - (c) homoskedasticity, which fails for low volatility;
   - (d) the entropy given up scales with c², so the slogan is exact only for position;
   - (e) Pearson vs Spearman.
7. **US universe; stale closes.** Accepted as limitations.
   - We confirmed that the lookup keeps only members present in the price file (387–496
     of 503–515 at year-ends; LEH, BSC, MER, FNM and FRE are absent).
   - The universe is relabelled and listed in NOTE §6 and §9.
   - The forward-fill of month-end closes for all stocks is disclosed (§9.7).
   - Full constituent histories with delisting returns: future work.
8. **Provenance.** Accepted.
   - NOTE §9.6 now says D8 was triggered by a result.
   - §10 explains that `real/summary.json` records `6346a96`, while the code that produced
     it was committed in `1b71fe9`.
   - Earlier runs were not archived; this is now stated.
   - Moving H3b to c = 1 after the simulation is disclosed in THEORY §8.
9. **Novelty overstated.** Accepted.
   - Brandt, Santa-Clara & Valkanov (2009) and Black–Litterman (1992) are added to
     LITERATURE (rows 27–28) and to NOTE §2 and the PROPOSAL.
   - The contribution is narrowed to the Gibbs-dial mapping and its pre-registered test.

## Minor

| # | Point | Response |
|---|---|---|
| 1 | Low-volatility R2 beats R1 | Accepted, NOTE §6.1 |
| 2 | Tu–Zhou is below 1/N gross | Accepted, NOTE §6.1 |
| 3 | "DGU report the same pattern" | Accepted: our replication's mean–variance losses were significant in 3 of 4 datasets, NOTE §6.3 |
| 4 | "Within one step" only for IC ≥ 0.02 | Already stated in §5; kept |
| 5 | H3d clustering | Accepted as a caveat in §6.3; month-clustered errors are future work |
| 6 | US table missing rows | Accepted, rows added (NOTE §6.2) |
| 7 | "39–45 of 100" assumes σ²_ρ ≤ 0.01 | Accepted, NOTE §3 |
| 8 | Truncated t | Noted; the mean t̂ values are labelled as averages of max(t, 0) in the json |
| 9 | Missing daily returns filled with 0 | Disclosed, NOTE §9.7 |
| 10 | No India cost sensitivity | Disclosed, NOTE §9.7; future work |
| 11 | R1-none and R1-momentum lose to min-variance in India | Accepted, NOTE §6.1 |
| 12 | PBO counts 1/N three times | Fixed: 31 distinct variants, PBO 0.24 (India) and 0.78 (US), from `postfix.json` |
