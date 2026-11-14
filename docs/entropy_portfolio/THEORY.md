# Theory: how much entropy should an investor give up?

*Paper 3, Phase 2. Written 13 Nov 2026, before any real-data result. Every number in the
tables below comes from `scripts/ep_lib.py` (`kz_scale`, `predicted_neff_ratio_closed`).*

## 0. Plain-language version

An equal-weight portfolio (1/N) spreads money as evenly as possible, so it has the most
**entropy** any portfolio can have: it carries no opinion about which stock is better.
Every time you tilt toward the stocks you think are better, you give up entropy. You end up
with fewer "effective" stocks (effective N = exp(entropy)).

How far should you tilt? Two things decide it:

1. **How good is your signal?** This is measured by its information coefficient (IC), the
   correlation between your score today and next month's returns.
2. **How sure are you that it is that good?** You only have T months of history to judge
   it. The right measure is the IC's **t-statistic**: the average IC divided by its
   standard error.

The algebra of estimation risk (Kan & Zhou 2007; Tu & Zhou 2011) gives a clean answer.
Act on a fraction **c = t²/(1 + t²)** of what the signal says. The remaining fraction,
1/(1 + t²), is your *ignorance*, and that part of the portfolio should stay at 1/N.
**Hold as much entropy as you have ignorance.**

Why does plain Markowitz fail where this works? With sample means, the investor estimates
**N** unknown means from T months. The ignorance term is then N/T, which is enormous for
100 stocks. A signal replaces N unknowns with **one** (how much the signal pays), so the
ignorance term falls to 1/T. That one change turns the 1/N puzzle (DeMiguel, Garlappi &
Uppal 2009) into a rule you can compute.

The theory gives a **number**. With N = 100 stocks, T = 36 months of IC history and a
signal with IC = 0.03, the optimal portfolio holds about 39–45 effective stocks. With
IC = 0, it holds all 100 equally. The data can check that number.

---

## 1. Set-up and notation

- N risky assets with monthly excess returns rₜ ∈ ℝᴺ.
- Weights w with 1′w = 1 (a fully invested risky portfolio, as in DGU's "fund of risky
  assets").
- The equal-weight portfolio is e = 1/N.
- Mean–variance utility: U(w) = E[w′r] − (γ/2) Var(w′r). The certainty-equivalent return
  (CEQ) is the sample analogue.

**Entropy and effective N.**
- For long-only w, H(w) = −Σ wᵢ ln wᵢ and N_eff = exp H(w) ∈ [1, N]. The maximum is at
  w = e (Jaynes 1957: maximum entropy = the distribution that assumes the least).
- The Rényi-2 version, N_eff,2 = 1/Σwᵢ², is defined for long-short weights too.
- Since 1′w = 1,

  Σwᵢ² = ‖w − e‖² + 1/N  (because e′(w − e) = (1/N)(1 − 1) = 0).    (1.1)

  So **a bound on Rényi-2 effective N is a bound on the Euclidean distance from 1/N.**
  This is the 2-norm constraint of DeMiguel, Garlappi, Nogales & Uppal (2009).
- For small tilts w = e + a with 1′a = 0, a second-order expansion gives

  H(e + a) = ln N − (N/2)‖a‖² + O(‖a‖³).    (1.2)

  Shannon and Rényi-2 entropy therefore agree near 1/N, and an entropy penalty is
  locally a quadratic (ridge / 2-norm) penalty on the distance from 1/N. **We state this
  plainly: entropy regularisation is not a new kind of shrinkage.** What can be new is the
  rule that says *how much* of it to apply.

## 2. Estimation risk with sample means (the DGU setting)

Assume rₜ ~ iid N(μ, Σ). Write θ² = μ′Σ⁻¹μ for the squared maximum Sharpe ratio. The
investor estimates μ̂ (the sample mean) and Σ̂ (the MLE covariance, divisor T) from T
months. Two facts:
- μ̂ ~ N(μ, Σ/T);
- TΣ̂ ~ Wishart_N(T − 1, Σ), independent of μ̂.

**Step 1, Wishart moments.** For W ~ W_N(n, Σ):
- E[W⁻¹] = Σ⁻¹/(n − N − 1);
- E[W⁻¹ΣW⁻¹] = (n − 1)Σ⁻¹ / ((n − N)(n − N − 1)(n − N − 3)).

Put n = T − 1. Then:
- E[Σ̂⁻¹] = k Σ⁻¹ with k = T/(T − N − 2);
- E[Σ̂⁻¹ΣΣ̂⁻¹] = h Σ⁻¹ with h = T²(T − 2)/((T − N − 1)(T − N − 2)(T − N − 4)).

**Step 2, utility of a scaled plug-in rule.** Let ŵ = (1/γ)Σ̂⁻¹μ̂ and consider cŵ. By
independence and E[μ̂μ̂′] = μμ′ + Σ/T:

  E[U(cŵ)] = (c/γ)·k θ² − (c²/2γ)·h (θ² + N/T).    (2.1)

**Step 3, optimise over c.**

  c\* = (k/h)·θ²/(θ² + N/T) = [(T−N−1)(T−N−4)/(T(T−2))] · θ²/(θ² + N/T).    (2.2)

This is Kan & Zhou's (2007) optimal scaling. Read it as **(finite-sample factor) ×
(signal share)**. The estimated mean vector's squared length splits into a true part θ²
and a noise part N/T, since E[μ̂′Σ⁻¹μ̂] = θ² + N/T. The investor should act on the true
share only.

**Step 4, mixing with 1/N (Tu & Zhou 2011).** For w(δ) = (1 − δ)e + δŵ:
- with the unbiased covariance (divisor T − N − 2), E[ŵ] = w\* = Σ⁻¹μ/γ;
- the δ that maximises E[U] is

  δ\* = π₁/(π₁ + π₂),  π₁ = (e − w\*)′Σ(e − w\*),  π₂ = E[(ŵ − w\*)′Σ(ŵ − w\*)].    (2.3)

  In words, δ\* is **bias² / (bias² + variance)**: how far 1/N is from the truth,
  against how noisy the estimate is.
- Expanding π₂ with Step 1 gives π₂ = [(c₁ − 1)θ² + c₁N/T]/γ², with
  c₁ = (T−2)(T−N−2)/((T−N−1)(T−N−4)). This is TZ's formula.
  (We derived it independently here because the TZ text we could read was garbled.)

**What this says for stocks.** The ignorance term is N/T. The table shows c\* for a
monthly Sharpe ratio θ = 0.2:

| N | T (months) | c\* |
|---|---|---|
| 11 | 120 | 0.243 |
| 24 | 120 | 0.103 |
| 100 | 120 | 0.001 |

With 100 stocks, the right amount of the plug-in Markowitz portfolio to hold is almost
zero, so the investor should stay at 1/N or minimum variance. **This is the prediction
behind H1.**

## 3. A signal turns N unknowns into one

Now the investor has a cross-sectional score zᵢₜ, converted to normal scores, so it has
mean 0 and variance 1 across stocks every month. Its information is described by the
monthly rank IC:
- ρₜ = corr(zₜ, rₜ₊₁) across stocks;
- mean ρ̄ and time-series variance σ²_IC.

Under Grinold's (1989) model the forecast is αᵢ = ρ̄·D·zᵢ, where D is the cross-sectional
standard deviation of returns.

**The unit tilt.** Moving weight (1/N)·zᵢ onto each stock earns

  fₜ₊₁ = (1/N) Σᵢ zᵢₜ rᵢ,ₜ₊₁ = ρₜ·Dₜ₊₁    (3.1)

(the cross-sectional covariance of score and return). Every signal portfolio near 1/N is
e + β·(z/N), whose return is R_e + β·f. **The only unknown the investor must estimate is
E[f] = ρ̄D, one number.** This is the Kan–Zhou problem with K = 1 "asset", the unit tilt
f, whose Sharpe ratio is θ_s = ρ̄/σ_IC. Equation (2.2) with N → 1 gives

  c\* = [(T−5)/T] · θ_s²/(θ_s² + 1/T) = [(T−5)/T] · t²/(1 + t²),  t = ρ̄√T/σ_IC.    (3.2)

**The knowledge share is t²/(1+t²), where t is the population t-statistic of the mean
IC. The ignorance share is 1/(1+t²).**

**Link to the fundamental law.** σ²_IC splits into two parts:
- true time variation, σ²_ρ;
- sampling noise, about 1/N when residuals are independent.

So θ_s² = ρ̄²/(σ²_ρ + 1/N).
- With σ²_ρ = 0 this is Grinold's IR² = IC²·N (breadth BR = N), and t² = T·N·IC².
- With σ²_ρ > 0 it is Qian & Hua's (2004) IR = mean(IC)/sd(IC), which is always smaller.

We pre-register the Qian–Hua form as primary because it is the Sharpe ratio Kan–Zhou's
algebra needs. The naive Grinold form is a secondary variant.

**Estimated version (what the rule uses in real time).**
- The sample t̂² is biased upward: E[t̂²] ≈ t² + 1.
- So we use the unbiased θ̃² = θ̂² − 1/T, which gives

  ĉ = [(T−5)/T] · max(0, 1 − 1/t̂²).    (3.3)

  This is the positive-part James–Stein factor. **Do not act on a signal whose IC
  t-statistic is below 1.** Above 1, act on 1 − 1/t̂² of it. For T = 36: t̂ = 1.5 gives
  ĉ = 0.48, t̂ = 2 gives 0.65, t̂ = 3 gives 0.77.

## 4. The entropy dial: the maximum-entropy tilt

Which long-only portfolio carries signal exposure m = Σwᵢzᵢ while staying as close to 1/N
(as high-entropy) as possible? By Jaynes (1957), maximising H(w) subject to Σwᵢzᵢ = m and
1′w = 1 gives the Gibbs family

  wᵢ(β) = exp(βzᵢ)/Σⱼ exp(βzⱼ),  β ≥ 0.    (4.1)

Equivalently, wᵢ(β) = argmax_{w ∈ simplex} β·z′w + H(w), the entropy-regularised
long-only problem.
- **Algorithm.** Mirror descent (exponentiated gradient) solves it in one step. The
  general solver `entropy_mv` reproduces the closed form to 1e-16 and passes a KKT check
  (`ep_tests.py`).
- **The dial.** β = 0 is 1/N; β → ∞ puts everything on the top-scored stock. For small β,
  wᵢ ≈ (1 + βzᵢ)/N, which is exactly the linear Grinold tilt of §3.

For normal scores and large N, three closed forms hold, and they are checked numerically
in `ep_tests.py`:
- m(β) = Σwᵢzᵢ = β;
- q(β) := Σwᵢ² − 1/N = (e^{β²} − 1)/N;
- N_eff(β)/N = exp(−β²/2).    (4.2)

The dial's **cost** is the idiosyncratic risk of concentration, D²q(β), which grows like
e^{β²}. Its **benefit** is signal exposure m(β), which grows like β.

## 5. The optimal entropy, and the number it predicts

Use the return model rᵢ,ₜ₊₁ = common + ρₜDzᵢ + εᵢ, with Var(εᵢ) ≈ D² across stocks. The
tilt's active return is R_a(β) = D[ρₜ m(β)] + Σ(wᵢ − 1/N)εᵢ. Its covariance with the 1/N
portfolio is m·cov(R_e, f), because the idiosyncratic part is orthogonal to 1/N.
Expected utility, relative to 1/N, is

  U(β) = m·μ_f − γ·m·σ_ef − (γ/2)[m²·D²σ²_ρ + D²·q(β)],    (5.1)

with μ_f = E[f] = ρ̄D and σ_ef = cov(R_e, f). Under estimation risk, μ_f is replaced by the
shrunk ĉ·μ̂_f (§3). The covariance terms are not shrunk: covariances are estimated far
more precisely than means (Chopra & Ziemba 1993).

**Prediction.** β\* = argmax U(β) and **N_eff\* = exp H(w(β\*))**. In real time, each
month uses the actual score vector z (`ep_lib.theory_beta`). Note that γ·σ_ef < 0, as for
a low-volatility tilt that lowers market risk, makes tilting worthwhile even with no
return information. That is minimum variance entering through covariances, not through
the IC.

**Closed form** (σ_ef = 0, normal scores, large N). From the first-order condition of
(5.1) with m = β:

  c·ρ̄ = γD·β·[σ²_ρ + e^{β²}/N],  N_eff\*/N = exp(−β\*²/2).    (5.2)

**Numbers** for N = 100, T = 36 and γD = 0.25 (γ = 2.5, the Black–Litterman standard;
D = 10% a month):

| IC (ρ̄) | Grinold (σ²_ρ = 0): c | β\* | **N_eff\*/N** | Qian–Hua (σ²_ρ = 0.01): c | β\* | **N_eff\*/N** |
|---|---|---|---|---|---|---|
| 0.00 | 0 | 0 | **1.00** | 0 | 0 | **1.00** |
| 0.01 | 0.265 | 0.67 | **0.80** | 0.153 | 0.29 | **0.96** |
| 0.02 | 0.590 | 1.18 | **0.50** | 0.419 | 0.96 | **0.63** |
| 0.03 | 0.764 | 1.38 | **0.39** | 0.618 | 1.26 | **0.45** |
| 0.05 | 0.900 | 1.56 | **0.30** | 0.818 | 1.51 | **0.32** |
| 0.08 | 0.958 | 1.70 | **0.24** | 0.920 | 1.68 | **0.25** |

(These c values use the population t of §3 without the (T−5)/T factor. The real-time rule
uses (3.3).)

**The thesis made exact.** Two properties follow from (5.2):
- β\* is increasing in c (the left side rises with c, the right side rises with β);
- for small β, β\* ≈ c·β°, where β° is the full-information tilt.

So the portfolio sits a fraction 1 − c = 1/(1+t²) of the way back from the
full-information portfolio toward 1/N. To second order, the entropy given up, ln N − H,
scales with c². "Hold as much entropy as you have ignorance" is a statement about the
**knowledge share c**, and it maps into effective N through (4.2).

## 6. What the theory predicts (the tests)

- **P1, no information means 1/N.** If the ex-ante IC t-statistic is ≤ 1, then N_eff\* = N.
  This applies to the "none" signal (a rolling historical mean) whenever its IC is
  noise.
- **P2, direction.** N_eff\* falls as the ex-ante IC (or its t) rises.
- **P3, amount.** The out-of-sample-optimal effective N on the dial is close to the
  predicted N_eff\*. This is tested against a block-bootstrap interval for the empirical
  optimum.
- **P4, calibration.** The theory says E[fₜ₊₁ | info] = ĉₜ·μ̂_f,t. Regress the realised
  unit-tilt return on the shrunk forecast (Mincer–Zarnowitz). The slope should be 1. An
  unshrunk forecast should give a slope near the average ĉ, i.e. below 1, because the raw
  plug-in is over-confident.
- **P5, the 1/N puzzle.** For N = 100 stocks, plug-in mean–variance from sample means
  should lose to 1/N out of sample, since c\* ≈ 0 by (2.2).

## 7. Assumptions, and where they could fail

1. **A stable IC over the 36-month window.** Momentum crashes break this. The
   σ²_ρ term absorbs part of it, but not regime shifts.
2. **Independent residuals.** Sector clustering raises the true cost of concentration
   above D²q(β). If so, the empirical optimum will sit at a *higher* N_eff than predicted.
   That is a known direction of failure, which we state in advance.
3. **The nonlinear map.** The shrinkage c is derived for a linear tilt and applied through
   the Gibbs map. This is exact for small β and an approximation otherwise. The simulation
   (Phase 4) measures the error.
4. **Utility vs Sharpe.** The theory optimises CEQ at γ = 2.5. A Sharpe-maximising
   investor behaves like γ = μ_e/σ_e², the Black–Litterman implied risk aversion of the
   1/N holder (about 2–3 for equity). CEQ is the primary criterion; the Sharpe ratio is
   reported alongside.
5. **Costs.** The theory ignores trading costs. Turnover rises as N_eff falls, so net of
   costs the optimum should sit at a slightly higher N_eff than predicted.

## References

See `LITERATURE.md` (Kan & Zhou 2007; Tu & Zhou 2011; DeMiguel, Garlappi & Uppal 2009;
DeMiguel, Garlappi, Nogales & Uppal 2009; Grinold 1989; Qian & Hua 2004; Jaynes 1957;
Chopra & Ziemba 1993; Jagannathan & Ma 2003).
