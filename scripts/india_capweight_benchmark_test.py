"""
#2 stress test — bound the India market-neutral alpha against the REAL
cap-weighted Nifty 500, not just our equal-weight benchmark.
=====================================================================
Concern #1: the clean India composite is low-vol/quality-driven with strongly
NEGATIVE beta, and its alpha was measured vs an equal-weight benchmark (Sharpe
~0.31–0.35). A negative-beta sleeve can look extra-good against a noisy, high-vol
equal-weight baseline. The honest test: regress against the actual investable,
cap-weighted Nifty 500 (^CRSLDX) and see if the alpha survives — and by how much.

Output → results/composites/india_capweight_benchmark.json

Run:
    .venv/bin/python scripts/india_capweight_benchmark_test.py
"""
import sys
import json
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtesting.composite_engine import sharpe, ann_vol, mdd, ANNUAL_PERIODS  # noqa: E402
from scripts.india_vs_us_market_neutral import load_sleeves_monthly, capm, benchmark_monthly  # noqa: E402

OUT = ROOT / "results" / "composites" / "india_capweight_benchmark.json"
CACHE = ROOT / "data_raw" / "nifty500_index.parquet"


def nifty500_monthly() -> pd.Series:
    """Real cap-weighted Nifty 500 (^CRSLDX) monthly returns."""
    if CACHE.exists():
        idx = pd.read_parquet(CACHE)["close"]
        idx.index = pd.to_datetime(pd.read_parquet(CACHE)["date"])
    else:
        import yfinance as yf
        d = yf.download("^CRSLDX", start="2005-01-01", end="2025-07-01",
                        auto_adjust=True, progress=False)
        idx = d["Close"].dropna()
        idx = idx.iloc[:, 0] if isinstance(idx, pd.DataFrame) else idx
        pd.DataFrame({"date": idx.index, "close": idx.values}).to_parquet(CACHE, index=False)
    m = idx.resample("M").last().pct_change()
    m.index = pd.to_datetime(m.index)
    return m.rename("nifty500")


def composite_vs(bench: pd.Series, rets: pd.DataFrame, label: str) -> dict:
    rows, neutrals = [], {}
    for name in rets.columns:
        c = capm(rets[name], bench)
        if c is None:
            continue
        neutrals[name] = c["neutral"]
        rows.append({"sleeve": name, "beta": round(c["beta"], 3),
                     "ann_alpha": round(c["ann_alpha"], 4), "alpha_tstat": round(c["alpha_tstat"], 3)})
    sig = [r["sleeve"] for r in rows if r["alpha_tstat"] > 1.96]
    comp = pd.DataFrame({n: neutrals[n] for n in sig}).dropna(how="all").mean(axis=1)
    cc = capm(comp, bench)
    return {"benchmark": label, "benchmark_sharpe": round(sharpe(bench.dropna()), 3),
            "n_sig": len(sig), "sig_sleeves": sig,
            "composite_sharpe": round(sharpe(comp), 3),
            "composite_alpha": round(cc["ann_alpha"], 4),
            "composite_alpha_tstat": round(cc["alpha_tstat"], 3),
            "composite_vol": round(ann_vol(comp), 4),
            "composite_corr_bench": round(float(comp.corr(bench.reindex(comp.index))), 3),
            "per_sleeve": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default=None,
                    help="corporate-action-corrected variant (raw|nohole|adj|adj_nohole|zero40|zero40_nohole): "
                         "reads results/nse_longshort_ca/<panel>_<variant> + the matching "
                         "data_processed panel, writes results/composites_ca/india_capweight_benchmark_<variant>.json")
    args = ap.parse_args()
    nifty = nifty500_monthly()
    print("=" * 82)
    print("INDIA MARKET-NEUTRAL ALPHA — bounded against the REAL cap-weighted Nifty 500")
    print("=" * 82)

    specs = [
        ("clean top-500", "results/nse_longshort_clean/nse_longshort_results.json",
         "data_processed/nse_survivorship_free.parquet"),
        ("clean top-150", "results/nse_longshort_clean150/nse_longshort_results.json",
         "data_processed/nse_survivorship_free_top150.parquet"),
    ]
    out_path = OUT
    if args.variant:
        v = args.variant
        suf = "" if v == "raw" else f"_{v}"
        specs = [
            ("clean top-500", f"results/nse_longshort_ca/top500_{v}/nse_longshort_results.json",
             f"data_processed/nse_survivorship_free{suf}.parquet"),
            ("clean top-150", f"results/nse_longshort_ca/top150_{v}/nse_longshort_results.json",
             f"data_processed/nse_survivorship_free_top150{suf}.parquet"),
        ]
        out_path = ROOT / "results" / "composites_ca" / f"india_capweight_benchmark_{v}.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
    out = {}
    for label, ls, pq in specs:
        rets = load_sleeves_monthly(ROOT / ls)
        ew = benchmark_monthly(ROOT / pq)          # equal-weight (what we used)
        r_ew = composite_vs(ew, rets, "equal-weight")
        r_cw = composite_vs(nifty, rets, "cap-weight Nifty500")
        out[label] = {"equal_weight": r_ew, "cap_weight": r_cw}

        print(f"\n── {label} ──")
        print(f"  {'benchmark':<22}{'benchSR':>8}{'compSR':>8}{'alpha':>8}{'t':>7}{'vol':>7}{'corr':>7}  sleeves")
        for r in (r_ew, r_cw):
            print(f"  {r['benchmark']:<22}{r['benchmark_sharpe']:>8.2f}{r['composite_sharpe']:>8.2f}"
                  f"{r['composite_alpha']*100:>7.1f}%{r['composite_alpha_tstat']:>7.2f}"
                  f"{r['composite_vol']*100:>6.0f}%{r['composite_corr_bench']:>7.2f}  {r['n_sig']} sig")
        # show how the low-vol sleeve's beta/alpha shifts across benchmarks
        def find(rows, s): return next((x for x in rows if x["sleeve"] == s), None)
        lv_ew = find(r_ew["per_sleeve"], "low_volatility_shield")
        lv_cw = find(r_cw["per_sleeve"], "low_volatility_shield")
        if lv_ew and lv_cw:
            print(f"    low_vol_shield: EW beta {lv_ew['beta']:+.2f} a {lv_ew['ann_alpha']*100:+.1f}% t{lv_ew['alpha_tstat']:.1f}"
                  f"  →  CW beta {lv_cw['beta']:+.2f} a {lv_cw['ann_alpha']*100:+.1f}% t{lv_cw['alpha_tstat']:.1f}")

    print("\n" + "=" * 82)
    cw500 = out["clean top-500"]["cap_weight"]
    ew500 = out["clean top-500"]["equal_weight"]
    print(f"VERDICT (clean top-500): vs equal-weight α={ew500['composite_alpha']*100:.1f}%/yr "
          f"(SR {ew500['composite_sharpe']}); vs cap-weight Nifty500 α={cw500['composite_alpha']*100:.1f}%/yr "
          f"(SR {cw500['composite_sharpe']}, t={cw500['composite_alpha_tstat']})")
    surv = cw500['composite_alpha_tstat'] > 1.96
    print("  → alpha " + ("SURVIVES" if surv else "does NOT survive") +
          " a real cap-weighted benchmark" +
          (" — robust, just smaller" if surv else " — was a benchmark/size artifact"))
    print("=" * 82)
    out_path.write_text(json.dumps(out, indent=2))
    print(f"saved: {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
