# Paper 3 literature check: "Hold as much entropy as you have ignorance"

*Checked 13 Nov 2026. Each citation was checked against a primary or catalogue source
(publisher page, RePEc/EconPapers, the authors' own PDF). "Full text read" means the
paper itself was opened. "Unverified" means we could not confirm the item, and it is
flagged wherever it is used. The detailed notes and URLs come from a research-assistant
pass; this file is the record.*

## 1. The citations

| # | Citation | Status | What we use from it |
|---|---|---|---|
| 1 | Markowitz, H. (1952). Portfolio selection. *Journal of Finance* 7(1), 77–91. | Verified (catalogue) | Mean–variance problem: max w′μ − (γ/2) w′Σw. |
| 2 | Chopra, V. & Ziemba, W. (1993). The effect of errors in means, variances, and covariances on optimal portfolio choice. *Journal of Portfolio Management* 19(2), 6–11. | Verified (index record); exact ratio unverified | Errors in means cost roughly 10× errors in variances and about 20× errors in covariances. We cite this as "roughly 10:2:1", flagged. |
| 3 | Jagannathan, R. & Ma, T. (2003). Risk reduction in large portfolios: why imposing the wrong constraints helps. *Journal of Finance* 58(4), 1651–1683. | Verified | A no-short-sale constraint on min-variance works like shrinking the covariance matrix. |
| 4a | Ledoit, O. & Wolf, M. (2004). A well-conditioned estimator for large-dimensional covariance matrices. *J. Multivariate Analysis* 88(2), 365–411. | Verified, full text read | Σ\* = (b²/d²)·m·I + (a²/d²)·S, with ‖A‖² = tr(AA′)/N, m = tr(S)/N, d² = ‖S − mI‖², b̄² = T⁻² Σₜ ‖xₜxₜ′ − S‖², b² = min(b̄², d²) and a² = d² − b². Implemented in `ep_lib.lw_identity` and unit-tested on a hand-worked example. |
| 4b | Ledoit, O. & Wolf, M. (2004). Honey, I shrunk the sample covariance matrix. *J. Portfolio Management* 30(4), 110–119. | Verified (bibliographic) | Constant-correlation target; cited only, not used. |
| 5 | Ledoit, O. & Wolf, M. (2008). Robust performance hypothesis testing with the Sharpe ratio. *J. Empirical Finance* 15(5), 850–859. | Verified, full text read | Studentised circular block bootstrap for H₀: SR₁ = SR₂. It works on υ = (μ₁, μ₂, E r₁², E r₂²). See the deviation note in §4. |
| 6 | Kan, R. & Zhou, G. (2007). Optimal portfolio choice with parameter uncertainty. *JFQA* 42(3), 621–656. | Bibliographic verified; formulas via Kan–Wang–Zhou's restatement | Optimal scaling of the plug-in rule c\* = k₃·θ²/(θ² + N/T), with k₃ = (T−N−1)(T−N−4)/(T(T−2)) and the MLE covariance. The adjusted θ² estimator uses the incomplete beta function. The three-fund rule is (c Σ̂⁻¹μ̂ + d Σ̂⁻¹1)/γ. |
| 7 | Garlappi, L., Uppal, R. & Wang, T. (2007). Portfolio selection with parameter and model uncertainty: a multi-prior approach. *RFS* 20(1), 41–81. | Verified | Ambiguity aversion pulls portfolios toward minimum variance and 1/N. |
| 8 | DeMiguel, V., Garlappi, L. & Uppal, R. (2009). Optimal versus naive diversification: how inefficient is the 1/N portfolio strategy? *RFS* 22(5), 1915–1953. | Bibliographic verified. **The printed tables could not be opened (paywall).** The authors' 2006 working-paper text was read in full. | Protocol: rolling M = 120 months, monthly rebalancing, out-of-sample excess returns, Sharpe ratio, CEQ with γ = 1, turnover as Σ\|w_{t+1} − w_{t+}\|, and the Jobson–Korkie–Memmel test. The published abstract gives about 3,000 months for N = 25 and about 6,000 for N = 50. |
| 9 | DeMiguel, V., Garlappi, L., Nogales, F. & Uppal, R. (2009). A generalized approach to portfolio optimization: improving performance by constraining portfolio norms. *Management Science* 55(5), 798–812. | Verified (abstract level); the calibration rule is unverified | Min-variance with a norm constraint ‖w‖ ≤ δ. It nests Jagannathan–Ma (1-norm), shrinkage and 1/N. We calibrate δ by cross-validation; that choice is ours and is labelled as ours. |
| 10 | Kritzman, M., Page, S. & Turkington, D. (2010). In defense of optimization: the fallacy of 1/N. *Financial Analysts Journal* 66(2), 31–39. | Verified | Optimisation with sensible long-run inputs beats 1/N; the 1/N result comes from noisy short-window means. |
| 11 | Tu, J. & Zhou, G. (2011). Markowitz meets Talmud: a combination of sophisticated and naive diversification strategies. *J. Financial Economics* 99(1), 204–215. | Verified, full text read (some equations OCR-garbled) | w = (1−δ)·1/N + δ·ŵ, with δ\* = π₁/(π₁+π₂). Here π₁ = (w_e − w\*)′Σ(w_e − w\*) and π₂ = E[(ŵ − w\*)′Σ(ŵ − w\*)]. With c₁ = (T−2)(T−N−2)/((T−N−1)(T−N−4)), π₂ = [(c₁−1)θ² + c₁N/T]/γ². We re-derive this in THEORY.md §2 rather than relying on the garbled layout. |
| 12 | Pflug, G., Pichler, A. & Wozabal, D. (2012). The 1/N investment strategy is optimal under high model ambiguity. *J. Banking & Finance* 36(2), 410–417. | Verified | As ambiguity grows, the worst-case-optimal portfolio tends to 1/N. This is the qualitative ancestor of our thesis. |
| 13 | Allen, D., Lizieri, C. & Satchell, S. (2019). In defense of portfolio optimization: what if we can forecast? *Financial Analysts Journal* 75(3), 20–38. | Verified; the published break-even IC is unverified (≈0.04 in the working paper, 0.07 in the FAJ summary) | Mean-variance beats 1/N once the forecast IC passes a threshold. This is the closest prior work on skill vs 1/N. |
| 14 | Grinold, R. (1989). The fundamental law of active management. *J. Portfolio Management* 15(3), 30–37. | Partly verified (pages from citing papers) | IR ≈ IC·√BR. |
| 15 | Meucci, A. (2009). Managing diversification. *Risk* (May), 74–79. | Partly verified | Effective number of bets = exp(entropy of risk contributions). |
| 16 | Jaynes, E. T. (1957). Information theory and statistical mechanics. *Physical Review* 106(4), 620–630. | Verified | The maximum-entropy distribution under a mean constraint is the exponential (Gibbs) family. This is our dial. |
| 17 | Hansen, P. R. (2005). A test for superior predictive ability. *J. Business & Economic Statistics* 23(4), 365–380. | Verified | SPA test, with the stationary bootstrap and a consistent recentring threshold of −√(2 log log n). |
| 18 | Bailey, D., Borwein, J., López de Prado, M. & Zhu, Q. (2017). The probability of backtest overfitting. *J. Computational Finance* 20(4), 39–69. | Partly verified (pages) | PBO by combinatorially symmetric cross-validation (CSCV). |
| 19 | Memmel, C. (2003). Performance hypothesis testing with the Sharpe ratio. *Finance Letters* 1, 21–23. | Verified as cited in Ledoit–Wolf (2008) | Corrected Jobson–Korkie variance: θ = [2 − 2ρ + ½(SR₁² + SR₂² − 2SR₁SR₂ρ²)]/T. |
| 20 | Jobson, J. D. & Korkie, B. (1981). Performance hypothesis testing with the Sharpe and Treynor measures. *Journal of Finance* 36(4), 889–908. | Verified | The original test. |
| 21 | Bera, A. & Park, S. (2008). Optimal portfolio diversification using the maximum entropy principle. *Econometric Reviews* 27(4–6), 484–512. | Verified | Entropy (cross-entropy to 1/N) as the diversification objective under mean–variance constraints. It is the closest entropy-portfolio paper, and it has no link to forecast skill. |
| 22 | Qian, E. & Hua, R. (2004). Active risk and information ratio. *J. Investment Management* 2(3). | Verified (title, issue); pages unverified | IR ≈ mean(IC)/sd(IC). The time variation of the IC ("strategy risk") lowers the IR below IC·√N. |
| 23 | Clarke, R., de Silva, H. & Thorley, S. (2002). Portfolio constraints and the fundamental law of active management. *Financial Analysts Journal* 58(5), 48–66. | Verified | IR = TC·IC·√BR. Long-only constraints lower the transfer coefficient. |
| 24 | Kan, R., Wang, X. & Zhou, G. (2016 WP; *JFQA* 2022). Optimal portfolio choice with estimation risk: no risk-free asset case. | Verified (working paper read) | Replicates DGU's published datasets; we use it as reference (B) in the replication. |
| 25 | Lassance, N., Vanderveken, R. & Vrins, F. (2026). Optimal portfolio size under parameter uncertainty. *JFQA* 61(5), 2312–2352. | Verified (partly read) | The optimal **number** of assets given T and the assets' Sharpe ratios. It is the closest recent analytic work. |
| 26 | Bouchaud, J.-P., Potters, M. & Aguilar, J.-P. (1997). Missing information and asset allocation. arXiv cond-mat/9707042. | Verified (abstract) | Imposes a minimum 1/Σw² because forecasts are unreliable. This is a heuristic version of our idea with no information-matched rule. |
| 27 | Brandt, M., Santa-Clara, P. & Valkanov, R. (2009). Parametric portfolio policies: exploiting characteristics in the cross-section of equity returns. *RFS* 22(9), 3411–3447. | Verified (EconPapers record), added 14 Nov after the referee report | Weights are a linear function of a few characteristics, w = w̄ + θ′x/N, with θ estimated by maximising utility. **This already reduces N unknown means to a handful of coefficients.** It is the closest prior to our "N unknowns become one" step. |
| 28 | Black, F. & Litterman, R. (1992). Global portfolio optimization. *Financial Analysts Journal* 48(5), 28–43. | Standard citation, not re-checked this session | A view blended with an equilibrium prior by precision. For one view, the posterior weight on the view is a signal-to-noise ratio of the same form as t²/(1+t²). |

**Emerging-market 1/N studies.**
- **India:** one study was found. "Optimal vs 1/N diversification and portfolio evaluation: a study on Indian stock market", *Asian Journal of Management* 10(3), 2019. It uses Nifty 50 stocks and finds that minimum variance beats 1/N. Its design looks in-sample, and it has no rolling DGU protocol and no survivorship control. Details are unverified because the full text was not read.
- **China:** Yan & Yan (2021, *International Journal of Finance & Economics*, doi 10.1002/ijfe.1984) find that some short-sale-constrained mean-variance rules beat 1/N in A-shares, while minimum variance does not.

## 2. What already exists

1. **The 1/N puzzle and its cause are known.** The puzzle is DGU (2009). Kan–Zhou (2007), Tu–Zhou (2011) and Kan–Wang–Zhou explain it. The loss from plug-in mean–variance grows with N/T. The optimal shrinkage toward 1/N (or toward the scaled tangency portfolio) is an explicit function of θ², N and T.
2. **Skill matters.** Allen–Lizieri–Satchell (2019) show mean–variance beats 1/N once the forecast IC passes a threshold. Lassance–Vanderveken–Vrins (2026) choose the optimal *number* of assets from T and Sharpe ratios.
3. **Entropy as a diversification measure or penalty exists.** Examples are Bera–Park (2008), Meucci (2009) and Bouchaud–Potters–Aguilar (1997). Pflug–Pichler–Wozabal (2012) prove that 1/N is optimal under high ambiguity.
4. **Norm constraints and no-short constraints act as shrinkage.** See Jagannathan–Ma (2003) and DGNU (2009). We show in THEORY.md that a constraint on the 2-norm of fully invested weights *is* a constraint on the Rényi-2 effective N. So "entropy regularisation" is, to second order, the DGNU norm constraint.

## 3. What would be new

The targeted search found no paper that does all of the following:
- turns a signal's *ex-ante* information (IC and its time-series noise) into a **numeric** prediction of the out-of-sample-optimal effective N, using the Kan–Zhou estimation-risk algebra and the fundamental law;
- shows that a signal collapses the estimation problem from N unknown means to one unknown scale, so the shrinkage factor becomes t²/(1+t²) of the signal's IC t-statistic instead of θ²/(θ² + N/T);
- tests that number out of sample, pre-registered, in India and the US, with a holdout.

That is the contribution, if it survives. The entropy penalty itself is **not** new and, locally, not even distinct: it is a norm constraint (§2.4).

**Narrowed on 14 Nov, after the referee report.** Parts of the second bullet are known:
- Brandt, Santa-Clara & Valkanov (2009) already collapse N means to a few characteristic
  coefficients;
- the one-view Black–Litterman weight has the same precision form as t²/(1+t²).

What remains specific to this paper:
1. The mapping of that knowledge share through the maximum-entropy (Gibbs) dial into a
   numeric effective N.
2. Its pre-registered out-of-sample test with a holdout. That test supported the
   direction but not the amount.

**What is only partly new:**
- **H1 (the 1/N puzzle in India).** One Indian study exists (Nifty 50, apparently in-sample). A rolling, survivorship-free DGU-protocol test on NSE data was not found. H1 is therefore best described as "the first DGU-protocol replication in India", not a new question.

**Limits of the search.** It was a web search with snippet-level reading of most candidates. "Not found" is not proof that no such paper exists.

## 4. Deviations recorded at this stage

- **The DGU printed table could not be opened.** The replication is checked against the authors' own 2006 working-paper tables (same datasets and period) and against Kan–Wang–Zhou's replication of the published FF datasets. See `results/entropy_portfolio/replication.md`.
- **Ledoit–Wolf (2008) test:**
  - LW use a prewhitened quadratic-spectral HAC standard error and calibrate the block size on a VAR(1).
  - We use a Newey–West HAC standard error for the original statistic and a block-based standard error inside the bootstrap.
  - The block size is fixed in advance at b = 5 months, the centre of LW's grid {1, 2, 4, 6, 8, 10}.
  - This is a simplification, stated here and in PREREGISTRATION.md.
- **DGNU (2009) δ calibration** is not verified from their text. Our cross-validated ridge parameter, which minimises out-of-fold variance, is our own implementation of the 2-norm idea.
