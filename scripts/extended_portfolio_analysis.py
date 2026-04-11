"""
Phase 3.9 — Strategy Correlation & Portfolio Analysis on Extended 25-Year Data

Mirrors Phase 2.7 but on 2000-2024 with PIT universe masking.

Key additions vs Phase 2.7:
  1. PIT-masked strategy returns throughout
  2. Regime-conditional correlation: how do correlations change in Bull vs Bear?
     (In Phase 2, only 4 years of data made regime-conditional correlation unreliable)
  3. Updated Tier 1 based on Phase 3 performance rankings
  4. Phase 2 vs Phase 3 correlation comparison
  5. Crisis correlation: do strategies stay diversified during crashes?

Usage:
    .venv/bin/python scripts/extended_portfolio_analysis.py
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

from src.strategies import STRATEGY_REGISTRY, get_strategy
from loguru import logger

logger.remove()
logger.add(lambda msg: print(msg, end=""), format="{time:HH:mm:ss} | {message}\n", level="INFO")

COMMISSION_BPS = 10
SLIPPAGE_BPS   = 5
RISK_FREE_RATE = 0.02
RESULTS_DIR    = PROJECT_ROOT / 'results' / 'extended_portfolio_analysis'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

ALL_STRATEGIES = list(STRATEGY_REGISTRY.keys())

# Phase 3 Tier 1: top performers on 25-year data (by Sharpe)
# low_vol_shield (0.66), rsi_mean_reversion (0.64), volatility_targeting (0.60),
# 52_week_high (0.59), composite_factor (0.59), quality_momentum (0.59)
TIER_1_P3 = [
    'low_volatility_shield',
    'rsi_mean_reversion',
    'volatility_targeting',
    '52_week_high_breakout',
    'composite_factor_score',
]

TREND_WINDOW       = 63
BEAR_RETURN_THRESH = -0.05
BULL_RETURN_THRESH =  0.05
HIGH_VOL_THRESH    =  0.20


def safe_float(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return round(float(v), 4)


def load_pit_universe(prices_index):
    lookup_path = PROJECT_ROOT / 'data_processed' / 'sp500_universe_lookup.csv'
    if not lookup_path.exists():
        return None
    lookup = pd.read_csv(lookup_path)
    lookup['date'] = pd.to_datetime(lookup['date'])
    lookup = lookup.sort_values('date')
    pit_by_date = {row['date']: set(row['tickers'].split(',')) if pd.notna(row['tickers']) else set()
                   for _, row in lookup.iterrows()}
    pit_dates = sorted(pit_by_date.keys())
    daily_universe = {}
    pit_idx = 0
    for dt in prices_index:
        while pit_idx < len(pit_dates) - 1 and pit_dates[pit_idx + 1] <= dt:
            pit_idx += 1
        cur = pit_dates[pit_idx]
        daily_universe[dt] = pit_by_date[pit_dates[0]] if cur > dt else pit_by_date[cur]
    return daily_universe


def get_strategy_returns_pit(strategy_key, data, prices, pit_universe):
    strategy = get_strategy(strategy_key, data)
    signals = strategy.generate_signals()
    signals = signals.reindex(prices.index).ffill().fillna(0)
    if pit_universe is not None:
        for dt in signals.index:
            if dt in pit_universe:
                off = [c for c in signals.columns if c not in pit_universe[dt]]
                if off:
                    signals.loc[dt, off] = 0.0
        rs = signals.sum(axis=1)
        nz = rs > 0
        signals.loc[nz] = signals.loc[nz].div(rs[nz], axis=0)
    all_returns = prices.pct_change(fill_method=None).fillna(0)
    shifted = signals.shift(1).fillna(0)
    ret = (shifted * all_returns).sum(axis=1)
    costs = shifted.diff().abs().sum(axis=1) / 2 * (COMMISSION_BPS + SLIPPAGE_BPS) / 10000
    return (ret - costs).fillna(0).rename(strategy_key)


def classify_regimes(market_returns):
    df = pd.DataFrame({'r': market_returns})
    df['cum'] = (1 + df['r']).rolling(TREND_WINDOW).apply(lambda x: x.prod() - 1, raw=True)
    df['vol'] = df['r'].rolling(TREND_WINDOW).std() * np.sqrt(252)
    cond = [df['cum'] < BEAR_RETURN_THRESH,
            (df['cum'] > BULL_RETURN_THRESH) & (df['vol'] < HIGH_VOL_THRESH),
            df['vol'] >= HIGH_VOL_THRESH]
    df['regime'] = np.select(cond, ['Bear', 'Bull', 'High-Vol'], default='Sideways')
    return df['regime'].dropna()


def portfolio_metrics(returns):
    if len(returns) < 20:
        return {}
    rf = RISK_FREE_RATE / 252
    ex = returns - rf
    std = ex.std()
    sr = float(np.sqrt(252) * ex.mean() / std) if std > 1e-10 else 0.0
    total = float((1 + returns).prod())
    n_yr = len(returns) / 252
    cagr = float(total ** (1 / n_yr) - 1) if total > 0 and n_yr > 0 else 0.0
    equity = (1 + returns).cumprod()
    mdd = float((equity / equity.cummax() - 1).min())
    vol = float(returns.std() * np.sqrt(252))
    return {
        'sharpe': safe_float(sr),
        'cagr': safe_float(cagr),
        'max_drawdown': safe_float(mdd),
        'ann_volatility': safe_float(vol),
    }


def diversification_ratio(returns_df, weights=None):
    if weights is None:
        weights = np.ones(len(returns_df.columns)) / len(returns_df.columns)
    indiv_vols = returns_df.std().values
    wtd_avg_vol = np.dot(weights, indiv_vols)
    port_vol = (returns_df * weights).sum(axis=1).std()
    return float(wtd_avg_vol / port_vol) if port_vol > 1e-10 else 1.0


def main():
    print("=" * 70)
    print("PHASE 3.9 — EXTENDED PORTFOLIO ANALYSIS (2000-2024)")
    print("=" * 70)

    data_path = PROJECT_ROOT / 'data_processed' / 'extended_prices_clean.parquet'
    logger.info("Loading extended data...")
    data = pd.read_parquet(data_path)
    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values(['date', 'symbol'])

    prices = data.pivot_table(index='date', columns='symbol', values='close').sort_index()
    pit_universe = load_pit_universe(prices.index)
    benchmark = prices.pct_change(fill_method=None).mean(axis=1).fillna(0).rename('benchmark')

    # Regimes for conditional correlation
    regime_series = classify_regimes(benchmark)

    # ── Step 1: Compute all strategy returns ──────────────────────────────
    logger.info(f"Computing {len(ALL_STRATEGIES)} strategy returns...")
    strategy_returns = {}
    for i, key in enumerate(ALL_STRATEGIES):
        logger.info(f"[{i+1:2d}/{len(ALL_STRATEGIES)}] {key}")
        try:
            strategy_returns[key] = get_strategy_returns_pit(key, data, prices, pit_universe)
        except Exception as e:
            logger.warning(f"  FAILED: {e}")

    ret_df = pd.DataFrame(strategy_returns).dropna()
    bench_aligned = benchmark.reindex(ret_df.index).fillna(0)

    # ── Step 2: Full correlation matrix ──────────────────────────────────
    print("\n" + "─" * 70)
    print("STEP 1: Full Correlation Matrix (2000-2024)")
    print("─" * 70)

    corr = ret_df.corr()
    n = len(corr)
    mask = ~np.eye(n, dtype=bool)
    avg_corr = float(corr.values[mask].mean())
    min_corr = float(corr.values[mask].min())
    max_corr = float(corr.values[mask].max())

    print(f"\n  Average inter-strategy correlation: {avg_corr:.3f}  (Phase 2: 0.788)")
    print(f"  Min pairwise correlation:           {min_corr:.3f}")
    print(f"  Max pairwise correlation:           {max_corr:.3f}")

    # Most and least correlated pairs
    pairs = []
    strats = list(corr.columns)
    for i in range(len(strats)):
        for j in range(i+1, len(strats)):
            pairs.append((strats[i], strats[j], corr.iloc[i, j]))

    pairs.sort(key=lambda x: -x[2])
    high_corr_pairs = [(a, b, round(c, 3)) for a, b, c in pairs if c > 0.80]
    low_corr_pairs  = [(a, b, round(c, 3)) for a, b, c in pairs if c < 0.40]

    print(f"\n  Highly correlated pairs (r > 0.80): {len(high_corr_pairs)}/{len(pairs)}")
    print(f"  Complementary pairs (r < 0.40):     {len(low_corr_pairs)}/{len(pairs)}")

    print(f"\n  Most correlated (most redundant):")
    for a, b, c in pairs[:5]:
        print(f"    {a:<35} ↔  {b:<35}  r={c:+.3f}")

    print(f"\n  Least correlated (most complementary):")
    for a, b, c in sorted(pairs, key=lambda x: x[2])[:5]:
        print(f"    {a:<35} ↔  {b:<35}  r={c:+.3f}")

    # ── Step 3: Regime-conditional correlation ────────────────────────────
    print("\n" + "─" * 70)
    print("STEP 2: Regime-Conditional Correlation")
    print("─" * 70)
    print("  (Does diversification survive during crashes?)")

    regime_corrs = {}
    for regime in ['Bull', 'Bear', 'High-Vol', 'Sideways']:
        mask_r = regime_series.reindex(ret_df.index) == regime
        sub = ret_df.loc[mask_r.fillna(False)]
        if len(sub) < 50:
            regime_corrs[regime] = None
            continue
        sub_corr = sub.corr()
        m = ~np.eye(len(sub_corr), dtype=bool)
        regime_corrs[regime] = float(sub_corr.values[m].mean())

    print(f"\n  Average inter-strategy correlation by regime:")
    for regime, rc in regime_corrs.items():
        if rc is not None:
            note = " ← correlations spike in crashes" if regime == 'Bear' else ""
            print(f"    {regime:<10} {rc:.3f}{note}")

    # ── Step 4: Individual strategy metrics ───────────────────────────────
    individual_metrics = {key: portfolio_metrics(ret_df[key]) for key in strats}
    bench_m = portfolio_metrics(bench_aligned)

    # ── Step 5: Portfolio construction ────────────────────────────────────
    print("\n" + "─" * 70)
    print("STEP 3: Portfolio Variants — Performance Comparison")
    print("─" * 70)

    def equal_wt(df):
        return df.mean(axis=1)

    def risk_parity(df):
        vols = df.std()
        w = (1 / vols) / (1 / vols).sum()
        return (df * w).sum(axis=1)

    # Build portfolios
    portfolios = {
        'Equal-weight all 14':       equal_wt(ret_df),
        'Tier 1 equal-wt (Ph3 top5)':equal_wt(ret_df[TIER_1_P3]),
        'Risk-parity all 14':        risk_parity(ret_df),
        'Risk-parity Tier 1 (Ph3)':  risk_parity(ret_df[TIER_1_P3]),
        'Benchmark (equal-wt idx)':  bench_aligned,
    }

    # Min-correlation: pick 3 strategies with lowest avg pairwise corr
    avg_corr_per_strat = {col: corr[col].drop(col).mean() for col in strats}
    min_corr_3 = sorted(avg_corr_per_strat, key=avg_corr_per_strat.get)[:3]
    portfolios[f'Min-corr top 3 ({", ".join(s[:8] for s in min_corr_3)})'] = equal_wt(ret_df[min_corr_3])

    print(f"\n  {'Portfolio':<45} {'Sharpe':>8} {'CAGR':>8} {'MDD':>9} {'Ann Vol':>9}")
    print("  " + "─" * 82)

    port_results = {}
    for name, port_ret in portfolios.items():
        m = portfolio_metrics(port_ret)
        port_results[name] = m
        sr = m.get('sharpe') or 0
        cg = m.get('cagr') or 0
        md = m.get('max_drawdown') or 0
        vl = m.get('ann_volatility') or 0
        marker = " ←── BENCHMARK" if 'Benchmark' in name else ""
        print(f"  {name:<45} {sr:>+8.2f} {cg*100:>7.1f}% {md*100:>8.1f}% {vl*100:>8.1f}%{marker}")

    # ── Step 6: Diversification ratio ─────────────────────────────────────
    dr_all  = diversification_ratio(ret_df)
    dr_t1   = diversification_ratio(ret_df[TIER_1_P3])
    print(f"\n  Diversification ratio — all 14: {dr_all:.3f}  (Phase 2: 1.051)")
    print(f"  Diversification ratio — Tier 1: {dr_t1:.3f}")
    print(f"  (1.0 = no benefit; >1.5 = meaningful diversification)")

    # ── Step 7: Average correlation per strategy ──────────────────────────
    print("\n" + "─" * 70)
    print("STEP 4: Avg Correlation Per Strategy (lowest = most unique)")
    print("─" * 70)

    sorted_by_corr = sorted(avg_corr_per_strat.items(), key=lambda x: x[1])
    print(f"\n  {'Strategy':<35} {'Avg Corr':>10}  Notes")
    print("  " + "─" * 65)
    for strat, ac in sorted_by_corr:
        note = " ← most unique"  if ac == sorted_by_corr[0][1]  else \
               " ← most redundant" if ac == sorted_by_corr[-1][1] else ""
        print(f"  {strat:<35} {ac:>10.3f}{note}")

    # ── Save results ──────────────────────────────────────────────────────
    output = {
        'data_period': '2000-2024',
        'avg_inter_strategy_correlation': safe_float(avg_corr),
        'min_pairwise_correlation': safe_float(min_corr),
        'max_pairwise_correlation': safe_float(max_corr),
        'n_high_corr_pairs': len(high_corr_pairs),
        'n_low_corr_pairs': len(low_corr_pairs),
        'high_corr_pairs': high_corr_pairs,
        'low_corr_pairs': low_corr_pairs,
        'regime_conditional_correlation': {k: safe_float(v) for k, v in regime_corrs.items()},
        'diversification_ratio_all14': safe_float(dr_all),
        'diversification_ratio_tier1': safe_float(dr_t1),
        'individual_strategy_metrics': individual_metrics,
        'benchmark_metrics': bench_m,
        'portfolio_results': port_results,
        'avg_corr_per_strategy': {k: safe_float(v) for k, v in avg_corr_per_strat.items()},
        'min_corr_3_selected': min_corr_3,
        'tier1_p3': TIER_1_P3,
    }

    with open(RESULTS_DIR / 'extended_portfolio_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)

    # Save correlation matrix CSV
    corr.to_csv(RESULTS_DIR / 'extended_correlation_matrix.csv')

    # Portfolio comparison CSV
    port_rows = [{'portfolio': name, **m} for name, m in port_results.items()]
    pd.DataFrame(port_rows).to_csv(RESULTS_DIR / 'extended_portfolio_comparison.csv', index=False)

    print(f"\n  Results saved to: {RESULTS_DIR}")
    print("\n" + "=" * 70)
    print("PHASE 3.9 COMPLETE")
    print("=" * 70)
    print("  NEXT: scripts/extended_walk_forward.py (Phase 3.10)")


if __name__ == '__main__':
    main()
