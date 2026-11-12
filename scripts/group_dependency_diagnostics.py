"""
NOT PRE-REGISTERED diagnostics for the group-dependency pilot (run after the registered
test, 11 Nov 2026). They do not change the verdict. They answer: what drives beta_S?

  D1  leave-one-group-out beta_S (BHAR 0-20, primary specification)
  D2  day-0 AR regression without the paper-1 episodes (R2 run on the day-0 outcome)
  D3  the events whose S siblings contribute most (event-level residuals, as in R8)
  D4  the share of S pairs and of the S "loss" coming from each trigger group

Run:  ~/.venvs/strategyhub/bin/python scripts/group_dependency_diagnostics.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import group_dependency_pilot as gp  # noqa: E402

OUT = gp.OUT
XS = ["S", "SI", "R", "rho", "log_size", "log_amihud"]


def main() -> None:
    d = pd.read_parquet(OUT / "pairs.parquet")
    keep = d[d["cls"].isin(["S", "SI"])]["event_id"].unique()
    d = gp.add_dummies(d[d["event_id"].isin(keep)].reset_index(drop=True))
    res = {"note": "NOT pre-registered; descriptive diagnostics after the registered run"}

    # D1 leave one trigger group out
    loo = []
    for g in sorted(d.loc[d["cls"] == "S", "trigger_group"].unique()):
        dd = d[d["trigger_group"] != g]
        r = gp.ols_fe(dd, "bhar_0_20", XS, gp.clusters_of(dd))
        loo.append({"dropped_group": g, "n_events_dropped": int(d.loc[d["trigger_group"] == g, "event_id"].nunique()),
                    "beta_S": r["coef"]["S"], "t_month": r["t"]["month"]["S"]})
    loo = pd.DataFrame(loo).sort_values("beta_S", ascending=False)
    loo.to_csv(OUT / "diag_leave_one_group_out.csv", index=False)
    res["D1_leave_one_group_out"] = {"max_beta_S": loo.iloc[0].to_dict(), "min_beta_S": loo.iloc[-1].to_dict(),
                                     "n_groups": int(len(loo)),
                                     "n_with_t_le_-1.96": int((loo["t_month"] <= -1.96).sum())}

    # D2 day-0 outcome without the paper-1 episodes
    dt = pd.to_datetime(d["date"])
    panel_dates = pd.to_datetime(pd.read_parquet(gp.PANEL, columns=["date"])["date"].unique())
    panel_dates = pd.DatetimeIndex(sorted(panel_dates))
    pos = dt.map(lambda x: panel_dates.searchsorted(x))
    p1 = pd.Series(False, index=d.index)
    for grp, day in gp.PAPER1_EPISODES:
        k0 = panel_dates.searchsorted(pd.Timestamp(day))
        p1 |= (d["trigger_group"] == grp) & ((pos - k0).abs() <= 60)
    dd = d[~p1]
    for y in ["ar_d0", "bhar_0_20", "car_0_20"]:
        r = gp.ols_fe(dd, y, XS, gp.clusters_of(dd))
        res[f"D2_no_paper1_{y}"] = {"beta_S": r["coef"]["S"], "t_month": r["t"]["month"]["S"],
                                    "beta_R": r["coef"]["R"], "t_R": r["t"]["month"]["R"],
                                    "S_minus_R": r["S_minus_R"], "t_S_minus_R": r["t_S_minus_R"]["month"],
                                    "n_events": r["n_events"]}
    res["D2_events_dropped"] = sorted(d.loc[p1, "event_id"].unique().tolist())

    # D3 event-level residuals of S stocks (controls fitted on B, as in R8)
    ctr = ["rho", "log_size", "log_amihud"]
    dz = d.dropna(subset=["bhar_0_20"] + ctr)
    Z = dz[["bhar_0_20"] + ctr].astype(float)
    mb = dz["cls"] == "B"
    means_b = Z[mb].groupby(dz.loc[mb, "event_id"]).mean()
    Zb = Z[mb] - means_b.loc[dz.loc[mb, "event_id"]].values
    gam = np.linalg.lstsq(Zb[ctr].values, Zb["bhar_0_20"].values, rcond=None)[0]
    s = dz[dz["cls"] == "S"].copy()
    mbe = means_b.loc[s["event_id"]].values
    s["resid"] = (s["bhar_0_20"].values - mbe[:, 0]) - (s[ctr].values - mbe[:, 1:]) @ gam
    ev = s.groupby("event_id").agg(date=("date", "first"), trigger=("trigger", "first"),
                                   group=("trigger_group", "first"), n_S=("stock", "size"),
                                   mean_resid=("resid", "mean"), siblings=("stock", " ".join))
    ev = ev.sort_values("mean_resid")
    ev.to_csv(OUT / "diag_event_residuals.csv")
    tot = ev["mean_resid"].sum()
    res["D3_events"] = {"n": int(len(ev)), "mean": float(ev["mean_resid"].mean()),
                        "median": float(ev["mean_resid"].median()),
                        "share_of_total_from_worst_5": float(ev["mean_resid"].head(5).sum() / tot),
                        "share_of_total_from_worst_10": float(ev["mean_resid"].head(10).sum() / tot),
                        "mean_without_worst_5": float(ev["mean_resid"].iloc[5:].mean()),
                        "worst_10": ev.head(10).reset_index()[["event_id", "date", "trigger", "group", "n_S", "mean_resid"]].to_dict("records"),
                        "best_5": ev.tail(5).reset_index()[["event_id", "date", "trigger", "group", "n_S", "mean_resid"]].to_dict("records")}
    # D4 by group
    byg = s.groupby("trigger_group").agg(n_events=("event_id", "nunique"), n_S_pairs=("stock", "size"),
                                         mean_resid=("resid", "mean")).sort_values("n_S_pairs", ascending=False)
    byg.to_csv(OUT / "diag_by_group.csv")
    res["D4_by_group_top10"] = byg.head(10).reset_index().to_dict("records")
    with open(OUT / "diagnostics_not_preregistered.json", "w") as f:
        json.dump(res, f, indent=2, default=lambda o: gp.safe(o) if isinstance(o, (np.integer, np.floating)) else str(o))
    print(json.dumps(res, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main()
