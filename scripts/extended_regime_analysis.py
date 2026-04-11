"""
Phase 3.6 — Market Regime Analysis on Extended 25-Year Data (2000-2024)

Uses the same regime detection method as Phase 2.4 (63-day trend + vol),
but on 25 years of data with PIT universe masking.

Key additions vs Phase 2.4:
  1. PIT-masked strategy returns (signals restricted to in-universe stocks)
  2. Named crisis period analysis: Dot-com (2000-02), GFC (2008-09),
     COVID (2020), 2022 bear — measure each strategy's performance in each
  3. Direct comparison table: Phase 2 vs Phase 3 regime Sharpes
  4. Regime distribution will now show ~20% Bear (vs 7% in Phase 2)

Usage:
    .venv/bin/python scripts/extended_regime_analysis.py
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
RESULTS_DIR      = PROJECT_ROOT / 'results' / 'extended_regime_analysis'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Regime detection parameters (same as Phase 2.4)
TREND_WINDOW         = 63
VOL_WINDOW           = 63
BULL_RETURN_THRESH   = 0.05
BEAR_RETURN_THRESH   = -0.05
HIGH_VOL_THRESH      = 0.20

ALL_STRATEGIES = list(STRATEGY_REGISTRY.keys())

# Named crisis / bull periods for specific period analysis
NAMED_PERIODS = [
    ('Dot-com crash',           '2000-03-01', '2002-10-09'),
    ('Post-crash recovery',     '2002-10-10', '2007-10-08'),
    ('GFC bear market',         '2007-10-09', '2009-03-09'),
    ('Post-GFC bull',           '2009-03-10', '2020-02-19'),
    ('COVID crash',             '2020-02-20', '2020-03-23'),
    ('COVID recovery & bull',   '2020-03-24', '2021-12-31'),
    ('2022 bear market',        '2022-01-01', '2022-12-31'),
    ('AI-driven recovery',      '2023-01-01', '2024-12-31'),
]


def safe_float(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return round(float(v), 4)


# ── PIT universe loader ────────────────────────────────────────────────────────

def load_pit_universe(prices_index: pd.DatetimeIndex) -> dict:
    lookup_path = PROJECT_ROOT / 'data_processed' / 'sp500_universe_lookup.csv'
    if not lookup_path.exists():
        logger.warning("No PIT lookup — using all symbols")
        return None

    lookup = pd.read_csv(lookup_path)
    lookup['date'] = pd.to_datetime(lookup['date'])
    lookup = lookup.sort_values('date')

    pit_by_date = {}
    for _, row in lookup.iterrows():
        tickers = set(row['tickers'].split(',')) if pd.notna(row['tickers']) else set()
        pit_by_date[row['date']] = tickers

    pit_dates = sorted(pit_by_date.keys())

    daily_universe = {}
    pit_idx = 0
    for dt in prices_index:
        while pit_idx < len(pit_dates) - 1 and pit_dates[pit_idx + 1] <= dt:
            pit_idx += 1
        current_pit_date = pit_dates[pit_idx]
        daily_universe[dt] = pit_by_date[pit_dates[0]] if current_pit_date > dt else pit_by_date[current_pit_date]

    return daily_universe


# ── Strategy returns with PIT masking ─────────────────────────────────────────

def get_strategy_returns_pit(strategy_key: str, data: pd.DataFrame,
                              prices: pd.DataFrame,
                              pit_universe: dict) -> pd.Series:
    strategy = get_strategy(strategy_key, data)
    signals = strategy.generate_signals()
    signals = signals.reindex(prices.index).ffill().fillna(0)

    if pit_universe is not None:
        for dt in signals.index:
            if dt in pit_universe:
                in_universe = pit_universe[dt]
                off_universe = [c for c in signals.columns if c not in in_universe]
                if off_universe:
                    signals.loc[dt, off_universe] = 0.0
        row_sums = signals.sum(axis=1)
        nz = row_sums > 0
        signals.loc[nz] = signals.loc[nz].div(row_sums[nz], axis=0)

    all_returns = prices.pct_change(fill_method=None).fillna(0)
    shifted = signals.shift(1).fillna(0)
    strategy_returns = (shifted * all_returns).sum(axis=1)

    turnover = shifted.diff().abs().sum(axis=1) / 2
    costs = turnover * (COMMISSION_BPS + SLIPPAGE_BPS) / 10000

    return (strategy_returns - costs).fillna(0).rename(strategy_key)


# ── Regime detection ──────────────────────────────────────────────────────────

def compute_market_returns(prices: pd.DataFrame) -> pd.Series:
    """Equal-weighted market return per day."""
    return prices.pct_change(fill_method=None).mean(axis=1)


def classify_regimes(market_returns: pd.Series) -> pd.DataFrame:
    df = pd.DataFrame({'market_return': market_returns})
    df['cum_return_63d'] = (1 + df['market_return']).rolling(TREND_WINDOW).apply(
        lambda x: x.prod() - 1, raw=True
    )
    df['ann_vol_63d'] = df['market_return'].rolling(VOL_WINDOW).std() * np.sqrt(252)

    conditions = [
        df['cum_return_63d'] < BEAR_RETURN_THRESH,
        (df['cum_return_63d'] > BULL_RETURN_THRESH) & (df['ann_vol_63d'] < HIGH_VOL_THRESH),
        df['ann_vol_63d'] >= HIGH_VOL_THRESH,
    ]
    df['regime'] = np.select(conditions, ['Bear', 'Bull', 'High-Vol'], default='Sideways')
    return df.dropna(subset=['cum_return_63d', 'ann_vol_63d'])


# ── Performance metrics ────────────────────────────────────────────────────────

def metrics_for_series(returns: pd.Series) -> dict:
    if len(returns) < 5:
        return {'sharpe': None, 'ann_return': None, 'ann_vol': None, 'max_drawdown': None,
                'win_rate': None, 'n_days': len(returns)}
    rf = RISK_FREE_RATE / 252
    mean_d = returns.mean()
    std_d = returns.std()
    sharpe = float(np.sqrt(252) * (mean_d - rf) / std_d) if std_d > 1e-10 else 0.0
    ann_return = mean_d * 252
    ann_vol = std_d * np.sqrt(252)
    equity = (1 + returns).cumprod()
    mdd = float((equity / equity.cummax() - 1).min())
    win_rate = float((returns > 0).mean())
    return {
        'sharpe': safe_float(sharpe),
        'ann_return': safe_float(ann_return),
        'ann_vol': safe_float(ann_vol),
        'max_drawdown': safe_float(mdd),
        'win_rate': safe_float(win_rate),
        'n_days': int(len(returns)),
    }


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("PHASE 3.6 — EXTENDED REGIME ANALYSIS (2000-2024, 25 YEARS)")
    print("=" * 70)

    # Load data
    data_path = PROJECT_ROOT / 'data_processed' / 'extended_prices_clean.parquet'
    logger.info("Loading extended data...")
    data = pd.read_parquet(data_path)
    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values(['date', 'symbol'])
    logger.info(f"  {len(data):,} rows, {data['symbol'].nunique()} symbols, "
                f"{data['date'].min().date()} → {data['date'].max().date()}")

    prices = data.pivot_table(index='date', columns='symbol', values='close').sort_index()
    pit_universe = load_pit_universe(prices.index)

    # ── Regime detection ──────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("STEP 1: Market Regime Classification")
    print("─" * 70)

    market_returns = compute_market_returns(prices)
    regime_df = classify_regimes(market_returns)

    total_days = len(regime_df)
    print(f"\n  Regime breakdown ({total_days:,} trading days after 63-day warmup):\n")
    print(f"  {'Regime':<12} {'Days':>6} {'% Total':>9} {'Ann Return':>12} {'Ann Vol':>10}")
    print("  " + "─" * 52)

    regime_summary = {}
    for regime in ['Bull', 'Bear', 'High-Vol', 'Sideways']:
        mask = regime_df['regime'] == regime
        n = int(mask.sum())
        pct = n / total_days * 100
        ret = regime_df.loc[mask, 'market_return']
        ann_r = float(ret.mean() * 252) if len(ret) > 0 else 0.0
        ann_v = float(ret.std() * np.sqrt(252)) if len(ret) > 1 else 0.0
        print(f"  {regime:<12} {n:>6}  {pct:>7.1f}%  {ann_r:>11.1%}  {ann_v:>9.1%}")
        regime_summary[regime] = {'n_days': n, 'pct': round(pct, 1),
                                   'ann_market_return': safe_float(ann_r),
                                   'ann_market_vol': safe_float(ann_v)}

    # ── Strategy returns ──────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print(f"STEP 2: Running {len(ALL_STRATEGIES)} Strategies with PIT Masking")
    print("─" * 70)

    all_strategy_returns = {}
    for i, key in enumerate(ALL_STRATEGIES):
        logger.info(f"[{i+1:2d}/{len(ALL_STRATEGIES)}] {key}")
        try:
            ret = get_strategy_returns_pit(key, data, prices, pit_universe)
            all_strategy_returns[key] = ret
        except Exception as e:
            logger.warning(f"  FAILED: {e}")

    # Benchmark
    all_strategy_returns['benchmark'] = market_returns.reindex(regime_df.index).fillna(0)

    # ── Regime performance ────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("STEP 3: Strategy Performance by Regime")
    print("─" * 70)

    print(f"\n  {'Strategy':<32} {'Bull':>8} {'Bear':>8} {'High-V':>8} {'Sidew':>8} {'Spread':>8} {'Best':>10}")
    print("  " + "─" * 86)

    all_results = {}
    for key, ret in all_strategy_returns.items():
        aligned = ret.reindex(regime_df.index).fillna(0)
        regime_perf = {}
        for regime in ['Bull', 'Bear', 'High-Vol', 'Sideways']:
            mask = regime_df['regime'] == regime
            regime_perf[regime] = metrics_for_series(aligned[mask])

        sharpes = {r: (regime_perf[r]['sharpe'] or 0) for r in ['Bull', 'Bear', 'High-Vol', 'Sideways']}
        best = max(sharpes, key=sharpes.get)
        worst = min(sharpes, key=sharpes.get)
        spread = sharpes[best] - sharpes[worst]

        all_results[key] = {
            'regime_performance': regime_perf,
            'edge': {
                'best_regime': best,
                'worst_regime': worst,
                'regime_spread': safe_float(spread),
                'regime_sharpes': {k: safe_float(v) for k, v in sharpes.items()},
            },
            'overall': metrics_for_series(aligned),
        }

        bull_s  = sharpes['Bull']
        bear_s  = sharpes['Bear']
        hvol_s  = sharpes['High-Vol']
        side_s  = sharpes['Sideways']
        display = key[:31]
        print(f"  {display:<32} {bull_s:>+8.2f} {bear_s:>+8.2f} {hvol_s:>+8.2f} {side_s:>+8.2f} {spread:>8.2f} {best:>10}")

    # ── Named period analysis ─────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("STEP 4: Named Crisis / Bull Period Analysis")
    print("─" * 70)

    named_results = {}
    for period_name, start_str, end_str in NAMED_PERIODS:
        start = pd.Timestamp(start_str)
        end   = pd.Timestamp(end_str)
        period_sharpes = {}
        for key, ret in all_strategy_returns.items():
            mask = (ret.index >= start) & (ret.index <= end)
            sub = ret[mask]
            if len(sub) >= 20:
                m = metrics_for_series(sub)
                period_sharpes[key] = m
        named_results[period_name] = {
            'start': start_str, 'end': end_str,
            'n_days': sum((ret.index >= start) & (ret.index <= end)),
            'strategies': period_sharpes,
        }

    # Print named period table (Sharpe only)
    strategy_keys = list(all_strategy_returns.keys())
    header_strats = ['benchmark', 'low_volatility_shield', 'quality_momentum',
                     'rsi_mean_reversion', 'earnings_surprise_momentum', 'large_cap_momentum']
    header_strats = [s for s in header_strats if s in all_strategy_returns]

    print(f"\n  {'Period':<28} {'N':>5} " +
          " ".join(f"{s[:10]:>11}" for s in header_strats))
    print("  " + "─" * (35 + 12 * len(header_strats)))

    for period_name, start_str, end_str in NAMED_PERIODS:
        row = named_results[period_name]
        sharpes_str = ""
        for s in header_strats:
            m = row['strategies'].get(s, {})
            sr = m.get('sharpe')
            sharpes_str += f"  {(sr if sr is not None else 0):>+9.2f}"
        print(f"  {period_name:<28} {row['n_days']:>5}{sharpes_str}")

    # ── Save results ──────────────────────────────────────────────────────
    # Serialize
    output = {
        'data_period': '2000-2024',
        'regime_params': {
            'trend_window': TREND_WINDOW,
            'vol_window': VOL_WINDOW,
            'bull_threshold': BULL_RETURN_THRESH,
            'bear_threshold': BEAR_RETURN_THRESH,
            'high_vol_threshold': HIGH_VOL_THRESH,
        },
        'regime_summary': regime_summary,
        'strategies': all_results,
        'named_periods': named_results,
    }

    out_path = RESULTS_DIR / 'extended_regime_results.json'
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    # CSV summary
    rows = []
    for key in ALL_STRATEGIES + ['benchmark']:
        if key not in all_results:
            continue
        r = all_results[key]
        edge = r['edge']
        row = {'strategy': key}
        for regime in ['Bull', 'Bear', 'High-Vol', 'Sideways']:
            row[f'{regime}_sharpe'] = (r['regime_performance'][regime].get('sharpe') or 0)
            row[f'{regime}_ann_return'] = (r['regime_performance'][regime].get('ann_return') or 0)
        row['regime_spread'] = edge['regime_spread']
        row['best_regime'] = edge['best_regime']
        row['worst_regime'] = edge['worst_regime']
        rows.append(row)
    pd.DataFrame(rows).to_csv(RESULTS_DIR / 'extended_regime_summary.csv', index=False)

    print(f"\n  Results saved to: {RESULTS_DIR}")
    print("\n" + "=" * 70)
    print("PHASE 3.6 COMPLETE")
    print("=" * 70)
    print("  NEXT: scripts/extended_rolling_performance.py")


if __name__ == '__main__':
    main()
