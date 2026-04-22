"""
Long-Short Walk-Forward Validation
====================================
Tests whether the L/S factor premium is genuinely persistent across time,
or whether it was concentrated in specific market regimes.

Method: expanding IS window + 5-year OOS windows (4 folds, 2005-2024).
        Also: decade analysis and rolling 12-month Sharpe consistency.

Focus strategies: quality_momentum, large_cap_momentum, dividend_aristocrats
                  + their equal-weight combination

Why this matters: the L/S strategy has no "parameters" to fit, so the
walk-forward isn't about preventing overfit — it's about answering:
"Does the cross-sectional factor signal persist into unseen future data?"

Results → results/ls_walkforward/ls_wf_results.json

Run:
    .venv/bin/python scripts/ls_walkforward.py
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
ANNUAL_PERIODS = 12   # monthly
FOCUS          = ["quality_momentum", "large_cap_momentum", "dividend_aristocrats"]

DISPLAY = {
    "quality_momentum":    "Quality Momentum",
    "large_cap_momentum":  "Large Cap Momentum",
    "dividend_aristocrats": "Dividend Aristocrats",
    "equal_weight_combo":  "Equal-Weight Combo (3)",
}


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


def _stats(r: pd.Series, label: str = "") -> dict:
    return {
        "label":       label,
        "sharpe":      _safe(_sharpe(r)),
        "cagr":        _safe(_cagr(r)),
        "max_drawdown": _safe(_mdd(r)),
        "win_rate":    _safe(_win_rate(r)),
        "n_months":    int(r.notna().sum()),
    }


def _equity_curve(r: pd.Series) -> list:
    eq = (1 + r.fillna(0)).cumprod()
    return [{"date": str(d.date()), "value": round(float(v), 6)}
            for d, v in eq.items() if pd.notna(v)]


# ── Load monthly returns ──────────────────────────────────────────────────────

def load_returns() -> pd.DataFrame:
    with open(LS_FILE) as f:
        raw = json.load(f)
    strats = raw["strategies"]
    series = {}
    for name in FOCUS:
        ec = strats[name]["equity_curve"]
        vals = pd.Series(
            [p["value"] for p in ec],
            index=pd.to_datetime([p["date"] for p in ec]),
        )
        series[name] = vals.pct_change().dropna()

    df = pd.DataFrame(series).dropna(how="all")
    df["equal_weight_combo"] = df[FOCUS].mean(axis=1)
    return df


# ── Walk-forward folds (expanding IS, fixed 5yr OOS) ─────────────────────────

FOLDS = [
    ("2000-02", "2004-12", "2005-01", "2009-12", "GFC fold"),
    ("2000-02", "2009-12", "2010-01", "2014-12", "Post-crisis fold"),
    ("2000-02", "2014-12", "2015-01", "2019-12", "Pre-COVID fold"),
    ("2000-02", "2019-12", "2020-01", "2024-12", "COVID/inflation fold"),
]


def run_walkforward(df: pd.DataFrame) -> dict:
    strategies = FOCUS + ["equal_weight_combo"]
    all_folds = []

    log.info("\n── Walk-Forward Folds ─────────────────────────────────────")
    log.info(f"{'Fold':<22} {'Strategy':<25} {'IS SR':>7} {'OOS SR':>8} {'WFE%':>7} {'OOS CAGR':>10}")
    log.info("─" * 82)

    for is_start, is_end, oos_start, oos_end, label in FOLDS:
        fold_result = {"label": label, "is_period": f"{is_start}–{is_end}",
                       "oos_period": f"{oos_start}–{oos_end}", "strategies": {}}

        for name in strategies:
            r = df[name].dropna()
            is_r  = r[(r.index >= is_start)  & (r.index <= is_end)]
            oos_r = r[(r.index >= oos_start) & (r.index <= oos_end)]

            is_sr  = _sharpe(is_r)
            oos_sr = _sharpe(oos_r)
            wfe    = (oos_sr / is_sr * 100) if is_sr != 0 else None

            fold_result["strategies"][name] = {
                "is_sharpe":   _safe(is_sr),
                "oos_sharpe":  _safe(oos_sr),
                "wfe_pct":     _safe(wfe),
                "oos_stats":   _stats(oos_r),
                "oos_equity":  _equity_curve(oos_r),
            }
            log.info(
                f"  {label:<20} {DISPLAY.get(name, name):<25} "
                f"{is_sr:>7.3f} {oos_sr:>8.3f} "
                f"{'N/A':>7}" if wfe is None else
                f"  {label:<20} {DISPLAY.get(name, name):<25} "
                f"{is_sr:>7.3f} {oos_sr:>8.3f} {wfe:>7.0f}% "
                f"{_cagr(oos_r)*100:>9.1f}%"
            )

        all_folds.append(fold_result)

    return all_folds


# ── Decade analysis ───────────────────────────────────────────────────────────

DECADES = [
    ("2000-02", "2004-12", "2000–2004 (dot-com crash + recovery)"),
    ("2005-01", "2009-12", "2005–2009 (GFC)"),
    ("2010-01", "2014-12", "2010–2014 (post-crisis bull)"),
    ("2015-01", "2019-12", "2015–2019 (steady bull)"),
    ("2020-01", "2024-12", "2020–2024 (COVID + inflation + AI)"),
]


def run_decade_analysis(df: pd.DataFrame) -> dict:
    strategies = FOCUS + ["equal_weight_combo"]
    results = []

    log.info("\n── Decade Analysis ────────────────────────────────────────")
    log.info(f"{'Period':<42} {'Strategy':<25} {'Sharpe':>8} {'CAGR':>8}")
    log.info("─" * 87)

    for start, end, label in DECADES:
        period = {"label": label, "period": f"{start}–{end}", "strategies": {}}
        for name in strategies:
            r = df[name]
            sub = r[(r.index >= start) & (r.index <= end)].dropna()
            s = _stats(sub, label)
            period["strategies"][name] = {**s, "equity_curve": _equity_curve(sub)}
            log.info(
                f"  {label:<40} {DISPLAY.get(name, name):<25} "
                f"{(s['sharpe'] or 0):>8.3f} {(s['cagr'] or 0)*100:>7.1f}%"
            )
        results.append(period)

    return results


# ── Rolling 12-month Sharpe ───────────────────────────────────────────────────

def rolling_sharpe(df: pd.DataFrame) -> dict:
    results = {}
    for name in FOCUS + ["equal_weight_combo"]:
        r = df[name].dropna()
        roll = r.rolling(12, min_periods=10).apply(
            lambda x: _sharpe(pd.Series(x)), raw=False
        )
        results[name] = [
            {"date": str(d.date()), "sharpe": _safe(v)}
            for d, v in roll.items() if pd.notna(v)
        ]
    return results


# ── Summary statistics ────────────────────────────────────────────────────────

def summary_stats(folds: list, df: pd.DataFrame) -> dict:
    strategies = FOCUS + ["equal_weight_combo"]
    out = {}

    for name in strategies:
        oos_sharpes = [
            f["strategies"][name]["oos_sharpe"]
            for f in folds
            if f["strategies"][name]["oos_sharpe"] is not None
        ]
        wfes = [
            f["strategies"][name]["wfe_pct"]
            for f in folds
            if f["strategies"][name]["wfe_pct"] is not None
        ]
        n_pos = sum(1 for s in oos_sharpes if s is not None and s > 0)

        # Full-period stats
        full = _stats(df[name].dropna(), "full_period")

        out[name] = {
            "full_period":        full,
            "avg_oos_sharpe":     _safe(np.mean(oos_sharpes)) if oos_sharpes else None,
            "pct_folds_positive": round(n_pos / len(folds) * 100, 1),
            "avg_wfe_pct":        _safe(np.mean(wfes)) if wfes else None,
            "n_folds":            len(folds),
            "verdict":            (
                "STRONG" if (oos_sharpes and np.mean(oos_sharpes) > 0.4 and n_pos >= 3)
                else "CONSISTENT" if (oos_sharpes and np.mean(oos_sharpes) > 0 and n_pos >= 3)
                else "MIXED" if (oos_sharpes and n_pos >= 2)
                else "WEAK"
            ),
        }

    return out


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 65)
    log.info("StrategyHub — L/S Walk-Forward Validation")
    log.info("=" * 65)
    log.info(f"Focus strategies: {FOCUS}")
    log.info(f"Method: expanding IS + 5-year OOS windows (4 folds)")

    df = load_returns()
    log.info(f"Loaded {len(df)} monthly observations "
             f"({df.index[0].date()} → {df.index[-1].date()})")

    folds    = run_walkforward(df)
    decades  = run_decade_analysis(df)
    rolling  = rolling_sharpe(df)
    summary  = summary_stats(folds, df)

    # ── Print summary ──────────────────────────────────────────────────────
    log.info(f"\n{'='*65}")
    log.info("SUMMARY")
    log.info(f"{'Strategy':<28} {'Avg OOS SR':>11} {'% Pos Folds':>13} {'Avg WFE':>9} {'Verdict':>12}")
    log.info("─" * 77)
    for name in FOCUS + ["equal_weight_combo"]:
        s = summary[name]
        log.info(
            f"  {DISPLAY.get(name, name):<26} "
            f"{(s['avg_oos_sharpe'] or 0):>11.3f} "
            f"{s['pct_folds_positive']:>12.0f}% "
            f"{(s['avg_wfe_pct'] or 0):>8.0f}% "
            f"{s['verdict']:>12}"
        )

    # ── Save ──────────────────────────────────────────────────────────────
    output = {
        "generated_at":   pd.Timestamp.now().isoformat(),
        "method":         "Expanding IS window + 5-year OOS folds",
        "focus_strategies": FOCUS,
        "n_folds":        len(folds),
        "data_period":    f"{df.index[0].date()} – {df.index[-1].date()}",
        "summary":        summary,
        "folds":          folds,
        "decade_analysis": decades,
        "rolling_12m_sharpe": rolling,
    }

    out_path = OUTPUT_DIR / "ls_wf_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    log.info(f"\nSaved → {out_path}")


if __name__ == "__main__":
    main()
