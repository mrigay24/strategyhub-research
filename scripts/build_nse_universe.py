"""
#2 — Build the survivorship-free, split-adjusted NSE universe from bhavcopy
=========================================================================
Input : data_raw/nse_bhavcopy_panel.parquet   (from nse_bhavcopy_pipeline.py)
Output: data_processed/nse_survivorship_free.parquet  (long format the engine eats:
        date, symbol, open, high, low, close, volume — adjusted close)

Three jobs:
  1. CORPORATE-ACTION BACK-ADJUST (splits/bonuses) using bhavcopy alone:
     on an ex-date NSE reports PREVCLOSE = adjusted prior close, so the per-day
     ratio r_t = PREVCLOSE_t / CLOSE_{t-1} ≈ 1 normally and = the split/bonus
     factor on ex-dates. Back-adjusted price = close_t × ∏_{s>t} r_s(event).
     (price-return; dividends NOT added — same basis as the US data.)
  2. IDENTITY by ISIN (survives symbol renames); label each line with the most
     recent symbol it traded under.
  3. PIT LIQUIDITY UNIVERSE: a name is investable in year Y if it ranked in the
     top `TOP_N` by median daily turnover in year Y-1 (prior-year → no lookahead).
     Survivorship-free: delisted names rank in the years they actually traded.

Run:
    .venv/bin/python scripts/build_nse_universe.py            # build
    .venv/bin/python scripts/build_nse_universe.py --selftest # just test the math
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data_raw" / "nse_bhavcopy_panel.parquet"
OUT = ROOT / "data_processed" / "nse_survivorship_free.parquet"

TOP_N = 500            # investable names per year (Nifty-500-scale)
EVENT_LO, EVENT_HI = 0.90, 1.10   # treat ratio outside this band as a CA event
RATIO_FLOOR, RATIO_CAP = 0.02, 50.0  # sane bounds (guard against bad ticks)
MAX_GAP_DAYS = 5       # only trust ratio across (near-)consecutive trading days


def back_adjust(g: pd.DataFrame) -> pd.Series:
    """Return split/bonus back-adjusted close for one symbol's time-ordered rows.
    g must have columns close, prevclose, date (ascending). Vectorized."""
    close = g["close"].to_numpy(dtype=float)
    prevc = g["prevclose"].to_numpy(dtype=float)
    dates = g["date"].to_numpy()
    n = len(g)
    prev_close = np.empty(n); prev_close[0] = np.nan; prev_close[1:] = close[:-1]
    gap = np.full(n, 9999.0); gap[1:] = (dates[1:] - dates[:-1]).astype("timedelta64[D]").astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = prevc / prev_close
    e = np.ones(n)
    event = ((gap <= MAX_GAP_DAYS) & np.isfinite(ratio) & (prev_close > 0)
             & (ratio > RATIO_FLOOR) & (ratio < RATIO_CAP)
             & ((ratio < EVENT_LO) | (ratio > EVENT_HI)))
    e[event] = ratio[event]                  # corporate-action factor on ex-dates
    # F_t = ∏_{s>t} e_s  → suffix product shifted by one
    suffix = np.cumprod(e[::-1])[::-1]       # P_t = ∏_{s>=t} e_s
    F = np.empty(n)
    F[:-1] = suffix[1:]                      # P_{t+1}
    F[-1] = 1.0
    return pd.Series(close * F, index=g.index)


def _selftest():
    """Synthetic 1:2 split: unadjusted close 100→50 must become continuous."""
    df = pd.DataFrame({
        "date": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-06"]),
        "close": [100.0, 50.0, 52.0, 51.0],
        "prevclose": [99.0, 50.0, 50.0, 52.0],   # ex-date 01-02: prevclose=50 (adj of 100)
    })
    adj = back_adjust(df).to_numpy()
    # pre-split 100 should scale to 50; post-split untouched
    assert abs(adj[0] - 50.0) < 1e-9, adj
    assert abs(adj[1] - 50.0) < 1e-9, adj
    assert abs(adj[2] - 52.0) < 1e-9, adj
    ret = adj[1] / adj[0] - 1
    assert abs(ret) < 1e-9, f"split should give 0% adj return, got {ret}"
    # and a no-event series must be unchanged
    df2 = pd.DataFrame({"date": pd.to_datetime(["2020-01-01", "2020-01-02"]),
                        "close": [100.0, 103.0], "prevclose": [99.0, 100.0]})
    assert np.allclose(back_adjust(df2).to_numpy(), [100.0, 103.0])
    print("self-test PASSED — back-adjust makes splits continuous, leaves normal days intact")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--panel", default=str(PANEL), help="bhavcopy panel parquet")
    ap.add_argument("--out", default=str(OUT), help="output universe parquet")
    ap.add_argument("--top-n", type=int, default=TOP_N, help="investable names per year")
    a = ap.parse_args()
    top_n = a.top_n
    if a.selftest:
        _selftest()
        return

    _selftest()  # always validate the math before trusting a real build
    panel_path, out_path = Path(a.panel), Path(a.out)
    if not panel_path.exists():
        print(f"panel not found: {panel_path} — run nse_bhavcopy_pipeline.py first")
        return

    df = pd.read_parquet(panel_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["series"].isin(["EQ", "BE"])].copy()
    # dedupe (isin,date): prefer EQ, then higher turnover
    df["_eq"] = (df["series"] == "EQ").astype(int)
    df = (df.sort_values(["isin", "date", "_eq", "turnover"])
            .drop_duplicates(["isin", "date"], keep="last"))
    print(f"panel: {len(df):,} rows | {df['isin'].nunique()} ISINs | "
          f"{df['date'].min().date()} → {df['date'].max().date()}")

    # most-recent symbol per ISIN (survives renames)
    last_symbol = (df.sort_values("date").groupby("isin")["symbol"].last())

    # back-adjust per ISIN
    df = df.sort_values(["isin", "date"])
    df["adj_close"] = df.groupby("isin", group_keys=False).apply(
        lambda g: back_adjust(g))
    # adjust OHL by the same per-row factor (factor = adj_close/close)
    fac = (df["adj_close"] / df["close"]).replace([np.inf, -np.inf], np.nan).fillna(1.0)
    for col in ("open", "high", "low"):
        df[col] = df[col] * fac

    # PIT liquidity universe: top-N by PRIOR-year median turnover
    df["year"] = df["date"].dt.year
    yr_turn = df.groupby(["isin", "year"])["turnover"].median().reset_index()
    keep_pairs = set()
    years = sorted(df["year"].unique())
    for y in years:
        prior = yr_turn[yr_turn["year"] == y - 1]
        ranked = prior.nlargest(top_n, "turnover")["isin"] if len(prior) else \
            yr_turn[yr_turn["year"] == y].nlargest(top_n, "turnover")["isin"]
        for isin in ranked:
            keep_pairs.add((isin, y))
    mask = pd.MultiIndex.from_arrays([df["isin"], df["year"]]).isin(keep_pairs)
    df = df[mask]

    out = pd.DataFrame({
        "date": df["date"],
        "symbol": df["isin"].map(last_symbol),
        "open": df["open"], "high": df["high"], "low": df["low"],
        "close": df["adj_close"], "volume": df["volume"],
    }).dropna(subset=["close", "symbol"])
    # if a rename collapsed two ISINs onto one symbol+date, keep the more liquid
    out = out.sort_values("volume").drop_duplicates(["date", "symbol"], keep="last")
    out = out.sort_values(["symbol", "date"]).reset_index(drop=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(out_path, index=False)
    print(f"\nsurvivorship-free universe → {out_path}")
    print(f"  rows {len(out):,} | names {out['symbol'].nunique()} | "
          f"{out['date'].min().date()} → {out['date'].max().date()}")
    # how many names per year (should hover near TOP_N)
    per_yr = out.assign(y=out["date"].dt.year).groupby("y")["symbol"].nunique()
    print(f"  names/yr: {dict(per_yr.iloc[[0, len(per_yr)//2, -1]])}")


if __name__ == "__main__":
    main()
