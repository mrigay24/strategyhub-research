"""
#2 — India L/S sleeves: run the dollar-neutral long-short engine on NSE data
===========================================================================
Reuses the EXACT US factor-score functions and L/S engine (from
run_longshort_backtests.py) on the Indian universe, so US-vs-India is a clean
apples-to-apples comparison: same signals, same engine, same costs — only the
market changes.

Benchmark = equal-weight of all NSE names (Nifty-500-proxy), identical definition
to the US equal-weight benchmark, so CAPM betas are comparable across markets.

Universe: 328 NSE names, 2005–2026 (data_processed/nse_prices_clean.parquet).
CAVEAT: this is the set of names WITH history, not point-in-time Nifty 500
membership — so it carries survivorship bias (unlike the US extended data, which
includes delistings). Treat India absolute numbers as optimistic; the US-vs-India
*gap* is the honest signal.

Output → results/nse_longshort/nse_longshort_results.json

Run:
    .venv/bin/python scripts/run_nse_longshort.py
"""
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtesting.long_short_engine import LongShortBacktester  # noqa: E402
from scripts.run_longshort_backtests import (  # noqa: E402  (reuse US machinery)
    STRATEGY_CONFIGS, _rebal_dates, _build_sparse, QUINTILE,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# defaults = the survivorship-BIASED set; override with --data/--out for clean data
DEFAULT_PARQUET = ROOT / "data_processed" / "nse_prices_clean.parquet"
DEFAULT_OUT = ROOT / "results" / "nse_longshort"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(DEFAULT_PARQUET), help="long-format price parquet")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="results dir")
    a = ap.parse_args()
    NSE_PARQUET = Path(a.data)
    OUT_DIR = Path(a.out).resolve()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log.info(f"data: {NSE_PARQUET.name}  →  out: {OUT_DIR}")
    log.info("=" * 65)
    log.info("StrategyHub — India (NSE) Long-Short Factor Backtest")
    log.info("=" * 65)

    raw = pd.read_parquet(NSE_PARQUET)
    prices = raw.pivot_table(index="date", columns="symbol", values="close")
    prices.index = pd.to_datetime(prices.index)
    prices = prices.sort_index().astype(float)
    log.info(f"  {prices.shape[0]:,} days × {prices.shape[1]} symbols  "
             f"({prices.index[0].date()} → {prices.index[-1].date()})")

    returns = prices.pct_change(fill_method=None).clip(-0.95, 2.0)
    # Nifty-500-proxy benchmark = equal-weight of all NSE names (same def as US)
    nse_bench = returns.mean(axis=1).fillna(0)

    results = {}
    success = 0
    for name, (freq, score_fn) in STRATEGY_CONFIGS.items():
        log.info(f"\n{'─'*55}\n  {name}  (rebal: {freq})")
        try:
            rebal_idx = _rebal_dates(prices.index, freq)
            scores_rebal = score_fn(prices, returns, rebal_idx)
            if scores_rebal.empty:
                results[name] = {"error": "No scores produced"}
                continue
            sparse = _build_sparse(scores_rebal, prices.index)
            engine = LongShortBacktester(
                prices=prices, factor_scores=sparse, quintile_pct=QUINTILE,
                commission_bps=15.0, borrow_cost_bps=50.0, spy_returns=nse_bench,
            )
            r = engine.run(strategy_name=name)
            log.info(f"  ✓ LS Sharpe={r.sharpe_ratio:.3f}  CAGR={r.cagr*100:.1f}%  "
                     f"MDD={r.max_drawdown*100:.1f}%  bench_corr={r.spy_correlation:.3f}")
            results[name] = r.to_dict()
            success += 1
        except Exception as e:
            import traceback
            log.error(f"  ✗ {name}: {e}\n{traceback.format_exc()}")
            results[name] = {"error": str(e)}

    log.info(f"\n{'='*65}\nCompleted: {success}/{len(STRATEGY_CONFIGS)}")
    rows = sorted([(n, r) for n, r in results.items() if "error" not in r],
                  key=lambda x: x[1].get("sharpe_ratio", -99), reverse=True)
    log.info(f"\n{'Strategy':<32}{'LS Sharpe':>10}{'CAGR':>8}{'benchCorr':>11}")
    log.info("─" * 61)
    for n, r in rows:
        log.info(f"  {n:<30}{r.get('sharpe_ratio', float('nan')):>10.3f}"
                 f"{r.get('cagr', float('nan'))*100:>7.1f}%{r.get('spy_correlation', float('nan')):>11.3f}")

    out = {
        "generated_at": datetime.now().isoformat(),
        "market": "India / NSE",
        "benchmark": "equal-weight NSE (Nifty-500 proxy)",
        "data_period": f"{prices.index[0].date()} – {prices.index[-1].date()}",
        "n_symbols": prices.shape[1],
        "quintile_pct": QUINTILE, "commission_bps": 15.0, "borrow_cost_bps": 50.0,
        "survivorship_caveat": "names-with-history, not point-in-time membership",
        "strategies": results,
    }
    (OUT_DIR / "nse_longshort_results.json").write_text(json.dumps(out, indent=2))
    log.info(f"\nSaved → {OUT_DIR / 'nse_longshort_results.json'}")


if __name__ == "__main__":
    main()
