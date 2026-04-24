"""
Long-Short Walk-Forward Validation — All 14 Strategies
=======================================================
Extends ls_walkforward.py to cover all 14 strategies, not just the 3 focus ones.
Same methodology: expanding IS + 5-year OOS windows (4 folds).

Use case: per-strategy WFE badge in the Research tab of each strategy detail page.

Results → results/ls_walkforward/ls_wf_all_results.json

Run:
    .venv/bin/python scripts/ls_walkforward_all.py
"""

import sys
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

LS_FILE    = ROOT / "results" / "longshort" / "longshort_results.json"
OUTPUT_DIR = ROOT / "results" / "ls_walkforward"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RF_ANNUAL      = 0.02
ANNUAL_PERIODS = 12

ALL_STRATEGIES = [
    "large_cap_momentum",
    "52_week_high_breakout",
    "deep_value_all_cap",
    "high_quality_roic",
    "low_volatility_shield",
    "dividend_aristocrats",
    "moving_average_trend",
    "rsi_mean_reversion",
    "value_momentum_blend",
    "quality_momentum",
    "quality_low_vol",
    "composite_factor_score",
    "volatility_targeting",
    "earnings_surprise_momentum",
]

DISPLAY = {
    "large_cap_momentum":         "Large Cap Momentum",
    "52_week_high_breakout":      "52-Week High Breakout",
    "deep_value_all_cap":         "Deep Value All-Cap",
    "high_quality_roic":          "High Quality ROIC",
    "low_volatility_shield":      "Low Volatility Shield",
    "dividend_aristocrats":       "Dividend Aristocrats",
    "moving_average_trend":       "MA Trend",
    "rsi_mean_reversion":         "RSI Mean Reversion",
    "value_momentum_blend":       "Value + Momentum",
    "quality_momentum":           "Quality Momentum",
    "quality_low_vol":            "Quality + Low Vol",
    "composite_factor_score":     "Composite Factor",
    "volatility_targeting":       "Volatility Targeting",
    "earnings_surprise_momentum": "Earnings Surprise",
}

FOLDS = [
    ("2000-02", "2004-12", "2005-01", "2009-12", "GFC fold"),
    ("2000-02", "2009-12", "2010-01", "2014-12", "Post-crisis fold"),
    ("2000-02", "2014-12", "2015-01", "2019-12", "Pre-COVID fold"),
    ("2000-02", "2019-12", "2020-01", "2024-12", "COVID/inflation fold"),
]


# ── Stat helpers ─────────────────────────────────────────────────────────────

def _safe(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return round(float(v), 4)


def _sharpe(r: pd.Series) -> float:
    r = r.dropna()
    if len(r) < 6 or r.std() == 0:
        return 0.0
    excess = r - RF_ANNUAL / ANNUAL_PERIODS
    return float(excess.mean() / r.std() * np.sqrt(ANNUAL_PERIODS))


def _cagr(r: pd.Series) -> float:
    r = r.dropna()
    if len(r) < 2:
        return 0.0
    total = (1 + r).prod() - 1
    if total <= -1:
        return -1.0
    return float((1 + total) ** (ANNUAL_PERIODS / len(r)) - 1)


def _mdd(r: pd.Series) -> float:
    eq = (1 + r.fillna(0)).cumprod()
    return float((eq / eq.expanding().max() - 1).min())


def _win_rate(r: pd.Series) -> float:
    r = r.dropna()
    nonzero = (r != 0).sum()
    return float((r > 0).sum() / nonzero) if nonzero > 0 else 0.0


def _stats(r: pd.Series) -> dict:
    return {
        "sharpe":       _safe(_sharpe(r)),
        "cagr":         _safe(_cagr(r)),
        "max_drawdown": _safe(_mdd(r)),
        "win_rate":     _safe(_win_rate(r)),
        "n_months":     int(r.notna().sum()),
    }


# ── Load ──────────────────────────────────────────────────────────────────────

def load_returns() -> pd.DataFrame:
    with open(LS_FILE) as f:
        raw = json.load(f)
    strats = raw["strategies"]
    series = {}
    available = []
    for name in ALL_STRATEGIES:
        if name not in strats:
            log.warning(f"  {name} not in longshort_results.json — skipping")
            continue
        ec = strats[name]["equity_curve"]
        vals = pd.Series(
            [p["value"] for p in ec],
            index=pd.to_datetime([p["date"] for p in ec]),
        )
        series[name] = vals.pct_change().dropna()
        available.append(name)

    df = pd.DataFrame(series).dropna(how="all")
    log.info(f"Loaded {len(df)} monthly obs for {len(available)} strategies")
    return df, available


# ── Walk-forward ──────────────────────────────────────────────────────────────

def run_walkforward(df: pd.DataFrame, strategies: list) -> dict:
    results = {}

    log.info("\n── Walk-Forward (All Strategies) ──────────────────────────────")
    log.info(f"{'Strategy':<28} {'Avg OOS SR':>11} {'% Pos':>7} {'Avg WFE':>9} {'Verdict':>12}")
    log.info("─" * 73)

    for name in strategies:
        r = df[name].dropna()
        folds_out = []
        oos_sharpes = []
        wfes = []

        for is_start, is_end, oos_start, oos_end, label in FOLDS:
            is_r  = r[(r.index >= is_start)  & (r.index <= is_end)]
            oos_r = r[(r.index >= oos_start) & (r.index <= oos_end)]
            is_sr  = _sharpe(is_r)
            oos_sr = _sharpe(oos_r)
            wfe    = (oos_sr / is_sr * 100) if is_sr != 0 else None

            folds_out.append({
                "label":      label,
                "is_period":  f"{is_start}–{is_end}",
                "oos_period": f"{oos_start}–{oos_end}",
                "is_sharpe":  _safe(is_sr),
                "oos_sharpe": _safe(oos_sr),
                "wfe_pct":    _safe(wfe),
                "oos_cagr":   _safe(_cagr(oos_r)),
                "oos_n_months": int(oos_r.notna().sum()),
            })
            if oos_sr is not None:
                oos_sharpes.append(oos_sr)
            if wfe is not None:
                wfes.append(wfe)

        n_pos = sum(1 for s in oos_sharpes if s > 0)
        avg_oos = float(np.mean(oos_sharpes)) if oos_sharpes else 0.0
        avg_wfe = float(np.mean(wfes)) if wfes else 0.0

        verdict = (
            "STRONG"     if avg_oos > 0.4 and n_pos >= 3
            else "CONSISTENT" if avg_oos > 0 and n_pos >= 3
            else "MIXED"      if n_pos >= 2
            else "WEAK"
        )

        results[name] = {
            "display_name":      DISPLAY.get(name, name),
            "avg_oos_sharpe":    _safe(avg_oos),
            "pct_folds_positive": round(n_pos / len(FOLDS) * 100, 1),
            "avg_wfe_pct":       _safe(avg_wfe),
            "n_folds":           len(FOLDS),
            "verdict":           verdict,
            "full_period":       _stats(r),
            "folds":             folds_out,
        }

        log.info(
            f"  {DISPLAY.get(name, name):<26} "
            f"{avg_oos:>11.3f} "
            f"{n_pos}/{len(FOLDS):>5} "
            f"{avg_wfe:>8.0f}% "
            f"{verdict:>12}"
        )

    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 65)
    log.info("StrategyHub — L/S Walk-Forward Validation (All 14 Strategies)")
    log.info("=" * 65)

    df, available = load_returns()

    results = run_walkforward(df, available)

    # Build sorted ranking
    ranked = sorted(
        results.items(),
        key=lambda x: x[1]["avg_oos_sharpe"] or -99,
        reverse=True,
    )

    output = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "method":       "Expanding IS window + 5-year OOS folds (4 folds)",
        "n_strategies": len(results),
        "data_period":  f"{df.index[0].date()} – {df.index[-1].date()}",
        "strategies":   results,
        "ranked_by_avg_oos_sharpe": [k for k, _ in ranked],
    }

    out_path = OUTPUT_DIR / "ls_wf_all_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    log.info(f"\nSaved → {out_path}")

    # Quick verdict summary
    verdicts = {}
    for name, s in results.items():
        v = s["verdict"]
        verdicts.setdefault(v, []).append(DISPLAY.get(name, name))
    for v, names in sorted(verdicts.items()):
        log.info(f"  {v}: {', '.join(names)}")


if __name__ == "__main__":
    main()
