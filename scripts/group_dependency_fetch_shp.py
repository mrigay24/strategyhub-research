"""
Fetch promoter and promoter-group names from NSE shareholding-pattern filings (XBRL),
to verify the group map (group map v2, Nov 2026).

Source: NSE's public API `corporate-share-holdings-master` (about the last 20-25
quarters, i.e. 2020/21 onward) and the XBRL file each filing links to on
nsearchives.nseindia.com. Polite: one request at a time with a pause. Raw XBRL is cached
outside the repo; only the parsed promoter names are written to results/.

For each symbol: map it to its current NSE symbol (NSE's symbolchange list), list its
filings, and parse the EARLIEST and LATEST quarter-end filings, plus, for symbols in
`--event-dates`, the filing nearest each event date when one exists.

Run:  ~/.venvs/strategyhub/bin/python scripts/group_dependency_fetch_shp.py \
          --symbols <csv with column symbol> --cache <dir> --symchange <symbolchange.csv>
Output: results/group_dependency/shp_filings.csv (one row per symbol x filing listed),
        results/group_dependency/shp_promoters.csv (one row per promoter name parsed)
"""
from __future__ import annotations

import argparse
import json
import re
import time
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
import requests  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "group_dependency"
API = "https://www.nseindia.com/api/corporate-share-holdings-master"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
PAUSE = 0.9
# axes of Table II (promoter and promoter group); used only when a file has no
# TypeOfPromoterShareholding tags
PROMOTER_AXES = ("IndividualsOrHUF", "CentralGovernmentStateGovernment", "FinancialInstitutionsBanks",
                 "OthersIndianShareholders", "IndividualsNonResidentIndividualsOrForeignIndividuals",
                 "OthersForeignShareholders", "Government", "ForeignPortfolioInvestor", "Institutions",
                 "BodiesCorporate", "AnyOther")
PUBLIC_MARK = ("InstitutionsForeignPortfolioInvestor", "MutualFund", "InsuranceCompan", "NonInstitution",
               "IndividualShareholders", "Institutions(Domestic)", "InstitutionsDomestic",
               "InstitutionsForeign", "AlternativeInvestment", "ProvidentFund", "SovereignWealth",
               "ForeignDirectInvestment", "NBFC", "IEPF", "Trusts", "ClearingMember", "Directors",
               "KeyManagerial", "Relatives", "NonResidentIndians", "ForeignNationals",
               "ForeignCompanies", "BodiesCorporateNonInstitution", "PublicShareholder", "Employee")


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "application/json, text/plain, */*",
                      "Accept-Language": "en-US,en;q=0.9", "Referer": "https://www.nseindia.com/"})
    try:
        s.get("https://www.nseindia.com", timeout=20)
    except Exception:
        pass
    return s


def current_symbol_map(symchange_csv: str) -> dict:
    sc = pd.read_csv(symchange_csv, encoding="latin1", dtype=str)
    sc.columns = [c.strip() for c in sc.columns]
    sc["d"] = pd.to_datetime(sc["EFFECTIVE DATE"], format="%d-%b-%Y", errors="coerce")
    nxt = {}
    for _, r in sc.sort_values("d").iterrows():
        nxt[r["OLD SYMBOL"].strip()] = r["NEW SYMBOL"].strip()

    def follow(s):
        seen = set()
        while s in nxt and s not in seen:
            seen.add(s)
            s = nxt[s]
        return s
    return follow


def list_filings(s, sym: str) -> list[dict]:
    for attempt in range(3):
        try:
            r = s.get(API, params={"index": "equities", "symbol": sym}, timeout=30)
            if r.status_code == 200:
                js = r.json()
                return js if isinstance(js, list) else js.get("data", [])
            time.sleep(5 * (attempt + 1))
        except Exception:
            time.sleep(5 * (attempt + 1))
    return []


def parse_xbrl(x: str) -> list[dict]:
    names = re.findall(r"<in-bse-shp:NameOfTheShareholder[^>]*contextRef=\"([^\"]+)\"[^>]*>([^<]+)<", x)
    prom_ctx = set(re.findall(r"<in-bse-shp:TypeOfPromoterShareholding[^>]*contextRef=\"([^\"]+)\"", x))
    pct = {}
    for c, v in re.findall(r"<in-bse-shp:ShareholdingAsAPercentageOfTotalNumberOfShares[^>]*contextRef=\"([^\"]+)\"[^>]*>([^<]+)<", x):
        try:
            pct[c] = float(v)
        except ValueError:
            pass
    scale = 100.0 if pct and max(pct.values()) <= 1.0 else 1.0   # fractions vs percent, per file
    out = []
    for c, n in names:
        if prom_ctx:
            is_prom = c in prom_ctx
        else:
            is_prom = any(a in c for a in PROMOTER_AXES) and not any(p in c for p in PUBLIC_MARK)
        if not is_prom:
            continue
        cands = [c, c[2:] if c.startswith("D_") else c, c[:-1] + "I" if c.endswith("D") else c]
        p = next((pct[k] for k in cands if k in pct), None)
        p = p * scale if p is not None else p
        out.append({"name": n.strip(), "context": c, "pct": p})
    return out


def qdate(s: str):
    return pd.to_datetime(s, format="%d-%b-%Y", errors="coerce")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--symchange", required=True)
    ap.add_argument("--event-dates", default="")
    ap.add_argument("--latest-only", action="store_true", help="parse only the latest filing")
    ap.add_argument("--tag", default="", help="suffix for the output file names")
    a = ap.parse_args()
    cache = Path(a.cache)
    cache.mkdir(parents=True, exist_ok=True)
    follow = current_symbol_map(a.symchange)
    syms = pd.read_csv(a.symbols)["symbol"].tolist()
    evd = {}
    if a.event_dates:
        e = pd.read_csv(a.event_dates)
        for s_, d_ in zip(e["symbol"], e["date"]):
            evd.setdefault(s_, set()).add(pd.Timestamp(d_))
    s = session()
    frows, prows = [], []
    for k, sym in enumerate(syms):
        q = follow(sym)
        lj = cache / f"list_{q}.json"
        if lj.exists():
            rows = json.loads(lj.read_text())
        else:
            rows = list_filings(s, q)
            lj.write_text(json.dumps(rows))
            time.sleep(PAUSE)
        rows = [r for r in rows if r.get("xbrl") and pd.notna(qdate(r.get("date", "")))]
        for r in rows:
            frows.append({"symbol": sym, "query_symbol": q, "date": qdate(r["date"]).date(),
                          "promoter_pct": r.get("pr_and_prgrp"), "company": r.get("name"),
                          "isin": r.get("isin"), "xbrl": r["xbrl"]})
        if not rows:
            continue
        rows = sorted(rows, key=lambda r: qdate(r["date"]))
        pick = {len(rows) - 1} if a.latest_only else {0, len(rows) - 1}
        for d in evd.get(sym, set()):
            j = min(range(len(rows)), key=lambda i: abs((qdate(rows[i]["date"]) - d).days))
            if abs((qdate(rows[j]["date"]) - d).days) <= 120:
                pick.add(j)
        for j in sorted(pick):
            r = rows[j]
            fx = cache / (r["xbrl"].rsplit("/", 1)[-1])
            if not fx.exists():
                try:
                    x = s.get(r["xbrl"], timeout=60).text
                    fx.write_text(x)
                except Exception:
                    continue
                time.sleep(PAUSE)
            for p in parse_xbrl(fx.read_text()):
                prows.append({"symbol": sym, "query_symbol": q, "filing_date": qdate(r["date"]).date(),
                              "which": "earliest" if j == 0 else ("latest" if j == len(rows) - 1 else "near_event"),
                              "xbrl": r["xbrl"], **p})
        if k % 25 == 0:
            print(f"{k}/{len(syms)} {sym}->{q}: {len(rows)} filings", flush=True)
    pd.DataFrame(frows).to_csv(OUT / f"shp_filings{a.tag}.csv", index=False)
    pd.DataFrame(prows).to_csv(OUT / f"shp_promoters{a.tag}.csv", index=False)
    print(f"done: {len(syms)} symbols, {len(frows)} filings listed, {len(prows)} promoter-name rows")


if __name__ == "__main__":
    main()
