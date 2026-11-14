"""Phase 4: simulate a market with known truth and check that the method recovers the
theory's optimal entropy (paper 3).

Market: N = 100 stocks, monthly.  r_{i,t+1} = m_{t+1} + s_{k(i),t+1} + rho_t * X * z_{i,t} + e_{i,t+1}
  market m ~ (0.006, 0.05); 4 sector factors s_k ~ (0, 0.03); idiosyncratic e ~ (0, 0.08);
  normal, or multivariate-t with 5 degrees of freedom scaled to the same variances.
  A "noisy oracle" signal z_t (normal scores, new every month) with true IC
  rho_t = rho_bar + sigma_rho * eta_t, sigma_rho = 0.05.
  X = sqrt(0.03^2 + 0.08^2), so corr(z, r) is about rho_t.

Pipeline (identical to the real-data run, scripts/ep_lib.py):
  each month, from the past 36 months of realised Spearman ICs: t-stat, knowledge share
  c = (T-5)/T * max(0, 1 - 1/t^2), theory beta* (eq. 5.1 of THEORY.md), the Gibbs dial
  at fixed effective-N levels, and the theory rule.

Questions answered:
  Q1  does the theory's predicted N_eff*/N match the true optimum of the dial (argmax of
      CEQ, gamma = 2.5, over a 20,000-month run)?
  Q2  does the theory rule's CEQ come close to the best fixed dial level?
  Q3  how many months of out-of-sample data does it take to see it (argmax hit rate and
      the probability the rule beats 1/N, by evaluation window)?
Outputs: results/entropy_portfolio/simulation.json, simulation.md (written by hand from
the json).  Seed fixed: one command reproduces every number.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
import ep_lib as L  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "entropy_portfolio"
N, K_SEC, T_IC, GAMMA = 100, 4, 36, 2.5
MONTHS = 20000
LEVELS = np.array([1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05])
IC_GRID = [0.0, 0.01, 0.02, 0.03, 0.05, 0.08]
SIG_RHO = 0.05
SIG_M, MU_M, SIG_S, SIG_E = 0.05, 0.006, 0.03, 0.08
X_SCALE = math.sqrt(SIG_S ** 2 + SIG_E ** 2)
BETA_GRID = np.linspace(0.0, 4.0, 801)
KAPPAS = [0.5, 1.0, 1.5, 2.0, "no-shrink", "threshold"]


def dial_tables(n):
    """Precompute, for normal scores of n stocks (a fixed set every month, permuted), the
    Gibbs moments on a beta grid and the beta for each N_eff level."""
    z = L.normal_scores(np.arange(n))
    m = np.empty(len(BETA_GRID))
    q = np.empty(len(BETA_GRID))
    ne = np.empty(len(BETA_GRID))
    for j, b in enumerate(BETA_GRID):
        w = L.gibbs(z, b)
        m[j], q[j], ne[j] = w @ z, (w ** 2).sum() - 1 / n, L.neff_shannon(w) / n
    lv_beta = np.array([L.gibbs_beta_for_neff(z, lv) for lv in LEVELS])
    return {"m": m, "q": q, "ne": ne, "lv_beta": lv_beta}


TAB = dial_tables(N)


def theory_beta_grid(mu_f, var_rho_D2, cov_ef, D2, gamma=GAMMA):
    U = TAB["m"] * mu_f - gamma * TAB["m"] * cov_ef - 0.5 * gamma * (
        TAB["m"] ** 2 * var_rho_D2 + D2 * TAB["q"])
    j = int(np.argmax(U))
    return (BETA_GRID[j], TAB["ne"][j]) if U[j] > 0 else (0.0, 1.0)


def knowledge_share(ic_hist, T=T_IC):
    mu, sd = ic_hist.mean(), ic_hist.std(ddof=1)
    if mu <= 0 or sd <= 0:
        return 0.0, 0.0
    t = mu / (sd / math.sqrt(T))
    return (T - 5) / T * max(0.0, 1 - 1 / t ** 2), t


def simulate(rho_bar, tails, seed):
    rng = np.random.default_rng(seed)
    sector = np.repeat(np.arange(K_SEC), N // K_SEC)

    def draw(shape):
        x = rng.standard_normal(shape)
        if tails == "t5":  # multivariate-t(5) scaled to unit variance
            x = x / np.sqrt(rng.chisquare(5, size=shape[0])[:, None] / 3.0)
        return x

    Tm = MONTHS + T_IC + 1
    mkt = MU_M + SIG_M * draw((Tm, 1))[:, 0]
    sec = SIG_S * draw((Tm, K_SEC))
    eps = SIG_E * draw((Tm, N))
    rho = rho_bar + SIG_RHO * rng.standard_normal(Tm)
    zbase = L.normal_scores(np.arange(N))
    Z = np.array([rng.permutation(zbase) for _ in range(Tm)])  # signal known at t
    # return realised over month t+1 uses z_t and rho_t
    R = np.empty((Tm, N))
    R[0] = np.nan
    R[1:] = (mkt[1:, None] + sec[1:, sector] + rho[:-1, None] * X_SCALE * Z[:-1] + eps[1:])
    # realised monthly diagnostics for the signal formed at t (needs R[t+1])
    IC = np.array([stats.spearmanr(Z[t], R[t + 1])[0] for t in range(Tm - 1)])
    D = R[1:].std(1, ddof=1)
    Re = R[1:].mean(1)
    Wl = np.array([L.gibbs(zbase, b) for b in TAB["lv_beta"]])  # level weights on sorted z
    level_ret, rule_ret, rule_ne, rule_c, ew_ret = [], [], [], [], []
    kap_ret = {k: [] for k in KAPPAS}
    for t in range(T_IC, Tm - 1):
        h = slice(t - T_IC, t)  # signals formed at t-36..t-1, all realised by t
        c, _ = knowledge_share(IC[h])
        Dbar = D[h].mean()
        mu_f = c * IC[h].mean() * Dbar
        var_rho_D2 = Dbar ** 2 * max(IC[h].var(ddof=1) - 1 / (N - 1), 0.0)
        f = IC[h] * D[h]
        cov_ef = np.cov(Re[h], f, ddof=1)[0, 1]
        b_star, ne_star = theory_beta_grid(mu_f, var_rho_D2, cov_ef, Dbar ** 2)
        kb = {}
        for kap in KAPPAS:  # real-time multipliers on the knowledge share (kappa=1: theory)
            if kap == "no-shrink":  # act fully whenever the mean IC is positive
                ck = 1.0 if IC[h].mean() > 0 else 0.0
            elif kap == "threshold":  # act fully only if t > 1 (the theory's threshold)
                ck = 1.0 if c > 0 else 0.0
            else:
                ck = min(kap * c, 1.0)
            kb[kap] = theory_beta_grid(ck * IC[h].mean() * Dbar, var_rho_D2, cov_ef,
                                       Dbar ** 2)[0]
        order = np.argsort(Z[t])  # map sorted-score weights to stocks
        r_next = R[t + 1][order]
        level_ret.append(Wl @ r_next)
        rule_ret.append(L.gibbs(zbase, b_star) @ r_next)
        for kap in KAPPAS:
            kap_ret[kap].append(L.gibbs(zbase, kb[kap]) @ r_next)
        rule_ne.append(ne_star)
        rule_c.append(c)
        ew_ret.append(r_next.mean())
    return (np.array(level_ret), np.array(rule_ret), np.array(rule_ne), np.array(rule_c),
            np.array(ew_ret), float(D.mean()), float(np.var(IC)),
            {k: np.array(v) for k, v in kap_ret.items()})


def full_info_prediction(rho_bar, Dbar, var_ic):
    """Theory with c = 1 and the true parameters: the optimum for an investor who knows the
    IC.  This is what an ex-post best fixed dial level estimates."""
    if rho_bar <= 0:
        return 1.0
    var_rho_D2 = Dbar ** 2 * max(var_ic - 1 / (N - 1), 0.0)
    return theory_beta_grid(rho_bar * Dbar, var_rho_D2, 0.0, Dbar ** 2)[1]


def population_prediction(rho_bar, Dbar, var_ic):
    """Theory with the true parameters (no estimation of the IC mean beyond T=36)."""
    if rho_bar <= 0:
        return 1.0, 0.0
    t = rho_bar * math.sqrt(T_IC) / math.sqrt(var_ic)
    c = (T_IC - 5) / T_IC * t * t / (1 + t * t)
    var_rho_D2 = Dbar ** 2 * max(var_ic - 1 / (N - 1), 0.0)
    _, ne = theory_beta_grid(c * rho_bar * Dbar, var_rho_D2, 0.0, Dbar ** 2)
    return ne, c


def main():
    out = {"settings": {"N": N, "T_ic": T_IC, "gamma": GAMMA, "months": MONTHS,
                        "levels": LEVELS.tolist(), "sigma_rho": SIG_RHO}, "runs": []}
    for tails in ("normal", "t5"):
        for k, rho_bar in enumerate(IC_GRID):
            lr, rr, rne, rc, ew, Dbar, var_ic, kr = simulate(rho_bar, tails,
                                                         L.SEED + 100 * k + (tails == "t5"))
            ceq_lv = np.array([L.ceq(lr[:, j], GAMMA) for j in range(len(LEVELS))])
            sr_lv = np.array([L.sharpe(lr[:, j]) for j in range(len(LEVELS))])
            j_best = int(np.argmax(ceq_lv))
            pop_ne, pop_c = population_prediction(rho_bar, Dbar, var_ic)
            full_ne = full_info_prediction(rho_bar, Dbar, var_ic)
            # interpolated ex-post optimum (parabola through the best grid point and its
            # neighbours, in level units)
            ceq_kap = {str(k): L.ceq(v, GAMMA) * 100 for k, v in kr.items()}
            # Q3: evaluation windows
            q3 = {}
            for win in (60, 120, 240, 480):
                nb = len(rr) // win
                hit, beat = 0, 0
                for b in range(nb):
                    s = slice(b * win, (b + 1) * win)
                    jb = int(np.argmax([L.ceq(lr[s, j], GAMMA) for j in range(len(LEVELS))]))
                    hit += abs(LEVELS[jb] - LEVELS[j_best]) <= 0.1 + 1e-9
                    beat += L.ceq(rr[s], GAMMA) > L.ceq(ew[s], GAMMA)
                q3[str(win)] = {"windows": nb, "argmax_within_0.1": hit / nb,
                                "rule_beats_1N": beat / nb}
            d = rr - ew - 0.5 * GAMMA * ((rr - rr.mean()) ** 2 - (ew - ew.mean()) ** 2)
            months_t2 = (2 * d.std(ddof=1) / d.mean()) ** 2 if d.mean() > 0 else None
            run = {
                "tails": tails, "ic": rho_bar, "D": Dbar, "var_ic": var_ic,
                "ceq_by_level_pct": (ceq_lv * 100).round(4).tolist(),
                "sharpe_by_level": sr_lv.round(4).tolist(),
                "true_opt_level": float(LEVELS[j_best]),
                "pred_level_realtime_mean": float(rne.mean()),
                "pred_level_realtime_median": float(np.median(rne)),
                "pred_level_population": pop_ne, "c_population": pop_c,
                "pred_level_full_info": full_ne,
                "ceq_by_kappa_pct": ceq_kap,
                "best_kappa": max(ceq_kap, key=ceq_kap.get),
                "c_realtime_mean": float(rc.mean()),
                "share_months_c_zero": float((rc == 0).mean()),
                "ceq_rule_pct": L.ceq(rr, GAMMA) * 100, "sharpe_rule": L.sharpe(rr),
                "ceq_best_level_pct": float(ceq_lv[j_best] * 100),
                "ceq_1N_pct": float(ceq_lv[0] * 100),
                "rule_minus_best_pct": (L.ceq(rr, GAMMA) - ceq_lv[j_best]) * 100,
                "rule_minus_1N_pct": (L.ceq(rr, GAMMA) - ceq_lv[0]) * 100,
                "months_for_t2_rule_vs_1N": months_t2,
                "q3": q3,
            }
            out["runs"].append(run)
            print(f"   full-info pred {full_ne:.2f} | CEQ by kappa " + " ".join(
                f"{k}:{v:.3f}" for k, v in ceq_kap.items()))
            print(f"{tails:6s} IC {rho_bar:.2f}: true opt {run['true_opt_level']:.2f} | pred rt "
                  f"{run['pred_level_realtime_mean']:.2f} pop {pop_ne:.2f} | c rt "
                  f"{run['c_realtime_mean']:.2f} pop {pop_c:.2f} | CEQ% 1/N "
                  f"{run['ceq_1N_pct']:.3f} best {run['ceq_best_level_pct']:.3f} rule "
                  f"{run['ceq_rule_pct']:.3f} | months(t=2) "
                  f"{'-' if months_t2 is None else round(months_t2)} | hit120 "
                  f"{q3['120']['argmax_within_0.1']:.2f} beat120 {q3['120']['rule_beats_1N']:.2f}")
    (OUT / "simulation.json").write_text(json.dumps(out, indent=2, default=float))


if __name__ == "__main__":
    main()
