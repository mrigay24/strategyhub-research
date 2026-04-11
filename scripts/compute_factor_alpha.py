"""
Factor Alpha Decomposition (Phase 4.5)

Computes CAPM alpha and beta for each strategy, and the theoretical
dollar-neutral long-short (strategy long, benchmark short) equity curve.

Results saved to: results/factor_alpha/factor_alpha.json
"""

import sys
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUTPUT_DIR = ROOT / "results" / "factor_alpha"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RF_ANNUAL = 0.02          # 2% annual risk-free rate (approximate T-bill average)
WEEKS_PER_YEAR = 52       # Equity curves are weekly

STRATEGY_NAMES = [
    "large_cap_momentum", "52_week_high_breakout", "deep_value_all_cap",
    "high_quality_roic", "low_volatility_shield", "dividend_aristocrats",
    "moving_average_trend", "rsi_mean_reversion", "value_momentum_blend",
    "quality_momentum", "quality_low_vol", "composite_factor_score",
    "volatility_targeting", "earnings_surprise_momentum",
]


def safe(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    return round(float(v), 4)


def annualized_return(returns: pd.Series, periods_per_year: int) -> float:
    """Geometric annualized return from a series of periodic returns."""
    return (1 + returns).prod() ** (periods_per_year / len(returns)) - 1


def annualized_vol(returns: pd.Series, periods_per_year: int) -> float:
    return returns.std() * np.sqrt(periods_per_year)


def sharpe(returns: pd.Series, periods_per_year: int, rf_annual: float = 0.02) -> float:
    rf_periodic = rf_annual / periods_per_year
    excess = returns - rf_periodic
    vol = annualized_vol(returns, periods_per_year)
    if vol == 0:
        return 0.0
    return (annualized_return(returns, periods_per_year) - rf_annual) / vol


def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = (equity - peak) / peak
    return float(dd.min())


def capm(strat_rets: pd.Series, bench_rets: pd.Series, rf_annual: float, periods: int):
    """
    OLS regression: r_strat - rf = alpha + beta * (r_bench - rf) + eps

    Returns (alpha_annual, beta, r_squared)
    """
    rf_p = rf_annual / periods
    y = strat_rets - rf_p
    x = bench_rets - rf_p

    # Align on common dates
    common = y.index.intersection(x.index)
    y = y.loc[common]
    x = x.loc[common]

    # OLS
    cov = np.cov(x, y)
    if cov[0, 0] == 0:
        return None, None, None
    beta = cov[0, 1] / cov[0, 0]
    alpha_periodic = y.mean() - beta * x.mean()
    alpha_annual = alpha_periodic * periods   # simple annualisation for small alpha

    # R²
    y_pred = alpha_periodic + beta * x
    ss_res = ((y - y_pred) ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else None

    return alpha_annual, beta, r2


def longshort_equity(strat_equity: pd.Series, bench_equity: pd.Series) -> pd.Series:
    """
    Dollar-neutral L/S equity curve:
        Long $1 in strategy, Short $1 of benchmark (equal-weight market proxy).
        L/S return_t = strategy_return_t - benchmark_return_t
    Starts at $1 (indexed).
    """
    strat_ret = strat_equity.pct_change().dropna()
    bench_ret = bench_equity.pct_change().dropna()
    common = strat_ret.index.intersection(bench_ret.index)
    ls_ret = strat_ret.loc[common] - bench_ret.loc[common]
    # Equity curve starting at $1
    equity = (1 + ls_ret).cumprod()
    return equity, ls_ret


def main():
    conn = sqlite3.connect(ROOT / "data" / "strategyhub.db")

    # Load all equity curves from latest runs
    df = pd.read_sql("""
        SELECT s.name AS strategy, ec.date, ec.equity
        FROM backtest_runs br
        JOIN strategies s ON br.strategy_id = s.id
        JOIN equity_curves ec ON ec.backtest_run_id = br.id
        WHERE br.id IN (
            SELECT MAX(br2.id) FROM backtest_runs br2
            JOIN strategies s2 ON br2.strategy_id = s2.id
            GROUP BY s2.name
        )
        ORDER BY s.name, ec.date
    """, conn)
    conn.close()

    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

    # Pivot: rows = dates, cols = strategies
    wide = df.pivot_table(index="date", columns="strategy", values="equity")
    logger.info(f"Loaded equity data: {wide.shape[0]} dates × {wide.shape[1]} strategies")

    if "benchmark" not in wide.columns:
        logger.error("No 'benchmark' column found in equity data.")
        return

    bench_equity = wide["benchmark"].dropna()

    results = {}

    for name in STRATEGY_NAMES:
        if name not in wide.columns:
            logger.warning(f"  {name}: not in DB, skipping")
            continue

        strat_equity = wide[name].dropna()
        strat_ret = strat_equity.pct_change().dropna()
        bench_ret = bench_equity.pct_change().dropna()

        common = strat_ret.index.intersection(bench_ret.index)
        if len(common) < 50:
            logger.warning(f"  {name}: too few common dates ({len(common)})")
            continue

        sr = strat_ret.loc[common]
        br = bench_ret.loc[common]

        # CAPM decomposition
        alpha_ann, beta, r2 = capm(sr, br, RF_ANNUAL, WEEKS_PER_YEAR)

        # Long-short (dollar-neutral) portfolio
        bench_ec_aligned = bench_equity.reindex(strat_equity.index, method="ffill").dropna()
        strat_ec_aligned = strat_equity.reindex(bench_ec_aligned.index).dropna()
        ls_equity, ls_ret = longshort_equity(strat_ec_aligned, bench_ec_aligned)

        ls_cagr = annualized_return(ls_ret, WEEKS_PER_YEAR)
        ls_vol = annualized_vol(ls_ret, WEEKS_PER_YEAR)
        ls_sharpe = sharpe(ls_ret, WEEKS_PER_YEAR, RF_ANNUAL)
        ls_mdd = max_drawdown(ls_equity)

        # Correlation of L/S with benchmark (should be near zero)
        ls_bench_corr = ls_ret.corr(br.reindex(ls_ret.index).fillna(0))

        # Strategy long-only stats for comparison
        strat_cagr = annualized_return(sr, WEEKS_PER_YEAR)
        strat_sharpe = sharpe(sr, WEEKS_PER_YEAR, RF_ANNUAL)

        # L/S equity curve (sampled ~monthly for API)
        ls_eq_monthly = ls_equity.resample("M").last()
        ls_eq_series = [
            {"date": str(d.date()), "value": round(float(v), 4)}
            for d, v in ls_eq_monthly.items()
            if pd.notna(v)
        ]

        results[name] = {
            "capm": {
                "alpha_annual": safe(alpha_ann),
                "beta": safe(beta),
                "r_squared": safe(r2),
            },
            "longshort": {
                "cagr": safe(ls_cagr),
                "volatility": safe(ls_vol),
                "sharpe_ratio": safe(ls_sharpe),
                "max_drawdown": safe(ls_mdd),
                "market_correlation": safe(ls_bench_corr),
                "equity_curve": ls_eq_series,
            },
            "longonly": {
                "cagr": safe(strat_cagr),
                "sharpe_ratio": safe(strat_sharpe),
            },
        }

        logger.info(
            f"  {name}: β={beta:.2f}, α={alpha_ann*100:.2f}%/yr | "
            f"L/S Sharpe={ls_sharpe:.2f}, corr={ls_bench_corr:.3f}"
        )

    # Benchmark stats for reference
    bench_ret_all = bench_equity.pct_change().dropna()
    results["_benchmark"] = {
        "cagr": safe(annualized_return(bench_ret_all, WEEKS_PER_YEAR)),
        "sharpe_ratio": safe(sharpe(bench_ret_all, WEEKS_PER_YEAR, RF_ANNUAL)),
    }

    output_path = OUTPUT_DIR / "factor_alpha.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"\nSaved to {output_path}")

    # Print summary table
    print(f"\n{'Strategy':<32} {'Beta':>6} {'Alpha%':>8} {'L/S SR':>8} {'L/S Corr':>10}")
    print("-" * 66)
    for name in STRATEGY_NAMES:
        r = results.get(name, {})
        c = r.get("capm", {})
        ls = r.get("longshort", {})
        beta = c.get("beta") or 0
        alpha = (c.get("alpha_annual") or 0) * 100
        ls_sr = ls.get("sharpe_ratio") or 0
        ls_corr = ls.get("market_correlation") or 0
        print(f"  {name:<30} {beta:>6.2f} {alpha:>7.1f}% {ls_sr:>8.2f} {ls_corr:>10.3f}")


if __name__ == "__main__":
    logger.remove()
    logger.add(lambda m: print(m, end=""), format="{message}", level="INFO")
    main()
