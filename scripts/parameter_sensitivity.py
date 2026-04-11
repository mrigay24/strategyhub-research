"""
Parameter Sensitivity Analysis

For each strategy, sweeps each tunable parameter across a range of values
while holding all other parameters at defaults. Records Sharpe, total return,
max drawdown, and Calmar ratio for every combination.

Answers the question: "Is this strategy's performance robust to parameter
changes, or does it only work at one specific setting?"

Usage:
    python scripts/parameter_sensitivity.py                  # All strategies
    python scripts/parameter_sensitivity.py large_cap_momentum  # One strategy
"""

import sys
import json
import time
from pathlib import Path
from itertools import product

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from loguru import logger

from src.strategies import STRATEGY_REGISTRY, get_strategy
from src.backtesting.engine import Backtester

# Configure logging
logger.remove()
logger.add(lambda msg: print(msg, end=""), format="{time:HH:mm:ss} | {message}\n", level="INFO")

# ─── Parameter sweep definitions ─────────────────────────────────────────────
# For each strategy: which params to sweep and what values to try.
# These are 1D sweeps (vary one param, hold others at default).

PARAM_SWEEPS = {
    'large_cap_momentum': {
        'lookback':     [63, 126, 189, 252, 315],
        'skip_recent':  [0, 5, 10, 21, 42],
        'top_pct':      [5, 10, 15, 20, 30],
        'large_cap_pct': [30, 40, 50, 70, 100],
    },
    '52_week_high_breakout': {
        'high_window':  [63, 126, 189, 252],
        'top_pct':      [5, 10, 15, 20, 30],
    },
    'deep_value_all_cap': {
        'lookback':     [63, 126, 189, 252],
        'top_pct':      [10, 15, 20, 30, 40],
        'ma_window':    [50, 100, 150, 200],
    },
    'high_quality_roic': {
        'vol_lookback': [63, 126, 189, 252],
        'mom_lookback': [63, 126, 189, 252],
        'top_pct':      [10, 15, 20, 30],
    },
    'low_volatility_shield': {
        'vol_lookback': [21, 42, 63, 126, 189],
        'bottom_pct':   [10, 15, 20, 30, 40],
    },
    'dividend_aristocrats': {
        'lookback_months':  [12, 24, 36, 48],
        'min_positive_pct': [0.4, 0.5, 0.6, 0.7, 0.8],
        'top_pct':          [10, 15, 20, 30],
    },
    'moving_average_trend': {
        'ma_window':    [50, 100, 150, 200, 250],
        'ma_type':      ['sma', 'ema'],
    },
    'rsi_mean_reversion': {
        'rsi_period':      [5, 7, 10, 14, 21],
        'oversold':        [15, 20, 25, 30, 40],
        'exit_threshold':  [40, 45, 50, 55, 60],
        'max_positions':   [10, 15, 20, 30, 50],
    },
    'value_momentum_blend': {
        'mom_lookback':  [63, 126, 189, 252],
        'mom_weight':    [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
        'top_pct':       [10, 15, 20, 30],
    },
    'quality_momentum': {
        'mom_lookback':  [63, 126, 189, 252],
        'mom_weight':    [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
        'top_pct':       [10, 15, 20, 30],
    },
    'quality_low_vol': {
        'vol_lookback':     [42, 63, 126, 189],
        'quality_lookback': [126, 189, 252],
        'vol_weight':       [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
        'top_pct':          [10, 15, 20, 30],
    },
    'composite_factor_score': {
        'lookback':         [63, 126, 189, 252],
        'momentum_weight':  [0.1, 0.2, 0.3, 0.4, 0.5],
        'value_weight':     [0.1, 0.2, 0.3, 0.4],
        'quality_weight':   [0.1, 0.2, 0.3, 0.4, 0.5],
        'top_pct':          [10, 15, 20, 30],
    },
    'volatility_targeting': {
        'target_vol':   [0.05, 0.08, 0.10, 0.12, 0.15, 0.20],
        'vol_lookback': [21, 42, 63, 126],
        'max_leverage': [1.0, 1.5, 2.0, 3.0],
    },
    'earnings_surprise_momentum': {
        'volume_spike_mult': [1.5, 2.0, 2.5, 3.0, 4.0, 5.0],
        'price_move_std':    [1.0, 1.5, 2.0, 2.5, 3.0],
        'drift_period':      [21, 42, 63, 126],
        'max_positions':     [10, 20, 30, 50],
    },
}

# 2D heatmap configs: the two most interesting params per strategy
HEATMAP_PAIRS = {
    'large_cap_momentum':        ('lookback', 'top_pct'),
    '52_week_high_breakout':     ('high_window', 'top_pct'),
    'deep_value_all_cap':        ('lookback', 'top_pct'),
    'high_quality_roic':         ('vol_lookback', 'top_pct'),
    'low_volatility_shield':     ('vol_lookback', 'bottom_pct'),
    'dividend_aristocrats':      ('lookback_months', 'min_positive_pct'),
    'moving_average_trend':      ('ma_window', 'ma_type'),
    'rsi_mean_reversion':        ('rsi_period', 'oversold'),
    'value_momentum_blend':      ('mom_weight', 'top_pct'),
    'quality_momentum':          ('mom_weight', 'top_pct'),
    'quality_low_vol':           ('vol_weight', 'top_pct'),
    'composite_factor_score':    ('momentum_weight', 'lookback'),
    'volatility_targeting':      ('target_vol', 'vol_lookback'),
    'earnings_surprise_momentum': ('drift_period', 'volume_spike_mult'),
}


def safe_float(v):
    """Convert to JSON-safe float."""
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return round(float(v), 6)


def run_single_backtest(strategy_name, data, params):
    """Run one backtest with given params, return key metrics."""
    try:
        strategy = get_strategy(strategy_name, data, params)
        backtester = Backtester(strategy, data, initial_capital=100000)
        result = backtester.run()
        return {
            'sharpe_ratio':  safe_float(result.metrics.get('sharpe_ratio')),
            'total_return':  safe_float(result.metrics.get('total_return')),
            'cagr':          safe_float(result.metrics.get('cagr')),
            'max_drawdown':  safe_float(result.metrics.get('max_drawdown')),
            'calmar_ratio':  safe_float(result.metrics.get('calmar_ratio')),
            'volatility':    safe_float(result.metrics.get('volatility')),
            'sortino_ratio': safe_float(result.metrics.get('sortino_ratio')),
            'win_rate':      safe_float(result.metrics.get('win_rate')),
            'profit_factor': safe_float(result.metrics.get('profit_factor')),
            'avg_turnover':  safe_float(result.metrics.get('avg_turnover')),
        }
    except Exception as e:
        logger.warning(f"  Failed with params {params}: {e}")
        return None


def run_1d_sweeps(strategy_name, data, sweep_config):
    """Run 1D parameter sweeps: vary one param at a time, hold others at default."""
    strategy_class = STRATEGY_REGISTRY[strategy_name]
    defaults = strategy_class.DEFAULT_PARAMS.copy()
    results = {}

    for param_name, values in sweep_config.items():
        logger.info(f"  Sweeping {param_name}: {values}")
        param_results = []

        for val in values:
            params = defaults.copy()
            params[param_name] = val
            metrics = run_single_backtest(strategy_name, data, params)
            if metrics:
                param_results.append({
                    'param_value': val,
                    'default_value': defaults.get(param_name),
                    **metrics
                })

        results[param_name] = param_results

    return results


def run_2d_heatmap(strategy_name, data, sweep_config, param_pair):
    """Run 2D sweep over two params, producing a heatmap grid."""
    strategy_class = STRATEGY_REGISTRY[strategy_name]
    defaults = strategy_class.DEFAULT_PARAMS.copy()

    p1, p2 = param_pair
    if p1 not in sweep_config or p2 not in sweep_config:
        return None

    vals1 = sweep_config[p1]
    vals2 = sweep_config[p2]
    results = []

    for v1, v2 in product(vals1, vals2):
        params = defaults.copy()
        params[p1] = v1
        params[p2] = v2
        metrics = run_single_backtest(strategy_name, data, params)
        if metrics:
            results.append({
                p1: v1,
                p2: v2,
                **metrics
            })

    return {
        'param_1': p1,
        'param_2': p2,
        'values_1': [v if not isinstance(v, float) else v for v in vals1],
        'values_2': [v if not isinstance(v, float) else v for v in vals2],
        'grid': results,
    }


def analyze_robustness(sweep_results):
    """
    Analyze robustness from 1D sweep results.
    Returns a summary dict per parameter.
    """
    analysis = {}

    for param_name, results in sweep_results.items():
        if not results:
            continue

        sharpes = [r['sharpe_ratio'] for r in results if r['sharpe_ratio'] is not None]
        if not sharpes:
            continue

        best_idx = np.argmax(sharpes)
        best_val = results[best_idx]['param_value']
        default_val = results[0]['default_value']

        # Find default result
        default_sharpe = None
        for r in results:
            if r['param_value'] == default_val:
                default_sharpe = r['sharpe_ratio']
                break

        # Coefficient of variation of Sharpe across sweep
        sharpe_mean = np.mean(sharpes)
        sharpe_std = np.std(sharpes)
        sharpe_range = max(sharpes) - min(sharpes)

        # Robustness score: lower CV = more robust
        # < 0.15 = very robust, 0.15-0.30 = moderate, > 0.30 = fragile
        cv = sharpe_std / abs(sharpe_mean) if sharpe_mean != 0 else float('inf')

        # Check if all sharpes are positive (consistently profitable)
        all_positive = all(s > 0 for s in sharpes)

        analysis[param_name] = {
            'n_values_tested': len(sharpes),
            'sharpe_min': round(min(sharpes), 3),
            'sharpe_max': round(max(sharpes), 3),
            'sharpe_mean': round(sharpe_mean, 3),
            'sharpe_std': round(sharpe_std, 3),
            'sharpe_range': round(sharpe_range, 3),
            'coefficient_of_variation': round(cv, 3),
            'best_value': best_val,
            'best_sharpe': round(max(sharpes), 3),
            'default_value': default_val,
            'default_sharpe': round(default_sharpe, 3) if default_sharpe else None,
            'all_positive_sharpe': all_positive,
            'robustness': (
                'ROBUST' if cv < 0.15 else
                'MODERATE' if cv < 0.30 else
                'FRAGILE'
            ),
        }

    return analysis


def print_strategy_summary(strategy_name, sweep_results, robustness):
    """Print a formatted summary for one strategy."""
    print(f"\n{'=' * 70}")
    print(f"  {strategy_name.upper().replace('_', ' ')}")
    print(f"{'=' * 70}")

    for param_name, analysis in robustness.items():
        results = sweep_results[param_name]
        rob_label = analysis['robustness']
        indicator = {'ROBUST': '+', 'MODERATE': '~', 'FRAGILE': '!'}[rob_label]

        print(f"\n  [{indicator}] {param_name} — {rob_label}")
        print(f"      Default: {analysis['default_value']} (Sharpe: {analysis['default_sharpe']})")
        print(f"      Best:    {analysis['best_value']} (Sharpe: {analysis['best_sharpe']})")
        print(f"      Range:   Sharpe {analysis['sharpe_min']} to {analysis['sharpe_max']} "
              f"(CV: {analysis['coefficient_of_variation']:.2f})")

        # Show all values
        vals_str = "      Values:  "
        for r in results:
            s = r['sharpe_ratio']
            marker = '*' if r['param_value'] == analysis['default_value'] else ' '
            vals_str += f"{r['param_value']}{marker}({s:.2f}) "
        print(vals_str)

    # Overall strategy robustness
    robustness_scores = [a['robustness'] for a in robustness.values()]
    fragile_count = robustness_scores.count('FRAGILE')
    robust_count = robustness_scores.count('ROBUST')

    print(f"\n  OVERALL: {robust_count} robust, "
          f"{robustness_scores.count('MODERATE')} moderate, "
          f"{fragile_count} fragile params")

    if fragile_count == 0:
        print("  >>> Strategy is parameter-robust — good sign for real-world use")
    elif fragile_count <= 1:
        print("  >>> Mostly robust with some sensitivity — tuning needed on fragile params")
    else:
        print("  >>> CAUTION: Multiple fragile parameters — high risk of overfitting")


def main():
    """Run parameter sensitivity analysis."""
    # Determine which strategies to run
    target_strategies = None
    if len(sys.argv) > 1:
        target_strategies = sys.argv[1:]
        # Validate
        for s in target_strategies:
            if s not in STRATEGY_REGISTRY:
                print(f"Unknown strategy: {s}")
                print(f"Available: {', '.join(STRATEGY_REGISTRY.keys())}")
                sys.exit(1)

    strategies_to_run = target_strategies or list(STRATEGY_REGISTRY.keys())

    print("=" * 70)
    print("PARAMETER SENSITIVITY ANALYSIS")
    print("=" * 70)
    print(f"Strategies: {len(strategies_to_run)}")
    total_runs = sum(
        sum(len(v) for v in PARAM_SWEEPS.get(s, {}).values())
        for s in strategies_to_run
    )
    print(f"Total parameter combinations: ~{total_runs} (1D) + 2D heatmaps")
    print(f"Transaction costs: 10 bps commission + 5 bps slippage (always on)")
    print()

    # Load data
    logger.info("Loading price data...")
    data = pd.read_parquet('data_processed/prices_clean.parquet')
    logger.info(f"Loaded {len(data)} rows, {data['symbol'].nunique()} symbols")
    print()

    output_dir = Path('results/parameter_sensitivity')
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results = {}
    all_robustness = {}
    start_time = time.time()

    for strategy_name in strategies_to_run:
        sweep_config = PARAM_SWEEPS.get(strategy_name)
        if not sweep_config:
            logger.warning(f"No sweep config for {strategy_name}, skipping")
            continue

        logger.info(f"\n{'─' * 50}")
        logger.info(f"Analyzing: {strategy_name}")
        logger.info(f"{'─' * 50}")

        # 1D sweeps
        sweep_results = run_1d_sweeps(strategy_name, data, sweep_config)

        # 2D heatmap
        heatmap_pair = HEATMAP_PAIRS.get(strategy_name)
        heatmap_results = None
        if heatmap_pair:
            logger.info(f"  2D heatmap: {heatmap_pair[0]} × {heatmap_pair[1]}")
            heatmap_results = run_2d_heatmap(strategy_name, data, sweep_config, heatmap_pair)

        # Robustness analysis
        robustness = analyze_robustness(sweep_results)

        # Print summary
        print_strategy_summary(strategy_name, sweep_results, robustness)

        # Save individual strategy results
        strategy_output = {
            'strategy': strategy_name,
            'defaults': STRATEGY_REGISTRY[strategy_name].DEFAULT_PARAMS,
            'sweep_1d': sweep_results,
            'heatmap_2d': heatmap_results,
            'robustness': robustness,
        }

        output_file = output_dir / f'{strategy_name}.json'
        with open(output_file, 'w') as f:
            json.dump(strategy_output, f, indent=2, default=str)

        all_results[strategy_name] = strategy_output
        all_robustness[strategy_name] = robustness

    elapsed = time.time() - start_time

    # ─── Summary across all strategies ────────────────────────────────────────
    print()
    print("=" * 70)
    print("OVERALL PARAMETER SENSITIVITY SUMMARY")
    print("=" * 70)
    print()
    print(f"{'Strategy':<30} {'Robust':>8} {'Moderate':>10} {'Fragile':>9} {'Verdict':>12}")
    print("-" * 70)

    strategy_verdicts = {}
    for strategy_name, robustness in all_robustness.items():
        scores = [a['robustness'] for a in robustness.values()]
        r = scores.count('ROBUST')
        m = scores.count('MODERATE')
        f = scores.count('FRAGILE')

        if f == 0 and r >= m:
            verdict = 'ROBUST'
        elif f <= 1:
            verdict = 'OK'
        else:
            verdict = 'FRAGILE'

        strategy_verdicts[strategy_name] = verdict
        display = strategy_name.replace('_', ' ')[:28]
        print(f"{display:<30} {r:>8} {m:>10} {f:>9} {verdict:>12}")

    # Save master summary
    summary_file = output_dir / 'summary.json'
    summary = {
        'generated_at': pd.Timestamp.now().isoformat(),
        'data_period': '2014-2017',
        'transaction_costs': '10 bps commission + 5 bps slippage',
        'strategies_analyzed': len(all_robustness),
        'elapsed_seconds': round(elapsed, 1),
        'verdicts': strategy_verdicts,
        'robustness_details': all_robustness,
    }
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    # Also save a flat CSV for easy viewing
    csv_rows = []
    for strategy_name, robustness in all_robustness.items():
        for param_name, analysis in robustness.items():
            csv_rows.append({
                'strategy': strategy_name,
                'parameter': param_name,
                'default_value': analysis['default_value'],
                'best_value': analysis['best_value'],
                'default_sharpe': analysis['default_sharpe'],
                'best_sharpe': analysis['best_sharpe'],
                'sharpe_min': analysis['sharpe_min'],
                'sharpe_max': analysis['sharpe_max'],
                'sharpe_range': analysis['sharpe_range'],
                'cv': analysis['coefficient_of_variation'],
                'robustness': analysis['robustness'],
            })

    csv_df = pd.DataFrame(csv_rows)
    csv_file = output_dir / 'sensitivity_summary.csv'
    csv_df.to_csv(csv_file, index=False)

    print()
    print(f"Time elapsed: {elapsed:.0f}s")
    print(f"Results saved to: {output_dir}/")
    print(f"  - Individual JSON per strategy")
    print(f"  - summary.json (master overview)")
    print(f"  - sensitivity_summary.csv (flat table)")
    print()
    print("Legend: [+] ROBUST  [~] MODERATE  [!] FRAGILE")
    print("CV (Coefficient of Variation): <0.15 = robust, 0.15-0.30 = moderate, >0.30 = fragile")


if __name__ == '__main__':
    main()
