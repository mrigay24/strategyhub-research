"""
Phase 3.7 — Rolling Performance Analysis on Extended 25-Year Data (2000-2024)

Mirrors Phase 2.8 (rolling_performance.py) but on the 25-year dataset with
PIT universe masking.

Key additions vs Phase 2.8:
  1. PIT-masked strategy returns
  2. Splits the 25-year window into 25 annual sub-periods (instead of 8 × 6mo)
  3. Rolling 252-day (1-year) Sharpe, CAGR, MDD
  4. Decade-level summary: 2000s, 2010s, 2020s
  5. Best/worst rolling year for each strategy

Usage:
    .venv/bin/python scripts/extended_rolling_performance.py
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
RESULTS_DIR    = PROJECT_ROOT / 'results' / 'extended_rolling_performance'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

ALL_STRATEGIES = list(STRATEGY_REGISTRY.keys())

ROLLING_WINDOW = 252   # 1-year rolling window

# Annual sub-period calendar: each calendar year as a sub-period
YEARS = list(range(2000, 2025))

# Decade groupings
DECADES = {
    '2000s (dot-com + GFC)': (2000, 2009),
    '2010s (long bull)':     (2010, 2019),
    '2020s (COVID + AI)':    (2020, 2024),
}


def safe_float(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return round(float(v), 4)


def load_pit_universe(prices_index: pd.DatetimeIndex) -> dict:
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


def metrics_for_series(returns: pd.Series) -> dict:
    if len(returns) < 10:
        return {'sharpe': None, 'cagr': None, 'max_drawdown': None, 'n_days': len(returns)}
    rf = RISK_FREE_RATE / 252
    excess = returns - rf
    std = excess.std()
    sharpe = float(np.sqrt(252) * excess.mean() / std) if std > 1e-10 else 0.0
    total = float((1 + returns).prod())
    n_years = len(returns) / 252
    cagr = float(total ** (1 / n_years) - 1) if total > 0 and n_years > 0 else 0.0
    equity = (1 + returns).cumprod()
    mdd = float((equity / equity.cummax() - 1).min())
    return {
        'sharpe': safe_float(sharpe),
        'cagr': safe_float(cagr),
        'max_drawdown': safe_float(mdd),
        'n_days': len(returns),
    }


def main():
    print("=" * 70)
    print("PHASE 3.7 — EXTENDED ROLLING PERFORMANCE (2000-2024, 25 YEARS)")
    print("=" * 70)

    data_path = PROJECT_ROOT / 'data_processed' / 'extended_prices_clean.parquet'
    logger.info("Loading extended data...")
    data = pd.read_parquet(data_path)
    data['date'] = pd.to_datetime(data['date'])
    data = data.sort_values(['date', 'symbol'])

    prices = data.pivot_table(index='date', columns='symbol', values='close').sort_index()
    pit_universe = load_pit_universe(prices.index)
    benchmark = prices.pct_change(fill_method=None).mean(axis=1).fillna(0).rename('benchmark')

    # ── Collect strategy returns ──────────────────────────────────────────
    logger.info(f"Running {len(ALL_STRATEGIES)} strategies...")
    all_returns = {'benchmark': benchmark}
    for i, key in enumerate(ALL_STRATEGIES):
        logger.info(f"[{i+1:2d}/{len(ALL_STRATEGIES)}] {key}")
        try:
            all_returns[key] = get_strategy_returns_pit(key, data, prices, pit_universe)
        except Exception as e:
            logger.warning(f"  FAILED: {e}")

    ret_df = pd.DataFrame(all_returns).sort_index()

    # ── Annual sub-period analysis ────────────────────────────────────────
    print("\n" + "─" * 70)
    print("ANNUAL SUB-PERIOD PERFORMANCE (Sharpe by year)")
    print("─" * 70)

    annual_results = {}
    for year in YEARS:
        start = pd.Timestamp(f'{year}-01-01')
        end   = pd.Timestamp(f'{year}-12-31')
        mask  = (ret_df.index >= start) & (ret_df.index <= end)
        if mask.sum() < 20:
            continue
        annual_results[year] = {}
        for col in ret_df.columns:
            annual_results[year][col] = metrics_for_series(ret_df.loc[mask, col])

    # Print summary table (Sharpe, top strategies + benchmark)
    show_strategies = ['benchmark', 'low_volatility_shield', 'rsi_mean_reversion',
                       'quality_momentum', 'large_cap_momentum', 'earnings_surprise_momentum']
    show_strategies = [s for s in show_strategies if s in ret_df.columns]

    print(f"\n  {'Year':<6} " + " ".join(f"{s[:11]:>12}" for s in show_strategies))
    print("  " + "─" * (8 + 13 * len(show_strategies)))

    for year in sorted(annual_results.keys()):
        row_str = f"  {year:<6}"
        for s in show_strategies:
            m = annual_results[year].get(s, {})
            sr = m.get('sharpe')
            row_str += f"  {(sr if sr is not None else 0):>+10.2f}"
        print(row_str)

    # ── Decade analysis ───────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("DECADE ANALYSIS — Sharpe, CAGR, MDD")
    print("─" * 70)

    decade_results = {}
    for decade_name, (start_yr, end_yr) in DECADES.items():
        start = pd.Timestamp(f'{start_yr}-01-01')
        end   = pd.Timestamp(f'{end_yr}-12-31')
        mask  = (ret_df.index >= start) & (ret_df.index <= end)
        decade_results[decade_name] = {}
        for col in ret_df.columns:
            decade_results[decade_name][col] = metrics_for_series(ret_df.loc[mask, col])

    for decade_name, results in decade_results.items():
        print(f"\n  {decade_name}:")
        print(f"  {'Strategy':<32} {'Sharpe':>8} {'CAGR':>8} {'MDD':>9}")
        print("  " + "─" * 60)
        # Sort by Sharpe
        sorted_strats = sorted(results.items(),
                               key=lambda x: (x[1].get('sharpe') or -99), reverse=True)
        for strat, m in sorted_strats:
            sr = m.get('sharpe') or 0
            cg = m.get('cagr') or 0
            md = m.get('max_drawdown') or 0
            marker = " ←── BENCHMARK" if strat == 'benchmark' else ""
            print(f"  {strat:<32} {sr:>+8.2f} {cg*100:>7.1f}% {md*100:>8.1f}%{marker}")

    # ── Rolling 252-day Sharpe ────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("ROLLING 252-DAY SHARPE — Best and Worst Trailing Year Per Strategy")
    print("─" * 70)

    rolling_sharpes = {}
    rf_daily = RISK_FREE_RATE / 252
    for col in ret_df.columns:
        series = ret_df[col]
        excess = series - rf_daily
        roll_mean = excess.rolling(ROLLING_WINDOW).mean()
        roll_std  = excess.rolling(ROLLING_WINDOW).std()
        roll_sr   = np.sqrt(252) * roll_mean / roll_std.replace(0, np.nan)
        rolling_sharpes[col] = roll_sr

    roll_df = pd.DataFrame(rolling_sharpes).dropna(how='all')

    print(f"\n  {'Strategy':<32} {'MeanSR':>8} {'StdSR':>8} {'BestSR':>8} {'WorstSR':>8} {'Best Date':>12} {'Worst Date':>12}")
    print("  " + "─" * 95)

    strategy_roll_summary = {}
    for col in ret_df.columns:
        col_roll = roll_df[col].dropna()
        if len(col_roll) < 100:
            continue
        mean_sr  = float(col_roll.mean())
        std_sr   = float(col_roll.std())
        best_sr  = float(col_roll.max())
        worst_sr = float(col_roll.min())
        best_dt  = col_roll.idxmax().strftime('%Y-%m')
        worst_dt = col_roll.idxmin().strftime('%Y-%m')
        strategy_roll_summary[col] = {
            'mean_sharpe': safe_float(mean_sr),
            'std_sharpe': safe_float(std_sr),
            'best_sharpe': safe_float(best_sr),
            'worst_sharpe': safe_float(worst_sr),
            'best_date': best_dt,
            'worst_date': worst_dt,
        }
        marker = " ←── BENCHMARK" if col == 'benchmark' else ""
        print(f"  {col:<32} {mean_sr:>+8.2f} {std_sr:>8.2f} {best_sr:>+8.2f} {worst_sr:>+8.2f} "
              f"{best_dt:>12} {worst_dt:>12}{marker}")

    # ── Rank stability ────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("ANNUAL RANK STABILITY")
    print("─" * 70)

    # Rank strategies by Sharpe in each year
    annual_sharpes = {}
    for year in sorted(annual_results.keys()):
        annual_sharpes[year] = {}
        for strat in ret_df.columns:
            if strat == 'benchmark':
                continue
            m = annual_results[year].get(strat, {})
            annual_sharpes[year][strat] = m.get('sharpe') or 0

    yearly_rank_df = pd.DataFrame(annual_sharpes).T.rank(ascending=False, axis=1)
    rank_corr_series = []
    years_sorted = sorted(annual_results.keys())
    for i in range(1, len(years_sorted)):
        y1 = years_sorted[i-1]
        y2 = years_sorted[i]
        if y1 in yearly_rank_df.index and y2 in yearly_rank_df.index:
            rc = yearly_rank_df.loc[y1].corr(yearly_rank_df.loc[y2], method='spearman')
            if not np.isnan(rc):
                rank_corr_series.append(rc)

    if rank_corr_series:
        mean_rc = float(np.mean(rank_corr_series))
        stability = "STABLE (≥ 0.6)" if mean_rc >= 0.6 else "UNSTABLE (< 0.6)"
        print(f"\n  Year-over-year rank correlation: {mean_rc:.3f}  [{stability}]")
        print(f"  (Interprets: do the same strategies consistently lead year after year?)")
    else:
        mean_rc = None

    # ── Save results ──────────────────────────────────────────────────────
    output = {
        'data_period': '2000-2024',
        'rolling_window': ROLLING_WINDOW,
        'annual_results': {str(y): {k: v for k, v in d.items()} for y, d in annual_results.items()},
        'decade_results': {k: {s: m for s, m in v.items()} for k, v in decade_results.items()},
        'rolling_summary': strategy_roll_summary,
        'rank_stability': {
            'mean_year_over_year_spearman': safe_float(mean_rc),
            'n_year_pairs': len(rank_corr_series),
        },
    }

    with open(RESULTS_DIR / 'extended_rolling_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)

    # Annual CSV
    annual_rows = []
    for year, strats in annual_results.items():
        for strat, m in strats.items():
            row = {'year': year, 'strategy': strat}
            row.update(m)
            annual_rows.append(row)
    pd.DataFrame(annual_rows).to_csv(RESULTS_DIR / 'annual_performance.csv', index=False)

    print(f"\n  Results saved to: {RESULTS_DIR}")
    print("\n" + "=" * 70)
    print("PHASE 3.7 COMPLETE")
    print("=" * 70)
    print("  NEXT: scripts/extended_regime_overlay.py")


if __name__ == '__main__':
    main()
