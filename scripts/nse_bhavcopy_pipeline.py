"""
#2 — Survivorship-bias-free NSE data pipeline (bhavcopy ingestion)
=================================================================
The existing nse_prices_clean.parquet is survivorship-BIASED: it takes TODAY's
Nifty 500 list (Wikipedia) and pulls each name's full back-history from Yahoo.
Any stock that left the index or delisted before today is simply missing, and
OHLV are faked (open/high/low=close, volume=placeholder).

This pipeline fixes that at the source by ingesting NSE BHAVCOPY — the official
daily end-of-day file that lists EVERY security that traded that day, including
names later delisted, with real OHLCV + ISIN + traded value.

Two facts that make this work (verified):
  1. NSE's Akamai wall (403 on homepage) is bypassed by a cookie handshake:
     GET the homepage (still 403, but it SETS cookies), then reuse those cookies
     + a Referer header on archives requests → 200.
  2. Corporate actions (splits/bonuses) can be back-adjusted from bhavcopy ALONE:
     on an ex-date NSE reports that day's PREVCLOSE as the ADJUSTED prior close,
     so adj_factor = PREVCLOSE_today / CLOSE_yesterday. No separate CA feed needed
     for price adjustment (dividends excluded — price-return, not total-return).

Formats (NSE changed format mid-2024):
  OLD  (< 2024-07-08): archives.nseindia.com/content/historical/EQUITIES/YYYY/MON/cmDDMONYYYYbhav.csv.zip
  UDiFF(>=2024-07-08): nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip

Usage:
    .venv/bin/python scripts/nse_bhavcopy_pipeline.py --sample        # PoC: 1 month + recent days
    .venv/bin/python scripts/nse_bhavcopy_pipeline.py --start 2005-01-01 --end 2025-06-30   # full pull
Cache: data_raw/nse_bhavcopy/<year>/  (resumable — skips already-downloaded days)
"""
from __future__ import annotations

import argparse
import io
import time
import zipfile
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data_raw" / "nse_bhavcopy"
CACHE.mkdir(parents=True, exist_ok=True)

UDIFF_CUTOVER = date(2024, 7, 8)
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def make_session() -> requests.Session:
    """Cookie handshake — the homepage 403s but still sets the cookies we need."""
    s = requests.Session()
    s.headers.update(HEADERS)
    try:
        s.get("https://www.nseindia.com/", timeout=10)
    except requests.RequestException:
        pass
    return s


def bhavcopy_url(d: date) -> tuple[str, str]:
    if d >= UDIFF_CUTOVER:
        return (f"https://nsearchives.nseindia.com/content/cm/"
                f"BhavCopy_NSE_CM_0_0_0_{d:%Y%m%d}_F_0000.csv.zip", "udiff")
    return (f"https://archives.nseindia.com/content/historical/EQUITIES/"
            f"{d.year}/{MONTHS[d.month-1]}/cm{d.day:02d}{MONTHS[d.month-1]}{d.year}bhav.csv.zip",
            "old")


def fetch_day(d: date, sess: requests.Session, retries: int = 2) -> Path | None:
    """Download + cache one day's bhavcopy zip. None = no file (holiday/weekend)."""
    if d.weekday() >= 5:
        return None
    out_dir = CACHE / str(d.year)
    out_dir.mkdir(exist_ok=True)
    dest = out_dir / f"{d:%Y%m%d}.zip"
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    url, fmt = bhavcopy_url(d)
    ref = "https://www.nseindia.com/all-reports" if fmt == "udiff" else "https://www.nseindia.com/"
    for attempt in range(retries + 1):
        try:
            r = sess.get(url, headers={"Referer": ref}, timeout=15)
        except requests.RequestException:
            time.sleep(1.0)
            continue
        if r.status_code == 200 and r.content[:2] == b"PK":   # zip magic
            dest.write_bytes(r.content)
            return dest
        if r.status_code == 404:
            return None                                       # holiday
        if r.status_code in (401, 403):                        # cookie expired
            sess.cookies.clear()
            sess.get("https://www.nseindia.com/", timeout=10)
            time.sleep(1.0)
    return None


def parse_day(path: Path, d: date) -> pd.DataFrame | None:
    """Normalize either format → [date, isin, symbol, series, open, high, low,
    close, prevclose, volume, turnover]."""
    try:
        with zipfile.ZipFile(path) as z:
            csv = z.read(z.namelist()[0])
    except (zipfile.BadZipFile, OSError):
        return None
    df = pd.read_csv(io.BytesIO(csv))
    df.columns = [c.strip() for c in df.columns]
    if "TckrSymb" in df.columns:   # UDiFF
        df = df[df["SctySrs"].astype(str).str.strip().isin(["EQ", "BE"])]
        out = pd.DataFrame({
            "isin": df["ISIN"].astype(str).str.strip(),
            "symbol": df["TckrSymb"].astype(str).str.strip(),
            "series": df["SctySrs"].astype(str).str.strip(),
            "open": df["OpnPric"], "high": df["HghPric"], "low": df["LwPric"],
            "close": df["ClsPric"], "prevclose": df["PrvsClsgPric"],
            "volume": df["TtlTradgVol"], "turnover": df["TtlTrfVal"],
        })
    else:                          # old format (ISIN absent in pre-~2007 files)
        df = df[df["SERIES"].astype(str).str.strip().isin(["EQ", "BE"])]
        sym = df["SYMBOL"].astype(str).str.strip()
        isin = df["ISIN"].astype(str).str.strip() if "ISIN" in df.columns else sym
        out = pd.DataFrame({
            "isin": isin,
            "symbol": sym,
            "series": df["SERIES"].astype(str).str.strip(),
            "open": df["OPEN"], "high": df["HIGH"], "low": df["LOW"],
            "close": df["CLOSE"], "prevclose": df["PREVCLOSE"],
            "volume": df["TOTTRDQTY"], "turnover": df["TOTTRDVAL"],
        })
    out.insert(0, "date", pd.Timestamp(d))
    return out


def daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def pull(start: date, end: date, throttle: float = 0.4) -> pd.DataFrame:
    sess = make_session()
    frames, got, miss = [], 0, 0
    for d in daterange(start, end):
        if d.weekday() >= 5:
            continue
        p = fetch_day(d, sess)
        if p is None:
            miss += 1
            continue
        df = parse_day(p, d)
        if df is not None and len(df):
            frames.append(df)
            got += 1
        time.sleep(throttle)
    print(f"  fetched {got} trading days, {miss} no-file days")
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def survivorship_report(early: pd.DataFrame, recent: pd.DataFrame):
    """The TRUE survivorship hole = names trading in the early window but GONE by
    the recent snapshot (delisted/merged/suspended). Kept distinct from "not in
    the 328-survivor subset" (which also includes recent IPOs & liquidity drops)."""
    surv_path = ROOT / "data_processed" / "nse_prices_clean.parquet"
    eq_e = early[early["series"] == "EQ"]
    early_syms = set(eq_e["symbol"].unique())
    recent_syms = set(recent[recent["series"] == "EQ"]["symbol"].unique())
    print(f"\n  EQ symbols trading in {early['date'].min().date():%Y-%m} window : {len(early_syms)}")
    print(f"  EQ symbols trading on {recent['date'].min().date()} snapshot : {len(recent_syms)}")

    gone = early_syms - recent_syms          # traded then, not now → delisted/merged
    print(f"  ★ trading then, GONE by {recent['date'].min().date()} : {len(gone)}  "
          f"← TRUE survivorship hole (delisted/merged/suspended)")
    liq = (eq_e[eq_e["symbol"].isin(gone)]
           .groupby("symbol")["turnover"].median().sort_values(ascending=False))
    liq = liq[liq > 1e7]                     # > ~1 cr/day median turnover
    print(f"  …of which LIQUID (>1cr/day median turnover)  : {len(liq)}")
    print(f"     e.g. {list(liq.head(12).index)}")

    if surv_path.exists():
        surv = set(pd.read_parquet(surv_path, columns=["symbol"])["symbol"].unique())
        gone_and_excluded = gone - surv
        print(f"  current survivor parquet has {len(surv)} names; of the {len(gone)} "
              f"delisted, {len(gone_and_excluded)} are absent from it ⇒ invisible to "
              f"the biased dataset")


def adjustment_demo(bhav: pd.DataFrame):
    """PREVCLOSE-based split/bonus adjustment-factor detection (CONTIGUOUS window
    only — needs true day-to-day continuity)."""
    print("\n  corporate-action factor detection (PREVCLOSE / prev-day CLOSE):")
    b = bhav[bhav["series"] == "EQ"].sort_values(["symbol", "date"]).copy()
    b["prev_close_lag"] = b.groupby("symbol")["close"].shift(1)
    # only trust the factor when consecutive trading days (no gap across the lag)
    b["prev_date"] = b.groupby("symbol")["date"].shift(1)
    b["gap_days"] = (b["date"] - b["prev_date"]).dt.days
    b["adj_factor"] = b["prevclose"] / b["prev_close_lag"]
    events = b[(b["gap_days"] <= 5) &
               ((b["adj_factor"] < 0.66) | (b["adj_factor"] > 1.5))].dropna(subset=["adj_factor"])
    print(f"    real split/bonus ex-dates in window       : {len(events)}")
    for _, r in events.head(8).iterrows():
        print(f"      {r['symbol']:14s} {r['date'].date()}  factor≈{r['adj_factor']:.3f}  "
              f"(prevC {r['prevclose']:.1f} vs lagC {r['prev_close_lag']:.1f})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="PoC: Jan-2015 + recent UDiFF days")
    ap.add_argument("--start", type=str)
    ap.add_argument("--end", type=str)
    a = ap.parse_args()

    print("=" * 74)
    print("NSE BHAVCOPY PIPELINE — survivorship-bias-free price ingestion")
    print("=" * 74)

    if a.sample or not (a.start and a.end):
        print("PoC: contiguous old-format month (Jan 2015) + recent UDiFF snapshot (2024-12-02)")
        early = pull(date(2015, 1, 1), date(2015, 1, 31))   # contiguous → clean adjustment
        recent = pull(date(2024, 12, 2), date(2024, 12, 2))  # snapshot → delisting check
        bhav = pd.concat([early, recent], ignore_index=True)
        if not early.empty:
            print(f"\nparsed rows: {len(bhav):,}  | days: {bhav['date'].nunique()}  | "
                  f"unique ISINs: {bhav['isin'].nunique()}  | symbols: {bhav['symbol'].nunique()}")
            survivorship_report(early, recent)
            adjustment_demo(early)        # CONTIGUOUS only
        out = ROOT / "data_raw" / "nse_bhavcopy_sample.parquet"
        if not bhav.empty:
            bhav.to_parquet(out, index=False)
            print(f"\nsaved sample → {out.relative_to(ROOT)}")
        return

    # ── full range → save the normalized long panel for the universe builder ──
    bhav = pull(date.fromisoformat(a.start), date.fromisoformat(a.end))
    if bhav.empty:
        print("\nNo data pulled (network/cookie/holiday). See logs above.")
        return
    print(f"\nparsed rows: {len(bhav):,}  | days: {bhav['date'].nunique()}  | "
          f"unique ISINs: {bhav['isin'].nunique()}  | symbols: {bhav['symbol'].nunique()}  | "
          f"{bhav['date'].min().date()} → {bhav['date'].max().date()}")
    out = ROOT / "data_raw" / "nse_bhavcopy_panel.parquet"
    bhav.to_parquet(out, index=False)
    print(f"saved panel → {out.relative_to(ROOT)}  (feed to scripts/build_nse_universe.py)")


if __name__ == "__main__":
    main()
