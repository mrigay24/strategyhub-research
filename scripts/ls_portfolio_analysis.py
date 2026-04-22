"""
Long-Short Factor Portfolio Analysis
======================================
Answers: which COMBINATION of L/S strategies maximises risk-adjusted return?

Key insight:
  Long-only avg correlation = 0.951  (combining adds almost nothing)
  L/S avg correlation       = 0.139  (combining is massively diversifying)

Analysis:
  1. Correlation matrix of all 14 L/S monthly return series
  2. Restrict universe to positive-Sharpe strategies (7 of 14)
  3. Equal-weight combination
  4. Risk-parity combination
  5. Max-Sharpe mean-variance combination
  6. Best 2- and 3-strategy pairs (exhaustive search)
  7. Regime breakdown: does the portfolio hold up in 2008 / 2020 / dot-com?
  8. Rolling 3-year Sharpe of best portfolio

Results saved → results/ls_portfolio/ls_portfolio_results.json

Run:
    .venv/bin/python scripts/ls_portfolio_analysis.py
"""

import sys
import json
import logging
from pathlib import Path
from itertools import combinations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

LS_FILE     = ROOT / "results" / "longshort" / "longshort_results.json"
OUTPUT_DIR  = ROOT / "results" / "ls_portfolio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RF_ANNUAL   = 0.02
ANNUAL_PERIODS = 12   # monthly data


# ── Helpers ─────────────────────────────────────────────────────────────────

def _safe(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return round(float(v), 4)


def _sharpe(returns: pd.Series) -> float:
    r = returns.dropna()
    if len(r) < 12 or r.std() == 0:
        return 0.0
    excess = r - RF_ANNUAL / ANNUAL_PERIODS
    return float(excess.mean() / r.std() * np.sqrt(ANNUAL_PERIODS))


def _cagr(returns: pd.Series) -> float:
    r = returns.dropna()
    if len(r) < 2:
        return 0.0
    total = (1 + r).prod() - 1
    if total <= -1:
        return -1.0
    return float((1 + total) ** (ANNUAL_PERIODS / len(r)) - 1)


def _mdd(returns: pd.Series) -> float:
    eq = (1 + returns.fillna(0)).cumprod()
    peak = eq.expanding().max()
    dd = (eq / peak - 1)
    return float(dd.min())


def _vol(returns: pd.Series) -> float:
    return float(returns.dropna().std() * np.sqrt(ANNUAL_PERIODS))


def _metrics(returns: pd.Series, label: str = "") -> dict:
    return {
        "label":        label,
        "sharpe":       _safe(_sharpe(returns)),
        "cagr":         _safe(_cagr(returns)),
        "max_drawdown": _safe(_mdd(returns)),
        "volatility":   _safe(_vol(returns)),
        "win_rate":     _safe(float((returns > 0).sum() / max((returns != 0).sum(), 1))),
        "n_months":     int(returns.notna().sum()),
    }


def _portfolio_return(weights: np.ndarray, ret_df: pd.DataFrame) -> pd.Series:
    """Weighted sum of strategy return columns."""
    w = pd.Series(weights, index=ret_df.columns)
    return (ret_df * w).sum(axis=1)


# ── Max-Sharpe optimisation ──────────────────────────────────────────────────

def _max_sharpe_weights(ret_df: pd.DataFrame) -> np.ndarray:
    """
    Long-only mean-variance max-Sharpe portfolio via scipy.
    Weights ≥ 0, sum = 1.
    """
    n = ret_df.shape[1]
    mu = ret_df.mean().values * ANNUAL_PERIODS
    sigma = ret_df.cov().values * ANNUAL_PERIODS

    def neg_sharpe(w):
        port_ret = float(w @ mu)
        port_vol = float(np.sqrt(w @ sigma @ w))
        if port_vol < 1e-10:
            return 0.0
        return -(port_ret - RF_ANNUAL) / port_vol

    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    bounds = [(0.0, 1.0)] * n
    result = minimize(
        neg_sharpe,
        x0=np.ones(n) / n,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-10},
    )
    w = result.x
    w = np.clip(w, 0, 1)
    w /= w.sum()
    return w


# ── Risk-parity weights ──────────────────────────────────────────────────────

def _risk_parity_weights(ret_df: pd.DataFrame) -> np.ndarray:
    """Equal risk contribution (vol-weighted)."""
    vols = ret_df.std().values
    if (vols == 0).any():
        return np.ones(len(vols)) / len(vols)
    inv_vol = 1.0 / vols
    w = inv_vol / inv_vol.sum()
    return w


# ── Regime labels ────────────────────────────────────────────────────────────

BEAR_PERIODS = [
    ("2000-03", "2002-09"),   # Dot-com bust
    ("2007-10", "2009-02"),   # GFC
    ("2020-02", "2020-03"),   # COVID crash
    ("2022-01", "2022-09"),   # Rate-hike bear
]

BULL_PERIODS = [
    ("2003-03", "2007-09"),
    ("2009-07", "2019-12"),
    ("2020-05", "2021-12"),
    ("2023-01", "2024-12"),
]


def _regime_returns(returns: pd.Series, periods: list) -> pd.Series:
    """Concat monthly returns within the specified date ranges."""
    masks = []
    idx = returns.index
    for start, end in periods:
        masks.append((idx >= start) & (idx <= end))
    mask = np.zeros(len(idx), dtype=bool)
    for m in masks:
        mask |= m
    return returns[mask]


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 65)
    log.info("StrategyHub — L/S Factor Portfolio Analysis")
    log.info("=" * 65)

    # ── Load monthly return series ────────────────────────────────────────
    with open(LS_FILE) as f:
        raw = json.load(f)

    strats = raw["strategies"]
    ret_series = {}
    for name, s in strats.items():
        ec = s.get("equity_curve", [])
        if len(ec) < 24:
            continue
        vals = pd.Series(
            [p["value"] for p in ec],
            index=pd.to_datetime([p["date"] for p in ec]),
            name=name,
        )
        ret_series[name] = vals.pct_change().dropna()

    all_ret = pd.DataFrame(ret_series).dropna(how="all")
    log.info(f"Loaded {len(ret_series)} strategies, {len(all_ret)} monthly observations")
    log.info(f"Period: {all_ret.index[0].date()} → {all_ret.index[-1].date()}")

    # ── Correlation matrix ────────────────────────────────────────────────
    corr_matrix = all_ret.corr()
    upper_tri = corr_matrix.where(
        np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
    )
    avg_corr_ls   = float(upper_tri.stack().mean())
    max_corr_ls   = float(upper_tri.stack().max())
    min_corr_ls   = float(upper_tri.stack().min())
    log.info(f"\nL/S correlation: avg={avg_corr_ls:.3f}  max={max_corr_ls:.3f}  min={min_corr_ls:.3f}")
    log.info("(Long-only avg correlation was 0.951 — L/S is 7× more diversifiable)")

    # ── Restrict to positive-Sharpe strategies ────────────────────────────
    individual = {}
    for name, r in ret_series.items():
        sr = _sharpe(r)
        individual[name] = {"sharpe": sr, "returns": r}

    positive = {n: v for n, v in individual.items() if v["sharpe"] > 0}
    pos_names = sorted(positive.keys(), key=lambda n: positive[n]["sharpe"], reverse=True)
    log.info(f"\nPositive-Sharpe strategies ({len(pos_names)}): {pos_names}")

    pos_ret = all_ret[pos_names].dropna(how="all")

    # ── Portfolio constructions ───────────────────────────────────────────
    portfolios = {}

    # 1. Equal-weight (positive Sharpe only)
    ew_w = np.ones(len(pos_names)) / len(pos_names)
    ew_ret = _portfolio_return(ew_w, pos_ret)
    portfolios["equal_weight_pos"] = {
        **_metrics(ew_ret, "Equal-Weight (7 positive-SR)"),
        "weights": dict(zip(pos_names, [round(float(w), 4) for w in ew_w])),
    }

    # 2. Risk-parity (positive Sharpe only)
    rp_w = _risk_parity_weights(pos_ret.fillna(0))
    rp_ret = _portfolio_return(rp_w, pos_ret)
    portfolios["risk_parity_pos"] = {
        **_metrics(rp_ret, "Risk-Parity (7 positive-SR)"),
        "weights": dict(zip(pos_names, [round(float(w), 4) for w in rp_w])),
    }

    # 3. Max-Sharpe MVO (positive Sharpe only)
    ms_w = _max_sharpe_weights(pos_ret.fillna(0))
    ms_ret = _portfolio_return(ms_w, pos_ret)
    portfolios["max_sharpe_pos"] = {
        **_metrics(ms_ret, "Max-Sharpe MVO (7 positive-SR)"),
        "weights": dict(zip(pos_names, [round(float(w), 4) for w in ms_w])),
    }

    log.info("\nPortfolio Sharpes:")
    for k, v in portfolios.items():
        log.info(f"  {v['label']:<40} SR={v['sharpe']:.3f}  CAGR={v['cagr']*100:.1f}%  MDD={v['max_drawdown']*100:.1f}%")

    # ── Best 2- and 3-strategy pairs ─────────────────────────────────────
    log.info("\nSearching best pairs / triplets...")
    pair_results = []
    for n in range(2, 4):
        for combo in combinations(pos_names, n):
            sub = pos_ret[list(combo)].dropna(how="all")
            w = np.ones(len(combo)) / len(combo)
            pr = _portfolio_return(w, sub)
            sr = _sharpe(pr)
            # pairwise avg correlation
            if len(combo) > 1:
                c = sub.corr()
                avg_c = float(c.where(np.triu(np.ones(c.shape), k=1).astype(bool)).stack().mean())
            else:
                avg_c = 1.0
            pair_results.append({
                "n": n,
                "strategies": list(combo),
                "sharpe": round(sr, 4),
                "cagr": _safe(_cagr(pr)),
                "max_drawdown": _safe(_mdd(pr)),
                "avg_correlation": round(avg_c, 3),
            })

    pair_results.sort(key=lambda x: x["sharpe"], reverse=True)
    best_pair    = next(r for r in pair_results if r["n"] == 2)
    best_triplet = next(r for r in pair_results if r["n"] == 3)

    log.info(f"  Best pair:    {best_pair['strategies']}  SR={best_pair['sharpe']:.3f}  avg_corr={best_pair['avg_correlation']:.3f}")
    log.info(f"  Best triplet: {best_triplet['strategies']}  SR={best_triplet['sharpe']:.3f}  avg_corr={best_triplet['avg_correlation']:.3f}")

    # ── Regime analysis ───────────────────────────────────────────────────
    # Use the max-Sharpe portfolio as the reference
    log.info("\nRegime analysis (Max-Sharpe portfolio):")
    regime_metrics = {}
    for regime, periods in [("bull", BULL_PERIODS), ("bear", BEAR_PERIODS)]:
        sub = _regime_returns(ms_ret, periods)
        m = _metrics(sub, regime)
        regime_metrics[regime] = m
        log.info(f"  {regime:<6} SR={m['sharpe']:.3f}  CAGR={m['cagr']*100:.1f}%  MDD={m['max_drawdown']*100:.1f}%  ({m['n_months']} months)")

    # Specific crisis periods
    crises = {
        "dot_com_bust":   ("2000-03", "2002-09"),
        "gfc":            ("2007-10", "2009-02"),
        "covid_crash":    ("2020-02", "2020-03"),
        "rate_hike_2022": ("2022-01", "2022-09"),
    }
    crisis_metrics = {}
    for label, (start, end) in crises.items():
        sub = ms_ret[(ms_ret.index >= start) & (ms_ret.index <= end)]
        if len(sub) < 2:
            continue
        m = _metrics(sub, label)
        crisis_metrics[label] = m
        log.info(f"  {label:<18} SR={m['sharpe']:.3f}  CAGR={m['cagr']*100:.1f}%  ({m['n_months']} months)")

    # ── Rolling 3-year Sharpe of max-Sharpe portfolio ─────────────────────
    rolling_sharpe = ms_ret.rolling(36, min_periods=24).apply(
        lambda r: _sharpe(pd.Series(r)), raw=False
    )
    rolling_monthly = [
        {"date": str(d.date()), "sharpe": _safe(v)}
        for d, v in rolling_sharpe.items()
        if pd.notna(v)
    ]

    # ── Build equity curves for each portfolio ────────────────────────────
    def _equity_curve(returns: pd.Series) -> list:
        eq = (1 + returns.fillna(0)).cumprod()
        monthly = eq.resample("M").last()
        return [{"date": str(d.date()), "value": round(float(v), 6)}
                for d, v in monthly.items() if pd.notna(v)]

    # ── Correlation matrix serialization ─────────────────────────────────
    corr_list = []
    for row in corr_matrix.index:
        for col in corr_matrix.columns:
            corr_list.append({
                "row": row,
                "col": col,
                "correlation": round(float(corr_matrix.loc[row, col]), 3),
            })

    # ── Summary ───────────────────────────────────────────────────────────
    log.info(f"\n{'='*65}")
    log.info("Summary:")
    log.info(f"  Avg L/S pairwise corr:  {avg_corr_ls:.3f}  (vs 0.951 long-only)")
    log.info(f"  Best individual SR:     {max(v['sharpe'] for v in individual.values()):.3f}")
    log.info(f"  Equal-weight combo SR:  {portfolios['equal_weight_pos']['sharpe']:.3f}")
    log.info(f"  Max-Sharpe combo SR:    {portfolios['max_sharpe_pos']['sharpe']:.3f}")
    log.info(f"  Best pair SR:           {best_pair['sharpe']:.3f}  {best_pair['strategies']}")
    log.info(f"  Best triplet SR:        {best_triplet['sharpe']:.3f}  {best_triplet['strategies']}")

    # ── Save ──────────────────────────────────────────────────────────────
    output = {
        "generated_at":       pd.Timestamp.now().isoformat(),
        "data_period":        f"{all_ret.index[0].date()} – {all_ret.index[-1].date()}",
        "n_strategies":       len(ret_series),
        "correlation_stats": {
            "avg":                round(avg_corr_ls, 4),
            "max":                round(max_corr_ls, 4),
            "min":                round(min_corr_ls, 4),
            "longonly_avg":       0.951,
            "improvement_factor": round(0.951 / avg_corr_ls, 1),
        },
        "individual_strategies": {
            n: {
                "sharpe":       _safe(v["sharpe"]),
                "cagr":         _safe(_cagr(v["returns"])),
                "max_drawdown": _safe(_mdd(v["returns"])),
                "equity_curve": _equity_curve(v["returns"]),
            }
            for n, v in individual.items()
        },
        "portfolios": {
            k: {**v, "equity_curve": _equity_curve(
                _portfolio_return(
                    np.array(list(v["weights"].values())),
                    pos_ret[list(v["weights"].keys())].dropna(how="all")
                )
            )}
            for k, v in portfolios.items()
        },
        "best_pairs":    pair_results[:10],
        "regime_metrics": {
            "max_sharpe_portfolio": {
                "bull":   regime_metrics.get("bull"),
                "bear":   regime_metrics.get("bear"),
                "crises": crisis_metrics,
            }
        },
        "rolling_sharpe_36m": rolling_monthly,
        "correlation_matrix": corr_list,
        "max_sharpe_weights": dict(zip(pos_names, [round(float(w), 4) for w in ms_w])),
    }

    out_path = OUTPUT_DIR / "ls_portfolio_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    log.info(f"\nSaved → {out_path}")


if __name__ == "__main__":
    main()
