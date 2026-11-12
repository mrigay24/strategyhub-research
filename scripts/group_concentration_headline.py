"""Count groups, not stocks: effective N of stocks vs owner groups per half-year.

Weights: AMFI 6-month average market cap (data_processed/amfi_avg_mcap.parquet,
built by scripts/amfi_marketcap_pipeline.py). Fallback (if that file is missing):
63-day average traded value from data_processed/nse_survivorship_free_adj.parquet.
Group map is read only. Usage: .venv/bin/python scripts/group_concentration_headline.py [--map PATH]

Group definitions (fixed before looking at results):
 G1: Family and Corporate groups are groups; everything else (MNC, State, Professional,
     PE, Unknown, unmatched) is standalone (each company its own group).
 G2: G1 + all State firms as one owner (Government of India).
 G3: G1 + MNC subsidiaries grouped by parent.
Map rows are matched on NSE symbol with start <= period_end <= end. The v1 map's
end is 2025-06-30 for ~all live companies; an end equal to the map's latest end
date is treated as open-ended (so the 2025-12 and 2026-06 periods can match).
"""
import argparse, csv, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "group_concentration")
ap = argparse.ArgumentParser()
ap.add_argument("--map", default=os.path.join(ROOT, "results", "group_dependency", "group_map.csv"))
ap.add_argument("--out", default=OUT)
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)

with open(args.map, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
gm = pd.DataFrame(rows).fillna("")
print("map rows", len(gm), "symbols", gm.symbol.nunique())
gm["start"] = pd.to_datetime(gm["start"], errors="coerce")
gm["end"] = pd.to_datetime(gm["end"], errors="coerce")
map_end = gm["end"].max()
gm.loc[gm["end"] == map_end, "end"] = pd.Timestamp("2100-01-01")
gm.loc[gm["start"].isna(), "start"] = pd.Timestamp("1900-01-01")
gm.loc[gm["end"].isna(), "end"] = pd.Timestamp("2100-01-01")

# ---- weights
amfi = os.path.join(ROOT, "data_processed", "amfi_avg_mcap.parquet")
if os.path.exists(amfi):
    w = pd.read_parquet(amfi).rename(columns={"avg_mcap_cr": "w"})
    w["key"] = w["isin"]
    label = "AMFI 6-month average market cap"
else:
    px = pd.read_parquet(os.path.join(ROOT, "data_processed", "nse_survivorship_free_adj.parquet"),
                         columns=["date", "symbol", "close", "volume"])
    px["tv"] = px.close * px.volume
    tv = px.pivot_table(index="date", columns="symbol", values="tv").sort_index()
    ends = pd.date_range("2015-06-30", tv.index.max(), freq="6M")
    parts = []
    for e in ends:
        s = tv.loc[:e].tail(63).mean().dropna()
        parts.append(pd.DataFrame({"period_end": e, "nse_symbol": s.index, "w": s.values, "company": s.index, "isin": s.index}))
    w = pd.concat(parts)
    w["key"] = w["isin"]
    label = "traded-value weights (fallback), not market cap"
w = w.dropna(subset=["w"])
w = w[w.w > 0]

def effn(x):
    x = x / x.sum()
    return float(np.exp(-(x * np.log(x)).sum()))

res, latest_groups = [], None
periods = sorted(w.period_end.unique())
for p in periods:
    d = w[w.period_end == p].sort_values("w", ascending=False).drop_duplicates("key").copy()
    total = d.w.sum()
    m = gm[(gm.start <= p) & (gm.end >= p)].drop_duplicates("symbol", keep="last")
    d = d.merge(m[["symbol", "group", "group_type"]], left_on="nse_symbol", right_on="symbol", how="left")
    d["group_type"] = d["group_type"].fillna("")
    d["group"] = d["group"].fillna("")
    solo = "solo:" + d["key"].astype(str)
    d["g1"] = np.where(d.group_type.isin(["Family", "Corporate"]), d["group"], solo)
    d["g2"] = np.where(d.group_type == "State", "State: Government of India", d["g1"])
    d["g3"] = np.where(d.group_type == "MNC", d["group"], d["g1"])
    for name, n in (("top100", 100), ("top500", 500)):
        u = d.nlargest(n, "w")
        r = dict(period=pd.Timestamp(p).date(), universe=name, n_stocks=len(u), effN_stocks=effn(u.w))
        for g in ("g1", "g2", "g3"):
            r["effN_groups_" + g.upper()] = effn(u.groupby(g).w.sum())
        r["ratio_stocks_to_groups_G1"] = r["effN_stocks"] / r["effN_groups_G1"]
        r["matched_mcap_share"] = u.loc[u.group_type != "", "w"].sum() / u.w.sum()
        r["universe_share_of_total_mcap"] = u.w.sum() / total
        res.append(r)
    if p == periods[-1]:
        u = d.nlargest(500, "w")
        g = u.groupby("g1").agg(w=("w", "sum"), n_companies=("key", "count"),
                                 members=("company", lambda s: "; ".join(s.head(6)))).nlargest(15, "w")
        g["share_of_top500_mcap"] = g.w / u.w.sum()
        g["share_of_total_mcap"] = g.w / total
        g.index.name = "group"
        g.index = [u.loc[u.key == k[5:], "company"].iloc[0] + " (standalone)" if str(k).startswith("solo:") else k for k in g.index]
        latest_groups = g.reset_index().rename(columns={"w": "avg_mcap"})
        latest_groups.insert(0, "period", pd.Timestamp(p).date())

R = pd.DataFrame(res)
R.to_csv(os.path.join(args.out, "headline_by_period.csv"), index=False, float_format="%.4f")
latest_groups.to_csv(os.path.join(args.out, "top_groups_latest.csv"), index=False, float_format="%.4f")
t = R[R.universe == "top500"]
plt.figure(figsize=(8, 4.5))
plt.plot(pd.to_datetime(t.period), t.effN_stocks, marker="o", label="effective N of stocks")
plt.plot(pd.to_datetime(t.period), t.effN_groups_G1, marker="o", label="effective N of owner groups (G1)")
plt.ylim(bottom=0)
plt.title("Top 500 by weight: effective N, stocks vs groups\n(%s; provisional v1 map)" % label, fontsize=10)
plt.legend(); plt.grid(alpha=.3); plt.tight_layout()
plt.savefig(os.path.join(args.out, "effn_stocks_vs_groups_top500.png"), dpi=130)
print(label); print(R.to_string())
