"""
Research API Routes

Endpoints for reading Phase 3 analysis results (Monte Carlo, Walk-Forward,
Regime Analysis, Phase 3 Summary Scorecard) and strategy parameter definitions.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/research", tags=["research"])

# Paths to Phase 3 result files
RESULTS_DIR = Path("results")
MC_FILE = RESULTS_DIR / "extended_monte_carlo" / "extended_monte_carlo_results.json"
WF_FILE = RESULTS_DIR / "extended_walk_forward" / "extended_walk_forward_results.json"
REGIME_FILE = RESULTS_DIR / "extended_regime_analysis" / "extended_regime_results.json"
SCORECARD_CSV = RESULTS_DIR / "phase3_summary" / "master_scorecard.csv"
ROLLING_FILE = RESULTS_DIR / "extended_rolling_performance" / "extended_rolling_results.json"
ALPHA_FILE = RESULTS_DIR / "factor_alpha" / "factor_alpha.json"
PORTFOLIO_FILE = RESULTS_DIR / "extended_portfolio_analysis" / "extended_portfolio_results.json"
CORR_MATRIX_CSV = RESULTS_DIR / "extended_portfolio_analysis" / "extended_correlation_matrix.csv"


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def _load_scorecard() -> dict:
    """Load master_scorecard.csv and index by strategy key."""
    if not SCORECARD_CSV.exists():
        return {}
    result = {}
    with open(SCORECARD_CSV) as f:
        reader = __import__('csv').DictReader(f)
        for row in reader:
            key = row.get('strategy', '')
            result[key] = {
                'tier': row.get('tier'),
                'sharpe': _safe_float(row.get('sharpe')),
                'cagr': _safe_float(row.get('cagr')),
                'max_drawdown': _safe_float(row.get('mdd')),
                'pct_positive_years': _safe_float(row.get('pct_pos_years')),
                'mc_verdict': row.get('mc_verdict'),
                'wf_verdict': row.get('wf_verdict'),
                'adj_sharpe': _safe_float(row.get('adj_sharpe')),
            }
    return result


def _safe_float(val) -> Optional[float]:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


# Strategy parameter definitions with robustness labels from Phase 2.1 sensitivity analysis
STRATEGY_PARAMS: Dict[str, List[Dict[str, Any]]] = {
    "large_cap_momentum": [
        {"name": "lookback", "label": "Lookback Period (days)", "default": 252, "min": 63, "max": 504, "step": 21, "robustness": "ROBUST", "description": "Trailing return window for momentum ranking (12 months default)"},
        {"name": "skip_recent", "label": "Skip Recent (days)", "default": 21, "min": 0, "max": 63, "step": 5, "robustness": "ROBUST", "description": "Days to skip to avoid short-term reversal effect"},
        {"name": "top_pct", "label": "Top % to Hold", "default": 10, "min": 5, "max": 30, "step": 5, "robustness": "ROBUST", "description": "Percentage of large-cap universe held long"},
        {"name": "large_cap_pct", "label": "Large Cap Filter %", "default": 50, "min": 20, "max": 80, "step": 10, "robustness": "ROBUST", "description": "Percentage of universe considered large cap (by dollar volume)"},
    ],
    "52_week_high_breakout": [
        {"name": "high_window", "label": "High Window (days)", "default": 252, "min": 126, "max": 504, "step": 21, "robustness": "ROBUST", "description": "Lookback window for 52-week high calculation"},
        {"name": "proximity_threshold", "label": "Proximity Threshold", "default": 0.95, "min": 0.80, "max": 0.99, "step": 0.01, "robustness": "ROBUST", "description": "Minimum ratio of price to 52-week high to be included"},
        {"name": "top_pct", "label": "Top % to Hold", "default": 10, "min": 5, "max": 30, "step": 5, "robustness": "ROBUST", "description": "Percentage of qualifying stocks to hold"},
    ],
    "deep_value_all_cap": [
        {"name": "lookback", "label": "Lookback Period (days)", "default": 252, "min": 126, "max": 504, "step": 21, "robustness": "ROBUST", "description": "Period for value proxy calculation (price relative to long-term average)"},
        {"name": "top_pct", "label": "Top % to Hold", "default": 20, "min": 10, "max": 40, "step": 5, "robustness": "ROBUST", "description": "Percentage of cheapest stocks held"},
        {"name": "ma_window", "label": "MA Window (days)", "default": 200, "min": 50, "max": 400, "step": 25, "robustness": "ROBUST", "description": "Moving average window for trend filter"},
    ],
    "high_quality_roic": [
        {"name": "vol_lookback", "label": "Vol Lookback (days)", "default": 252, "min": 63, "max": 504, "step": 21, "robustness": "ROBUST", "description": "Lookback for volatility (quality proxy: low vol = stable earnings)"},
        {"name": "mom_lookback", "label": "Mom Lookback (days)", "default": 252, "min": 126, "max": 504, "step": 21, "robustness": "ROBUST", "description": "Momentum lookback for quality+momentum combo"},
        {"name": "top_pct", "label": "Top % to Hold", "default": 20, "min": 10, "max": 40, "step": 5, "robustness": "ROBUST", "description": "Percentage of highest quality stocks held"},
    ],
    "low_volatility_shield": [
        {"name": "vol_lookback", "label": "Vol Lookback (days)", "default": 63, "min": 21, "max": 252, "step": 21, "robustness": "ROBUST", "description": "Window for volatility estimation (3 months default)"},
        {"name": "bottom_pct", "label": "Bottom % to Hold", "default": 20, "min": 10, "max": 40, "step": 5, "robustness": "ROBUST", "description": "Percentage of lowest-volatility stocks held"},
    ],
    "dividend_aristocrats": [
        {"name": "lookback_months", "label": "Lookback (months)", "default": 36, "min": 12, "max": 60, "step": 6, "robustness": "FRAGILE", "description": "Months of history required for dividend consistency check"},
        {"name": "min_positive_pct", "label": "Min Positive Return %", "default": 0.6, "min": 0.4, "max": 0.8, "step": 0.05, "robustness": "FRAGILE", "description": "Minimum fraction of months with positive returns to qualify"},
        {"name": "top_pct", "label": "Top % to Hold", "default": 20, "min": 10, "max": 40, "step": 5, "robustness": "FRAGILE", "description": "Percentage of qualifying dividend-consistent stocks held"},
    ],
    "moving_average_trend": [
        {"name": "ma_window", "label": "MA Window (days)", "default": 200, "min": 50, "max": 400, "step": 25, "robustness": "ROBUST", "description": "Moving average window for trend signal (200-day is classic)"},
        {"name": "min_stocks", "label": "Min Stocks", "default": 10, "min": 5, "max": 50, "step": 5, "robustness": "ROBUST", "description": "Minimum number of stocks to hold even in downtrend"},
    ],
    "rsi_mean_reversion": [
        {"name": "rsi_period", "label": "RSI Period (days)", "default": 14, "min": 7, "max": 28, "step": 1, "robustness": "ROBUST", "description": "RSI calculation window (14 is classic Wilder period)"},
        {"name": "oversold", "label": "Oversold Threshold", "default": 30, "min": 20, "max": 45, "step": 5, "robustness": "ROBUST", "description": "RSI level below which stock is considered oversold (buy signal)"},
        {"name": "exit_threshold", "label": "Exit Threshold", "default": 50, "min": 40, "max": 65, "step": 5, "robustness": "ROBUST", "description": "RSI level at which to exit long position"},
        {"name": "max_positions", "label": "Max Positions", "default": 20, "min": 5, "max": 50, "step": 5, "robustness": "ROBUST", "description": "Maximum number of simultaneous positions"},
    ],
    "value_momentum_blend": [
        {"name": "mom_lookback", "label": "Momentum Lookback (days)", "default": 252, "min": 126, "max": 504, "step": 21, "robustness": "ROBUST", "description": "Trailing return window for momentum factor"},
        {"name": "value_lookback", "label": "Value Lookback (days)", "default": 252, "min": 126, "max": 504, "step": 21, "robustness": "ROBUST", "description": "Lookback for value proxy calculation"},
        {"name": "mom_weight", "label": "Momentum Weight", "default": 0.5, "min": 0.1, "max": 0.9, "step": 0.1, "robustness": "ROBUST", "description": "Weight given to momentum factor (value weight = 1 - this)"},
        {"name": "top_pct", "label": "Top % to Hold", "default": 20, "min": 10, "max": 40, "step": 5, "robustness": "ROBUST", "description": "Percentage of highest-scored stocks held"},
    ],
    "quality_momentum": [
        {"name": "mom_lookback", "label": "Momentum Lookback (days)", "default": 252, "min": 126, "max": 504, "step": 21, "robustness": "ROBUST", "description": "Trailing return window for momentum factor"},
        {"name": "mom_weight", "label": "Momentum Weight", "default": 0.5, "min": 0.1, "max": 0.9, "step": 0.1, "robustness": "ROBUST", "description": "Weight given to momentum factor (quality weight = 1 - this)"},
        {"name": "top_pct", "label": "Top % to Hold", "default": 20, "min": 10, "max": 40, "step": 5, "robustness": "ROBUST", "description": "Percentage of highest-scored stocks held"},
    ],
    "quality_low_vol": [
        {"name": "vol_lookback", "label": "Vol Lookback (days)", "default": 126, "min": 63, "max": 252, "step": 21, "robustness": "ROBUST", "description": "Volatility lookback for low-vol factor"},
        {"name": "quality_lookback", "label": "Quality Lookback (days)", "default": 252, "min": 126, "max": 504, "step": 21, "robustness": "ROBUST", "description": "Lookback for quality factor (low vol = quality proxy)"},
        {"name": "vol_weight", "label": "Vol Weight", "default": 0.5, "min": 0.1, "max": 0.9, "step": 0.1, "robustness": "ROBUST", "description": "Weight given to low-volatility factor (quality weight = 1 - this)"},
        {"name": "top_pct", "label": "Top % to Hold", "default": 20, "min": 10, "max": 40, "step": 5, "robustness": "ROBUST", "description": "Percentage of highest-scored stocks held"},
    ],
    "composite_factor_score": [
        {"name": "lookback", "label": "Lookback Period (days)", "default": 252, "min": 126, "max": 504, "step": 21, "robustness": "ROBUST", "description": "Shared lookback for all four factors"},
        {"name": "momentum_weight", "label": "Momentum Weight", "default": 0.30, "min": 0.0, "max": 0.6, "step": 0.05, "robustness": "ROBUST", "description": "Weight for momentum factor in composite score"},
        {"name": "value_weight", "label": "Value Weight", "default": 0.20, "min": 0.0, "max": 0.5, "step": 0.05, "robustness": "ROBUST", "description": "Weight for value factor in composite score"},
        {"name": "quality_weight", "label": "Quality Weight", "default": 0.30, "min": 0.0, "max": 0.6, "step": 0.05, "robustness": "ROBUST", "description": "Weight for quality factor in composite score"},
        {"name": "low_vol_weight", "label": "Low-Vol Weight", "default": 0.20, "min": 0.0, "max": 0.5, "step": 0.05, "robustness": "ROBUST", "description": "Weight for low-volatility factor in composite score"},
        {"name": "top_pct", "label": "Top % to Hold", "default": 20, "min": 10, "max": 40, "step": 5, "robustness": "ROBUST", "description": "Percentage of highest-scored stocks held"},
    ],
    "volatility_targeting": [
        {"name": "target_vol", "label": "Target Volatility", "default": 0.10, "min": 0.05, "max": 0.25, "step": 0.01, "robustness": "ROBUST", "description": "Annualized volatility target (0.10 = 10%)"},
        {"name": "vol_lookback", "label": "Vol Lookback (days)", "default": 63, "min": 21, "max": 126, "step": 21, "robustness": "ROBUST", "description": "Window for realised volatility estimation"},
        {"name": "max_leverage", "label": "Max Leverage", "default": 2.0, "min": 1.0, "max": 3.0, "step": 0.25, "robustness": "ROBUST", "description": "Maximum portfolio leverage allowed"},
    ],
    "earnings_surprise_momentum": [
        {"name": "volume_spike_mult", "label": "Volume Spike Multiplier", "default": 3.0, "min": 1.5, "max": 6.0, "step": 0.5, "robustness": "FRAGILE", "description": "Volume must be this multiple above the lookback mean"},
        {"name": "price_move_std", "label": "Price Move (std devs)", "default": 2.0, "min": 1.0, "max": 4.0, "step": 0.5, "robustness": "FRAGILE", "description": "Minimum price move in standard deviations to qualify as event"},
        {"name": "drift_period", "label": "Drift Period (days)", "default": 63, "min": 21, "max": 126, "step": 21, "robustness": "FRAGILE", "description": "Days to hold the position after the earnings event"},
        {"name": "max_positions", "label": "Max Positions", "default": 30, "min": 10, "max": 60, "step": 5, "robustness": "FRAGILE", "description": "Maximum simultaneous positions"},
    ],
}


@router.get("/rolling/{strategy_name}")
async def get_rolling_metrics(strategy_name: str):
    """
    Annual rolling performance (Sharpe, CAGR, MDD) for a strategy vs benchmark.
    Used by the Rolling Metrics tab on the strategy detail page.
    """
    d = _load_json(ROLLING_FILE)
    if not d:
        raise HTTPException(status_code=404, detail="Rolling performance data not available")

    annual = d.get("annual_results", {})
    years = sorted(annual.keys())

    series_sharpe, series_cagr, series_mdd = [], [], []
    for yr in years:
        yr_data = annual.get(yr, {})
        strat = yr_data.get(strategy_name, {})
        bench = yr_data.get("benchmark", {})
        series_sharpe.append({
            "year": int(yr),
            "strategy": strat.get("sharpe"),
            "benchmark": bench.get("sharpe"),
        })
        series_cagr.append({
            "year": int(yr),
            "strategy": strat.get("cagr"),
            "benchmark": bench.get("cagr"),
        })
        series_mdd.append({
            "year": int(yr),
            "strategy": strat.get("max_drawdown"),
            "benchmark": bench.get("max_drawdown"),
        })

    # Rank stability for this strategy
    rank_stab = d.get("rank_stability", {}).get("mean_year_over_year_spearman")

    return {
        "strategy_name": strategy_name,
        "data_period": d.get("data_period"),
        "annual_sharpe": series_sharpe,
        "annual_cagr": series_cagr,
        "annual_mdd": series_mdd,
        "rank_stability": rank_stab,
        "n_years": len(years),
    }


@router.get("/correlation")
async def get_correlation_data():
    """
    Strategy correlation matrix from Phase 3 portfolio analysis.
    Returns the full NxN matrix as strategy list + flat cell list for heatmap.
    """
    if not CORR_MATRIX_CSV.exists():
        raise HTTPException(status_code=404, detail="Correlation matrix CSV not available")

    import csv as _csv
    rows = []
    strategies = []
    with open(CORR_MATRIX_CSV) as f:
        reader = _csv.reader(f)
        header = next(reader)
        strategies = header[1:]  # skip index column
        for row in reader:
            rows.append(row)

    # Build flat cell list for heatmap
    cells = []
    for i, row in enumerate(rows):
        row_label = row[0]
        for j, val in enumerate(row[1:]):
            cells.append({
                "row": row_label,
                "col": strategies[j],
                "value": round(float(val), 3) if val else None,
            })

    # Summary stats from portfolio JSON
    d = _load_json(PORTFOLIO_FILE)
    avg_corr = d.get("avg_inter_strategy_correlation")
    dr = d.get("diversification_ratio_all14")

    return {
        "strategies": strategies,
        "cells": cells,
        "avg_correlation": avg_corr,
        "diversification_ratio": dr,
        "data_period": d.get("data_period"),
    }


@router.get("/scorecard")
async def get_full_scorecard():
    """
    Get Phase 3 tier and key metrics for all 14 strategies in one call.
    Used by the dashboard to show tier badges without N separate API calls.
    """
    return {"scorecard": _load_scorecard()}


@router.get("/alpha/{strategy_name}")
async def get_factor_alpha(strategy_name: str):
    """
    CAPM factor attribution for a strategy.

    Returns beta (market sensitivity), annualized CAPM alpha (excess return
    after adjusting for beta), and R² (how much return is explained by market).
    Also returns L/S (dollar-neutral) portfolio stats.
    """
    data = _load_json(ALPHA_FILE)
    if strategy_name not in data:
        raise HTTPException(status_code=404, detail=f"No alpha data for: {strategy_name}")

    r = data[strategy_name]
    bench = data.get("_benchmark", {})
    return {
        "strategy_name": strategy_name,
        "capm": r.get("capm", {}),
        "longshort": r.get("longshort", {}),
        "longonly": r.get("longonly", {}),
        "benchmark": bench,
    }


@router.get("/sensitivity/{strategy_name}")
async def get_parameter_sensitivity(strategy_name: str):
    """
    Get parameter sensitivity analysis results for a strategy.

    Returns the 2D Sharpe heatmap (two key params) and 1D sweeps for
    all tunable parameters. Used to visualise robustness on the Parameters tab.
    """
    sens_file = RESULTS_DIR / "parameter_sensitivity" / f"{strategy_name}.json"
    if not sens_file.exists():
        raise HTTPException(status_code=404, detail=f"No sensitivity data for: {strategy_name}")

    data = _load_json(sens_file)

    # 1D sweeps: list of {param, values: [{param_value, sharpe_ratio, is_default}]}
    sweep_1d = []
    defaults = data.get("defaults", {})
    for param_name, results in data.get("sweep_1d", {}).items():
        if not isinstance(results, list):
            continue
        sweep_1d.append({
            "param": param_name,
            "values": [
                {
                    "param_value": r["param_value"],
                    "sharpe_ratio": r.get("sharpe_ratio"),
                    "is_default": r["param_value"] == defaults.get(param_name),
                }
                for r in results
            ],
        })

    # 2D heatmap
    h2 = data.get("heatmap_2d", {})
    default_p1 = defaults.get(h2.get("param_1", ""))
    default_p2 = defaults.get(h2.get("param_2", ""))
    heatmap = {
        "param_1": h2.get("param_1"),
        "param_2": h2.get("param_2"),
        "values_1": h2.get("values_1", []),
        "values_2": h2.get("values_2", []),
        "default_1": default_p1,
        "default_2": default_p2,
        "grid": [
            {
                "v1": row[h2.get("param_1", "")],
                "v2": row[h2.get("param_2", "")],
                "sharpe": row.get("sharpe_ratio"),
            }
            for row in h2.get("grid", [])
            if isinstance(row, dict)
        ],
    }

    # Per-param robustness summary
    robustness = data.get("robustness", {})

    return {
        "strategy_name": strategy_name,
        "defaults": defaults,
        "sweep_1d": sweep_1d,
        "heatmap": heatmap,
        "robustness": robustness,
    }


@router.get("/parameters/{strategy_name}")
async def get_strategy_parameters(strategy_name: str):
    """
    Get tunable parameter definitions for a strategy.

    Returns parameter name, default value, min/max range, step size,
    robustness label (ROBUST/FRAGILE from Phase 2.1 sensitivity analysis),
    and human-readable description.
    """
    params = STRATEGY_PARAMS.get(strategy_name)
    if params is None:
        raise HTTPException(status_code=404, detail=f"No parameters found for strategy: {strategy_name}")
    return {"strategy_name": strategy_name, "parameters": params}


@router.get("/{strategy_name}")
async def get_strategy_research(strategy_name: str):
    """
    Get Phase 3 research results for a strategy.

    Returns:
    - Monte Carlo verdict and adjusted Sharpe
    - Walk-forward efficiency and fold results
    - Regime performance breakdown
    - Phase 3 tier classification
    """
    mc_data = _load_json(MC_FILE)
    wf_data = _load_json(WF_FILE)
    regime_data = _load_json(REGIME_FILE)
    scorecard_data = _load_scorecard()

    # Pull strategy-level data
    mc_result = mc_data.get("results", {}).get(strategy_name, {})
    wf_simple = wf_data.get("simple_oos_results", {}).get(strategy_name, {})
    wf_rolling = wf_data.get("rolling_results", {}).get(strategy_name, {})
    regime_strat = regime_data.get("strategies", {}).get(strategy_name, {})


    if not mc_result and not wf_simple:
        raise HTTPException(status_code=404, detail=f"No research data found for: {strategy_name}")

    # Monte Carlo section
    monte_carlo = None
    if mc_result:
        monte_carlo = {
            "sharpe": mc_result.get("sharpe"),
            "adjusted_sharpe": mc_result.get("adjusted_sharpe"),
            "verdict": mc_result.get("verdict"),
            "iid_p_value": mc_result.get("iid_bootstrap", {}).get("p_value"),
            "iid_ci_lower": mc_result.get("iid_bootstrap", {}).get("ci_lower"),
            "iid_ci_upper": mc_result.get("iid_bootstrap", {}).get("ci_upper"),
            "block_p_value": mc_result.get("block_bootstrap", {}).get("p_value"),
            "sign_p_value": mc_result.get("random_sign_test", {}).get("p_value"),
            "percentile_rank": mc_result.get("random_sign_test", {}).get("percentile_rank"),
        }

    # Walk-forward section
    walk_forward = None
    if wf_simple:
        raw_folds = wf_data.get("rolling_folds", [])
        n_folds = len(raw_folds) if isinstance(raw_folds, list) else int(raw_folds or 0)
        # Build fold labels: "IS end → OOS window" from [is_start, is_end, oos_start, oos_end]
        fold_labels = []
        if isinstance(raw_folds, list):
            for fold in raw_folds:
                if isinstance(fold, (list, tuple)) and len(fold) >= 4:
                    fold_labels.append(f"{fold[2][:7]} – {fold[3][:7]}")
        walk_forward = {
            "is_sharpe": wf_simple.get("is_sharpe"),
            "oos_sharpe": wf_simple.get("oos_sharpe"),
            "wfe": wf_simple.get("wfe"),
            "verdict": wf_simple.get("verdict"),
            "avg_oos_sharpe": wf_rolling.get("avg_oos_sharpe"),
            "avg_wfe": wf_rolling.get("avg_wfe"),
            "fold_oos_sharpes": wf_rolling.get("fold_oos_sharpes", []),
            "fold_wfes": wf_rolling.get("fold_wfes", []),
            "n_folds": n_folds,
            "fold_labels": fold_labels,
        }

    # Regime section
    regime = None
    if regime_strat:
        rp = regime_strat.get("regime_performance", {})
        regime = {
            "bull_sharpe": rp.get("Bull", {}).get("sharpe"),
            "bear_sharpe": rp.get("Bear", {}).get("sharpe"),
            "high_vol_sharpe": rp.get("High-Vol", {}).get("sharpe"),
            "sideways_sharpe": rp.get("Sideways", {}).get("sharpe"),
            "best_regime": regime_strat.get("edge", {}).get("best_regime"),
            "worst_regime": regime_strat.get("edge", {}).get("worst_regime"),
            "regime_spread": regime_strat.get("edge", {}).get("regime_spread"),
            "overall_sharpe": regime_strat.get("overall", {}).get("sharpe"),
        }

    # Scorecard / tier
    tier = scorecard_data.get(strategy_name)

    return {
        "strategy_name": strategy_name,
        "monte_carlo": monte_carlo,
        "walk_forward": walk_forward,
        "regime": regime,
        "scorecard": tier,
        "data_period": mc_data.get("data_period") or wf_data.get("data_period"),
        "n_bootstrap": mc_data.get("n_bootstrap"),
    }


# ── Live signals ──────────────────────────────────────────────────────────────

SIGNALS_FILE = RESULTS_DIR / "live_signals" / "current_signals.json"


@router.get("/signals/{strategy_name}")
async def get_live_signals(strategy_name: str):
    """
    Get the latest live strategy holdings generated by scripts/generate_live_signals.py.

    Returns the top holdings (symbol + weight) from the most recent signal run.
    Refresh by running: .venv/bin/python scripts/generate_live_signals.py
    """
    if not SIGNALS_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Live signals not yet generated. Run: .venv/bin/python scripts/generate_live_signals.py",
        )

    data = _load_json(SIGNALS_FILE)
    strat_data = data.get("strategies", {}).get(strategy_name)

    if strat_data is None:
        raise HTTPException(status_code=404, detail=f"No signals found for: {strategy_name}")

    if "error" in strat_data:
        raise HTTPException(
            status_code=422,
            detail=f"Signal generation failed for {strategy_name}: {strat_data['error']}",
        )

    return {
        "strategy_name": strategy_name,
        "generated_at": data.get("generated_at"),
        "signal_date": strat_data.get("signal_date"),
        "n_holdings": strat_data.get("n_holdings"),
        "holdings": strat_data.get("holdings", []),
        "data_source": data.get("data_source", "Yahoo Finance"),
    }


@router.get("/signals")
async def get_all_live_signals():
    """
    Get metadata for all strategies' live signal status.
    Used to show which strategies have current holdings available.
    """
    if not SIGNALS_FILE.exists():
        return {"available": False, "strategies": {}}

    data = _load_json(SIGNALS_FILE)
    strategies = data.get("strategies", {})

    summary = {
        name: {
            "available": "error" not in info,
            "n_holdings": info.get("n_holdings"),
            "signal_date": info.get("signal_date"),
            "error": info.get("error"),
        }
        for name, info in strategies.items()
    }

    return {
        "available": True,
        "generated_at": data.get("generated_at"),
        "signal_date": data.get("signal_date"),
        "n_symbols": data.get("n_symbols"),
        "strategies": summary,
    }
