"""
Factor Rotation Model

Builds a regime-adaptive strategy rotation model showing:
1. Which strategies work in each market regime (Bull/Bear/High-Vol/Sideways)
2. Annual leadership rotation (who led each calendar year 2000-2024)
3. Current regime detection from live SPY data
4. Recommended strategy weights for current regime
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, date

import numpy as np
import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
REGIME_FILE   = ROOT / "results/extended_regime_analysis/extended_regime_results.json"
ROLLING_FILE  = ROOT / "results/extended_rolling_performance/extended_rolling_results.json"
WF_ALL_FILE   = ROOT / "results/ls_walkforward/ls_wf_all_results.json"
OUT_DIR       = ROOT / "results/factor_rotation"
OUT_DIR.mkdir(exist_ok=True)

DISPLAY = {
    "large_cap_momentum":         "Large Cap Momentum",
    "52_week_high_breakout":      "52-Week High Breakout",
    "deep_value_all_cap":         "Deep Value All-Cap",
    "high_quality_roic":          "High Quality ROIC",
    "low_volatility_shield":      "Low Volatility Shield",
    "dividend_aristocrats":       "Dividend Aristocrats",
    "moving_average_trend":       "MA Trend",
    "rsi_mean_reversion":         "RSI Mean Reversion",
    "value_momentum_blend":       "Value+Momentum",
    "quality_momentum":           "Quality+Momentum",
    "quality_low_vol":            "Quality+Low Vol",
    "composite_factor_score":     "Composite Factor",
    "volatility_targeting":       "Volatility Targeting",
    "earnings_surprise_momentum": "Earnings Surprise",
}

STRATEGY_ORDER = list(DISPLAY.keys())
REGIMES = ["Bull", "Bear", "High-Vol", "Sideways"]

def safe_float(v, default=None):
    try:
        f = float(v)
        return None if np.isnan(f) or np.isinf(f) else f
    except (TypeError, ValueError):
        return default


# ── 1. Load data ───────────────────────────────────────────────────────────────

regime_data  = json.loads(REGIME_FILE.read_text())
rolling_data = json.loads(ROLLING_FILE.read_text())
wf_data      = json.loads(WF_ALL_FILE.read_text())

strategies_regime = regime_data["strategies"]
annual_results    = rolling_data["annual_results"]     # year → {strategy → {sharpe, cagr, ...}}
regime_summary    = regime_data["regime_summary"]      # Bull/Bear/... → {n_days, pct, ...}


# ── 2. Regime Sharpe matrix ────────────────────────────────────────────────────

regime_matrix: dict[str, dict[str, float | None]] = {}
for name in STRATEGY_ORDER:
    if name not in strategies_regime:
        continue
    rp = strategies_regime[name]["regime_performance"]
    regime_matrix[name] = {r: safe_float(rp.get(r, {}).get("sharpe")) for r in REGIMES}

# Rank within each regime (1 = best)
regime_ranks: dict[str, dict[str, int]] = {name: {} for name in STRATEGY_ORDER}
for regime in REGIMES:
    scores = [(n, regime_matrix[n][regime]) for n in STRATEGY_ORDER if regime_matrix[n][regime] is not None]
    scores.sort(key=lambda x: x[1], reverse=True)
    for rank, (name, _) in enumerate(scores, 1):
        regime_ranks[name][regime] = rank


# ── 3. Annual leadership calendar ─────────────────────────────────────────────

annual_leaders: list[dict] = []

for year_str in sorted(annual_results.keys()):
    yr_data = annual_results[year_str]
    # Benchmark stats
    bench = yr_data.get("benchmark", {})
    bench_sr = safe_float(bench.get("sharpe"))
    bench_ret = safe_float(bench.get("cagr"))

    # Strategy scores
    scores = {}
    for name in STRATEGY_ORDER:
        if name in yr_data:
            s = safe_float(yr_data[name].get("sharpe"))
            if s is not None:
                scores[name] = s

    if not scores:
        continue

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top3 = ranked[:3]
    bottom1 = ranked[-1]

    annual_leaders.append({
        "year": int(year_str),
        "leader":       top3[0][0] if len(top3) > 0 else None,
        "leader_sr":    top3[0][1] if len(top3) > 0 else None,
        "second":       top3[1][0] if len(top3) > 1 else None,
        "second_sr":    top3[1][1] if len(top3) > 1 else None,
        "third":        top3[2][0] if len(top3) > 2 else None,
        "third_sr":     top3[2][1] if len(top3) > 2 else None,
        "laggard":      bottom1[0],
        "laggard_sr":   bottom1[1],
        "benchmark_sr": bench_sr,
        "all_sharpes":  {n: s for n, s in scores.items()},
    })


# ── 4. Current regime detection via SPY ───────────────────────────────────────

current_regime   = "Unknown"
regime_metrics: dict = {}
data_source      = "historical_only"

try:
    import yfinance as yf
    spy = yf.download("SPY", period="6mo", progress=False, auto_adjust=True)
    if not spy.empty and len(spy) >= 70:
        close = spy["Close"].squeeze()
        TREND_WIN = 63
        VOL_WIN   = 63
        ret = close.pct_change().dropna()

        trend_ret = (close.iloc[-1] / close.iloc[-TREND_WIN] - 1)   # 63-day total return
        vol_63    = ret.iloc[-VOL_WIN:].std() * np.sqrt(252)

        bull_thresh  = 0.05
        bear_thresh  = -0.05
        hivol_thresh = 0.20

        if vol_63 >= hivol_thresh:
            current_regime = "High-Vol"
        elif trend_ret >= bull_thresh:
            current_regime = "Bull"
        elif trend_ret <= bear_thresh:
            current_regime = "Bear"
        else:
            current_regime = "Sideways"

        regime_metrics = {
            "trend_63d":       round(float(trend_ret), 4),
            "vol_63d_ann":     round(float(vol_63), 4),
            "spy_price":       round(float(close.iloc[-1]), 2),
            "as_of":           str(close.index[-1].date()),
        }
        data_source = "live_spy"
        print(f"Live SPY: trend={trend_ret:.2%}, vol={vol_63:.2%} → {current_regime}")
except Exception as e:
    print(f"Could not fetch live SPY ({e}) — regime set to Unknown")


# ── 5. Recommended weights for current regime ─────────────────────────────────

def compute_weights(regime: str, top_n: int = 14) -> dict[str, float]:
    """Proportional weights based on positive Sharpe within the regime."""
    if regime not in REGIMES:
        return {}
    sharpes = [(n, regime_matrix[n][regime]) for n in STRATEGY_ORDER
               if regime_matrix[n].get(regime) is not None]
    # Shift so all values ≥ 0 (preserves relative ordering)
    min_s = min(s for _, s in sharpes)
    shifted = [(n, s - min_s) for n, s in sharpes]
    total   = sum(s for _, s in shifted)
    if total == 0:
        return {n: round(100 / len(STRATEGY_ORDER), 1) for n, _ in sharpes}
    weights = {n: round((s / total) * 100, 1) for n, s in shifted}
    return weights

recommended_weights = compute_weights(current_regime)

# Also pre-compute weights for all regimes (useful for "what-if" on frontend)
all_regime_weights: dict[str, dict[str, float]] = {r: compute_weights(r) for r in REGIMES}


# ── 6. Strategy-level summary (for frontend cards) ────────────────────────────

strategy_summaries = []
for name in STRATEGY_ORDER:
    if name not in regime_matrix:
        continue
    rm = regime_matrix[name]
    rr = regime_ranks.get(name, {})
    wf  = wf_data.get("strategies", {}).get(name, {})
    strategy_summaries.append({
        "name":         name,
        "display_name": DISPLAY[name],
        "regime_sharpes": rm,
        "regime_ranks":   rr,
        "best_regime":   max(rm, key=lambda r: rm[r] or -99),
        "worst_regime":  min(rm, key=lambda r: rm[r] or 99),
        "wf_verdict":    wf.get("verdict"),
        "recommended_weight_pct": recommended_weights.get(name, 0),
    })

strategy_summaries.sort(key=lambda x: x["recommended_weight_pct"], reverse=True)


# ── 7. Rotation insight sentences ─────────────────────────────────────────────

def make_insight(regime: str) -> str:
    ranked = sorted(
        [(n, regime_matrix[n][regime]) for n in STRATEGY_ORDER if regime_matrix[n].get(regime) is not None],
        key=lambda x: x[1], reverse=True
    )
    top = [DISPLAY[n] for n, _ in ranked[:3]]
    worst = [DISPLAY[n] for n, _ in ranked[-2:]]
    return f"In {regime} markets: top strategies are {', '.join(top)}; avoid {', '.join(worst)}."

insights = {r: make_insight(r) for r in REGIMES}


# ── 8. Assemble output ────────────────────────────────────────────────────────

output = {
    "generated_at":        str(date.today()),
    "data_source":         data_source,
    "current_regime":      current_regime,
    "current_regime_metrics": regime_metrics,
    "regime_descriptions": {
        "Bull":     "Strong upward trend (SPY +5% in 63 days, vol < 20%)",
        "Bear":     "Significant downtrend (SPY −5% in 63 days, vol < 20%)",
        "High-Vol": "Elevated volatility (ann. vol ≥ 20%) regardless of direction",
        "Sideways": "No clear trend (SPY between −5% and +5% in 63 days, vol < 20%)",
    },
    "regime_stats": {
        r: {
            "pct_of_time": regime_summary[r]["pct"],
            "ann_market_return": regime_summary[r]["ann_market_return"],
            "ann_market_vol":    regime_summary[r]["ann_market_vol"],
        }
        for r in REGIMES if r in regime_summary
    },
    "regime_matrix":            regime_matrix,
    "regime_ranks":             regime_ranks,
    "all_regime_weights":       all_regime_weights,
    "recommended_weights":      recommended_weights,
    "strategy_summaries":       strategy_summaries,
    "annual_leaders":           annual_leaders,
    "insights":                 insights,
}

OUT_FILE = OUT_DIR / "factor_rotation.json"
OUT_FILE.write_text(json.dumps(output, indent=2, default=str))
print(f"\nSaved → {OUT_FILE}")
print(f"Current regime: {current_regime}")
print(f"Top 5 recommended strategies:")
for s in strategy_summaries[:5]:
    print(f"  {s['display_name']:<30} {s['recommended_weight_pct']:.1f}%  (best: {s['best_regime']})")
