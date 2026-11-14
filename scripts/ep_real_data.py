"""Phases 6-7 of paper 3: the pre-registered real-data run (India primary, US second).

Implements docs/entropy_portfolio/PREREGISTRATION.md exactly; deviations are logged there.
  python scripts/ep_real_data.py            # pre-holdout evaluation windows
  python scripts/ep_real_data.py --holdout  # the holdout, run once at the end
Outputs: results/entropy_portfolio/{real|holdout}/<market>_returns.csv, summary.json
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
import ep_lib as L  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data_processed"
GAMMA, NU, T_IC = 2.5, 100, 36
LEVELS = np.array([1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05])
BETA_GRID = np.linspace(0.0, 6.0, 1201)
SIGNALS = ["none", "mom", "lowvol"]
MARKETS = {
    "india": dict(path=DATA / "nse_survivorship_free_adj_nohole.parquet", floor=None,
                  first_signal="2007-01", eval=("2010-02", "2020-12"),
                  hold=("2021-01", "2025-06"), rf="const"),
    "us": dict(path=DATA / "extended_prices.parquet", floor=1.0, first_signal="2002-01",
               eval=("2005-02", "2020-12"), hold=("2021-01", "2024-12"), rf="french"),
}
RF_INDIA_MONTHLY = (1.065) ** (1 / 12) - 1  # deviation D1: constant 6.5% a year
US_COST = {"primary": 0.0010, "s25": 0.0025, "s50": 0.0050}


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


# ----------------------------------------------------------------------------- data
def load_market(name):
    cfg = MARKETS[name]
    raw = pd.read_parquet(cfg["path"], columns=["date", "symbol", "close", "volume"])
    raw["date"] = pd.to_datetime(raw["date"])
    close = raw.pivot_table(index="date", columns="symbol", values="close")
    volume = raw.pivot_table(index="date", columns="symbol", values="volume")
    del raw
    if cfg["floor"] is not None:
        close = close.where(close >= cfg["floor"])
    close = close.where(close > 0)
    ret = close.pct_change(fill_method=None)
    per = close.index.to_period("M")
    me_pos = np.where(per[1:] != per[:-1])[0]
    me_pos = np.append(me_pos, len(per) - 1)
    me_per = per[me_pos]
    tv63 = (close * volume).rolling(63, min_periods=40).mean().iloc[me_pos]
    cnt252 = ret.notna().rolling(252).sum().iloc[me_pos]
    vol252 = ret.rolling(252, min_periods=200).std().iloc[me_pos]
    close_me = close.iloc[me_pos]
    for df in (tv63, cnt252, vol252, close_me):
        df.index = me_per
    mret = (1 + ret.fillna(0.0)).groupby(per).prod() - 1  # cash after delisting
    nobs = ret.notna().groupby(per).sum()
    mret_sig = mret.where(nobs > 0)
    member = None
    if name == "us":
        lk = pd.read_csv(DATA / "sp500_universe_lookup.csv", parse_dates=["date"])
        member = pd.DataFrame(False, index=me_per, columns=close.columns)
        for d, tick in zip(lk["date"].dt.to_period("M"), lk["tickers"]):
            if d in member.index:
                names = [t for t in str(tick).split(",") if t in member.columns]
                member.loc[d, names] = True
    if cfg["rf"] == "french":
        from ep_replicate_dgu import read_first_monthly_block
        rf = read_first_monthly_block(ROOT / "data_raw" / "french_ff" /
                                      "F-F_Research_Data_Factors.csv")["RF"]
    else:
        rf = pd.Series(RF_INDIA_MONTHLY, index=mret.index)
    return dict(ret=ret, me_pos=pd.Series(me_pos, index=me_per), tv63=tv63, cnt252=cnt252,
                vol252=vol252, close_me=close_me, mret=mret, mret_sig=mret_sig,
                member=member, rf=rf)


# ----------------------------------------------------------------------------- dial math
def dial_arrays(z):
    """Gibbs moments for this month's score vector on the beta grid (vectorised)."""
    A = BETA_GRID[:, None] * z[None, :]
    A = A - A.max(1, keepdims=True)
    W = np.exp(A)
    W /= W.sum(1, keepdims=True)
    m = W @ z
    q = (W ** 2).sum(1) - 1.0 / len(z)
    with np.errstate(divide="ignore", invalid="ignore"):
        H = -(np.where(W > 0, W * np.log(W), 0.0)).sum(1)
    ne = np.exp(H) / len(z)
    return m, q, ne


def beta_for_level(ne, level):
    if level >= 1.0:
        return 0.0
    # ne is decreasing in beta; interpolate on the reversed arrays
    return float(np.interp(level, ne[::-1], BETA_GRID[::-1]))


def theory_beta(m, q, ne, mu_f, var_rho_D2, cov_ef, D2):
    U = m * mu_f - GAMMA * m * cov_ef - 0.5 * GAMMA * (m * m * var_rho_D2 + D2 * q)
    j = int(np.argmax(U))
    return (float(BETA_GRID[j]), float(ne[j])) if U[j] > 0 else (0.0, 1.0)


def knowledge_share(ic, grinold_N=None):
    mu, sd = ic.mean(), ic.std(ddof=1)
    if mu <= 0 or sd <= 0:
        return 0.0, 0.0
    t2 = T_IC * grinold_N * mu * mu if grinold_N else (mu / (sd / math.sqrt(T_IC))) ** 2
    return (T_IC - 5) / T_IC * max(0.0, 1 - 1 / t2), math.sqrt(t2)


# ----------------------------------------------------------------------------- run
def build_months(d, name, first, last):
    """Universe, signals and next-month returns for signal months first..last."""
    out = {}
    pers = pd.period_range(first, last, freq="M")
    cm = d["close_me"]
    cm12 = cm.shift(12)
    mom_all = cm.shift(1) / cm12 - 1
    none_all = d["mret_sig"].rolling(36, min_periods=24).mean()
    for p in pers:
        if p + 1 not in d["mret"].index or p not in cm.index:
            continue
        ok = cm.loc[p].notna() & cm12.loc[p].notna() & (d["cnt252"].loc[p] >= 200)
        if d["member"] is not None:
            ok &= d["member"].loc[p]
        tv = d["tv63"].loc[p][ok].dropna().sort_values(ascending=False)
        uni = tv.index[:NU]
        if len(uni) < NU:
            continue
        sig = {"mom": mom_all.loc[p, uni], "lowvol": -d["vol252"].loc[p, uni],
               "none": none_all.loc[p, uni]}
        rnext = d["mret"].loc[p + 1, uni] - d["rf"].get(p + 1, d["rf"].iloc[-1])
        terc = pd.Series(np.repeat([0, 1, 2], [34, 33, 33])[: len(uni)], index=uni)
        out[p] = dict(uni=uni, sig=sig, rnext=rnext, terc=terc,
                      rtot=d["mret"].loc[p + 1, uni])
    return out


def zscores(s):
    z = pd.Series(0.0, index=s.index)
    ok = s.notna()
    z[ok] = L.normal_scores(s[ok].values)
    return z


def baselines(d, p, uni):
    pos = int(d["me_pos"].loc[p])
    X = d["ret"].iloc[pos - 251: pos + 1][uni].fillna(0.0).values
    mu_d = X.mean(0)
    S_d = L.cov_mle(X)
    S_m, mu_m = 21 * S_d, 21 * mu_d
    w = {}
    w["mv"] = L.w_mv(mu_d, S_d)
    w["min"] = L.w_gmv(S_d)
    w["min-LW"] = L.w_gmv(L.lw_identity(X)[0])
    w["min-norm2-CV"] = L.w_gmv_norm2_cv(X)
    w["min-c"] = L.qp_simplex(S_m, np.zeros(len(uni)), iters=5000)[0]
    w["mv-c"] = L.qp_simplex(GAMMA * S_m, mu_m, iters=5000)[0]
    w["KZ3"] = L.w_kz3(mu_d, S_d, 252, GAMMA)
    w["TZ"] = L.w_tz(mu_d, S_d, 252, GAMMA)[0]
    return {k: pd.Series(v, index=uni) for k, v in w.items()}


def run_market(name, window, holdout):
    log(f"{name}: loading")
    d = load_market(name)
    cfg = MARKETS[name]
    first_sig = pd.Period(cfg["first_signal"], "M")
    ev0, ev1 = pd.Period(window[0], "M"), pd.Period(window[1], "M")
    months = build_months(d, name, first_sig, ev1 - 1)
    log(f"{name}: {len(months)} signal months built")
    sig_months = sorted(months)
    # realised IC, D, R_e for each signal month (known one month later)
    diag = {s: {} for s in SIGNALS}
    for p in sig_months:
        mo = months[p]
        r = mo["rnext"]
        lo, hi = r.quantile(0.01), r.quantile(0.99)
        D = r.clip(lo, hi).std(ddof=1)
        Re = r.mean()
        for s in SIGNALS:
            sv = mo["sig"][s]
            ok = sv.notna()
            ic = stats.spearmanr(sv[ok], r[ok])[0]
            diag[s][p] = (ic, D, Re)
    # weights per strategy per month
    W = {}  # (strategy) -> {p: Series}
    info = {s: {} for s in SIGNALS}
    level_hist = {(s, lv): {} for s in SIGNALS for lv in LEVELS}
    for p in sig_months:
        ret_month = p + 1
        mo = months[p]
        uni = mo["uni"]
        need_rules = ret_month >= ev0
        hist = [q for q in sig_months if p - T_IC <= q <= p - 1]
        W.setdefault("1/N", {})[p] = pd.Series(1.0 / NU, index=uni)
        for s in SIGNALS:
            z = zscores(mo["sig"][s]).values
            m, q, ne = dial_arrays(z)
            for lv in LEVELS:
                b = beta_for_level(ne, lv)
                W.setdefault(f"{s}:L{lv:.2f}", {})[p] = pd.Series(L.gibbs(z, b), index=uni)
            if not need_rules or len(hist) < T_IC:
                continue
            ic = np.array([diag[s][h][0] for h in hist])
            D = np.array([diag[s][h][1] for h in hist])
            Re = np.array([diag[s][h][2] for h in hist])
            Dbar = D.mean()
            var_rho_D2 = Dbar ** 2 * max(ic.var(ddof=1) - 1 / (NU - 1), 0.0)
            cov_ef = np.cov(Re, ic * D, ddof=1)[0, 1]
            c, t = knowledge_share(ic)
            b1, ne1 = theory_beta(m, q, ne, c * ic.mean() * Dbar, var_rho_D2, cov_ef, Dbar ** 2)
            c2 = 1.0 if ic.mean() > 0 else 0.0
            b2, ne2 = theory_beta(m, q, ne, c2 * ic.mean() * Dbar, var_rho_D2, cov_ef,
                                  Dbar ** 2)
            cg, _ = knowledge_share(ic, grinold_N=NU)
            bg, neg = theory_beta(m, q, ne, cg * ic.mean() * Dbar, 0.0, cov_ef, Dbar ** 2)
            W.setdefault(f"{s}:R1", {})[p] = pd.Series(L.gibbs(z, b1), index=uni)
            W.setdefault(f"{s}:R2", {})[p] = pd.Series(L.gibbs(z, b2), index=uni)
            W.setdefault(f"{s}:R1G", {})[p] = pd.Series(L.gibbs(z, bg), index=uni)
            info[s][p] = dict(c=c, t=t, ne_R1=ne1, ne_R2=ne2, ne_R1G=neg, beta_R1=b1,
                              icbar=float(ic.mean()), Dbar=float(Dbar),
                              forecast_shrunk=c * ic.mean() * Dbar,
                              forecast_raw=ic.mean() * Dbar)
        if need_rules:
            for k, v in baselines(d, p, uni).items():
                W.setdefault(k, {})[p] = v
    # R3: each month pick the dial level with the best CEQ over its own realised gross
    # returns in the past 36 months (signal months p-36..p-1, all realised by p)
    for s in SIGNALS:
        lr = {lv: {q: float((W[f"{s}:L{lv:.2f}"][q] * months[q]["rnext"]).sum())
                   for q in sig_months} for lv in LEVELS}
        for p in sig_months:
            if p not in info[s]:
                continue
            hist = [q for q in sig_months if p - T_IC <= q <= p - 1]
            ceqs = [L.ceq(np.array([lr[lv][q] for q in hist]), GAMMA) for lv in LEVELS]
            best = LEVELS[int(np.argmax(ceqs))]
            W.setdefault(f"{s}:R3", {})[p] = W[f"{s}:L{best:.2f}"][p]
            info[s][p]["R3_level"] = float(best)
    log(f"{name}: weights built")
    # returns, turnover, costs
    eval_sig = [p for p in sig_months if ev0 <= p + 1 <= ev1]
    res = {}
    for k, wd in W.items():
        rows = []
        prev = None
        for p in sig_months:
            if p not in wd:
                prev = None
                continue
            mo = months[p]
            w = wd[p]
            if prev is None:  # first month of a strategy: switch from 1/N, not from cash
                dw = w.sub(pd.Series(1.0 / NU, index=mo["uni"]), fill_value=0.0).abs()
            else:
                dw = w.sub(prev, fill_value=0.0).abs()
            if name == "india":
                stat = 0.00136 if p < pd.Period("2013-06", "M") else 0.00111
                imp = mo["terc"].reindex(dw.index).map({0: 0.0005, 1: 0.0010, 2: 0.0020})
                rate = stat + imp.fillna(0.0020)
                cost = float((dw * rate).sum())
                costs = {"net": cost}
            else:
                to = float(dw.sum())
                costs = {"net": to * US_COST["primary"], "net25": to * US_COST["s25"],
                         "net50": to * US_COST["s50"]}
            gross = float((w * mo["rnext"]).sum())
            g = w * (1 + mo["rtot"])
            sgn = g.sum()
            prev = g / sgn if abs(sgn) > 1e-12 else w
            if ev0 <= p + 1 <= ev1:
                row = {"month": str(p + 1), "gross": gross, "turnover": float(dw.sum()),
                       "neff": (L.neff_shannon(w.values) if (w.values >= -1e-12).all()
                                else L.neff_renyi2(w.values))}
                for ck, cv in costs.items():
                    row[ck] = gross - cv
                rows.append(row)
        if rows:
            res[k] = pd.DataFrame(rows).set_index("month")
    common = sorted(set.intersection(*[set(v.index) for k, v in res.items()
                                       if not k.split(":")[-1].startswith("L")]))
    res = {k: v.loc[[m for m in v.index if m in common]] for k, v in res.items()}
    log(f"{name}: {len(common)} evaluation months {common[0]}..{common[-1]}")
    return d, months, diag, info, res, common


# ----------------------------------------------------------------------------- analysis
def summarise(res):
    out = {}
    for k, v in res.items():
        o = {"months": len(v), "turnover": float(v["turnover"].mean()),
             "neff_ratio": float(v["neff"].mean() / NU)}
        for col in [c for c in v.columns if c.startswith("gross") or c.startswith("net")]:
            x = v[col].values
            o[col] = {"mean_pct": x.mean() * 100, "sd_pct": x.std(ddof=1) * 100,
                      "sharpe": L.sharpe(x), "ceq25_pct": L.ceq(x, GAMMA) * 100,
                      "ceq1_pct": L.ceq(x, 1.0) * 100}
        out[k] = o
    return out


def pair_test(a, b, M=4999):
    d_, se, p = L.lw_sharpe_test(a, b, b=5, M=M)
    z, pj = L.jkm_test(a, b)
    return {"sr_diff": d_, "lw_p": p, "jkm_p": pj,
            "ceq_diff_pct": (L.ceq(a, GAMMA) - L.ceq(b, GAMMA)) * 100}


def argmax_level_boot(R, B=2000, seed=L.SEED):
    """R: (T, levels) returns; stationary-bootstrap distribution of the CEQ-argmax level."""
    rng = np.random.default_rng(seed)
    T = R.shape[0]
    best = []
    for _ in range(B):
        idx = L.stationary_bootstrap_indices(T, 6.0, rng)
        x = R[idx]
        ceqs = x.mean(0) - 0.5 * GAMMA * x.var(0, ddof=1)
        best.append(LEVELS[int(np.argmax(ceqs))])
    best = np.array(best)
    return float(np.quantile(best, 0.05)), float(np.quantile(best, 0.95)), best


def full_info_prediction(diag_s, eval_sig):
    ic = np.array([diag_s[p][0] for p in eval_sig])
    D = np.array([diag_s[p][1] for p in eval_sig])
    Re = np.array([diag_s[p][2] for p in eval_sig])
    z = L.normal_scores(np.arange(NU))
    m, q, ne = dial_arrays(z)
    Dbar = D.mean()
    var_rho_D2 = Dbar ** 2 * max(ic.var(ddof=1) - 1 / (NU - 1), 0.0)
    cov_ef = np.cov(Re, ic * D, ddof=1)[0, 1]
    mu = ic.mean() * Dbar if ic.mean() > 0 else 0.0
    _, ne_star = theory_beta(m, q, ne, mu, var_rho_D2, cov_ef, Dbar ** 2)
    return float(ne_star), float(ic.mean()), float(ic.std(ddof=1)), float(cov_ef)


def analyse(name, months, diag, info, res, common, holdout):
    netcol = "net"
    summ = summarise(res)
    out = {"market": name, "evaluation": [common[0], common[-1]], "months": len(common),
           "summary": summ}
    g = lambda k, c="gross": res[k][c].values  # noqa: E731
    out["H1"] = {"mv_vs_1N_gross": pair_test(g("mv"), g("1/N")),
                 "mv_vs_1N_net": pair_test(g("mv", netcol), g("1/N", netcol))}
    h2 = {}
    for s in SIGNALS:
        h2[s] = {"R1_vs_1N_net": pair_test(g(f"{s}:R1", netcol), g("1/N", netcol)),
                 "R1_vs_mv_net": pair_test(g(f"{s}:R1", netcol), g("mv", netcol)),
                 "R1_vs_minLW_net": pair_test(g(f"{s}:R1", netcol), g("min-LW", netcol))}
    out["H2"] = h2
    # SPA over 12 real-time models vs 1/N (net, utility differentials)
    base = g("1/N", netcol)
    ub = base - 0.5 * GAMMA * (base - base.mean()) ** 2
    models = [f"{s}:{r}" for s in SIGNALS for r in ("R1", "R2", "R3", "R1G")]
    D = []
    for k in models:
        x = g(k, netcol)
        D.append(x - 0.5 * GAMMA * (x - x.mean()) ** 2 - ub)
    out["SPA"] = {"models": models, **L.spa_test(np.column_stack(D), B=4999, mean_block=6.0)}
    dial_keys = [f"{s}:L{lv:.2f}" for s in SIGNALS for lv in LEVELS]
    Rd = np.column_stack([g(k, netcol) for k in dial_keys])
    pbo, logits = L.pbo_cscv(Rd, S=16)
    out["PBO"] = {"pbo": pbo, "median_logit": float(np.median(logits)), "variants": len(dial_keys)}
    # dial curves and H3
    eval_sig = [pd.Period(m, "M") - 1 for m in common]
    h3 = {}
    for s in SIGNALS:
        keys = [f"{s}:L{lv:.2f}" for lv in LEVELS]
        Rg = np.column_stack([g(k) for k in keys])
        Rn = np.column_stack([g(k, netcol) for k in keys])
        ceq_g = [L.ceq(Rg[:, j], GAMMA) * 100 for j in range(len(LEVELS))]
        ceq_n = [L.ceq(Rn[:, j], GAMMA) * 100 for j in range(len(LEVELS))]
        sr_g = [L.sharpe(Rg[:, j]) for j in range(len(LEVELS))]
        sr_n = [L.sharpe(Rn[:, j]) for j in range(len(LEVELS))]
        lo, hi, _ = argmax_level_boot(Rg)
        pred, icm, icsd, covef = full_info_prediction(diag[s], eval_sig)
        rt = pd.DataFrame(info[s]).T
        rt = rt.loc[[p for p in eval_sig if p in rt.index]]
        rules = {r: summ[f"{s}:{r}"][netcol] for r in ("R1", "R2", "R3", "R1G")}
        h3[s] = {
            "levels": LEVELS.tolist(), "ceq_gross_pct": ceq_g, "ceq_net_pct": ceq_n,
            "sharpe_gross": sr_g, "sharpe_net": sr_n,
            "argmax_gross": float(LEVELS[int(np.argmax(ceq_g))]),
            "argmax_net": float(LEVELS[int(np.argmax(ceq_n))]),
            "argmax_boot90": [lo, hi],
            "full_info_pred": pred, "pred_inside": bool(lo - 1e-9 <= pred <= hi + 1e-9),
            "eval_ic_mean": icm, "eval_ic_sd": icsd, "eval_cov_ef": covef,
            "R1_mean_neff_ratio": float(rt["ne_R1"].mean()),
            "R2_mean_neff_ratio": float(rt["ne_R2"].mean()),
            "mean_c": float(rt["c"].mean()), "share_c_zero": float((rt["c"] == 0).mean()),
            "mean_t": float(rt["t"].mean()),
            "rules_net": rules,
            "R1_vs_R2_net": pair_test(g(f"{s}:R1", netcol), g(f"{s}:R2", netcol)),
        }
    out["H3"] = h3
    # H3d calibration: pooled over signals
    ys, xs, xr = [], [], []
    for s in SIGNALS:
        for p in eval_sig:
            if p in info[s]:
                ic, D, _ = diag[s][p]
                ys.append(ic * D)
                xs.append(info[s][p]["forecast_shrunk"])
                xr.append(info[s][p]["forecast_raw"])
    ys, xs, xr = map(np.array, (ys, xs, xr))
    cal = {}
    for lab, x in (("shrunk", xs), ("raw", xr)):
        bta, se = L.newey_west_ols(ys, np.column_stack([np.ones(len(x)), x]), lags=6)
        cal[lab] = {"slope": float(bta[1]), "se": float(se[1]),
                    "ci95": [float(bta[1] - 1.96 * se[1]), float(bta[1] + 1.96 * se[1])],
                    "n": int(len(x))}
    out["H3d"] = cal
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--holdout", action="store_true")
    ap.add_argument("--markets", default="india,us")
    a = ap.parse_args()
    tag = "holdout" if a.holdout else "real"
    outdir = ROOT / "results" / "entropy_portfolio" / tag
    outdir.mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                            cwd=ROOT).stdout.strip()
    allout = {"commit": commit, "mode": tag}
    for name in a.markets.split(","):
        win = MARKETS[name]["hold" if a.holdout else "eval"]
        d, months, diag, info, res, common = run_market(name, win, a.holdout)
        frame = pd.concat({k: v for k, v in res.items()}, axis=1)
        frame.to_csv(outdir / f"{name}_returns.csv")
        allout[name] = analyse(name, months, diag, info, res, common, a.holdout)
        (outdir / "summary.json").write_text(json.dumps(allout, indent=1, default=float))
        log(f"{name}: done")
    log("all done")


if __name__ == "__main__":
    main()
