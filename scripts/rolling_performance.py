"""
Rolling Performance Analysis (Phase 2.8)

Answers: "Is strategy performance stable over time, or concentrated in specific sub-periods?"

What we compute:
  1. Rolling 126-day (6-month) Sharpe ratio for each strategy
  2. Rolling 126-day max drawdown (trailing)
  3. Rolling 126-day annualized volatility
  4. Rolling average inter-strategy correlation (126-day window)
  5. Rolling strategy rank stability — do the best strategies stay best?
  6. Sub-period performance breakdown: split 4yr window into 8× 6-month blocks

Key insight: If a strategy's rolling Sharpe is +2.0 for 6 months then -0.5 for 18 months,
its overall Sharpe of 0.9 is misleading — performance is concentrated, not stable.

Usage:
    .venv/bin/python scripts/rolling_performance.py
"""

import sys
import json
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

COMMISSION_BPS = 10
SLIPPAGE_BPS = 5
RISK_FREE_RATE = 0.02
ROLLING_WINDOW = 126   # 6 months of trading days
RESULTS_DIR = PROJECT_ROOT / 'results' / 'rolling_performance'

ALL_STRATEGIES = list(STRATEGY_REGISTRY.keys())

TIER_1 = [
    'large_cap_momentum',
    '52_week_high_breakout',
    'quality_momentum',
    'composite_factor_score',
    'low_volatility_shield',
]


def safe_float(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return round(float(v), 6)


# ── Return computation ─────────────────────────────────────────────────────────

def get_strategy_returns(strategy_key: str, data: pd.DataFrame,
                         prices: pd.DataFrame) -> pd.Series:
    """Get daily net returns for one strategy."""
    strategy = get_strategy(strategy_key, data)
    signals = strategy.generate_signals()
    signals = signals.reindex(prices.index).ffill().fillna(0)

    all_returns = prices.pct_change()
    shifted = signals.shift(1).fillna(0)
    strategy_returns = (shifted * all_returns).sum(axis=1)

    turnover = shifted.diff().abs().sum(axis=1) / 2
    costs = turnover * (COMMISSION_BPS + SLIPPAGE_BPS) / 10000
    return (strategy_returns - costs).fillna(0).rename(strategy_key)


# ── Rolling metrics ────────────────────────────────────────────────────────────

def rolling_sharpe(returns: pd.Series, window: int = ROLLING_WINDOW) -> pd.Series:
    """Rolling annualized Sharpe ratio."""
    rf_daily = RISK_FREE_RATE / 252
    excess = returns - rf_daily
    roll_mean = excess.rolling(window).mean()
    roll_std = excess.rolling(window).std()
    result = np.sqrt(252) * roll_mean / roll_std
    result[roll_std < 1e-10] = 0.0
    result[np.isinf(result)] = 0.0
    return result


def rolling_max_drawdown(returns: pd.Series, window: int = ROLLING_WINDOW) -> pd.Series:
    """Rolling trailing max drawdown."""
    equity = (1 + returns).cumprod()
    # For each point, compute the MDD of the preceding window
    mdd_series = pd.Series(index=returns.index, dtype=float)
    for i in range(window, len(equity) + 1):
        window_equity = equity.iloc[i - window:i]
        mdd_series.iloc[i - 1] = float((window_equity / window_equity.cummax() - 1).min())
    return mdd_series


def rolling_volatility(returns: pd.Series, window: int = ROLLING_WINDOW) -> pd.Series:
    """Rolling annualized volatility."""
    return returns.rolling(window).std() * np.sqrt(252)


def rolling_avg_correlation(returns_df: pd.DataFrame, window: int = ROLLING_WINDOW) -> pd.Series:
    """
    Rolling average pairwise correlation across all strategy pairs.
    Computed by taking the mean of all off-diagonal entries of the
    rolling correlation matrix at each point in time.
    """
    avg_corr = pd.Series(index=returns_df.index, dtype=float)

    for i in range(window, len(returns_df) + 1):
        window_data = returns_df.iloc[i - window:i]
        corr_matrix = window_data.corr()
        # Extract upper triangle (off-diagonal)
        upper = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        ).stack()
        avg_corr.iloc[i - 1] = float(upper.mean()) if len(upper) > 0 else np.nan

    return avg_corr


# ── Sub-period analysis ────────────────────────────────────────────────────────

def sub_period_performance(returns: pd.Series, n_periods: int = 8):
    """
    Split the full return series into n_periods equal sub-periods and compute
    Sharpe, CAGR, and MDD for each sub-period.
    """
    total_days = len(returns)
    period_len = total_days // n_periods
    results = []

    for i in range(n_periods):
        start = i * period_len
        end = (i + 1) * period_len if i < n_periods - 1 else total_days
        period_ret = returns.iloc[start:end]

        if len(period_ret) < 20:
            continue

        period_start_date = str(period_ret.index[0].date())
        period_end_date = str(period_ret.index[-1].date())

        excess = period_ret - RISK_FREE_RATE / 252
        std = excess.std()
        sr = float(np.sqrt(252) * excess.mean() / std) if std > 1e-10 else 0.0
        if np.isnan(sr) or np.isinf(sr):
            sr = 0.0

        total = float((1 + period_ret).prod())
        n_years = len(period_ret) / 252
        cagr = float(total ** (1 / n_years) - 1) if total > 0 and n_years > 0 else 0.0

        equity = (1 + period_ret).cumprod()
        mdd = float((equity / equity.cummax() - 1).min())

        results.append({
            'period': i + 1,
            'start': period_start_date,
            'end': period_end_date,
            'sharpe': safe_float(sr),
            'cagr': safe_float(cagr),
            'max_drawdown': safe_float(mdd),
            'n_days': len(period_ret),
        })

    return results


# ── Rank stability ────────────────────────────────────────────────────────────

def rank_stability(rolling_sharpe_df: pd.DataFrame) -> dict:
    """
    Measure how stable strategy rankings are over time.
    Uses Spearman rank correlation between consecutive 126-day rolling windows.
    High rank stability = same strategies consistently on top.
    Low rank stability = rank ordering changes frequently.
    """
    # For each date, rank strategies by rolling Sharpe (1 = best)
    ranks = rolling_sharpe_df.rank(axis=1, ascending=False, method='average')
    ranks = ranks.dropna(how='all')

    # Month-end ranks only (to reduce noise)
    monthly_ranks = ranks.resample('M').last()
    monthly_ranks = monthly_ranks.dropna(how='all')

    # Spearman correlation between consecutive months
    from scipy.stats import spearmanr
    corrs = []
    for i in range(1, len(monthly_ranks)):
        prev = monthly_ranks.iloc[i - 1]
        curr = monthly_ranks.iloc[i]
        # Only use strategies that are ranked in both periods
        valid = prev.notna() & curr.notna()
        if valid.sum() >= 5:
            corr, _ = spearmanr(prev[valid], curr[valid])
            if not np.isnan(corr):
                corrs.append(float(corr))

    avg_rank_corr = float(np.mean(corrs)) if corrs else 0.0
    return {
        'avg_rank_correlation': safe_float(avg_rank_corr),
        'n_monthly_periods': len(monthly_ranks),
        'interpretation': (
            'STABLE (top strategies stay on top)' if avg_rank_corr > 0.6 else
            'MODERATE (some rank changes)' if avg_rank_corr > 0.3 else
            'UNSTABLE (rankings change frequently)'
        )
    }


# ── Main analysis ──────────────────────────────────────────────────────────────

def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load price data
    logger.info("Loading price data...")
    data_path = PROJECT_ROOT / 'data_processed' / 'prices_clean.parquet'
    data = pd.read_parquet(data_path)
    data.index = pd.to_datetime(data.index)

    prices_wide = data.pivot_table(index='date', columns='symbol', values='close')
    prices_wide = prices_wide.sort_index()

    logger.info(f"Price data: {prices_wide.shape[0]} days × {prices_wide.shape[1]} symbols")

    # ── Step 1: Compute all strategy returns ───────────────────────────────────
    logger.info("Computing strategy returns for all 14 strategies...")
    all_returns = {}
    for i, key in enumerate(ALL_STRATEGIES):
        logger.info(f"  [{i+1:2d}/14] {key}")
        try:
            ret = get_strategy_returns(key, data, prices_wide)
            all_returns[key] = ret
        except Exception as e:
            logger.warning(f"    FAILED: {e}")

    returns_df = pd.DataFrame(all_returns).dropna(how='all')
    logger.info(f"Returns matrix: {returns_df.shape[0]} days × {returns_df.shape[1]} strategies")

    # Market benchmark
    benchmark = prices_wide.pct_change().mean(axis=1).rename('benchmark')
    benchmark = benchmark.reindex(returns_df.index).fillna(0)

    # ── Step 2: Rolling Sharpe ─────────────────────────────────────────────────
    logger.info("Computing rolling Sharpe ratios (126-day window)...")
    rolling_sr = pd.DataFrame()
    for key in all_returns:
        rolling_sr[key] = rolling_sharpe(returns_df[key])

    # Save rolling Sharpe
    rolling_sr.to_csv(RESULTS_DIR / 'rolling_sharpe.csv')
    logger.info("  Saved rolling_sharpe.csv")

    # ── Step 3: Rolling Drawdown ───────────────────────────────────────────────
    logger.info("Computing rolling max drawdown (126-day trailing)...")
    rolling_mdd = pd.DataFrame()
    for key in all_returns:
        rolling_mdd[key] = rolling_max_drawdown(returns_df[key])

    rolling_mdd.to_csv(RESULTS_DIR / 'rolling_drawdown.csv')
    logger.info("  Saved rolling_drawdown.csv")

    # ── Step 4: Rolling Volatility ─────────────────────────────────────────────
    logger.info("Computing rolling volatility...")
    rolling_vol = pd.DataFrame()
    for key in all_returns:
        rolling_vol[key] = rolling_volatility(returns_df[key])

    rolling_vol.to_csv(RESULTS_DIR / 'rolling_volatility.csv')
    logger.info("  Saved rolling_volatility.csv")

    # ── Step 5: Rolling avg inter-strategy correlation ────────────────────────
    logger.info("Computing rolling average inter-strategy correlation...")
    # Use Tier 1 strategies only for speed and signal clarity
    tier1_returns = returns_df[[k for k in TIER_1 if k in returns_df.columns]]
    rolling_avg_corr = rolling_avg_correlation(tier1_returns)
    rolling_avg_corr.to_csv(RESULTS_DIR / 'rolling_avg_correlation.csv', header=['avg_correlation'])
    logger.info("  Saved rolling_avg_correlation.csv")

    # ── Step 6: Rank stability ─────────────────────────────────────────────────
    logger.info("Computing rank stability...")
    rank_stability_result = rank_stability(rolling_sr)
    logger.info(f"  Rank stability: {rank_stability_result['interpretation']}")
    logger.info(f"  Avg rank correlation: {rank_stability_result['avg_rank_correlation']:.3f}")

    # ── Step 7: Sub-period breakdown ──────────────────────────────────────────
    logger.info("Computing sub-period performance (8 × 6-month blocks)...")
    sub_period_results = {}
    for key in all_returns:
        sub_period_results[key] = sub_period_performance(returns_df[key], n_periods=8)

    # Also compute for benchmark
    sub_period_results['benchmark'] = sub_period_performance(benchmark, n_periods=8)

    # ── Step 8: Rolling Sharpe summary stats ──────────────────────────────────
    logger.info("Summarizing rolling Sharpe statistics...")
    rolling_summary = {}
    for key in all_returns:
        sr_series = rolling_sr[key].dropna()
        if len(sr_series) < 10:
            continue
        rolling_summary[key] = {
            'mean_rolling_sharpe': safe_float(sr_series.mean()),
            'std_rolling_sharpe': safe_float(sr_series.std()),
            'min_rolling_sharpe': safe_float(sr_series.min()),
            'max_rolling_sharpe': safe_float(sr_series.max()),
            'pct_positive': safe_float(float((sr_series > 0).mean())),
            'pct_above_1': safe_float(float((sr_series > 1.0).mean())),
            'pct_below_neg1': safe_float(float((sr_series < -1.0).mean())),
            # Sharpe stability: low std = consistently good; high std = volatile quality
            'sharpe_stability_ratio': safe_float(
                float(sr_series.mean() / sr_series.std())
                if sr_series.std() > 1e-10 else 0.0
            ),
        }

    # ── Step 9: Identify best/worst sub-periods ───────────────────────────────
    logger.info("Identifying best and worst sub-periods for each strategy...")
    best_worst = {}
    for key in all_returns:
        if key not in sub_period_results:
            continue
        periods = sub_period_results[key]
        if not periods:
            continue
        by_sharpe = sorted(periods, key=lambda x: x['sharpe'] or -99, reverse=True)
        best = by_sharpe[0]
        worst = by_sharpe[-1]
        best_worst[key] = {
            'best_period': best['period'],
            'best_start': best['start'],
            'best_end': best['end'],
            'best_sharpe': best['sharpe'],
            'worst_period': worst['period'],
            'worst_start': worst['start'],
            'worst_end': worst['end'],
            'worst_sharpe': worst['sharpe'],
            'sharpe_range': safe_float((best['sharpe'] or 0) - (worst['sharpe'] or 0)),
        }

    # ── Step 10: Crisis sub-period analysis ──────────────────────────────────
    # Identify which 6-month block had worst cross-strategy performance
    logger.info("Identifying worst-performing sub-period across strategies...")
    period_avg_sharpe = {}
    for key in all_returns:
        if key not in sub_period_results:
            continue
        for p in sub_period_results[key]:
            pid = p['period']
            if pid not in period_avg_sharpe:
                period_avg_sharpe[pid] = {
                    'start': p['start'],
                    'end': p['end'],
                    'sharpes': []
                }
            if p['sharpe'] is not None:
                period_avg_sharpe[pid]['sharpes'].append(p['sharpe'])

    period_summary = []
    for pid, info in period_avg_sharpe.items():
        sharpes = info['sharpes']
        if not sharpes:
            continue
        period_summary.append({
            'period': pid,
            'start': info['start'],
            'end': info['end'],
            'avg_sharpe_across_strategies': safe_float(float(np.mean(sharpes))),
            'pct_strategies_positive': safe_float(float(np.mean([s > 0 for s in sharpes]))),
            'min_strategy_sharpe': safe_float(float(np.min(sharpes))),
            'max_strategy_sharpe': safe_float(float(np.max(sharpes))),
        })

    period_summary.sort(key=lambda x: x['period'])

    # ── Assemble final results ────────────────────────────────────────────────
    results = {
        'phase': '2.8',
        'analysis': 'Rolling Performance Analysis',
        'rolling_window_days': ROLLING_WINDOW,
        'n_strategies': len(all_returns),
        'date_range': {
            'start': str(returns_df.index[0].date()),
            'end': str(returns_df.index[-1].date()),
            'n_trading_days': len(returns_df),
        },
        'rolling_sharpe_summary': rolling_summary,
        'sub_period_performance': sub_period_results,
        'period_summary': period_summary,
        'best_worst_periods': best_worst,
        'rank_stability': rank_stability_result,
        'rolling_avg_correlation_stats': {
            'mean': safe_float(float(rolling_avg_corr.dropna().mean())),
            'min': safe_float(float(rolling_avg_corr.dropna().min())),
            'max': safe_float(float(rolling_avg_corr.dropna().max())),
            'std': safe_float(float(rolling_avg_corr.dropna().std())),
        },
    }

    results_path = RESULTS_DIR / 'rolling_performance_results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Results saved to {results_path}")

    # ── Print summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("PHASE 2.8 — ROLLING PERFORMANCE ANALYSIS RESULTS")
    print("=" * 70)

    print(f"\n{'Strategy':<35} {'Mean SR':>8} {'Std SR':>8} {'Min SR':>8} {'Max SR':>8} {'% Pos':>7}")
    print("-" * 76)
    # Sort by mean rolling Sharpe
    sorted_strats = sorted(
        rolling_summary.items(),
        key=lambda x: x[1]['mean_rolling_sharpe'] or -99,
        reverse=True
    )
    for key, s in sorted_strats:
        print(f"{key:<35} {s['mean_rolling_sharpe']:>8.2f} {s['std_rolling_sharpe']:>8.2f} "
              f"{s['min_rolling_sharpe']:>8.2f} {s['max_rolling_sharpe']:>8.2f} "
              f"{s['pct_positive']*100:>6.0f}%")

    print(f"\n{'=' * 70}")
    print("SUB-PERIOD BREAKDOWN (8 × ~6-month blocks)")
    print(f"{'=' * 70}")
    print(f"\n{'Period':<10} {'Date Range':<28} {'Avg SR':>8} {'%Pos':>7} {'Min SR':>8} {'Max SR':>8}")
    print("-" * 70)
    for p in period_summary:
        print(f"P{p['period']:<9} {p['start']} → {p['end']}  "
              f"{p['avg_sharpe_across_strategies']:>8.2f}  "
              f"{p['pct_strategies_positive']*100:>5.0f}%  "
              f"{p['min_strategy_sharpe']:>8.2f}  "
              f"{p['max_strategy_sharpe']:>8.2f}")

    print(f"\n{'=' * 70}")
    print("RANK STABILITY")
    print(f"{'=' * 70}")
    rs = rank_stability_result
    print(f"Average rank correlation:    {rs['avg_rank_correlation']:.3f}")
    print(f"Interpretation:              {rs['interpretation']}")
    print(f"N monthly periods:           {rs['n_monthly_periods']}")

    print(f"\n{'=' * 70}")
    print("ROLLING AVG INTER-STRATEGY CORRELATION (Tier 1 only)")
    print(f"{'=' * 70}")
    rc = results['rolling_avg_correlation_stats']
    print(f"Mean:  {rc['mean']:.3f}   Std: {rc['std']:.3f}   Min: {rc['min']:.3f}   Max: {rc['max']:.3f}")

    print(f"\n{'=' * 70}")
    print("BEST/WORST SUB-PERIOD PER STRATEGY")
    print(f"{'=' * 70}")
    print(f"\n{'Strategy':<35} {'Best SR':>8} {'Worst SR':>8} {'Range':>8}")
    print("-" * 60)
    sorted_bw = sorted(best_worst.items(), key=lambda x: x[1]['sharpe_range'] or 0)
    for key, bw in sorted_bw:
        print(f"{key:<35} {bw['best_sharpe']:>8.2f}  {bw['worst_sharpe']:>8.2f}  {bw['sharpe_range']:>8.2f}")

    print("\n")


if __name__ == '__main__':
    main()
