"""
Long-Short Factor Backtest Runner
==================================
Computes proper dollar-neutral long-short (quintile) backtests for all 14
strategies over the 25-year extended dataset (2000–2024).

Each strategy's underlying factor score is computed for ALL stocks in the
universe (not just the long leg), enabling genuine top-quintile vs
bottom-quintile comparison that measures the pure cross-sectional factor
premium — independent of market direction.

Results are saved to: results/longshort/longshort_results.json

Run:
    .venv/bin/python scripts/run_longshort_backtests.py
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtesting.long_short_engine import LongShortBacktester

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

PRICES_PATH   = ROOT / "data_processed" / "extended_prices_clean.parquet"
RESULTS_DIR   = ROOT / "results" / "longshort"
SCORECARD_CSV = ROOT / "results" / "phase3_summary" / "master_scorecard.csv"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

QUINTILE = 0.20     # top / bottom 20 % of universe = one quintile


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return round(float(v), 4)


def _rebal_dates(index: pd.DatetimeIndex, freq: str) -> pd.DatetimeIndex:
    """Month-end / week-end / quarter-end dates present in index."""
    sampled = index.to_series().resample(freq).last().dropna()
    valid = sampled[sampled.index.isin(index)]
    return valid.index


def _build_sparse(scores_at_rebal: pd.DataFrame,
                  full_index: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Expand rebalancing-date scores to full daily index.
    Scores are placed only on rebalancing dates; everything else is NaN.
    LongShortBacktester reads NaN as 'no rebalance today'.
    """
    sparse = pd.DataFrame(np.nan, index=full_index,
                          columns=scores_at_rebal.columns)
    dates_present = scores_at_rebal.index.intersection(full_index)
    sparse.loc[dates_present] = scores_at_rebal.loc[dates_present]
    return sparse


def _load_longonly_sharpes() -> Dict[str, float]:
    if not SCORECARD_CSV.exists():
        return {}
    import csv
    out = {}
    with open(SCORECARD_CSV) as f:
        for row in csv.DictReader(f):
            try:
                out[row["strategy"]] = float(row["sharpe"])
            except (KeyError, ValueError):
                pass
    return out


def _get_spy_returns(prices: pd.DataFrame) -> pd.Series:
    if "SPY" in prices.columns:
        return prices["SPY"].pct_change(fill_method=None).fillna(0)
    try:
        import yfinance as yf
        spy = yf.download("SPY", start="2000-01-01", end="2025-01-01",
                          auto_adjust=True, progress=False)
        spy_ret = spy["Close"].pct_change().dropna()
        return spy_ret.reindex(prices.index).fillna(0)
    except Exception as e:
        log.warning(f"Could not fetch SPY returns: {e}")
        return pd.Series(0.0, index=prices.index)


# ── Factor score functions ─────────────────────────────────────────────────────
# Each returns a DataFrame (rebal_dates × symbols) with raw scores.
# Higher score = more attractive for the long leg.

def score_large_cap_momentum(prices, _returns, rebal_idx):
    """12M momentum, skip last month. Large-cap proxy: top 50% by avg price."""
    mom  = (prices.shift(21) / prices.shift(252) - 1)
    avg_p = prices.rolling(63, min_periods=21).mean()
    out = pd.DataFrame(np.nan, index=rebal_idx, columns=prices.columns)
    for date in rebal_idx:
        if date not in mom.index:
            continue
        m = mom.loc[date].dropna()
        a = avg_p.loc[date].dropna()
        common = m.index.intersection(a.index)
        if len(common) < 20:
            continue
        large_cap = a[common][a[common].rank(pct=True) >= 0.50].index
        if len(large_cap) < 10:
            continue
        out.loc[date, large_cap] = m[large_cap]
    return out.dropna(how="all")


def score_52wk_high(prices, _returns, rebal_idx):
    proximity = prices / prices.rolling(252, min_periods=126).max()
    return proximity.reindex(rebal_idx).dropna(how="all")


def score_deep_value(prices, _returns, rebal_idx):
    """Negate P/MA: cheapest stocks get highest score."""
    ma200 = prices.rolling(200, min_periods=100).mean()
    return (-(prices / ma200.replace(0, np.nan))).reindex(rebal_idx).dropna(how="all")


def score_high_quality(_prices, returns, rebal_idx):
    """Rolling Sharpe ratio (smooth uptrend = quality proxy)."""
    r_mean = returns.rolling(252, min_periods=63).mean()
    r_std  = returns.rolling(252, min_periods=63).std()
    quality = r_mean / r_std.replace(0, np.nan) * np.sqrt(252)
    return quality.reindex(rebal_idx).dropna(how="all")


def score_low_vol(_prices, returns, rebal_idx, vol_lb=63):
    vol = returns.rolling(vol_lb, min_periods=21).std() * np.sqrt(252)
    return (-vol).reindex(rebal_idx).dropna(how="all")


def score_dividend_aristocrats(prices, _returns, rebal_idx):
    monthly_ret = prices.resample("M").last().pct_change(fill_method=None)
    pct_pos = (monthly_ret > 0).rolling(36, min_periods=24).mean()
    out = pd.DataFrame(np.nan, index=rebal_idx, columns=prices.columns)
    for date in rebal_idx:
        match = pct_pos.index[pct_pos.index <= date]
        if len(match) == 0:
            continue
        out.loc[date] = pct_pos.loc[match[-1]]
    return out.dropna(how="all")


def score_ma_trend(prices, _returns, rebal_idx):
    ma50  = prices.rolling(50,  min_periods=25).mean()
    ma200 = prices.rolling(200, min_periods=100).mean()
    trend = (ma50 - ma200) / ma200.replace(0, np.nan)
    return trend.reindex(rebal_idx).dropna(how="all")


def score_rsi(_prices, returns, rebal_idx, period=14):
    gain = returns.clip(lower=0).ewm(com=period - 1, min_periods=period).mean()
    loss = (-returns.clip(upper=0)).ewm(com=period - 1, min_periods=period).mean()
    rs   = gain / loss.replace(0, np.nan)
    rsi  = 100 - (100 / (1 + rs))
    return (-rsi).reindex(rebal_idx).dropna(how="all")  # negate: oversold = high score


def score_value_momentum(prices, returns, rebal_idx):
    val_score = score_deep_value(prices, returns, rebal_idx)
    mom_score = score_large_cap_momentum(prices, returns, rebal_idx)
    common_idx = val_score.index.intersection(mom_score.index)
    v = val_score.reindex(common_idx).rank(axis=1, pct=True, na_option="keep")
    m = mom_score.reindex(common_idx).rank(axis=1, pct=True, na_option="keep")
    return (0.5 * v + 0.5 * m).dropna(how="all")


def score_quality_momentum(prices, returns, rebal_idx):
    q_score = score_high_quality(prices, returns, rebal_idx)
    m_score = score_large_cap_momentum(prices, returns, rebal_idx)
    common_idx = q_score.index.intersection(m_score.index)
    q = q_score.reindex(common_idx).rank(axis=1, pct=True, na_option="keep")
    m = m_score.reindex(common_idx).rank(axis=1, pct=True, na_option="keep")
    return (0.5 * q + 0.5 * m).dropna(how="all")


def score_quality_low_vol(prices, returns, rebal_idx):
    q_score  = score_high_quality(prices, returns, rebal_idx)
    lv_score = score_low_vol(prices, returns, rebal_idx)
    common_idx = q_score.index.intersection(lv_score.index)
    q  = q_score.reindex(common_idx).rank(axis=1, pct=True, na_option="keep")
    lv = lv_score.reindex(common_idx).rank(axis=1, pct=True, na_option="keep")
    return (0.5 * q + 0.5 * lv).dropna(how="all")


def score_composite(prices, returns, rebal_idx):
    """30% momentum + 20% value + 30% quality + 20% low-vol."""
    m_s  = score_large_cap_momentum(prices, returns, rebal_idx)
    v_s  = score_deep_value(prices, returns, rebal_idx)
    q_s  = score_high_quality(prices, returns, rebal_idx)
    lv_s = score_low_vol(prices, returns, rebal_idx)
    idx  = m_s.index.intersection(v_s.index).intersection(q_s.index).intersection(lv_s.index)
    m  = m_s.reindex(idx).rank(axis=1, pct=True, na_option="keep")
    v  = v_s.reindex(idx).rank(axis=1, pct=True, na_option="keep")
    q  = q_s.reindex(idx).rank(axis=1, pct=True, na_option="keep")
    lv = lv_s.reindex(idx).rank(axis=1, pct=True, na_option="keep")
    return (0.30*m + 0.20*v + 0.30*q + 0.20*lv).dropna(how="all")


def score_earnings_surprise(_prices, returns, rebal_idx):
    """Z-score of recent 5-day return (PEAD proxy)."""
    r5     = returns.rolling(5, min_periods=3).sum()
    r_mean = returns.rolling(63, min_periods=21).mean() * 5
    r_std  = returns.rolling(63, min_periods=21).std()  * np.sqrt(5)
    z      = (r5 - r_mean) / r_std.replace(0, np.nan)
    return z.reindex(rebal_idx).dropna(how="all")


# ── Strategy configuration ────────────────────────────────────────────────────

STRATEGY_CONFIGS = {
    "large_cap_momentum":         ("M",     score_large_cap_momentum),
    "52_week_high_breakout":      ("M",     score_52wk_high),
    "deep_value_all_cap":         ("Q",     score_deep_value),
    "high_quality_roic":          ("M",     score_high_quality),
    "low_volatility_shield":      ("M",     score_low_vol),
    "dividend_aristocrats":       ("Q",     score_dividend_aristocrats),
    "moving_average_trend":       ("W-FRI", score_ma_trend),
    "rsi_mean_reversion":         ("W-FRI", score_rsi),
    "value_momentum_blend":       ("M",     score_value_momentum),
    "quality_momentum":           ("M",     score_quality_momentum),
    "quality_low_vol":            ("M",     score_quality_low_vol),
    "composite_factor_score":     ("M",     score_composite),
    "volatility_targeting":       ("M",     score_low_vol),         # closest analog
    "earnings_surprise_momentum": ("W-FRI", score_earnings_surprise),
}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 65)
    log.info("StrategyHub — Long-Short Factor Backtest Runner")
    log.info("=" * 65)

    # Load prices — long format (date, symbol, close, ...) → pivot to wide
    log.info(f"Loading {PRICES_PATH.name} ...")
    raw = pd.read_parquet(PRICES_PATH)
    prices = raw.pivot_table(index="date", columns="symbol", values="close")
    prices.index = pd.to_datetime(prices.index)
    prices = prices.sort_index().astype(float)
    log.info(f"  {prices.shape[0]:,} days × {prices.shape[1]} symbols  "
             f"({prices.index[0].date()} → {prices.index[-1].date()})")

    returns = prices.pct_change(fill_method=None).clip(-0.95, 2.0)
    spy_ret = _get_spy_returns(prices)
    lo_sharpes = _load_longonly_sharpes()

    results = {}
    success = 0

    for name, (freq, score_fn) in STRATEGY_CONFIGS.items():
        log.info(f"\n{'─'*55}")
        log.info(f"  {name}  (rebal: {freq})")
        try:
            rebal_idx    = _rebal_dates(prices.index, freq)
            scores_rebal = score_fn(prices, returns, rebal_idx)

            if scores_rebal.empty:
                results[name] = {"error": "No scores produced"}
                continue

            sparse = _build_sparse(scores_rebal, prices.index)

            engine = LongShortBacktester(
                prices          = prices,
                factor_scores   = sparse,
                quintile_pct    = QUINTILE,
                commission_bps  = 15.0,
                borrow_cost_bps = 50.0,
                spy_returns     = spy_ret,
            )
            r = engine.run(strategy_name=name)

            lo_sr = lo_sharpes.get(name)
            delta = (r.sharpe_ratio - lo_sr) if lo_sr is not None else None

            log.info(
                f"  ✓ LS Sharpe={r.sharpe_ratio:.3f}  "
                f"CAGR={r.cagr*100:.1f}%  "
                f"MDD={r.max_drawdown*100:.1f}%  "
                f"SPY_corr={r.spy_correlation:.3f}  "
                f"{'Δ vs L/O: ' + (f'{delta:+.3f}' if delta is not None else 'N/A')}"
            )

            d = r.to_dict()
            d["longonly_sharpe"]     = _safe(lo_sr)
            d["sharpe_vs_longonly"]  = _safe(delta)
            results[name] = d
            success += 1

        except Exception as e:
            import traceback
            log.error(f"  ✗ {name}: {e}")
            log.error(traceback.format_exc())
            results[name] = {"error": str(e)}

    # ── Summary table ──────────────────────────────────────────────────────────
    log.info(f"\n{'='*65}")
    log.info(f"Completed: {success}/{len(STRATEGY_CONFIGS)}")
    log.info(f"\n{'Strategy':<35} {'LS Sharpe':>10} {'LO Sharpe':>10} {'Delta':>8} {'SPY Corr':>10}")
    log.info("─" * 75)
    rows = [(n, r) for n, r in results.items() if "error" not in r]
    rows.sort(key=lambda x: x[1].get("sharpe_ratio", -99), reverse=True)
    for n, r in rows:
        log.info(
            f"  {n:<33} "
            f"{r.get('sharpe_ratio', float('nan')):>10.3f} "
            f"{(r.get('longonly_sharpe') or float('nan')):>10.3f} "
            f"{(r.get('sharpe_vs_longonly') or float('nan')):>+8.3f} "
            f"{r.get('spy_correlation', float('nan')):>10.3f}"
        )

    # ── Save JSON ──────────────────────────────────────────────────────────────
    output = {
        "generated_at":    datetime.now().isoformat(),
        "data_period":     f"{prices.index[0].date()} – {prices.index[-1].date()}",
        "n_symbols":       prices.shape[1],
        "quintile_pct":    QUINTILE,
        "commission_bps":  15.0,
        "borrow_cost_bps": 50.0,
        "strategies":      results,
    }
    with open(RESULTS_DIR / "longshort_results.json", "w") as f:
        json.dump(output, f, indent=2)
    log.info(f"\nSaved → {RESULTS_DIR / 'longshort_results.json'}")

    # ── Save CSV comparison ────────────────────────────────────────────────────
    csv_data = []
    for n, r in rows:
        csv_data.append({
            "strategy":         n,
            "ls_sharpe":        r.get("sharpe_ratio"),
            "lo_sharpe":        r.get("longonly_sharpe"),
            "sharpe_delta":     r.get("sharpe_vs_longonly"),
            "ls_cagr":          r.get("cagr"),
            "ls_max_drawdown":  r.get("max_drawdown"),
            "ls_volatility":    r.get("volatility"),
            "spy_correlation":  r.get("spy_correlation"),
        })
    pd.DataFrame(csv_data).to_csv(RESULTS_DIR / "comparison.csv", index=False)
    log.info(f"CSV   → {RESULTS_DIR / 'comparison.csv'}")


if __name__ == "__main__":
    main()
