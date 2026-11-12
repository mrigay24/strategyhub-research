"""
Group map v2 (verified against filings), built from v1 plus documented changes only.

Inputs (results/group_dependency/):
  group_map.csv                 v1 (the registered map)
  verify/p1_history.csv         priority-1 symbols checked at their event dates
                                (Sonnet subagent, documentary sources; spot-checked)
  shp_check.csv                 filing-based consistency check, 2020/21 onward
                                (group_dependency_verify.py)
  verify/decisions.csv          reviewed changes: symbol, action (relabel | split | note),
                                group, group_type, start, end, reason, source_url, filing_date

Output:
  group_map_v2.csv              v1 columns + source_url, filing_date, verified, verified_scope, notes_v2
  group_map_v2_changes.csv      one row per changed field, v1 -> v2, with the reason

`verified`: yes / changed / unverifiable / not checked.
`confidence` in v2 = "high" where a document supports the label for the dates that
matter (event dates for priority 1, the filing period otherwise); checked rows with no
supporting document drop "high" to "medium"; rows not checked keep their v1 confidence.

Run:  ~/.venvs/strategyhub/bin/python scripts/group_dependency_build_map_v2.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "group_dependency"
V = OUT / "verify"
END = pd.Timestamp("2025-06-30")


def main() -> None:
    v1 = pd.read_csv(OUT / "group_map.csv", dtype=str).fillna("")
    hist = pd.read_csv(V / "p1_history.csv", dtype=str).fillna("").drop_duplicates("symbol").set_index("symbol")
    chk = pd.read_csv(OUT / "shp_check.csv", dtype=str).fillna("").drop_duplicates("symbol").set_index("symbol")
    dec = pd.read_csv(V / "decisions.csv", dtype=str).fillna("") if (V / "decisions.csv").exists() \
        else pd.DataFrame(columns=["symbol", "action", "group", "group_type", "start", "end", "reason",
                                   "source_url", "filing_date"])
    m = v1.copy()
    for c in ["source_url", "filing_date", "verified", "verified_scope", "notes_v2"]:
        m[c] = ""
    m["verified"] = "not checked"
    m["weak"] = False
    changes = []

    # 1) filing evidence (2020/21 onward)
    for i, r in m.iterrows():
        s = r["symbol"]
        if s in chk.index and chk.at[s, "check"] not in ("", "no filing"):
            c = chk.loc[s]
            m.at[i, "source_url"] = c["xbrl_latest"]
            m.at[i, "filing_date"] = c["latest_filing"]
            ok = c["check"].startswith("consistent") or c["check"].startswith("no group link")
            m.at[i, "verified"] = "yes" if ok else "unverifiable"
            m.at[i, "verified_scope"] = f"filings {c['earliest_filing']}..{c['latest_filing']}"
            m.at[i, "notes_v2"] = f"NSE SHP: {c['check']}; promoters: {c['top_promoters_latest'][:160]}"
        elif s in chk.index:
            m.at[i, "verified"] = "unverifiable"
            m.at[i, "verified_scope"] = "no NSE filing in the 2020+ window"
    # 2) priority-1 history at event dates (overrides the filing status for those rows)
    for i, r in m.iterrows():
        s = r["symbol"]
        if s in hist.index:
            h = hist.loc[s]
            m.at[i, "verified"] = h["verified"] if h["verified"] in ("yes", "changed", "unverifiable") else "unverifiable"
            m.at[i, "verified_scope"] = "event dates" + (f" (+ {m.at[i, 'verified_scope']})" if m.at[i, "verified_scope"] else "")
            if h["source_url"]:
                m.at[i, "source_url"] = h["source_url"]
                m.at[i, "filing_date"] = h["evidence_date"]
            filing_ok = s in chk.index and chk.at[s, "check"].startswith(("consistent", "no group link"))
            if h["verified"] == "yes" and h["source_type"] == "wikipedia" and not filing_ok:
                m.at[i, "weak"] = True     # undated group list only
            m.at[i, "notes_v2"] = (f"history [{h['source_type']}]: {h['notes']}" + (" | " + m.at[i, "notes_v2"] if m.at[i, "notes_v2"] else ""))[:400]
    # 3) reviewed decisions (relabel a whole symbol, or split its period)
    for _, d in dec.iterrows():
        rows = m.index[m["symbol"] == d["symbol"]]
        if d["action"] == "relabel":
            for i in rows:
                for col in ["group", "group_type"]:
                    if d[col] and m.at[i, col] != d[col]:
                        changes.append({"symbol": d["symbol"], "field": col, "v1": m.at[i, col], "v2": d[col],
                                        "period": f"{m.at[i, 'start']}..{m.at[i, 'end']}", "reason": d["reason"],
                                        "source_url": d["source_url"]})
                        m.at[i, col] = d[col]
                m.at[i, "verified"] = "changed"
                m.at[i, "source_url"], m.at[i, "filing_date"] = d["source_url"], d["filing_date"]
                m.at[i, "notes_v2"] = ("decision: " + d["reason"] + " | " + m.at[i, "notes_v2"])[:400]
        elif d["action"] == "split":
            # new control period [start, end] for this symbol: clip existing rows, add one row
            ds, de = pd.Timestamp(d["start"]), pd.Timestamp(d["end"] or END)
            base = m.loc[rows].copy()
            keep = []
            for i in rows:
                a_, b_ = pd.Timestamp(m.at[i, "start"]), pd.Timestamp(m.at[i, "end"])
                if b_ < ds or a_ > de:
                    keep.append(m.loc[i].to_dict())
                    continue
                if a_ < ds:
                    x = m.loc[i].to_dict(); x["end"] = str((ds - pd.Timedelta(days=1)).date()); keep.append(x)
                if b_ > de:
                    x = m.loc[i].to_dict(); x["start"] = str((de + pd.Timedelta(days=1)).date()); keep.append(x)
            new = base.iloc[0].to_dict()
            new.update({"group": d["group"], "group_type": d["group_type"], "start": str(ds.date()),
                        "end": str(de.date()), "verified": "changed", "source_url": d["source_url"],
                        "filing_date": d["filing_date"], "confidence": "high",
                        "notes_v2": "decision: " + d["reason"]})
            changes.append({"symbol": d["symbol"], "field": "group (period)", "v1": "; ".join(
                f"{x['group']} {x['start']}..{x['end']}" for x in base.to_dict('records')),
                "v2": f"{d['group']} {new['start']}..{new['end']}", "period": f"{new['start']}..{new['end']}",
                "reason": d["reason"], "source_url": d["source_url"]})
            m = pd.concat([m.drop(index=rows), pd.DataFrame(keep + [new])], ignore_index=True)
        elif d["action"] == "confirm":
            for i in rows:
                if m.at[i, "verified"] in ("unverifiable", "not checked") and m.at[i, "source_url"]:
                    m.at[i, "verified"] = "yes"
                m.at[i, "notes_v2"] = ("reviewed: " + d["reason"] + " | " + m.at[i, "notes_v2"])[:400]
        elif d["action"] == "note":
            for i in rows:
                m.at[i, "notes_v2"] = ("decision: " + d["reason"] + " | " + m.at[i, "notes_v2"])[:400]
    # 4) confidence in v2
    for i, r in m.iterrows():
        old = r["confidence"]
        if r["verified"] in ("yes", "changed") and r["source_url"] and not r["weak"]:
            new = "high"
        elif r["weak"]:
            new = "medium" if old in ("high", "medium") else old
        elif r["verified"] == "unverifiable":
            new = "medium" if old == "high" else old
        else:
            new = old
        if new != old:
            changes.append({"symbol": r["symbol"], "field": "confidence", "v1": old, "v2": new,
                            "period": f"{r['start']}..{r['end']}", "reason": f"verified={r['verified']}",
                            "source_url": r["source_url"]})
            m.at[i, "confidence"] = new
    m["verified_scope"] = [v + (" [undated group list only]" if w else "") for v, w in zip(m["verified_scope"], m["weak"])]
    m = m.drop(columns="weak").sort_values(["symbol", "start"]).reset_index(drop=True)
    m.to_csv(OUT / "group_map_v2.csv", index=False)
    ch = pd.DataFrame(changes)
    ch.to_csv(OUT / "group_map_v2_changes.csv", index=False)
    per_sym = m.groupby("symbol")["verified"].agg(lambda x: "changed" if (x == "changed").any() else
                                                  ("yes" if (x == "yes").all() else
                                                   ("unverifiable" if (x == "unverifiable").any() else "not checked")))
    print("symbols by status:", per_sym.value_counts().to_dict())
    print("changed fields:", ch["field"].value_counts().to_dict() if len(ch) else {})
    g = ch[ch["field"].str.startswith("group")] if len(ch) else ch
    print(f"group-label changes: {len(g)} rows, {g['symbol'].nunique() if len(g) else 0} symbols")


if __name__ == "__main__":
    main()
