"""
Build corporate-action-corrected NSE panels
===========================================
Input : data_processed/nse_survivorship_free.parquet          (top-500 PIT universe)
        data_processed/nse_survivorship_free_top150.parquet   (top-150 PIT universe)
Output: data_processed/<panel>_adj.parquet     – confirmed / likely splits & bonuses back-adjusted
        data_processed/<panel>_zero40.parquet  – BRACKET variant: every consecutive-row |move|>40%
                                                 neutralised (return forced to 0), real crashes included

Why: scripts/build_nse_universe.py trusted NSE's PREVCLOSE to carry the adjusted prior
close on an ex-date. It does not (see results/nse_data_audit/README.md): in the 2005-2024
old-format files PREVCLOSE on the ex-date is the RAW previous close, so the ratio
PREVCLOSE/CLOSE_{t-1} is 1.0 and no event is ever detected. This script repairs the
output panels directly from the price path, using scripts/nse_ca_audit.py's classifier
(clean-ratio test + persistence + traded-value continuity + Yahoo split-adjusted cross-check).

Adjustment convention (same as build_nse_universe.back_adjust): for an event on date t with
post/pre ratio f, every PRE-event row of that symbol (date < t) has open/high/low/close
multiplied by f (and volume divided by f, i.e. restated in post-event share units). The
post-event price is untouched, so the latest prices stay equal to what traded.

Run:
    .venv/bin/python scripts/build_nse_adjusted_panels.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.nse_ca_audit import PANELS, YAHOO, BIG, SHORT_GAP, classify_events  # noqa: E402

DATA = ROOT / "data_processed"
CA_VERDICTS = ("CA_CONFIRMED_YAHOO", "CA_LIKELY_NICE")


def apply_events(panel: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Back-adjust `panel` for `events` (columns: symbol, date, adj_factor)."""
    df = panel.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)
    cum = np.ones(len(df))
    # per symbol: cumulative factor for rows strictly before each event date
    by_sym = {s: g for s, g in events.groupby("symbol")}
    sym_arr = df["symbol"].to_numpy()
    date_arr = df["date"].to_numpy()
    starts = pd.Series(np.arange(len(df))).groupby(sym_arr).agg(["min", "max"])
    for sym, g in by_sym.items():
        if sym not in starts.index:
            continue
        lo, hi = int(starts.loc[sym, "min"]), int(starts.loc[sym, "max"]) + 1
        d = date_arr[lo:hi]
        for _, ev in g.iterrows():
            m = d < np.datetime64(ev["date"])
            cum[lo:hi][m] *= float(ev["adj_factor"])
    for c in ("open", "high", "low", "close"):
        df[c] = df[c] * cum
    df["volume"] = (df["volume"] / cum).round().astype("int64")
    return df


def hole_events(panel: pd.DataFrame, min_gap_days: int = 30) -> pd.DataFrame:
    """Panel-wide date holes. The universe builder lost 2011-06-22..2011-12-30 (the ISIN column
    appears in NSE's files on 2011-06-22, which breaks the ISIN-keyed point-in-time universe), so
    on 2012-01-02 EVERY stock's 'daily' return is really a 195-day return. Neutralise it: events
    (symbol, T, f=q) for each name that has a row on both sides of the hole."""
    d = panel[["date", "symbol", "close"]].copy()
    d["date"] = pd.to_datetime(d["date"])
    idx = pd.Series(np.sort(d["date"].unique()))
    gap = idx.diff().dt.days
    rows = []
    for t, prev in zip(idx[gap > min_gap_days], idx.shift(1)[gap > min_gap_days]):
        a = d[d["date"] == prev].set_index("symbol")["close"]
        b = d[d["date"] == t].set_index("symbol")["close"]
        both = a.index.intersection(b.index)
        rows.append(pd.DataFrame({"symbol": both, "date": t, "adj_factor": (b[both] / a[both]).to_numpy()}))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["symbol", "date", "adj_factor"])


def main():
    yahoo = pd.read_parquet(YAHOO)
    for label, path in PANELS.items():
        raw = pd.read_parquet(path)
        ev = classify_events(raw, yahoo, label)

        # A) corporate-action back-adjustment
        ca = ev[ev["verdict"].isin(CA_VERDICTS)].dropna(subset=["adj_factor"])
        adj = apply_events(raw, ca)
        out_a = DATA / f"{path.stem}_adj.parquet"
        adj.to_parquet(out_a, index=False)

        # B) bracket: neutralise EVERY consecutive-row |move|>40% (gap <= SHORT_GAP) with the
        #    observed ratio (return := 0), whatever the verdict. Kills genuine crashes too.
        big = ev[(ev["ret"].abs() > BIG) & (ev["gap_days"] <= SHORT_GAP)].copy()
        big["adj_factor"] = np.where(big["adj_factor"].notna(), big["adj_factor"], big["q"])
        # for events we already adjust with a snapped factor keep it; the rest are zeroed at q
        zero = apply_events(raw, big)
        out_b = DATA / f"{path.stem}_zero40.parquet"
        zero.to_parquet(out_b, index=False)

        # C) neutralise the 2011-H2 data hole on each variant (+ on the raw panel, to isolate it)
        # (factors are computed on each variant's OWN prices, so CA adjustments are not double counted)
        raw_d = raw.assign(date=pd.to_datetime(raw["date"]))
        hole = hole_events(raw_d)
        out_files = {"raw_nohole": apply_events(raw_d, hole)}
        out_files["adj_nohole"] = apply_events(adj, hole_events(adj))
        out_files["zero40_nohole"] = apply_events(zero, hole_events(zero))
        for tag, df in out_files.items():
            df.to_parquet(DATA / f"{path.stem}_{tag.replace('raw_', '')}.parquet", index=False)
        print(f"   hole events neutralised: {len(hole)} names on {sorted(set(hole['date'].dt.date.astype(str)))}")

        # sanity: residual consecutive-day moves
        def resid(df):
            p = df.pivot_table(index="date", columns="symbol", values="close")
            r = p.pct_change(fill_method=None).stack()
            return int((r < -BIG).sum()), int((r > BIG).sum()), float(r.min()), float(r.max())

        print(f"\n[{label}] CA events applied: {len(ca)}  "
              f"(confirmed-by-Yahoo {int((ca['verdict']=='CA_CONFIRMED_YAHOO').sum())}, "
              f"likely-clean-ratio {int((ca['verdict']=='CA_LIKELY_NICE').sum())})")
        for tag, df in (("raw", raw_d), ("adj", adj), ("zero40", zero), ("adj_nohole", out_files["adj_nohole"])):
            lo, hi, mn, mx = resid(df)
            print(f"   {tag:7s} engine-visible moves < -40%: {lo:4d}   > +40%: {hi:3d}   min {mn:+.1%}  max {mx:+.1%}")
        print(f"   -> {out_a.relative_to(ROOT)}\n   -> {out_b.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
