"""
Phase 3 — robustness of the US death test (Part A), 2026-11-11.

Variants of the isolated-crash event study in scripts/death_test.py:
  baseline       peers = GICS sub-industry, crash = own return < -15% and < -12% vs peers
  thr10 / thr20  crash thresholds -10%/-8% and -20%/-16%
  ex_crises      drop events in 2008-09 and 2020
  ex_financials  drop events where the crashing firm is in Financials
  sector_peers   peers = the whole GICS sector instead of the sub-industry

For each variant (aggregates only):
  * mean peer reaction on day 0 and days 0-20, with ordinary t, t clustered by
    event date, and a date-cluster bootstrap 95% CI (5,000 draws)
  * by share tercile, and the large-minus-small gap with a bootstrap CI
  * does share explain the reaction? adjusted R^2 in sample AND 5-fold
    cross-validated R^2 (out of sample, 20 repeats) for share+HHI vs industry
    dummies, and the share coefficient *within* sub-industry (dummies included),
    t clustered by date

Output: results/death_test/robustness.csv, robustness.log
Run:    ~/.venvs/strategyhub/bin/python scripts/death_test_robustness.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from death_test import build_events, gics_maps, load  # noqa: E402
from entropy_research import DATA, log, us_pit_mask  # noqa: E402

OUT = ROOT / "results" / "death_test"
RNG = np.random.default_rng(20261111)
NBOOT = 5000


def ols_cluster(y: np.ndarray, X: np.ndarray, groups: np.ndarray):
    """OLS with CR1 cluster-robust standard errors. X excludes the constant."""
    X = np.column_stack([np.ones(len(y)), X])
    n, k = X.shape
    xtx_inv = np.linalg.pinv(X.T @ X)
    b = xtx_inv @ X.T @ y
    u = y - X @ b
    _, gi = np.unique(groups, return_inverse=True)
    G = gi.max() + 1
    S = np.zeros((G, k))
    np.add.at(S, gi, X * u[:, None])
    meat = S.T @ S
    c = G / max(G - 1, 1) * (n - 1) / max(n - k, 1)
    cov = c * xtx_inv @ meat @ xtx_inv
    return b, b / np.sqrt(np.diag(cov)), u


def mean_stats(x: pd.Series, dates: pd.Series) -> dict:
    ok = x.notna()
    x, d = x[ok].values, dates[ok].values
    n = len(x)
    m = x.mean()
    t_iid = m / (x.std(ddof=1) / np.sqrt(n))
    _, t_cl, _ = ols_cluster(x, np.empty((n, 0)), d)
    # date-cluster bootstrap
    ud, gi = np.unique(d, return_inverse=True)
    sums = np.bincount(gi, weights=x)
    cnts = np.bincount(gi)
    draws = RNG.integers(0, len(ud), size=(NBOOT, len(ud)))
    bm = sums[draws].sum(1) / cnts[draws].sum(1)
    return {"mean": m, "t_iid": t_iid, "t_cl": t_cl[0],
            "ci_lo": np.percentile(bm, 2.5), "ci_hi": np.percentile(bm, 97.5)}


def tercile_gap(ev: pd.DataFrame, col: str) -> dict:
    e = ev.dropna(subset=["firm_share", col]).copy()
    e["terc"] = pd.qcut(e["firm_share"], 3, labels=False)
    means = e.groupby("terc")[col].mean()
    d = e["date"].values
    ud, gi = np.unique(d, return_inverse=True)
    draws = RNG.integers(0, len(ud), size=(1000, len(ud)))
    gaps = []
    for dr in draws:
        idx = np.concatenate([np.where(gi == g)[0] for g in dr])
        s = e.iloc[idx]
        mm = s.groupby("terc")[col].mean()
        if 0 in mm.index and 2 in mm.index:
            gaps.append(mm[2] - mm[0])
    return {"small": means.get(0), "mid": means.get(1), "large": means.get(2),
            "gap": means.get(2) - means.get(0),
            "gap_lo": np.percentile(gaps, 2.5), "gap_hi": np.percentile(gaps, 97.5)}


def dummies(s: pd.Series, min_n: int = 5) -> pd.DataFrame:
    big = s.map(s.value_counts()) >= min_n
    return pd.get_dummies(s.where(big, "other"), drop_first=True).astype(float)


def adj_r2(y, X) -> float:
    X1 = np.column_stack([np.ones(len(y)), X])
    b = np.linalg.pinv(X1.T @ X1) @ X1.T @ y
    u = y - X1 @ b
    r2 = 1 - (u ** 2).sum() / ((y - y.mean()) ** 2).sum()
    n, k = X1.shape
    return 1 - (1 - r2) * (n - 1) / max(n - k, 1)


def cv_r2(y, X, folds: int = 5, reps: int = 20) -> float:
    out = []
    n = len(y)
    for _ in range(reps):
        perm = RNG.permutation(n)
        sse = sst = 0.0
        for f in range(folds):
            te = perm[f::folds]
            tr = np.setdiff1d(perm, te)
            X1 = np.column_stack([np.ones(len(tr)), X[tr]])
            b = np.linalg.pinv(X1.T @ X1) @ X1.T @ y[tr]
            pred = np.column_stack([np.ones(len(te)), X[te]]) @ b
            sse += ((y[te] - pred) ** 2).sum()
            sst += ((y[te] - y[tr].mean()) ** 2).sum()
        out.append(1 - sse / sst)
    return float(np.mean(out))


def share_tests(ev: pd.DataFrame, col: str, sub_of: dict, sector_of: dict) -> dict:
    e = ev.dropna(subset=["firm_share", "sub_hhi", "own_ab_d0", col]).reset_index(drop=True)
    y = e[col].values
    base = e[["firm_share", "sub_hhi", "own_ab_d0"]].values.astype(float)
    sub = e["symbol"].map(sub_of)
    sec = e["symbol"].map(sector_of)
    Dsub = dummies(sub).values
    Dsec = pd.get_dummies(sec, drop_first=True).astype(float).values
    own = e[["own_ab_d0"]].values.astype(float)
    b, t, _ = ols_cluster(y, np.column_stack([base, Dsub]), e["date"].values)
    return {"adjR2_share_hhi": adj_r2(y, base),
            "adjR2_sector": adj_r2(y, np.column_stack([own, Dsec])),
            "adjR2_subind": adj_r2(y, np.column_stack([own, Dsub])),
            "cvR2_share_hhi": cv_r2(y, base),
            "cvR2_subind": cv_r2(y, np.column_stack([own, Dsub])),
            "share_coef_within_subind": b[1], "share_t_within_subind_cl": t[1]}


def main() -> None:
    log("Loading US (raw, $1 floor)")
    rets, dv = load(DATA / "extended_prices.parquet", 1.0)
    mask = us_pit_mask(rets)
    sub_of, sector_of = gics_maps()

    base = build_events(rets, mask, dv, sub_of, sector_of)
    variants = {
        "baseline (sub-industry, -15%/-12%)": base,
        "crash threshold -10%/-8%": build_events(rets, mask, dv, sub_of, sector_of, -0.10, -0.08),
        "crash threshold -20%/-16%": build_events(rets, mask, dv, sub_of, sector_of, -0.20, -0.16),
        "excluding 2008-09 and 2020": base[~base["date"].dt.year.isin([2008, 2009, 2020])],
        "excluding Financials": base[base["sector"] != "Financials"],
        "sector-level peers": build_events(rets, mask, dv, sector_of, sector_of),
    }
    rows, lines = [], []
    for name, ev in variants.items():
        ev = ev.reset_index(drop=True)
        r = {"variant": name, "n_events": len(ev), "n_dates": ev["date"].nunique(),
             "pct_peers_down_d0": (ev["peer_car_d0"] < 0).mean()}
        for col, tag in [("peer_car_d0", "d0"), ("peer_car_0_20", "0_20")]:
            for k, v in mean_stats(ev[col], ev["date"]).items():
                r[f"{tag}_{k}"] = v
            for k, v in tercile_gap(ev, col).items():
                r[f"{tag}_share_{k}"] = v
            for k, v in share_tests(ev, col, sub_of, sector_of).items():
                r[f"{tag}_{k}"] = v
        rows.append(r)
        lines.append(f"\n== {name}: {len(ev)} events on {r['n_dates']} dates ==")
        for tag, lab in [("d0", "day 0"), ("0_20", "days 0-20")]:
            lines.append(
                f"  {lab:9s} mean {r[f'{tag}_mean']:+.2%}  t {r[f'{tag}_t_iid']:+.1f} "
                f"(clustered {r[f'{tag}_t_cl']:+.1f})  95% CI [{r[f'{tag}_ci_lo']:+.2%}, {r[f'{tag}_ci_hi']:+.2%}]")
            lines.append(
                f"            share terciles {r[f'{tag}_share_small']:+.2%} / {r[f'{tag}_share_mid']:+.2%} / "
                f"{r[f'{tag}_share_large']:+.2%}; large-small {r[f'{tag}_share_gap']:+.2%} "
                f"[{r[f'{tag}_share_gap_lo']:+.2%}, {r[f'{tag}_share_gap_hi']:+.2%}]")
            lines.append(
                f"            adj R2: share+HHI {r[f'{tag}_adjR2_share_hhi']:.3f}, sector {r[f'{tag}_adjR2_sector']:.3f}, "
                f"sub-ind {r[f'{tag}_adjR2_subind']:.3f} | CV R2: share+HHI {r[f'{tag}_cvR2_share_hhi']:.3f}, "
                f"sub-ind {r[f'{tag}_cvR2_subind']:.3f} | share within sub-ind: coef "
                f"{r[f'{tag}_share_coef_within_subind']:+.4f}, t_cl {r[f'{tag}_share_t_within_subind_cl']:+.1f}")
        log("\n".join(lines[-7:]))
    pd.DataFrame(rows).to_csv(OUT / "robustness.csv", index=False)
    (OUT / "robustness.log").write_text("\n".join(lines) + "\n")
    log("Done: results/death_test/robustness.csv")


if __name__ == "__main__":
    main()
