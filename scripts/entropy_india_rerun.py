"""
Re-run entropy Test 2 (market entropy and fragility) for INDIA on the corrected NSE panels
===========================================================================================
Why: results/entropy_research/test2_entropy_series_India.csv shows the co-movement entropy
falling from 0.73 (mid-2011) to ~0.64 in 2012 and snapping back to 0.76 by 2013. That window is
exactly the 252-day lookback that contains 2012-01-02, the one "daily" return that is really a
195-day return for every stock (the 2011-H2 data hole, see results/nse_data_audit/README.md).
One huge common observation inflates the first eigenvalue and mechanically lowers eigen-entropy.

Variants (panels from scripts/build_nse_adjusted_panels.py), each run through the UNCHANGED
entropy_research.entropy_series / test2_analyse code:
    raw          panel as used originally            (must reproduce the old India series)
    nohole       raw + the 195-day return zeroed      (isolates the hole artefact)
    adj_nohole   corporate actions back-adjusted + hole zeroed   (best-corrected)
and, for each, a "trimmed" copy that drops every month whose 252-day window overlaps the
2011-H2 hole (month-ends 2011-06 .. 2012-12), because the 2012 universe is also half size.

Output -> results/entropy_research_ca/<variant>[_trimmed]/ and results/entropy_research_ca/comparison.csv
Run:  .venv/bin/python scripts/entropy_india_rerun.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import entropy_research as er  # noqa: E402

DATA = ROOT / "data_processed"
BASE = ROOT / "results" / "entropy_research_ca"
VARIANTS = {"raw": "nse_survivorship_free.parquet",
            "nohole": "nse_survivorship_free_nohole.parquet",
            "adj_nohole": "nse_survivorship_free_adj_nohole.parquet"}
HOLE_FIRST, HOLE_LAST = pd.Timestamp("2011-06-01"), pd.Timestamp("2012-12-31")  # month-ends whose window touches the hole


def summarise(df: pd.DataFrame, res: dict, tag: str) -> dict:
    r = res["regressions"]
    q = {d["eig_q"]: d for d in res["quintiles"]}
    row = {"variant": tag, "months": res["months"], "mean_n": round(float(df["n"].mean()), 1),
           "eig_entropy_mean": round(float(df["eig_entropy_norm"].mean()), 4),
           "eig_entropy_min": round(float(df["eig_entropy_norm"].min()), 4)}
    for y in ("fwd_vol_63", "fwd_mdd_126", "fwd_ret_63"):
        row[f"{y}_coef"] = round(r[y]["coef_entropy_z"], 4)
        row[f"{y}_t"] = round(r[y]["t_entropy"], 2)
    row["Q1_low_fwd_mdd"] = round(q["Q1 low"]["fwd_mdd_126"], 3)
    row["Q5_high_fwd_mdd"] = round(q["Q5 high"]["fwd_mdd_126"], 3)
    row["Q1_low_fwd_vol"] = round(q["Q1 low"]["fwd_vol_63"], 3)
    row["Q5_high_fwd_vol"] = round(q["Q5 high"]["fwd_vol_63"], 3)
    return row


def main():
    rows, series = [], {}
    for tag, fname in VARIANTS.items():
        rin, dvin = er.load_panel(DATA / fname, max_abs_ret=0.5)
        for trimmed in (False, True):
            name = tag + ("_trimmed" if trimmed else "")
            er.OUT = BASE / name
            er.OUT.mkdir(parents=True, exist_ok=True)
            df = er.entropy_series(rin, rin.notna(), dvin, "India", top_n=300)
            if trimmed:
                df = df[(df.index < HOLE_FIRST) | (df.index > HOLE_LAST)]
            res = er.test2_analyse(df, "India")
            rows.append(summarise(df, res, name))
            if not trimmed:
                series[tag] = df["eig_entropy_norm"].rename(tag)
            (er.OUT / "summary_india.json").write_text(json.dumps(res, indent=2, default=str))
    out = pd.DataFrame(rows)
    BASE.mkdir(parents=True, exist_ok=True)
    out.to_csv(BASE / "comparison.csv", index=False)
    s = pd.concat(series.values(), axis=1)
    s.to_csv(BASE / "eig_entropy_series_by_variant.csv")
    pd.set_option("display.width", 220)
    print(out.T.to_string())
    print("\neig_entropy_norm around the hole:")
    print(s.loc["2011-03-01":"2013-06-30"].round(3).to_string())


if __name__ == "__main__":
    main()
