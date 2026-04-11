"""
Strategy Correlation & Portfolio Analysis (Phase 2.7)

Answers: "Which strategies are truly different, and how should we combine them?"

What we compute:
  1. Full 14×14 correlation matrix of daily strategy returns
  2. Clustering: which strategies are redundant vs complementary
  3. Diversification benefit: portfolio volatility vs individual
  4. Five portfolio variants and their performance:
       - Equal-weight (1/14 each)
       - Tier 1 only (top 5 from all prior tests)
       - Risk-parity (weight by inverse volatility)
       - Minimum correlation (weight to minimize average pairwise correlation)
       - Top 3 lowest-correlation picks
  5. Benchmark comparison (equal-weighted S&P 500 index)

Key insight this delivers: are our 14 strategies genuinely diversified, or are they
all basically "long large-cap US equities with slightly different sorting rules"?

Usage:
    .venv/bin/python scripts/portfolio_analysis.py
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

COMMISSION_BPS = 10
SLIPPAGE_BPS = 5
RISK_FREE_RATE = 0.02
RESULTS_DIR = PROJECT_ROOT / 'results' / 'portfolio_analysis'

# ── Tier 1 strategies from all prior Phase 2 tests ────────────────────────────
TIER_1 = [
    'large_cap_momentum',
    '52_week_high_breakout',
    'quality_momentum',
    'composite_factor_score',
    'low_volatility_shield',
]

TIER_1_AND_2 = TIER_1 + [
    'value_momentum_blend',
    'quality_low_vol',
    'high_quality_roic',
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


def get_market_benchmark(data: pd.DataFrame, prices: pd.DataFrame) -> pd.Series:
    """Equal-weighted S&P 500 daily return (our benchmark)."""
    return prices.pct_change().mean(axis=1).rename('benchmark')


# ── Performance metrics ────────────────────────────────────────────────────────

def sharpe(returns, rf=RISK_FREE_RATE):
    excess = returns - rf / 252
    std = excess.std()
    if std < 1e-10:
        return 0.0
    sr = float(np.sqrt(252) * excess.mean() / std)
    return sr if not (np.isnan(sr) or np.isinf(sr)) else 0.0


def annual_return(returns):
    total = (1 + returns).prod()
    n_years = len(returns) / 252
    if n_years <= 0 or total <= 0:
        return 0.0
    return float(total ** (1 / n_years) - 1)


def max_drawdown(returns):
    equity = (1 + returns).cumprod()
    dd = (equity / equity.cummax() - 1)
    return float(dd.min())


def ann_volatility(returns):
    return float(returns.std() * np.sqrt(252))


def metrics(returns):
    return {
        'sharpe': safe_float(sharpe(returns)),
        'annual_return': safe_float(annual_return(returns)),
        'max_drawdown': safe_float(max_drawdown(returns)),
        'ann_volatility': safe_float(ann_volatility(returns)),
        'total_return': safe_float(float((1 + returns).prod() - 1)),
    }


# ── Portfolio construction ─────────────────────────────────────────────────────

def equal_weight_portfolio(returns_df: pd.DataFrame) -> pd.Series:
    """Simple 1/N equal-weight portfolio."""
    n = len(returns_df.columns)
    return returns_df.mean(axis=1).rename('equal_weight')


def risk_parity_portfolio(returns_df: pd.DataFrame) -> pd.Series:
    """
    Inverse-volatility weights: weight_i = (1/vol_i) / sum(1/vol_j)
    Each strategy contributes equal volatility to the portfolio.
    """
    vols = returns_df.std()
    inv_vols = 1.0 / vols
    weights = inv_vols / inv_vols.sum()
    weighted = (returns_df * weights).sum(axis=1)
    return weighted.rename('risk_parity')


def min_correlation_portfolio(returns_df: pd.DataFrame, n_top: int = 3) -> pd.Series:
    """
    Select the n_top strategies with the lowest average pairwise correlation.
    Equal-weight those selected strategies.

    This maximizes diversification by picking the most orthogonal strategies.
    """
    corr = returns_df.corr()
    # Average correlation per strategy (excluding self-correlation)
    avg_corr = {}
    for col in corr.columns:
        other_corrs = corr[col].drop(col)
        avg_corr[col] = other_corrs.mean()

    # Select n_top lowest avg correlation strategies
    selected = sorted(avg_corr, key=avg_corr.get)[:n_top]
    portfolio = returns_df[selected].mean(axis=1).rename(f'min_corr_top{n_top}')
    return portfolio, selected, avg_corr


# ── Correlation analysis ───────────────────────────────────────────────────────

def cluster_strategies(corr_matrix: pd.DataFrame) -> dict:
    """
    Simple linkage-style clustering using correlation.
    Groups strategies with correlation > 0.8 as "highly correlated" (redundant).
    Groups with correlation < 0.4 as "complementary".
    """
    strategies = list(corr_matrix.columns)
    high_corr_pairs = []
    low_corr_pairs = []

    for i, s1 in enumerate(strategies):
        for j, s2 in enumerate(strategies):
            if j <= i:
                continue
            c = corr_matrix.loc[s1, s2]
            if c > 0.80:
                high_corr_pairs.append((s1, s2, c))
            elif c < 0.40:
                low_corr_pairs.append((s1, s2, c))

    # Sort
    high_corr_pairs.sort(key=lambda x: -x[2])
    low_corr_pairs.sort(key=lambda x: x[2])

    return {
        'high_correlation_pairs': [(s1, s2, round(c, 3)) for s1, s2, c in high_corr_pairs],
        'low_correlation_pairs': [(s1, s2, round(c, 3)) for s1, s2, c in low_corr_pairs],
    }


def diversification_ratio(returns_df: pd.DataFrame,
                           weights: np.ndarray = None) -> float:
    """
    Diversification Ratio = weighted avg individual vol / portfolio vol
    DR > 1 = diversification benefit exists
    DR = 1 = no diversification benefit (all perfectly correlated)
    """
    if weights is None:
        weights = np.ones(len(returns_df.columns)) / len(returns_df.columns)
    individual_vols = returns_df.std().values
    weighted_avg_vol = np.dot(weights, individual_vols)
    portfolio = (returns_df * weights).sum(axis=1)
    portfolio_vol = portfolio.std()
    if portfolio_vol < 1e-10:
        return 1.0
    return float(weighted_avg_vol / portfolio_vol)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    data_path = PROJECT_ROOT / 'data_processed' / 'prices_clean.parquet'
    logger.info("Loading data...")
    data = pd.read_parquet(data_path)
    logger.info(f"Loaded {len(data):,} rows, {data['symbol'].nunique()} symbols")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    prices = data.pivot(index='date', columns='symbol', values='close')

    # ── Step 1: Get all strategy returns ──────────────────────────────────────
    logger.info("\nComputing all strategy returns...")
    all_keys = list(STRATEGY_REGISTRY.keys())

    strategy_returns = {}
    t0 = time.time()
    for key in all_keys:
        logger.info(f"  {key}...")
        r = get_strategy_returns(key, data, prices)
        strategy_returns[key] = r

    benchmark = get_market_benchmark(data, prices)
    returns_df = pd.DataFrame(strategy_returns).dropna()
    logger.info(f"  Done in {time.time()-t0:.1f}s — {len(returns_df)} days")

    # ── Step 2: Correlation matrix ────────────────────────────────────────────
    logger.info("\nComputing correlation matrix...")
    corr_matrix = returns_df.corr()
    clustering = cluster_strategies(corr_matrix)

    # Average inter-strategy correlation (excluding self)
    n = len(corr_matrix)
    mask = ~np.eye(n, dtype=bool)
    avg_inter_corr = float(corr_matrix.values[mask].mean())

    # ── Step 3: Individual strategy metrics ───────────────────────────────────
    individual_metrics = {}
    for key in all_keys:
        individual_metrics[key] = metrics(returns_df[key])

    bench_metrics = metrics(benchmark.reindex(returns_df.index).fillna(0))

    # ── Step 4: Portfolio construction ────────────────────────────────────────
    logger.info("Building portfolios...")

    # A: Equal-weight all 14
    p_equal = equal_weight_portfolio(returns_df)

    # B: Tier 1 only (top 5 from all prior tests)
    p_tier1 = equal_weight_portfolio(returns_df[TIER_1])

    # C: Tier 1+2 (top 8)
    p_tier12 = equal_weight_portfolio(returns_df[TIER_1_AND_2])

    # D: Risk-parity all 14
    p_rp = risk_parity_portfolio(returns_df)

    # E: Risk-parity Tier 1 only
    p_rp_t1 = risk_parity_portfolio(returns_df[TIER_1])

    # F: Min-correlation top 3
    p_mincorr, mincorr_selected, avg_corr_per_strategy = min_correlation_portfolio(returns_df, n_top=3)

    # G: Min-correlation top 5
    p_mincorr5, mincorr5_selected, _ = min_correlation_portfolio(returns_df, n_top=5)

    portfolios = {
        'equal_weight_all14': p_equal,
        'tier1_equal_weight': p_tier1,
        'tier1and2_equal_weight': p_tier12,
        'risk_parity_all14': p_rp,
        'risk_parity_tier1': p_rp_t1,
        'min_corr_top3': p_mincorr,
        'min_corr_top5': p_mincorr5,
    }

    portfolio_metrics = {name: metrics(p) for name, p in portfolios.items()}

    # Diversification ratios
    dr_equal = diversification_ratio(returns_df)
    dr_tier1 = diversification_ratio(returns_df[TIER_1])
    dr_rp = diversification_ratio(
        returns_df,
        weights=(1.0 / returns_df.std().values) / (1.0 / returns_df.std().values).sum()
    )

    # ── Step 5: Print Results ─────────────────────────────────────────────────

    logger.info(f"\n{'='*75}")
    logger.info("PORTFOLIO ANALYSIS RESULTS")
    logger.info(f"{'='*75}\n")

    # Correlation overview
    logger.info(f"CORRELATION OVERVIEW:")
    logger.info(f"  Average inter-strategy correlation: {avg_inter_corr:.3f}")
    logger.info(f"  Diversification ratio (equal-weight): {dr_equal:.3f}")
    logger.info(f"  Diversification ratio (Tier 1 only): {dr_tier1:.3f}")
    logger.info(f"  Diversification ratio (risk-parity): {dr_rp:.3f}")

    # Full correlation matrix (abbreviated — just show avg corr per strategy)
    logger.info(f"\nAVERAGE PAIRWISE CORRELATION PER STRATEGY:")
    logger.info(f"{'Strategy':<30} {'Avg Corr':>10} {'With Mkt':>10}")
    logger.info("-" * 52)
    bench_aligned = benchmark.reindex(returns_df.index).fillna(0)
    for key in all_keys:
        avg_c = float(corr_matrix[key].drop(key).mean())
        with_mkt = float(returns_df[key].corr(bench_aligned))
        logger.info(f"{key:<30} {avg_c:>10.3f} {with_mkt:>10.3f}")

    # Highly correlated pairs
    if clustering['high_correlation_pairs']:
        logger.info(f"\nHIGHLY CORRELATED PAIRS (>0.80) — may be redundant:")
        for s1, s2, c in clustering['high_correlation_pairs'][:10]:
            logger.info(f"  {s1:30} ↔ {s2:30}  r={c:.3f}")
    else:
        logger.info(f"\nNo pairs with correlation > 0.80")

    # Low correlation pairs (complementary)
    if clustering['low_correlation_pairs']:
        logger.info(f"\nLOWEST CORRELATION PAIRS — most complementary:")
        for s1, s2, c in clustering['low_correlation_pairs'][:10]:
            logger.info(f"  {s1:30} ↔ {s2:30}  r={c:.3f}")

    # Portfolio comparison
    logger.info(f"\n{'─'*75}")
    logger.info("PORTFOLIO PERFORMANCE COMPARISON:")
    header = f"{'Portfolio':<28} {'Sharpe':>7} {'Ann Ret':>8} {'MDD':>8} {'AnnVol':>8}"
    logger.info(header)
    logger.info("-" * len(header))

    # Benchmark first
    bm = bench_metrics
    logger.info(f"{'[Benchmark EW S&P500]':<28} {bm['sharpe']:>7.2f} {bm['annual_return']:>8.2%} {bm['max_drawdown']:>8.2%} {bm['ann_volatility']:>8.2%}")
    logger.info("-" * len(header))

    for name, m in portfolio_metrics.items():
        logger.info(f"{name:<28} {m['sharpe']:>7.2f} {m['annual_return']:>8.2%} {m['max_drawdown']:>8.2%} {m['ann_volatility']:>8.2%}")

    # Individual strategies (for reference)
    logger.info(f"\nINDIVIDUAL STRATEGY PERFORMANCE (for reference):")
    logger.info(f"{'Strategy':<30} {'Sharpe':>7} {'Ann Ret':>8} {'MDD':>8}")
    logger.info("-" * 55)
    sorted_strats = sorted(individual_metrics.items(), key=lambda x: x[1]['sharpe'] or 0, reverse=True)
    for key, m in sorted_strats:
        logger.info(f"{key:<30} {m['sharpe']:>7.2f} {m['annual_return']:>8.2%} {m['max_drawdown']:>8.2%}")

    # Min-corr selections
    logger.info(f"\nMIN-CORRELATION SELECTION:")
    logger.info(f"  Top 3 most orthogonal strategies: {mincorr_selected}")
    logger.info(f"  Top 5 most orthogonal strategies: {mincorr5_selected}")

    # Key insights
    logger.info(f"\n{'─'*75}")
    logger.info("KEY INSIGHTS:")

    best_portfolio = max(portfolio_metrics.items(), key=lambda x: x[1]['sharpe'] or 0)
    best_mdd_portfolio = max(portfolio_metrics.items(), key=lambda x: x[1]['max_drawdown'] or -999)
    logger.info(f"  Best Sharpe portfolio: {best_portfolio[0]} ({best_portfolio[1]['sharpe']:.2f})")
    logger.info(f"  Best MDD portfolio: {best_mdd_portfolio[0]} ({best_mdd_portfolio[1]['max_drawdown']:.2%})")
    logger.info(f"  Benchmark Sharpe: {bench_metrics['sharpe']:.2f} — all portfolios vs this")

    n_high = len(clustering['high_correlation_pairs'])
    n_low = len(clustering['low_correlation_pairs'])
    logger.info(f"  Redundant pairs (>0.80 corr): {n_high}")
    logger.info(f"  Complementary pairs (<0.40 corr): {n_low}")
    logger.info(f"  Average inter-strategy corr: {avg_inter_corr:.3f}")
    if avg_inter_corr > 0.7:
        logger.info(f"  → HIGH average correlation: strategies are similar bets, limited diversification")
    elif avg_inter_corr > 0.5:
        logger.info(f"  → MODERATE correlation: some diversification benefit")
    else:
        logger.info(f"  → LOW correlation: good diversification across strategies")

    # ── Save results ──────────────────────────────────────────────────────────
    corr_dict = {}
    for c in corr_matrix.columns:
        corr_dict[c] = {r: safe_float(corr_matrix.loc[c, r]) for r in corr_matrix.index}

    summary = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'avg_inter_strategy_correlation': safe_float(avg_inter_corr),
        'diversification_ratios': {
            'equal_weight_all14': safe_float(dr_equal),
            'tier1_equal_weight': safe_float(dr_tier1),
            'risk_parity_all14': safe_float(dr_rp),
        },
        'clustering': {
            'high_corr_pairs': clustering['high_correlation_pairs'],
            'low_corr_pairs': clustering['low_correlation_pairs'][:20],
        },
        'min_corr_selections': {
            'top3': mincorr_selected,
            'top5': mincorr5_selected,
        },
        'benchmark': bench_metrics,
        'portfolios': portfolio_metrics,
        'individual': individual_metrics,
        'correlation_matrix': corr_dict,
        'avg_corr_per_strategy': {k: safe_float(v) for k, v in avg_corr_per_strategy.items()},
    }

    with open(RESULTS_DIR / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    # CSV: portfolio comparison
    rows = [{'portfolio': 'benchmark', **bench_metrics}]
    for name, m in portfolio_metrics.items():
        rows.append({'portfolio': name, **m})
    pd.DataFrame(rows).to_csv(RESULTS_DIR / 'portfolio_comparison.csv', index=False)

    # CSV: correlation matrix
    corr_matrix.to_csv(RESULTS_DIR / 'correlation_matrix.csv')

    # CSV: individual strategy metrics
    ind_rows = [{'strategy': k, **v} for k, v in individual_metrics.items()]
    pd.DataFrame(ind_rows).to_csv(RESULTS_DIR / 'individual_metrics.csv', index=False)

    elapsed = time.time() - t0
    logger.info(f"\nResults saved to {RESULTS_DIR}/")
    logger.info(f"Total time: {elapsed:.1f}s")


if __name__ == '__main__':
    main()
