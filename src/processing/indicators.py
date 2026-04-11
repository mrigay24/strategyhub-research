"""
Technical Indicators Library

Vectorized implementations of common technical indicators using Pandas/NumPy.
All functions are designed to work with both Series and DataFrames.
"""

import pandas as pd
import numpy as np
from typing import Union, Tuple, Optional


# =============================================================================
# MOVING AVERAGES
# =============================================================================

def sma(data: Union[pd.Series, pd.DataFrame], window: int) -> Union[pd.Series, pd.DataFrame]:
    """
    Simple Moving Average

    Args:
        data: Price series or DataFrame
        window: Lookback period

    Returns:
        SMA values
    """
    return data.rolling(window=window, min_periods=window).mean()


def ema(data: Union[pd.Series, pd.DataFrame], span: int) -> Union[pd.Series, pd.DataFrame]:
    """
    Exponential Moving Average

    Args:
        data: Price series or DataFrame
        span: EMA span (decay factor = 2/(span+1))

    Returns:
        EMA values
    """
    return data.ewm(span=span, adjust=False, min_periods=span).mean()


def wma(data: pd.Series, window: int) -> pd.Series:
    """
    Weighted Moving Average

    Args:
        data: Price series
        window: Lookback period

    Returns:
        WMA values
    """
    weights = np.arange(1, window + 1)
    return data.rolling(window=window).apply(
        lambda x: np.dot(x, weights) / weights.sum(), raw=True
    )


# =============================================================================
# MOMENTUM INDICATORS
# =============================================================================

def rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index

    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss

    Args:
        data: Price series (typically close prices)
        period: RSI period (default 14)

    Returns:
        RSI values (0-100)
    """
    # Calculate price changes
    delta = data.diff()

    # Separate gains and losses
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)

    # Calculate average gain/loss using EMA (Wilder's smoothing)
    avg_gain = gains.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi_values = 100 - (100 / (1 + rs))

    return rsi_values


def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Moving Average Convergence Divergence

    Args:
        data: Price series
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period

    Returns:
        Tuple of (MACD line, Signal line, Histogram)
    """
    ema_fast = ema(data, fast)
    ema_slow = ema(data, slow)

    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def rate_of_change(data: pd.Series, period: int) -> pd.Series:
    """
    Rate of Change (ROC)

    ROC = (Price - Price_n) / Price_n * 100

    Args:
        data: Price series
        period: Lookback period

    Returns:
        ROC values (percentage)
    """
    return data.pct_change(periods=period) * 100


# =============================================================================
# VOLATILITY INDICATORS
# =============================================================================

def rolling_std(data: Union[pd.Series, pd.DataFrame], window: int) -> Union[pd.Series, pd.DataFrame]:
    """
    Rolling Standard Deviation

    Args:
        data: Price or returns series
        window: Lookback period

    Returns:
        Rolling standard deviation
    """
    return data.rolling(window=window, min_periods=window).std()


def rolling_volatility(returns: Union[pd.Series, pd.DataFrame], window: int,
                       annualize: bool = True, periods_per_year: int = 252) -> Union[pd.Series, pd.DataFrame]:
    """
    Rolling Annualized Volatility

    Args:
        returns: Returns series
        window: Lookback period
        annualize: Whether to annualize (default True)
        periods_per_year: Trading periods per year

    Returns:
        Rolling volatility
    """
    vol = returns.rolling(window=window, min_periods=window).std()

    if annualize:
        vol = vol * np.sqrt(periods_per_year)

    return vol


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Average True Range

    TR = max(High - Low, |High - PrevClose|, |Low - PrevClose|)
    ATR = EMA(TR, period)

    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: ATR period

    Returns:
        ATR values
    """
    prev_close = close.shift(1)

    # True Range components
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    # True Range = max of the three
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # ATR = EMA of True Range
    atr_values = true_range.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    return atr_values


def bollinger_bands(data: pd.Series, window: int = 20, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bands

    Middle Band = SMA(window)
    Upper Band = Middle + num_std * STD
    Lower Band = Middle - num_std * STD

    Args:
        data: Price series
        window: SMA window
        num_std: Number of standard deviations

    Returns:
        Tuple of (Upper Band, Middle Band, Lower Band)
    """
    middle = sma(data, window)
    std = rolling_std(data, window)

    upper = middle + (num_std * std)
    lower = middle - (num_std * std)

    return upper, middle, lower


def bollinger_bandwidth(data: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.Series:
    """
    Bollinger Bandwidth

    Bandwidth = (Upper - Lower) / Middle

    Args:
        data: Price series
        window: SMA window
        num_std: Number of standard deviations

    Returns:
        Bandwidth values
    """
    upper, middle, lower = bollinger_bands(data, window, num_std)
    return (upper - lower) / middle


def bollinger_percent_b(data: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.Series:
    """
    Bollinger %B

    %B = (Price - Lower) / (Upper - Lower)

    Args:
        data: Price series
        window: SMA window
        num_std: Number of standard deviations

    Returns:
        %B values (0-1, can exceed bounds)
    """
    upper, middle, lower = bollinger_bands(data, window, num_std)
    return (data - lower) / (upper - lower)


# =============================================================================
# CHANNEL INDICATORS
# =============================================================================

def donchian_channels(high: pd.Series, low: pd.Series, window: int) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Donchian Channels

    Upper = Highest High over N periods
    Lower = Lowest Low over N periods
    Middle = (Upper + Lower) / 2

    Args:
        high: High price series
        low: Low price series
        window: Lookback period

    Returns:
        Tuple of (Upper Channel, Middle Channel, Lower Channel)
    """
    upper = high.rolling(window=window, min_periods=window).max()
    lower = low.rolling(window=window, min_periods=window).min()
    middle = (upper + lower) / 2

    return upper, middle, lower


def keltner_channels(high: pd.Series, low: pd.Series, close: pd.Series,
                     ema_period: int = 20, atr_period: int = 10,
                     multiplier: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Keltner Channels

    Middle = EMA(close, period)
    Upper = Middle + multiplier * ATR
    Lower = Middle - multiplier * ATR

    Args:
        high: High price series
        low: Low price series
        close: Close price series
        ema_period: EMA period
        atr_period: ATR period
        multiplier: ATR multiplier

    Returns:
        Tuple of (Upper Channel, Middle Channel, Lower Channel)
    """
    middle = ema(close, ema_period)
    atr_val = atr(high, low, close, atr_period)

    upper = middle + (multiplier * atr_val)
    lower = middle - (multiplier * atr_val)

    return upper, middle, lower


# =============================================================================
# STATISTICAL FUNCTIONS
# =============================================================================

def z_score(data: pd.Series, window: int) -> pd.Series:
    """
    Rolling Z-Score

    Z = (Value - Mean) / StdDev

    Args:
        data: Data series
        window: Lookback period for mean and std

    Returns:
        Z-score values
    """
    rolling_mean = data.rolling(window=window, min_periods=window).mean()
    rolling_std_val = data.rolling(window=window, min_periods=window).std()

    return (data - rolling_mean) / rolling_std_val


def rolling_returns(prices: Union[pd.Series, pd.DataFrame], period: int) -> Union[pd.Series, pd.DataFrame]:
    """
    Rolling Returns over N periods

    Return = Price[t] / Price[t-period] - 1

    Args:
        prices: Price series or DataFrame
        period: Lookback period

    Returns:
        Rolling returns
    """
    return prices.pct_change(periods=period)


def rolling_correlation(series1: pd.Series, series2: pd.Series, window: int) -> pd.Series:
    """
    Rolling Correlation between two series

    Args:
        series1: First data series
        series2: Second data series
        window: Lookback period

    Returns:
        Rolling correlation
    """
    return series1.rolling(window=window, min_periods=window).corr(series2)


def rolling_beta(asset_returns: pd.Series, market_returns: pd.Series, window: int) -> pd.Series:
    """
    Rolling Beta (regression coefficient)

    Beta = Cov(Asset, Market) / Var(Market)

    Args:
        asset_returns: Asset returns series
        market_returns: Market/benchmark returns series
        window: Lookback period

    Returns:
        Rolling beta values
    """
    covariance = asset_returns.rolling(window=window, min_periods=window).cov(market_returns)
    variance = market_returns.rolling(window=window, min_periods=window).var()

    return covariance / variance


def rolling_covariance_matrix(returns: pd.DataFrame, window: int) -> pd.DataFrame:
    """
    Rolling Covariance Matrix (returns last available covariance matrix)

    Args:
        returns: Returns DataFrame (columns = assets)
        window: Lookback period

    Returns:
        Covariance matrix DataFrame
    """
    return returns.iloc[-window:].cov()


def rolling_rank(data: pd.DataFrame, axis: int = 1) -> pd.DataFrame:
    """
    Cross-sectional rank (percentile rank across assets for each date)

    Args:
        data: DataFrame with dates as index, assets as columns
        axis: 1 for cross-sectional (across columns), 0 for time-series

    Returns:
        Percentile ranks (0 to 1)
    """
    return data.rank(axis=axis, pct=True)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def crossover(series1: pd.Series, series2: pd.Series) -> pd.Series:
    """
    Detect crossover (series1 crosses above series2)

    Args:
        series1: First series
        series2: Second series

    Returns:
        Boolean series (True when crossover occurs)
    """
    prev_below = series1.shift(1) < series2.shift(1)
    curr_above = series1 > series2
    return prev_below & curr_above


def crossunder(series1: pd.Series, series2: pd.Series) -> pd.Series:
    """
    Detect crossunder (series1 crosses below series2)

    Args:
        series1: First series
        series2: Second series

    Returns:
        Boolean series (True when crossunder occurs)
    """
    prev_above = series1.shift(1) > series2.shift(1)
    curr_below = series1 < series2
    return prev_above & curr_below


def highest(data: pd.Series, window: int) -> pd.Series:
    """
    Rolling highest value

    Args:
        data: Data series
        window: Lookback period

    Returns:
        Rolling maximum
    """
    return data.rolling(window=window, min_periods=window).max()


def lowest(data: pd.Series, window: int) -> pd.Series:
    """
    Rolling lowest value

    Args:
        data: Data series
        window: Lookback period

    Returns:
        Rolling minimum
    """
    return data.rolling(window=window, min_periods=window).min()


if __name__ == "__main__":
    # Quick test
    import numpy as np

    # Create sample data
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    prices = pd.Series(100 * np.exp(np.cumsum(np.random.randn(100) * 0.02)), index=dates)

    print("Testing indicators...")
    print(f"SMA(20): {sma(prices, 20).iloc[-1]:.2f}")
    print(f"EMA(20): {ema(prices, 20).iloc[-1]:.2f}")
    print(f"RSI(14): {rsi(prices, 14).iloc[-1]:.2f}")
    print(f"Z-Score(20): {z_score(prices, 20).iloc[-1]:.2f}")

    upper, middle, lower = bollinger_bands(prices, 20, 2)
    print(f"Bollinger Bands: Upper={upper.iloc[-1]:.2f}, Middle={middle.iloc[-1]:.2f}, Lower={lower.iloc[-1]:.2f}")

    print("\nAll indicator tests passed!")
