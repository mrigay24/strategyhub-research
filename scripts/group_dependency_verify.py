"""
Group map v2, step 1: filing-based consistency check (offline, from the fetch cache).

For every symbol in the verification list, read its cached NSE shareholding-pattern
filings (2020/21 onward; see group_dependency_fetch_shp.py), extract the promoter and
promoter-group names, and ask:
  * does the firm share at least one promoter entity name with another member of its v1
    group (as of the filing date)?  -> "consistent"
  * does it share names with a different multi-company group instead?   -> "conflict"
  * a firm outside any multi-company group that shares >= 2 promoter names with one ->
    "possible missed member"
  * no filing in NSE's window -> "no filing"
Names are normalised (case, punctuation, honorifics, Pvt/Private, Ltd/Limited).
The flags are evidence for review, not verdicts.

Run:  ~/.venvs/strategyhub/bin/python scripts/group_dependency_verify.py --symbols <csv> \
          --cache <dir> --symchange <symbolchange.csv> [--event-dates <csv>]
Output: results/group_dependency/shp_promoters.csv, shp_check.csv
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
from group_dependency_fetch_shp import current_symbol_map, parse_xbrl, qdate  # noqa: E402

OUT = ROOT / "results" / "group_dependency"
MAIN = {"Family", "Corporate"}
HONOR = r"\b(SMT|SHRI|SRI|MR|MRS|MS|DR|KUMARI|LATE|M/S)\b"


def norm(n: str) -> str:
    n = n.upper().replace("&", " AND ")
    n = re.sub(r"\bPRIVATE\b", "PVT", n)
    n = re.sub(r"\bLIMITED\b", "LTD", n)
    n = re.sub(HONOR, " ", n)
    n = re.sub(r"[^A-Z0-9 ]", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--symchange", required=True)
    ap.add_argument("--event-dates", default="")
    a = ap.parse_args()
    cache = Path(a.cache)
    follow = current_symbol_map(a.symchange)
    vs = pd.read_csv(a.symbols)
    evd = {}
    if a.event_dates:
        e = pd.read_csv(a.event_dates)
        for s_, d_ in zip(e["symbol"], e["date"]):
            evd.setdefault(s_, set()).add(pd.Timestamp(d_))
    prows = []
    for sym, pri in zip(vs["symbol"], vs["priority"]):
        q = follow(sym)
        lj = cache / f"list_{q}.json"
        if not lj.exists():
            continue
        rows = [r for r in json.loads(lj.read_text()) if r.get("xbrl") and pd.notna(qdate(r.get("date", "")))]
        rows = sorted(rows, key=lambda r: qdate(r["date"]))
        for j, r in enumerate(rows):
            fx = cache / r["xbrl"].rsplit("/", 1)[-1]
            if not fx.exists():
                continue
            which = "earliest" if j == 0 else ("latest" if j == len(rows) - 1 else "near_event")
            for p in parse_xbrl(fx.read_text()):
                prows.append({"symbol": sym, "priority": pri, "query_symbol": q,
                              "filing_date": qdate(r["date"]).date(), "which": which,
                              "xbrl": r["xbrl"], "name": p["name"], "pct": p["pct"]})
    pr = pd.DataFrame(prows)
    pr["norm"] = pr["name"].map(norm)
    pr.drop(columns="norm").to_csv(OUT / "shp_promoters.csv", index=False)
    listed = {s: (cache / f"list_{follow(s)}.json").exists() for s in vs["symbol"]}

    gm = pd.read_csv(OUT / "group_map.csv", dtype=str).fillna("")
    gm["start"], gm["end"] = pd.to_datetime(gm["start"]), pd.to_datetime(gm["end"])

    def group_at(s, d):
        d = min(d, pd.Timestamp("2025-06-30"))      # the map ends with the price panel
        m = gm[(gm["symbol"] == s) & (gm["start"] <= d) & (gm["end"] >= d)]
        return (m["group"].iloc[0], m["group_type"].iloc[0]) if len(m) else ("", "")

    # names per symbol (all parsed filings) and the v1 group at each filing date
    pr["filing_date"] = pd.to_datetime(pr["filing_date"])
    labs = {}
    for (s, d), _ in pr.groupby(["symbol", "filing_date"]):
        labs[(s, d)] = group_at(s, d)
    pr["v1_group"] = [labs[(s, d)][0] for s, d in zip(pr["symbol"], pr["filing_date"])]
    pr["v1_type"] = [labs[(s, d)][1] for s, d in zip(pr["symbol"], pr["filing_date"])]
    names_of = pr.groupby("symbol")["norm"].apply(set).to_dict()
    cname = gm.drop_duplicates("symbol").set_index("symbol")["company_name"].map(norm).to_dict()
    gsets = {}
    for g, sub in pr[pr["v1_type"].isin(MAIN)].groupby("v1_group"):
        gsets[g] = sub.groupby("symbol")["norm"].apply(set).to_dict()
    # every v1 member's own company name also identifies the group (a sibling as promoter)
    for g, sub in gm[gm["group_type"].isin(MAIN)].groupby("group"):
        for m in sub["symbol"].unique():
            gsets.setdefault(g, {}).setdefault(m, set()).add(cname.get(m, m))
    multi = {g for g, d in gsets.items() if len(d) >= 2}
    # possible new groups: symbols outside multi-company groups sharing >= 2 promoter names
    lone = [s_ for s_ in names_of if not any(s_ in gsets[g] for g in multi)]
    newpairs = []
    for i, a_ in enumerate(lone):
        for b_ in lone[i + 1:]:
            sh = names_of[a_] & names_of[b_]
            if len(sh) >= 2 or cname.get(a_) in names_of[b_] or cname.get(b_) in names_of[a_]:
                newpairs.append({"a": a_, "b": b_, "shared": "; ".join(sorted(sh))[:300]})
    pd.DataFrame(newpairs).to_csv(OUT / "shp_possible_new_groups.csv", index=False)
    print(f"possible new-group pairs among non-group symbols: {len(newpairs)}")

    out = []
    for s, pri in zip(vs["symbol"], vs["priority"]):
        sub = pr[pr["symbol"] == s]
        if sub.empty:
            out.append({"symbol": s, "priority": pri, "check": "no filing" if not listed[s] or True else "",
                        "listed_on_nse_api": listed[s]})
            continue
        latest = sub[sub["filing_date"] == sub["filing_date"].max()]
        earliest = sub[sub["filing_date"] == sub["filing_date"].min()]
        g_l, t_l = latest["v1_group"].iloc[0], latest["v1_type"].iloc[0]
        mine = names_of[s]
        ov = {}
        for g, members in gsets.items():
            others = set().union(*[v for k, v in members.items() if k != s]) if len(members) > 1 or s not in members else set()
            ov[g] = len(mine & others)
        best = max(ov, key=ov.get) if ov else ""
        own = ov.get(g_l, 0)
        if t_l in MAIN and g_l in multi:
            if own >= 1 and own >= ov.get(best, 0):
                chk = "consistent"
            elif ov.get(best, 0) >= 1:
                chk = f"conflict: shares {ov[best]} names with {best}, {own} with own group"
            else:
                chk = "no shared promoter name with own group"
        else:
            chk = (f"possible missed member of {best} ({ov[best]} shared names)"
                   if best and ov.get(best, 0) >= 2 and best != g_l else "no group link (standalone ok)")
        top = lambda t: "; ".join(t.sort_values("pct", ascending=False)["name"].head(6))
        out.append({"symbol": s, "priority": pri, "check": chk, "listed_on_nse_api": True,
                    "v1_group_latest": g_l, "v1_type_latest": t_l,
                    "earliest_filing": str(earliest["filing_date"].iloc[0].date()),
                    "latest_filing": str(latest["filing_date"].iloc[0].date()),
                    "promoter_pct_latest": round(latest["pct"].sum(), 2),
                    "top_promoters_earliest": top(earliest), "top_promoters_latest": top(latest),
                    "xbrl_latest": latest["xbrl"].iloc[0]})
    ck = pd.DataFrame(out)
    ck.to_csv(OUT / "shp_check.csv", index=False)
    print(ck["check"].str.split(":").str[0].str.replace(r" \(.*", "", regex=True).value_counts().to_string())


if __name__ == "__main__":
    main()
