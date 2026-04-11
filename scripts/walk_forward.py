"""
Walk-Forward + Out-of-Sample Analysis

Implements two levels of validation:

1. Simple OOS Split (70/30):
   - Train on 2014-01 to ~2016-10
   - Test on ~2016-10 to 2017-12
   - Compare IS Sharpe vs OOS Sharpe
   - Measure degradation percentage

2. Rolling Walk-Forward:
   - Train window: 12 months, Test window: 6 months
   - Roll forward by 6 months
   - Chain all OOS periods together
   - Report average OOS Sharpe and Walk-Forward Efficiency (WFE)

Transaction costs are ALWAYS on (10 bps commission + 5 bps slippage).

Usage:
    python scripts/walk_forward.py                          # All strategies
    python scripts/walk_forward.py large_cap_momentum       # One strategy
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
from src.backtesting.metrics import calculate_metrics

# Configure logging
logger.remove()
logger.add(lambda msg: print(msg, end=""), format="{time:HH:mm:ss} | {message}\n", level="INFO")


def safe_float(v):
    """Convert to JSON-safe float."""
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return round(float(v), 6)


def run_backtest_on_period(strategy_name, full_data, start_date, end_date,
                           lookback_buffer_days=400, params=None):
    """
    Run a backtest on a specific time period.

    Includes a lookback buffer BEFORE start_date so strategies with long
    lookback windows (e.g., 252-day momentum) can compute signals properly.
    Performance metrics are measured ONLY on [start_date, end_date].

    Args:
        strategy_name: Strategy key from STRATEGY_REGISTRY
        full_data: Full price data (long format)
        start_date: Start of evaluation period
        end_date: End of evaluation period
        lookback_buffer_days: Calendar days of extra data before start_date
        params: Strategy params (uses defaults if None)

    Returns:
        dict with metrics, or None on failure
    """
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)

    # Include buffer before start_date for lookback calculations
    buffer_start = start_ts - pd.Timedelta(days=lookback_buffer_days)

    period_data = full_data[
        (full_data['date'] >= buffer_start) &
        (full_data['date'] <= end_ts)
    ].copy()

    if len(period_data) < 100:
        return None

    # Check we have enough data in the actual evaluation window
    eval_data = period_data[period_data['date'] >= start_ts]
    n_eval_dates = eval_data['date'].nunique()
    if n_eval_dates < 20:
        return None

    try:
        strategy_class = STRATEGY_REGISTRY[strategy_name]
        if params is None:
            params = strategy_class.DEFAULT_PARAMS.copy()

        strategy = get_strategy(strategy_name, period_data, params)
        backtester = Backtester(strategy, period_data, initial_capital=100000)
        result = backtester.run()

        # Slice returns to ONLY the evaluation period [start_date, end_date]
        eval_returns = result.returns[result.returns.index >= start_ts]

        if len(eval_returns) < 20:
            return None

        # Rebuild equity curve for the evaluation period
        eval_equity = 100000 * (1 + eval_returns).cumprod()

        # Calculate metrics on evaluation period only
        metrics = calculate_metrics(
            returns=eval_returns,
            equity_curve=eval_equity,
            risk_free_rate=0.02
        )

        return {
            'sharpe_ratio': safe_float(metrics.get('sharpe_ratio')),
            'total_return': safe_float(metrics.get('total_return')),
            'cagr': safe_float(metrics.get('cagr')),
            'max_drawdown': safe_float(metrics.get('max_drawdown')),
            'calmar_ratio': safe_float(metrics.get('calmar_ratio')),
            'volatility': safe_float(metrics.get('volatility')),
            'sortino_ratio': safe_float(metrics.get('sortino_ratio')),
            'win_rate': safe_float(metrics.get('win_rate')),
            'profit_factor': safe_float(metrics.get('profit_factor')),
            'avg_turnover': safe_float(metrics.get('avg_turnover')),
            'n_days': len(eval_returns),
            'start': str(start_date)[:10],
            'end': str(end_date)[:10],
        }
    except Exception as e:
        logger.warning(f"  Backtest failed on {start_date} to {end_date}: {e}")
        return None


def simple_oos_split(strategy_name, data, train_frac=0.70):
    """
    Simple out-of-sample split.
    Train on first 70%, test on last 30%.
    """
    dates = sorted(data['date'].unique())
    split_idx = int(len(dates) * train_frac)
    split_date = dates[split_idx]

    train_start = dates[0]
    train_end = split_date
    test_start = split_date
    test_end = dates[-1]

    logger.info(f"  OOS Split: Train [{str(train_start)[:10]} to {str(train_end)[:10]}] "
                f"| Test [{str(test_start)[:10]} to {str(test_end)[:10]}]")

    is_result = run_backtest_on_period(strategy_name, data, train_start, train_end)
    oos_result = run_backtest_on_period(strategy_name, data, test_start, test_end)

    if not is_result or not oos_result:
        return None

    # Also run on full period for reference
    full_result = run_backtest_on_period(strategy_name, data, train_start, test_end)

    # Calculate degradation
    is_sharpe = is_result['sharpe_ratio'] or 0
    oos_sharpe = oos_result['sharpe_ratio'] or 0

    if is_sharpe != 0:
        degradation = (is_sharpe - oos_sharpe) / abs(is_sharpe)
    else:
        degradation = None

    # Interpret
    if degradation is not None:
        if degradation <= 0.20:
            verdict = 'EXCELLENT'
        elif degradation <= 0.40:
            verdict = 'ACCEPTABLE'
        elif degradation <= 0.60:
            verdict = 'CONCERNING'
        else:
            verdict = 'LIKELY_OVERFIT'

        # If OOS actually improved (negative degradation)
        if degradation < 0:
            verdict = 'EXCELLENT'
    else:
        verdict = 'UNKNOWN'

    return {
        'method': 'simple_oos_split',
        'train_frac': train_frac,
        'train_period': f"{str(train_start)[:10]} to {str(train_end)[:10]}",
        'test_period': f"{str(test_start)[:10]} to {str(test_end)[:10]}",
        'in_sample': is_result,
        'out_of_sample': oos_result,
        'full_period': full_result,
        'is_sharpe': round(is_sharpe, 3),
        'oos_sharpe': round(oos_sharpe, 3),
        'degradation_pct': round(degradation * 100, 1) if degradation is not None else None,
        'verdict': verdict,
    }


def rolling_walk_forward(strategy_name, data, train_months=12, test_months=6):
    """
    Rolling walk-forward analysis.
    Fixed training window, roll forward by test_months.
    """
    dates = sorted(data['date'].unique())
    start = pd.Timestamp(dates[0])
    end = pd.Timestamp(dates[-1])

    folds = []
    fold_num = 0
    current_train_start = start

    while True:
        train_end = current_train_start + pd.DateOffset(months=train_months)
        test_start = train_end
        test_end = test_start + pd.DateOffset(months=test_months)

        # Stop if test period goes beyond data
        if test_end > end:
            # Try with whatever data is left
            test_end = end
            if test_start >= end:
                break

        fold_num += 1
        logger.info(f"  Fold {fold_num}: Train [{str(current_train_start)[:10]} to "
                    f"{str(train_end)[:10]}] → Test [{str(test_start)[:10]} to {str(test_end)[:10]}]")

        is_result = run_backtest_on_period(strategy_name, data, current_train_start, train_end)
        oos_result = run_backtest_on_period(strategy_name, data, test_start, test_end)

        if is_result and oos_result:
            folds.append({
                'fold': fold_num,
                'train_period': f"{str(current_train_start)[:10]} to {str(train_end)[:10]}",
                'test_period': f"{str(test_start)[:10]} to {str(test_end)[:10]}",
                'is_sharpe': is_result['sharpe_ratio'],
                'oos_sharpe': oos_result['sharpe_ratio'],
                'is_return': is_result['total_return'],
                'oos_return': oos_result['total_return'],
                'is_max_dd': is_result['max_drawdown'],
                'oos_max_dd': oos_result['max_drawdown'],
                'is_metrics': is_result,
                'oos_metrics': oos_result,
            })

        # Roll forward by test_months
        current_train_start = current_train_start + pd.DateOffset(months=test_months)

        # Safety: stop if we've gone past data
        if current_train_start + pd.DateOffset(months=train_months) > end:
            break

    if not folds:
        return None

    # Aggregate results
    is_sharpes = [f['is_sharpe'] for f in folds if f['is_sharpe'] is not None]
    oos_sharpes = [f['oos_sharpe'] for f in folds if f['oos_sharpe'] is not None]

    avg_is = np.mean(is_sharpes) if is_sharpes else 0
    avg_oos = np.mean(oos_sharpes) if oos_sharpes else 0

    # Walk-Forward Efficiency
    wfe = (avg_oos / avg_is * 100) if avg_is != 0 else None

    # Count how many folds had positive OOS Sharpe
    positive_oos = sum(1 for s in oos_sharpes if s and s > 0)

    # Verdict
    if wfe is not None:
        if wfe >= 80:
            verdict = 'EXCELLENT'
        elif wfe >= 50:
            verdict = 'GOOD'
        elif wfe >= 20:
            verdict = 'ACCEPTABLE'
        elif wfe >= 0:
            verdict = 'WEAK'
        else:
            verdict = 'FAILING'
    else:
        verdict = 'UNKNOWN'

    # OOS consistency
    if len(oos_sharpes) > 0:
        consistency = positive_oos / len(oos_sharpes)
    else:
        consistency = 0

    return {
        'method': 'rolling_walk_forward',
        'train_months': train_months,
        'test_months': test_months,
        'n_folds': len(folds),
        'folds': folds,
        'avg_is_sharpe': round(avg_is, 3),
        'avg_oos_sharpe': round(avg_oos, 3),
        'wfe_pct': round(wfe, 1) if wfe is not None else None,
        'positive_oos_folds': positive_oos,
        'total_folds': len(folds),
        'consistency_pct': round(consistency * 100, 1),
        'verdict': verdict,
    }


def print_strategy_results(strategy_name, oos_split, walk_forward):
    """Print formatted results for one strategy."""
    print(f"\n{'=' * 70}")
    print(f"  {strategy_name.upper().replace('_', ' ')}")
    print(f"{'=' * 70}")

    if oos_split:
        d = oos_split['degradation_pct']
        deg_str = f"{d:+.1f}%" if d is not None else "N/A"

        print(f"\n  SIMPLE OOS SPLIT (70/30)")
        print(f"  ├─ In-Sample Sharpe:  {oos_split['is_sharpe']:.3f}  "
              f"({oos_split['train_period']})")
        print(f"  ├─ OOS Sharpe:        {oos_split['oos_sharpe']:.3f}  "
              f"({oos_split['test_period']})")
        print(f"  ├─ Degradation:       {deg_str}")
        print(f"  └─ Verdict:           {oos_split['verdict']}")

    if walk_forward:
        print(f"\n  ROLLING WALK-FORWARD ({walk_forward['train_months']}mo train → "
              f"{walk_forward['test_months']}mo test)")
        print(f"  ├─ Folds:             {walk_forward['n_folds']}")
        print(f"  ├─ Avg IS Sharpe:     {walk_forward['avg_is_sharpe']:.3f}")
        print(f"  ├─ Avg OOS Sharpe:    {walk_forward['avg_oos_sharpe']:.3f}")
        wfe = walk_forward['wfe_pct']
        wfe_str = f"{wfe:.1f}%" if wfe is not None else "N/A"
        print(f"  ├─ WFE:               {wfe_str}")
        print(f"  ├─ Consistency:       {walk_forward['positive_oos_folds']}/"
              f"{walk_forward['total_folds']} folds positive "
              f"({walk_forward['consistency_pct']:.0f}%)")
        print(f"  └─ Verdict:           {walk_forward['verdict']}")

        # Show per-fold breakdown
        print(f"\n  Per-Fold Detail:")
        print(f"  {'Fold':>6}  {'IS Sharpe':>10}  {'OOS Sharpe':>11}  {'OOS Return':>11}  {'OOS MaxDD':>10}")
        print(f"  {'-'*52}")
        for f in walk_forward['folds']:
            is_s = f"{f['is_sharpe']:.2f}" if f['is_sharpe'] is not None else "N/A"
            oos_s = f"{f['oos_sharpe']:.2f}" if f['oos_sharpe'] is not None else "N/A"
            oos_r = f"{f['oos_return']:.1%}" if f['oos_return'] is not None else "N/A"
            oos_dd = f"{f['oos_max_dd']:.1%}" if f['oos_max_dd'] is not None else "N/A"
            print(f"  {f['fold']:>6}  {is_s:>10}  {oos_s:>11}  {oos_r:>11}  {oos_dd:>10}")


def main():
    """Run walk-forward and OOS analysis."""
    # Determine strategies
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
    print("WALK-FORWARD + OUT-OF-SAMPLE ANALYSIS")
    print("=" * 70)
    print(f"Strategies: {len(strategies)}")
    print(f"Method 1: Simple OOS split (70% train / 30% test)")
    print(f"Method 2: Rolling walk-forward (12mo train → 6mo test, rolling)")
    print(f"Transaction costs: 10 bps commission + 5 bps slippage (always on)")
    print()

    # Load data
    logger.info("Loading price data...")
    data = pd.read_parquet('data_processed/prices_clean.parquet')
    data['date'] = pd.to_datetime(data['date'])
    logger.info(f"Loaded {len(data)} rows, {data['symbol'].nunique()} symbols")
    logger.info(f"Date range: {data['date'].min().date()} to {data['date'].max().date()}")
    print()

    output_dir = Path('results/walk_forward')
    output_dir.mkdir(parents=True, exist_ok=True)

    all_results = {}
    start_time = time.time()

    for strategy_name in strategies:
        logger.info(f"\n{'─' * 50}")
        logger.info(f"Analyzing: {strategy_name}")
        logger.info(f"{'─' * 50}")

        # Method 1: Simple OOS split
        oos_result = simple_oos_split(strategy_name, data, train_frac=0.70)

        # Method 2: Rolling walk-forward
        wf_result = rolling_walk_forward(strategy_name, data,
                                          train_months=12, test_months=6)

        # Print results
        print_strategy_results(strategy_name, oos_result, wf_result)

        # Store
        strategy_output = {
            'strategy': strategy_name,
            'simple_oos': oos_result,
            'walk_forward': wf_result,
        }

        # Save individual file
        with open(output_dir / f'{strategy_name}.json', 'w') as f:
            json.dump(strategy_output, f, indent=2, default=str)

        all_results[strategy_name] = strategy_output

    elapsed = time.time() - start_time

    # ─── Overall Summary ─────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("OVERALL WALK-FORWARD SUMMARY")
    print("=" * 70)
    print()
    print(f"{'Strategy':<30} {'IS Sharpe':>10} {'OOS Sharpe':>11} {'Degrad%':>8} "
          f"{'WFE%':>6} {'Consist':>8} {'Verdict':>10}")
    print("-" * 85)

    summary_rows = []
    for name, result in all_results.items():
        oos = result.get('simple_oos')
        wf = result.get('walk_forward')

        is_s = f"{oos['is_sharpe']:.2f}" if oos and oos.get('is_sharpe') is not None else "—"
        oos_s = f"{oos['oos_sharpe']:.2f}" if oos and oos.get('oos_sharpe') is not None else "—"
        deg = f"{oos['degradation_pct']:+.0f}%" if oos and oos.get('degradation_pct') is not None else "—"
        wfe = f"{wf['wfe_pct']:.0f}%" if wf and wf.get('wfe_pct') is not None else "—"
        cons = f"{wf['consistency_pct']:.0f}%" if wf and wf.get('consistency_pct') is not None else "—"

        # Combined verdict: use the more conservative of the two
        oos_verdict = oos.get('verdict', 'UNKNOWN') if oos else 'UNKNOWN'
        wf_verdict = wf.get('verdict', 'UNKNOWN') if wf else 'UNKNOWN'

        # Priority order for verdict severity
        severity = {'EXCELLENT': 0, 'GOOD': 1, 'ACCEPTABLE': 2,
                   'CONCERNING': 3, 'WEAK': 3, 'LIKELY_OVERFIT': 4,
                   'FAILING': 5, 'UNKNOWN': 6}
        v1 = severity.get(oos_verdict, 6)
        v2 = severity.get(wf_verdict, 6)
        combined = oos_verdict if v1 >= v2 else wf_verdict

        display = name.replace('_', ' ')[:28]
        print(f"{display:<30} {is_s:>10} {oos_s:>11} {deg:>8} {wfe:>6} {cons:>8} {combined:>10}")

        summary_rows.append({
            'strategy': name,
            'is_sharpe': oos['is_sharpe'] if oos else None,
            'oos_sharpe': oos['oos_sharpe'] if oos else None,
            'degradation_pct': oos['degradation_pct'] if oos else None,
            'oos_verdict': oos_verdict,
            'wf_avg_oos_sharpe': wf['avg_oos_sharpe'] if wf else None,
            'wfe_pct': wf['wfe_pct'] if wf else None,
            'wf_consistency_pct': wf['consistency_pct'] if wf else None,
            'wf_verdict': wf_verdict,
            'combined_verdict': combined,
        })

    # Save summary
    summary = {
        'generated_at': pd.Timestamp.now().isoformat(),
        'data_period': '2014-2017',
        'transaction_costs': '10 bps commission + 5 bps slippage',
        'oos_split': '70% train / 30% test',
        'walk_forward': '12mo train / 6mo test / rolling',
        'elapsed_seconds': round(elapsed, 1),
        'strategies': summary_rows,
    }

    with open(output_dir / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    # CSV
    pd.DataFrame(summary_rows).to_csv(output_dir / 'walk_forward_summary.csv', index=False)

    print()
    print(f"Time elapsed: {elapsed:.0f}s")
    print(f"Results saved to: {output_dir}/")
    print()
    print("Verdict guide:")
    print("  EXCELLENT: OOS ≈ IS, WFE ≥ 80% — strategy is genuine")
    print("  GOOD:      Minor degradation, WFE ≥ 50% — likely real edge")
    print("  ACCEPTABLE: Moderate degradation, WFE ≥ 20% — edge exists but weaker than IS suggests")
    print("  WEAK/CONCERNING: Significant degradation — handle with caution")
    print("  FAILING/LIKELY_OVERFIT: OOS performance collapse — strategy may not be real")


if __name__ == '__main__':
    main()
