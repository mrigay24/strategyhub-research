"""
Monte Carlo Bootstrap Confidence Intervals

Tests whether each strategy's performance is statistically significant
or could have occurred by chance.

Three methods:
1. IID Bootstrap: Resample daily returns with replacement (10,000 trials)
   → Produces 95% confidence interval for Sharpe ratio
2. Block Bootstrap: Resample 20-day blocks with replacement
   → Preserves autocorrelation (momentum/mean-reversion structure)
3. Permutation Test: Shuffle returns randomly (null hypothesis: no skill)
   → p-value: probability of observing this Sharpe by pure luck

Transaction costs: 10 bps commission + 5 bps slippage (always on).

Usage:
    python scripts/monte_carlo.py                          # All strategies
    python scripts/monte_carlo.py large_cap_momentum       # One strategy
"""

import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from loguru import logger

from src.strategies import STRATEGY_REGISTRY, get_strategy
from src.backtesting.engine import Backtester

# Configure logging
logger.remove()
logger.add(lambda msg: print(msg, end=""), format="{time:HH:mm:ss} | {message}\n", level="INFO")

# ─── Configuration ────────────────────────────────────────────────────────────
N_BOOTSTRAP = 10_000       # Number of bootstrap samples
N_PERMUTATIONS = 10_000    # Number of random sign test trials
BLOCK_SIZE = 20            # Block size for block bootstrap (trading days ≈ 1 month)
CONFIDENCE_LEVEL = 0.95    # For confidence intervals
RISK_FREE_RATE = 0.02


def safe_float(v):
    """Convert to JSON-safe float."""
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return round(float(v), 6)


def annualized_sharpe(returns, risk_free_rate=0.02):
    """Calculate annualized Sharpe ratio from daily returns."""
    if len(returns) < 10:
        return 0.0
    excess = returns - risk_free_rate / 252
    if excess.std() == 0:
        return 0.0
    return float(np.sqrt(252) * excess.mean() / excess.std())


def get_strategy_returns(strategy_name, data):
    """
    Run a strategy backtest and return the daily returns series.
    """
    strategy = get_strategy(strategy_name, data)
    backtester = Backtester(strategy, data, initial_capital=100000)
    result = backtester.run()
    return result.returns


def iid_bootstrap(returns, n_bootstrap=N_BOOTSTRAP):
    """
    IID Bootstrap: resample daily returns with replacement.

    Returns:
        dict with observed_sharpe, bootstrap_sharpes, CI, p_value
    """
    observed = annualized_sharpe(returns)
    n = len(returns)
    ret_values = returns.values

    # Vectorized bootstrap for speed
    # Generate all random indices at once: (n_bootstrap, n)
    rng = np.random.default_rng(42)
    indices = rng.integers(0, n, size=(n_bootstrap, n))

    sharpes = np.zeros(n_bootstrap)
    daily_rf = RISK_FREE_RATE / 252

    for i in range(n_bootstrap):
        sample = ret_values[indices[i]]
        excess = sample - daily_rf
        std = excess.std()
        if std > 0:
            sharpes[i] = np.sqrt(252) * excess.mean() / std
        else:
            sharpes[i] = 0.0

    # Confidence interval
    alpha = 1 - CONFIDENCE_LEVEL
    ci_lower = float(np.percentile(sharpes, alpha / 2 * 100))
    ci_upper = float(np.percentile(sharpes, (1 - alpha / 2) * 100))

    # p-value: fraction of bootstraps with Sharpe <= 0
    p_value = float((sharpes <= 0).mean())

    return {
        'method': 'iid_bootstrap',
        'n_samples': n_bootstrap,
        'observed_sharpe': safe_float(observed),
        'mean_bootstrap_sharpe': safe_float(float(np.mean(sharpes))),
        'std_bootstrap_sharpe': safe_float(float(np.std(sharpes))),
        'ci_lower': safe_float(ci_lower),
        'ci_upper': safe_float(ci_upper),
        'ci_width': safe_float(ci_upper - ci_lower),
        'p_value': safe_float(p_value),
        'significant_at_5pct': p_value < 0.05,
        'significant_at_1pct': p_value < 0.01,
    }


def block_bootstrap(returns, n_bootstrap=N_BOOTSTRAP, block_size=BLOCK_SIZE):
    """
    Block Bootstrap: resample consecutive blocks of returns.
    Preserves autocorrelation structure (important for momentum/mean-reversion).

    Returns:
        dict with observed_sharpe, bootstrap_sharpes, CI, p_value
    """
    observed = annualized_sharpe(returns)
    n = len(returns)
    ret_values = returns.values

    # Number of blocks needed to fill the series
    n_blocks = int(np.ceil(n / block_size))

    rng = np.random.default_rng(123)
    max_start = n - block_size  # Maximum valid block start index

    if max_start <= 0:
        # Not enough data for block bootstrap
        return {
            'method': 'block_bootstrap',
            'n_samples': 0,
            'observed_sharpe': safe_float(observed),
            'error': 'Insufficient data for block bootstrap',
        }

    sharpes = np.zeros(n_bootstrap)
    daily_rf = RISK_FREE_RATE / 252

    for i in range(n_bootstrap):
        # Randomly select block start positions
        starts = rng.integers(0, max_start + 1, size=n_blocks)

        # Build resampled series from blocks
        blocks = [ret_values[s:s + block_size] for s in starts]
        sample = np.concatenate(blocks)[:n]  # Trim to original length

        excess = sample - daily_rf
        std = excess.std()
        if std > 0:
            sharpes[i] = np.sqrt(252) * excess.mean() / std
        else:
            sharpes[i] = 0.0

    # Confidence interval
    alpha = 1 - CONFIDENCE_LEVEL
    ci_lower = float(np.percentile(sharpes, alpha / 2 * 100))
    ci_upper = float(np.percentile(sharpes, (1 - alpha / 2) * 100))

    # p-value
    p_value = float((sharpes <= 0).mean())

    return {
        'method': 'block_bootstrap',
        'block_size': block_size,
        'n_samples': n_bootstrap,
        'observed_sharpe': safe_float(observed),
        'mean_bootstrap_sharpe': safe_float(float(np.mean(sharpes))),
        'std_bootstrap_sharpe': safe_float(float(np.std(sharpes))),
        'ci_lower': safe_float(ci_lower),
        'ci_upper': safe_float(ci_upper),
        'ci_width': safe_float(ci_upper - ci_lower),
        'p_value': safe_float(p_value),
        'significant_at_5pct': p_value < 0.05,
        'significant_at_1pct': p_value < 0.01,
    }


def random_sign_test(returns, n_permutations=N_PERMUTATIONS):
    """
    Random Sign Test (proper null hypothesis test for strategies).

    Null hypothesis: the strategy has no directional skill.
    We randomly flip the sign of each daily return (+1 or -1),
    effectively simulating a random long/short decision each day.
    If the observed Sharpe is better than most random-sign versions,
    the strategy's TIMING (knowing when to be long/short) is real.

    Why not shuffle returns? Shuffling preserves mean and std,
    so the Sharpe stays identical (p=1.0 always). The sign test
    destroys the strategy's directional edge while preserving
    return magnitudes.

    Returns:
        dict with observed_sharpe, p_value, percentile_rank
    """
    observed = annualized_sharpe(returns)
    ret_values = returns.values.copy()
    n = len(ret_values)

    rng = np.random.default_rng(456)
    sharpes = np.zeros(n_permutations)
    daily_rf = RISK_FREE_RATE / 252

    for i in range(n_permutations):
        # Randomly flip the sign of each return
        signs = rng.choice([-1, 1], size=n)
        flipped = ret_values * signs
        excess = flipped - daily_rf
        std = excess.std()
        if std > 0:
            sharpes[i] = np.sqrt(252) * excess.mean() / std
        else:
            sharpes[i] = 0.0

    # p-value: fraction of random-sign trials with Sharpe >= observed
    # (one-sided test: is observed Sharpe better than random direction?)
    p_value = float((sharpes >= observed).mean())

    # Percentile rank of observed Sharpe among random-sign trials
    percentile = float((sharpes < observed).mean() * 100)

    return {
        'method': 'random_sign_test',
        'n_permutations': n_permutations,
        'observed_sharpe': safe_float(observed),
        'mean_random_sharpe': safe_float(float(np.mean(sharpes))),
        'std_random_sharpe': safe_float(float(np.std(sharpes))),
        'p_value': safe_float(p_value),
        'percentile_rank': safe_float(percentile),
        'significant_at_5pct': p_value < 0.05,
        'significant_at_1pct': p_value < 0.01,
    }


def additional_metrics(returns):
    """
    Compute additional Monte Carlo-adjacent statistics.
    """
    n = len(returns)
    observed = annualized_sharpe(returns)

    # Standard error of Sharpe (Lo, 2002 approximation)
    # SE(Sharpe) ≈ sqrt((1 + 0.5 * Sharpe^2) / n) * sqrt(252)
    se_sharpe = np.sqrt((1 + 0.5 * observed ** 2) / n) * np.sqrt(252)

    # T-statistic for Sharpe
    t_stat = observed / se_sharpe if se_sharpe > 0 else 0

    # Skewness and kurtosis of returns
    skew = float(returns.skew()) if len(returns) > 3 else 0
    kurt = float(returns.kurtosis()) if len(returns) > 4 else 0

    # Adjusted Sharpe (Pezier & White, 2006) — corrects for non-normal returns
    # AdjSharpe = Sharpe * (1 + (skew/6)*Sharpe - ((kurt-3)/24)*Sharpe^2)
    adj_sharpe = observed * (1 + (skew / 6) * observed - ((kurt - 3) / 24) * observed ** 2)

    return {
        'n_observations': n,
        'se_sharpe_lo2002': safe_float(se_sharpe),
        't_statistic': safe_float(t_stat),
        'skewness': safe_float(skew),
        'excess_kurtosis': safe_float(kurt),
        'adjusted_sharpe_pezier_white': safe_float(adj_sharpe),
    }


def print_strategy_results(name, iid, block, sign, extra):
    """Print formatted results for one strategy."""
    print(f"\n{'=' * 70}")
    print(f"  {name.upper().replace('_', ' ')}")
    print(f"{'=' * 70}")

    observed = iid['observed_sharpe'] or 0

    print(f"\n  Observed Sharpe: {observed:.3f}")
    print(f"  Adjusted Sharpe (Pezier-White): {extra.get('adjusted_sharpe_pezier_white', 0) or 0:.3f}")
    print(f"  Skewness: {extra.get('skewness', 0) or 0:.2f}  |  Excess Kurtosis: {extra.get('excess_kurtosis', 0) or 0:.2f}")
    print(f"  SE(Sharpe) [Lo 2002]: {extra.get('se_sharpe_lo2002', 0) or 0:.3f}  |  t-stat: {extra.get('t_statistic', 0) or 0:.2f}")

    print(f"\n  IID BOOTSTRAP ({iid['n_samples']:,} samples)")
    print(f"  ├─ 95% CI:       [{iid.get('ci_lower', 0) or 0:.3f}, {iid.get('ci_upper', 0) or 0:.3f}]")
    print(f"  ├─ CI Width:     {iid.get('ci_width', 0) or 0:.3f}")
    print(f"  ├─ p-value:      {iid.get('p_value', 1) or 1:.4f}")
    sig = "YES ***" if iid.get('significant_at_1pct') else ("YES *" if iid.get('significant_at_5pct') else "NO")
    print(f"  └─ Significant:  {sig}")

    print(f"\n  BLOCK BOOTSTRAP (block={block.get('block_size', BLOCK_SIZE)}, {block.get('n_samples', 0):,} samples)")
    if block.get('error'):
        print(f"  └─ Error: {block['error']}")
    else:
        print(f"  ├─ 95% CI:       [{block.get('ci_lower', 0) or 0:.3f}, {block.get('ci_upper', 0) or 0:.3f}]")
        print(f"  ├─ CI Width:     {block.get('ci_width', 0) or 0:.3f}")
        print(f"  ├─ p-value:      {block.get('p_value', 1) or 1:.4f}")
        sig_b = "YES ***" if block.get('significant_at_1pct') else ("YES *" if block.get('significant_at_5pct') else "NO")
        print(f"  └─ Significant:  {sig_b}")

    print(f"\n  RANDOM SIGN TEST ({sign['n_permutations']:,} trials)")
    print(f"  ├─ p-value:      {sign.get('p_value', 1) or 1:.4f}")
    print(f"  ├─ Percentile:   {sign.get('percentile_rank', 0) or 0:.1f}th")
    sig_p = "YES ***" if sign.get('significant_at_1pct') else ("YES *" if sign.get('significant_at_5pct') else "NO")
    print(f"  └─ Significant:  {sig_p}")

    # Overall verdict
    iid_sig = iid.get('significant_at_5pct', False)
    block_sig = block.get('significant_at_5pct', False)
    sign_sig = sign.get('significant_at_5pct', False)

    n_sig = sum([iid_sig, block_sig, sign_sig])
    if n_sig == 3:
        verdict = "STATISTICALLY SIGNIFICANT"
    elif n_sig == 2:
        verdict = "LIKELY SIGNIFICANT"
    elif n_sig == 1:
        verdict = "MARGINAL"
    else:
        verdict = "NOT SIGNIFICANT"

    ci_contains_zero = (iid.get('ci_lower', 0) or 0) <= 0

    print(f"\n  ┌─────────────────────────────────┐")
    print(f"  │  VERDICT: {verdict:<22s} │")
    print(f"  │  CI contains zero: {'YES — caution' if ci_contains_zero else 'NO — edge is real':<22s}│")
    print(f"  └─────────────────────────────────┘")


def main():
    """Run Monte Carlo analysis on all strategies."""
    target = None
    if len(sys.argv) > 1:
        target = sys.argv[1:]
        for s in target:
            if s not in STRATEGY_REGISTRY:
                print(f"Unknown strategy: {s}")
                print(f"Available: {', '.join(STRATEGY_REGISTRY.keys())}")
                sys.exit(1)

    strategies = target or list(STRATEGY_REGISTRY.keys())

    print("=" * 70)
    print("MONTE CARLO BOOTSTRAP CONFIDENCE INTERVALS")
    print("=" * 70)
    print(f"Strategies: {len(strategies)}")
    print(f"Method 1: IID Bootstrap ({N_BOOTSTRAP:,} resamples)")
    print(f"Method 2: Block Bootstrap (block={BLOCK_SIZE} days, {N_BOOTSTRAP:,} resamples)")
    print(f"Method 3: Random Sign Test ({N_PERMUTATIONS:,} trials)")
    print(f"Confidence Level: {CONFIDENCE_LEVEL:.0%}")
    print(f"Transaction costs: 10 bps commission + 5 bps slippage (always on)")
    print()

    # Load data
    logger.info("Loading price data...")
    data = pd.read_parquet('data_processed/prices_clean.parquet')
    data['date'] = pd.to_datetime(data['date'])
    logger.info(f"Loaded {len(data)} rows, {data['symbol'].nunique()} symbols")
    logger.info(f"Date range: {data['date'].min().date()} to {data['date'].max().date()}")
    print()

    output_dir = Path('results/monte_carlo')
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results = {}
    start_time = time.time()

    for strategy_name in strategies:
        logger.info(f"\n{'─' * 50}")
        logger.info(f"Analyzing: {strategy_name}")
        logger.info(f"{'─' * 50}")

        # Get strategy returns
        logger.info("  Running full backtest...")
        try:
            returns = get_strategy_returns(strategy_name, data)
        except Exception as e:
            logger.warning(f"  Failed to get returns: {e}")
            continue

        # Drop NaN/zero-only periods
        returns = returns.dropna()
        if len(returns) < 50:
            logger.warning(f"  Too few returns ({len(returns)}), skipping")
            continue

        logger.info(f"  Got {len(returns)} daily returns")

        # Run all three methods
        logger.info("  Running IID bootstrap...")
        iid_result = iid_bootstrap(returns)

        logger.info("  Running block bootstrap...")
        block_result = block_bootstrap(returns)

        logger.info("  Running random sign test...")
        sign_result = random_sign_test(returns)

        # Additional metrics
        extra = additional_metrics(returns)

        # Print results
        print_strategy_results(strategy_name, iid_result, block_result, sign_result, extra)

        # Store
        strategy_output = {
            'strategy': strategy_name,
            'n_returns': len(returns),
            'iid_bootstrap': iid_result,
            'block_bootstrap': block_result,
            'random_sign_test': sign_result,
            'additional_metrics': extra,
        }

        # Save individual file
        with open(output_dir / f'{strategy_name}.json', 'w') as f:
            json.dump(strategy_output, f, indent=2, default=str)

        all_results[strategy_name] = strategy_output

    elapsed = time.time() - start_time

    # ─── Overall Summary ─────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("OVERALL MONTE CARLO SUMMARY")
    print("=" * 70)
    print()
    print(f"{'Strategy':<30} {'Sharpe':>7} {'95% CI':>16} {'p(IID)':>8} "
          f"{'p(Block)':>9} {'p(Sign)':>8} {'Verdict':>22}")
    print("-" * 100)

    summary_rows = []
    for name, result in all_results.items():
        iid = result['iid_bootstrap']
        block = result['block_bootstrap']
        sign = result['random_sign_test']
        extra = result['additional_metrics']

        sharpe = f"{iid.get('observed_sharpe', 0) or 0:.3f}"
        ci_lo = iid.get('ci_lower', 0) or 0
        ci_hi = iid.get('ci_upper', 0) or 0
        ci_str = f"[{ci_lo:.2f}, {ci_hi:.2f}]"
        p_iid = f"{iid.get('p_value', 1) or 1:.4f}"
        p_block = f"{block.get('p_value', 1) or 1:.4f}" if not block.get('error') else "N/A"
        p_sign = f"{sign.get('p_value', 1) or 1:.4f}"

        # Verdict
        n_sig = sum([
            iid.get('significant_at_5pct', False),
            block.get('significant_at_5pct', False),
            sign.get('significant_at_5pct', False),
        ])
        if n_sig == 3:
            verdict = "SIGNIFICANT ***"
        elif n_sig == 2:
            verdict = "LIKELY SIGNIFICANT **"
        elif n_sig == 1:
            verdict = "MARGINAL *"
        else:
            verdict = "NOT SIGNIFICANT"

        display = name.replace('_', ' ')[:28]
        print(f"{display:<30} {sharpe:>7} {ci_str:>16} {p_iid:>8} "
              f"{p_block:>9} {p_sign:>8} {verdict:>22}")

        summary_rows.append({
            'strategy': name,
            'observed_sharpe': iid.get('observed_sharpe'),
            'adjusted_sharpe': extra.get('adjusted_sharpe_pezier_white'),
            'ci_lower': ci_lo,
            'ci_upper': ci_hi,
            'ci_width': iid.get('ci_width'),
            'p_value_iid': iid.get('p_value'),
            'p_value_block': block.get('p_value'),
            'p_value_sign': sign.get('p_value'),
            'significant_iid': iid.get('significant_at_5pct'),
            'significant_block': block.get('significant_at_5pct'),
            'significant_sign': sign.get('significant_at_5pct'),
            'n_significant': n_sig,
            'verdict': verdict.strip(' *'),
            'skewness': extra.get('skewness'),
            'excess_kurtosis': extra.get('excess_kurtosis'),
            't_statistic': extra.get('t_statistic'),
        })

    # Save summary
    summary = {
        'generated_at': pd.Timestamp.now().isoformat(),
        'data_period': '2014-2017',
        'transaction_costs': '10 bps commission + 5 bps slippage',
        'n_bootstrap': N_BOOTSTRAP,
        'n_permutations': N_PERMUTATIONS,
        'block_size': BLOCK_SIZE,
        'confidence_level': CONFIDENCE_LEVEL,
        'elapsed_seconds': round(elapsed, 1),
        'strategies': summary_rows,
    }

    with open(output_dir / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    # CSV
    pd.DataFrame(summary_rows).to_csv(output_dir / 'monte_carlo_summary.csv', index=False)

    print()
    print(f"Time elapsed: {elapsed:.0f}s")
    print(f"Results saved to: {output_dir}/")
    print()
    print("Significance guide:")
    print("  *** = All 3 methods significant at p<0.05 — very strong evidence")
    print("  **  = 2/3 methods significant — likely real edge")
    print("  *   = 1/3 methods significant — marginal, needs more data")
    print("  (none) = No methods significant — edge may not be real")
    print()
    print("Key insight: Block bootstrap typically produces WIDER CIs than IID")
    print("because it preserves return autocorrelation. If a strategy is significant")
    print("under block bootstrap, it's very likely real.")


if __name__ == '__main__':
    main()
