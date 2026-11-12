"""
Phase 5: does concentration in FEW business groups predict crisis losses?
Rules: docs/group_dependency/PREREGISTRATION_2.md (commit it before `run`).

Matched portfolios at a formation date 126 trading days before each crisis window:
  B  base: N random top-500 stocks, equal weights
  C  concentrated twin: up to N/2 base stocks swapped, one at a time, for same-industry
     stocks of a business group ALREADY in the portfolio
  D  dispersed twin: the SAME base stocks swapped for same-industry stocks of business
     groups NOT in the portfolio (so C and D hold the same group-affiliated weight)
  C and D must each match B's Meucci effective number of bets and trailing volatility
  within +-5%, and C's group effective N must be <= 85% of B's.
T1 (primary) = DD(C) - DD(D)  (max drawdown in the window; negative = C lost more)

Subcommands:
  time   construction only (no outcome is computed), to fix the budget
  run    the registered tests (T1, T1b, T1-x, T1-hc, T2), once
Run:  OPENBLAS_NUM_THREADS=1 ~/.venvs/strategyhub/bin/python scripts/group_dependency_phase5.py <time|run>
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import group_dependency_pilot as gp  # noqa: E402

gp.MAP_PATH = gp.OUT / "group_map_v2.csv"          # the verified map
OUT = gp.OUT / "phase5"
MAIN = {"Family", "Corporate"}
WINDOWS = [("GFC", "2008-01", "2009-03"), ("Taper", "2013-05", "2013-08"),
           ("ILFS", "2018-08", "2018-10"), ("COVID", "2020-01", "2020-03"),
           ("Hindenburg", "2023-01", "2023-02"), ("Smallcap24", "2024-09", "2025-02")]
FORM_LAG, COV_LEN, COV_MIN = 126, 252, 200
MATCH_TOL, CONC_MAX = 0.05, 0.85
PILOT_DRIVERS = {"Adani", "Reliance ADAG (Anil Ambani)", "Indiabulls (Sameer Gehlaut)",
                 "Future (Kishore Biyani)"}
SEED = 20261112
CFG = {"pairs": 500, "placebos": 200, "ns": (30, 60), "t2_per_n": 3334, "t2_placebos": 200}
_STATE: dict = {}


# ----------------------------------------------------------------------------
# data for one formation date
# ----------------------------------------------------------------------------
def window_positions(P) -> list[dict]:
    idx = (1 + P.mkt.fillna(0)).cumprod()
    out = []
    for name, a, b in WINDOWS:
        s = idx.loc[a].idxmax()
        e = idx.loc[b].idxmin()
        ps, pe = P.dates.get_loc(s), P.dates.get_loc(e)
        out.append({"window": name, "start": str(s.date()), "end": str(e.date()), "ps": ps, "pe": pe,
                    "pf": ps - FORM_LAG, "formation": str(P.dates[ps - FORM_LAG].date()),
                    "market_window_ret": float(idx.iloc[pe] / idx.iloc[ps] - 1)})
    return out


def setup_date(P, G, w: dict, exclude: set = frozenset(), hc_only: bool = False) -> dict:
    f, ps, pe = w["pf"], w["ps"], w["pe"]
    R = P.rets.values
    valid = np.isfinite(R[f - COV_LEN + 1:f + 1]).sum(0)
    uni = P.uni.values[f] & (valid >= COV_MIN)
    fr = G.frame_at(P.dates[f])
    syms = P.syms[uni]
    grp, typ, conf = [], [], []
    for s in syms:
        if s in fr.index:
            r = fr.loc[s]
            grp.append(r["group"]); typ.append(r["group_type"]); conf.append(r["confidence"])
        else:
            grp.append(""); typ.append(""); conf.append("")
    grp, typ, conf = np.array(grp, dtype=object), np.array(typ), np.array(conf)
    keep = ~np.isin(grp, list(exclude))
    syms, grp, typ, conf = syms[keep], grp[keep], typ[keep], conf[keep]
    cols = np.where(uni)[0][keep]
    is_main = np.isin(typ, list(MAIN)) & (grp != "")
    if hc_only:
        is_main &= conf == "high"
    key = np.where(is_main, grp, np.array(["solo:" + s for s in syms], dtype=object))
    gcode = pd.factorize(key)[0]
    ind = pd.factorize(np.array([G.industry.get(s, "") for s in syms], dtype=object))[0]
    X = R[f - COV_LEN + 1:f + 1][:, cols]
    m = np.isfinite(X)
    Xd = np.where(m, X - np.nanmean(X, 0), 0.0)
    n = m.T.astype(float) @ m.astype(float)
    cov = (Xd.T @ Xd) / np.maximum(n - 1, 1)
    Gm = np.cumprod(1 + np.nan_to_num(R[f + 1:pe + 1][:, cols]), axis=0)   # value path from formation
    return {"syms": syms, "gcode": gcode, "is_main": is_main, "ind": ind, "cov": cov,
            "vol": np.sqrt(np.clip(np.diag(cov), 0, None)), "Gm": Gm, "w0": ps - f - 1,
            "n": len(syms), "groupname": key}


def enb_vol(cov_sub: np.ndarray) -> tuple[float, float]:
    """Meucci (2009) effective number of bets for an equal-weight portfolio, and annual vol."""
    k = cov_sub.shape[0]
    w = np.full(k, 1.0 / k)
    lam, E = np.linalg.eigh(cov_sub)
    lam = np.clip(lam, 0, None)
    v = (E.T @ w) ** 2 * lam
    tot = v.sum()
    p = v[v > 0] / tot
    return float(np.exp(-(p * np.log(p)).sum())), float(np.sqrt(tot * 252))


def eff_n_groups(codes: np.ndarray) -> float:
    _, c = np.unique(codes, return_counts=True)
    p = c / c.sum()
    return float(np.exp(-(p * np.log(p)).sum()))


def multi_mask(gcode: np.ndarray, is_main: np.ndarray) -> np.ndarray:
    sizes = np.bincount(gcode)
    return is_main & (sizes[gcode] >= 2)


# ----------------------------------------------------------------------------
# twin construction (no outcomes)
# ----------------------------------------------------------------------------
def build_pair(D: dict, gcode: np.ndarray, aff: np.ndarray, N: int, rng) -> dict | None:
    n, ind, vol, cov = D["n"], D["ind"], D["vol"], D["cov"]
    ng = gcode.max() + 1
    base = rng.choice(n, N, replace=False)
    inB = np.zeros(n, bool); inB[base] = True
    cntB = np.bincount(gcode[base], minlength=ng)
    C, Dd = base.copy(), base.copy()
    inC, inD = inB.copy(), inB.copy()
    cntC, cntD = cntB.copy(), cntB.copy()
    swaps = 0
    for k in rng.permutation(N):
        if swaps >= N // 2:
            break
        s = base[k]
        same = ind == ind[s]
        # group already held by another stock of C (s itself is about to leave)
        present = (cntC[gcode] - (gcode == gcode[s]).astype(int)) > 0
        candC = np.where(same & ~inC & aff & present)[0]
        candD = np.where(same & ~inD & aff & (cntB[gcode] == 0) & (cntD[gcode] == 0))[0]
        if len(candC) == 0 or len(candD) == 0:
            continue
        pick = []
        for cand in (candC, candD):
            near = cand[np.argsort(np.abs(vol[cand] - vol[s]))[:3]]
            pick.append(rng.choice(near))
        c, d = pick
        C[k], Dd[k] = c, d
        inC[s] = False; inC[c] = True; cntC[gcode[s]] -= 1; cntC[gcode[c]] += 1
        inD[s] = False; inD[d] = True; cntD[gcode[s]] -= 1; cntD[gcode[d]] += 1
        swaps += 1
    if swaps == 0:
        return None
    eB, vB = enb_vol(cov[np.ix_(base, base)])
    eC, vC = enb_vol(cov[np.ix_(C, C)])
    eD, vD = enb_vol(cov[np.ix_(Dd, Dd)])
    gB, gC, gD = eff_n_groups(gcode[base]), eff_n_groups(gcode[C]), eff_n_groups(gcode[Dd])
    ok = (gC <= CONC_MAX * gB and abs(eC / eB - 1) <= MATCH_TOL and abs(eD / eB - 1) <= MATCH_TOL
          and abs(vC / vB - 1) <= MATCH_TOL and abs(vD / vB - 1) <= MATCH_TOL)
    if not ok:
        return None
    return {"B": base, "C": C, "D": Dd, "swaps": swaps, "enb": (eB, eC, eD), "vol": (vB, vC, vD),
            "geffn": (gB, gC, gD), "aff_w": (aff[base].mean(), aff[C].mean(), aff[Dd].mean())}


def build_pairs(D: dict, gcode: np.ndarray, N: int, K: int, rng, max_tries: int) -> tuple[list, int]:
    aff = multi_mask(gcode, D["is_main"])
    out, tries = [], 0
    while len(out) < K and tries < max_tries:
        tries += 1
        p = build_pair(D, gcode, aff, N, rng)
        if p is not None:
            out.append(p)
    return out, tries


# ----------------------------------------------------------------------------
# outcomes
# ----------------------------------------------------------------------------
def drawdown_and_ret(D: dict, members: np.ndarray) -> tuple[float, float]:
    V = D["Gm"][:, members].mean(1)
    w = V[D["w0"]:]
    peak = np.maximum.accumulate(w)
    return float((w / peak - 1).min()), float(w[-1] / w[0] - 1)


def score_pairs(D: dict, pairs: list, mret: float) -> pd.DataFrame:
    rows = []
    for p in pairs:
        r = {"swaps": p["swaps"], "enb_B": p["enb"][0], "enb_C": p["enb"][1], "enb_D": p["enb"][2],
             "gN_B": p["geffn"][0], "gN_C": p["geffn"][1], "gN_D": p["geffn"][2],
             "aff_B": p["aff_w"][0], "aff_C": p["aff_w"][1], "aff_D": p["aff_w"][2]}
        for lab in "BCD":
            dd, ret = drawdown_and_ret(D, p[lab])
            r[f"dd_{lab}"], r[f"xret_{lab}"] = dd, ret - mret
        rows.append(r)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# one full twin experiment (real labels or a placebo shuffle)
# ----------------------------------------------------------------------------
def experiment(variant: str, shuffle_seed: int | None, K: int, with_outcomes: bool) -> dict:
    st = _STATE[variant]
    rng = np.random.default_rng(SEED if shuffle_seed is None else SEED + 1000 + shuffle_seed)
    res = []
    for w, D in zip(st["windows"], st["dates"]):
        gcode = D["gcode"]
        if shuffle_seed is not None:
            gcode, is_main = _shuffle_together(D, rng)
            D = dict(D, is_main=is_main)
        for N in CFG["ns"]:
            pairs, tries = build_pairs(D, gcode, N, K, rng, max_tries=40 * K)
            row = {"window": w["window"], "N": N, "n_pairs": len(pairs), "tries": tries}
            if with_outcomes and pairs:
                sc = score_pairs(D, pairs, w["market_window_ret"])
                row.update({"T1": float((sc.dd_C - sc.dd_D).mean()), "T1b": float((sc.dd_C - sc.dd_B).mean()),
                            "T1_ret": float((sc.xret_C - sc.xret_D).mean()), "n": len(sc)})
                if shuffle_seed is None:
                    sc.insert(0, "window", w["window"]); sc.insert(1, "N", N)
                    row["_scores"] = sc
            res.append(row)
    return {"cells": res}


def _shuffle_together(D: dict, rng):
    """Placebo: reassign (group label, is-business-group) pairs across stocks; sizes kept."""
    perm = rng.permutation(D["n"])
    return D["gcode"][perm], D["is_main"][perm]


def pooled(cells: list, key: str) -> float:
    num = sum(c[key] * c["n"] for c in cells if c.get("n"))
    den = sum(c["n"] for c in cells if c.get("n"))
    return num / den if den else float("nan")


def _placebo_worker(args):
    variant, b, K = args
    r = experiment(variant, b, K, True)
    cells = [c for c in r["cells"] if c.get("n")]
    return {"b": b, "T1": pooled(cells, "T1"), "T1b": pooled(cells, "T1b"),
            "by_window": {f"{c['window']}|{c['N']}": c["T1"] for c in cells}}


def prepare(variants: list[str]) -> None:
    gp.log("Loading panel (verified map v2)")
    P = gp.Panel()
    G = gp.GroupMap(P.syms)
    wins = window_positions(P)
    for v in variants:
        ws = [w for w in wins if not (v == "x" and w["window"] == "Hindenburg")]
        excl = PILOT_DRIVERS if v == "x" else frozenset()
        _STATE[v] = {"windows": ws, "dates": [setup_date(P, G, w, excl, hc_only=(v == "hc")) for w in ws]}
    _STATE["_P"], _STATE["_G"], _STATE["_wins"] = P, G, wins


# ----------------------------------------------------------------------------
# T2: plain random portfolios
# ----------------------------------------------------------------------------
def t2_portfolios(rng) -> pd.DataFrame:
    rows = []
    for w, D in zip(_STATE["main"]["windows"], _STATE["main"]["dates"]):
        n = D["n"]
        for N in (20, 50, 100):
            for j in range(CFG["t2_per_n"]):
                mem = rng.choice(n, N, replace=False)
                wts = np.full(N, 1.0 / N) if j % 2 == 0 else rng.dirichlet(np.ones(N))
                rows.append((w["window"], N, j % 2, mem, wts))
    return rows


def t2_measures(D: dict, mem, wts, gcode) -> tuple:
    def effn(codes):
        s = pd.Series(wts).groupby(codes).sum().values
        s = s[s > 0]
        return float(np.exp(-(s * np.log(s)).sum()))
    cov = D["cov"][np.ix_(mem, mem)]
    lam, E = np.linalg.eigh(cov)
    lam = np.clip(lam, 0, None)
    v = (E.T @ wts) ** 2 * lam
    p = v[v > 0] / v.sum()
    enb = float(np.exp(-(p * np.log(p)).sum()))
    vol = float(np.sqrt(v.sum() * 252))
    hs = float(np.exp(-(wts[wts > 0] * np.log(wts[wts > 0])).sum()))
    return hs, effn(D["ind"][mem]), effn(gcode[mem]), enb, vol


def time_construction() -> dict:
    prepare(["main"])
    st = _STATE["main"]
    out = []
    for w, D in zip(st["windows"], st["dates"]):
        for N in CFG["ns"]:
            rng = np.random.default_rng(1)
            t0 = time.time()
            pairs, tries = build_pairs(D, D["gcode"], N, 50, rng, max_tries=40 * 50)
            dt = time.time() - t0
            out.append({"window": w["window"], "formation": w["formation"], "start": w["start"], "end": w["end"],
                        "universe": D["n"], "N": N, "pairs_built": len(pairs), "tries": tries,
                        "accept_rate": len(pairs) / max(tries, 1), "sec_per_pair": dt / max(len(pairs), 1),
                        "mean_swaps": float(np.mean([p["swaps"] for p in pairs])) if pairs else None,
                        "gN_B": float(np.mean([p["geffn"][0] for p in pairs])) if pairs else None,
                        "gN_C": float(np.mean([p["geffn"][1] for p in pairs])) if pairs else None,
                        "gN_D": float(np.mean([p["geffn"][2] for p in pairs])) if pairs else None,
                        "aff_C": float(np.mean([p["aff_w"][1] for p in pairs])) if pairs else None,
                        "aff_D": float(np.mean([p["aff_w"][2] for p in pairs])) if pairs else None})
            gp.log(f"  {out[-1]}")
    return {"cells": out}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["time", "run"])
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.step == "time":
        r = time_construction()
        pd.DataFrame(r["cells"]).to_csv(OUT / "construction_timing.csv", index=False)
        return
    run_all()


def t1_summary(cells: list) -> dict:
    cells = [c for c in cells if c.get("n")]
    byw = {}
    for c in cells:
        byw.setdefault(c["window"], []).append(c)
    win = {w: pooled(cs, "T1") for w, cs in byw.items()}
    return {"T1": pooled(cells, "T1"), "T1b": pooled(cells, "T1b"), "T1_ret": pooled(cells, "T1_ret"),
            "T1_by_window": win, "windows_negative": int(sum(v < 0 for v in win.values())),
            "n_windows": len(win), "n_pairs": int(sum(c["n"] for c in cells)),
            "cells": [{k: v for k, v in c.items() if k != "_scores"} for c in cells]}


def placebo_p(variant: str, n_placebo: int, real: dict, workers: int) -> dict:
    args = [(variant, b, CFG["pairs"]) for b in range(n_placebo)]
    with mp.get_context("fork").Pool(workers) as pool:
        draws = pool.map(_placebo_worker, args)
    t1 = np.array([d["T1"] for d in draws])
    t1b = np.array([d["T1b"] for d in draws])
    pd.DataFrame([{"b": d["b"], "T1": d["T1"], "T1b": d["T1b"]} for d in draws]).to_csv(
        OUT / f"placebo_{variant}.csv", index=False)
    return {"n_placebo": n_placebo, "p_T1": float(np.mean(t1 <= real["T1"])),
            "p_T1b": float(np.mean(t1b <= real["T1b"])), "placebo_T1_mean": float(np.nanmean(t1)),
            "placebo_T1_sd": float(np.nanstd(t1)), "placebo_T1_q05": float(np.nanquantile(t1, 0.05))}


def ols_fe(y: np.ndarray, X: np.ndarray, fe: np.ndarray) -> np.ndarray:
    def dm(a):
        return a - pd.DataFrame(a).groupby(fe).transform("mean").values
    yd, Xd = dm(y.reshape(-1, 1)).ravel(), dm(X)
    return np.linalg.lstsq(Xd, yd, rcond=None)[0]


def run_t2(rng, workers: int) -> dict:
    st = _STATE["main"]
    port = t2_portfolios(rng)
    rows = []
    for wname, N, kind, mem, wts in port:
        D = st["dates"][[w["window"] for w in st["windows"]].index(wname)]
        hs, hi, hg, enb, vol = t2_measures(D, mem, wts, D["gcode"])
        V = (D["Gm"][:, mem] * wts).sum(1)
        w_ = V[D["w0"]:]
        dd = float((w_ / np.maximum.accumulate(w_) - 1).min())
        rows.append((wname, N, kind, hs, hi, hg, enb, vol, dd))
    df = pd.DataFrame(rows, columns=["window", "N", "dirichlet", "effn_stock", "effn_ind", "effn_group",
                                     "enb", "vol", "dd"])
    df.to_parquet(OUT / "t2_portfolios.parquet", index=False)
    fe = df["window"].values
    Xcols = ["effn_stock", "effn_ind", "effn_group", "enb"]
    X = np.column_stack([np.log(df[c].values) for c in Xcols] + [df["vol"].values])
    b = ols_fe(df["dd"].values, X, fe)
    # leave-one-window-out R2 gain from adding log group effective N (within-window demeaned)
    def dm(a):
        return a - pd.DataFrame(a).groupby(fe).transform("mean").values
    yd, Xd = dm(df["dd"].values.reshape(-1, 1)).ravel(), dm(X)
    gains, sse_w, sse_wo, sst = [], 0.0, 0.0, 0.0
    for w in np.unique(fe):
        tr, te = fe != w, fe == w
        bw = np.linalg.lstsq(Xd[tr], yd[tr], rcond=None)[0]
        wo = [0, 1, 3, 4]
        bwo = np.linalg.lstsq(Xd[tr][:, wo], yd[tr], rcond=None)[0]
        sse_w += float(((yd[te] - Xd[te] @ bw) ** 2).sum())
        sse_wo += float(((yd[te] - Xd[te][:, wo] @ bwo) ** 2).sum())
        sst += float((yd[te] ** 2).sum())
    r2_with, r2_without = 1 - sse_w / sst, 1 - sse_wo / sst
    # placebo for the group coefficient: shuffle group labels across stocks (sizes kept)
    mems = [p[3] for p in port]
    wts = [p[4] for p in port]
    widx = [[w["window"] for w in st["windows"]].index(p[0]) for p in port]
    coefs = []
    prng = np.random.default_rng(SEED + 7)
    for _ in range(CFG["t2_placebos"]):
        perms = [prng.permutation(D["gcode"]) for D in st["dates"]]
        lg = np.empty(len(port))
        for i, (m_, w_, k) in enumerate(zip(mems, wts, widx)):
            s = np.bincount(perms[k][m_], weights=w_)
            s = s[s > 0]
            lg[i] = -(s * np.log(s)).sum()
        Xp = X.copy(); Xp[:, 2] = lg
        coefs.append(ols_fe(df["dd"].values, Xp, fe)[2])
    coefs = np.array(coefs)
    return {"n_portfolios": int(len(df)), "coef": dict(zip(Xcols + ["vol"], map(float, b))),
            "group_coef_placebo_p": float(np.mean(coefs >= b[2])), "placebo_coef_mean": float(coefs.mean()),
            "placebo_coef_sd": float(coefs.std()), "oos_r2_with_group": r2_with,
            "oos_r2_without_group": r2_without, "oos_r2_gain": r2_with - r2_without,
            "mean_measures": df[["effn_stock", "effn_ind", "effn_group", "enb", "vol", "dd"]].mean().to_dict()}


def run_all() -> None:
    workers = max(1, (os.cpu_count() or 2) - 1)
    t0 = time.time()
    prepare(["main", "x", "hc"])
    res = {"config": {**CFG, "ns": list(CFG["ns"]), "match_tol": MATCH_TOL, "conc_max": CONC_MAX,
                      "form_lag": FORM_LAG, "seed": SEED, "workers": workers},
           "windows": [{k: v for k, v in w.items() if k not in ("ps", "pe", "pf")} for w in _STATE["_wins"]]}
    scores = []
    for v, n_pl in [("main", CFG["placebos"]), ("x", CFG["placebos"]), ("hc", CFG["placebos"] // 2)]:
        gp.log(f"variant {v}: real labels ...")
        r = experiment(v, None, CFG["pairs"], True)
        for c in r["cells"]:
            if "_scores" in c:
                sc = c["_scores"]; sc.insert(0, "variant", v); scores.append(sc)
        summ = t1_summary(r["cells"])
        gp.log(f"  T1 {summ['T1']:.4f} ({summ['windows_negative']}/{summ['n_windows']} windows negative); placebos ...")
        summ["placebo"] = placebo_p(v, n_pl, summ, workers)
        gp.log(f"  placebo p {summ['placebo']['p_T1']:.3f}  ({time.time() - t0:.0f}s)")
        res[f"T1_{v}"] = summ
    pd.concat(scores).to_parquet(OUT / "twin_pairs.parquet", index=False)
    gp.log("T2 ...")
    res["T2"] = run_t2(np.random.default_rng(SEED + 3), workers)
    m, x = res["T1_main"], res["T1_x"]
    supported = m["placebo"]["p_T1"] < 0.05 and m["windows_negative"] >= 4
    x_holds = x["placebo"]["p_T1"] < 0.05 and x["windows_negative"] >= 3
    if supported and x_holds:
        v1 = "SUPPORTED: concentration in few groups predicts deeper crisis losses, also without the pilot's episodes"
    elif supported:
        v1 = "NARROWED: supported only with the pilot's stressed groups (group concentration matters when a group is under stress)"
    else:
        v1 = "NOT SUPPORTED"
    t2 = res["T2"]
    v2 = ("SUPPORTED" if t2["coef"]["effn_group"] > 0 and t2["group_coef_placebo_p"] < 0.05
          and t2["oos_r2_gain"] > 0 else "NOT SUPPORTED")
    res["verdict"] = {"H_P1": v1, "H_P2": v2, "rule": "PREREGISTRATION_2 §5"}
    res["runtime_sec"] = time.time() - t0
    with open(OUT / "results.json", "w") as f:
        json.dump(res, f, indent=2, default=lambda o: gp.safe(o) if isinstance(o, (np.integer, np.floating)) else str(o))
    gp.log(f"VERDICT {res['verdict']}  ({res['runtime_sec']:.0f}s)")


if __name__ == "__main__":
    main()
