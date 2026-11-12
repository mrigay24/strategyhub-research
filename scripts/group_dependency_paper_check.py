"""
Traceability check for docs/group_dependency/PAPER2_DRAFT.md (2026-11-12).

Every headline number is recomputed from its file in results/, formatted the way the
paper prints it, and checked to appear in the paper's text ABOVE Appendix C (so the
traceability table cannot match itself). Prints PASS/FAIL per row; exit 1 on any FAIL.

  ~/.venvs/strategyhub/bin/python scripts/group_dependency_paper_check.py           # check
  ~/.venvs/strategyhub/bin/python scripts/group_dependency_paper_check.py --table   # Appendix C table
  ~/.venvs/strategyhub/bin/python scripts/group_dependency_paper_check.py --funds   # Appendix D table
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "docs" / "group_dependency" / "PAPER2_DRAFT.md"
GD, GC = ROOT / "results" / "group_dependency", ROOT / "results" / "group_concentration"
M = "−"


def f(x: float, d: int = 2, sign: bool = False) -> str:
    return (f"{x:+.{d}f}" if sign else f"{x:.{d}f}").replace("-", M)


def pp(x: float, d: int = 2) -> str:
    return f(x * 100, d) + " pp"


def reg(d: dict, key: str) -> dict:
    return d["primary"]["regression"] if key == "primary" else d["robustness"][key]


def rows() -> list[tuple[str, str, str]]:
    v1, v2 = json.load(open(GD / "tests.json")), json.load(open(GD / "v2" / "tests.json"))
    dg = json.load(open(GD / "v2" / "diagnostics_not_preregistered.json"))
    ev = json.load(open(GD / "v2" / "events_summary.json"))
    h = pd.read_csv(GC / "v2" / "headline_by_period.csv")
    t5 = h[h.universe == "top500"].set_index("period")
    t1 = h[h.universe == "top100"].set_index("period")
    top = pd.read_csv(GC / "v2" / "top_groups_latest.csv").set_index("group")
    fd = pd.read_csv(GC / "fund_level_latest_v2map.csv")
    fv1, fv2, fh, fdg, fev = ("results/group_dependency/tests.json", "results/group_dependency/v2/tests.json",
                              "results/group_concentration/v2/headline_by_period.csv",
                              "results/group_dependency/v2/diagnostics_not_preregistered.json",
                              "results/group_dependency/v2/events_summary.json")
    a, b = "2017-12-31", "2026-06-30"
    out = [
        ("Top 500 effN stocks, Dec 2017 / Jun 2026", f"{t5.loc[a, 'effN_stocks']:.1f} / {t5.loc[b, 'effN_stocks']:.1f}", fh),
        ("Top 500 effN groups G1", f"{t5.loc[a, 'effN_groups_G1']:.1f} / {t5.loc[b, 'effN_groups_G1']:.1f}", fh),
        ("Top 500 effN groups G2", f"{t5.loc[a, 'effN_groups_G2']:.1f} / {t5.loc[b, 'effN_groups_G2']:.1f}", fh),
        ("Top 500 ratio stocks/G1", f"{t5.loc[a, 'ratio_stocks_to_groups_G1']:.2f} / {t5.loc[b, 'ratio_stocks_to_groups_G1']:.2f}", fh),
        ("Top 500 ratio, min and max over periods",
         f"{t5['ratio_stocks_to_groups_G1'].min():.2f} / {t5['ratio_stocks_to_groups_G1'].max():.2f}", fh),
        ("Top 100 stocks / G1 / G2, Jun 2026",
         f"{t1.loc[b, 'effN_stocks']:.1f} / {t1.loc[b, 'effN_groups_G1']:.1f} / {t1.loc[b, 'effN_groups_G2']:.1f}", fh),
        ("Headline rounded: 231 / 156 / 82",
         f"{t5.loc[b, 'effN_stocks']:.0f} / {t5.loc[b, 'effN_groups_G1']:.0f} / {t5.loc[b, 'effN_groups_G2']:.0f}", fh),
        ("Group shares of top-500 cap: Tata / Reliance / Adani",
         " / ".join(f"{top.loc[g, 'share_of_top500_mcap'] * 100:.1f}%" for g in ["Tata", "Reliance (Mukesh Ambani)", "Adani"]),
         "results/group_concentration/v2/top_groups_latest.csv"),
        ("Funds: count / median ratio", f"{len(fd)} funds / {fd['ratio'].median():.2f}",
         "results/group_concentration/fund_level_latest_v2map.csv"),
        ("Funds: median effN stocks / G1", f"{fd['effN_stocks'].median():.1f} / {fd['effN_G1'].median():.1f}",
         "results/group_concentration/fund_level_latest_v2map.csv"),
        ("Funds: ratio range", f"{fd['ratio'].min():.2f} / {fd['ratio'].max():.2f}",
         "results/group_concentration/fund_level_latest_v2map.csv"),
        ("Funds: median matched weight", f"{fd['matched_weight'].median() * 100:.1f}%",
         "results/group_concentration/fund_level_latest_v2map.csv"),
        ("v2 events / groups", f"{ev['n_events']} / {ev['n_groups']}", fev),
        ("v2 events with S / groups with S", f"{v2['counts']['n_events_with_S']} / {v2['counts']['n_groups_with_S']}", fv2),
        ("v2 pairs", f"{v2['counts']['n_pairs']:,}", fv2),
        ("v2 class means S: rho / day-0 AR / BHAR mean / median",
         f"{v2['class_means']['S']['mean_rho']:.2f} / {f(v2['class_means']['S']['mean_ar_d0'] * 100)}% / "
         f"{f(v2['class_means']['S']['mean_bhar_0_20'] * 100)}% / {f(v2['class_means']['S']['median_bhar_0_20'] * 100)}%", fv2),
    ]
    for lab, d, src in [("v2", v2, fv2), ("v1", v1, fv1)]:
        r = reg(d, "primary")
        out += [
            (f"{lab} beta_S / t", f"{pp(r['coef']['S'])} / {f(r['t']['month']['S'])}", src),
            (f"{lab} beta_R / t", f"{pp(r['coef']['R'])} / {f(r['t']['month']['R'])}", src),
            (f"{lab} beta_SI / t", f"{pp(r['coef']['SI'])} / {f(r['t']['month']['SI'])}", src),
            (f"{lab} beta_S - beta_R / t", f"{pp(r['S_minus_R'])} / {f(r['t_S_minus_R']['month'])}", src),
            (f"{lab} beta_S without rho / t",
             f"{pp(d['R10_no_rho']['regression']['coef']['S'])} / {f(d['R10_no_rho']['regression']['t']['month']['S'])}", src),
            (f"{lab} permutation draws as negative", f"{int(d['primary']['permutation']['p_one_sided'] * 2000)} as negative", src),
        ]
        for k in ["R1_no_crises", "R2_no_paper1_episodes", "R3_day0_AR", "R3_car_0_20", "R6_high_confidence",
                  "R7_news_checked_clean", "R9_rho_deciles"]:
            r = reg(d, k)
            out.append((f"{lab} {k}: beta_S / t", f"{pp(r['coef']['S'])} / {f(r['t']['month']['S'])}", src))
        r8 = d["robustness"]["R8_event_level"]
        out.append((f"{lab} R8: share negative / sign p",
                    f"{r8['share_negative'] * 100:.0f}% / {r8['sign_p_one_sided']:.3f}", src))
        out.append((f"{lab} R5: t clustered by trigger group", f(d["primary"]["regression"]["t"]["group"]["S"]), src))
    tail = {c["cls"]: c for c in v2["tail_dependence"]["by_class"]}
    out += [
        ("Tail pairs (v2)", f"{v2['tail_dependence']['n_pairs']:,}", fv2),
        ("Tail excess: unrelated / same industry / same group / both",
         " / ".join(f"{tail[c]['mean_excess'] * 100:.3f}%" for c in ["neither", "same_industry", "same_group", "both"]), fv2),
        ("Leave-one-group-out: without Adani / without Tata",
         f"{f(dg['D1_leave_one_group_out']['max_beta_S']['beta_S'] * 100, 1)} / {f(dg['D1_leave_one_group_out']['min_beta_S']['beta_S'] * 100, 1)}", fdg),
        ("Worst 10 / worst 5 share of total sibling loss",
         f"{dg['D3_events']['share_of_total_from_worst_10'] * 100:.0f}% / {dg['D3_events']['share_of_total_from_worst_5'] * 100:.0f}%", fdg),
        ("Mean without worst 5", f(dg["D3_events"]["mean_without_worst_5"] * 100, 1), fdg),
        ("Crash day without companion episodes: beta_S / t",
         f"{f(dg['D2_no_paper1_ar_d0']['beta_S'] * 100, 1)} / {f(dg['D2_no_paper1_ar_d0']['t_month'])}", fdg),
    ]
    return out


def funds_table() -> str:
    fd = pd.read_csv(GC / "fund_level_latest_v2map.csv")
    lines = ["| Fund | Category | Holdings | effN stocks | effN groups (G1) | Ratio | Matched weight |",
             "|---|---|---|---|---|---|---|"]
    for r in fd.sort_values(["category", "fund"]).itertuples():
        lines.append(f"| {r.fund} | {r.category} | {r.n_holdings} | {r.effN_stocks:.1f} | {r.effN_G1:.1f} | "
                     f"{r.ratio:.2f} | {r.matched_weight * 100:.0f}% |")
    return "\n".join(lines) + "\n\n*Source: `results/group_concentration/fund_level_latest_v2map.csv` (portfolios as on 31 Oct 2026).*"


def main() -> None:
    if "--funds" in sys.argv:
        print(funds_table())
        return
    rs = rows()
    if "--table" in sys.argv:
        print("| Headline number | Value | Source |\n|---|---|---|")
        for lab, val, src in rs:
            print(f"| {lab} | {val} | `{src}` |")
        return
    body = PAPER.read_text().split("## Appendix C")[0]
    text = " ".join(body.split())
    fails = 0
    for lab, val, src in rs:
        parts = [v.strip() for v in val.split(" / ")]
        ok = all(p_ in text for p_ in parts if p_)
        fails += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {lab}: {val}")
    print(f"\n{len(rs) - fails}/{len(rs)} rows found in PAPER2_DRAFT.md")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
