"""
Phase 6, "AI death test" (2026-11-11). NOT pre-registered; descriptive only.

An LLM gets the PREREGISTRATION §5 rule and the 40 out-of-sample case paragraphs, with
labels, reasoning and outcomes removed (results/ai_death_test/paragraphs_named.csv), in a
shuffled order under neutral codes. It labels each case. We compare its labels with ours
and with the rival outcomes.

  prepare : writes input_named.md (rule + shuffled paragraphs) and key.csv (code -> case)
  score   : reads labels_<version>.csv (code,label,reason) and writes scores_<version>.json

Run:  ~/.venvs/strategyhub/bin/python scripts/ai_death_test.py prepare
      ~/.venvs/strategyhub/bin/python scripts/ai_death_test.py score named
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "ai_death_test"
PREREG = ROOT / "docs" / "entropy_research" / "PREREGISTRATION.md"


def rule_text() -> str:
    lines = PREREG.read_text().splitlines()
    a = next(i for i, ln in enumerate(lines) if ln.startswith("## 5. Classification rule"))
    b = next(i for i, ln in enumerate(lines) if ln.startswith("**Who labels.**"))
    return "\n".join(lines[a:b]).strip()


def prepare() -> None:
    p = pd.read_csv(OUT / "paragraphs_named.csv")
    rng = np.random.default_rng(20261111)
    p = p.iloc[rng.permutation(len(p))].reset_index(drop=True)
    p["code"] = [f"K{i + 1:02d}" for i in range(len(p))]
    p[["code", "case_id"]].to_csv(OUT / "key.csv", index=False)
    body = "\n\n".join(f"**{c}.** {t}" for c, t in zip(p["code"], p["paragraph"]))
    (OUT / "input_named.md").write_text(
        "# Classification task\n\n## The rule\n\n" + rule_text() + "\n\n## The cases\n\n" + body + "\n")
    print(f"wrote input_named.md ({len(p)} cases) and key.csv")


def kappa(a: pd.Series, b: pd.Series) -> float:
    cats = sorted(set(a) | set(b))
    po = (a.values == b.values).mean()
    pe = sum((a == c).mean() * (b == c).mean() for c in cats)
    return float((po - pe) / (1 - pe)) if pe < 1 else float("nan")


def score(version: str) -> None:
    key = pd.read_csv(OUT / "key.csv")
    lab = pd.read_csv(OUT / f"labels_{version}.csv")
    lab["label"] = lab["label"].str.strip().str.upper().replace({"INDUSTRY SHOCK": "IND"})
    out = pd.read_csv(ROOT / "results" / "death_test_oos" / "outcomes.csv")
    out = out[(out.status == "case") & (out.peer_set == "rivals")][["case_id", "label", "bhar_0_20", "sample"]]
    d = key.merge(lab, on="code").merge(out.rename(columns={"label": "ours"}), on="case_id")
    conf = pd.crosstab(d["ours"], d["label"]).to_dict()
    res = {"n": len(d), "agreement": float((d["ours"] == d["label"]).mean()),
           "kappa": kappa(d["ours"], d["label"]), "confusion_ours_by_llm": conf,
           "disagreements": d.loc[d["ours"] != d["label"], ["case_id", "ours", "label", "reason"]]
           .to_dict("records")}
    by = {}
    for L, g in d.groupby("label"):
        y = g["bhar_0_20"]
        hit = (y < 0) if L == "SD" else (y >= 0)
        by[L] = {"n": len(g), "mean_bhar_0_20": float(y.mean()), "hit_rate": float(hit.mean()),
                 "cases": list(g["case_id"])}
    res["outcomes_by_llm_label"] = by
    with open(OUT / f"scores_{version}.json", "w") as f:
        json.dump(res, f, indent=2, default=float)
    print(json.dumps({k: v for k, v in res.items() if k != "disagreements"}, indent=1, default=float))
    for r in res["disagreements"]:
        print(f"  {r['case_id']}: ours {r['ours']}, LLM {r['label']} - {r['reason']}")


if __name__ == "__main__":
    if sys.argv[1] == "prepare":
        prepare()
    else:
        score(sys.argv[2])
