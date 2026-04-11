"""
Transaction Cost Sensitivity Analysis (Phase 2.5)

For each strategy, sweeps total transaction costs from 0 to 100 bps and measures
how Sharpe ratio, total return, and annual turnover degrade.

Key outputs:
- Breakeven cost: The cost level at which Sharpe drops to zero
- Cost sensitivity score: How much Sharpe drops per 10 bps of cost increase
- Turnover analysis: Annual turnover drives cost sensitivity

This answers: "How expensive can trading get before each strategy stops working?"

Usage:
    .venv/bin/python scripts/transaction_cost_sensitivity.py                     # All strategies
    .venv/bin/python scripts/transaction_cost_sensitivity.py large_cap_momentum  # One strategy
"""

import sys
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.backtesting.engine import Backtester
from src.strategies import get_strategy, STRATEGY_REGISTRY
from loguru import logger

# Configure logging
logger.remove()
logger.add(lambda msg: print(msg, end=""), format="{time:HH:mm:ss} | {message}\n", level="INFO")

# ─── Configuration ────────────────────────────────────────────────────────────

# Cost levels to sweep (total round-trip cost in bps)
COST_LEVELS_BPS = [0, 2, 5, 10, 15, 20, 30, 50, 75, 100]

# Reference cost level (our standard backtest assumption)
REFERENCE_COST_BPS = 15  # 10 commission + 5 slippage

# Institutional realistic range
INSTITUTIONAL_LOW_BPS = 5    # Large-cap electronic execution
INSTITUTIONAL_HIGH_BPS = 30  # Mid-cap with market impact

RISK_FREE_RATE = 0.02

RESULTS_DIR = PROJECT_ROOT / 'results' / 'transaction_costs'


def safe_float(v):
    """Convert to JSON-safe float."""
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return round(float(v), 6)


def annualized_sharpe(returns, risk_free_rate=0.02):
    """Calculate annualized Sharpe from daily returns."""
    if len(returns) < 10:
        return 0.0
    excess = returns - risk_free_rate / 252
    std = excess.std()
    if std == 0:
        return 0.0
    return float(np.sqrt(252) * excess.mean() / std)


def annualized_return(returns):
    """Calculate annualized total return from daily returns."""
    if len(returns) < 10:
        return 0.0
    total = (1 + returns).prod()
    n_years = len(returns) / 252
    if n_years <= 0 or total <= 0:
        return 0.0
    return float(total ** (1 / n_years) - 1)


def annual_turnover(turnover_series):
    """Calculate annualized turnover from daily turnover."""
    if turnover_series is None or len(turnover_series) == 0:
        return 0.0
    n_years = len(turnover_series) / 252
    if n_years <= 0:
        return 0.0
    return float(turnover_series.sum() / n_years)


# ─── Core Analysis ────────────────────────────────────────────────────────────

def run_at_cost_level(strategy_key, data, cost_bps):
    """
    Run a single strategy at a given total cost level.

    Splits total cost evenly between commission and slippage.
    Returns: dict with sharpe, annual_return, turnover, max_drawdown
    """
    strategy = get_strategy(strategy_key, data)

    # Split cost: 2/3 commission, 1/3 slippage (roughly realistic)
    commission = cost_bps * 2 / 3
    slippage = cost_bps * 1 / 3

    bt = Backtester(
        strategy=strategy,
        data=data,
        initial_capital=1_000_000,
        commission_bps=commission,
        slippage_bps=slippage,
    )

    result = bt.run()

    return {
        'sharpe': annualized_sharpe(result.returns, RISK_FREE_RATE),
        'annual_return': annualized_return(result.returns),
        'annual_turnover': annual_turnover(result.turnover),
        'max_drawdown': float(result.metrics.get('max_drawdown', 0)),
        'total_return': float(result.metrics.get('total_return', 0)),
    }


def find_breakeven_cost(cost_results):
    """
    Find the cost level (in bps) where Sharpe crosses zero.
    Uses linear interpolation between the two nearest points.

    Returns: breakeven cost in bps, or None if Sharpe never crosses zero
    """
    # Sort by cost
    costs = sorted(cost_results.keys())
    sharpes = [cost_results[c]['sharpe'] for c in costs]

    # If Sharpe is negative even at 0 cost, breakeven is 0
    if sharpes[0] <= 0:
        return 0.0

    # If Sharpe is positive even at max cost, breakeven > max cost
    if sharpes[-1] > 0:
        return None  # Still profitable at highest cost tested

    # Find crossing point
    for i in range(len(costs) - 1):
        if sharpes[i] > 0 and sharpes[i + 1] <= 0:
            # Linear interpolation
            s1, s2 = sharpes[i], sharpes[i + 1]
            c1, c2 = costs[i], costs[i + 1]
            # s1 + (s2 - s1) * (breakeven - c1) / (c2 - c1) = 0
            breakeven = c1 + s1 * (c2 - c1) / (s1 - s2)
            return round(float(breakeven), 1)

    return None


def compute_cost_sensitivity(cost_results):
    """
    Compute sensitivity metrics from cost sweep results.

    Returns dict with:
    - sharpe_per_10bps: Sharpe drop per 10bps of cost increase
    - breakeven_cost: Cost where Sharpe hits zero
    - sharpe_at_zero: Gross Sharpe (no costs)
    - sharpe_at_reference: Sharpe at standard 15 bps
    - cost_drag_pct: What % of gross return is eaten by costs at reference level
    """
    costs = sorted(cost_results.keys())

    # Sharpe at zero cost vs max cost for slope
    sharpe_0 = cost_results[0]['sharpe']

    # Find reference cost (closest to 15 bps)
    ref_cost = min(costs, key=lambda c: abs(c - REFERENCE_COST_BPS))
    sharpe_ref = cost_results[ref_cost]['sharpe']

    # Sharpe slope: drop per 10 bps
    # Use linear regression across all points for stability
    x = np.array(costs, dtype=float)
    y = np.array([cost_results[c]['sharpe'] for c in costs])

    if len(x) > 1 and np.std(x) > 0:
        slope = np.polyfit(x, y, 1)[0]  # Sharpe per 1 bps
        sharpe_per_10bps = slope * 10
    else:
        sharpe_per_10bps = 0.0

    # Return drag: gross return - net return at reference
    gross_return = cost_results[0]['annual_return']
    net_return = cost_results[ref_cost]['annual_return']
    if gross_return != 0:
        cost_drag_pct = (gross_return - net_return) / abs(gross_return)
    else:
        cost_drag_pct = 0.0

    return {
        'sharpe_at_zero': sharpe_0,
        'sharpe_at_reference': sharpe_ref,
        'sharpe_per_10bps': sharpe_per_10bps,
        'breakeven_cost_bps': find_breakeven_cost(cost_results),
        'cost_drag_pct': cost_drag_pct,
        'annual_turnover': cost_results[ref_cost]['annual_turnover'],
        'return_at_zero': cost_results[0]['annual_return'],
        'return_at_reference': cost_results[ref_cost]['annual_return'],
    }


def classify_cost_resilience(sensitivity):
    """
    Classify strategy's cost resilience into categories.

    Categories:
    - BULLETPROOF: Breakeven > 75 bps (can survive expensive execution)
    - RESILIENT: Breakeven 30-75 bps (works with typical institutional costs)
    - SENSITIVE: Breakeven 10-30 bps (only works with low-cost execution)
    - FRAGILE: Breakeven < 10 bps (wiped out by any realistic costs)
    """
    be = sensitivity['breakeven_cost_bps']

    if be is None:  # Still profitable at 100 bps
        return 'BULLETPROOF'
    elif be > 75:
        return 'BULLETPROOF'
    elif be > 30:
        return 'RESILIENT'
    elif be > 10:
        return 'SENSITIVE'
    else:
        return 'FRAGILE'


# ─── Main Analysis ────────────────────────────────────────────────────────────

def analyze_strategy(strategy_key, data):
    """Run full transaction cost sensitivity for one strategy."""
    logger.info(f"  Analyzing {strategy_key}...")

    cost_results = {}
    for cost_bps in COST_LEVELS_BPS:
        try:
            cost_results[cost_bps] = run_at_cost_level(strategy_key, data, cost_bps)
        except Exception as e:
            logger.warning(f"    Failed at {cost_bps} bps: {e}")
            continue

    if len(cost_results) < 2:
        logger.warning(f"    Not enough cost levels succeeded for {strategy_key}")
        return None

    # Compute sensitivity metrics
    sensitivity = compute_cost_sensitivity(cost_results)
    resilience = classify_cost_resilience(sensitivity)

    return {
        'strategy': strategy_key,
        'resilience': resilience,
        'sensitivity': {k: safe_float(v) if isinstance(v, (int, float)) else v
                       for k, v in sensitivity.items()},
        'cost_curve': {
            str(cost): {k: safe_float(v) for k, v in metrics.items()}
            for cost, metrics in cost_results.items()
        },
    }


def main():
    """Run transaction cost sensitivity for all (or specified) strategies."""

    # Parse command line
    if len(sys.argv) > 1:
        strategy_keys = [sys.argv[1]]
        if strategy_keys[0] not in STRATEGY_REGISTRY:
            print(f"Unknown strategy: {strategy_keys[0]}")
            print(f"Available: {list(STRATEGY_REGISTRY.keys())}")
            sys.exit(1)
    else:
        strategy_keys = list(STRATEGY_REGISTRY.keys())

    # Load data
    data_path = PROJECT_ROOT / 'data_processed' / 'prices_clean.parquet'
    logger.info(f"Loading data from {data_path}")
    data = pd.read_parquet(data_path)
    logger.info(f"Loaded {len(data):,} rows, {data['symbol'].nunique()} symbols")

    # Create results directory
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Run analysis
    all_results = []
    t0 = time.time()

    logger.info(f"\n{'='*70}")
    logger.info(f"TRANSACTION COST SENSITIVITY ANALYSIS")
    logger.info(f"Cost levels: {COST_LEVELS_BPS} bps")
    logger.info(f"Reference cost: {REFERENCE_COST_BPS} bps (10 commission + 5 slippage)")
    logger.info(f"{'='*70}\n")

    for key in strategy_keys:
        result = analyze_strategy(key, data)
        if result:
            all_results.append(result)

            # Save per-strategy result
            out_path = RESULTS_DIR / f"{key}.json"
            with open(out_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)

    elapsed = time.time() - t0

    # ── Print Summary ─────────────────────────────────────────────────────────

    logger.info(f"\n{'='*70}")
    logger.info(f"RESULTS SUMMARY  ({elapsed:.1f}s)")
    logger.info(f"{'='*70}\n")

    # Summary table
    header = f"{'Strategy':<30} {'Resilience':<13} {'Gross SR':>8} {'Net SR':>8} {'BE Cost':>8} {'Turnover':>10} {'Drag':>8}"
    logger.info(header)
    logger.info("-" * len(header))

    # Sort by breakeven cost (None = bulletproof, highest first)
    def sort_key(r):
        be = r['sensitivity']['breakeven_cost_bps']
        return be if be is not None else 999

    all_results.sort(key=sort_key, reverse=True)

    for r in all_results:
        s = r['sensitivity']
        be = s['breakeven_cost_bps']
        be_str = f"{be:.0f} bps" if be is not None else ">100 bps"
        turnover = s['annual_turnover'] if s['annual_turnover'] is not None else 0
        drag = s['cost_drag_pct'] if s['cost_drag_pct'] is not None else 0
        gross_sr = s['sharpe_at_zero'] if s['sharpe_at_zero'] is not None else 0
        net_sr = s['sharpe_at_reference'] if s['sharpe_at_reference'] is not None else 0

        logger.info(
            f"{r['strategy']:<30} {r['resilience']:<13} "
            f"{gross_sr:>8.2f} {net_sr:>8.2f} "
            f"{be_str:>8} {turnover:>9.1f}x {drag:>7.1%}"
        )

    # ── Category breakdown ────────────────────────────────────────────────────

    categories = {}
    for r in all_results:
        cat = r['resilience']
        categories.setdefault(cat, []).append(r['strategy'])

    logger.info(f"\n{'─'*50}")
    logger.info("COST RESILIENCE CATEGORIES:")
    for cat in ['BULLETPROOF', 'RESILIENT', 'SENSITIVE', 'FRAGILE']:
        if cat in categories:
            logger.info(f"  {cat}: {', '.join(categories[cat])}")

    # ── Turnover analysis ─────────────────────────────────────────────────────

    logger.info(f"\n{'─'*50}")
    logger.info("TURNOVER vs COST SENSITIVITY:")
    logger.info(f"{'Strategy':<30} {'Turnover':>10} {'SR/10bps':>10} {'Correlation':>12}")
    logger.info("-" * 62)

    turnovers = []
    slopes = []
    for r in all_results:
        s = r['sensitivity']
        t = s['annual_turnover'] if s['annual_turnover'] else 0
        sl = s['sharpe_per_10bps'] if s['sharpe_per_10bps'] else 0
        turnovers.append(t)
        slopes.append(sl)
        logger.info(f"{r['strategy']:<30} {t:>9.1f}x {sl:>+10.3f}")

    if len(turnovers) > 2:
        corr = np.corrcoef(turnovers, slopes)[0, 1]
        logger.info(f"\nTurnover ↔ Cost Sensitivity correlation: {corr:.3f}")
        logger.info("(Negative = higher turnover → more Sharpe loss per cost increase)")

    # ── Key insights ──────────────────────────────────────────────────────────

    logger.info(f"\n{'─'*50}")
    logger.info("KEY INSIGHTS:")

    bulletproof = categories.get('BULLETPROOF', [])
    fragile = categories.get('FRAGILE', [])

    if bulletproof:
        logger.info(f"  ✓ {len(bulletproof)} strategies survive even 100 bps costs")
    if fragile:
        logger.info(f"  ✗ {len(fragile)} strategies are wiped out by realistic costs")

    # Find highest and lowest turnover
    if all_results:
        by_turnover = sorted(all_results,
                           key=lambda r: r['sensitivity']['annual_turnover'] or 0,
                           reverse=True)
        highest = by_turnover[0]
        lowest = by_turnover[-1]
        logger.info(f"  Highest turnover: {highest['strategy']} ({highest['sensitivity']['annual_turnover']:.1f}x/yr)")
        logger.info(f"  Lowest turnover: {lowest['strategy']} ({lowest['sensitivity']['annual_turnover']:.1f}x/yr)")

    # ── Save summary ──────────────────────────────────────────────────────────

    summary = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'cost_levels_bps': COST_LEVELS_BPS,
        'reference_cost_bps': REFERENCE_COST_BPS,
        'n_strategies': len(all_results),
        'categories': categories,
        'strategies': {r['strategy']: r for r in all_results},
    }

    summary_path = RESULTS_DIR / 'summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    # CSV summary
    rows = []
    for r in all_results:
        s = r['sensitivity']
        rows.append({
            'strategy': r['strategy'],
            'resilience': r['resilience'],
            'sharpe_gross': s['sharpe_at_zero'],
            'sharpe_net_15bps': s['sharpe_at_reference'],
            'sharpe_per_10bps': s['sharpe_per_10bps'],
            'breakeven_cost_bps': s['breakeven_cost_bps'],
            'annual_turnover': s['annual_turnover'],
            'cost_drag_pct': s['cost_drag_pct'],
            'return_gross': s['return_at_zero'],
            'return_net_15bps': s['return_at_reference'],
        })

    csv_path = RESULTS_DIR / 'cost_sensitivity.csv'
    pd.DataFrame(rows).to_csv(csv_path, index=False)

    logger.info(f"\nResults saved to {RESULTS_DIR}/")
    logger.info(f"Done in {elapsed:.1f}s")


if __name__ == '__main__':
    main()
