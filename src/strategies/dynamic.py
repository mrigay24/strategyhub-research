"""
Dynamic Factor Strategy

Wraps a user-provided Python factor scoring function into a full backtestable
MultiAssetStrategy. Used exclusively by the AI Strategy Builder to run
custom-generated strategies through the 25-year backtest pipeline.

The scoring function receives:
  prices:  pd.DataFrame — date × symbol adjusted close prices
  returns: pd.DataFrame — date × symbol daily returns (pct_change)
  pd:      pandas module (injected)
  np:      numpy module (injected)

And must return:
  pd.DataFrame — same shape as prices, higher value = more attractive stock.
  NaN means "no signal yet" for that stock on that date.

Top quintile (20%) goes long, equal-weighted. Monthly rebalancing.
"""

import textwrap
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd

from src.strategies.base import MultiAssetStrategy


class DynamicFactorStrategy(MultiAssetStrategy):
    """
    A strategy class built at runtime from a user-supplied factor scoring function.

    Parameters
    ----------
    data : pd.DataFrame
        Wide-format price data (date index, symbol columns).
    params : dict
        Strategy parameters. Relevant keys:
          - top_pct (float, default 0.20): fraction of stocks to hold long
          - rebalance_freq (str, default 'ME'): pandas offset for rebalancing
    factor_code : str
        Python function body that receives `prices`, `returns`, `pd`, `np`
        and returns a pd.DataFrame of scores (same shape as prices).
    """

    DEFAULT_PARAMS: Dict[str, Any] = {
        "top_pct": 0.20,
        "rebalance_freq": "ME",
    }

    def __init__(self, data: pd.DataFrame, params: Optional[Dict] = None, factor_code: str = ""):
        super().__init__(data, params or self.DEFAULT_PARAMS)
        self.factor_code = factor_code
        self._scoring_fn = self._compile_factor_code(factor_code)

    # ── compile ────────────────────────────────────────────────────────────────

    @staticmethod
    def _compile_factor_code(code: str):
        """
        Compile the factor_code string into a callable function.

        Wraps the code in a def block and injects pd / np into the namespace.
        Only pd, np, and the price/return DataFrames are accessible — no builtins
        that could cause harm (open, exec, eval, import, etc.).
        """
        # Indent every line so it becomes the function body
        indented = textwrap.indent(code.strip(), "    ")
        full_fn = f"def _score_fn(prices, returns, pd, np):\n{indented}\n"

        # Restricted execution namespace — no __builtins__ access
        safe_namespace: Dict[str, Any] = {"__builtins__": {}}
        exec(compile(full_fn, "<factor_code>", "exec"), safe_namespace)
        return safe_namespace["_score_fn"]

    # ── generate_signals ───────────────────────────────────────────────────────

    def generate_signals(self) -> pd.DataFrame:
        """
        Run the scoring function on all dates, then select top-quintile stocks
        monthly and return equal-weighted position signals.
        """
        top_pct: float = self.params.get("top_pct", 0.20)
        rebalance_freq: str = self.params.get("rebalance_freq", "ME")

        # 1. Compute scores for all dates
        try:
            scores: pd.DataFrame = self._scoring_fn(self.prices, self.returns, pd, np)
        except Exception as e:
            raise RuntimeError(f"Factor code execution failed: {e}") from e

        if not isinstance(scores, pd.DataFrame):
            raise ValueError(
                f"Factor code must return a pd.DataFrame, got {type(scores).__name__}"
            )

        # Align scores to price index
        scores = scores.reindex(index=self.prices.index, columns=self.prices.columns)

        # 2. Build signal DataFrame (all zeros to start)
        signals = pd.DataFrame(0.0, index=self.prices.index, columns=self.prices.columns)

        # 3. Monthly rebalancing: on each rebalance date, select top-pct stocks
        try:
            rebalance_dates = self.prices.resample(rebalance_freq).last().index
        except Exception:
            # Fallback to month-end
            rebalance_dates = self.prices.resample("ME").last().index

        for rdate in rebalance_dates:
            if rdate not in scores.index:
                continue
            day_scores = scores.loc[rdate].dropna()
            if len(day_scores) < 5:
                continue

            # Select top_pct of stocks by score
            n_long = max(1, int(len(day_scores) * top_pct))
            selected = day_scores.nlargest(n_long)

            weight = 1.0 / len(selected)
            signals.loc[rdate, selected.index] = weight

        # Forward-fill between rebalance dates
        signals = signals.replace(0.0, np.nan)
        signals = signals.ffill()
        signals = signals.fillna(0.0)

        return signals
