"""
Walk-Forward Composite Engine
=============================
Builds a META-strategy: a time-varying weighted blend of the long-short factor
"sleeves" (the 14 dollar-neutral strategy return streams). The point of this
engine — vs the existing `ls_portfolio_analysis.py` — is that weights are
estimated OUT-OF-SAMPLE: at each rebalance date the weights are computed from a
trailing lookback window only, then held forward into unseen data. It also
charges a transaction cost on the turnover of the weight vector, so the reported
Sharpe is net of the cost of actually running the blend.

Why this matters: `ls_portfolio_analysis.py` fits weights on the full 25 years
and reports the resulting Sharpe — that is look-ahead. A blend that looks great
with hindsight-optimal weights tells you nothing about what you could have
traded. This engine answers the honest question: "if you had only ever seen the
past, and paid to rebalance, what would the blend have returned?"

Design notes
------------
* Inputs are MONTHLY L/S sleeve returns (from results/longshort/longshort_results.json).
  Monthly is deliberate: it matches how the sleeves rebalance and avoids fitting
  to daily noise. All Sharpes here are monthly-based (× sqrt(12)).
* Weighting schemes are pluggable (equal / inverse-vol / risk-parity-ERC /
  max-Sharpe-MVO). All produce non-negative weights summing to 1 over the
  selected sleeves — we never short a *sleeve* (that would be a long-short of a
  long-short, which is exotic and not what we're claiming).
* Sleeve eligibility is decided IN-SAMPLE per window (e.g. "only sleeves whose
  trailing Sharpe > 0"), so the live blend never gets to peek at a sleeve's
  future. This can leave a window with too few eligible sleeves — handled by a
  fallback to equal-weight over whatever is eligible (or all sleeves if none).

This module is import-only (no side effects). Runners live in scripts/.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
LS_FILE = ROOT / "results" / "longshort" / "longshort_results.json"

RF_ANNUAL = 0.02
ANNUAL_PERIODS = 12  # monthly


# ── Data loading ──────────────────────────────────────────────────────────────

def load_sleeve_returns(ls_file: Path = LS_FILE) -> pd.DataFrame:
    """Monthly L/S return matrix: index=month-end dates, columns=sleeve names."""
    raw = json.loads(Path(ls_file).read_text())
    series = {}
    for name, s in raw["strategies"].items():
        ec = s.get("equity_curve", [])
        if len(ec) < 24:
            continue
        vals = pd.Series(
            [p["value"] for p in ec],
            index=pd.to_datetime([p["date"] for p in ec]),
            name=name,
        )
        series[name] = vals.pct_change()
    return pd.DataFrame(series).dropna(how="all")


# ── Stat helpers (monthly) ────────────────────────────────────────────────────

def sharpe(r: pd.Series, rf_annual: float = RF_ANNUAL) -> float:
    r = r.dropna()
    if len(r) < 6 or r.std() == 0:
        return 0.0
    excess = r - rf_annual / ANNUAL_PERIODS
    return float(excess.mean() / r.std() * np.sqrt(ANNUAL_PERIODS))


def cagr(r: pd.Series) -> float:
    r = r.dropna()
    if len(r) < 2:
        return 0.0
    total = (1 + r).prod() - 1
    if total <= -1:
        return -1.0
    return float((1 + total) ** (ANNUAL_PERIODS / len(r)) - 1)


def mdd(r: pd.Series) -> float:
    eq = (1 + r.fillna(0)).cumprod()
    return float((eq / eq.expanding().max() - 1).min())


def ann_vol(r: pd.Series) -> float:
    return float(r.dropna().std() * np.sqrt(ANNUAL_PERIODS))


def sortino(r: pd.Series, rf_annual: float = RF_ANNUAL) -> float:
    r = r.dropna()
    if len(r) < 6:
        return 0.0
    excess = r - rf_annual / ANNUAL_PERIODS
    downside = excess[excess < 0]
    dd = downside.std()
    if dd == 0 or np.isnan(dd):
        return 0.0
    return float(excess.mean() / dd * np.sqrt(ANNUAL_PERIODS))


def metrics(r: pd.Series, label: str = "") -> dict:
    r = r.dropna()
    c = cagr(r)
    m = mdd(r)
    return {
        "label": label,
        "sharpe": round(sharpe(r), 4),
        "sortino": round(sortino(r), 4),
        "cagr": round(c, 4),
        "ann_vol": round(ann_vol(r), 4),
        "max_drawdown": round(m, 4),
        "calmar": round(c / abs(m), 4) if m < 0 else None,
        "win_rate": round(float((r > 0).sum() / max((r != 0).sum(), 1)), 4),
        "n_months": int(r.notna().sum()),
    }


# ── Weighting schemes ─────────────────────────────────────────────────────────
# Each takes a trailing-window return frame (rows=months, cols=eligible sleeves)
# and returns a non-negative weight vector summing to 1, aligned to its columns.

def w_equal(window: pd.DataFrame) -> np.ndarray:
    n = window.shape[1]
    return np.ones(n) / n


def w_inverse_vol(window: pd.DataFrame) -> np.ndarray:
    vol = window.std().values
    if np.any(vol <= 0) or np.any(~np.isfinite(vol)):
        return w_equal(window)
    inv = 1.0 / vol
    return inv / inv.sum()


def w_risk_parity(window: pd.DataFrame, iters: int = 250) -> np.ndarray:
    """Equal-risk-contribution weights via simple multiplicative iteration.

    Each sleeve contributes the same share of portfolio variance. Falls back to
    inverse-vol if the covariance is degenerate.
    """
    cov = window.cov().values
    n = cov.shape[0]
    if n == 0 or not np.all(np.isfinite(cov)):
        return w_equal(window)
    w = np.ones(n) / n
    for _ in range(iters):
        mrc = cov @ w                      # marginal risk contribution
        rc = w * mrc                       # risk contribution
        port_var = float(w @ cov @ w)
        if port_var <= 0:
            return w_inverse_vol(window)
        target = port_var / n
        # nudge each weight toward equal risk contribution
        w = w * (target / np.maximum(rc, 1e-12)) ** 0.5
        w = np.clip(w, 0, None)
        s = w.sum()
        if s <= 0:
            return w_inverse_vol(window)
        w = w / s
    return w


def w_max_sharpe(window: pd.DataFrame) -> np.ndarray:
    """Long-only max-Sharpe (mean-variance) weights via scipy SLSQP.

    This is the most aggressive / overfit-prone scheme — included precisely so we
    can SEE it overfit out-of-sample and contrast it with the humbler schemes.
    """
    try:
        from scipy.optimize import minimize
    except Exception:
        return w_inverse_vol(window)
    mu = window.mean().values * ANNUAL_PERIODS
    sigma = window.cov().values * ANNUAL_PERIODS
    n = len(mu)
    if n == 0 or not np.all(np.isfinite(sigma)):
        return w_equal(window)

    def neg_sharpe(w):
        pv = float(np.sqrt(max(w @ sigma @ w, 1e-18)))
        return -((w @ mu - RF_ANNUAL) / pv)

    res = minimize(
        neg_sharpe, x0=np.ones(n) / n, method="SLSQP",
        bounds=[(0.0, 1.0)] * n,
        constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}],
        options={"maxiter": 500, "ftol": 1e-9},
    )
    w = np.clip(res.x, 0, 1)
    s = w.sum()
    return w / s if s > 0 else w_equal(window)


WEIGHT_SCHEMES = {
    "equal": w_equal,
    "inverse_vol": w_inverse_vol,
    "risk_parity": w_risk_parity,
    "max_sharpe": w_max_sharpe,
}


# ── Composite specification ───────────────────────────────────────────────────

@dataclass
class CompositeSpec:
    """One composite recipe. The grid in build_composites.py is a list of these."""
    name: str
    sleeves: list[str]                      # candidate universe (subset of 14)
    scheme: str = "inverse_vol"             # key into WEIGHT_SCHEMES
    lookback: int = 36                      # trailing months used to estimate weights
    rebalance_every: int = 3                # months between re-estimation
    eligibility: str = "positive_sharpe"    # "all" | "positive_sharpe"
    cost_bps: float = 10.0                  # one-way cost per unit of weight turnover
    min_sleeves: int = 2                    # below this, fall back to equal-weight
    display: str = ""
    notes: str = ""


# ── The walk-forward engine ───────────────────────────────────────────────────

@dataclass
class CompositeResult:
    spec: CompositeSpec
    gross_returns: pd.Series                # before composite-layer costs
    net_returns: pd.Series                  # after turnover costs
    weights: pd.DataFrame                   # index=rebalance dates, cols=sleeves
    turnover: pd.Series                     # per-rebalance one-way turnover
    meta: dict = field(default_factory=dict)


def _eligible(window: pd.DataFrame, mode: str) -> list[str]:
    if mode == "all":
        return list(window.columns)
    if mode == "positive_sharpe":
        keep = [c for c in window.columns if sharpe(window[c]) > 0]
        return keep
    raise ValueError(f"unknown eligibility: {mode}")


def run_composite(returns: pd.DataFrame, spec: CompositeSpec) -> CompositeResult:
    """Walk-forward backtest of one composite spec.

    At each rebalance month t:
      window = returns[t-lookback : t]          # strictly past data
      elig   = sleeves passing the in-sample eligibility rule
      w      = scheme(window[elig])             # weights from past only
      apply w to the NEXT `rebalance_every` months of sleeve returns (OOS).
    Turnover cost = cost_bps * sum(|w_t - w_{t-1}|) charged in the first month
    of each new weight regime.
    """
    rets = returns[spec.sleeves].copy()
    dates = rets.index
    lb, step = spec.lookback, spec.rebalance_every

    gross = pd.Series(0.0, index=dates)
    net = pd.Series(0.0, index=dates)
    turn = {}
    weight_hist = {}

    prev_w = pd.Series(0.0, index=spec.sleeves)
    scheme_fn = WEIGHT_SCHEMES[spec.scheme]

    # first rebalance once we have a full lookback window
    start_i = lb
    i = start_i
    while i < len(dates):
        window = rets.iloc[i - lb:i].dropna(axis=1, how="any")
        elig = _eligible(window, spec.eligibility)

        if len(elig) < spec.min_sleeves:
            # not enough conviction sleeves → equal-weight over whatever we have,
            # or over all sleeves if literally nothing passed.
            elig = list(window.columns) if len(window.columns) else spec.sleeves
            w_vec = np.ones(len(elig)) / len(elig)
        else:
            w_vec = scheme_fn(window[elig])

        w = pd.Series(0.0, index=spec.sleeves)
        w[elig] = w_vec

        # turnover vs previous regime (one-way) and its cost in bps
        t_over = float(np.abs(w.values - prev_w.values).sum()) / 2.0
        cost = t_over * spec.cost_bps / 1e4
        rebal_date = dates[i]
        turn[rebal_date] = t_over
        weight_hist[rebal_date] = w.copy()
        prev_w = w

        # apply weights OOS across the holding block
        block = dates[i:i + step]
        for j, d in enumerate(block):
            row = rets.loc[d]
            r = float((w * row).sum(skipna=True))
            gross[d] = r
            net[d] = r - (cost if j == 0 else 0.0)  # cost hits first month of block

        i += step

    # trim leading warm-up months (no position yet)
    gross = gross.iloc[start_i:]
    net = net.iloc[start_i:]

    weights_df = pd.DataFrame(weight_hist).T
    turn_s = pd.Series(turn)

    return CompositeResult(
        spec=spec,
        gross_returns=gross,
        net_returns=net,
        weights=weights_df,
        turnover=turn_s,
        meta={
            "oos_start": str(gross.index[0].date()),
            "oos_end": str(gross.index[-1].date()),
            "n_months": int(len(gross)),
            "n_rebalances": int(len(turn_s)),
            "avg_turnover": round(float(turn_s.mean()), 4),
            "ann_turnover": round(float(turn_s.mean()) * (ANNUAL_PERIODS / step), 4),
            "cost_drag_annual": round(
                float(turn_s.mean()) * spec.cost_bps / 1e4 * (ANNUAL_PERIODS / step), 5
            ),
        },
    )


def equity_curve(r: pd.Series) -> list[dict]:
    eq = (1 + r.fillna(0)).cumprod()
    return [{"date": str(d.date()), "value": round(float(v), 6)}
            for d, v in eq.items() if pd.notna(v)]
