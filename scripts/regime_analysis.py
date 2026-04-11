"""
Market Regime Analysis (Phase 2.4)

Classifies market days into regimes (Bull, Bear, High-Vol, Sideways) using
a simple trend + volatility framework, then measures each strategy's
performance within each regime.

This answers: "WHEN does each strategy work and when does it fail?"

Usage:
    .venv/bin/python scripts/regime_analysis.py
    .venv/bin/python scripts/regime_analysis.py large_cap_momentum
"""

import sys
import os
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from datetime import datetime

warnings.filterwarnings('ignore')

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.backtesting.engine import Backtester
from src.backtesting.metrics import calculate_metrics
from src.strategies import get_strategy, STRATEGY_REGISTRY

# ── Configuration ────────────────────────────────────────────────────────────

# Regime detection parameters
TREND_WINDOW = 63          # ~3 months for trend measurement
VOL_WINDOW = 63            # ~3 months for realized volatility
BULL_RETURN_THRESHOLD = 0.05   # 63-day return > +5%
BEAR_RETURN_THRESHOLD = -0.05  # 63-day return < -5%
HIGH_VOL_THRESHOLD = 0.20      # Annualized vol > 20%

# Results directory
RESULTS_DIR = PROJECT_ROOT / 'results' / 'regime_analysis'


def safe_float(val):
    """Convert to JSON-safe float"""
    if val is None or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
        return 0.0
    return float(val)


# ── Regime Detection ─────────────────────────────────────────────────────────

def compute_market_index(data: pd.DataFrame) -> pd.Series:
    """
    Compute an equal-weighted market index from all stocks.
    Returns a daily return series for the "market".
    """
    # Pivot to wide format: date × symbol → close price
    prices = data.pivot(index='date', columns='symbol', values='close')

    # Daily returns for each stock
    returns = prices.pct_change()

    # Equal-weighted market return = mean across all stocks each day
    market_return = returns.mean(axis=1)

    return market_return


def classify_regimes(market_returns: pd.Series) -> pd.DataFrame:
    """
    Classify each trading day into a market regime.

    Method: Simple Trend + Volatility
    - Bull:     63-day cumulative return > +5% AND annualized vol < 20%
    - Bear:     63-day cumulative return < -5%
    - High-Vol: Annualized 63-day vol > 20% (but not bear)
    - Sideways: Everything else

    Returns DataFrame with columns: [date, market_return, cum_return_63d,
                                     ann_vol_63d, regime]
    """
    df = pd.DataFrame({
        'market_return': market_returns
    })

    # Rolling 63-day cumulative return (compound)
    df['cum_return_63d'] = (1 + df['market_return']).rolling(TREND_WINDOW).apply(
        lambda x: x.prod() - 1, raw=True
    )

    # Rolling 63-day annualized volatility
    df['ann_vol_63d'] = df['market_return'].rolling(VOL_WINDOW).std() * np.sqrt(252)

    # Classify regimes
    conditions = [
        # Bear: negative trend (check first — bear overrides high-vol)
        df['cum_return_63d'] < BEAR_RETURN_THRESHOLD,
        # Bull: positive trend AND low vol
        (df['cum_return_63d'] > BULL_RETURN_THRESHOLD) & (df['ann_vol_63d'] < HIGH_VOL_THRESHOLD),
        # High-Vol: elevated vol but not bear
        df['ann_vol_63d'] >= HIGH_VOL_THRESHOLD,
    ]
    choices = ['Bear', 'Bull', 'High-Vol']
    df['regime'] = np.select(conditions, choices, default='Sideways')

    # Drop warmup period (first 63 days have NaN rolling stats)
    df = df.dropna(subset=['cum_return_63d', 'ann_vol_63d'])

    return df


def get_regime_summary(regime_df: pd.DataFrame) -> dict:
    """Summarize the regime classification"""
    total_days = len(regime_df)
    summary = {}

    for regime in ['Bull', 'Bear', 'High-Vol', 'Sideways']:
        mask = regime_df['regime'] == regime
        n_days = mask.sum()
        pct = n_days / total_days * 100 if total_days > 0 else 0

        regime_returns = regime_df.loc[mask, 'market_return']
        ann_ret = regime_returns.mean() * 252 if len(regime_returns) > 0 else 0
        ann_vol = regime_returns.std() * np.sqrt(252) if len(regime_returns) > 1 else 0

        summary[regime] = {
            'n_days': int(n_days),
            'pct_of_total': safe_float(pct),
            'ann_market_return': safe_float(ann_ret),
            'ann_market_vol': safe_float(ann_vol),
        }

    return summary


# ── Per-Strategy Regime Analysis ─────────────────────────────────────────────

def get_strategy_returns(strategy_name: str, data: pd.DataFrame) -> pd.Series:
    """Run a strategy backtest and return the daily returns series."""
    strategy = get_strategy(strategy_name, data)
    backtester = Backtester(strategy, data, initial_capital=100000)
    result = backtester.run()
    return result.returns


def analyze_strategy_by_regime(
    strategy_returns: pd.Series,
    regime_df: pd.DataFrame,
) -> dict:
    """
    Calculate strategy performance metrics within each regime.

    Returns dict of regime → metrics.
    """
    results = {}

    # Align strategy returns with regime dates
    aligned = pd.DataFrame({
        'strategy_return': strategy_returns,
        'regime': regime_df['regime'],
        'market_return': regime_df['market_return'],
    }).dropna()

    for regime in ['Bull', 'Bear', 'High-Vol', 'Sideways']:
        mask = aligned['regime'] == regime
        regime_returns = aligned.loc[mask, 'strategy_return']
        market_returns_regime = aligned.loc[mask, 'market_return']

        n_days = len(regime_returns)
        if n_days < 5:
            results[regime] = {
                'n_days': n_days,
                'sharpe': 0.0,
                'ann_return': 0.0,
                'ann_vol': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'avg_daily_return': 0.0,
                'market_ann_return': 0.0,
                'excess_return': 0.0,
                'sortino': 0.0,
                'worst_day': 0.0,
                'best_day': 0.0,
            }
            continue

        # Annualized metrics
        mean_daily = regime_returns.mean()
        std_daily = regime_returns.std()
        ann_return = mean_daily * 252
        ann_vol = std_daily * np.sqrt(252)

        # Sharpe (annualized)
        daily_rf = 0.02 / 252
        sharpe = np.sqrt(252) * (mean_daily - daily_rf) / std_daily if std_daily > 0 else 0

        # Sortino
        downside = regime_returns[regime_returns < 0]
        downside_std = downside.std() * np.sqrt(252) if len(downside) > 1 else 0
        sortino = (ann_return - 0.02) / downside_std if downside_std > 0 else 0

        # Max drawdown within regime (using contiguous regime days)
        equity = (1 + regime_returns).cumprod()
        running_max = equity.cummax()
        drawdown = (equity / running_max) - 1
        max_dd = drawdown.min()

        # Win rate
        win_rate = (regime_returns > 0).sum() / n_days if n_days > 0 else 0

        # Market return in this regime
        mkt_ann = market_returns_regime.mean() * 252

        results[regime] = {
            'n_days': int(n_days),
            'sharpe': safe_float(sharpe),
            'ann_return': safe_float(ann_return),
            'ann_vol': safe_float(ann_vol),
            'max_drawdown': safe_float(max_dd),
            'win_rate': safe_float(win_rate),
            'avg_daily_return': safe_float(mean_daily),
            'market_ann_return': safe_float(mkt_ann),
            'excess_return': safe_float(ann_return - mkt_ann),
            'sortino': safe_float(sortino),
            'worst_day': safe_float(regime_returns.min()),
            'best_day': safe_float(regime_returns.max()),
        }

    # Overall metrics (for comparison)
    overall_returns = aligned['strategy_return']
    overall_mean = overall_returns.mean()
    overall_std = overall_returns.std()
    results['Overall'] = {
        'n_days': int(len(overall_returns)),
        'sharpe': safe_float(np.sqrt(252) * (overall_mean - 0.02/252) / overall_std if overall_std > 0 else 0),
        'ann_return': safe_float(overall_mean * 252),
        'ann_vol': safe_float(overall_std * np.sqrt(252)),
    }

    return results


def compute_regime_edge_score(regime_results: dict) -> dict:
    """
    Compute a regime edge score for each strategy.

    Edge Score = how much the strategy's regime-conditional Sharpe deviates
    from its overall Sharpe. Positive = strategy exploits that regime.

    Also identifies:
    - best_regime: where it performs best
    - worst_regime: where it suffers most
    - regime_spread: best Sharpe - worst Sharpe (higher = more regime-dependent)
    """
    overall_sharpe = regime_results.get('Overall', {}).get('sharpe', 0)

    regime_sharpes = {}
    for regime in ['Bull', 'Bear', 'High-Vol', 'Sideways']:
        if regime in regime_results:
            regime_sharpes[regime] = regime_results[regime]['sharpe']

    if not regime_sharpes:
        return {'best_regime': 'N/A', 'worst_regime': 'N/A', 'regime_spread': 0}

    best_regime = max(regime_sharpes, key=regime_sharpes.get)
    worst_regime = min(regime_sharpes, key=regime_sharpes.get)
    regime_spread = regime_sharpes[best_regime] - regime_sharpes[worst_regime]

    return {
        'overall_sharpe': safe_float(overall_sharpe),
        'best_regime': best_regime,
        'best_regime_sharpe': safe_float(regime_sharpes[best_regime]),
        'worst_regime': worst_regime,
        'worst_regime_sharpe': safe_float(regime_sharpes[worst_regime]),
        'regime_spread': safe_float(regime_spread),
        'regime_sharpes': {k: safe_float(v) for k, v in regime_sharpes.items()},
    }


# ── Regime Transition Analysis ───────────────────────────────────────────────

def analyze_regime_transitions(regime_df: pd.DataFrame) -> dict:
    """
    Analyze how often regimes change and what transitions look like.
    Useful context for understanding regime persistence.
    """
    regimes = regime_df['regime'].values
    transitions = 0
    transition_counts = {}

    for i in range(1, len(regimes)):
        if regimes[i] != regimes[i-1]:
            transitions += 1
            key = f"{regimes[i-1]} → {regimes[i]}"
            transition_counts[key] = transition_counts.get(key, 0) + 1

    # Average regime duration
    durations = []
    current_start = 0
    for i in range(1, len(regimes)):
        if regimes[i] != regimes[i-1]:
            durations.append(i - current_start)
            current_start = i
    durations.append(len(regimes) - current_start)

    return {
        'total_transitions': transitions,
        'avg_regime_duration_days': safe_float(np.mean(durations) if durations else 0),
        'median_regime_duration_days': safe_float(np.median(durations) if durations else 0),
        'top_transitions': dict(sorted(transition_counts.items(), key=lambda x: -x[1])[:10]),
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def run_regime_analysis(strategy_names=None):
    """Run regime analysis on specified strategies (or all)."""

    start_time = time.time()

    # Load data
    print("=" * 70)
    print("MARKET REGIME ANALYSIS — Phase 2.4")
    print("=" * 70)
    print()

    data_path = PROJECT_ROOT / 'data_processed' / 'prices_clean.parquet'
    data = pd.read_parquet(data_path)
    print(f"Loaded data: {len(data):,} rows, {data['symbol'].nunique()} symbols")
    print(f"Period: {data['date'].min().date()} to {data['date'].max().date()}")
    print()

    # ── Step 1: Compute market index and classify regimes ────────────────

    print("─" * 70)
    print("STEP 1: Market Regime Detection")
    print("─" * 70)
    print()

    market_returns = compute_market_index(data)
    regime_df = classify_regimes(market_returns)

    regime_summary = get_regime_summary(regime_df)
    transitions = analyze_regime_transitions(regime_df)

    print(f"Regime Classification ({TREND_WINDOW}-day trend, {VOL_WINDOW}-day vol):")
    print(f"  Bull:     63d return > +{BULL_RETURN_THRESHOLD:.0%}, vol < {HIGH_VOL_THRESHOLD:.0%}")
    print(f"  Bear:     63d return < {BEAR_RETURN_THRESHOLD:.0%}")
    print(f"  High-Vol: vol ≥ {HIGH_VOL_THRESHOLD:.0%} (not bear)")
    print(f"  Sideways: everything else")
    print()

    print(f"{'Regime':<12} {'Days':>6} {'% Total':>8} {'Ann Return':>12} {'Ann Vol':>10}")
    print("─" * 50)
    for regime in ['Bull', 'Bear', 'High-Vol', 'Sideways']:
        s = regime_summary[regime]
        print(f"{regime:<12} {s['n_days']:>6} {s['pct_of_total']:>7.1f}% "
              f"{s['ann_market_return']:>11.1%} {s['ann_market_vol']:>9.1%}")

    print()
    print(f"Regime transitions: {transitions['total_transitions']} total")
    print(f"Avg regime duration: {transitions['avg_regime_duration_days']:.0f} days")
    print()

    # ── Step 2: Analyze each strategy by regime ──────────────────────────

    if strategy_names is None:
        strategy_names = list(STRATEGY_REGISTRY.keys())

    print("─" * 70)
    print(f"STEP 2: Strategy Performance by Regime ({len(strategy_names)} strategies)")
    print("─" * 70)
    print()

    all_results = {}

    for i, name in enumerate(strategy_names, 1):
        print(f"[{i}/{len(strategy_names)}] {name}...", end=' ', flush=True)

        try:
            returns = get_strategy_returns(name, data)
            regime_results = analyze_strategy_by_regime(returns, regime_df)
            edge_score = compute_regime_edge_score(regime_results)

            all_results[name] = {
                'regime_performance': regime_results,
                'edge_score': edge_score,
            }

            # Print compact summary
            best = edge_score['best_regime']
            worst = edge_score['worst_regime']
            spread = edge_score['regime_spread']
            print(f"Best={best}({edge_score['best_regime_sharpe']:+.2f}) "
                  f"Worst={worst}({edge_score['worst_regime_sharpe']:+.2f}) "
                  f"Spread={spread:.2f}")

        except Exception as e:
            print(f"ERROR: {e}")
            all_results[name] = {'error': str(e)}

    # ── Step 3: Cross-strategy regime analysis ───────────────────────────

    print()
    print("─" * 70)
    print("STEP 3: Cross-Strategy Regime Summary")
    print("─" * 70)
    print()

    # Build summary table
    print(f"{'Strategy':<30} {'Bull':>8} {'Bear':>8} {'High-V':>8} {'Sidew':>8} {'Spread':>8} {'Best':>10} {'Worst':>10}")
    print("─" * 100)

    summary_rows = []
    for name in strategy_names:
        if 'error' in all_results.get(name, {}):
            continue

        edge = all_results[name]['edge_score']
        sharpes = edge.get('regime_sharpes', {})
        row = {
            'strategy': name,
            'Bull': sharpes.get('Bull', 0),
            'Bear': sharpes.get('Bear', 0),
            'High-Vol': sharpes.get('High-Vol', 0),
            'Sideways': sharpes.get('Sideways', 0),
            'spread': edge.get('regime_spread', 0),
            'best_regime': edge.get('best_regime', '?'),
            'worst_regime': edge.get('worst_regime', '?'),
        }
        summary_rows.append(row)

        # Colorize Sharpe values
        def fmt_sharpe(s):
            if s > 1.0:
                return f"{s:>+7.2f}★"
            elif s > 0:
                return f"{s:>+8.2f}"
            else:
                return f"{s:>+8.2f}"

        display_name = name[:29]
        print(f"{display_name:<30} {fmt_sharpe(row['Bull'])} {fmt_sharpe(row['Bear'])} "
              f"{fmt_sharpe(row['High-Vol'])} {fmt_sharpe(row['Sideways'])} "
              f"{row['spread']:>8.2f} {row['best_regime']:>10} {row['worst_regime']:>10}")

    # ── Step 4: Identify complementary pairs ─────────────────────────────

    print()
    print("─" * 70)
    print("STEP 4: Regime Complementarity")
    print("─" * 70)
    print()

    # Find strategies that do well in different regimes
    if len(summary_rows) >= 2:
        # For each pair, compute correlation of regime Sharpes
        regimes = ['Bull', 'Bear', 'High-Vol', 'Sideways']
        print("Strategies with OPPOSITE regime preferences (good portfolio candidates):")
        print()

        pairs = []
        for i in range(len(summary_rows)):
            for j in range(i+1, len(summary_rows)):
                a = summary_rows[i]
                b = summary_rows[j]
                a_vec = np.array([a[r] for r in regimes])
                b_vec = np.array([b[r] for r in regimes])
                if np.std(a_vec) > 0 and np.std(b_vec) > 0:
                    corr = np.corrcoef(a_vec, b_vec)[0, 1]
                    pairs.append((a['strategy'], b['strategy'], corr))

        # Show most complementary (lowest correlation)
        pairs.sort(key=lambda x: x[2])
        print(f"{'Strategy A':<30} {'Strategy B':<30} {'Corr':>6}")
        print("─" * 70)
        for a, b, corr in pairs[:10]:
            label = "★ COMPLEMENT" if corr < 0 else ""
            print(f"{a[:29]:<30} {b[:29]:<30} {corr:>+5.2f}  {label}")

    # ── Step 5: Strategy improvement recommendations ─────────────────────

    print()
    print("─" * 70)
    print("STEP 5: Strategy Improvement Recommendations")
    print("─" * 70)
    print()

    for name in strategy_names:
        if 'error' in all_results.get(name, {}):
            continue

        edge = all_results[name]['edge_score']
        perf = all_results[name]['regime_performance']
        worst = edge['worst_regime']
        worst_sharpe = edge['worst_regime_sharpe']
        best = edge['best_regime']
        spread = edge['regime_spread']

        # Only flag strategies with clear weaknesses
        if worst_sharpe < -0.5 or spread > 2.0:
            print(f"  {name}:")
            print(f"    Problem: Sharpe = {worst_sharpe:+.2f} in {worst} regime")
            if worst == 'Bear':
                print(f"    → Consider adding a bear market filter (e.g., exit when 200-day MA is falling)")
            elif worst == 'High-Vol':
                print(f"    → Consider scaling position size by inverse volatility")
            elif worst == 'Sideways':
                print(f"    → Strategy may be trend-dependent; consider adding a mean-reversion component")
            print()

    # ── Save Results ─────────────────────────────────────────────────────

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save per-strategy JSONs
    for name, result in all_results.items():
        fpath = RESULTS_DIR / f'{name}.json'
        with open(fpath, 'w') as f:
            json.dump(result, f, indent=2, default=str)

    # Save summary JSON
    summary = {
        'generated_at': datetime.now().isoformat(),
        'data_period': '2014-2017',
        'regime_params': {
            'trend_window': TREND_WINDOW,
            'vol_window': VOL_WINDOW,
            'bull_threshold': BULL_RETURN_THRESHOLD,
            'bear_threshold': BEAR_RETURN_THRESHOLD,
            'high_vol_threshold': HIGH_VOL_THRESHOLD,
        },
        'regime_summary': regime_summary,
        'regime_transitions': transitions,
        'strategies': [],
    }

    for name in strategy_names:
        if 'error' in all_results.get(name, {}):
            continue

        edge = all_results[name]['edge_score']
        perf = all_results[name]['regime_performance']

        entry = {
            'strategy': name,
            'overall_sharpe': edge.get('overall_sharpe', 0),
            'best_regime': edge['best_regime'],
            'best_regime_sharpe': edge['best_regime_sharpe'],
            'worst_regime': edge['worst_regime'],
            'worst_regime_sharpe': edge['worst_regime_sharpe'],
            'regime_spread': edge['regime_spread'],
        }
        for regime in ['Bull', 'Bear', 'High-Vol', 'Sideways']:
            entry[f'{regime.lower().replace("-", "_")}_sharpe'] = perf.get(regime, {}).get('sharpe', 0)
            entry[f'{regime.lower().replace("-", "_")}_ann_return'] = perf.get(regime, {}).get('ann_return', 0)
            entry[f'{regime.lower().replace("-", "_")}_max_dd'] = perf.get(regime, {}).get('max_drawdown', 0)

        summary['strategies'].append(entry)

    with open(RESULTS_DIR / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    # Save CSV summary
    if summary['strategies']:
        df = pd.DataFrame(summary['strategies'])
        df.to_csv(RESULTS_DIR / 'regime_summary.csv', index=False)

    elapsed = time.time() - start_time
    print()
    print("=" * 70)
    print(f"REGIME ANALYSIS COMPLETE — {elapsed:.1f}s")
    print(f"Results saved to: {RESULTS_DIR}/")
    print("=" * 70)

    return all_results, regime_summary, regime_df


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Run for specific strategies
        strategies = sys.argv[1:]
        run_regime_analysis(strategies)
    else:
        run_regime_analysis()
