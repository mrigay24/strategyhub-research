"""
Generate Live NSE Signals
=========================
Downloads latest NSE 500 price data and runs all 14 strategies,
saving current holdings to results/live_signals/nse_signals.json

Run:
    .venv/bin/python scripts/generate_nse_signals.py
"""

import sys
import json
import logging
import urllib.request
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np
import yfinance as yf

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.strategies import get_strategy, STRATEGY_REGISTRY

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

OUTPUT_PATH    = Path("results/live_signals/nse_signals.json")
LOOKBACK_DAYS  = 504   # ~2 years of trading days
MIN_COVERAGE   = 0.70
TOP_N          = 30


def get_nse500_symbols() -> list:
    log.info("Fetching NIFTY 500 symbols from Wikipedia...")
    req = urllib.request.Request(
        "https://en.wikipedia.org/wiki/NIFTY_500",
        headers={"User-Agent": "Mozilla/5.0 (compatible; StrategyHub/1.0)"},
    )
    with urllib.request.urlopen(req) as r:
        tables = pd.read_html(r.read().decode("utf-8"))
    t = tables[4]
    t.columns = t.iloc[0]
    t = t.iloc[1:].reset_index(drop=True)
    symbols = [s + ".NS" for s in t["Symbol"].dropna().str.strip().tolist()]
    log.info(f"Found {len(symbols)} NIFTY 500 symbols")
    return symbols


def download_prices(symbols: list) -> pd.DataFrame:
    log.info(f"Downloading 2y price data for {len(symbols)} NSE symbols...")
    raw = yf.download(symbols, period="2y", auto_adjust=True, progress=False, threads=True)
    prices = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
    min_rows = int(len(prices) * MIN_COVERAGE)
    prices = prices.dropna(axis=1, thresh=min_rows).dropna(how="all").astype(float)

    # Remove .NS suffix from column names for strategy compatibility
    prices.columns = [c.replace(".NS", "") for c in prices.columns]
    log.info(f"Clean price matrix: {prices.shape[0]} days × {prices.shape[1]} symbols")
    return prices


def run_strategy_signals(strategy_name: str, prices: pd.DataFrame) -> dict:
    try:
        strategy_class = STRATEGY_REGISTRY[strategy_name]
        strategy = strategy_class(prices, strategy_class.DEFAULT_PARAMS.copy())
        signals = strategy.generate_signals()
        if signals is None or signals.empty:
            return {"error": "No signals"}

        latest = None
        for i in range(len(signals) - 1, max(len(signals) - 10, -1), -1):
            row = signals.iloc[i].dropna()
            row = row[row > 1e-4]
            if len(row) > 0:
                latest = row
                signal_date = signals.index[i].strftime("%Y-%m-%d")
                break

        if latest is None:
            return {"error": "All recent rows empty"}

        top = latest.nlargest(TOP_N)
        top = top / top.sum()
        holdings = [
            {"symbol": sym, "weight": round(float(w), 4), "rank": i + 1}
            for i, (sym, w) in enumerate(top.items())
        ]
        return {"signal_date": signal_date, "n_holdings": len(latest), "holdings": holdings}

    except Exception as e:
        log.warning(f"  ✗ {strategy_name}: {e}")
        return {"error": str(e)}


def main():
    log.info("=" * 60)
    log.info("StrategyHub — NSE Live Signal Generation")
    log.info("=" * 60)

    symbols = get_nse500_symbols()
    prices  = download_prices(symbols)
    signal_date = prices.index[-1].strftime("%Y-%m-%d")

    results = {}
    log.info("Running signal generation...")
    for name in STRATEGY_REGISTRY:
        log.info(f"  → {name}")
        r = run_strategy_signals(name, prices)
        results[name] = r
        if "error" not in r:
            top = r["holdings"][0]["symbol"] if r["holdings"] else "N/A"
            log.info(f"     ✓ {r['n_holdings']} holdings, top: {top}")

    success = sum(1 for r in results.values() if "error" not in r)
    log.info(f"\nCompleted: {success}/{len(STRATEGY_REGISTRY)} strategies")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "generated_at":  datetime.now().isoformat(),
        "signal_date":   signal_date,
        "market":        "NSE",
        "data_source":   "Yahoo Finance (.NS)",
        "n_symbols":     prices.shape[1],
        "strategies":    results,
    }
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    log.info(f"Saved → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
