"""
Event-Driven Strategies

Earnings Surprise Momentum strategy.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

from src.strategies.base import MultiAssetStrategy, StrategyType
from src.processing.indicators import rolling_volatility


class EarningsSurpriseMomentumStrategy(MultiAssetStrategy):
    """
    Earnings Surprise Momentum (Post-Earnings Drift) Strategy

    Exploits the Post-Earnings Announcement Drift (PEAD) anomaly:
    stocks with positive earnings surprises tend to drift higher
    for weeks after the announcement.

    Price-Based Proxy (no earnings data needed):
    - Detect "earnings-like" events as days with abnormally high volume
      AND a large price move (>2 std devs)
    - If the surprise was positive (price up), go long
    - Hold for a drift period (default 63 days ~3 months)

    NOTE: With actual earnings data, this strategy would use:
    - EPS surprise (actual - consensus)
    - Revenue surprise
    - Standardized Unexpected Earnings (SUE)
    - Earnings revision momentum

    Tunable Parameters:
    - volume_spike_mult: Volume must be N times average (default 3.0)
    - price_move_std: Price move must exceed N std devs (default 2.0)
    - vol_lookback: Window for calculating normal volume/price vol (default 21)
    - drift_period: Days to hold after event (default 63)
    - max_positions: Maximum concurrent positions (default 30)
    - rebalance_freq: How often to scan for new events (default D)
    """

    DEFAULT_PARAMS = {
        'volume_spike_mult': 3.0,
        'price_move_std': 2.0,
        'vol_lookback': 21,
        'drift_period': 63,
        'max_positions': 30,
        'rebalance_freq': 'D',
    }

    @property
    def name(self) -> str:
        return "Earnings Surprise Momentum"

    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.MOMENTUM

    def generate_signals(self) -> pd.DataFrame:
        vol_lb = self.params['vol_lookback']
        spike_mult = self.params['volume_spike_mult']
        move_std = self.params['price_move_std']
        drift = self.params['drift_period']
        max_pos = self.params['max_positions']

        # Daily returns and their rolling std
        daily_returns = self.returns
        return_std = daily_returns.rolling(vol_lb, min_periods=vol_lb).std()

        # Volume data
        if 'volume' in self._all_prices:
            volume = self._all_prices['volume']
            avg_volume = volume.rolling(vol_lb, min_periods=vol_lb).mean()
            volume_ratio = volume / avg_volume
        else:
            # Without volume data, use only price moves
            volume_ratio = pd.DataFrame(
                spike_mult + 1,  # Always passes volume filter
                index=self.prices.index,
                columns=self.prices.columns
            )

        # Detect positive surprise events
        is_volume_spike = volume_ratio > spike_mult
        is_large_up_move = daily_returns > (move_std * return_std)

        positive_surprise = is_volume_spike & is_large_up_move

        signals = pd.DataFrame(0.0, index=self.prices.index, columns=self.prices.columns)

        # Track active positions: {stock: expiry_date}
        active_positions = {}

        for i, date in enumerate(self.prices.index):
            # Remove expired positions
            expired = [s for s, exp in active_positions.items() if date >= exp]
            for s in expired:
                del active_positions[s]

            # Check for new events on this date
            if date in positive_surprise.index:
                events_today = positive_surprise.loc[date].dropna()
                new_events = events_today[events_today].index

                for stock in new_events:
                    if stock not in active_positions and len(active_positions) < max_pos:
                        # Calculate expiry
                        future_idx = i + drift
                        if future_idx < len(self.prices.index):
                            expiry = self.prices.index[future_idx]
                        else:
                            expiry = self.prices.index[-1]
                        active_positions[stock] = expiry

            # Set equal weights for active positions
            n = len(active_positions)
            if n > 0:
                weight = 1.0 / n
                for stock in active_positions:
                    signals.loc[date, stock] = weight

        return signals

    def get_param_grid(self) -> Dict[str, List[Any]]:
        return {
            'volume_spike_mult': [2.0, 3.0, 5.0],
            'price_move_std': [1.5, 2.0, 3.0],
            'drift_period': [21, 42, 63],
            'max_positions': [15, 30],
        }
