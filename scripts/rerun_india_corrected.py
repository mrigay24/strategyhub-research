"""
Re-run the India long-short + market-neutral analysis on corrected NSE panels
=============================================================================
For each universe (top500, top150) and each data variant it runs, UNCHANGED:
    scripts/run_nse_longshort.py          -> results/nse_longshort_ca/<panel>_<variant>/
    scripts/india_vs_us_market_neutral.py -> results/composites_ca/india_vs_us_<panel>_<variant>.json
and writes the before/after table to results/nse_data_audit/before_after.{csv,md}.
Old result folders are never touched.

Variants (panel files made by scripts/build_nse_adjusted_panels.py)
    raw           the panels exactly as published      (must reproduce the old headline)
    nohole        raw, but the 195-day 2011-H2 data hole day (2012-01-02) neutralised
    adj           splits/bonuses back-adjusted         <- the corporate-action fix
    adj_nohole    adj + hole day neutralised           <- best-corrected estimate
    zero40        BRACKET: every consecutive-day |move|>40% zeroed (kills real crashes too)
    zero40_nohole bracket + hole day neutralised       <- most conservative

Run:
    .venv/bin/python scripts/rerun_india_corrected.py            # all
    .venv/bin/python scripts/rerun_india_corrected.py --only adj_nohole
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.india_vs_us_market_neutral import benchmark_monthly  # noqa: E402
from src.backtesting.composite_engine import sharpe  # noqa: E402

DATA = ROOT / "data_processed"
PANELS = {"top500": "nse_survivorship_free", "top150": "nse_survivorship_free_top150"}
VARIANTS = ["raw", "nohole", "adj", "adj_nohole", "zero40", "zero40_nohole"]
LS_DIR = ROOT / "results" / "nse_longshort_ca"
CMP_DIR = ROOT / "results" / "composites_ca"
AUDIT_DIR = ROOT / "results" / "nse_data_audit"
OLD_HEADLINE = {  # stored pre-fix results, for the "published" column
    "top500": ROOT / "results" / "composites" / "india_vs_us_clean.json",
    "top150": ROOT / "results" / "composites" / "india_vs_us_clean150.json",
}


def parquet_for(panel: str, variant: str) -> Path:
    stem = PANELS[panel]
    return DATA / (f"{stem}.parquet" if variant == "raw" else f"{stem}_{variant}.parquet")


def run(cmd: list[str]):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")


def summarize(js: dict, bench: pd.Series) -> dict:
    ind = js["india"]
    c = ind["composite"]
    rows = {r["sleeve"]: r for r in ind["per_sleeve"]}
    sig = ind["significant_sleeves"]
    betas = [rows[s]["beta"] for s in sig if s in rows and rows[s]["beta"] is not None]
    lv = rows.get("low_volatility_shield", {})
    b = bench.dropna()
    return {
        "alpha_pct": round(100 * c["ann_alpha"], 2), "alpha_t": c["alpha_tstat"],
        "neutral_sharpe": c["neutral_sharpe"], "bootstrap_p": c["bootstrap_p"],
        "ann_vol_pct": round(100 * c["ann_vol"], 1), "mdd_pct": round(100 * c["mdd"], 1),
        "n_sig_sleeves": len(sig), "sig_sleeves": "|".join(sig),
        "hedge_beta_mean_sig": round(float(np.mean(betas)), 3) if betas else None,
        "lowvol_beta": lv.get("beta"), "lowvol_alpha_pct": round(100 * lv["ann_alpha"], 2) if lv else None,
        "lowvol_alpha_t": lv.get("alpha_tstat"),
        "bench_cagr_pct": round(100 * ((1 + b).prod() ** (12 / len(b)) - 1), 2),
        "bench_sharpe": round(sharpe(b), 3), "blend_sharpe": c["blend_sharpe"],
        "period": "–".join(ind["period"]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="restrict to these variants")
    ap.add_argument("--skip-run", action="store_true", help="only rebuild the table from existing json")
    a = ap.parse_args()
    variants = a.only or VARIANTS
    LS_DIR.mkdir(parents=True, exist_ok=True)
    CMP_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    out_rows = []
    for panel in PANELS:
        # published (pre-fix) numbers straight from the stored json
        old = json.loads(OLD_HEADLINE[panel].read_text())
        bench_old = benchmark_monthly(DATA / f"{PANELS[panel]}.parquet")
        s = summarize(old, bench_old)
        out_rows.append({"panel": panel, "variant": "published", **s})
        for v in variants:
            pq = parquet_for(panel, v)
            ls_out = LS_DIR / f"{panel}_{v}"
            cmp_out = CMP_DIR / f"india_vs_us_{panel}_{v}.json"
            if not a.skip_run:
                print(f"[{panel}/{v}] long-short …", flush=True)
                run([sys.executable, "scripts/run_nse_longshort.py", "--data", str(pq), "--out", str(ls_out)])
                run([sys.executable, "scripts/india_vs_us_market_neutral.py",
                     "--india-ls", str(ls_out / "nse_longshort_results.json"),
                     "--india-parquet", str(pq), "--india-label", f"India {panel} {v}",
                     "--out", str(cmp_out)])
            js = json.loads(cmp_out.read_text())
            s = summarize(js, benchmark_monthly(pq))
            out_rows.append({"panel": panel, "variant": v, **s})
            print(f"   alpha {s['alpha_pct']:+.2f}%/yr  t={s['alpha_t']:.2f}  SR={s['neutral_sharpe']:.3f}  "
                  f"hedge-β={s['hedge_beta_mean_sig']}  sleeves={s['sig_sleeves']}", flush=True)

    df = pd.DataFrame(out_rows)
    df.to_csv(AUDIT_DIR / "before_after.csv", index=False)
    print("\nsaved results/nse_data_audit/before_after.csv")


if __name__ == "__main__":
    main()
