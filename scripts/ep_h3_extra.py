"""Cross-case statistics for paper 3 (pre-registered H3a; H3b gap; cost sensitivity).
Reads results/entropy_portfolio/<mode>/summary.json, writes h3_extra.json next to it.
  python scripts/ep_h3_extra.py [real|holdout]"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
mode = sys.argv[1] if len(sys.argv) > 1 else "real"
S = json.loads((ROOT / "results" / "entropy_portfolio" / mode / "summary.json").read_text())
cases = []
for mk in ("india", "us"):
    for s, v in S[mk]["H3"].items():
        cases.append({"case": f"{mk}:{s}", "ic": v["eval_ic_mean"], "argmax": v["argmax_gross"],
                      "pred": v["full_info_pred"], "lo": v["argmax_boot90"][0],
                      "hi": v["argmax_boot90"][1], "inside": v["pred_inside"]})
ic = np.array([c["ic"] for c in cases])
am = np.array([c["argmax"] for c in cases])
pr = np.array([c["pred"] for c in cases])
rho, p = stats.spearmanr(ic, am)
gap = am - pr
gap = np.where(np.abs(gap) < 1e-9, 0.0, gap)  # floating-point ties are ties (referee minor)
out = {
    "cases": cases,
    "H3a_spearman_ic_vs_argmax": float(rho), "H3a_p_two_sided": float(p),
    "H3a_spearman_ic_vs_pred": float(stats.spearmanr(ic, pr)[0]),
    "H3b_inside_count": int(sum(c["inside"] for c in cases)),
    "H3b_gap_argmax_minus_pred": gap.round(4).tolist(),
    "H3b_gap_mean": float(gap.mean()),
    "H3b_gap_positive": int((gap > 0).sum()),
    "H3b_gap_ties": int((gap == 0).sum()),
    "H3b_sign_test_p_excl_ties_posthoc": float(stats.binomtest(
        int((gap > 0).sum()), int((gap != 0).sum())).pvalue) if (gap != 0).any() else None,
    "H3b_interval_width_mean": float(np.mean([c["hi"] - c["lo"] for c in cases])),
}
if "us" in S:
    sm = S["us"]["summary"]
    out["us_cost_sensitivity_net_sharpe"] = {
        k: {c: sm[k][c]["sharpe"] for c in ("gross", "net", "net25", "net50")}
        for k in ["1/N", "min-LW", "min-c"] + [f"{s}:R1" for s in ("none", "mom", "lowvol")]}
(ROOT / "results" / "entropy_portfolio" / mode / "h3_extra.json").write_text(
    json.dumps(out, indent=1))
print(json.dumps({k: v for k, v in out.items() if k != "cases"}, indent=1))
