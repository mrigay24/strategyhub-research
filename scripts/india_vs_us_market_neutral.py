"""
#2 — US vs India: market-neutral alpha, head to head
====================================================
Runs the identical beta-neutral CAPM analysis (full-sample, market-neutral stream
= y - beta*x, alpha t-stat from OLS) on BOTH markets and prints them side by side.

The thesis: US large-cap factors are largely arbitraged away — once beta is
removed, only ~5.8%/yr alpha (Sharpe ~0.38) remains. India is a less-efficient
market (NSE long-only avg SR 1.01 vs US 0.58). If the market-neutral alpha is
materially larger in India, that — not reblending US factors — is where edge lives.

Same signals, same engine, same costs; only the market differs.
US    : results/longshort/longshort_results.json     + equal-weight S&P benchmark
India : results/nse_longshort/nse_longshort_results.json + equal-weight NSE benchmark

CAVEAT: India universe is names-with-history (survivorship bias), US is point-in-time
with delistings. India absolute alpha is optimistic; the GAP is the honest signal.

Output → results/composites/india_vs_us_market_neutral.json

Run:
    .venv/bin/python scripts/india_vs_us_market_neutral.py
"""
import sys
import json
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtesting.composite_engine import sharpe, mdd, ann_vol, ANNUAL_PERIODS  # noqa: E402

US_LS = ROOT / "results" / "longshort" / "longshort_results.json"
IN_LS = ROOT / "results" / "nse_longshort" / "nse_longshort_results.json"
US_PARQUET = ROOT / "data_processed" / "extended_prices_clean.parquet"
IN_PARQUET = ROOT / "data_processed" / "nse_prices_clean.parquet"
OUT = ROOT / "results" / "composites" / "india_vs_us_market_neutral.json"


def _safe(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return round(float(v), 4)


def load_sleeves_monthly(ls_file: Path) -> pd.DataFrame:
    """Monthly returns per sleeve from a *_longshort_results.json equity curve."""
    data = json.loads(ls_file.read_text())["strategies"]
    series = {}
    for name, s in data.items():
        ec = s.get("equity_curve", [])
        if len(ec) < 24:
            continue
        eq = pd.Series([p["value"] for p in ec],
                       index=pd.to_datetime([p["date"] for p in ec]))
        series[name] = eq.resample("M").last().pct_change()
    return pd.DataFrame(series).dropna(how="all")


def benchmark_monthly(parquet: Path) -> pd.Series:
    raw = pd.read_parquet(parquet)
    prices = raw.pivot_table(index="date", columns="symbol", values="close")
    daily = prices.pct_change(fill_method=None).mean(axis=1)
    m = daily.resample("M").apply(lambda x: (1 + x).prod() - 1)
    m.index = pd.to_datetime(m.index)
    return m.rename("benchmark")


def capm(sleeve: pd.Series, bench: pd.Series) -> dict:
    """Full-sample CAPM. Market-neutral stream = y - beta*x (corr 0, keeps alpha)."""
    df = pd.concat([sleeve.rename("y"), bench.rename("x")], axis=1).dropna()
    if len(df) < 24:
        return None
    y, x = df["y"].values, df["x"].values
    n = len(y)
    xbar = x.mean()
    sxx = np.sum((x - xbar) ** 2)
    beta = np.sum((x - xbar) * (y - y.mean())) / sxx
    alpha = y.mean() - beta * xbar
    resid = y - alpha - beta * x
    s_e = np.sqrt(np.sum(resid ** 2) / (n - 2))
    se_alpha = s_e * np.sqrt(1.0 / n + xbar ** 2 / sxx)
    t = alpha / se_alpha if se_alpha > 0 else 0.0
    neutral = pd.Series(y - beta * x, index=df.index)
    return {"beta": float(beta), "ann_alpha": float(alpha * ANNUAL_PERIODS),
            "alpha_tstat": float(t), "neutral_sharpe": float(sharpe(neutral)),
            "neutral": neutral}


def analyze(market: str, ls_file: Path, parquet: Path) -> dict:
    rets = load_sleeves_monthly(ls_file)
    bench = benchmark_monthly(parquet)
    rows, neutrals = [], {}
    for name in rets.columns:
        c = capm(rets[name], bench)
        if c is None:
            continue
        neutrals[name] = c["neutral"]
        rows.append({"sleeve": name, "beta": _safe(c["beta"]),
                     "raw_sharpe": _safe(sharpe(rets[name].dropna())),
                     "ann_alpha": _safe(c["ann_alpha"]), "alpha_tstat": _safe(c["alpha_tstat"]),
                     "neutral_sharpe": _safe(c["neutral_sharpe"])})
    rows.sort(key=lambda r: r["alpha_tstat"], reverse=True)

    sig = [r["sleeve"] for r in rows if (r["alpha_tstat"] or 0) > 1.96]
    if len(sig) < 2:
        sig = [r["sleeve"] for r in rows if (r["ann_alpha"] or 0) > 0][:5]
    comp = pd.DataFrame({n: neutrals[n] for n in sig}).dropna(how="all").mean(axis=1)
    comp_capm = capm(comp, bench)

    rng = np.random.default_rng(7)
    arr = comp.dropna().values
    sims = np.array([sharpe(pd.Series(arr[rng.integers(0, len(arr), len(arr))]))
                     for _ in range(5000)])
    p = float((sims <= 0).mean())

    # blend payoff
    bw = bench.reindex(comp.index).dropna()
    cc = comp.reindex(bw.index)
    mu = np.array([bw.mean(), cc.mean()]) - 0.02 / ANNUAL_PERIODS
    cov = np.cov(np.vstack([bw.values, cc.values]))
    try:
        w = np.clip(np.linalg.solve(cov, mu), 0, None)
        w = w / w.sum() if w.sum() > 0 else np.array([0.5, 0.5])
    except np.linalg.LinAlgError:
        w = np.array([0.5, 0.5])
    blend = w[0] * bw + w[1] * cc

    return {
        "market": market, "n_sleeves": len(rows),
        "period": [str(rets.index[0].date()), str(rets.index[-1].date())],
        "benchmark_sharpe": _safe(sharpe(bench.reindex(comp.index).dropna())),
        "n_significant_positive_alpha": len(sig), "significant_sleeves": sig,
        "per_sleeve": rows,
        "composite": {
            "neutral_sharpe": _safe(sharpe(comp)), "bootstrap_p": _safe(p),
            "ann_alpha": _safe(comp_capm["ann_alpha"]), "alpha_tstat": _safe(comp_capm["alpha_tstat"]),
            "ann_vol": _safe(ann_vol(comp)), "mdd": _safe(mdd(comp)),
            "corr_to_benchmark": _safe(float(comp.corr(bench.reindex(comp.index)))),
            "blend_benchmark_w": _safe(w[0]), "blend_composite_w": _safe(w[1]),
            "blend_sharpe": _safe(sharpe(blend)),
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--india-ls", default=str(IN_LS), help="India L/S results json")
    ap.add_argument("--india-parquet", default=str(IN_PARQUET), help="India price parquet (benchmark)")
    ap.add_argument("--india-label", default="India / NSE")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()

    us = analyze("US / S&P", US_LS, US_PARQUET)
    ind = analyze(a.india_label, Path(a.india_ls), Path(a.india_parquet))

    print("=" * 78)
    print("US vs INDIA — MARKET-NEUTRAL ALPHA (beta-removed, full-sample CAPM)")
    print("=" * 78)
    print(f"\n{'metric':<38}{'US / S&P':>18}{'India / NSE':>18}")
    print("-" * 78)
    def line(label, u, i, pct=False, plus=False):
        fu = (f"{u*100:+.1f}%" if plus else f"{u*100:.1f}%") if pct else f"{u:.3f}"
        fi = (f"{i*100:+.1f}%" if plus else f"{i*100:.1f}%") if pct else f"{i:.3f}"
        print(f"{label:<38}{fu:>18}{fi:>18}")
    cu, ci = us["composite"], ind["composite"]
    print(f"{'period':<38}{'–'.join(us['period']):>18}{'–'.join(ind['period']):>18}")
    print(f"{'sleeves w/ significant +alpha':<38}{us['n_significant_positive_alpha']:>18}{ind['n_significant_positive_alpha']:>18}")
    line("market-neutral composite Sharpe", cu["neutral_sharpe"], ci["neutral_sharpe"])
    line("  bootstrap p-value", cu["bootstrap_p"], ci["bootstrap_p"])
    line("annual alpha", cu["ann_alpha"], ci["ann_alpha"], pct=True, plus=True)
    line("  alpha t-stat", cu["alpha_tstat"], ci["alpha_tstat"])
    line("ann vol", cu["ann_vol"], ci["ann_vol"], pct=True)
    line("max drawdown", cu["mdd"], ci["mdd"], pct=True, plus=True)
    line("corr to benchmark", cu["corr_to_benchmark"], ci["corr_to_benchmark"])
    line("benchmark Sharpe (matched window)", us["benchmark_sharpe"], ind["benchmark_sharpe"])
    line("blend Sharpe (bench+composite)", cu["blend_sharpe"], ci["blend_sharpe"])
    print("-" * 78)

    ratio = (ci["ann_alpha"] / cu["ann_alpha"]) if cu["ann_alpha"] else float("nan")
    print(f"\nIndia market-neutral alpha is {ratio:.1f}× the US "
          f"({ci['ann_alpha']*100:.1f}%/yr vs {cu['ann_alpha']*100:.1f}%/yr).")
    verdict = ("INEFFICIENCY THESIS CONFIRMED — India market-neutral alpha far exceeds US"
               if ci["ann_alpha"] > 1.5 * cu["ann_alpha"] and ci["alpha_tstat"] > 1.96
               else "MIXED — India edge not clearly larger after beta removal")
    print(f"VERDICT: {verdict}")
    print("(reminder: India carries survivorship bias — the GAP is the signal, not the level)")
    print("=" * 78)

    out_path = Path(a.out)
    out_path.write_text(json.dumps({"us": us, "india": ind, "alpha_ratio_india_over_us": _safe(ratio),
                                    "verdict": verdict}, indent=2))
    print(f"saved: {out_path}")


if __name__ == "__main__":
    main()
