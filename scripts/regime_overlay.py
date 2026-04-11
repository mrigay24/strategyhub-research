"""
Regime Overlay — Strategy Improvement via Market Filter (Phase 2.6)

Uses the Bear-market finding from Phase 2.4 as direct feedback to improve all strategies.
Applies a market-regime filter ON TOP of existing strategy signals:

  Bear regime  → Set position weights to 0 (go to cash)
  Other regimes → Keep strategy signals as-is (or apply partial reduction in Sideways)

Three overlay variants tested:
  1. Bear-only overlay:     Cash only in Bear, normal positions otherwise
  2. Aggressive overlay:    Cash in Bear + 50% position in Sideways
  3. Trend-only overlay:    Cash whenever 63-day market return is negative (simpler rule)

For each strategy, we report:
  - Before vs after Sharpe ratio (overall and per-regime)
  - Max drawdown improvement
  - Bear regime Sharpe (target: from negative to near-zero)
  - "Cost of protection": how much Bull/High-Vol performance we sacrifice

Usage:
    .venv/bin/python scripts/regime_overlay.py                          # All strategies
    .venv/bin/python scripts/regime_overlay.py large_cap_momentum       # One strategy
"""

import sys
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.strategies import get_strategy, STRATEGY_REGISTRY
from loguru import logger

logger.remove()
logger.add(lambda msg: print(msg, end=""), format="{time:HH:mm:ss} | {message}\n", level="INFO")

# ─── Configuration ────────────────────────────────────────────────────────────

# Same regime parameters as regime_analysis.py (must be consistent)
TREND_WINDOW = 63
VOL_WINDOW = 63
BULL_RETURN_THRESHOLD = 0.05
BEAR_RETURN_THRESHOLD = -0.05
HIGH_VOL_THRESHOLD = 0.20

COMMISSION_BPS = 10
SLIPPAGE_BPS = 5
RISK_FREE_RATE = 0.02

RESULTS_DIR = PROJECT_ROOT / 'results' / 'regime_overlay'


def safe_float(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return round(float(v), 6)


# ─── Regime Detection ─────────────────────────────────────────────────────────

def compute_market_index(data: pd.DataFrame) -> pd.Series:
    """Equal-weighted daily return across all stocks (same as regime_analysis.py)."""
    prices = data.pivot(index='date', columns='symbol', values='close')
    returns = prices.pct_change()
    return returns.mean(axis=1)


def classify_regimes(market_returns: pd.Series) -> pd.Series:
    """
    Classify each day into Bull / Bear / High-Vol / Sideways.
    Identical logic to regime_analysis.py.
    """
    df = pd.DataFrame({'ret': market_returns})
    df['cum_return_63d'] = (1 + df['ret']).rolling(TREND_WINDOW).apply(
        lambda x: x.prod() - 1, raw=True
    )
    df['ann_vol_63d'] = df['ret'].rolling(VOL_WINDOW).std() * np.sqrt(252)

    conditions = [
        df['cum_return_63d'] < BEAR_RETURN_THRESHOLD,
        (df['cum_return_63d'] > BULL_RETURN_THRESHOLD) & (df['ann_vol_63d'] < HIGH_VOL_THRESHOLD),
        df['ann_vol_63d'] >= HIGH_VOL_THRESHOLD,
    ]
    choices = ['Bear', 'Bull', 'High-Vol']
    regimes = np.select(conditions, choices, default='Sideways')
    return pd.Series(regimes, index=market_returns.index, name='regime')


# ─── Overlay Logic ────────────────────────────────────────────────────────────

def apply_overlay(signals: pd.DataFrame, regimes: pd.Series, overlay_type: str) -> pd.DataFrame:
    """
    Apply a regime overlay to strategy signals.

    overlay_type:
      'bear_only'   — zero positions in Bear only
      'aggressive'  — zero in Bear, half in Sideways
      'trend_only'  — zero when 63-day trend < 0 (simpler threshold, no vol component)

    Returns modified signals DataFrame (same shape as input).
    """
    overlay = signals.copy()
    aligned_regimes = regimes.reindex(signals.index).fillna('Sideways')

    if overlay_type == 'bear_only':
        bear_mask = aligned_regimes == 'Bear'
        overlay.loc[bear_mask] = 0

    elif overlay_type == 'aggressive':
        bear_mask = aligned_regimes == 'Bear'
        sideways_mask = aligned_regimes == 'Sideways'
        overlay.loc[bear_mask] = 0
        overlay.loc[sideways_mask] *= 0.5

    elif overlay_type == 'trend_only':
        # Even simpler: use only the 63-day trend direction, ignore vol
        # Negative 63-day return → cash. This is a common "trend filter" in the literature.
        # Re-derive from signals index (we need market index for this)
        # This is computed in the main analysis function below
        pass  # Will be handled separately

    return overlay


# ─── Performance Metrics ──────────────────────────────────────────────────────

def compute_returns_from_signals(signals: pd.DataFrame, prices: pd.DataFrame) -> pd.Series:
    """Apply shifted signals to price returns and subtract transaction costs."""
    all_returns = prices.pct_change()
    shifted = signals.shift(1).fillna(0)
    strategy_returns = (shifted * all_returns).sum(axis=1)

    # Turnover-based costs
    turnover = shifted.diff().abs().sum(axis=1) / 2
    costs = turnover * (COMMISSION_BPS + SLIPPAGE_BPS) / 10000
    return (strategy_returns - costs).fillna(0)


def sharpe(returns, rf=RISK_FREE_RATE):
    if len(returns) < 5:
        return 0.0
    excess = returns - rf / 252
    std = excess.std()
    # Near-zero std means basically flat (in cash) — return 0
    if std < 1e-8:
        return 0.0
    sr = float(np.sqrt(252) * excess.mean() / std)
    # Guard against numerical blowup
    if np.isnan(sr) or np.isinf(sr) or abs(sr) > 1000:
        return 0.0
    return sr


def max_drawdown(returns):
    equity = (1 + returns).cumprod()
    rolling_max = equity.cummax()
    dd = (equity - rolling_max) / rolling_max
    return float(dd.min())


def annual_return(returns):
    if len(returns) < 10:
        return 0.0
    total = (1 + returns).prod()
    n_years = len(returns) / 252
    if n_years <= 0 or total <= 0:
        return 0.0
    return float(total ** (1 / n_years) - 1)


def regime_sharpe(returns: pd.Series, regimes: pd.Series, target_regime: str) -> float:
    """Sharpe ratio of the strategy during a specific market regime."""
    mask = regimes.reindex(returns.index) == target_regime
    r = returns[mask]
    if len(r) < 10:
        return 0.0
    return sharpe(r)


def compute_full_metrics(returns: pd.Series, regimes: pd.Series) -> dict:
    return {
        'sharpe': sharpe(returns),
        'annual_return': annual_return(returns),
        'max_drawdown': max_drawdown(returns),
        'sharpe_bull': regime_sharpe(returns, regimes, 'Bull'),
        'sharpe_bear': regime_sharpe(returns, regimes, 'Bear'),
        'sharpe_highvol': regime_sharpe(returns, regimes, 'High-Vol'),
        'sharpe_sideways': regime_sharpe(returns, regimes, 'Sideways'),
    }


# ─── Core Analysis ────────────────────────────────────────────────────────────

def analyze_strategy(strategy_key: str, data: pd.DataFrame,
                     regimes: pd.Series, trend_mask: pd.Series) -> dict:
    """Run baseline + three overlays for one strategy."""

    logger.info(f"  Analyzing {strategy_key}...")

    # Get strategy signals (no backtest engine — we'll apply costs manually)
    strategy = get_strategy(strategy_key, data)
    raw_signals = strategy.generate_signals()

    # Align signals to price index
    prices = data.pivot(index='date', columns='symbol', values='close')
    raw_signals = raw_signals.reindex(prices.index).ffill().fillna(0)

    # ── Baseline (no overlay) ─────────────────────────────────────────────────
    baseline_returns = compute_returns_from_signals(raw_signals, prices)
    baseline_metrics = compute_full_metrics(baseline_returns, regimes)

    # ── Overlay 1: Bear-only (cash in Bear) ───────────────────────────────────
    bear_signals = apply_overlay(raw_signals, regimes, 'bear_only')
    bear_returns = compute_returns_from_signals(bear_signals, prices)
    bear_metrics = compute_full_metrics(bear_returns, regimes)

    # ── Overlay 2: Aggressive (cash in Bear, 50% in Sideways) ─────────────────
    agg_signals = apply_overlay(raw_signals, regimes, 'aggressive')
    agg_returns = compute_returns_from_signals(agg_signals, prices)
    agg_metrics = compute_full_metrics(agg_returns, regimes)

    # ── Overlay 3: Trend-only (cash when 63d trend negative) ──────────────────
    trend_signals = raw_signals.copy()
    trend_signals.loc[trend_mask] = 0
    trend_returns = compute_returns_from_signals(trend_signals, prices)
    trend_metrics = compute_full_metrics(trend_returns, regimes)

    # ── Compute improvement scores ────────────────────────────────────────────

    def improvement(overlay_m, base_m):
        return {
            'sharpe_delta': safe_float(overlay_m['sharpe'] - base_m['sharpe']),
            'bear_sharpe_delta': safe_float(overlay_m['sharpe_bear'] - base_m['sharpe_bear']),
            'mdd_delta': safe_float(overlay_m['max_drawdown'] - base_m['max_drawdown']),  # Less negative = better
            'bull_cost': safe_float(overlay_m['sharpe_bull'] - base_m['sharpe_bull']),   # Sharpe lost in bull
            'protection_score': safe_float(
                (overlay_m['sharpe_bear'] - base_m['sharpe_bear'])   # Bear improvement
                + (overlay_m['max_drawdown'] - base_m['max_drawdown']) * 5  # MDD improvement (scaled)
            ),
        }

    return {
        'strategy': strategy_key,
        'baseline': {k: safe_float(v) for k, v in baseline_metrics.items()},
        'bear_only': {k: safe_float(v) for k, v in bear_metrics.items()},
        'aggressive': {k: safe_float(v) for k, v in agg_metrics.items()},
        'trend_only': {k: safe_float(v) for k, v in trend_metrics.items()},
        'improvement_bear_only': improvement(bear_metrics, baseline_metrics),
        'improvement_aggressive': improvement(agg_metrics, baseline_metrics),
        'improvement_trend_only': improvement(trend_metrics, baseline_metrics),
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) > 1:
        strategy_keys = [sys.argv[1]]
        if strategy_keys[0] not in STRATEGY_REGISTRY:
            print(f"Unknown strategy: {strategy_keys[0]}")
            sys.exit(1)
    else:
        strategy_keys = list(STRATEGY_REGISTRY.keys())

    data_path = PROJECT_ROOT / 'data_processed' / 'prices_clean.parquet'
    logger.info(f"Loading data...")
    data = pd.read_parquet(data_path)
    logger.info(f"Loaded {len(data):,} rows, {data['symbol'].nunique()} symbols")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Compute market regime signals ONCE (shared across all strategies)
    logger.info("Computing market regimes...")
    market_returns = compute_market_index(data)
    regimes = classify_regimes(market_returns)

    # Trend-only mask: 63-day cumulative return < 0
    cum_return_63d = (1 + market_returns).rolling(63).apply(lambda x: x.prod() - 1, raw=True)
    trend_mask = cum_return_63d < 0

    # Regime summary
    regime_counts = regimes.value_counts()
    total_days = len(regimes)
    logger.info(f"\nRegime breakdown:")
    for regime, count in sorted(regime_counts.items()):
        logger.info(f"  {regime:10}: {count:4d} days ({count/total_days:.1%})")

    # Trend mask: how many days we'd be in cash
    trend_cash_days = trend_mask.sum()
    logger.info(f"  Trend overlay (neg 63d return): {trend_cash_days} cash days ({trend_cash_days/total_days:.1%})")

    logger.info(f"\n{'='*75}")
    logger.info("REGIME OVERLAY ANALYSIS — THREE VARIANTS")
    logger.info(f"{'='*75}\n")

    all_results = []
    t0 = time.time()

    for key in strategy_keys:
        result = analyze_strategy(key, data, regimes, trend_mask)
        all_results.append(result)
        out_path = RESULTS_DIR / f"{key}.json"
        with open(out_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)

    elapsed = time.time() - t0

    # ── Print Summary ─────────────────────────────────────────────────────────

    logger.info(f"\n{'='*75}")
    logger.info(f"RESULTS SUMMARY  ({elapsed:.1f}s)")
    logger.info(f"{'='*75}\n")

    # Overall Sharpe comparison
    header = f"{'Strategy':<28} {'Base SR':>7} {'Bear-Only':>9} {'Aggressive':>10} {'Trend':>7} {'Best':>8}"
    logger.info(header)
    logger.info("-" * len(header))

    for r in all_results:
        b = r['baseline']['sharpe'] or 0
        bo = r['bear_only']['sharpe'] or 0
        ag = r['aggressive']['sharpe'] or 0
        tr = r['trend_only']['sharpe'] or 0
        best_val = max(b, bo, ag, tr)
        best_name = ['Base', 'Bear-Only', 'Aggressive', 'Trend'][
            [b, bo, ag, tr].index(best_val)
        ]
        bo_sign = '+' if bo > b else ''
        ag_sign = '+' if ag > b else ''
        tr_sign = '+' if tr > b else ''
        logger.info(
            f"{r['strategy']:<28} {b:>7.2f} "
            f"{bo:>+8.2f} ({bo_sign}{bo-b:.2f}) "
            f"{ag:>+9.2f} ({ag_sign}{ag-b:.2f}) "
            f"{tr:>+6.2f} ({tr_sign}{tr-b:.2f}) "
            f"  [{best_name}]"
        )

    # Bear regime improvement
    logger.info(f"\n{'─'*75}")
    logger.info("BEAR REGIME SHARPE — BASELINE vs OVERLAYS:")
    logger.info(f"{'Strategy':<28} {'Base Bear':>9} {'Bear-Only':>9} {'Aggressive':>10} {'Trend':>7}")
    logger.info("-" * 65)

    for r in all_results:
        b_bear = r['baseline']['sharpe_bear'] or 0
        bo_bear = r['bear_only']['sharpe_bear'] or 0
        ag_bear = r['aggressive']['sharpe_bear'] or 0
        tr_bear = r['trend_only']['sharpe_bear'] or 0
        logger.info(
            f"{r['strategy']:<28} {b_bear:>9.2f} {bo_bear:>9.2f} {ag_bear:>10.2f} {tr_bear:>7.2f}"
        )

    # Max drawdown improvement
    logger.info(f"\n{'─'*75}")
    logger.info("MAX DRAWDOWN — BASELINE vs BEST OVERLAY:")
    logger.info(f"{'Strategy':<28} {'Base MDD':>9} {'Best MDD':>9} {'Improvement':>12}")
    logger.info("-" * 60)

    for r in all_results:
        b_mdd = r['baseline']['max_drawdown'] or 0
        bo_mdd = r['bear_only']['max_drawdown'] or 0
        ag_mdd = r['aggressive']['max_drawdown'] or 0
        tr_mdd = r['trend_only']['max_drawdown'] or 0
        best_mdd = max(bo_mdd, ag_mdd, tr_mdd)  # max = least negative
        improvement = best_mdd - b_mdd
        logger.info(
            f"{r['strategy']:<28} {b_mdd:>9.2%} {best_mdd:>9.2%} {improvement:>+12.2%}"
        )

    # Key insights
    logger.info(f"\n{'─'*75}")
    logger.info("KEY INSIGHTS:")

    # Count strategies improved overall Sharpe
    improved_bear = sum(
        1 for r in all_results
        if (r['bear_only']['sharpe'] or 0) > (r['baseline']['sharpe'] or 0)
    )
    improved_mdd = sum(
        1 for r in all_results
        if (r['bear_only']['max_drawdown'] or 0) > (r['baseline']['max_drawdown'] or 0)
    )
    logger.info(f"  Bear-only overlay improves overall Sharpe: {improved_bear}/{len(all_results)} strategies")
    logger.info(f"  Bear-only overlay reduces max drawdown: {improved_mdd}/{len(all_results)} strategies")

    # Average Bear Sharpe improvement
    avg_base_bear = np.mean([r['baseline']['sharpe_bear'] or 0 for r in all_results])
    avg_bo_bear = np.mean([r['bear_only']['sharpe_bear'] or 0 for r in all_results])
    logger.info(f"  Average Bear Sharpe: {avg_base_bear:.2f} → {avg_bo_bear:.2f} (bear-only overlay)")
    logger.info(f"  (Bear-only should be ~0.0 since we're in cash during Bear periods)")

    # Cost of protection: average Bull Sharpe drop
    avg_base_bull = np.mean([r['baseline']['sharpe_bull'] or 0 for r in all_results])
    avg_bo_bull = np.mean([r['bear_only']['sharpe_bull'] or 0 for r in all_results])
    logger.info(f"  Average Bull Sharpe (no cost): {avg_base_bull:.2f} → {avg_bo_bull:.2f}")
    logger.info(f"  (Bull Sharpe should be unchanged — we only remove Bear positions)")

    # Save summary
    summary = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'regime_breakdown': {r: int(regime_counts.get(r, 0)) for r in ['Bull', 'Bear', 'High-Vol', 'Sideways']},
        'trend_cash_days': int(trend_cash_days),
        'n_strategies': len(all_results),
        'strategies': {r['strategy']: r for r in all_results},
    }

    with open(RESULTS_DIR / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    # CSV
    rows = []
    for r in all_results:
        rows.append({
            'strategy': r['strategy'],
            'base_sharpe': r['baseline']['sharpe'],
            'bear_only_sharpe': r['bear_only']['sharpe'],
            'aggressive_sharpe': r['aggressive']['sharpe'],
            'trend_only_sharpe': r['trend_only']['sharpe'],
            'base_mdd': r['baseline']['max_drawdown'],
            'bear_only_mdd': r['bear_only']['max_drawdown'],
            'base_bear_sharpe': r['baseline']['sharpe_bear'],
            'bear_only_bear_sharpe': r['bear_only']['sharpe_bear'],
            'base_bull_sharpe': r['baseline']['sharpe_bull'],
            'bear_only_bull_sharpe': r['bear_only']['sharpe_bull'],
            'sharpe_improvement': (r['bear_only']['sharpe'] or 0) - (r['baseline']['sharpe'] or 0),
            'mdd_improvement': (r['bear_only']['max_drawdown'] or 0) - (r['baseline']['max_drawdown'] or 0),
        })

    pd.DataFrame(rows).to_csv(RESULTS_DIR / 'overlay_results.csv', index=False)

    logger.info(f"\nResults saved to {RESULTS_DIR}/")
    logger.info(f"Done in {elapsed:.1f}s")


if __name__ == '__main__':
    main()
