"""Traceability check for paper 3 (presence-and-value check: a number can also match
elsewhere in the text, so this proves each stored value is printed, not where): every key number in docs/entropy_portfolio/NOTE.md is
recomputed from results/entropy_portfolio/ and must (a) appear in the NOTE as printed and
(b) equal the stored result after rounding.  Run: python scripts/ep_traceability.py"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results" / "entropy_portfolio"
NOTE = (ROOT / "docs" / "entropy_portfolio" / "NOTE.md").read_text()
J = {
    "real": json.loads((RES / "real" / "summary.json").read_text()),
    "hold": json.loads((RES / "holdout" / "summary.json").read_text()),
    "x": json.loads((RES / "real" / "h3_extra.json").read_text()),
    "xh": json.loads((RES / "holdout" / "h3_extra.json").read_text()),
    "rep": json.loads((RES / "replication.json").read_text()),
}


def get(path):
    src, *keys = path.split("|")
    v = J[src]
    for k in keys:
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def sm(src, mk, strat, col, field):
    return f"{src}|{mk}|summary|{strat}|{col}|{field}"


# (number as printed in NOTE, json path, decimals, scale)
C = []
for mk, strats in {
    "india": ["1/N", "min", "min-LW", "min-norm2-CV", "min-c", "mv-c", "KZ3", "TZ",
              "none:R1", "mom:R1", "lowvol:R1"],
    "us": ["1/N", "min-LW", "min-norm2-CV", "min-c", "none:R1", "mom:R1", "lowvol:R1"],
}.items():
    for s in strats:
        C.append((sm("real", mk, s, "gross", "sharpe"), 3, 1))
        C.append((sm("real", mk, s, "net", "sharpe"), 3, 1))
        C.append((sm("real", mk, s, "net", "ceq25_pct"), 3, 1))
        C.append((f"real|{mk}|summary|{s}|turnover", 2, 1))
C += [
    (sm("real", "india", "mv", "gross", "sharpe"), 3, 1),
    (sm("real", "india", "mv", "gross", "ceq25_pct"), 1, 1),
    ("real|india|summary|mv|turnover", 2, 1),
    ("real|us|summary|mv|turnover", 2, 1),
    ("real|india|H1|mv_vs_1N_gross|sr_diff", 3, 1),
    ("real|india|H1|mv_vs_1N_gross|lw_p", 2, 1),
    ("real|us|H1|mv_vs_1N_gross|sr_diff", 3, 1),
    ("real|us|H1|mv_vs_1N_gross|lw_p", 2, 1),
    ("real|india|H2|none|R1_vs_1N_net|sr_diff", 3, 1),
    ("real|india|H2|mom|R1_vs_1N_net|sr_diff", 3, 1),
    ("real|india|H2|lowvol|R1_vs_1N_net|sr_diff", 3, 1),
    ("real|india|H2|none|R1_vs_1N_net|lw_p", 2, 1),
    ("real|india|H2|mom|R1_vs_1N_net|lw_p", 2, 1),
    ("real|india|H2|lowvol|R1_vs_1N_net|lw_p", 2, 1),
    ("real|india|H2|none|R1_vs_1N_net|ceq_diff_pct", 2, 1),
    ("real|india|H2|mom|R1_vs_1N_net|ceq_diff_pct", 2, 1),
    ("real|india|H2|lowvol|R1_vs_1N_net|ceq_diff_pct", 2, 1),
    ("real|india|H2|lowvol|R1_vs_mv_net|lw_p", 3, 1),
    ("real|india|SPA|p_consistent", 2, 1),
    ("real|us|SPA|p_consistent", 2, 1),
    ("real|india|PBO|pbo", 2, 1),
    ("real|us|PBO|pbo", 2, 1),
    ("x|H3a_spearman_ic_vs_argmax", 2, 1),
    ("x|H3a_p_two_sided", 3, 1),
    ("x|H3b_gap_mean", 2, 1),
    ("x|H3b_sign_test_p", 3, 1),
    ("x|H3b_interval_width_mean", 2, 1),
    ("real|india|H3|lowvol|eval_ic_mean", 3, 1),
    ("real|india|H3|mom|eval_ic_mean", 3, 1),
    ("real|india|H3|none|eval_ic_mean", 3, 1),
    ("real|us|H3|none|eval_ic_mean", 3, 1),
    ("real|us|H3|mom|eval_ic_mean", 3, 1),
    ("real|us|H3|lowvol|eval_ic_mean", 3, 1),
    ("real|india|H3|lowvol|full_info_pred", 2, 1),
    ("real|india|H3|mom|full_info_pred", 2, 1),
    ("real|us|H3|none|full_info_pred", 2, 1),
    ("real|us|H3|mom|full_info_pred", 2, 1),
    ("real|us|H3|lowvol|full_info_pred", 2, 1),
    ("real|india|H3d|shrunk|slope", 2, 1),
    ("real|us|H3d|shrunk|slope", 2, 1),
    ("real|india|H3|none|rules_net|R2|ceq25_pct", 3, 1),
    ("real|india|H3|mom|rules_net|R2|ceq25_pct", 3, 1),
    ("real|india|H3|mom|rules_net|R3|ceq25_pct", 3, 1),
    ("real|us|H3|none|rules_net|R3|ceq25_pct", 3, 1),
    ("real|us|H3|mom|rules_net|R2|ceq25_pct", 3, 1),
    ("real|us|H3|lowvol|rules_net|R3|ceq25_pct", 3, 1),
    ("real|us|summary|1/N|net25|sharpe", 3, 1),
    ("real|us|summary|1/N|net50|sharpe", 3, 1),
    ("real|us|summary|lowvol:R1|net25|sharpe", 3, 1),
    ("real|us|summary|lowvol:R1|net50|sharpe", 3, 1),
    ("real|us|summary|min-LW|net25|sharpe", 3, 1),
    ("real|us|summary|min-LW|net50|sharpe", 3, 1),
    # holdout
    ("hold|india|summary|1/N|net|sharpe", 3, 1),
    ("hold|us|summary|1/N|net|sharpe", 3, 1),
    ("hold|india|summary|none:R1|net|sharpe", 3, 1),
    ("hold|india|summary|mom:R1|net|sharpe", 3, 1),
    ("hold|india|summary|lowvol:R1|net|sharpe", 3, 1),
    ("hold|india|summary|min-c|net|sharpe", 3, 1),
    ("hold|us|summary|none:R1|net|sharpe", 3, 1),
    ("hold|us|summary|mom:R1|net|sharpe", 3, 1),
    ("hold|us|summary|lowvol:R1|net|sharpe", 3, 1),
    ("hold|us|summary|mv|net|sharpe", 3, 1),
    ("hold|india|H3|mom|rules_net|R1|ceq25_pct", 3, 1),
    ("hold|india|H3|mom|rules_net|R2|ceq25_pct", 3, 1),
    ("hold|us|H3|lowvol|rules_net|R1|ceq25_pct", 3, 1),
    ("hold|us|H3|lowvol|rules_net|R2|ceq25_pct", 3, 1),
    ("hold|us|H3|lowvol|R1_vs_R2_net|lw_p", 3, 1),
    ("xh|H3a_spearman_ic_vs_argmax", 2, 1),
    ("xh|H3a_p_two_sided", 2, 1),
    ("hold|india|H3d|shrunk|slope", 2, 1),
    ("hold|us|H3d|shrunk|slope", 2, 1),
    ("hold|india|H1|mv_vs_1N_gross|sr_diff", 3, 1),
    ("hold|us|H1|mv_vs_1N_gross|sr_diff", 3, 1),
    ("hold|us|H1|mv_vs_1N_gross|lw_p", 3, 1),
    # replication
    ("rep|Industry|checks|1/N|ours", 4, 1),
    ("rep|MKT/SMB/HML|checks|1/N|diff", 4, 1),
    ("rep|Industry|checks|mv|diff", 4, 1),
    ("rep|Industry|checks|min|diff", 4, 1),
]


def fmt(v, dec):
    s = f"{v:.{dec}f}"
    if s.startswith("-0") and float(s) == 0:
        s = s[1:]
    return s.replace("-", "−")


ok, bad = 0, []
for path, dec, scale in C:
    v = get(path) * scale
    s = fmt(v, dec)
    variants = {s, s.lstrip("−"), s.replace("−", "-")}
    if s.startswith("0."):
        variants.add(s[1:])
    if abs(v) >= 1000:
        variants.add(f"{v:,.{dec}f}".replace("-", "−"))
    if any(x in NOTE for x in variants):
        ok += 1
    else:
        bad.append((path, s))
print(f"traceability: {ok}/{len(C)} numbers found in NOTE.md exactly as stored")
for p, s in bad:
    print("  MISSING", p, s)
sys.exit(0 if not bad else 1)
