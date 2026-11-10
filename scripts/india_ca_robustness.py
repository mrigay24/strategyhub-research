"""
India market-neutral alpha — robustness of the corporate-action fix
===================================================================
`rerun_india_corrected.py` lets each variant re-select its own "significant" sleeves (t>1.96),
so the headline can move because the SELECTION moved, not because the data did. This script
separates the effects. For raw / adj / adj_nohole panels and for two benchmarks
(the panel's own equal-weight index, and the real cap-weighted Nifty 500 which our data
fixes cannot touch) it reports the beta-neutral composite alpha and t-stat for:

  A. published selection  – the exact sleeve lists behind the old headline (fixed)
  B. re-selected          – sleeves with in-sample alpha t>1.96 on THAT variant
  C. unselected           – equal-weight of all 14 sleeves (no data-snooping on the t-stat)

It also reports the 2x2 decomposition (sleeve P&L raw/adj  x  benchmark raw/adj) of the
change in the published-selection alpha, to show how much is real sleeve P&L and how much
is the equal-weight benchmark's drift being repaired (negative-beta sleeves earn
alpha = mean(y) - beta*mean(x), so a higher benchmark mean lifts measured alpha).

Output -> results/nse_data_audit/robustness.csv (+ printed tables)
Run:  .venv/bin/python scripts/india_ca_robustness.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.india_vs_us_market_neutral import load_sleeves_monthly, capm, benchmark_monthly  # noqa: E402
from scripts.india_capweight_benchmark_test import nifty500_monthly  # noqa: E402

DATA = ROOT / "data_processed"
LS = ROOT / "results" / "nse_longshort_ca"
OUT = ROOT / "results" / "nse_data_audit" / "robustness.csv"
STEMS = {"top500": "nse_survivorship_free", "top150": "nse_survivorship_free_top150"}
VARIANTS = ["raw", "adj", "adj_nohole"]
PUBLISHED = {
    ("top500", "EW"): ["low_volatility_shield", "volatility_targeting", "quality_low_vol",
                       "high_quality_roic", "52_week_high_breakout", "moving_average_trend"],
    ("top500", "CW"): ["high_quality_roic", "low_volatility_shield", "quality_low_vol", "volatility_targeting"],
    ("top150", "EW"): ["low_volatility_shield", "quality_low_vol", "volatility_targeting"],
    ("top150", "CW"): ["low_volatility_shield", "quality_low_vol", "volatility_targeting"],
}


def composite(rets: pd.DataFrame, bench: pd.Series, sleeves: list[str]) -> dict | None:
    sleeves = [s for s in sleeves if s in rets.columns]
    if len(sleeves) == 0:
        return None
    neutral = {s: capm(rets[s], bench)["neutral"] for s in sleeves}
    comp = pd.DataFrame(neutral).dropna(how="all").mean(axis=1)
    c = capm(comp, bench)
    betas = [capm(rets[s], bench)["beta"] for s in sleeves]
    return {"n": len(sleeves), "alpha_pct": 100 * c["ann_alpha"], "t": c["alpha_tstat"],
            "sharpe": c["neutral_sharpe"], "mean_beta": float(np.mean(betas))}


def selected(rets: pd.DataFrame, bench: pd.Series) -> list[str]:
    ok = []
    for s in rets.columns:
        c = capm(rets[s], bench)
        if c and c["alpha_tstat"] > 1.96:
            ok.append(s)
    return ok


def main():
    cw = nifty500_monthly()
    rows = []
    for panel, stem in STEMS.items():
        for variant in VARIANTS:
            rets = load_sleeves_monthly(LS / f"{panel}_{variant}" / "nse_longshort_results.json")
            pq = DATA / (f"{stem}.parquet" if variant == "raw" else f"{stem}_{variant}.parquet")
            benches = {"EW": benchmark_monthly(pq), "CW": cw}
            for bname, bench in benches.items():
                sets = {
                    "A_published": PUBLISHED[(panel, bname)],
                    "B_reselected": selected(rets, bench),
                    "C_all14": list(rets.columns),
                }
                for sname, sl in sets.items():
                    r = composite(rets, bench, sl)
                    if r:
                        rows.append({"panel": panel, "variant": variant, "benchmark": bname,
                                     "sleeve_set": sname, **{k: round(v, 3) for k, v in r.items()}})
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    pd.set_option("display.width", 200)
    for panel in STEMS:
        print(f"\n===== {panel} =====")
        for bname in ("EW", "CW"):
            sub = df[(df.panel == panel) & (df.benchmark == bname)]
            print(f"\n  benchmark = {bname}  (alpha %/yr, t-stat, n sleeves)")
            piv = sub.pivot_table(index="sleeve_set", columns="variant", values=["alpha_pct", "t", "n"])
            print(piv.reindex(columns=VARIANTS, level=1).round(2).to_string())

    # 2x2 decomposition (EW benchmark, published selection)
    print("\n===== 2x2 decomposition of the published-selection EW alpha (sleeves x benchmark) =====")
    dec = []
    for panel, stem in STEMS.items():
        sl = PUBLISHED[(panel, "EW")]
        r_raw = load_sleeves_monthly(LS / f"{panel}_raw" / "nse_longshort_results.json")
        r_adj = load_sleeves_monthly(LS / f"{panel}_adj_nohole" / "nse_longshort_results.json")
        b_raw = benchmark_monthly(DATA / f"{stem}.parquet")
        b_adj = benchmark_monthly(DATA / f"{stem}_adj_nohole.parquet")
        for lr, rr in (("raw", r_raw), ("adj_nohole", r_adj)):
            for lb, bb in (("raw", b_raw), ("adj_nohole", b_adj)):
                c = composite(rr, bb, sl)
                dec.append({"panel": panel, "sleeve_pnl": lr, "benchmark": lb,
                            "alpha_pct": round(c["alpha_pct"], 2), "t": round(c["t"], 2), "mean_beta": round(c["mean_beta"], 3)})
    d2 = pd.DataFrame(dec)
    print(d2.to_string(index=False))
    d2.to_csv(OUT.parent / "decomposition_2x2.csv", index=False)
    print(f"\nsaved {OUT.relative_to(ROOT)} and decomposition_2x2.csv")


if __name__ == "__main__":
    main()
