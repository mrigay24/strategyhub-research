"""
Generate Live Strategy Signals

Downloads 2 years of S&P 500 price data via Yahoo Finance, runs all 14 strategies'
signal generation on the latest data, and saves current holdings to:
  results/live_signals/current_signals.json

Run manually to refresh signals:
  .venv/bin/python scripts/generate_live_signals.py

The API endpoint GET /api/v1/signals/{strategy_name} serves from this cache.
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np

# ── Add project root to path ──────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

import yfinance as yf
from src.strategies import get_strategy, STRATEGY_REGISTRY

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

OUTPUT_PATH = Path("results/live_signals/current_signals.json")
LOOKBACK_PERIOD = "2y"          # Enough for all strategy lookback windows
MIN_COVERAGE = 0.70             # Drop symbols with >30% missing data
TOP_N = 30                      # Max holdings to return per strategy


def get_sp500_symbols() -> list[str]:
    """Fetch current S&P 500 symbols from Wikipedia (with fallback to parquet symbols)."""
    import urllib.request
    try:
        req = urllib.request.Request(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            headers={"User-Agent": "Mozilla/5.0 (compatible; StrategyHub/1.0)"},
        )
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode("utf-8")
        tables = pd.read_html(html, header=0)
        symbols = tables[0]["Symbol"].str.replace(".", "-", regex=False).tolist()
        log.info(f"Fetched {len(symbols)} S&P 500 symbols from Wikipedia")
        return symbols
    except Exception as e:
        log.warning(f"Wikipedia fetch failed ({e}), falling back to extended parquet symbols")
        parquet = Path("data_processed/extended_prices_clean.parquet")
        if parquet.exists():
            df = pd.read_parquet(parquet, columns=["symbol"])
            symbols = df["symbol"].unique().tolist()
            log.info(f"Using {len(symbols)} symbols from extended parquet")
            return symbols
        raise RuntimeError("No symbol source available — Wikipedia blocked and parquet not found")


def download_prices(symbols: list[str]) -> pd.DataFrame:
    """Download adjusted close prices for all symbols."""
    log.info(f"Downloading {LOOKBACK_PERIOD} of price data for {len(symbols)} symbols...")
    raw = yf.download(
        symbols,
        period=LOOKBACK_PERIOD,
        auto_adjust=True,
        progress=False,
        threads=True,
    )

    # Handle both single and multi-symbol outputs
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw

    # Drop symbols with insufficient data
    min_rows = int(len(prices) * MIN_COVERAGE)
    prices = prices.dropna(axis=1, thresh=min_rows)

    # Drop any rows where all values are NaN
    prices = prices.dropna(how="all")

    log.info(f"Clean price matrix: {prices.shape[0]} days × {prices.shape[1]} symbols")
    return prices.astype(float)


def run_strategy_signals(strategy_name: str, prices: pd.DataFrame) -> dict:
    """
    Run a strategy's generate_signals() on live price data.
    Returns the current holdings (top N by weight).
    """
    try:
        strategy_class = STRATEGY_REGISTRY[strategy_name]
        params = strategy_class.DEFAULT_PARAMS.copy()
        strategy = strategy_class(prices, params)
        signals = strategy.generate_signals()

        if signals is None or signals.empty:
            return {"error": "No signals returned"}

        # Get latest non-NaN signal row
        latest = None
        for i in range(len(signals) - 1, max(len(signals) - 10, -1), -1):
            row = signals.iloc[i].dropna()
            row = row[row > 1e-4]
            if len(row) > 0:
                latest = row
                signal_date = signals.index[i].strftime("%Y-%m-%d")
                break

        if latest is None:
            return {"error": "All recent signal rows are empty/zero"}

        # Top N holdings by weight
        top = latest.nlargest(TOP_N)
        # Equal-renormalize so weights sum to 1.0
        top = top / top.sum()

        holdings = [
            {"symbol": sym, "weight": round(float(w), 4), "rank": i + 1}
            for i, (sym, w) in enumerate(top.items())
        ]

        return {
            "signal_date": signal_date,
            "n_holdings": len(latest),
            "holdings": holdings,
        }

    except Exception as e:
        log.warning(f"  ✗ {strategy_name}: {e}")
        return {"error": str(e)}


def main():
    log.info("=" * 60)
    log.info("StrategyHub — Live Signal Generation")
    log.info("=" * 60)

    # 1. Fetch symbols + prices
    symbols = get_sp500_symbols()
    prices = download_prices(symbols)

    signal_date_global = prices.index[-1].strftime("%Y-%m-%d")
    generated_at = datetime.now().isoformat()

    # 2. Run all 14 strategies
    results = {}
    log.info("\nRunning signal generation for all strategies...")
    for strategy_name in STRATEGY_REGISTRY:
        log.info(f"  → {strategy_name}")
        result = run_strategy_signals(strategy_name, prices)
        results[strategy_name] = result
        if "error" not in result:
            log.info(f"     ✓ {result['n_holdings']} holdings, top: {result['holdings'][0]['symbol'] if result['holdings'] else 'N/A'}")

    # 3. Summary
    success = sum(1 for r in results.values() if "error" not in r)
    log.info(f"\nCompleted: {success}/{len(STRATEGY_REGISTRY)} strategies generated signals")

    # 4. Save output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "generated_at": generated_at,
        "signal_date": signal_date_global,
        "data_source": "Yahoo Finance",
        "lookback_period": LOOKBACK_PERIOD,
        "n_symbols": prices.shape[1],
        "strategies": results,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    log.info(f"\nSaved → {OUTPUT_PATH}")
    log.info("Refresh signals at any time: .venv/bin/python scripts/generate_live_signals.py")


if __name__ == "__main__":
    main()
