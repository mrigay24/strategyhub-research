"""
Market Sentiment Tracker
========================
Pulls real-time market sentiment indicators and prints a daily dashboard.
Run each morning alongside the trade list for context on WHEN to act on signals.

Usage:
    .venv/bin/python scripts/market_sentiment.py

    # Save to JSON:
    .venv/bin/python scripts/market_sentiment.py --save

Indicators:
    1. VIX (CBOE Volatility Index) — market fear gauge
    2. Put/Call Ratio (via VIX term structure proxy)
    3. Market Breadth — % of S&P 500 above 50-day MA
    4. Momentum — SPY 1-month, 3-month, 6-month return
    5. Sector rotation — which sectors are leading/lagging
    6. Regime classification — BULL / BEAR / HIGH-VOL / SIDEWAYS
"""

import sys
import json
import logging
from datetime import datetime, date, timedelta
from pathlib import Path

import pandas as pd
import numpy as np
import yfinance as yf

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

OUTPUT_DIR = Path("results/sentiment")

# Sector ETFs for rotation analysis
SECTOR_ETFS = {
    "Technology":       "XLK",
    "Healthcare":       "XLV",
    "Financials":       "XLF",
    "Energy":           "XLE",
    "Utilities":        "XLU",
    "Consumer Disc.":   "XLY",
    "Consumer Staples": "XLP",
    "Industrials":      "XLI",
    "Materials":        "XLB",
    "Real Estate":      "XLRE",
    "Communication":    "XLC",
}


def fetch_prices(tickers: list, period: str = "1y") -> pd.DataFrame:
    """Download adjusted close for a list of tickers."""
    raw = yf.download(tickers, period=period, auto_adjust=True, progress=False)
    if isinstance(raw.columns, pd.MultiIndex):
        return raw["Close"].astype(float)
    return raw.astype(float)


# ── 1. VIX Fear Gauge ────────────────────────────────────────────────────────

def get_vix() -> dict:
    """VIX level + classification."""
    vix = yf.Ticker("^VIX").history(period="5d")
    if vix.empty:
        return {"level": None, "label": "Unknown", "signal": "NEUTRAL"}

    level = round(float(vix["Close"].iloc[-1]), 2)
    prev  = round(float(vix["Close"].iloc[-2]), 2) if len(vix) > 1 else level
    change = round(level - prev, 2)

    if level < 15:
        label, signal = "Complacency", "CAUTION"       # too calm, often precedes reversal
    elif level < 20:
        label, signal = "Low Fear",    "BULLISH"
    elif level < 25:
        label, signal = "Moderate",    "NEUTRAL"
    elif level < 30:
        label, signal = "Elevated",    "BEARISH"
    else:
        label, signal = "Extreme Fear","EXTREME FEAR"

    return {"level": level, "change": change, "label": label, "signal": signal}


# ── 2. Market Breadth ────────────────────────────────────────────────────────

def get_market_breadth(sp500_prices: pd.DataFrame) -> dict:
    """
    % of S&P 500 stocks above their 50-day and 200-day moving average.
    High breadth (>70%) = broad participation = healthy bull.
    Low breadth (<30%) = narrow market = fragile, watch for reversal.
    """
    if sp500_prices.empty or len(sp500_prices) < 200:
        return {"above_50d": None, "above_200d": None, "signal": "UNKNOWN"}

    ma50  = sp500_prices.rolling(50).mean()
    ma200 = sp500_prices.rolling(200).mean()

    latest       = sp500_prices.iloc[-1]
    latest_ma50  = ma50.iloc[-1]
    latest_ma200 = ma200.iloc[-1]

    above_50  = (latest > latest_ma50).mean() * 100
    above_200 = (latest > latest_ma200).mean() * 100

    if above_50 >= 70:
        signal = "BULLISH"
    elif above_50 >= 50:
        signal = "NEUTRAL"
    elif above_50 >= 30:
        signal = "BEARISH"
    else:
        signal = "EXTREME BEARISH"

    return {
        "above_50d":  round(above_50, 1),
        "above_200d": round(above_200, 1),
        "signal":     signal,
    }


# ── 3. SPY Momentum ──────────────────────────────────────────────────────────

def get_spy_momentum(spy: pd.Series) -> dict:
    """1M, 3M, 6M, 12M returns for SPY. Trend direction matters."""
    if spy.empty:
        return {}

    def ret(n):
        return round((spy.iloc[-1] / spy.iloc[-n] - 1) * 100, 2) if len(spy) >= n else None

    r1m  = ret(21)
    r3m  = ret(63)
    r6m  = ret(126)
    r12m = ret(252)

    # Trend score: count of positive periods
    positives = sum(1 for r in [r1m, r3m, r6m, r12m] if r and r > 0)
    if positives >= 3:
        signal = "BULLISH"
    elif positives >= 2:
        signal = "NEUTRAL"
    else:
        signal = "BEARISH"

    return {
        "1m_return":  r1m,
        "3m_return":  r3m,
        "6m_return":  r6m,
        "12m_return": r12m,
        "signal":     signal,
    }


# ── 4. Sector Rotation ───────────────────────────────────────────────────────

def get_sector_rotation(sector_prices: pd.DataFrame) -> dict:
    """
    1-month return for each sector ETF.
    Leading sectors = risk appetite.
    Lagging = defensive rotation = caution signal.
    """
    if sector_prices.empty:
        return {}

    returns = {}
    for sector, ticker in SECTOR_ETFS.items():
        if ticker in sector_prices.columns:
            prices = sector_prices[ticker].dropna()
            if len(prices) >= 21:
                r = (prices.iloc[-1] / prices.iloc[-21] - 1) * 100
                returns[sector] = round(float(r), 2)

    if not returns:
        return {}

    sorted_rets = sorted(returns.items(), key=lambda x: x[1], reverse=True)

    # Risk-on if tech/consumer disc lead; risk-off if utilities/staples lead
    top3     = [s for s, _ in sorted_rets[:3]]
    bottom3  = [s for s, _ in sorted_rets[-3:]]
    risk_on  = {"Technology", "Consumer Disc.", "Financials", "Industrials"}
    risk_off = {"Utilities", "Consumer Staples", "Healthcare"}

    leading_risk_on  = len(set(top3) & risk_on)
    leading_risk_off = len(set(top3) & risk_off)

    if leading_risk_on >= 2:
        rotation_signal = "RISK-ON"
    elif leading_risk_off >= 2:
        rotation_signal = "RISK-OFF"
    else:
        rotation_signal = "MIXED"

    return {
        "returns":          dict(sorted_rets),
        "leaders":          top3,
        "laggards":         bottom3,
        "rotation_signal":  rotation_signal,
    }


# ── 5. Overall Regime ────────────────────────────────────────────────────────

def classify_regime(vix: dict, breadth: dict, momentum: dict, rotation: dict) -> dict:
    """
    Combine all signals into a single regime verdict with action guidance.
    """
    signals = [
        vix.get("signal", "NEUTRAL"),
        breadth.get("signal", "NEUTRAL"),
        momentum.get("signal", "NEUTRAL"),
        rotation.get("rotation_signal", "MIXED"),
    ]

    bull_count = sum(1 for s in signals if s in {"BULLISH", "RISK-ON", "Low Fear"})
    bear_count = sum(1 for s in signals if s in {"BEARISH", "EXTREME BEARISH", "RISK-OFF", "EXTREME FEAR"})

    if vix.get("level", 20) >= 30:
        regime  = "HIGH-VOLATILITY"
        action  = "REDUCE SIZE — use 50% of normal allocation. High VIX = binary risk."
        color   = "RED"
    elif bull_count >= 3:
        regime  = "BULL"
        action  = "FULL ALLOCATION — execute morning trade list normally."
        color   = "GREEN"
    elif bear_count >= 3:
        regime  = "BEAR"
        action  = "SKIP TODAY — all factor strategies fail in bear markets. Protect capital."
        color   = "RED"
    elif bull_count >= 2:
        regime  = "BULL-LEANING"
        action  = "PROCEED — slight caution, stick to top 10 positions only."
        color   = "YELLOW"
    else:
        regime  = "SIDEWAYS"
        action  = "SELECTIVE — only take ★★ rated positions (5+ strategy confirmations)."
        color   = "YELLOW"

    return {"regime": regime, "action": action, "color": color,
            "bull_signals": bull_count, "bear_signals": bear_count}


# ── Print Dashboard ───────────────────────────────────────────────────────────

def print_dashboard(vix, breadth, momentum, rotation, regime):
    sep = "─" * 72
    today = date.today().strftime("%B %d, %Y")

    print(f"\n{'═' * 72}")
    print(f"  STRATEGYHUB — MARKET SENTIMENT DASHBOARD")
    print(f"  {today}")
    print(f"{'═' * 72}\n")

    # Regime verdict (top)
    regime_icon = "🟢" if regime["color"] == "GREEN" else ("🔴" if regime["color"] == "RED" else "🟡")
    print(f"  {regime_icon} REGIME: {regime['regime']}")
    print(f"  → {regime['action']}")
    print()

    # VIX
    print("  VIX (Fear Gauge)")
    print(sep)
    vix_change = f"({'+'if (vix.get('change',0) or 0)>0 else ''}{vix.get('change',0):.1f} today)" if vix.get("change") else ""
    print(f"  Level: {vix.get('level', 'N/A')} {vix_change}")
    print(f"  Status: {vix.get('label', 'N/A')} — {vix.get('signal', 'N/A')}")
    print()

    # Breadth
    print("  MARKET BREADTH (% S&P 500 above moving averages)")
    print(sep)
    print(f"  Above 50-day MA:  {breadth.get('above_50d', 'N/A')}%")
    print(f"  Above 200-day MA: {breadth.get('above_200d', 'N/A')}%")
    print(f"  Signal: {breadth.get('signal', 'N/A')}")
    print()

    # SPY Momentum
    print("  SPY MOMENTUM")
    print(sep)
    for period, key in [("1 month", "1m_return"), ("3 months", "3m_return"),
                         ("6 months", "6m_return"), ("12 months", "12m_return")]:
        val = momentum.get(key)
        arrow = "▲" if val and val > 0 else ("▼" if val and val < 0 else "─")
        print(f"  {period:<12}: {arrow} {val:+.1f}%" if val is not None else f"  {period:<12}: N/A")
    print(f"  Signal: {momentum.get('signal', 'N/A')}")
    print()

    # Sector rotation
    if rotation.get("returns"):
        print("  SECTOR ROTATION (1-month returns)")
        print(sep)
        for sector, ret in rotation["returns"].items():
            bar = "▓" * min(int(abs(ret) / 2), 15)
            lead = " ← LEADING" if sector in rotation.get("leaders", []) else (
                   " ← LAGGING" if sector in rotation.get("laggards", []) else "")
            print(f"  {sector:<20} {ret:>+6.1f}%  {bar}{lead}")
        print(f"  Signal: {rotation.get('rotation_signal', 'N/A')}")
        print()

    print(f"{'═' * 72}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--save", action="store_true", help="Save output to JSON")
    parser.add_argument("--breadth-symbols", type=int, default=100,
                        help="Number of S&P 500 stocks to use for breadth (default 100, faster)")
    args = parser.parse_args()

    log.info("Fetching market sentiment data...")

    # Fetch all data
    spy_data    = fetch_prices(["SPY"], period="2y")
    vix_data    = get_vix()

    # Breadth: use a representative sample of large caps for speed
    sp500_sample = [
        "AAPL","MSFT","AMZN","NVDA","GOOGL","META","BRK-B","LLY","AVGO","JPM",
        "UNH","XOM","TSLA","PG","MA","HD","MRK","COST","CVX","ABBV",
        "KO","PEP","WMT","BAC","CRM","ACN","MCD","TMO","CSCO","ABT",
        "DHR","TXN","NEE","ADBE","LIN","PM","ORCL","QCOM","AMD","UPS",
        "AMGN","LOW","INTU","BMY","GE","SPGI","CAT","HON","BA","DE",
        "MMC","CB","AXP","BLK","SYK","ISRG","VRTX","REGN","MO","CI",
        "ZTS","SO","DUK","AON","EMR","PLD","AMT","CCI","PSA","EQR",
        "GS","MS","USB","PNC","TFC","COF","SCHW","ICE","CME","MCO",
        "RTX","LMT","NOC","GD","ITW","PH","ROK","ETN","DOV","XYL",
        "FCX","NEM","APD","SHW","ECL","IFF","PPG","VMC","MLM","NUE",
    ]
    sp500_prices = fetch_prices(sp500_sample[:args.breadth_symbols], period="1y")

    sector_prices = fetch_prices(list(SECTOR_ETFS.values()), period="3mo")

    # Compute indicators
    log.info("Computing indicators...")
    spy_series = spy_data["SPY"] if "SPY" in spy_data.columns else spy_data.iloc[:, 0]

    vix      = vix_data
    breadth  = get_market_breadth(sp500_prices)
    momentum = get_spy_momentum(spy_series)
    rotation = get_sector_rotation(sector_prices)
    regime   = classify_regime(vix, breadth, momentum, rotation)

    # Print
    print_dashboard(vix, breadth, momentum, rotation, regime)

    # Save
    if args.save:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out = {
            "generated_at": datetime.now().isoformat(),
            "regime":       regime,
            "vix":          vix,
            "breadth":      breadth,
            "momentum":     momentum,
            "sector_rotation": rotation,
        }
        path = OUTPUT_DIR / "sentiment.json"
        with open(path, "w") as f:
            json.dump(out, f, indent=2, default=str)
        log.info(f"Saved → {path}")


if __name__ == "__main__":
    main()
