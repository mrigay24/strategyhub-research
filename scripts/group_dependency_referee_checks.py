"""
Paper 2: diagnostics requested by the referee (docs/group_dependency/REFEREE_REPORT_2.md).
NOT PRE-REGISTERED. Descriptive; none changes the registered GO verdict.

Inputs (read only): results/group_dependency/v2/pairs.parquet (and v1 pairs.parquet),
v2/diagnostics_not_preregistered.json, group_map_v2.csv, data_processed/amfi_avg_mcap.parquet,
results/group_concentration/fund_level_latest_v2map.csv and v2/headline_by_period.csv.
Output: results/paper2_referee/referee_checks.json

  M1  CAR 1-20 (car_0_20 - ar_d0): the response after the crash day; co-crashing siblings
  M2  wild cluster bootstrap-t by trigger group (restricted, Rademacher, 1,999 draws)
  M3  R2 (no companion-paper episodes) and one event per group-year, with the bootstrap
  M4  which S pairs move in / out of "high confidence" between map v1 and v2
  M6  market benchmarks, latest half-year, top 500: industry effective N, Family-only G1,
      random-partition null (group labels shuffled across stocks, sizes kept)
  M7  funds: Spearman(ratio, matched weight); large-cap ratios vs the top-100 ratio

Run:  ~/.venvs/strategyhub/bin/python scripts/group_dependency_referee_checks.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from group_dependency_pilot import add_dummies, clusters_of, ols_fe  # noqa: E402

GD = ROOT / "results" / "group_dependency"
OUT = ROOT / "results" / "paper2_referee"
OUT.mkdir(exist_ok=True)
SEED, NBOOT = 20261112, 1999
XS = ["S", "SI", "R", "rho", "log_size", "log_amihud"]


def load(path: Path) -> pd.DataFrame:
    d = pd.read_parquet(path)
    sib = d[d["cls"].isin(["S", "SI"])]["event_id"].unique()
    d = add_dummies(d[d["event_id"].isin(sib)].reset_index(drop=True))
    d["car_1_20"] = d["car_0_20"] - d["ar_d0"]
    return d


def wild_boot(d: pd.DataFrame, y: str, rng) -> dict:
    """Restricted wild cluster bootstrap-t for beta_S, clusters = trigger group, event FE."""
    d = d.dropna(subset=[y] + XS).reset_index(drop=True)
    Z = d[[y] + XS].astype(float)
    Zd = (Z - Z.groupby(d["event_id"]).transform("mean")).values
    Y, X = Zd[:, 0], Zd[:, 1:]
    n, k = X.shape
    g_codes, g_uniq = pd.factorize(d["trigger_group"])
    G = len(g_uniq)
    Gm = np.zeros((G, n))
    Gm[g_codes, np.arange(n)] = 1.0
    xtx_inv = np.linalg.pinv(X.T @ X)
    c = (G / (G - 1)) * ((n - 1) / (n - k))

    def t_s(yv):
        b = xtx_inv @ (X.T @ yv)
        u = yv - X @ b
        sc = Gm @ (X * u[:, None])
        V = xtx_inv @ (sc.T @ sc) @ xtx_inv * c
        return b[0], b[0] / np.sqrt(V[0, 0])

    b_obs, t_obs = t_s(Y)
    Xr = X[:, 1:]
    br = np.linalg.lstsq(Xr, Y, rcond=None)[0]
    fit_r, u_r = Xr @ br, Y - Xr @ br
    ts = np.empty(NBOOT)
    for i in range(NBOOT):
        w = rng.choice([-1.0, 1.0], G)
        ts[i] = t_s(fit_r + w[g_codes] * u_r)[1]
    return {"beta_S": float(b_obs), "t_group_cluster": float(t_obs), "n_groups": int(G),
            "n_events": int(d["event_id"].nunique()),
            "boot_p_two_sided": float(np.mean(np.abs(ts) >= abs(t_obs)))}


def reg(d: pd.DataFrame, y: str) -> dict:
    r = ols_fe(d, y, XS, clusters_of(d))
    return {"beta_S": r["coef"]["S"], "t_month": r["t"]["month"]["S"], "t_group": r["t"]["group"]["S"],
            "beta_R": r["coef"]["R"], "t_S_minus_R_month": r["t_S_minus_R"]["month"],
            "t_S_minus_R_group": r["t_S_minus_R"]["group"], "n_events": r["n_events"]}


def main() -> None:
    rng = np.random.default_rng(SEED)
    d = load(GD / "v2" / "pairs.parquet")
    dg = json.load(open(GD / "v2" / "diagnostics_not_preregistered.json"))
    res = {"note": "NOT pre-registered; referee-requested diagnostics on the v2 run"}
    check = reg(d, "bhar_0_20")
    res["replication_primary"] = check  # must equal tests.json: -4.70 pp, t -2.66

    # M1 + M2: outcomes x inference
    samples = {"all": d, "no_companion_episodes": d[~d["event_id"].isin(dg["D2_events_dropped"])]}
    first = (d.assign(year=pd.to_datetime(d["date"]).dt.year).sort_values("date")
             .groupby(["trigger_group", "year"])["event_id"].first())
    samples["one_event_per_group_year"] = d[d["event_id"].isin(first.values)]
    out = {}
    for sname, sd in samples.items():
        out[sname] = {}
        for y in ["bhar_0_20", "ar_d0", "car_1_20"]:
            out[sname][y] = {**reg(sd, y), "wild_bootstrap": wild_boot(sd, y, rng)}
    res["M1_M2_M3_outcomes_by_sample"] = out
    sib = d[d["cls"].isin(["S", "SI"])]
    cc = sib[sib["ar_d0"] <= -0.12]
    res["M1_co_crashing_siblings"] = {"pairs_S_or_SI_with_day0_AR_le_-12pct": int(len(cc)),
                                      "events": int(cc["event_id"].nunique()),
                                      "examples": cc.sort_values("ar_d0")[["date", "trigger", "stock", "ar_d0"]]
                                      .head(6).astype(str).values.tolist()}

    # M4: high-confidence S pairs, v1 vs v2
    d1 = load(GD / "pairs.parquet")
    key = ["date", "trigger", "stock"]
    s1 = d1[d1["cls"] == "S"].assign(hc1=lambda x: (x.conf_trigger == "high") & (x.conf_stock == "high"))
    s2 = d[d["cls"] == "S"].assign(hc2=lambda x: (x.conf_trigger == "high") & (x.conf_stock == "high"))
    m = s1[key + ["hc1", "bhar_0_20", "trigger_group"]].merge(s2[key + ["hc2"]], on=key, how="outer")
    m_in = m[(m.hc2 == True) & (m.hc1 != True)]  # noqa: E712
    m_out = m[(m.hc1 == True) & (m.hc2 != True)]  # noqa: E712
    hc2 = s2[s2.hc2].assign(year=lambda x: pd.to_datetime(x["date"]).dt.year)
    res["M4_high_conf_shift"] = {
        "S_pairs_moved_in": int(len(m_in)), "moved_in_mean_bhar": float(m_in["bhar_0_20"].mean()),
        "S_pairs_moved_out": int(len(m_out)), "moved_out_mean_bhar": float(m_out["bhar_0_20"].mean()),
        "moved_out_tata_pairs": int((m_out["trigger_group"] == "Tata").sum()),
        "v2_hc_S_pairs": int(len(hc2)),
        "v2_hc_S_mean_bhar_2019_on": float(hc2.loc[hc2.year >= 2019, "bhar_0_20"].mean()),
        "v2_hc_S_mean_bhar_before_2019": float(hc2.loc[hc2.year < 2019, "bhar_0_20"].mean()),
        "v2_hc_S_share_2019_on": float((hc2.year >= 2019).mean())}

    # M6: market benchmarks, latest half-year, top 500
    gm = pd.read_csv(GD / "group_map_v2.csv", dtype=str).fillna("")
    gm["start"] = pd.to_datetime(gm["start"], errors="coerce").fillna(pd.Timestamp("1900-01-01"))
    gm["end"] = pd.to_datetime(gm["end"], errors="coerce")
    gm.loc[gm["end"] == gm["end"].max(), "end"] = pd.Timestamp("2100-01-01")
    gm["end"] = gm["end"].fillna(pd.Timestamp("2100-01-01"))
    w = pd.read_parquet(ROOT / "data_processed" / "amfi_avg_mcap.parquet").rename(columns={"avg_mcap_cr": "w"})
    w = w.dropna(subset=["w"])
    w = w[w.w > 0]
    p = w.period_end.max()
    u = w[w.period_end == p].sort_values("w", ascending=False).drop_duplicates("isin")
    mp = gm[(gm.start <= p) & (gm.end >= p)].drop_duplicates("symbol", keep="last")
    u = u.merge(mp[["symbol", "group", "group_type", "industry"]], left_on="nse_symbol", right_on="symbol", how="left")
    u = u.fillna({"group": "", "group_type": "", "industry": ""}).nlargest(500, "w").reset_index(drop=True)
    solo = "solo:" + u["isin"].astype(str)
    u["g1"] = np.where(u.group_type.isin(["Family", "Corporate"]), u["group"], solo)
    u["fam"] = np.where(u.group_type == "Family", u["group"], solo)
    u["ind"] = np.where(u["industry"] != "", u["industry"], "unmatched:" + u["isin"].astype(str))

    def effn(x):
        x = np.asarray(x, float) / np.sum(x)
        x = x[x > 0]
        return float(np.exp(-(x * np.log(x)).sum()))

    obs = effn(u.groupby("g1").w.sum())
    lab = u["g1"].values
    null = np.array([effn(u.w.groupby(rng.permutation(lab)).sum()) for _ in range(1000)])
    res["M6_market_benchmarks"] = {
        "period": str(pd.Timestamp(p).date()), "effN_stocks": effn(u.w), "effN_groups_G1": obs,
        "effN_groups_family_only": effn(u.groupby("fam").w.sum()),
        "effN_industries_mapped_plus_unmatched_solo": effn(u.groupby("ind").w.sum()),
        "random_partition_null_mean": float(null.mean()), "random_partition_null_p05": float(np.quantile(null, 0.05)),
        "random_partition_null_p95": float(np.quantile(null, 0.95)),
        "share_obs_le_null": float(np.mean(null <= obs))}

    # M7: funds
    fd = pd.read_csv(ROOT / "results" / "group_concentration" / "fund_level_latest_v2map.csv")
    h = pd.read_csv(ROOT / "results" / "group_concentration" / "v2" / "headline_by_period.csv")
    rho, pv = stats.spearmanr(fd["ratio"], fd["matched_weight"])
    lc = fd[fd["category"] == "Large cap"]["ratio"]
    res["M7_funds"] = {"spearman_ratio_matched_weight": float(rho), "spearman_p": float(pv),
                       "large_cap_ratio_min": float(lc.min()), "large_cap_ratio_max": float(lc.max()),
                       "top100_ratio_latest": float(h[h.universe == "top100"]["ratio_stocks_to_groups_G1"].iloc[-1]),
                       "small_cap_matched_weight_min": float(fd[fd.category == "Small cap"]["matched_weight"].min()),
                       "small_cap_matched_weight_max": float(fd[fd.category == "Small cap"]["matched_weight"].max())}
    with open(OUT / "referee_checks.json", "w") as f:
        json.dump(res, f, indent=2, default=float)
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
