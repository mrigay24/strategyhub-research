"""
Diagnostics requested by the referee (REFEREE_REPORT.md), 2026-11-11.
NOT PRE-REGISTERED. Descriptive; none of them changes a pre-registered verdict.

Reads results/death_test_oos/outcomes.csv and tests.json, results/death_test/robustness.csv.
Writes results/death_test_oos/referee_checks.json.

  M4  episodes: cases in the same market whose day 0s are within 30 calendar days of the
      previous case are one episode; episode-stratified permutation of SD vs OR
  M5  within-crisis comparison (the episodes that contain an SD case)
  M6  power: minimum detectable SD-OR gap; OR sub-group intervals and binomial tests
  M7a drop the three cases that overlap the eight case studies (IN-ATGL, IN-DHFL19, IN-MAYTAS)
  M2  95% interval for the out-of-sample share coefficient
  M3  every out-of-sample R^2 in robustness.csv, both horizons

Run:  ~/.venvs/strategyhub/bin/python scripts/death_test_referee_checks.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
OOS = ROOT / "results" / "death_test_oos"
sys.path.insert(0, str(ROOT / "scripts"))
from death_test_oos import tests  # noqa: E402

SEED, NPERM, GAPDAYS = 20261111, 20000, 30
Z = stats.norm.ppf(0.95) + stats.norm.ppf(0.80)


def episodes(d: pd.DataFrame) -> pd.Series:
    ep, k = {}, 0
    for _, g in d.sort_values("day0_used").groupby("market"):
        last = None
        for cid, day in zip(g["case_id"], pd.to_datetime(g["day0_used"])):
            if last is None or (day - last).days > GAPDAYS:
                k += 1
            ep[cid], last = k, day
    return d["case_id"].map(ep)


def stratified_perm(d: pd.DataFrame, rng) -> dict:
    mixed = [g for _, g in d.groupby("episode") if g["sd"].any() and (~g["sd"]).any()]
    gaps = [g.loc[g.sd, "y"].mean() - g.loc[~g.sd, "y"].mean() for g in mixed]
    obs = float(np.mean(gaps))
    sims = np.empty(NPERM)
    for i in range(NPERM):
        gs = []
        for g in mixed:
            lab = rng.permutation(g["sd"].values)
            gs.append(g["y"].values[lab].mean() - g["y"].values[~lab].mean())
        sims[i] = np.mean(gs)
    return {"episodes_with_both_labels": len(mixed),
            "episode_cases": [list(g["case_id"]) for g in mixed],
            "within_episode_gaps": [float(x) for x in gaps], "mean_gap": obs,
            "perm_p_one_sided": float((sims <= obs).mean())}


def main() -> None:
    out = pd.read_csv(OOS / "outcomes.csv")
    t = json.load(open(OOS / "tests.json"))
    d = out[(out.status == "case") & (out.peer_set == "rivals")].copy()
    d["sd"], d["y"] = d["label"] == "SD", d["bhar_0_20"]
    d["episode"] = episodes(d)
    rng = np.random.default_rng(SEED)
    res = {"note": "NOT pre-registered; referee-requested diagnostics"}

    # M4: dependence between cases
    sizes = d.groupby("episode").size()
    res["M4_episodes"] = {
        "n_cases": len(d), "n_episodes": int(len(sizes)),
        "cases_in_multi_case_episodes": int(sizes[sizes > 1].sum()),
        "multi_case_episodes": int((sizes > 1).sum()),
        "n_SD_episodes": int(d.loc[d.sd, "episode"].nunique()),
        "stratified": stratified_perm(d, rng)}

    # M5: within-crisis (BAC episode, Citi episode)
    crisis = {}
    for cid in ["US-C", "US-BAC"]:
        e = d.loc[d.case_id == cid, "episode"].iloc[0]
        g = d[d.episode == e]
        crisis[cid] = {"SD_bhar": float(g.loc[g.case_id == cid, "y"].iloc[0]),
                       "OR_cases": list(g.loc[~g.sd, "case_id"]),
                       "OR_mean": float(g.loc[~g.sd, "y"].mean())}
    rank = d.sort_values("y").reset_index(drop=True)
    crisis["largest_losses_rank"] = [f"{r.case_id} {r.label} {r.y:.3f}" for r in rank.head(7).itertuples()]
    res["M5_within_crisis"] = crisis

    # M6: power and OR sub-groups
    sig = float(d["y"].std(ddof=1))
    mde = lambda n1, n2: float(Z * sig * np.sqrt(1 / n1 + 1 / n2))  # noqa: E731
    gap = t["full_population"]["T1_T2"]["diff"]
    n_need = int(np.ceil((Z * sig / abs(gap)) ** 2 * (1 + 1 / 9)))  # OR = 9 x SD, as in the sample
    orsub = {}
    for name, g in [("financial", d[(~d.sd) & (d.financial == "Y")]), ("non_financial", d[(~d.sd) & (d.financial != "Y")])]:
        se = g["y"].std(ddof=1) / np.sqrt(len(g))
        hits = int((g["y"] >= 0).sum())
        orsub[name] = {"n": len(g), "mean": float(g["y"].mean()),
                       "ci95": [float(g["y"].mean() - 1.96 * se), float(g["y"].mean() + 1.96 * se)],
                       "hits": hits, "binom_p_hit_gt_half": float(stats.binomtest(hits, len(g), 0.5, alternative="greater").pvalue),
                       "t_mean_vs_0": float(g["y"].mean() / se)}
    res["M6_power"] = {"sd_of_case_outcomes": sig, "mde_4_vs_36": mde(4, 36), "mde_5_vs_35": mde(5, 35),
                       "mde_2_vs_24": mde(2, 24), "observed_gap_full": gap,
                       "sd_cases_needed_for_observed_gap_at_9to1": n_need, "OR_subgroups": orsub}

    # M7a: drop cases overlapping the eight case studies
    keep = ~d["case_id"].isin(["IN-ATGL", "IN-DHFL19", "IN-MAYTAS"])
    res["M7a_drop_case_study_overlaps"] = tests(d[keep])

    # M2: share coefficient interval (from T5)
    ci = {}
    for v in ["registered", "full_population"]:
        b, tt = t[v]["T5_share"]["coef_share"], t[v]["T5_share"]["t_share"]
        se = abs(b / tt)
        ci[v] = {"coef": b, "se": se, "ci95": [b - 1.96 * se, b + 1.96 * se],
                 "effect_of_20pp_share_ci": [0.2 * (b - 1.96 * se), 0.2 * (b + 1.96 * se)]}
    res["M2_share_ci"] = ci

    # M3: every out-of-sample R^2 in Part A robustness
    rob = pd.read_csv(ROOT / "results" / "death_test" / "robustness.csv")
    res["M3_cv_r2"] = {r["variant"]: {"d0_share_hhi": r["d0_cvR2_share_hhi"], "d0_subind": r["d0_cvR2_subind"],
                                      "20d_share_hhi": r["0_20_cvR2_share_hhi"], "20d_subind": r["0_20_cvR2_subind"]}
                       for _, r in rob.iterrows()}

    with open(OOS / "referee_checks.json", "w") as f:
        json.dump(res, f, indent=2, default=float)
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
