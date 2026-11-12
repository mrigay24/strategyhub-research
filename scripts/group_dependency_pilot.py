"""
Paper 2 pilot: business groups and hidden concentration (India).
Plan: docs/group_dependency/PILOT_PLAN.md · Rules: docs/group_dependency/PREREGISTRATION.md

Subcommands (run in this order; each step is committed before the next):

  universe   Phase 2. Build the symbol universe from TRADED VALUE ONLY
             (close x volume). No returns are computed here. Output:
             results/group_dependency/universe.csv (the list the group map covers).
  run        Phase 4. The pre-registered tests. Only after the group map and the
             pre-registration are committed.

Run:  .venv/bin/python scripts/group_dependency_pilot.py universe
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data_processed"
PANEL = DATA / "nse_survivorship_free_adj.parquet"
OUT = ROOT / "results" / "group_dependency"
OUT.mkdir(parents=True, exist_ok=True)

TOP_N = 500                  # top names by 63-day traded value at a month-end
START, END = "2005-01-01", "2025-12-31"


def traded_value_panel() -> pd.DataFrame:
    raw = pd.read_parquet(PANEL, columns=["date", "symbol", "close", "volume"])
    raw["date"] = pd.to_datetime(raw["date"])
    raw["tv"] = raw["close"] * raw["volume"]
    return raw.pivot_table(index="date", columns="symbol", values="tv")


def build_universe() -> pd.DataFrame:
    """Every symbol that was in the top TOP_N by 63-day average traded value at any
    month-end 2005-2025. Uses traded value only; no returns."""
    tv = traded_value_panel()
    tv63 = tv.rolling(63, min_periods=40).mean()
    per = tv63.index.to_period("M")
    month_end = tv63.index[np.append(np.where(per[1:] != per[:-1])[0], len(per) - 1)]
    me = tv63.loc[month_end].loc[START:END]
    rank = me.rank(axis=1, ascending=False)
    inn = rank <= TOP_N
    syms = inn.columns[inn.any()]
    rows = []
    for s in syms:
        months = inn.index[inn[s]]
        rows.append({
            "symbol": s,
            "first_top500": months.min().date().isoformat(),
            "last_top500": months.max().date().isoformat(),
            "n_months_top500": int(len(months)),
            "best_rank": int(rank[s].min()),
            "first_trade": tv[s].first_valid_index().date().isoformat(),
            "last_trade": tv[s].last_valid_index().date().isoformat(),
            "median_tv63_cr": float(me.loc[months, s].median() / 1e7),
        })
    u = pd.DataFrame(rows).sort_values("best_rank").reset_index(drop=True)
    u.to_csv(OUT / "universe.csv", index=False)
    print(f"universe: {len(u)} symbols ever in the top {TOP_N} at a month-end "
          f"({me.index.min().date()} to {me.index.max().date()}, {len(me)} month-ends)")
    return u


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["universe", "run"])
    a = ap.parse_args()
    if a.step == "universe":
        build_universe()
    else:
        sys.exit("run: not yet written (needs the committed group map and pre-registration)")


if __name__ == "__main__":
    main()
