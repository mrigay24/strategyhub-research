"""
Phase 3.11 — Monte Carlo Significance Testing on Extended 25-Year Data (2000-2024)

Mirrors Phase 2.3 (monte_carlo.py) but on the 25-year dataset with PIT masking.

Three tests:
  1. IID Bootstrap (10,000 trials): resample daily returns, compute CI for Sharpe
  2. Block Bootstrap (20-day blocks): preserves autocorrelation
  3. Random Sign Test (10,000 trials): null hypothesis = no directional timing skill

Key differences vs Phase 2:
  - 6,288 trading days (vs 1,007) → much tighter confidence intervals
  - Sharpe ratios are lower (0.53-0.66 vs 0.52-1.20) but n is 6× larger
  - Statistical power is much higher → expect more strategies significant at 1%
  - PIT universe masking applied throughout

Key question: Do the lower Sharpe ratios over 25 years remain statistically significant,
or do they collapse to noise once real bear markets are included?

Usage:
    .venv/bin/python scripts/extended_monte_carlo.py
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

# ─── Configuration ─────────────────────────────────────────────────────────────
N_BOOTSTRAP    = 10_000
BLOCK_SIZE     = 20           # ~1 month of trading days
CONFIDENCE     = 0.95
COMMISSION_BPS = 10
SLIPPAGE_BPS   = 5
RISK_FREE_RATE = 0.02
RESULTS_DIR    = PROJECT_ROOT / 'results' / 'extended_monte_carlo'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

ALL_STRATEGIES = list(STRATEGY_REGISTRY.keys())


def safe_float(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return round(float(v), 6)


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


def compute_strategy_returns(strategy_key, data, prices, pit_universe):
    """Compute PIT-masked strategy returns for the full dataset."""
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
    return (ret - costs).fillna(0)


def annualized_sharpe(returns):
    if len(returns) < 20:
        return 0.0
    rf = RISK_FREE_RATE / 252
    excess = returns - rf
    std = excess.std()
    if std < 1e-10:
        return 0.0
    return float(np.sqrt(252) * excess.mean() / std)


def iid_bootstrap(returns):
    observed = annualized_sharpe(returns)
    n = len(returns)
    ret_vals = returns.values
    daily_rf = RISK_FREE_RATE / 252
    rng = np.random.default_rng(42)
    indices = rng.integers(0, n, size=(N_BOOTSTRAP, n))
    sharpes = np.zeros(N_BOOTSTRAP)
    for i in range(N_BOOTSTRAP):
        sample = ret_vals[indices[i]]
        excess = sample - daily_rf
        std = excess.std()
        sharpes[i] = np.sqrt(252) * excess.mean() / std if std > 0 else 0.0
    alpha = 1 - CONFIDENCE
    ci_lower = float(np.percentile(sharpes, alpha / 2 * 100))
    ci_upper = float(np.percentile(sharpes, (1 - alpha / 2) * 100))
    p_value = float((sharpes <= 0).mean())
    return {
        'observed_sharpe': safe_float(observed),
        'ci_lower': safe_float(ci_lower),
        'ci_upper': safe_float(ci_upper),
        'ci_width': safe_float(ci_upper - ci_lower),
        'p_value': safe_float(p_value),
        'significant_5pct': p_value < 0.05,
        'significant_1pct': p_value < 0.01,
    }


def block_bootstrap(returns):
    observed = annualized_sharpe(returns)
    n = len(returns)
    ret_vals = returns.values
    daily_rf = RISK_FREE_RATE / 252
    n_blocks = int(np.ceil(n / BLOCK_SIZE))
    max_start = n - BLOCK_SIZE
    if max_start <= 0:
        return {'observed_sharpe': safe_float(observed), 'error': 'insufficient data'}
    rng = np.random.default_rng(123)
    sharpes = np.zeros(N_BOOTSTRAP)
    for i in range(N_BOOTSTRAP):
        starts = rng.integers(0, max_start + 1, size=n_blocks)
        blocks = [ret_vals[s:s + BLOCK_SIZE] for s in starts]
        sample = np.concatenate(blocks)[:n]
        excess = sample - daily_rf
        std = excess.std()
        sharpes[i] = np.sqrt(252) * excess.mean() / std if std > 0 else 0.0
    alpha = 1 - CONFIDENCE
    ci_lower = float(np.percentile(sharpes, alpha / 2 * 100))
    ci_upper = float(np.percentile(sharpes, (1 - alpha / 2) * 100))
    p_value = float((sharpes <= 0).mean())
    return {
        'observed_sharpe': safe_float(observed),
        'ci_lower': safe_float(ci_lower),
        'ci_upper': safe_float(ci_upper),
        'ci_width': safe_float(ci_upper - ci_lower),
        'p_value': safe_float(p_value),
        'significant_5pct': p_value < 0.05,
        'significant_1pct': p_value < 0.01,
    }


def random_sign_test(returns):
    observed = annualized_sharpe(returns)
    ret_vals = returns.values.copy()
    n = len(ret_vals)
    daily_rf = RISK_FREE_RATE / 252
    rng = np.random.default_rng(456)
    sharpes = np.zeros(N_BOOTSTRAP)
    for i in range(N_BOOTSTRAP):
        signs = rng.choice([-1, 1], size=n)
        flipped = ret_vals * signs
        excess = flipped - daily_rf
        std = excess.std()
        sharpes[i] = np.sqrt(252) * excess.mean() / std if std > 0 else 0.0
    p_value = float((sharpes >= observed).mean())
    percentile = float((sharpes < observed).mean() * 100)
    return {
        'observed_sharpe': safe_float(observed),
        'mean_random_sharpe': safe_float(float(np.mean(sharpes))),
        'p_value': safe_float(p_value),
        'percentile_rank': safe_float(percentile),
        'significant_5pct': p_value < 0.05,
        'significant_1pct': p_value < 0.01,
    }


def pezier_white_adjusted_sharpe(returns):
    """Pezier-White adjustment for non-normal returns (penalizes negative skew and excess kurtosis)."""
    sr = annualized_sharpe(returns)
    n = len(returns)
    if n < 20:
        return sr
    skew = float(returns.skew())
    kurt = float(returns.kurtosis())  # Excess kurtosis
    # Pezier-White (2006): ASR = SR * [1 + (skew/6)*SR - ((kurt-3)/24)*SR^2]
    adjusted = sr * (1 + (skew / 6) * sr - ((kurt - 3) / 24) * sr ** 2)
    return adjusted


def sharpe_se(returns):
    """Lo (2002) standard error of the Sharpe ratio."""
    n = len(returns)
    sr = annualized_sharpe(returns)
    if n < 20:
        return None
    # SE(SR_annual) ≈ sqrt((1 + SR_daily^2 / 2) * T / n) where T = 252
    sr_daily = sr / np.sqrt(252)
    se = float(np.sqrt((1 + sr_daily ** 2 / 2) / (n / 252)))
    return se


def verdict(iid_p, block_p, sign_p):
    """Combine three p-values into a single verdict string."""
    tests_sig = sum([iid_p < 0.05, block_p < 0.05, sign_p < 0.05])
    tests_strong = sum([iid_p < 0.01, block_p < 0.01, sign_p < 0.01])
    if tests_strong == 3:
        return 'SIGNIFICANT ★★★'
    if tests_sig == 3:
        return 'SIGNIFICANT ★★★'
    if tests_sig == 2:
        return 'LIKELY SIGNIFICANT ★★'
    if tests_sig == 1:
        return 'MARGINAL ★'
    return 'NOT SIGNIFICANT'


def main():
    print("=" * 70)
    print("PHASE 3.11 — MONTE CARLO SIGNIFICANCE TESTS (2000-2024)")
    print("=" * 70)
    print(f"  Bootstrap samples: {N_BOOTSTRAP:,} | Block size: {BLOCK_SIZE} days")
    print(f"  Data: 25 years | PIT universe masking: YES")
    print()

    data_path = PROJECT_ROOT / 'data_processed' / 'extended_prices_clean.parquet'
    logger.info("Loading extended data...")
    data = pd.read_parquet(data_path)
    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values(['date', 'symbol'])

    prices = data.pivot_table(index='date', columns='symbol', values='close').sort_index()
    pit_universe = load_pit_universe(prices.index)

    # ── Pre-compute all strategy returns ──────────────────────────────────────
    logger.info(f"Computing strategy returns (25 years, PIT masked)...")
    all_returns = {}
    for i, key in enumerate(ALL_STRATEGIES):
        logger.info(f"[{i+1:2d}/{len(ALL_STRATEGIES)}] {key}")
        try:
            all_returns[key] = compute_strategy_returns(key, data, prices, pit_universe)
        except Exception as e:
            logger.warning(f"  FAILED: {e}")

    n_days = len(prices)
    n_years = n_days / 252
    print(f"\n  Sample size: {n_days:,} trading days (~{n_years:.1f} years)\n")

    # ── Run Monte Carlo tests ─────────────────────────────────────────────────
    print("─" * 95)
    print(f"  {'Strategy':<32} {'Sharpe':>7} {'IID CI (95%)':<22} {'IID p':>7} {'Blk p':>7} {'Sign p':>7}  Verdict")
    print("  " + "─" * 90)

    results = {}
    summary_rows = []

    for key, ret in all_returns.items():
        sr = annualized_sharpe(ret)
        se = sharpe_se(ret)
        adj_sr = pezier_white_adjusted_sharpe(ret)

        iid = iid_bootstrap(ret)
        blk = block_bootstrap(ret)
        sgn = random_sign_test(ret)

        iid_p = iid['p_value'] or 1.0
        blk_p = blk.get('p_value') or 1.0
        sgn_p = sgn['p_value'] or 1.0
        v = verdict(iid_p, blk_p, sgn_p)

        ci_str = f"[{iid['ci_lower']:+.3f}, {iid['ci_upper']:+.3f}]"
        print(f"  {key:<32} {sr:>+7.3f} {ci_str:<22} {iid_p:>7.4f} {blk_p:>7.4f} {sgn_p:>7.4f}  {v}")

        results[key] = {
            'sharpe': safe_float(sr),
            'sharpe_se': safe_float(se),
            'adjusted_sharpe': safe_float(adj_sr),
            'iid_bootstrap': iid,
            'block_bootstrap': blk,
            'random_sign_test': sgn,
            'verdict': v,
        }
        summary_rows.append({
            'strategy': key,
            'sharpe': safe_float(sr),
            'sharpe_se': safe_float(se),
            'adjusted_sharpe': safe_float(adj_sr),
            'iid_ci_lower': iid['ci_lower'],
            'iid_ci_upper': iid['ci_upper'],
            'iid_p_value': iid_p,
            'block_p_value': blk_p,
            'sign_p_value': sgn_p,
            'verdict': v,
        })

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("SUMMARY — Significance Comparison: Phase 2 vs Phase 3")
    print("─" * 70)

    sig_count    = sum(1 for r in results.values() if '★★★' in r['verdict'])
    likely_count = sum(1 for r in results.values() if '★★' in r['verdict'])
    marg_count   = sum(1 for r in results.values() if r['verdict'].count('★') == 1)
    not_count    = sum(1 for r in results.values() if r['verdict'] == 'NOT SIGNIFICANT')

    print(f"\n  Statistically significant (★★★): {sig_count}")
    print(f"  Likely significant (★★):          {likely_count}")
    print(f"  Marginal (★):                     {marg_count}")
    print(f"  Not significant:                   {not_count}")
    print()
    print(f"  Phase 2 comparison (2014-2017, 1,007 days):")
    print(f"    Significant: 5 | Likely: 3 | Marginal: 3 | Not: 3")
    print(f"  Phase 3 (2000-2024, {n_days:,} days): see above")
    print()
    print(f"  KEY INSIGHT: Larger sample (6× more days) → tighter confidence intervals.")
    print(f"  Even with LOWER Sharpe ratios (0.53-0.66 vs 0.52-1.20), statistical")
    print(f"  significance may be HIGHER due to more data. More data = more certainty,")
    print(f"  even if the certainty is 'the alpha is small but real.'")

    # Adjusted Sharpe comparison
    print("\n" + "─" * 70)
    print("ADJUSTED SHARPE — Pezier-White Correction for Non-Normal Returns")
    print("─" * 70)
    print(f"\n  {'Strategy':<32} {'Raw Sharpe':>12} {'Adj Sharpe':>12}  {'Adjustment':>12}")
    print("  " + "─" * 72)
    for row in sorted(summary_rows, key=lambda x: -(x['sharpe'] or 0)):
        raw = row['sharpe'] or 0
        adj = results[row['strategy']]['adjusted_sharpe'] or 0
        diff = adj - raw
        print(f"  {row['strategy']:<32} {raw:>+12.4f} {adj:>+12.4f}  {diff:>+12.4f}")

    # ── Save results ───────────────────────────────────────────────────────────
    output = {
        'data_period': '2000-2024',
        'n_trading_days': n_days,
        'n_years': safe_float(n_years),
        'n_bootstrap': N_BOOTSTRAP,
        'block_size': BLOCK_SIZE,
        'confidence_level': CONFIDENCE,
        'results': results,
    }
    with open(RESULTS_DIR / 'extended_monte_carlo_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)

    pd.DataFrame(summary_rows).to_csv(RESULTS_DIR / 'extended_mc_summary.csv', index=False)

    print(f"\n  Results saved to: {RESULTS_DIR}")
    print("\n" + "=" * 70)
    print("PHASE 3.11 COMPLETE")
    print("=" * 70)
    print("  NEXT: Update PROGRESS_REPORT + KNOWLEDGE_BASE, then Phase 3.12 (Final Summary)")


if __name__ == '__main__':
    main()
