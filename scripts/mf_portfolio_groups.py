"""Fund-level 'count groups, not stocks': effective N of stocks vs owner groups for Indian equity MFs.

One monthly disclosure per fund (latest available), parsed from AMC xlsx files in
data_raw/mf_portfolios/<amc>/ (parse only, never executed). Holdings: equity ISINs (INE....01...),
matched ISIN -> NSE symbol (data_processed/amfi_avg_mcap.parquet) -> group map (read only).
Group definitions G1/G2/G3 are identical to scripts/group_concentration_headline.py.
Weights renormalised to the matched+unmatched equity sleeve (all INE equity ISINs).
Usage: .venv/bin/python scripts/mf_portfolio_groups.py [--map PATH] [--out CSV]
"""
import argparse, csv, os, re, sys
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from amfi_marketcap_pipeline import read_xlsx  # stdlib xlsx reader

RAW = os.path.join(ROOT, "data_raw", "mf_portfolios")
EQ_ISIN = re.compile(r"^INE[0-9A-Z]{4}01[0-9A-Z]{3}$")  # note: 12 chars; chars 8-9 '01' = equity

# (amc, fund, category, file under RAW/<amc>/, sheet code or None (single-sheet), month, source_url)
NIP = "https://mf.nipponindiaim.com/InvestorServices/FactsheetsDocuments/NIMF-MONTHLY-PORTFOLIO-31-Oct-26.xls"
PP = "https://amc.ppfas.com/downloads/portfolio-disclosure/2026/"
FUNDS = [
    ("Nippon India", "Nippon India Small Cap Fund", "Small cap", "nippon/NIMF-MONTHLY-PORTFOLIO-31-Oct-26.xls", "SC", "2026-10", NIP),
    ("Nippon India", "Nippon India Large Cap Fund", "Large cap", "nippon/NIMF-MONTHLY-PORTFOLIO-31-Oct-26.xls", "EA", "2026-10", NIP),
    ("Nippon India", "Nippon India Multi Cap Fund", "Multi cap", "nippon/NIMF-MONTHLY-PORTFOLIO-31-Oct-26.xls", "EO", "2026-10", NIP),
    ("Nippon India", "Nippon India Growth Mid Cap Fund", "Mid cap", "nippon/NIMF-MONTHLY-PORTFOLIO-31-Oct-26.xls", "GF", "2026-10", NIP),
    ("Nippon India", "Nippon India Value Fund", "Value", "nippon/NIMF-MONTHLY-PORTFOLIO-31-Oct-26.xls", "SE", "2026-10", NIP),
    ("PPFAS", "Parag Parikh Flexi Cap Fund", "Flexi cap", "ppfas/PPFCF_Oct_2026.xlsx", None, "2026-10",
     PP + "PPFCF_PPFAS_Monthly_Portfolio_Report_October_31_2026.xlsx"),
]
# Extra funds are appended by FUNDS_EXTRA in mf_portfolio_sources.py-style entries below (same tuple shape).


def parse_fund(path, sheet):
    book = read_xlsx(path)
    rows = book[sheet] if sheet else next(iter(book.values()))
    isin_c = w_c = None
    out = {}
    for r in rows:
        cells = [("" if c is None else str(c)) for c in r]
        if isin_c is None or w_c is None:
            for i, c in enumerate(cells):
                cl = c.lower().replace("\n", " ")
                if cl.strip() == "isin": isin_c = i
                if cl.strip().startswith("% to"): w_c = i
            continue
        if isin_c >= len(cells) or w_c >= len(cells): continue
        isin = cells[isin_c].strip()
        if not EQ_ISIN.match(isin) or isin[7:9] != "01": continue
        try: wt = float(cells[w_c])
        except ValueError: wt = 0.0   # e.g. '$0.00%' style tiny/nil entries
        if wt > 0: out[isin] = out.get(isin, 0.0) + wt
    return pd.Series(out, dtype=float)


def effn(x):
    x = np.asarray(x, float); x = x[x > 0]; x = x / x.sum()
    return float(np.exp(-(x * np.log(x)).sum()))


def load_map(path, asof):
    with open(path, newline="", encoding="utf-8") as f:
        gm = pd.DataFrame(list(csv.DictReader(f))).fillna("")
    gm["start"] = pd.to_datetime(gm["start"], errors="coerce"); gm["end"] = pd.to_datetime(gm["end"], errors="coerce")
    me = gm["end"].max(); gm.loc[gm["end"] == me, "end"] = pd.Timestamp("2100-01-01")
    gm.loc[gm["start"].isna(), "start"] = pd.Timestamp("1900-01-01"); gm.loc[gm["end"].isna(), "end"] = pd.Timestamp("2100-01-01")
    return gm[(gm.start <= asof) & (gm.end >= asof)].drop_duplicates("symbol", keep="last")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", default=os.path.join(ROOT, "results", "group_dependency", "group_map.csv"))
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "group_concentration", "fund_level_latest.csv"))
    a = ap.parse_args()
    amfi = pd.read_parquet(os.path.join(ROOT, "data_processed", "amfi_avg_mcap.parquet"))
    amfi = amfi.dropna(subset=["isin", "nse_symbol"]).sort_values("period_end").drop_duplicates("isin", keep="last")
    i2s = amfi.set_index("isin")["nse_symbol"]
    i2c = amfi.set_index("isin")["company"]
    gm = load_map(a.map, pd.Timestamp("2026-10-31"))
    res = []
    for amc, fund, cat, f, sheet, month, url in FUNDS:
        p = os.path.join(RAW, f)
        s = parse_fund(p, sheet)
        if s.empty: print("EMPTY", fund); continue
        d = pd.DataFrame({"isin": s.index, "w": s.values / s.sum()})
        d["symbol"] = d["isin"].map(i2s); d["company"] = d["isin"].map(i2c).fillna(d["isin"])
        d = d.merge(gm[["symbol", "group", "group_type"]], on="symbol", how="left").fillna({"group": "", "group_type": ""})
        solo = "solo:" + d["isin"]
        d["g1"] = np.where(d.group_type.isin(["Family", "Corporate"]), d.group, solo)
        d["g2"] = np.where(d.group_type == "State", "State: Government of India", d.g1)
        d["g3"] = np.where(d.group_type == "MNC", d.group, d.g1)
        r = dict(fund=fund, amc=amc, category=cat, month=month, n_holdings=len(d), equity_pct_of_nav_sum=round(s.sum() * (100 if s.sum() <= 1.5 else 1), 1),
                 effN_stocks=effn(d.w))
        for g in ("g1", "g2", "g3"): r["effN_" + g.upper()] = effn(d.groupby(g).w.sum())
        r["ratio"] = r["effN_stocks"] / r["effN_G1"]
        r["matched_weight"] = d.loc[d.group_type != "", "w"].sum()
        r["isin_mapped_weight"] = d.loc[d.symbol.notna(), "w"].sum()
        t = d.groupby("g1").w.sum().nlargest(3)
        name = lambda k: (d.loc[d["isin"] == k[5:], "company"].iloc[0] + " (standalone)") if k.startswith("solo:") else k
        r["top3_groups"] = "; ".join("%s %.1f%%" % (name(k), v * 100) for k, v in t.items())
        r["source_url"] = url
        res.append(r)
    R = pd.DataFrame(res)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    R.to_csv(a.out, index=False, float_format="%.4f")
    print(R.drop(columns=["source_url"]).to_string())
    print("median ratio", R.ratio.median())


if __name__ == "__main__":
    main()
