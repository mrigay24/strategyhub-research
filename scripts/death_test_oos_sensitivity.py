"""
NOT PRE-REGISTERED sensitivity check for the out-of-sample death test (2026-11-11).

Promised in PREREGISTRATION §9a and written AFTER the pre-registered run
(`death_test_oos.py run`) had produced results/death_test_oos/outcomes.csv.

Rule: two cases form an overlapping pair if they are in the same market, one failed
firm is in the other's rival set (either direction), and their day 0s are within 20
trading days of each other. For every such pair the LATER case is dropped (same day:
the one listed later in the case file). The pre-registered §7-§8 analysis is then re-run
on what is left, for both versions (registered, full_population).

Why: overlapping cases count the same rival move twice (e.g. Regions on 20 Jan 2009
and Fifth Third on 22 Jan 2009 are each in the other's rival set).

Run:  ~/.venvs/strategyhub/bin/python scripts/death_test_oos_sensitivity.py
Output: results/death_test_oos/sensitivity_overlap.json and sensitivity_overlap.log
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from death_test_oos import CASE_FILE, OUT, analyze  # noqa: E402

CAL = {"India": ROOT / "data_processed" / "nse_survivorship_free_adj.parquet",
       "US": ROOT / "data_processed" / "extended_prices.parquet"}
GAP = 20


def calendar(path: Path) -> pd.DatetimeIndex:
    d = pq.read_table(path, columns=["date"]).column("date").to_pandas()
    return pd.DatetimeIndex(pd.to_datetime(d).unique()).sort_values()


def main() -> None:
    cases = pd.read_csv(CASE_FILE, dtype=str).fillna("")
    cases["order"] = np.arange(len(cases))
    out = pd.read_csv(OUT / "outcomes.csv")
    lines = ["NOT PRE-REGISTERED: drop the later case of each overlapping rival pair "
             f"(day 0 within {GAP} trading days)."]
    drop: set = set()
    for market, g in cases[cases["status"] == "case"].groupby("market"):
        cal = calendar(CAL[market])
        pos = {r.case_id: int(cal.searchsorted(pd.Timestamp(r.day0))) for r in g.itertuples()}
        rows = list(g.itertuples())
        for i, a in enumerate(rows):
            for b in rows[i + 1:]:
                linked = (b.symbol in a.rivals.split()) or (a.symbol in b.rivals.split())
                gap = abs(pos[a.case_id] - pos[b.case_id])
                if not linked or gap > GAP:
                    continue
                later = max((a, b), key=lambda r: (pos[r.case_id], r.order))
                mutual = (b.symbol in a.rivals.split()) and (a.symbol in b.rivals.split())
                drop.add(later.case_id)
                lines.append(f"  pair {a.case_id} / {b.case_id}: {gap} trading days apart, "
                             f"{'mutual' if mutual else 'one-way'} rivals -> drop {later.case_id}")
    lines.append(f"Dropped: {sorted(drop)}")
    kept = out[~out["case_id"].isin(drop)]
    res = {"rule": lines[0], "dropped": sorted(drop)}
    for name, keep in [("registered", kept["sample"] == "registered"),
                       ("full_population", kept["sample"].isin(["registered", "extension"]))]:
        res[name] = analyze(kept[keep])
        t = res[name]["T1_T2"]
        lines.append(f"{name}: n={t['n']} (SD {t['n_SD']}, OR {t['n_OR']}); mean SD {t['mean_SD']:.4f}, "
                     f"mean OR {t['mean_OR']:.4f}; hit SD {t['hit_rate_SD']:.3f}, OR {t['hit_rate_OR']:.3f}; "
                     f"perm p {t.get('perm_p', 'n/a')}; verdict {res[name]['verdict_H1']}; "
                     f"T3 {res[name]['T3_meaning']}")
    with open(OUT / "sensitivity_overlap.json", "w") as f:
        json.dump(res, f, indent=2, default=float)
    (OUT / "sensitivity_overlap.log").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
