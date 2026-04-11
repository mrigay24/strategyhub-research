"""
Run All Backtests Script

Runs all 14 strategies on real data and stores results in the database.
Also calculates the market benchmark (equal-weighted S&P 500 proxy).
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from loguru import logger

from src.database.connection import init_db, session_scope
from src.database.models import Strategy, BacktestRun, BacktestMetrics, EquityCurve
from src.strategies import STRATEGY_REGISTRY, get_strategy
from src.backtesting.engine import Backtester
from src.backtesting.metrics import calculate_metrics

# Configure logging
logger.remove()
logger.add(lambda msg: print(msg, end=""), format="{time:HH:mm:ss} | {level} | {message}\n", level="INFO")


def calculate_benchmark(data: pd.DataFrame, initial_capital: float = 100000):
    """Calculate equal-weighted benchmark from all stocks."""
    logger.info("Calculating market benchmark (equal-weighted S&P 500 proxy)...")

    prices = data.pivot(index='date', columns='symbol', values='close')
    returns = prices.pct_change()
    benchmark_returns = returns.mean(axis=1).fillna(0)
    benchmark_equity = initial_capital * (1 + benchmark_returns).cumprod()

    benchmark_df = pd.DataFrame({
        'date': benchmark_equity.index,
        'equity': benchmark_equity.values,
        'returns': benchmark_returns.values
    })
    benchmark_df.set_index('date', inplace=True)

    metrics = calculate_metrics(
        returns=benchmark_returns,
        equity_curve=benchmark_equity,
        risk_free_rate=0.02
    )

    logger.info(f"Benchmark: Total Return={metrics['total_return']:.2%}, "
                f"CAGR={metrics['cagr']:.2%}, Sharpe={metrics['sharpe_ratio']:.2f}")

    return benchmark_df, metrics


def run_multi_asset_backtest(strategy_name: str, data: pd.DataFrame):
    """Run backtest for multi-asset strategy on full universe."""
    strategy_class = STRATEGY_REGISTRY[strategy_name]
    params = strategy_class.DEFAULT_PARAMS.copy()

    strategy = get_strategy(strategy_name, data, params)
    backtester = Backtester(strategy, data, initial_capital=100000)

    return backtester.run()


def safe_float(v):
    """Convert to float, handling NaN/Inf."""
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return float(v)


def save_benchmark_to_db(benchmark_df: pd.DataFrame, metrics: dict):
    """Save benchmark as a special 'strategy' in the database."""
    with session_scope() as session:
        existing = session.query(Strategy).filter(Strategy.name == '_benchmark_').first()
        if existing:
            session.query(BacktestRun).filter(BacktestRun.strategy_id == existing.id).delete()
            session.delete(existing)

        benchmark_strategy = Strategy(
            name='_benchmark_',
            strategy_type='benchmark',
            description='Equal-weighted S&P 500 proxy',
            default_params={},
            is_active=True
        )
        session.add(benchmark_strategy)
        session.flush()

        run = BacktestRun(
            strategy_id=benchmark_strategy.id,
            params={},
            symbol='SP500_PROXY',
            start_date=benchmark_df.index[0].to_pydatetime(),
            end_date=benchmark_df.index[-1].to_pydatetime(),
            initial_capital=100000,
            final_capital=float(benchmark_df['equity'].iloc[-1]),
            commission_bps=0,
            slippage_bps=0,
            status='completed'
        )
        session.add(run)
        session.flush()

        bm = BacktestMetrics(
            backtest_run_id=run.id,
            total_return=safe_float(metrics.get('total_return')),
            cagr=safe_float(metrics.get('cagr')),
            volatility=safe_float(metrics.get('volatility')),
            sharpe_ratio=safe_float(metrics.get('sharpe_ratio')),
            sortino_ratio=safe_float(metrics.get('sortino_ratio')),
            max_drawdown=safe_float(metrics.get('max_drawdown')),
            calmar_ratio=safe_float(metrics.get('calmar_ratio')),
            win_rate=safe_float(metrics.get('win_rate')),
            all_metrics={k: safe_float(v) for k, v in metrics.items()}
        )
        session.add(bm)

        weekly = benchmark_df.resample('W').last()
        for date, row in weekly.iterrows():
            point = EquityCurve(
                backtest_run_id=run.id,
                date=date.to_pydatetime(),
                equity=float(row['equity'])
            )
            session.add(point)

        logger.info(f"Saved benchmark to database (id={benchmark_strategy.id})")


def save_strategy_result(strategy_name: str, result, symbol: str = None):
    """Save strategy backtest result to database."""
    with session_scope() as session:
        existing = session.query(Strategy).filter(Strategy.name == strategy_name).first()

        if existing:
            strategy_id = existing.id
            old_runs = session.query(BacktestRun).filter(
                BacktestRun.strategy_id == strategy_id,
                BacktestRun.symbol == symbol
            ).all()
            for old_run in old_runs:
                session.delete(old_run)
        else:
            strategy_class = STRATEGY_REGISTRY.get(strategy_name)

            new_strategy = Strategy(
                name=strategy_name,
                strategy_type=result.strategy_name,
                description=f'{result.strategy_name} strategy',
                default_params=strategy_class.DEFAULT_PARAMS if strategy_class else {},
                is_active=True
            )
            session.add(new_strategy)
            session.flush()
            strategy_id = new_strategy.id

        run = BacktestRun(
            strategy_id=strategy_id,
            params=result.params,
            symbol=symbol,
            start_date=pd.Timestamp(result.start_date).to_pydatetime() if result.start_date else None,
            end_date=pd.Timestamp(result.end_date).to_pydatetime() if result.end_date else None,
            initial_capital=result.initial_capital,
            final_capital=float(result.equity_curve.iloc[-1]) if len(result.equity_curve) > 0 else None,
            commission_bps=result.commission_bps,
            status='completed'
        )
        session.add(run)
        session.flush()

        metrics = BacktestMetrics(
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
            avg_win=safe_float(result.metrics.get('avg_win')),
            avg_loss=safe_float(result.metrics.get('avg_loss')),
            all_metrics={k: safe_float(v) for k, v in result.metrics.items()}
        )
        session.add(metrics)

        equity_series = result.equity_curve
        if len(equity_series) > 0:
            equity_df = equity_series.to_frame('equity')
            weekly = equity_df.resample('W').last()

            running_max = weekly['equity'].expanding().max()
            weekly['drawdown'] = weekly['equity'] / running_max - 1

            for date, row in weekly.iterrows():
                point = EquityCurve(
                    backtest_run_id=run.id,
                    date=date.to_pydatetime(),
                    equity=float(row['equity']),
                    drawdown=float(row['drawdown'])
                )
                session.add(point)

        logger.info(f"Saved {strategy_name} to database (run_id={run.id})")
        return run.id


def main():
    """Main function to run all backtests."""
    print("=" * 70)
    print("RUNNING ALL 14 STRATEGY BACKTESTS")
    print("=" * 70)
    print()

    # Initialize database
    logger.info("Initializing database...")
    init_db()

    # Load data
    logger.info("Loading price data...")
    data = pd.read_parquet('data_processed/prices_clean.parquet')
    logger.info(f"Loaded {len(data)} rows, {data['symbol'].nunique()} symbols")

    # Calculate and save benchmark
    benchmark_df, benchmark_metrics = calculate_benchmark(data)
    save_benchmark_to_db(benchmark_df, benchmark_metrics)

    print()
    print("-" * 70)
    print("RUNNING STRATEGY BACKTESTS")
    print("-" * 70)

    # All 14 strategies are multi-asset
    all_strategies = list(STRATEGY_REGISTRY.keys())
    results_summary = []

    for strategy_name in all_strategies:
        logger.info(f"\nRunning {strategy_name}...")

        try:
            result = run_multi_asset_backtest(strategy_name, data)
            if result:
                save_strategy_result(strategy_name, result, 'UNIVERSE')
                results_summary.append({
                    'strategy': strategy_name,
                    'display_name': result.strategy_name,
                    'total_return': result.metrics.get('total_return', 0),
                    'cagr': result.metrics.get('cagr', 0),
                    'sharpe': result.metrics.get('sharpe_ratio', 0),
                    'max_dd': result.metrics.get('max_drawdown', 0),
                })
        except Exception as e:
            logger.error(f"Error running {strategy_name}: {e}")
            import traceback
            traceback.print_exc()

    # Print summary
    print()
    print("=" * 70)
    print("BACKTEST RESULTS SUMMARY")
    print("=" * 70)
    print()
    print(f"{'Strategy':<30} {'Return':>10} {'CAGR':>8} {'Sharpe':>8} {'Max DD':>10}")
    print("-" * 70)

    for r in results_summary:
        name = r['display_name'][:28]
        ret = f"{r['total_return']:.1%}" if r['total_return'] else "N/A"
        cagr = f"{r['cagr']:.1%}" if r['cagr'] else "N/A"
        sharpe = f"{r['sharpe']:.2f}" if r['sharpe'] else "N/A"
        dd = f"{r['max_dd']:.1%}" if r['max_dd'] else "N/A"
        print(f"{name:<30} {ret:>10} {cagr:>8} {sharpe:>8} {dd:>10}")

    print()
    print("=" * 70)
    print("BENCHMARK (Equal-Weighted S&P 500 Proxy)")
    print("=" * 70)
    print(f"Total Return: {benchmark_metrics['total_return']:.2%}")
    print(f"CAGR: {benchmark_metrics['cagr']:.2%}")
    print(f"Sharpe Ratio: {benchmark_metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {benchmark_metrics['max_drawdown']:.2%}")
    print()
    print(f"Strategies run: {len(results_summary)}/14")
    print("All results saved to database!")


if __name__ == '__main__':
    main()
