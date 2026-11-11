"""
Traceability check for docs/entropy_research/PAPER_DRAFT.md (2026-11-11).

Every headline number in the paper is recomputed here from its file in results/,
formatted the way the paper prints it, and checked to appear in the draft text.
Prints PASS/FAIL per row; exit code 1 if any row fails.

  ~/.venvs/strategyhub/bin/python scripts/death_test_paper_check.py            # check
  ~/.venvs/strategyhub/bin/python scripts/death_test_paper_check.py --table    # print Appendix C table
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "docs" / "entropy_research" / "PAPER_DRAFT.md"
R = ROOT / "results"
M = "−"  # the paper prints a true minus sign


def pct(x: float, d: int = 1, sign: bool = False) -> str:
    s = f"{x * 100:+.{d}f}" if sign else f"{x * 100:.{d}f}"
    return s.replace("-", M) + "%"


def num(x: float, d: int = 2, sign: bool = False) -> str:
    return (f"{x:+.{d}f}" if sign else f"{x:.{d}f}").replace("-", M)


def pp(x: float, d: int = 1) -> str:
    return num(x * 100, d) + " pp"


def rows() -> list[tuple[str, str, str]]:
    rob = pd.read_csv(R / "death_test" / "robustness.csv").set_index("variant")
    base = rob.iloc[0]
    var = {k: rob.iloc[i] for i, k in enumerate(["base", "t10", "t20", "excrisis", "exfin", "sector"])}
    terc = pd.read_csv(R / "death_test" / "us_by_share_tercile.csv").set_index("share_tercile")
    ev = pd.read_csv(R / "death_test" / "us_events.csv")
    summ = json.load(open(R / "death_test" / "summary.json"))
    pb = {(c["case"], c["peer_group"]): c for c in summ["part_b"]["cases"]}
    pbc = {c["case"]: c for c in summ["part_b"]["cases"]}
    t = json.load(open(R / "death_test_oos" / "tests.json"))
    reg, full = t["registered"], t["full_population"]
    sens = json.load(open(R / "death_test_oos" / "sensitivity_overlap.json"))
    out = pd.read_csv(R / "death_test_oos" / "outcomes.csv")
    t1 = pd.read_csv(R / "entropy_research" / "test1_summary_by_N.csv").set_index("N")
    f_rob, f_t, f_ev, f_sum = ("results/death_test/robustness.csv", "results/death_test_oos/tests.json",
                               "results/death_test/us_events.csv", "results/death_test/summary.json")
    orc = out[(out.status == "case") & (out.peer_set == "rivals") & (out.label == "OR")]
    return [
        # Part A
        ("US isolated crash events", str(len(ev)), f_ev),
        ("Sub-industries in Part A", str(ev["sub_industry"].nunique()), f_ev),
        ("Day-0 rival reaction, all", pct(base["d0_mean"], 2), f_rob + " (baseline d0_mean)"),
        ("Day-0 clustered t", num(base["d0_t_cl"], 1), f_rob + " (d0_t_cl)"),
        ("Share of events with rivals down on day 0", f"{base['pct_peers_down_d0'] * 100:.0f}%", f_rob),
        ("20-day rival reaction, all", pct(base["0_20_mean"], 2), f_rob + " (0_20_mean)"),
        ("20-day CI low / high", f"[{num(base['0_20_ci_lo'] * 100, 2)}, {num(base['0_20_ci_hi'] * 100, 2, True)}]", f_rob),
        ("Day 0, small / mid / large share",
         " / ".join(pct(terc.loc[k, "peer_car_d0"], 2) for k in ["small share", "mid share", "large share"]),
         "results/death_test/us_by_share_tercile.csv"),
        ("Large − small share gap, day 0 [CI]",
         f"{num(base['d0_share_gap'] * 100, 2)} pp [{num(base['d0_share_gap_lo'] * 100, 2)}, {num(base['d0_share_gap_hi'] * 100, 2)}]", f_rob),
        ("CV R², share + HHI (base, −10%, −20%, ex-Fin)",
         ", ".join(pct(var[k]["d0_cvR2_share_hhi"], 1) for k in ["base", "t10", "t20", "exfin"]), f_rob + " (d0_cvR2_share_hhi)"),
        ("CV R², sub-industry (base, −10%, −20%, ex-Fin)",
         ", ".join(pct(var[k]["d0_cvR2_subind"], 1, k in ("t10", "t20")) for k in ["base", "t10", "t20", "exfin"]),
         f_rob + " (d0_cvR2_subind)"),
        ("In-sample adj. R², share + HHI / sub-industry (base)",
         f"{pct(base['d0_adjR2_share_hhi'])} / {pct(base['d0_adjR2_subind'])}", f_rob),
        ("Within-sub-industry share t, day 0", num(base["d0_share_t_within_subind_cl"], 1), f_rob),
        ("Day 0 excluding Financials", pct(var["exfin"]["d0_mean"], 2), f_rob),
        ("Persistence of day-0 reaction (Spearman, 7 sub-industries)",
         num(summ["part_a"]["persistence"]["sub_industry:peer_car_d0"]["spearman"], 2), f_sum),
        # Part B
        ("Satyam rivals, 20-day BHAR", pct(pbc["satyam"]["peer_bhar_0_20"], 1, True), f_sum),
        ("Adani group firms, 20-day BHAR", pct(pb[("adani", "Adani group companies")]["peer_bhar_0_20"], 1), f_sum),
        ("Adani sector rivals, 20-day BHAR",
         pct(pb[("adani", "Sector rivals (cement, power, ports)")]["peer_bhar_0_20"], 1, True), f_sum),
        ("IL&FS lenders, 20-day BHAR", pct(pbc["ilfs"]["peer_bhar_0_20"], 1), f_sum),
        ("Yes Bank rivals, 20-day BHAR", pct(pbc["yes_bank"]["peer_bhar_0_20"], 1), f_sum),
        ("SVB regional banks, 20-day BHAR", pct(pbc["svb"]["peer_bhar_0_20"], 1), f_sum),
        # Pre-registered test
        ("OOS SD mean, registered / full", f"{pct(reg['T1_T2']['mean_SD'])} / {pct(full['T1_T2']['mean_SD'])}", f_t),
        ("OOS OR mean, registered / full", f"{pct(reg['T1_T2']['mean_OR'])} / {pct(full['T1_T2']['mean_OR'])}", f_t),
        ("OOS SD − OR, registered",
         pp(reg["T1_T2"]["mean_SD"] - reg["T1_T2"]["mean_OR"]), f_t + " (mean_SD − mean_OR)"),
        ("OOS SD − OR, full", pp(full["T1_T2"]["diff"]), f_t + " (full_population.T1_T2.diff)"),
        ("OOS permutation p, full", f"{full['T1_T2']['perm_p']:.3f}", f_t),
        ("OOS Fisher p, full", f"{full['T1_T2']['fisher_p']:.3f}", f_t),
        ("OOS hit rate, all (both versions)",
         f"{reg['T1_T2']['hit_rate'] * 100:.0f}% / {full['T1_T2']['hit_rate'] * 100:.0f}%", f_t),
        ("OOS OR hit rate, registered / full",
         f"{reg['T1_T2']['hit_rate_OR'] * 100:.0f}% / {full['T1_T2']['hit_rate_OR'] * 100:.0f}%", f_t),
        ("H1 verdict (both)", f"{reg['verdict_H1']} / {full['verdict_H1']}", f_t),
        ("T3 meaning (both)", f"{reg['T3_meaning']} / {full['T3_meaning']}", f_t),
        ("T4 group sets mean, sign p", f"{pct(full['T4_group']['mean'])}, {full['T4_group']['sign_p']:.3f}", f_t),
        ("T5 SD t, registered / full", f"{num(reg['T5_share']['t_SD'])} / {num(full['T5_share']['t_SD'])}", f_t),
        ("T5 share t, registered / full",
         f"{num(reg['T5_share']['t_share'])} / {num(full['T5_share']['t_share'])}", f_t),
        ("Market-model perm p, full", f"{full['robustness']['bhar_mm_0_20']['perm_p']:.3f}", f_t),
        ("Ex-crisis SD / OR mean, full",
         f"{pct(full['robustness']['ex_crises']['mean_SD'])} / {pct(full['robustness']['ex_crises']['mean_OR'])}", f_t),
        ("OR day-0 mean, full", pct(orc["car_0_0"].mean()), "results/death_test_oos/outcomes.csv"),
        ("OR median, full", pct(orc["bhar_0_20"].median()), "results/death_test_oos/outcomes.csv"),
        ("Not pre-registered: overlap check SD − OR, p (full)",
         f"{pp(sens['full_population']['T1_T2']['diff'])}, {sens['full_population']['T1_T2']['perm_p']:.3f}",
         "results/death_test_oos/sensitivity_overlap.json"),
        ("$10m rival basket: SD / OR loss",
         f"${abs(full['T1_T2']['mean_SD']) * 10:.2f} million / ${abs(full['T1_T2']['mean_OR']) * 10:.2f} million", f_t),
        # Appendix A
        ("Test 1 median return, N = 1 / 50",
         f"{pct(t1.loc[1, 'median_ann_return'])} / {pct(t1.loc[50, 'median_ann_return'])}",
         "results/entropy_research/test1_summary_by_N.csv"),
        ("Test 1 chance of lagging by >3 pp, N = 1 / 50",
         f"{t1.loc[1, 'prob_lag_universe_by_3pct_pa'] * 100:.0f}% / {t1.loc[50, 'prob_lag_universe_by_3pct_pa'] * 100:.0f}%",
         "results/entropy_research/test1_summary_by_N.csv"),
    ]


def main() -> None:
    text = " ".join(PAPER.read_text().split())  # ignore line wrapping
    rs = rows()
    if "--table" in sys.argv:
        print("| Headline number | Value | Source |\n|---|---|---|")
        for lab, val, src in rs:
            print(f"| {lab} | {val} | `{src}` |")
        return
    fails = 0
    for lab, val, src in rs:
        parts = [v.strip() for v in val.replace("[", " / ").replace("]", "").replace(", ", " / ").split(" / ")]
        ok = all(pp_ in text for pp_ in parts if pp_)
        fails += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {lab}: {val}")
    print(f"\n{len(rs) - fails}/{len(rs)} rows found in PAPER_DRAFT.md")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
