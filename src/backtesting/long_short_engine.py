"""
Long-Short Backtesting Engine
==============================
Dollar-neutral long-short portfolio backtester.

Takes a DataFrame of factor scores (rows = dates, cols = symbols),
splits the universe into long quintile (top 20%) and short quintile
(bottom 20%), runs a fully-vectorized backtest, and returns metrics
including SPY (market) correlation — the key proof of market independence.

Usage:
    from src.backtesting.long_short_engine import LongShortBacktester, LongShortResult

    engine = LongShortBacktester(prices, factor_scores)
    result = engine.run()
    print(result.sharpe_ratio, result.spy_correlation)
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class LongShortResult:
    """All outputs from a long-short backtest."""

    # Core metrics
    sharpe_ratio: float
    cagr: float
    max_drawdown: float
    volatility: float
    sortino_ratio: float
    calmar_ratio: float
    win_rate: float

    # The key number: how independent from the market is this?
    spy_correlation: float

    # Component metrics
    long_sharpe: float
    short_sharpe: float
    long_cagr: float
    short_cagr: float

    # Equity curves (monthly sampled for frontend)
    equity_curve: pd.Series         # net L/S, daily
    long_equity: pd.Series          # long-only leg, daily
    short_equity: pd.Series         # short-only leg, daily

    # Returns (daily)
    returns: pd.Series

    # Metadata
    strategy_name: str = ""
    factor_direction: str = "higher_is_better"   # 'higher_is_better' or 'lower_is_better'
    quintile_pct: float = 0.20
    start_date: str = ""
    end_date: str = ""
    n_long: int = 0
    n_short: int = 0

    def to_dict(self) -> dict:
        """Serialise for JSON output (no DataFrames)."""
        # Monthly equity curve for frontend
        monthly = self.equity_curve.resample("M").last()
        eq_series = [
            {"date": str(d.date()), "value": round(float(v), 6)}
            for d, v in monthly.items()
            if pd.notna(v)
        ]
        return {
            "sharpe_ratio":    round(float(self.sharpe_ratio),   4),
            "cagr":            round(float(self.cagr),            4),
            "max_drawdown":    round(float(self.max_drawdown),    4),
            "volatility":      round(float(self.volatility),      4),
            "sortino_ratio":   round(float(self.sortino_ratio),   4),
            "calmar_ratio":    round(float(self.calmar_ratio),    4),
            "win_rate":        round(float(self.win_rate),        4),
            "spy_correlation": round(float(self.spy_correlation), 4),
            "long_sharpe":     round(float(self.long_sharpe),     4),
            "short_sharpe":    round(float(self.short_sharpe),    4),
            "long_cagr":       round(float(self.long_cagr),       4),
            "short_cagr":      round(float(self.short_cagr),      4),
            "equity_curve":    eq_series,
            "strategy_name":   self.strategy_name,
            "factor_direction": self.factor_direction,
            "start_date":      self.start_date,
            "end_date":        self.end_date,
            "n_avg_long":      self.n_long,
            "n_avg_short":     self.n_short,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class LongShortBacktester:
    """
    Dollar-neutral long-short backtester.

    Parameters
    ----------
    prices : pd.DataFrame
        Wide price matrix (index = dates, columns = tickers).
        Must already be cleaned (no extreme returns, price floor applied).

    factor_scores : pd.DataFrame
        Raw factor scores for every stock at every rebalancing date.
        Same shape/columns as prices (but typically sparse — only populated
        at rebalancing dates, NaN elsewhere).
        Higher score = better according to the factor.
        If the factor is "lower is better" (e.g. volatility), pass
        factor_scores = -1 * raw_scores so that higher is still better.

    quintile_pct : float
        Fraction of universe in each leg. Default 0.20 (quintile).

    commission_bps : float
        Round-trip commission in basis points. Applied to both legs.
        Default 15 bps.

    borrow_cost_bps : float
        Annual short-selling borrow cost in basis points.
        Default 50 bps (~0.50%/yr), representative for large-cap US.

    spy_returns : pd.Series, optional
        Daily SPY returns for correlation calculation.
        If None, correlation is set to NaN.

    rebal_freq : str
        Rebalancing frequency passed to pandas resample/offset logic.
        Typically 'ME' (month-end) or 'QE' (quarter-end).
        If None, the engine infers rebalancing from non-NaN rows in
        factor_scores.
    """

    ANNUAL_PERIODS = 252
    RF_ANNUAL = 0.02          # 2% risk-free rate

    def __init__(
        self,
        prices: pd.DataFrame,
        factor_scores: pd.DataFrame,
        quintile_pct: float = 0.20,
        commission_bps: float = 15.0,
        borrow_cost_bps: float = 50.0,
        spy_returns: Optional[pd.Series] = None,
        rebal_freq: Optional[str] = None,
    ):
        self.prices = prices.copy()
        self.factor_scores = factor_scores.copy()
        self.quintile_pct = quintile_pct
        self.commission_bps = commission_bps
        self.borrow_cost_daily = (borrow_cost_bps / 10_000) / self.ANNUAL_PERIODS
        self.spy_returns = spy_returns
        self.rebal_freq = rebal_freq

        # Compute price returns once (fill_method=None to avoid false returns
        # at NaN boundaries — same safeguard as main engine)
        self.returns = prices.pct_change(fill_method=None).clip(-0.95, 2.0)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self, strategy_name: str = "") -> LongShortResult:
        """Run the full long-short backtest and return a LongShortResult."""

        long_w, short_w = self._build_weights()

        # ── Long leg ──────────────────────────────────────────────────
        long_ret  = self._leg_returns(long_w,  sign=+1)
        short_ret = self._leg_returns(short_w, sign=-1)

        # ── Net long-short portfolio ──────────────────────────────────
        # Align on common dates
        common = long_ret.index.intersection(short_ret.index)
        ls_ret  = (long_ret.loc[common] + short_ret.loc[common]).fillna(0)

        # Clip at -50% to prevent cumprod zeroing
        ls_ret = ls_ret.clip(-0.50, 0.50)

        # ── Equity curves ─────────────────────────────────────────────
        ls_eq     = (1 + ls_ret).cumprod()
        long_eq   = (1 + long_ret.reindex(common).fillna(0)).cumprod()
        short_eq  = (1 + short_ret.reindex(common).fillna(0)).cumprod()

        # ── Metrics ───────────────────────────────────────────────────
        sr          = self._sharpe(ls_ret)
        cagr_v      = self._cagr(ls_eq)
        mdd         = self._mdd(ls_eq)
        vol         = ls_ret.std() * np.sqrt(self.ANNUAL_PERIODS)
        sortino     = self._sortino(ls_ret)
        calmar      = cagr_v / abs(mdd) if mdd != 0 else 0.0
        win_r       = (ls_ret > 0).sum() / max((ls_ret != 0).sum(), 1)

        long_sr     = self._sharpe(long_ret.reindex(common).fillna(0))
        short_sr    = self._sharpe(short_ret.reindex(common).fillna(0))
        long_cagr   = self._cagr(long_eq)
        short_cagr  = self._cagr(short_eq)

        spy_corr = np.nan
        if self.spy_returns is not None:
            spy = self.spy_returns
            # Ensure 1-D: squeeze DataFrame → Series
            if isinstance(spy, pd.DataFrame):
                spy = spy.squeeze()
            aligned_spy = spy.reindex(common).fillna(0)
            spy_std = float(aligned_spy.std())
            ls_std  = float(ls_ret.std())
            if spy_std > 0 and ls_std > 0:
                spy_corr = float(ls_ret.corr(aligned_spy))

        # Average number of positions (non-zero weights, sampled monthly)
        monthly_long  = long_w.resample("M").last()
        monthly_short = short_w.resample("M").last()
        n_long  = int((monthly_long  > 1e-9).sum(axis=1).mean())
        n_short = int((monthly_short > 1e-9).sum(axis=1).mean())

        return LongShortResult(
            sharpe_ratio   = float(sr),
            cagr           = float(cagr_v),
            max_drawdown   = float(mdd),
            volatility     = float(vol),
            sortino_ratio  = float(sortino),
            calmar_ratio   = float(calmar),
            win_rate       = float(win_r),
            spy_correlation= float(spy_corr),
            long_sharpe    = float(long_sr),
            short_sharpe   = float(short_sr),
            long_cagr      = float(long_cagr),
            short_cagr     = float(short_cagr),
            equity_curve   = ls_eq,
            long_equity    = long_eq,
            short_equity   = short_eq,
            returns        = ls_ret,
            strategy_name  = strategy_name,
            start_date     = str(ls_eq.index[0].date()) if len(ls_eq) > 0 else "",
            end_date       = str(ls_eq.index[-1].date()) if len(ls_eq) > 0 else "",
            n_long         = n_long,
            n_short        = n_short,
        )

    # ------------------------------------------------------------------
    # Internal: weight construction
    # ------------------------------------------------------------------

    def _build_weights(self):
        """
        Build long and short weight matrices.

        At each rebalancing date:
        - Long leg:  top `quintile_pct` of stocks by factor score
                     → equal-weighted, sum = +1.0
        - Short leg: bottom `quintile_pct` of stocks by factor score
                     → equal-weighted, sum = +1.0  (sign applied later)

        Weights are forward-filled between rebalancing dates.
        """
        # Determine rebalancing dates = rows where factor_scores has any
        # non-NaN value (strategies populate scores only at rebal dates)
        all_dates = self.prices.index
        score_cols = self.factor_scores.columns.intersection(self.prices.columns)
        scores_aligned = self.factor_scores[score_cols].reindex(all_dates)

        # Rows with at least one non-NaN score = rebalancing dates
        rebal_mask = scores_aligned.notna().any(axis=1)
        rebal_dates = all_dates[rebal_mask]

        long_w  = pd.DataFrame(0.0, index=all_dates, columns=score_cols)
        short_w = pd.DataFrame(0.0, index=all_dates, columns=score_cols)

        for date in rebal_dates:
            row = scores_aligned.loc[date].dropna()
            if len(row) < 10:        # need at least 10 stocks to form quintiles
                continue

            n_side = max(2, int(len(row) * self.quintile_pct))

            top_stocks    = row.nlargest(n_side).index
            bottom_stocks = row.nsmallest(n_side).index

            long_w.loc[date, :]           = 0.0
            long_w.loc[date, top_stocks]  = 1.0 / n_side

            short_w.loc[date, :]             = 0.0
            short_w.loc[date, bottom_stocks] = 1.0 / n_side

        # Forward-fill between rebalancing dates
        long_w  = long_w.replace(0, np.nan).ffill().fillna(0)
        short_w = short_w.replace(0, np.nan).ffill().fillna(0)

        # Shift by 1 day: signal at t executes at t+1 (no look-ahead)
        long_w  = long_w.shift(1).fillna(0)
        short_w = short_w.shift(1).fillna(0)

        return long_w, short_w

    # ------------------------------------------------------------------
    # Internal: leg returns
    # ------------------------------------------------------------------

    def _leg_returns(self, weights: pd.DataFrame, sign: int) -> pd.Series:
        """
        Compute daily returns for one leg.

        sign = +1  for long leg  → return = weights · asset_returns
        sign = -1  for short leg → return = -weights · asset_returns - borrow_cost

        Transaction costs are applied on turnover (weight changes).
        """
        # Align weights with available return columns
        common_cols = weights.columns.intersection(self.returns.columns)
        w = weights[common_cols]
        r = self.returns[common_cols]

        # Portfolio return before costs
        raw = (w * r).sum(axis=1) * sign

        # Turnover: sum of absolute weight changes / 2
        turnover = w.diff().abs().sum(axis=1) / 2.0
        tx_cost  = turnover * (self.commission_bps / 10_000)

        # Short borrow cost only on short leg
        borrow_cost = 0.0
        if sign == -1:
            # Applied daily, proportional to how much of the portfolio is short
            active_short = (w > 1e-9).any(axis=1).astype(float)
            borrow_cost  = active_short * self.borrow_cost_daily

        daily_ret = raw - tx_cost - borrow_cost
        return daily_ret.fillna(0)

    # ------------------------------------------------------------------
    # Internal: scalar metrics
    # ------------------------------------------------------------------

    def _sharpe(self, returns: pd.Series) -> float:
        returns = returns.dropna()
        if len(returns) < 10 or returns.std() == 0:
            return 0.0
        excess = returns - self.RF_ANNUAL / self.ANNUAL_PERIODS
        return float(excess.mean() / returns.std() * np.sqrt(self.ANNUAL_PERIODS))

    def _cagr(self, equity: pd.Series) -> float:
        if len(equity) < 2:
            return 0.0
        total = equity.iloc[-1] / equity.iloc[0] - 1
        if total <= -1:
            return -1.0
        return float((1 + total) ** (self.ANNUAL_PERIODS / len(equity)) - 1)

    def _mdd(self, equity: pd.Series) -> float:
        if len(equity) < 2:
            return 0.0
        peak = equity.expanding().max()
        dd   = (equity / peak - 1)
        return float(dd.min())

    def _sortino(self, returns: pd.Series) -> float:
        returns = returns.dropna()
        if len(returns) < 10:
            return 0.0
        excess = returns - self.RF_ANNUAL / self.ANNUAL_PERIODS
        down   = returns[returns < 0]
        if len(down) == 0 or down.std() == 0:
            return 0.0
        down_vol = down.std() * np.sqrt(self.ANNUAL_PERIODS)
        return float(excess.mean() * self.ANNUAL_PERIODS / down_vol)
