"""
Probe: does NSE's PREVCLOSE on an ex-date carry the ADJUSTED prior close?
=========================================================================
build_nse_universe.back_adjust assumes it does (ratio PREVCLOSE_t / CLOSE_{t-1} = split factor on
an ex-date). This script opens the raw daily bhavcopy zips (data_raw/nse_bhavcopy/<year>/<date>.zip)
for a stratified sample of corporate actions that Yahoo's adjusted series confirms, and prints
PREVCLOSE_exdate / CLOSE_prevday. If NSE adjusted PREVCLOSE this would be ~ the split factor
(0.2, 0.5 ...); if it is ~1.00 the ratio-based detector is blind to the event.

NOTE: the daily zips are iCloud 'dataless' stubs (~50 KB each); each read downloads one file,
so keep the sample small. A SIGALRM guard stops a hung download.

Run:  .venv/bin/python scripts/nse_prevclose_probe.py [N]
Output: results/nse_data_audit/prevclose_probe.csv
"""
from __future__ import annotations

import io
import signal
import sys
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BH = ROOT / "data_raw" / "nse_bhavcopy"
SUS = ROOT / "results" / "nse_data_audit" / "corporate_action_suspects.csv"
OUT = ROOT / "results" / "nse_data_audit" / "prevclose_probe.csv"
UDIFF = pd.Timestamp("2024-07-08")


def day_rows(d: pd.Timestamp) -> pd.DataFrame | None:
    p = BH / str(d.year) / f"{d:%Y%m%d}.zip"
    if not p.exists():
        return None
    signal.alarm(40)
    try:
        z = zipfile.ZipFile(p)
        df = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])))
    finally:
        signal.alarm(0)
    df.columns = [c.strip() for c in df.columns]
    if "TckrSymb" in df.columns:
        return pd.DataFrame({"symbol": df["TckrSymb"].astype(str).str.strip(), "series": df["SctySrs"].astype(str).str.strip(),
                             "close": df["ClsPric"], "prevclose": df["PrvsClsgPric"],
                             "isin": df["ISIN"].astype(str).str.strip()})
    return pd.DataFrame({"symbol": df["SYMBOL"].astype(str).str.strip(), "series": df["SERIES"].astype(str).str.strip(),
                         "close": df["CLOSE"], "prevclose": df["PREVCLOSE"],
                         "isin": df["ISIN"].astype(str).str.strip() if "ISIN" in df.columns else ""})


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    t = pd.read_csv(SUS, parse_dates=["date", "prev_date"])
    c = t[(t.verdict == "CA_CONFIRMED_YAHOO") & (t.gap_days <= 5) & (t.tier == "primary_gt40")].sort_values("date")
    # stratify by year so every era (old format, ISIN era, UDiFF) is represented
    pick = c.groupby(c.date.dt.year, group_keys=False).apply(lambda g: g.iloc[len(g) // 2]).reset_index(drop=True)
    if len(pick) > n:
        pick = pick.iloc[[int(i) for i in pd.Series(range(n)) * (len(pick) - 1) / (n - 1)]]
    rows = []
    for _, e in pick.iterrows():
        a, b = day_rows(e["prev_date"]), day_rows(e["date"])
        if a is None or b is None:
            continue
        ra = a[(a.symbol == e["symbol"]) & a.series.isin(["EQ", "BE"])]
        rb = b[(b.symbol == e["symbol"]) & b.series.isin(["EQ", "BE"])]
        if ra.empty or rb.empty:
            continue
        ra, rb = ra.iloc[0], rb.iloc[0]
        rows.append({"symbol": e["symbol"], "ex_date": e["date"].date(), "fmt": "UDiFF" if e["date"] >= UDIFF else "old",
                     "close_prev_day": ra["close"], "prevclose_on_exdate": rb["prevclose"], "close_exdate": rb["close"],
                     "prevclose/close_prev": round(rb["prevclose"] / ra["close"], 4), "true_ratio(Yahoo-implied)": e["adj_factor"],
                     "isin_prev": ra["isin"], "isin_exdate": rb["isin"], "isin_changed": ra["isin"] != rb["isin"]})
        print(rows[-1], flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    if len(df):
        unadj = (df["prevclose/close_prev"].between(0.98, 1.02)).sum()
        print(f"\nPREVCLOSE on the ex-date equals the RAW prior close in {unadj}/{len(df)} sampled actions "
              f"(an adjusted PREVCLOSE would equal the split factor).")


if __name__ == "__main__":
    main()
