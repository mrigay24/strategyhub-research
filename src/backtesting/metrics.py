"""
Performance Metrics Module

Calculates standard performance and risk metrics for backtesting.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class MetricResult:
    """Container for a single metric"""
    name: str
    value: float
    description: str


def calculate_metrics(
    returns: pd.Series,
    equity_curve: pd.Series,
    turnover: Optional[pd.Series] = None,
    risk_free_rate: float = 0.02,
    periods_per_year: int = 252,
) -> Dict[str, float]:
    """
    Calculate comprehensive performance metrics

    Args:
        returns: Strategy returns series
        equity_curve: Cumulative equity curve
        turnover: Portfolio turnover series
        risk_free_rate: Annual risk-free rate
        periods_per_year: Trading periods per year (252 for daily)

    Returns:
        Dictionary of metrics
    """
    # Drop NaN values
    returns = returns.dropna()

    if len(returns) < 2:
        return _empty_metrics()

    metrics = {}

    # Total Return
    metrics['total_return'] = total_return(equity_curve)

    # Annualized Return (CAGR)
    metrics['cagr'] = cagr(equity_curve, periods_per_year)

    # Annualized Volatility
    metrics['volatility'] = annualized_volatility(returns, periods_per_year)

    # Sharpe Ratio
    metrics['sharpe_ratio'] = sharpe_ratio(returns, risk_free_rate, periods_per_year)

    # Sortino Ratio
    metrics['sortino_ratio'] = sortino_ratio(returns, risk_free_rate, periods_per_year)

    # Maximum Drawdown
    metrics['max_drawdown'] = max_drawdown(equity_curve)

    # Calmar Ratio
    metrics['calmar_ratio'] = calmar_ratio(equity_curve, periods_per_year)

    # Win Rate
    metrics['win_rate'] = win_rate(returns)

    # Profit Factor
    metrics['profit_factor'] = profit_factor(returns)

    # Average Win / Average Loss
    metrics['avg_win'] = average_win(returns)
    metrics['avg_loss'] = average_loss(returns)
    metrics['win_loss_ratio'] = win_loss_ratio(returns)

    # Number of trades (approximation from turnover)
    if turnover is not None:
        metrics['avg_turnover'] = turnover.mean()
        metrics['total_turnover'] = turnover.sum()

    # Skewness and Kurtosis
    metrics['skewness'] = returns.skew()
    metrics['kurtosis'] = returns.kurtosis()

    # Worst day/month
    metrics['worst_day'] = returns.min()
    metrics['best_day'] = returns.max()

    # VaR (Value at Risk) at 95%
    metrics['var_95'] = value_at_risk(returns, 0.05)

    # CVaR (Expected Shortfall) at 95%
    metrics['cvar_95'] = conditional_var(returns, 0.05)

    return metrics


def _empty_metrics() -> Dict[str, float]:
    """Return empty metrics dictionary"""
    return {
        'total_return': 0.0,
        'cagr': 0.0,
        'volatility': 0.0,
        'sharpe_ratio': 0.0,
        'sortino_ratio': 0.0,
        'max_drawdown': 0.0,
        'calmar_ratio': 0.0,
        'win_rate': 0.0,
        'profit_factor': 0.0,
        'avg_win': 0.0,
        'avg_loss': 0.0,
        'win_loss_ratio': 0.0,
    }


# =============================================================================
# RETURN METRICS
# =============================================================================

def total_return(equity_curve: pd.Series) -> float:
    """
    Total cumulative return

    Return = (Final Value / Initial Value) - 1
    """
    if len(equity_curve) < 2:
        return 0.0
    return equity_curve.iloc[-1] / equity_curve.iloc[0] - 1


def cagr(equity_curve: pd.Series, periods_per_year: int = 252) -> float:
    """
    Compound Annual Growth Rate

    CAGR = (Final/Initial)^(periods_per_year/n_periods) - 1
    """
    if len(equity_curve) < 2:
        return 0.0

    total_ret = total_return(equity_curve)
    n_periods = len(equity_curve)

    if total_ret <= -1:
        return -1.0

    return (1 + total_ret) ** (periods_per_year / n_periods) - 1


def annualized_return(returns: pd.Series, periods_per_year: int = 252) -> float:
    """
    Annualized return from periodic returns

    Ann_Return = ((1 + mean_return) ^ periods_per_year) - 1
    """
    mean_ret = returns.mean()
    return (1 + mean_ret) ** periods_per_year - 1


# =============================================================================
# RISK METRICS
# =============================================================================

def annualized_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    """
    Annualized volatility (standard deviation of returns)

    Vol = Std(returns) * sqrt(periods_per_year)
    """
    return returns.std() * np.sqrt(periods_per_year)


def downside_deviation(returns: pd.Series, target: float = 0.0,
                       periods_per_year: int = 252) -> float:
    """
    Downside deviation (standard deviation of negative returns)

    Only considers returns below target.
    """
    downside_returns = returns[returns < target]
    if len(downside_returns) == 0:
        return 0.0
    return downside_returns.std() * np.sqrt(periods_per_year)


def max_drawdown(equity_curve: pd.Series) -> float:
    """
    Maximum Drawdown

    Max peak-to-trough decline as a percentage.
    Returns negative value (e.g., -0.20 for 20% drawdown).
    """
    if len(equity_curve) < 2:
        return 0.0

    # Running maximum
    running_max = equity_curve.expanding().max()

    # Drawdown at each point
    drawdown = equity_curve / running_max - 1

    return drawdown.min()


def drawdown_series(equity_curve: pd.Series) -> pd.Series:
    """
    Calculate drawdown series

    Returns series of drawdowns at each point.
    """
    running_max = equity_curve.expanding().max()
    return equity_curve / running_max - 1


def max_drawdown_duration(equity_curve: pd.Series) -> int:
    """
    Maximum drawdown duration in periods

    Number of periods from peak to recovery.
    """
    running_max = equity_curve.expanding().max()
    underwater = equity_curve < running_max

    # Find consecutive underwater periods
    max_duration = 0
    current_duration = 0

    for is_underwater in underwater:
        if is_underwater:
            current_duration += 1
            max_duration = max(max_duration, current_duration)
        else:
            current_duration = 0

    return max_duration


def value_at_risk(returns: pd.Series, confidence: float = 0.05) -> float:
    """
    Value at Risk (VaR)

    The loss that is not exceeded with (1-confidence) probability.
    E.g., VaR at 5% = 5th percentile of returns.
    """
    return returns.quantile(confidence)


def conditional_var(returns: pd.Series, confidence: float = 0.05) -> float:
    """
    Conditional Value at Risk (CVaR / Expected Shortfall)

    Average loss in the worst (confidence)% of cases.
    """
    var = value_at_risk(returns, confidence)
    return returns[returns <= var].mean()


# =============================================================================
# RISK-ADJUSTED RETURN METRICS
# =============================================================================

def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02,
                 periods_per_year: int = 252) -> float:
    """
    Sharpe Ratio

    Sharpe = (Return - Risk_Free) / Volatility

    Measures risk-adjusted return. Higher is better.
    """
    excess_returns = returns - risk_free_rate / periods_per_year
    vol = returns.std()

    if vol == 0 or np.isnan(vol):
        return 0.0

    return excess_returns.mean() / vol * np.sqrt(periods_per_year)


def sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.02,
                  periods_per_year: int = 252) -> float:
    """
    Sortino Ratio

    Like Sharpe but only penalizes downside volatility.
    Better for strategies with asymmetric returns.
    """
    excess_returns = returns - risk_free_rate / periods_per_year
    down_vol = downside_deviation(returns, 0, periods_per_year)

    if down_vol == 0 or np.isnan(down_vol):
        return 0.0

    # Annualized excess return
    ann_excess = excess_returns.mean() * periods_per_year

    return ann_excess / down_vol


def calmar_ratio(equity_curve: pd.Series, periods_per_year: int = 252) -> float:
    """
    Calmar Ratio

    Calmar = CAGR / |Max Drawdown|

    Measures return relative to worst-case drawdown.
    """
    ann_return = cagr(equity_curve, periods_per_year)
    mdd = abs(max_drawdown(equity_curve))

    if mdd == 0:
        return 0.0

    return ann_return / mdd


def information_ratio(returns: pd.Series, benchmark_returns: pd.Series,
                      periods_per_year: int = 252) -> float:
    """
    Information Ratio

    IR = (Strategy Return - Benchmark Return) / Tracking Error

    Measures risk-adjusted outperformance vs benchmark.
    """
    excess_returns = returns - benchmark_returns
    tracking_error = excess_returns.std() * np.sqrt(periods_per_year)

    if tracking_error == 0:
        return 0.0

    return excess_returns.mean() * periods_per_year / tracking_error


# =============================================================================
# TRADE ANALYSIS METRICS
# =============================================================================

def win_rate(returns: pd.Series) -> float:
    """
    Win Rate

    Percentage of positive return periods.
    """
    if len(returns) == 0:
        return 0.0

    # Only count non-zero periods as trades
    trades = returns[returns != 0]
    if len(trades) == 0:
        return 0.0

    return (trades > 0).sum() / len(trades)


def profit_factor(returns: pd.Series) -> float:
    """
    Profit Factor

    Profit Factor = Gross Profit / Gross Loss

    > 1 means profitable, higher is better.
    """
    gains = returns[returns > 0].sum()
    losses = abs(returns[returns < 0].sum())

    if losses == 0:
        return float('inf') if gains > 0 else 0.0

    return gains / losses


def average_win(returns: pd.Series) -> float:
    """Average winning return"""
    wins = returns[returns > 0]
    if len(wins) == 0:
        return 0.0
    return wins.mean()


def average_loss(returns: pd.Series) -> float:
    """Average losing return (negative value)"""
    losses = returns[returns < 0]
    if len(losses) == 0:
        return 0.0
    return losses.mean()


def win_loss_ratio(returns: pd.Series) -> float:
    """
    Win/Loss Ratio

    Average Win / |Average Loss|
    """
    avg_w = average_win(returns)
    avg_l = abs(average_loss(returns))

    if avg_l == 0:
        return float('inf') if avg_w > 0 else 0.0

    return avg_w / avg_l


def expectancy(returns: pd.Series) -> float:
    """
    Expected value per trade

    E = (Win Rate * Avg Win) - (Loss Rate * |Avg Loss|)
    """
    wr = win_rate(returns)
    avg_w = average_win(returns)
    avg_l = abs(average_loss(returns))

    return (wr * avg_w) - ((1 - wr) * avg_l)


# =============================================================================
# BENCHMARK COMPARISON
# =============================================================================

def alpha_beta(returns: pd.Series, benchmark_returns: pd.Series,
               risk_free_rate: float = 0.02,
               periods_per_year: int = 252) -> tuple:
    """
    Calculate Alpha and Beta vs benchmark

    Uses CAPM: R = alpha + beta * Rm + epsilon

    Returns:
        (alpha, beta) tuple
    """
    # Align series
    aligned = pd.concat([returns, benchmark_returns], axis=1).dropna()
    if len(aligned) < 2:
        return 0.0, 0.0

    strategy = aligned.iloc[:, 0]
    benchmark = aligned.iloc[:, 1]

    # Calculate beta
    covariance = strategy.cov(benchmark)
    variance = benchmark.var()
    beta = covariance / variance if variance != 0 else 0

    # Calculate alpha
    strategy_return = strategy.mean() * periods_per_year
    benchmark_return = benchmark.mean() * periods_per_year
    alpha = strategy_return - (risk_free_rate + beta * (benchmark_return - risk_free_rate))

    return alpha, beta


if __name__ == "__main__":
    # Test metrics
    import numpy as np

    np.random.seed(42)

    # Generate sample returns
    returns = pd.Series(np.random.randn(252) * 0.01)  # ~1% daily vol

    # Generate equity curve
    equity = 1000000 * (1 + returns).cumprod()

    # Calculate metrics
    metrics = calculate_metrics(returns, equity)

    print("Sample Metrics:")
    print("-" * 40)
    for name, value in metrics.items():
        if 'return' in name.lower() or 'drawdown' in name.lower():
            print(f"{name}: {value:.2%}")
        elif 'ratio' in name.lower():
            print(f"{name}: {value:.3f}")
        else:
            print(f"{name}: {value:.4f}")
