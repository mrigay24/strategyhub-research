"""
Run All Backtests on Extended Data (2000-2024) and Store to Database

Replaces the 2014-2017 SQLite results with 25-year backtests.
Uses data_processed/extended_prices_clean.parquet.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from loguru import logger

# Patch the data file path BEFORE importing run_all_backtests
# We monkey-patch by re-implementing main() with the extended data file

from src.database.connection import init_db, session_scope
from src.database.models import Strategy, BacktestRun, BacktestMetrics, EquityCurve
from src.strategies import STRATEGY_REGISTRY, get_strategy
from src.backtesting.engine import Backtester
from src.backtesting.metrics import calculate_metrics

logger.remove()
logger.add(lambda msg: print(msg, end=""), format="{time:HH:mm:ss} | {level} | {message}\n", level="INFO")

EXTENDED_DATA = 'data_processed/extended_prices_clean.parquet'


def safe_float(v):
    if v is None:
        return None
    try:
        f = float(v)
        if not (f == f):  # nan check
            return None
        if f == float('inf') or f == float('-inf'):
            return None
        return f
    except Exception:
        return None


def calculate_benchmark(data: pd.DataFrame, initial_capital: float = 100000):
    logger.info("Calculating market benchmark (equal-weighted proxy)...")
    prices = data.pivot(index='date', columns='symbol', values='close')
    returns = prices.pct_change(fill_method=None).fillna(0)
    benchmark_returns = returns.mean(axis=1)
    benchmark_equity = initial_capital * (1 + benchmark_returns).cumprod()
    benchmark_df = pd.DataFrame({'equity': benchmark_equity.values, 'returns': benchmark_returns.values},
                                 index=benchmark_equity.index)
    metrics = calculate_metrics(returns=benchmark_returns, equity_curve=benchmark_equity, risk_free_rate=0.02)
    logger.info(f"Benchmark: CAGR={metrics['cagr']:.2%}, Sharpe={metrics['sharpe_ratio']:.2f}")
    return benchmark_df, metrics


def run_backtest(strategy_name: str, data: pd.DataFrame):
    strategy_class = STRATEGY_REGISTRY[strategy_name]
    params = strategy_class.DEFAULT_PARAMS.copy()
    strategy = get_strategy(strategy_name, data, params)
    backtester = Backtester(strategy=strategy, data=data, initial_capital=100000, commission_bps=10, slippage_bps=5)
    result = backtester.run()
    return result


def save_benchmark(benchmark_df, metrics):
    with session_scope() as session:
        existing = session.query(Strategy).filter(Strategy.name == 'benchmark').first()
        if existing:
            for old_run in session.query(BacktestRun).filter(BacktestRun.strategy_id == existing.id).all():
                session.delete(old_run)
            strategy_id = existing.id
        else:
            s = Strategy(name='benchmark', strategy_type='Equal-Weighted Benchmark',
                         description='Equal-weighted S&P 500 proxy', default_params={}, is_active=True)
            session.add(s)
            session.flush()
            strategy_id = s.id

        run = BacktestRun(
            strategy_id=strategy_id, params={}, symbol='UNIVERSE',
            start_date=benchmark_df.index[0].to_pydatetime(),
            end_date=benchmark_df.index[-1].to_pydatetime(),
            initial_capital=100000,
            final_capital=float(benchmark_df['equity'].iloc[-1]),
            commission_bps=0, slippage_bps=0, status='completed'
        )
        session.add(run)
        session.flush()

        bm = BacktestMetrics(
            backtest_run_id=run.id,
            total_return=safe_float(metrics.get('total_return')),
            cagr=safe_float(metrics.get('cagr')),
            volatility=safe_float(metrics.get('volatility')),
            sharpe_ratio=safe_float(metrics.get('sharpe_ratio')),
            max_drawdown=safe_float(metrics.get('max_drawdown')),
            all_metrics={k: safe_float(v) for k, v in metrics.items()}
        )
        session.add(bm)

        weekly = benchmark_df.resample('W').last()
        for date, row in weekly.iterrows():
            session.add(EquityCurve(
                backtest_run_id=run.id,
                date=date.to_pydatetime(),
                equity=float(row['equity'])
            ))
        logger.info(f"Saved benchmark (strategy_id={strategy_id})")


def save_result(strategy_name: str, result):
    with session_scope() as session:
        existing = session.query(Strategy).filter(Strategy.name == strategy_name).first()
        if existing:
            for old_run in session.query(BacktestRun).filter(
                BacktestRun.strategy_id == existing.id,
                BacktestRun.symbol == 'UNIVERSE'
            ).all():
                session.delete(old_run)
            strategy_id = existing.id
        else:
            cls = STRATEGY_REGISTRY.get(strategy_name)
            s = Strategy(
                name=strategy_name, strategy_type=result.strategy_name,
                description=f'{result.strategy_name} strategy',
                default_params=cls.DEFAULT_PARAMS if cls else {}, is_active=True
            )
            session.add(s)
            session.flush()
            strategy_id = s.id

        run = BacktestRun(
            strategy_id=strategy_id, params=result.params, symbol='UNIVERSE',
            start_date=pd.Timestamp(result.start_date).to_pydatetime() if result.start_date else None,
            end_date=pd.Timestamp(result.end_date).to_pydatetime() if result.end_date else None,
            initial_capital=result.initial_capital,
            final_capital=float(result.equity_curve.iloc[-1]) if len(result.equity_curve) > 0 else None,
            commission_bps=result.commission_bps, status='completed'
        )
        session.add(run)
        session.flush()

        metrics_row = BacktestMetrics(
            backtest_run_id=run.id,
            total_return=safe_float(result.metrics.get('total_return')),
            cagr=safe_float(result.metrics.get('cagr')),
            volatility=safe_float(result.metrics.get('volatility')),
            sharpe_ratio=safe_float(result.metrics.get('sharpe_ratio')),
            sortino_ratio=safe_float(result.metrics.get('sortino_ratio')),
            max_drawdown=safe_float(result.metrics.get('max_drawdown')),
            calmar_ratio=safe_float(result.metrics.get('calmar_ratio')),
            win_rate=safe_float(result.metrics.get('win_rate')),
            profit_factor=safe_float(result.metrics.get('profit_factor')),
            all_metrics={k: safe_float(v) for k, v in result.metrics.items()}
        )
        session.add(metrics_row)

        if len(result.equity_curve) > 0:
            equity_df = result.equity_curve.to_frame('equity')
            weekly = equity_df.resample('W').last()
            running_max = weekly['equity'].expanding().max()
            weekly['drawdown'] = weekly['equity'] / running_max - 1
            for date, row in weekly.iterrows():
                session.add(EquityCurve(
                    backtest_run_id=run.id,
                    date=date.to_pydatetime(),
                    equity=float(row['equity']),
                    drawdown=float(row['drawdown'])
                ))

        logger.info(f"Saved {strategy_name} (run_id={run.id})")


def main():
    print("=" * 70)
    print("RUNNING ALL 14 BACKTESTS ON EXTENDED DATA (2000-2024)")
    print("=" * 70)

    init_db()

    logger.info(f"Loading extended data from {EXTENDED_DATA}...")
    data = pd.read_parquet(EXTENDED_DATA)
    logger.info(f"Loaded {len(data):,} rows, {data['symbol'].nunique()} symbols, "
                f"{data['date'].min().date()} to {data['date'].max().date()}")

    benchmark_df, benchmark_metrics = calculate_benchmark(data)
    save_benchmark(benchmark_df, benchmark_metrics)

    results = []
    all_strategies = list(STRATEGY_REGISTRY.keys())

    for name in all_strategies:
        logger.info(f"\nRunning {name}...")
        try:
            result = run_backtest(name, data)
            if result:
                save_result(name, result)
                results.append({
                    'strategy': name,
                    'display': result.strategy_name,
                    'total_return': result.metrics.get('total_return', 0),
                    'cagr': result.metrics.get('cagr', 0),
                    'sharpe': result.metrics.get('sharpe_ratio', 0),
                    'max_dd': result.metrics.get('max_drawdown', 0),
                })
        except Exception as e:
            logger.error(f"Error running {name}: {e}")
            import traceback; traceback.print_exc()

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{'Strategy':<30} {'Return':>10} {'CAGR':>8} {'Sharpe':>8} {'Max DD':>10}")
    print("-" * 70)
    for r in results:
        ret = f"{r['total_return']:.1%}" if r['total_return'] else "N/A"
        cagr = f"{r['cagr']:.1%}" if r['cagr'] else "N/A"
        sharpe = f"{r['sharpe']:.2f}" if r['sharpe'] else "N/A"
        dd = f"{r['max_dd']:.1%}" if r['max_dd'] else "N/A"
        print(f"{r['display'][:28]:<30} {ret:>10} {cagr:>8} {sharpe:>8} {dd:>10}")
    print(f"\nDone! {len(results)}/14 strategies saved.")


if __name__ == '__main__':
    main()
