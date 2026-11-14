"""Unit tests for scripts/ep_lib.py (paper 3).  Run: python scripts/ep_tests.py

Each test compares the code with a number worked out by hand or with an independent
route to the same answer.  Exits non-zero on any failure."""
from __future__ import annotations

import math
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import ep_lib as L  # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
    if not ok:
        FAILS.append(name)


# 1. Ledoit-Wolf on a hand-computed 4 x 2 example --------------------------------
# x1=(2,2) x2=(-2,-2) x3=(1,-1) x4=(-1,1); means are zero.
# S = [[2.5,1.5],[1.5,2.5]], m = 2.5, d^2 = (1.5^2*2)/2 = 2.25.
# ||x_t x_t' - S||_F^2 = 17 for every t  ->  b_bar^2 = (4*17/2)/16 = 2.125.
# b^2 = min(2.125, 2.25) = 2.125, shrinkage = 2.125/2.25 = 17/18.
# Sigma* = (17/18)*2.5*I + (1/18)*S  ->  diag 2.5, off-diagonal 1.5/18 = 0.083333.
X = np.array([[2, 2], [-2, -2], [1, -1], [-1, 1]], float)
Sig, s = L.lw_identity(X)
check("LW shrinkage = 17/18", abs(s - 17 / 18) < 1e-12, f"{s:.6f}")
check("LW Sigma*", np.allclose(Sig, [[2.5, 1.5 / 18], [1.5 / 18, 2.5]], atol=1e-12),
      np.array2string(Sig, precision=6))

# 2. Gibbs closed form equals the mirror-descent fixed point (S = 0) ----------------
rng = np.random.default_rng(1)
z = rng.standard_normal(30)
mu = 0.01 * z
tau = 0.004
w_md, kkt, it = L.entropy_mv(mu, None, gamma=1.0, tau=tau)
w_cf = L.gibbs(z, 0.01 / tau)
check("mirror descent = Gibbs closed form", np.abs(w_md - w_cf).max() < 1e-10,
      f"max diff {np.abs(w_md - w_cf).max():.2e}, kkt {kkt:.1e}, iters {it}")

# 3. Entropy-regularised MV with a covariance: KKT residual and limits -------------
A = rng.standard_normal((60, 8))
S = np.cov(A.T) * 1e-3
mu = rng.normal(0.01, 0.01, 8)
w, kkt, it = L.entropy_mv(mu, S, gamma=3.0, tau=0.002)
check("entropy-MV KKT residual < 1e-9", kkt < 1e-9, f"{kkt:.1e} in {it} iters")
w_big, _, _ = L.entropy_mv(mu, S, gamma=3.0, tau=10.0)
check("tau large -> 1/N", np.abs(w_big - 1 / 8).max() < 1e-3, f"{np.abs(w_big - 1/8).max():.1e}")
w_small, _, _ = L.entropy_mv(mu, S, gamma=3.0, tau=1e-6, iters=400000)
w_qp, kkt_qp = L.qp_simplex(3.0 * S, mu)
check("tau -> 0 approaches long-only MV (QP)", np.abs(w_small - w_qp).max() < 2e-3,
      f"{np.abs(w_small - w_qp).max():.1e}; QP kkt {kkt_qp:.1e}")

# 4. Long-only GMV equals the unconstrained GMV when that is already positive ----
S2 = np.diag([1.0, 2.0, 4.0])
w_lo = L.w_gmv_longonly(S2)
check("long-only GMV, diagonal S", np.allclose(w_lo, [4 / 7, 2 / 7, 1 / 7], atol=1e-8),
      np.array2string(w_lo, precision=6))

# 5. Gibbs effective N for normal scores: N_eff/N -> exp(-beta^2/2) ----------------
zz = L.normal_scores(np.arange(20000))
for b in (0.5, 1.0, 1.5):
    r = L.neff_shannon(L.gibbs(zz, b)) / len(zz)
    check(f"Gibbs N_eff/N at beta={b}", abs(r - math.exp(-b * b / 2)) < 0.01,
          f"{r:.4f} vs {math.exp(-b * b / 2):.4f}")
bb = L.gibbs_beta_for_neff(zz, 0.5)
check("bisection hits N_eff target", abs(L.neff_shannon(L.gibbs(zz, bb)) / len(zz) - 0.5) < 1e-6,
      f"beta {bb:.4f} vs sqrt(2 ln 2) {math.sqrt(2 * math.log(2)):.4f}")

# 6. Renyi-2 identity: sum w^2 = ||w - 1/N||^2 + 1/N when sum w = 1 ---------------
w = rng.normal(0.1, 0.3, 10)
w = w / w.sum()
check("Renyi-2 = distance to 1/N", abs((w ** 2).sum() - (((w - 0.1) ** 2).sum() + 0.1)) < 1e-12)

# 7. JK-Memmel: identical series -> z = 0; known variance formula ------------------
r = rng.normal(0.01, 0.04, 200)
z0, p0 = L.jkm_test(r, r + 0.0)
check("JKM identical series", abs(z0) < 1e-12 and p0 > 0.999)

# 8. Newey-West with lags=0 equals White standard errors ---------------------------
x = rng.standard_normal(300)
y = 0.5 * x + rng.standard_normal(300) * (1 + np.abs(x))
Xd = np.column_stack([np.ones(300), x])
b_nw, se_nw = L.newey_west_ols(y, Xd, lags=0)
XtXi = np.linalg.inv(Xd.T @ Xd)
e = y - Xd @ b_nw
white = np.sqrt(np.diag(XtXi @ (Xd * e[:, None] ** 2).T @ Xd @ XtXi))
check("Newey-West(0) = White", np.allclose(se_nw, white))

# 9. Kan-Zhou scale: theta2 -> inf gives the finite-sample constant ---------------
c = L.kz_scale(1e9, K=10, T=120)
check("KZ scale limit", abs(c - (109 * 106) / (120 * 118)) < 1e-6, f"{c:.6f}")

# 10. Adjusted theta2 is close to theta2_hat - N/T when theta2_hat is large -------
th = L.theta2_adjusted(0.5, N=5, T=200)
check("KZ adjusted theta2 (large)", abs(th - ((200 - 7) * 0.5 - 5) / 200) < 1e-6, f"{th:.6f}")
th0 = L.theta2_adjusted(0.001, N=5, T=200)
check("KZ adjusted theta2 >= 0 near zero", th0 >= 0, f"{th0:.6g}")

# 11. Simplex projection -----------------------------------------------------------
pv = L.proj_simplex(np.array([0.5, 0.5, 0.5]))
check("simplex projection", np.allclose(pv, [1 / 3] * 3))

# 12. LW Sharpe bootstrap: size under H0 and power under a clear alternative ------
rej = 0
for rep in range(60):
    g = np.random.default_rng(100 + rep)
    a = g.normal(0.01, 0.05, 240)
    bser = 0.5 * a + math.sqrt(0.75) * g.normal(0.0, 0.05, 240) + 0.005  # same SR = 0.2
    rej += L.lw_sharpe_test(a, bser, M=199, seed=rep)[2] < 0.10
check("LW bootstrap size at 10% (60 reps) <= 0.2", rej / 60 <= 0.2, f"rejection rate {rej/60:.3f}")
g = np.random.default_rng(7)
a = g.normal(0.02, 0.05, 240)
bser = 0.5 * a + math.sqrt(0.75) * g.normal(0.0, 0.05, 240) - 0.01
d, se, p = L.lw_sharpe_test(a, bser, M=499)
check("LW bootstrap power (SR gap 0.4)", p < 0.01, f"d={d:.3f}, p={p:.3f}")

# 13. SPA: ordering p_lower <= p_consistent <= p_upper; a clearly superior model is found;
#     identical models are not
g = np.random.default_rng(11)
noise = g.normal(0, 0.04, (240, 5))
d_sup = noise.copy()
d_sup[:, 0] += 0.012  # model 0 beats the benchmark by about t = 4.6
r_sup = L.spa_test(d_sup, B=999)
check("SPA finds a superior model", r_sup["p_consistent"] < 0.01, f"{r_sup}")
r_null = L.spa_test(noise - noise.mean(0) - 0.002, B=999)
check("SPA null (all models slightly worse)", r_null["p_consistent"] > 0.2, f"{r_null}")
check("SPA p ordering", r_null["p_lower"] <= r_null["p_consistent"] + 1e-12 <= r_null["p_upper"] + 2e-12)

print()
print("ALL PASS" if not FAILS else f"{len(FAILS)} FAILED: {FAILS}")
sys.exit(1 if FAILS else 0)
