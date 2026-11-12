"""
Merge the labeller's four parts into results/group_dependency/group_map.csv (Phase 2).

Inputs: results/group_dependency/map_raw/map_part{1..4}.csv and groups.csv, written by a
Sonnet subagent following GROUP_MAP_README.md (11 Nov 2026), from NSE's public symbol
lists plus its own knowledge and a few web searches.

This script applies only the fixes listed in FIXES (each found in our spot checks, all
before any return was computed) and makes `same_company_as` symmetric. No returns are read.

Run:  ~/.venvs/strategyhub/bin/python scripts/group_dependency_build_map.py
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "group_dependency"
RAW = OUT / "map_raw"
JK = "JK Organisation (Hari Shankar Singhania family)"

# (symbol, column, new value, reason)
FIXES = [
    ("RELIGARE", "industry", "Finance - NBFC & Housing Finance",
     "one industry per symbol; Religare Finvest (NBFC lending) was the largest business"),
    ("NAM-INDIA", "same_company_as", "",
     "ITBEES is a Nippon India ETF, not the AMC (a name-list artefact)"),
    ("JKPAPER", "group", JK, "JK Paper, JK Lakshmi Cement and JK Tyre are all JK Organisation "
     "(Hari Shankar Singhania's family; his sons chair different firms)"),
    ("JKLAKSHMI", "group", JK, "same"),
    ("JKTYRE", "group", JK, "same"),
    ("JKINDUSTRY", "group", JK, "same; JK Industries is JK Tyre's former name"),
    ("JKINDUSTRY", "same_company_as", "JKTYRE", "JK Industries was renamed JK Tyre & Industries (2008)"),
    ("MEGH", "group", "Meghmani (Patel family)", "old Meghmani Organics symbol; same family as MOL/EPIGRAL"),
    ("MEGH", "group_type", "Family", "same"),
    ("MEGH", "confidence", "medium", "same"),
]


# same-company links that are wrong: separate companies that later merged (they traded at
# the same time, so they are siblings, not one company)
UNLINK = [
    ("TATAINFOTE", "TCS", "Tata Infotech was a separate listed company until it merged into TCS (2006)"),
    ("INDSWFTLAB", "INDSWFTLTD", "Ind-Swift Labs and Ind-Swift Ltd are separate companies"),
    ("NETWORK18", "TV-18", "Television Eighteen merged into Network18 in 2011; separate before"),
    ("NETWORK18", "TV18", "same"),
]


def norm_name(s: str) -> str:
    s = s.lower().replace("&", "and")
    s = re.sub(r"\b(limited|ltd|the|india|company|co)\b", " ", s)
    return re.sub(r"[^a-z0-9]", "", s)


def main() -> None:
    m = pd.concat([pd.read_csv(RAW / f"map_part{i}.csv", dtype=str) for i in range(1, 5)])
    m = m.fillna("").reset_index(drop=True)
    for sym, col, val, _ in FIXES:
        hit = m["symbol"] == sym
        assert hit.any(), sym
        m.loc[hit, col] = val
    # symmetric same-company links, plus identical company names
    links: dict[str, set] = {}
    for s, o in zip(m["symbol"], m["same_company_as"]):
        for x in [t for t in re.split(r"[;\s,]+", o) if t]:
            links.setdefault(s, set()).add(x)
            links.setdefault(x, set()).add(s)
    names = m.drop_duplicates("symbol").set_index("symbol")["company_name"]
    etf = set(m.loc[m["group"] == "ETF (not a company)", "symbol"])
    by_name: dict[str, list] = {}
    for s, n in names.items():
        if n and s not in etf:
            by_name.setdefault(norm_name(n), []).append(s)
    n_auto = 0
    for k, ss in by_name.items():
        if len(ss) > 1 and k:
            for a in ss:
                for b in ss:
                    if a != b and b not in links.get(a, set()):
                        links.setdefault(a, set()).add(b)
                        n_auto += 1
    for a, b, why in UNLINK:
        links.get(a, set()).discard(b)
        links.get(b, set()).discard(a)
    m["same_company_as"] = m["symbol"].map(lambda s: ";".join(sorted(links.get(s, set()))))
    m = m.sort_values(["symbol", "start"]).reset_index(drop=True)
    m.to_csv(OUT / "group_map.csv", index=False)

    # diagnostics: do any same-company symbols trade at the same time? (dates only)
    u = pd.read_csv(OUT / "universe.csv", parse_dates=["first_trade", "last_trade"]).set_index("symbol")
    over = []
    for a, bs in links.items():
        for b in bs:
            if a < b and a in u.index and b in u.index:
                lo = max(u.at[a, "first_trade"], u.at[b, "first_trade"])
                hi = min(u.at[a, "last_trade"], u.at[b, "last_trade"])
                if (hi - lo).days > 5:
                    over.append((a, b, lo.date(), hi.date()))
    main_ = m[m["group_type"].isin(["Family", "Corporate"])]
    # distinct companies per group: collapse same-company symbols
    comp = {}
    for s in names.index:
        comp[s] = min({s} | links.get(s, set()))
    main_ = main_.assign(company=main_["symbol"].map(comp))
    gsize = main_.groupby("group")["company"].nunique()
    print(f"group_map.csv: {len(m)} rows, {m['symbol'].nunique()} symbols; "
          f"{len(FIXES)} fixes; {n_auto} same-company links added from identical names")
    print("types:", m["group_type"].value_counts().to_dict())
    print("confidence:", m["confidence"].value_counts().to_dict())
    print(f"Family/Corporate groups with >= 2 distinct companies: {(gsize >= 2).sum()} "
          f"({int(gsize[gsize >= 2].sum())} companies)")
    print("same-company symbols that trade at the same time (excluded from pairing):", over)
    pd.read_csv(RAW / "groups.csv", dtype=str).to_csv(OUT / "groups.csv", index=False)
    with open(OUT / "group_map_fixes.csv", "w") as f:
        fx = pd.DataFrame(FIXES, columns=["symbol", "column", "new_value", "reason"])
        ul = pd.DataFrame([(a, "same_company_as", f"remove link to {b}", w) for a, b, w in UNLINK],
                          columns=fx.columns)
        pd.concat([fx, ul]).to_csv(f, index=False)


if __name__ == "__main__":
    main()
