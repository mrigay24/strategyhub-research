"""
Phase 3.8 — Regime Overlay on Extended 25-Year Data (2000-2024)

Applies a bear-market filter on top of all 14 strategy signals and measures
the improvement in MDD and Sharpe, now with 3 real bear markets included.

Mirrors Phase 2.6 (regime_overlay.py) but on the 25-year dataset with PIT masking.

Overlay variants:
  Bear-only:   Go to cash (zero signal) when Bear regime detected
  Aggressive:  Cash in Bear + 50% position in Sideways
  Trend-only:  Cash when 63-day trend is negative (regardless of vol)

Key question answered: With REAL bear markets (2002, 2008, 2020, 2022),
does the regime overlay actually IMPROVE Sharpe (not just reduce MDD)?

Usage:
    .venv/bin/python scripts/extended_regime_overlay.py
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

COMMISSION_BPS  = 10
SLIPPAGE_BPS    = 5
RISK_FREE_RATE  = 0.02
RESULTS_DIR     = PROJECT_ROOT / 'results' / 'extended_regime_overlay'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TREND_WINDOW       = 63
VOL_WINDOW         = 63
BEAR_RETURN_THRESH = -0.05
HIGH_VOL_THRESH    = 0.20
BULL_RETURN_THRESH = 0.05

ALL_STRATEGIES = list(STRATEGY_REGISTRY.keys())


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


def get_signals_pit(strategy_key, data, prices, pit_universe):
    """Return signals DataFrame (not yet shifted) with PIT masking."""
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
    """Compute strategy returns + costs from a (possibly modified) signals df."""
    shifted = signals.shift(1).fillna(0)
    ret = (shifted * all_returns).sum(axis=1)
    costs = shifted.diff().abs().sum(axis=1) / 2 * (COMMISSION_BPS + SLIPPAGE_BPS) / 10000
    return (ret - costs).fillna(0)


def classify_regimes(market_returns):
    df = pd.DataFrame({'market_return': market_returns})
    df['cum_63d'] = (1 + df['market_return']).rolling(TREND_WINDOW).apply(
        lambda x: x.prod() - 1, raw=True
    )
    df['vol_63d'] = df['market_return'].rolling(VOL_WINDOW).std() * np.sqrt(252)
    conditions = [
        df['cum_63d'] < BEAR_RETURN_THRESH,
        (df['cum_63d'] > BULL_RETURN_THRESH) & (df['vol_63d'] < HIGH_VOL_THRESH),
        df['vol_63d'] >= HIGH_VOL_THRESH,
    ]
    df['regime'] = np.select(conditions, ['Bear', 'Bull', 'High-Vol'], default='Sideways')
    df['trend_negative'] = df['cum_63d'] < 0
    return df


def metrics(returns):
    if len(returns) < 20:
        return {'sharpe': None, 'cagr': None, 'max_drawdown': None}
    rf = RISK_FREE_RATE / 252
    ex = returns - rf
    std = ex.std()
    sr = float(np.sqrt(252) * ex.mean() / std) if std > 1e-10 else 0.0
    total = float((1 + returns).prod())
    n_yr = len(returns) / 252
    cagr = float(total ** (1 / n_yr) - 1) if total > 0 and n_yr > 0 else 0.0
    equity = (1 + returns).cumprod()
    mdd = float((equity / equity.cummax() - 1).min())
    return {'sharpe': safe_float(sr), 'cagr': safe_float(cagr), 'max_drawdown': safe_float(mdd)}


def apply_overlay(signals, regime_df, variant):
    """
    Apply regime overlay to signals.
    variant:
      'bear_only'  — zero signals in Bear regime
      'aggressive' — zero in Bear, 50% in Sideways
      'trend_only' — zero when 63d trend is negative
    """
    modified = signals.copy()
    regime_aligned = regime_df.reindex(signals.index)

    if variant == 'bear_only':
        bear_mask = regime_aligned['regime'] == 'Bear'
        modified.loc[bear_mask] = 0.0

    elif variant == 'aggressive':
        bear_mask = regime_aligned['regime'] == 'Bear'
        side_mask = regime_aligned['regime'] == 'Sideways'
        modified.loc[bear_mask] = 0.0
        modified.loc[side_mask] = modified.loc[side_mask] * 0.5

    elif variant == 'trend_only':
        neg_trend = regime_aligned['trend_negative'].fillna(False)
        modified.loc[neg_trend] = 0.0

    return modified


def main():
    print("=" * 70)
    print("PHASE 3.8 — EXTENDED REGIME OVERLAY (2000-2024, 25 YEARS)")
    print("=" * 70)

    data_path = PROJECT_ROOT / 'data_processed' / 'extended_prices_clean.parquet'
    logger.info("Loading extended data...")
    data = pd.read_parquet(data_path)
    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values(['date', 'symbol'])

    prices = data.pivot_table(index='date', columns='symbol', values='close').sort_index()
    pit_universe = load_pit_universe(prices.index)
    all_returns = prices.pct_change(fill_method=None).fillna(0)

    # Regime detection
    market_returns = prices.pct_change(fill_method=None).mean(axis=1)
    regime_df = classify_regimes(market_returns)

    bear_pct = (regime_df['regime'] == 'Bear').mean() * 100
    logger.info(f"Bear days: {bear_pct:.1f}% of total (Phase 2 was ~7%)")

    print("\n" + "─" * 90)
    print("REGIME OVERLAY RESULTS  (Sharpe / MDD — Base vs Bear-only vs Aggressive vs Trend-only)")
    print("─" * 90)
    print(f"\n  {'Strategy':<32}  {'Base SR':>8} {'Bear SR':>8} {'Aggr SR':>8} {'Trend SR':>8}  "
          f"{'Base MDD':>9} {'Bear MDD':>9} {'Bear ΔMD':>9}")
    print("  " + "─" * 96)

    all_results = {}
    summary_rows = []

    for i, key in enumerate(ALL_STRATEGIES):
        logger.info(f"[{i+1:2d}/{len(ALL_STRATEGIES)}] {key}")
        try:
            signals = get_signals_pit(key, data, prices, pit_universe)

            # Base (no overlay)
            base_ret = returns_from_signals(signals, all_returns)
            base_m = metrics(base_ret)

            # Overlays
            overlay_results = {}
            for variant in ('bear_only', 'aggressive', 'trend_only'):
                mod_sig = apply_overlay(signals, regime_df, variant)
                mod_ret = returns_from_signals(mod_sig, all_returns)
                overlay_results[variant] = metrics(mod_ret)

            # How many days in cash?
            bear_cash_days = (regime_df['regime'] == 'Bear').reindex(signals.index).sum()
            total_days = len(signals)
            cash_pct_bear = bear_cash_days / total_days * 100

            all_results[key] = {
                'base': base_m,
                'overlays': overlay_results,
                'bear_cash_pct': safe_float(cash_pct_bear),
            }

            # Print row
            base_sr = base_m['sharpe'] or 0
            bear_sr = overlay_results['bear_only']['sharpe'] or 0
            aggr_sr = overlay_results['aggressive']['sharpe'] or 0
            trend_sr = overlay_results['trend_only']['sharpe'] or 0
            base_mdd = base_m['max_drawdown'] or 0
            bear_mdd = overlay_results['bear_only']['max_drawdown'] or 0
            delta_mdd = (bear_mdd - base_mdd) * 100  # positive = improvement (less negative)

            summary_rows.append({
                'strategy': key,
                'base_sharpe': base_sr,
                'bear_sharpe': bear_sr,
                'aggressive_sharpe': aggr_sr,
                'trend_sharpe': trend_sr,
                'base_mdd': base_mdd,
                'bear_mdd': bear_mdd,
                'delta_mdd_pp': delta_mdd,
            })

            print(f"  {key:<32}  {base_sr:>+8.2f} {bear_sr:>+8.2f} {aggr_sr:>+8.2f} {trend_sr:>+8.2f}  "
                  f"{base_mdd*100:>8.1f}% {bear_mdd*100:>8.1f}% {delta_mdd:>+8.1f}pp")

        except Exception as e:
            logger.warning(f"  FAILED: {e}")

    # Summary stats
    if summary_rows:
        df = pd.DataFrame(summary_rows)
        print("\n" + "─" * 70)
        print("SUMMARY — Bear-Only Overlay Impact")
        print("─" * 70)
        bear_improves_sr = (df['bear_sharpe'] > df['base_sharpe']).sum()
        avg_delta_mdd = df['delta_mdd_pp'].mean()
        avg_delta_sr  = (df['bear_sharpe'] - df['base_sharpe']).mean()
        print(f"\n  Strategies where Bear-only IMPROVES Sharpe: {bear_improves_sr}/{len(df)}")
        print(f"  Avg Sharpe change (Bear-only):  {avg_delta_sr:+.2f}")
        print(f"  Avg MDD improvement (Bear-only): {avg_delta_mdd:+.1f}pp")
        print(f"  (Positive MDD change = less negative = better protection)")
        print(f"\n  Note: In Phase 2 (bull-heavy data), Bear-only HURT Sharpe by ~0.04-0.16.")
        print(f"  In Phase 3 (with 3 real bear markets), the overlay should HELP Sharpe.")
        best_mdd_improvement = df.nlargest(3, 'delta_mdd_pp')[['strategy', 'base_mdd', 'bear_mdd', 'delta_mdd_pp']]
        print(f"\n  Top 3 MDD improvements (Bear-only):")
        for _, row in best_mdd_improvement.iterrows():
            print(f"    {row['strategy']:<35} base MDD {row['base_mdd']*100:.1f}% → "
                  f"bear MDD {row['bear_mdd']*100:.1f}%  ({row['delta_mdd_pp']:+.1f}pp)")

    # Save
    out_path = RESULTS_DIR / 'extended_overlay_results.json'
    with open(out_path, 'w') as f:
        json.dump({'strategies': all_results}, f, indent=2, default=str)

    pd.DataFrame(summary_rows).to_csv(RESULTS_DIR / 'extended_overlay_summary.csv', index=False)

    print(f"\n  Results saved to: {RESULTS_DIR}")
    print("\n" + "=" * 70)
    print("PHASE 3.8 COMPLETE")
    print("=" * 70)
    print("  NEXT: Update PROGRESS_REPORT.md + KNOWLEDGE_BASE.md with Phase 3.6-3.8")


if __name__ == '__main__':
    main()
