"""
Phase 3.10 — Walk-Forward Validation on Extended 25-Year Data (2000-2024)

With 25 years of data we can run a GENUINELY long out-of-sample test:
  Train: 2000-2012 (13 years) → Test: 2013-2024 (12 years)

This is how institutional research actually validates strategies:
a long enough OOS window to capture multiple market regimes, not just 18 months.

Two tests:
  1. Simple OOS split (50/50 approx): train 2000-2012, test 2013-2024
  2. Rolling walk-forward: 5-year train → 2-year test, rolling by 2 years
     Folds cover the full 25-year history and measure consistency

Key metric: Walk-Forward Efficiency (WFE) = OOS_Sharpe / IS_Sharpe
  WFE > 100% = strategy actually IMPROVES out-of-sample (unusual but possible)
  WFE  50-100% = reasonable degradation (expected)
  WFE  < 50%  = overfitting likely

All strategy returns use PIT universe masking and fill_method=None.

Usage:
    .venv/bin/python scripts/extended_walk_forward.py
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

COMMISSION_BPS   = 10
SLIPPAGE_BPS     = 5
RISK_FREE_RATE   = 0.02
LOOKBACK_BUFFER  = 400   # days before OOS start needed for indicator warmup
RESULTS_DIR      = PROJECT_ROOT / 'results' / 'extended_walk_forward'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

ALL_STRATEGIES = list(STRATEGY_REGISTRY.keys())

# Walk-forward fold definitions: (train_start, train_end, test_start, test_end)
ROLLING_FOLDS = [
    ('2000-01-01', '2005-12-31', '2006-01-01', '2007-12-31'),  # Fold 1: dot-com recovery era
    ('2000-01-01', '2007-12-31', '2008-01-01', '2009-12-31'),  # Fold 2: GFC test
    ('2000-01-01', '2009-12-31', '2010-01-01', '2011-12-31'),  # Fold 3: post-crisis
    ('2000-01-01', '2012-12-31', '2013-01-01', '2014-12-31'),  # Fold 4: early bull
    ('2000-01-01', '2014-12-31', '2015-01-01', '2016-12-31'),  # Fold 5: mid bull
    ('2000-01-01', '2016-12-31', '2017-01-01', '2018-12-31'),  # Fold 6: late bull + 2018 correction
    ('2000-01-01', '2018-12-31', '2019-01-01', '2020-12-31'),  # Fold 7: COVID year
    ('2000-01-01', '2020-12-31', '2021-01-01', '2022-12-31'),  # Fold 8: 2022 bear
    ('2000-01-01', '2022-12-31', '2023-01-01', '2024-12-31'),  # Fold 9: AI recovery
]


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


def compute_signals(strategy_key, data, prices, pit_universe):
    """Compute PIT-masked signals for the full dataset."""
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
    return signals


def returns_from_signals(signals, all_returns):
    shifted = signals.shift(1).fillna(0)
    ret = (shifted * all_returns).sum(axis=1)
    costs = shifted.diff().abs().sum(axis=1) / 2 * (COMMISSION_BPS + SLIPPAGE_BPS) / 10000
    return (ret - costs).fillna(0)


def sharpe_of(returns):
    if len(returns) < 20:
        return None
    rf = RISK_FREE_RATE / 252
    ex = returns - rf
    std = ex.std()
    if std < 1e-10:
        return 0.0
    sr = float(np.sqrt(252) * ex.mean() / std)
    return None if (np.isnan(sr) or np.isinf(sr)) else sr


def metrics_of(returns):
    if len(returns) < 20:
        return {'sharpe': None, 'cagr': None, 'max_drawdown': None}
    sr = sharpe_of(returns)
    total = float((1 + returns).prod())
    n_yr = len(returns) / 252
    cagr = float(total ** (1 / n_yr) - 1) if total > 0 and n_yr > 0 else 0.0
    equity = (1 + returns).cumprod()
    mdd = float((equity / equity.cummax() - 1).min())
    return {'sharpe': safe_float(sr), 'cagr': safe_float(cagr), 'max_drawdown': safe_float(mdd)}


def main():
    print("=" * 70)
    print("PHASE 3.10 — EXTENDED WALK-FORWARD VALIDATION (2000-2024)")
    print("=" * 70)

    data_path = PROJECT_ROOT / 'data_processed' / 'extended_prices_clean.parquet'
    logger.info("Loading extended data...")
    data = pd.read_parquet(data_path)
    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values(['date', 'symbol'])

    prices = data.pivot_table(index='date', columns='symbol', values='close').sort_index()
    pit_universe = load_pit_universe(prices.index)
    all_returns = prices.pct_change(fill_method=None).fillna(0)

    # ── Pre-compute all strategy signals (once) ────────────────────────────
    logger.info(f"Pre-computing signals for {len(ALL_STRATEGIES)} strategies...")
    all_signals = {}
    for i, key in enumerate(ALL_STRATEGIES):
        logger.info(f"[{i+1:2d}/{len(ALL_STRATEGIES)}] {key}")
        try:
            all_signals[key] = compute_signals(key, data, prices, pit_universe)
        except Exception as e:
            logger.warning(f"  FAILED: {e}")

    # Pre-compute full-period returns for each strategy
    full_returns = {}
    for key, sigs in all_signals.items():
        full_returns[key] = returns_from_signals(sigs, all_returns)

    # ── Part 1: Simple 50/50 split: train 2000-2012, test 2013-2024 ───────
    print("\n" + "─" * 70)
    print("PART 1: SIMPLE OOS SPLIT — Train 2000-2012, Test 2013-2024")
    print("─" * 70)

    is_start  = pd.Timestamp('2000-01-01')
    is_end    = pd.Timestamp('2012-12-31')
    oos_start = pd.Timestamp('2013-01-01')
    oos_end   = pd.Timestamp('2024-12-31')

    print(f"\n  {'Strategy':<32} {'IS Sharpe':>10} {'OOS Sharpe':>11} {'WFE':>8} {'Verdict':>10}")
    print("  " + "─" * 75)

    simple_oos_results = {}
    for key, ret in full_returns.items():
        is_ret  = ret[(ret.index >= is_start) & (ret.index <= is_end)]
        oos_ret = ret[(ret.index >= oos_start) & (ret.index <= oos_end)]
        is_sr  = sharpe_of(is_ret) or 0
        oos_sr = sharpe_of(oos_ret) or 0
        wfe = (oos_sr / is_sr * 100) if abs(is_sr) > 0.05 else None
        verdict = 'EXCELLENT' if wfe and wfe > 100 else \
                  'GOOD'      if wfe and wfe >= 70  else \
                  'MODERATE'  if wfe and wfe >= 50  else \
                  'WEAK'      if wfe and wfe >= 0   else 'FAIL'
        simple_oos_results[key] = {
            'is_sharpe': safe_float(is_sr),
            'oos_sharpe': safe_float(oos_sr),
            'wfe': safe_float(wfe),
            'verdict': verdict,
        }
        wfe_str = f"{wfe:.0f}%" if wfe is not None else "N/A"
        print(f"  {key:<32} {is_sr:>+10.2f} {oos_sr:>+11.2f} {wfe_str:>8} {verdict:>10}")

    # ── Part 2: Rolling walk-forward folds ────────────────────────────────
    print("\n" + "─" * 70)
    print("PART 2: ROLLING WALK-FORWARD FOLDS (Expanding Train Window)")
    print("─" * 70)
    print(f"  {len(ROLLING_FOLDS)} folds: expanding train window, 2-year test each\n")

    fold_labels = [f"Test {ts[:4]}-{te[:4]}" for _, _, ts, te in ROLLING_FOLDS]
    header = f"  {'Strategy':<32}" + "".join(f" {lbl:>13}" for lbl in fold_labels) + "   Avg OOS WFE"
    print(header)
    print("  " + "─" * (34 + 14 * len(ROLLING_FOLDS) + 14))

    rolling_results = {}
    for key, ret in full_returns.items():
        fold_wfes = []
        fold_oos_srs = []
        row_str = f"  {key:<32}"

        for train_s, train_e, test_s, test_e in ROLLING_FOLDS:
            ts = pd.Timestamp(train_s)
            te = pd.Timestamp(train_e)
            oos_s = pd.Timestamp(test_s)
            oos_e = pd.Timestamp(test_e)

            is_r  = ret[(ret.index >= ts) & (ret.index <= te)]
            oos_r = ret[(ret.index >= oos_s) & (ret.index <= oos_e)]

            is_sr  = sharpe_of(is_r)  or 0
            oos_sr = sharpe_of(oos_r) or 0
            wfe = (oos_sr / is_sr * 100) if abs(is_sr) > 0.05 else None

            fold_wfes.append(wfe)
            fold_oos_srs.append(oos_sr)
            row_str += f" {oos_sr:>+13.2f}"

        avg_wfe = np.mean([w for w in fold_wfes if w is not None]) if any(w is not None for w in fold_wfes) else None
        avg_oos_sr = np.mean(fold_oos_srs)
        row_str += f"  {(avg_wfe or 0):>7.0f}%"
        print(row_str)

        rolling_results[key] = {
            'fold_oos_sharpes': [safe_float(s) for s in fold_oos_srs],
            'fold_wfes': [safe_float(w) for w in fold_wfes],
            'avg_oos_sharpe': safe_float(avg_oos_sr),
            'avg_wfe': safe_float(avg_wfe),
        }

    # ── Summary ────────────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("SUMMARY — Overall Walk-Forward Verdict")
    print("─" * 70)

    print(f"\n  {'Strategy':<32} {'IS SR':>8} {'OOS SR':>8} {'WFE':>8} {'Folds +':>9} {'Verdict':>10}")
    print("  " + "─" * 80)

    summary_rows = []
    for key in ALL_STRATEGIES:
        if key not in simple_oos_results:
            continue
        s = simple_oos_results[key]
        r = rolling_results.get(key, {})
        is_sr  = s['is_sharpe'] or 0
        oos_sr = s['oos_sharpe'] or 0
        wfe    = s['wfe']
        fold_srs = r.get('fold_oos_sharpes', [])
        n_pos_folds = sum(1 for x in fold_srs if (x or 0) > 0)
        verdict = s['verdict']
        wfe_str = f"{wfe:.0f}%" if wfe else "N/A"
        print(f"  {key:<32} {is_sr:>+8.2f} {oos_sr:>+8.2f} {wfe_str:>8} {n_pos_folds}/{len(fold_srs):>4}    {verdict:>10}")
        summary_rows.append({
            'strategy': key,
            'is_sharpe': s['is_sharpe'],
            'oos_sharpe': s['oos_sharpe'],
            'wfe': wfe,
            'n_positive_folds': n_pos_folds,
            'total_folds': len(fold_srs),
            'verdict': verdict,
        })

    # Save
    output = {
        'data_period': '2000-2024',
        'lookback_buffer': LOOKBACK_BUFFER,
        'is_period': '2000-2012',
        'oos_period': '2013-2024',
        'rolling_folds': [(a, b, c, d) for a, b, c, d in ROLLING_FOLDS],
        'simple_oos_results': simple_oos_results,
        'rolling_results': rolling_results,
    }
    with open(RESULTS_DIR / 'extended_walk_forward_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)

    pd.DataFrame(summary_rows).to_csv(RESULTS_DIR / 'extended_wf_summary.csv', index=False)

    print(f"\n  Results saved to: {RESULTS_DIR}")
    print("\n" + "=" * 70)
    print("PHASE 3.10 COMPLETE")
    print("=" * 70)
    print("  NEXT: Update PROGRESS_REPORT + KNOWLEDGE_BASE, then Phase 3.11 (Monte Carlo)")


if __name__ == '__main__':
    main()
