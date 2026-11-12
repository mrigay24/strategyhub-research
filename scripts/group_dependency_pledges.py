"""
Promoter shares pledged, from the shareholding-pattern XBRL filings already cached for the
group-map check (no extra fetching, no analysis). Saved for later work on "fragile groups".

For each cached filing: the promoter-and-promoter-group total context
(ShareholdingOfPromoterAndPromoterGroup...I) gives the promoters' share count and the number
of those shares pledged (NumberOfSharesEncumberedUnderPledged, or the older
...PledgedOrOtherwiseEncumbered element). pledged_pct_of_promoter = pledged / promoter shares.
promoter_holding_pct is NSE's own field from the filing list.

Run:  ~/.venvs/strategyhub/bin/python scripts/group_dependency_pledges.py --cache <dir> --symchange <csv> --symbols <csv>
Output: results/group_dependency/promoter_pledges.csv
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from group_dependency_fetch_shp import current_symbol_map, qdate  # noqa: E402

OUT = ROOT / "results" / "group_dependency"


def pledge(x: str):
    ctx = re.findall(r'<xbrli:context id="(ShareholdingOfPromoterAndPromoterGroup[A-Za-z_]*I)"', x)
    for c in ctx:
        sh = re.search(rf'<in-bse-shp:NumberOfShares contextRef="{c}"[^>]*>([^<]+)<', x)
        pl = re.search(rf'<in-bse-shp:NumberOf[A-Za-z]*(?:Pledg|Encumbered)[A-Za-z]* contextRef="{c}"[^>]*>([^<]+)<', x)
        if sh:
            try:
                s, p = float(sh.group(1)), float(pl.group(1)) if pl else float("nan")
            except ValueError:
                continue
            return s, p
    return None, None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--symchange", required=True)
    ap.add_argument("--symbols", required=True)
    a = ap.parse_args()
    cache, follow = Path(a.cache), current_symbol_map(a.symchange)
    rows = []
    for sym in pd.read_csv(a.symbols)["symbol"]:
        lj = cache / f"list_{follow(sym)}.json"
        if not lj.exists():
            continue
        for r in json.loads(lj.read_text()):
            if not r.get("xbrl"):
                continue
            fx = cache / r["xbrl"].rsplit("/", 1)[-1]
            if not fx.exists():
                continue
            s, p = pledge(fx.read_text())
            if s is None:
                continue
            d = qdate(r.get("date", ""))
            rows.append({"symbol": sym, "filing_date": d.date() if pd.notna(d) else "",
                         "promoter_holding_pct": r.get("pr_and_prgrp"),
                         "pledged_pct_of_promoter": round(100 * p / s, 4) if s and p == p else None,
                         "source_url": r["xbrl"]})
    df = pd.DataFrame(rows).drop_duplicates(["symbol", "filing_date"]).sort_values(["symbol", "filing_date"])
    df.to_csv(OUT / "promoter_pledges.csv", index=False)
    print(f"{len(df)} filings, {df['symbol'].nunique()} symbols; with a pledge figure: "
          f"{df['pledged_pct_of_promoter'].notna().sum()}")


if __name__ == "__main__":
    main()
