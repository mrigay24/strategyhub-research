"""Paper 3 post-referee recomputations from the SAVED monthly returns (no portfolio is
re-run, so the holdout stays a single run):
  * Hansen SPA with the corrected centring (ep_lib.spa_test, fixed 13 Nov 2026);
  * PBO without the three duplicate 1/N columns (level 1.00 is identical for all signals);
  * H3a exact permutation p-value (6 cases, 720 permutations);
  * H3b gaps with floating-point ties treated as zero;
  * R1-vs-R2 win counts by net CEQ (ties = |diff| < 0.001 %/month).
Writes results/entropy_portfolio/<mode>/postfix.json.  Run: python scripts/ep_postfix.py"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
import ep_lib as L  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GAMMA = 2.5
SIG = ["none", "mom", "lowvol"]
LEVELS = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05]

for mode in ("real", "holdout"):
    d = ROOT / "results" / "entropy_portfolio" / mode
    S = json.loads((d / "summary.json").read_text())
    out = {}
    for mk in ("india", "us"):
        R = pd.read_csv(d / f"{mk}_returns.csv", header=[0, 1], index_col=0)
        net = lambda k: R[(k, "net")].values  # noqa: E731
        base = net("1/N")
        ub = base - 0.5 * GAMMA * (base - base.mean()) ** 2
        models = [f"{s}:{r}" for s in SIG for r in ("R1", "R2", "R3", "R1G")]
        D = np.column_stack([net(k) - 0.5 * GAMMA * (net(k) - net(k).mean()) ** 2 - ub
                             for k in models])
        spa = L.spa_test(D, B=4999, mean_block=6.0)
        keys = ["none:L1.00"] + [f"{s}:L{lv:.2f}" for s in SIG for lv in LEVELS if lv < 1.0]
        pbo, logits = L.pbo_cscv(np.column_stack([net(k) for k in keys]), S=16)
        wins = {"R1": 0, "R2": 0, "tie": 0}
        for s in SIG:
            a = S[mk]["H3"][s]["rules_net"]["R1"]["ceq25_pct"]
            b = S[mk]["H3"][s]["rules_net"]["R2"]["ceq25_pct"]
            wins["tie" if abs(a - b) < 1e-3 else ("R1" if a > b else "R2")] += 1
        r1_vs_1n = {s: S[mk]["H3"][s]["rules_net"]["R1"]["ceq25_pct"]
                    - S[mk]["summary"]["1/N"]["net"]["ceq25_pct"] for s in SIG}
        out[mk] = {"spa": spa, "pbo": pbo, "pbo_variants": len(keys),
                   "R1_vs_R2_wins": wins, "R1_minus_1N_net_ceq_pct": r1_vs_1n,
                   "mean_c": {s: S[mk]["H3"][s]["mean_c"] for s in SIG}}
    # H3a exact permutation test and tie-safe H3b
    cases = [(mk, s) for mk in ("india", "us") for s in SIG]
    ic = np.array([S[mk]["H3"][s]["eval_ic_mean"] for mk, s in cases])
    am = np.array([S[mk]["H3"][s]["argmax_gross"] for mk, s in cases])
    pr = np.array([S[mk]["H3"][s]["full_info_pred"] for mk, s in cases])
    rho = stats.spearmanr(ic, am)[0]
    perms = [stats.spearmanr(ic, am[list(p)])[0] for p in itertools.permutations(range(6))]
    p_exact = float(np.mean(np.abs(perms) >= abs(rho) - 1e-12))
    gap = am - pr
    gap = np.where(np.abs(gap) < 1e-9, 0.0, gap)
    npos, nneg = int((gap > 0).sum()), int((gap < 0).sum())
    out["H3a"] = {"rho": float(rho), "p_exact_two_sided": p_exact,
                  "rho_within_india": float(stats.spearmanr(ic[:3], am[:3])[0]),
                  "rho_within_us": float(stats.spearmanr(ic[3:], am[3:])[0])}
    out["H3b"] = {"gaps": gap.round(4).tolist(), "positive": npos, "negative": nneg,
                  "ties": int((gap == 0).sum()),
                  "sign_test_p_excluding_ties": float(stats.binomtest(npos, npos + nneg).pvalue)
                  if npos + nneg else None,
                  "note": "post hoc (not pre-registered); cases not independent"}
    (d / "postfix.json").write_text(json.dumps(out, indent=1, default=float))
    print(mode, json.dumps({mk: {"spa_p_cons": round(out[mk]["spa"]["p_consistent"], 3),
                                 "spa_p_upper": round(out[mk]["spa"]["p_upper"], 3),
                                 "pbo": round(out[mk]["pbo"], 3),
                                 "R1_vs_R2": out[mk]["R1_vs_R2_wins"]} for mk in ("india", "us")}),
          json.dumps(out["H3a"]), json.dumps(out["H3b"]))
