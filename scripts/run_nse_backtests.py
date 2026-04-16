"""
NSE 500 Backtests
=================
Runs all 14 strategies on NSE 500 data and stores results in the database
under market='NSE' so they can be displayed separately from S&P 500 results.

Run AFTER download_nse_data.py:
    .venv/bin/python scripts/run_nse_backtests.py

Takes ~30-45 minutes for all 14 strategies on 20 years of NSE data.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.strategies import STRATEGY_REGISTRY
from src.backtesting.engine import Backtester

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

NSE_DATA_PATH = Path("data_processed/nse_prices_clean.parquet")
OUTPUT_DIR    = Path("results/nse_backtests")
BENCHMARK_COL = "NIFTY50_proxy"   # equal-weight all stocks as proxy


def safe_float(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return float(v)


def compute_benchmark(prices_wide: pd.DataFrame) -> pd.Series:
    """Equal-weight benchmark across all NSE 500 stocks."""
    rets   = prices_wide.pct_change(fill_method=None)
    eq_ret = rets.mean(axis=1)
    bench  = (1 + eq_ret).cumprod()
    bench  = bench / bench.iloc[0] * 100
    return bench


def run_strategy(name: str, data: pd.DataFrame) -> dict:
    """Run one strategy and return metrics dict."""
    try:
        strategy_class = STRATEGY_REGISTRY[name]
        strategy = strategy_class(data, strategy_class.DEFAULT_PARAMS.copy())
        bt = Backtester(strategy, data)
        result = bt.run()
        m = result.metrics  # BacktestResult is a dataclass

        # Equity curve as list of {date, value} dicts
        eq = result.equity_curve
        equity_curve = [
            {"date": str(d.date()), "value": round(float(v), 2)}
            for d, v in eq.items()
        ][::5]  # sample every 5th point to reduce size

        return {
            "strategy":    name,
            "market":      "NSE",
            "sharpe":      safe_float(m.get("sharpe_ratio")),
            "cagr":        safe_float(m.get("cagr")),
            "max_dd":      safe_float(m.get("max_drawdown")),
            "volatility":  safe_float(m.get("volatility")),
            "total_return":safe_float(m.get("total_return")),
            "win_rate":    safe_float(m.get("win_rate")),
            "equity_curve": equity_curve,
            "status":      "success",
        }
    except Exception as e:
        log.warning(f"  ✗ {name}: {e}")
        return {"strategy": name, "market": "NSE", "status": "error", "error": str(e)}


def main():
    log.info("=" * 60)
    log.info("NSE 500 Backtests — StrategyHub")
    log.info("=" * 60)

    if not NSE_DATA_PATH.exists():
        log.error(f"NSE data not found at {NSE_DATA_PATH}")
        log.error("Run: .venv/bin/python scripts/download_nse_data.py")
        sys.exit(1)

    log.info(f"Loading NSE data from {NSE_DATA_PATH}...")
    data = pd.read_parquet(NSE_DATA_PATH)
    log.info(f"  {data['symbol'].nunique()} symbols | "
             f"{data['date'].min().date()} → {data['date'].max().date()} | "
             f"{len(data):,} rows")

    # Benchmark
    prices_wide = data.pivot(index="date", columns="symbol", values="close")
    benchmark   = compute_benchmark(prices_wide)

    # Run all strategies
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    summary_rows = []

    for name in STRATEGY_REGISTRY:
        log.info(f"\n  → {name}")
        r = run_strategy(name, data)
        results[name] = r

        if r["status"] == "success":
            log.info(f"     Sharpe: {r['sharpe']:.3f}  |  CAGR: {r['cagr']*100:.1f}%  |  MDD: {r['max_dd']*100:.1f}%")
            summary_rows.append({
                "strategy":  name,
                "market":    "NSE",
                "sharpe":    r["sharpe"],
                "cagr_pct":  round(r["cagr"] * 100, 2) if r["cagr"] else None,
                "max_dd_pct":round(r["max_dd"] * 100, 2) if r["max_dd"] else None,
                "status":    "success",
            })
        else:
            summary_rows.append({"strategy": name, "market": "NSE", "status": "error"})

    # Benchmark stats
    bench_rets = benchmark.pct_change(fill_method=None).dropna()
    bench_sharpe = (bench_rets.mean() / bench_rets.std()) * np.sqrt(252)
    bench_cagr   = (benchmark.iloc[-1] / benchmark.iloc[0]) ** (252 / len(benchmark)) - 1
    log.info(f"\n  Benchmark (equal-weight NSE 500): Sharpe={bench_sharpe:.3f}, CAGR={bench_cagr*100:.1f}%")

    # Save summary CSV
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(OUTPUT_DIR / "nse_summary.csv", index=False)

    # Save full results JSON
    output = {
        "generated_at":   datetime.now().isoformat(),
        "market":         "NSE",
        "n_symbols":      data["symbol"].nunique(),
        "date_range":     [str(data["date"].min().date()), str(data["date"].max().date())],
        "benchmark":      {
            "name":   "Equal-weight NSE 500",
            "sharpe": safe_float(bench_sharpe),
            "cagr":   safe_float(bench_cagr),
        },
        "strategies": {
            name: {k: v for k, v in r.items() if k != "equity_curve"}
            for name, r in results.items()
        },
    }
    with open(OUTPUT_DIR / "nse_results.json", "w") as f:
        json.dump(output, f, indent=2, default=str)

    # Print scorecard
    success = [r for r in summary_rows if r["status"] == "success"]
    success.sort(key=lambda x: x.get("sharpe") or -99, reverse=True)

    log.info(f"\n{'=' * 60}")
    log.info("NSE BACKTEST SCORECARD")
    log.info(f"{'=' * 60}")
    log.info(f"{'Strategy':<35} {'Sharpe':>7} {'CAGR%':>7} {'MDD%':>7}")
    log.info("-" * 60)
    for r in success:
        log.info(f"  {r['strategy']:<33} {r.get('sharpe',0) or 0:>7.3f} "
                 f"{r.get('cagr_pct',0) or 0:>7.1f} {r.get('max_dd_pct',0) or 0:>7.1f}")
    log.info("-" * 60)
    log.info(f"  {'Benchmark (EW NSE 500)':<33} {bench_sharpe:>7.3f} {bench_cagr*100:>7.1f}")
    log.info(f"\nResults saved → {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
