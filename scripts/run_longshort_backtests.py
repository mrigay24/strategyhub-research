"""
Long-Short Backtest Runner
==========================

Converts all 14 long-only strategies to market-neutral long-short by:
  Long  leg: top 20% of stocks by factor score  (+1/n_long per stock)
  Short leg: bottom 20% of stocks by factor score (-1/n_short per stock)

The backtester normalises absolute weights to 1.0, so effectively each
leg runs at 50% exposure — dollar-neutral, zero net market beta.

Sharpe ratio is scale-invariant, so the comparison with long-only is valid.
MDD / CAGR will be roughly halved at half leverage.

Run:
    .venv/bin/python scripts/run_longshort_backtests.py

Results saved to:
    results/longshort/longshort_results.json
    results/longshort/comparison.csv
"""

import sys
import json
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Callable, Dict, Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backtesting.engine import Backtester
from src.strategies.base import MultiAssetStrategy, StrategyType


class _WideBacktester(Backtester):
    """Backtester variant that accepts an already-pivoted wide prices DataFrame."""
    def _preprocess_data(self) -> None:
        self.prices = self.data  # already wide (date × symbol)
        self.returns = self.prices.pct_change(fill_method=None).clip(lower=-0.95, upper=2.0)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────

PRICES_PATH = Path("data_processed/extended_prices_clean.parquet")
RESULTS_DIR = Path("results/longshort")
SCORECARD_CSV = Path("results/phase3_summary/master_scorecard.csv")

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

LONG_PCT  = 0.20   # top quintile = long leg
SHORT_PCT = 0.20   # bottom quintile = short leg
MIN_STOCKS = 20    # minimum stocks in universe to generate signals


# ── Minimal strategy wrapper for pre-computed signals ─────────────────────────

class _PrecomputedStrategy(MultiAssetStrategy):
    """Wraps pre-computed signals DataFrame — used to feed custom signals into Backtester."""

    DEFAULT_PARAMS = {}

    def __init__(self, data: pd.DataFrame, signals: pd.DataFrame, strategy_name: str):
        self._precomputed_signals = signals
        self._name = strategy_name
        super().__init__(data)

    @property
    def name(self) -> str:
        return self._name

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.FACTOR

    def generate_signals(self) -> pd.DataFrame:
        return self._precomputed_signals


# ── Data helpers ───────────────────────────────────────────────────────────────

def load_prices() -> pd.DataFrame:
    log.info(f"Loading extended price data from {PRICES_PATH} ...")
    df = pd.read_parquet(PRICES_PATH)
    prices = df.pivot_table(index="date", columns="symbol", values="close", aggfunc="last")
    prices = prices.sort_index()
    log.info(f"Loaded: {prices.shape[0]:,} days × {prices.shape[1]} symbols")
    return prices


def get_monthly_rebalance_dates(prices: pd.DataFrame) -> pd.DatetimeIndex:
    grouped = prices.groupby(pd.Grouper(freq="M"))
    dates = [grp.index[-1] for _, grp in grouped if len(grp) > 0]
    return pd.DatetimeIndex(dates)


def safe_float(v) -> Optional[float]:
    try:
        f = float(v)
        return None if (np.isnan(f) or np.isinf(f)) else round(f, 6)
    except (TypeError, ValueError):
        return None


# ── Signal builder from raw scores ────────────────────────────────────────────

def build_longshort_signals(
    scores: pd.DataFrame,
    rebal_dates: pd.DatetimeIndex,
    long_pct: float = LONG_PCT,
    short_pct: float = SHORT_PCT,
) -> pd.DataFrame:
    """
    Given a raw score matrix (date × symbols, higher = more attractive),
    produce monthly-rebalanced long-short signals.

    Long  top long_pct  → weight = +1 / n_long
    Short bot short_pct → weight = -1 / n_short
    Between rebalance dates: forward fill.
    """
    signals = pd.DataFrame(0.0, index=scores.index, columns=scores.columns)

    for date in rebal_dates:
        if date not in scores.index:
            continue
        row = scores.loc[date].dropna()
        if len(row) < MIN_STOCKS:
            continue

        ranks = row.rank(pct=True)

        longs  = ranks[ranks >= (1 - long_pct)].index
        shorts = ranks[ranks <= short_pct].index

        n_long  = len(longs)
        n_short = len(shorts)

        if n_long > 0:
            signals.loc[date, longs]  = +1.0 / n_long
        if n_short > 0:
            signals.loc[date, shorts] = -1.0 / n_short

    # Forward fill between rebalance dates, then zero any remaining NaN
    signals = signals.replace(0, np.nan).ffill().fillna(0)
    return signals


# ── Factor scoring functions (one per strategy) ───────────────────────────────
# Each receives prices (date×symbol) and returns (daily pct_change) DataFrames.
# Must return a score DataFrame of the same shape — higher score = more attractive.

def score_large_cap_momentum(prices: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """12-month momentum, skip last month (Jegadeesh & Titman 1993)"""
    return prices.pct_change(252).shift(21)


def score_52wk_high_breakout(prices: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """Proximity to 52-week high (George & Hwang 2004)"""
    rolling_high = prices.rolling(252, min_periods=126).max()
    return prices / rolling_high


def score_deep_value(prices: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """Price below 200-day MA → undervalued proxy (lower price/MA = better)"""
    ma200 = prices.rolling(200, min_periods=100).mean()
    return -(prices / ma200)   # invert: cheapest stocks rank highest


def score_high_quality_roic(prices: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """50% quality (low realised vol = ROIC proxy) + 50% momentum"""
    vol = returns.rolling(63, min_periods=21).std()
    mom = prices.pct_change(252).shift(21)
    # Low vol = high quality rank (invert)
    q_rank  = (1 - vol.rank(axis=1, pct=True, na_option="keep"))
    m_rank  = mom.rank(axis=1, pct=True, na_option="keep")
    return 0.5 * q_rank + 0.5 * m_rank


def score_low_volatility_shield(prices: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """Inverse 63-day realised volatility (Baker, Bradley & Wurgler 2011)"""
    vol = returns.rolling(63, min_periods=21).std() * np.sqrt(252)
    return -vol   # lowest vol = highest score


def score_dividend_aristocrats(prices: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """Fraction of positive monthly returns over trailing 36 months (consistency proxy)"""
    monthly_ret = prices.resample("M").last().pct_change()
    pos_months  = (monthly_ret > 0).rolling(36, min_periods=24).mean()
    # Reindex to daily (forward fill weekends/mid-month dates)
    return pos_months.reindex(prices.index, method="ffill")


def score_moving_average_trend(prices: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """Price / 200-day MA — above = uptrend, below = downtrend"""
    ma200 = prices.rolling(200, min_periods=100).mean()
    return prices / ma200


def score_rsi_mean_reversion(prices: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """Negative RSI: oversold (low RSI) stocks rank highest, overbought rank lowest"""
    gain = returns.clip(lower=0).rolling(14, min_periods=7).mean()
    loss = (-returns.clip(upper=0)).rolling(14, min_periods=7).mean()
    rs  = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return -rsi   # most oversold = highest score


def score_value_momentum_blend(prices: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """50% value (price/MA) + 50% momentum"""
    ma200  = prices.rolling(200, min_periods=100).mean()
    value  = -(prices / ma200)
    mom    = prices.pct_change(252).shift(21)
    v_rank = value.rank(axis=1, pct=True, na_option="keep")
    m_rank = mom.rank(axis=1,   pct=True, na_option="keep")
    return 0.5 * v_rank + 0.5 * m_rank


def score_quality_momentum(prices: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """50% quality (low vol) + 50% momentum"""
    vol    = returns.rolling(63, min_periods=21).std()
    mom    = prices.pct_change(252).shift(21)
    q_rank = (1 - vol.rank(axis=1, pct=True, na_option="keep"))
    m_rank = mom.rank(axis=1, pct=True, na_option="keep")
    return 0.5 * q_rank + 0.5 * m_rank


def score_quality_low_vol(prices: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """50% quality (return consistency) + 50% low vol"""
    vol       = returns.rolling(63, min_periods=21).std()
    pos_ret   = (returns > 0).rolling(252, min_periods=126).mean()
    q_rank    = pos_ret.rank(axis=1, pct=True, na_option="keep")
    lv_rank   = (1 - vol.rank(axis=1, pct=True, na_option="keep"))
    return 0.5 * q_rank + 0.5 * lv_rank


def score_composite_factor(prices: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """30% momentum + 20% value + 30% quality + 20% low vol"""
    mom     = prices.pct_change(252).shift(21)
    ma200   = prices.rolling(200, min_periods=100).mean()
    value   = -(prices / ma200)
    vol     = returns.rolling(63, min_periods=21).std()
    pos_ret = (returns > 0).rolling(252, min_periods=126).mean()

    m_rank  = mom.rank(axis=1,     pct=True, na_option="keep")
    v_rank  = value.rank(axis=1,   pct=True, na_option="keep")
    q_rank  = pos_ret.rank(axis=1, pct=True, na_option="keep")
    lv_rank = (1 - vol.rank(axis=1, pct=True, na_option="keep"))

    return 0.30 * m_rank + 0.20 * v_rank + 0.30 * q_rank + 0.20 * lv_rank


def score_volatility_targeting(prices: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """
    Volatility targeting is a risk-management overlay, not a cross-sectional
    stock-selection strategy. Long-short doesn't apply — we rank by inverse vol
    as the closest factor analog, but results should be interpreted cautiously.
    """
    vol = returns.rolling(63, min_periods=21).std() * np.sqrt(252)
    return -vol


def score_earnings_surprise(prices: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """
    PEAD proxy: 5-day cumulative return as earnings-surprise signal.
    Large positive move = likely positive surprise (long).
    Large negative move = likely negative surprise (short) — reverse PEAD.
    """
    return returns.rolling(5, min_periods=3).sum()


# ── Strategy registry ──────────────────────────────────────────────────────────

STRATEGIES: Dict[str, Callable] = {
    "large_cap_momentum":       score_large_cap_momentum,
    "52_week_high_breakout":    score_52wk_high_breakout,
    "deep_value_all_cap":       score_deep_value,
    "high_quality_roic":        score_high_quality_roic,
    "low_volatility_shield":    score_low_volatility_shield,
    "dividend_aristocrats":     score_dividend_aristocrats,
    "moving_average_trend":     score_moving_average_trend,
    "rsi_mean_reversion":       score_rsi_mean_reversion,
    "value_momentum_blend":     score_value_momentum_blend,
    "quality_momentum":         score_quality_momentum,
    "quality_low_vol":          score_quality_low_vol,
    "composite_factor_score":   score_composite_factor,
    "volatility_targeting":     score_volatility_targeting,
    "earnings_surprise_momentum": score_earnings_surprise,
}


# ── Long-only benchmark (buy-and-hold equal weight) ───────────────────────────

def run_benchmark(prices: pd.DataFrame) -> dict:
    """Equal-weight buy-and-hold S&P 500 proxy."""
    ew_returns = prices.pct_change(fill_method=None).mean(axis=1).fillna(0)
    equity = 100_000 * (1 + ew_returns).cumprod()
    total_ret  = (equity.iloc[-1] / equity.iloc[0]) - 1
    n_years    = len(equity) / 252
    cagr       = (1 + total_ret) ** (1 / n_years) - 1 if n_years > 0 else 0
    ann_ret    = ew_returns.mean() * 252
    ann_vol    = ew_returns.std()  * np.sqrt(252)
    sharpe     = (ann_ret - 0.02) / ann_vol if ann_vol > 0 else 0
    roll_max   = equity.cummax()
    drawdowns  = (equity - roll_max) / roll_max
    mdd        = drawdowns.min()
    return {"sharpe_ratio": safe_float(sharpe), "cagr": safe_float(cagr),
            "max_drawdown": safe_float(mdd)}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("Long-Short Backtest Runner")
    log.info("=" * 60)

    prices = load_prices()
    returns = prices.pct_change(fill_method=None)
    rebal_dates = get_monthly_rebalance_dates(prices)

    # Load long-only Sharpe from scorecard for comparison
    longonly_sharpes: Dict[str, float] = {}
    if SCORECARD_CSV.exists():
        import csv
        with open(SCORECARD_CSV) as f:
            for row in csv.DictReader(f):
                key = row.get("strategy", "")
                try:
                    longonly_sharpes[key] = float(row["sharpe"])
                except (ValueError, KeyError):
                    pass

    results = {}

    for strategy_name, score_fn in STRATEGIES.items():
        log.info(f"\n{'─' * 50}")
        log.info(f"  {strategy_name}")

        try:
            # 1. Compute raw scores
            scores = score_fn(prices, returns)

            # 2. Build long-short signals
            signals = build_longshort_signals(scores, rebal_dates)

            n_long  = (signals > 0).sum(axis=1).mean()
            n_short = (signals < 0).sum(axis=1).mean()
            log.info(f"  Avg positions: {n_long:.0f} long, {n_short:.0f} short")

            # 3. Wrap in PrecomputedStrategy and run backtester
            strategy = _PrecomputedStrategy(
                data=prices,
                signals=signals,
                strategy_name=f"{strategy_name}_longshort",
            )

            backtester = _WideBacktester(
                strategy=strategy,
                data=prices,
                initial_capital=100_000,
                commission_bps=10,
                slippage_bps=5,
            )
            result = backtester.run()
            m = result.metrics

            ls_sharpe = safe_float(m.get("sharpe_ratio"))
            lo_sharpe = longonly_sharpes.get(strategy_name)
            improvement = (ls_sharpe - lo_sharpe) if (ls_sharpe and lo_sharpe) else None

            results[strategy_name] = {
                "longshort": {
                    "sharpe_ratio": ls_sharpe,
                    "cagr":         safe_float(m.get("cagr")),
                    "max_drawdown": safe_float(m.get("max_drawdown")),
                    "volatility":   safe_float(m.get("volatility")),
                    "total_return": safe_float(m.get("total_return")),
                },
                "longonly_sharpe": lo_sharpe,
                "sharpe_improvement": safe_float(improvement) if improvement else None,
            }

            arrow = "▲" if improvement and improvement > 0 else "▼"
            log.info(
                f"  L/S Sharpe: {ls_sharpe:.3f}  |  "
                f"Long-only: {lo_sharpe:.3f}  |  "
                f"Change: {arrow} {improvement:+.3f}"
                if (ls_sharpe and lo_sharpe and improvement is not None)
                else f"  L/S Sharpe: {ls_sharpe}  (no long-only baseline)"
            )

        except Exception as e:
            log.error(f"  FAILED: {e}")
            results[strategy_name] = {"error": str(e)}

    # ── Benchmark ──────────────────────────────────────────────────────────────
    log.info("\nRunning benchmark (equal-weight buy-and-hold) ...")
    benchmark = run_benchmark(prices)
    results["_benchmark"] = benchmark
    log.info(f"Benchmark Sharpe: {benchmark['sharpe_ratio']:.3f}")

    # ── Save results ───────────────────────────────────────────────────────────
    out_path = RESULTS_DIR / "longshort_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    log.info(f"\nResults saved → {out_path}")

    # ── Print comparison table ─────────────────────────────────────────────────
    log.info("\n" + "=" * 68)
    log.info(f"{'Strategy':<32} {'L/S Sharpe':>10} {'L/O Sharpe':>10} {'Delta':>8}")
    log.info("=" * 68)

    rows = []
    for name, r in results.items():
        if name.startswith("_") or "error" in r:
            continue
        ls = r.get("longshort", {}).get("sharpe_ratio")
        lo = r.get("longonly_sharpe")
        delta = r.get("sharpe_improvement")
        rows.append((name, ls, lo, delta))

    rows.sort(key=lambda x: (x[1] or -99), reverse=True)

    for name, ls, lo, delta in rows:
        ls_s   = f"{ls:.3f}" if ls is not None else "N/A"
        lo_s   = f"{lo:.3f}" if lo is not None else "N/A"
        d_s    = f"{delta:+.3f}" if delta is not None else "N/A"
        arrow  = "▲" if delta and delta > 0 else ("▼" if delta and delta < 0 else " ")
        log.info(f"{name:<32} {ls_s:>10} {lo_s:>10} {arrow}{d_s:>7}")

    bm_sharpe = results.get("_benchmark", {}).get("sharpe_ratio")
    log.info("─" * 68)
    log.info(f"{'Benchmark (equal-weight)':<32} {bm_sharpe:.3f}" if bm_sharpe else "")
    log.info("=" * 68)

    # ── Save CSV ───────────────────────────────────────────────────────────────
    csv_rows = []
    for name, ls, lo, delta in rows:
        mdd = results[name].get("longshort", {}).get("max_drawdown")
        cagr = results[name].get("longshort", {}).get("cagr")
        csv_rows.append({
            "strategy": name,
            "ls_sharpe": ls,
            "lo_sharpe": lo,
            "sharpe_delta": delta,
            "ls_cagr": cagr,
            "ls_max_drawdown": mdd,
        })
    pd.DataFrame(csv_rows).to_csv(RESULTS_DIR / "comparison.csv", index=False)
    log.info(f"CSV saved → {RESULTS_DIR / 'comparison.csv'}")


if __name__ == "__main__":
    main()
