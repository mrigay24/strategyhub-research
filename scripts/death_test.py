"""
The "death test", version 2 (2026-11-09).

Paper question:
  When a company suffers its own crash, do its rivals gain (the firm was
  replaceable) or lose (shared fate / it mattered), and does the company's
  market share explain which?

Part A  US, 2000-2024, S&P 500 point-in-time members, peers = GICS
        SUB-INDUSTRY (current classification). Every isolated idiosyncratic
        crash. Tests:
          A1 average peer reaction, by sector and by sub-industry
             (the "replaceability map")
          A2 does market share explain it? Regress the peer reaction on the
             firm's share of its sub-industry and the sub-industry HHI, then
             compare the R^2 with sector / sub-industry identity
          A3 is replaceability a stable trait of an industry? Correlate each
             sub-industry's average peer reaction in 2000-12 with 2012-24
          A4 crashes followed by delisting within 60 days (closest to a death)
Part B  Case studies with clean, well-known firm-specific shocks:
        India: Satyam, Jet Airways, IL&FS, DHFL, Yes Bank, Adani-Hindenburg
        US:    PG&E wildfire bankruptcy, Signature Bank / SVB

Size proxy: 63-day average dollar volume (there are no market caps in the data).
Returns: raw prices with a $1 floor (US). Real crashes down to -95% are kept;
spikes above +100% are dropped, and an event is dropped if the next day
reverses by more than +25% (likely a bad print).

Run:  .venv/bin/python scripts/death_test.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from entropy_research import (DATA, entropy_norm, load_panel, log, safe,  # noqa: E402
                              us_pit_mask)

OUT = ROOT / "results" / "death_test"
OUT.mkdir(parents=True, exist_ok=True)
SPLIT = pd.Timestamp("2012-07-01")


def load(path: Path, floor: float | None):
    rets, dv = load_panel(path, max_abs_ret=0.95, price_floor=floor)
    return rets.where(rets <= 1.0), dv


# ----------------------------------------------------------------------------
# Small OLS helper with White (heteroskedasticity-robust) t-stats
# ----------------------------------------------------------------------------
def fit(y: pd.Series, X: pd.DataFrame) -> dict:
    d = pd.concat([y.rename("y"), X], axis=1).dropna()
    yv = d["y"].values
    Xv = np.column_stack([np.ones(len(d)), d.drop(columns="y").values.astype(float)])
    n, k = Xv.shape
    xtx_inv = np.linalg.pinv(Xv.T @ Xv)
    b = xtx_inv @ Xv.T @ yv
    u = yv - Xv @ b
    cov = xtx_inv @ (Xv * u[:, None] ** 2).T @ Xv @ xtx_inv * n / max(n - k, 1)
    t = b / np.sqrt(np.diag(cov))
    r2 = 1 - (u ** 2).sum() / ((yv - yv.mean()) ** 2).sum()
    adj = 1 - (1 - r2) * (n - 1) / max(n - k, 1)
    names = ["const"] + list(X.columns)
    keep = [i for i, nm in enumerate(names) if not nm.startswith("d_")]
    return {"n": int(n), "k": int(k), "r2": safe(r2), "adj_r2": safe(adj),
            "coef": {names[i]: safe(b[i]) for i in keep},
            "t": {names[i]: safe(t[i]) for i in keep}}


def summ(g: pd.DataFrame) -> pd.Series:
    out = {"n_events": len(g), "own_ab_d0": g["own_ab_d0"].mean()}
    for col in ["peer_car_d0", "peer_car_0_5", "peer_car_0_20"]:
        x = g[col].dropna()
        out[col] = x.mean()
        out[f"t_{col}"] = x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan
    out["pct_peers_down_d0"] = (g["peer_car_d0"] < 0).mean()
    out["pct_peers_up_0_20"] = (g["peer_car_0_20"] > 0).mean()
    return pd.Series(out)


# ----------------------------------------------------------------------------
# Part A — US large-sample death test at sub-industry level
# ----------------------------------------------------------------------------
def part_a(rets: pd.DataFrame, mask: pd.DataFrame, dv: pd.DataFrame) -> dict:
    log("Part A: US death test at GICS sub-industry level")
    gm = pd.read_csv(ROOT / "data_raw" / "sp500_constituents" / "sp500_subindustry.csv")
    sub_of = dict(zip(gm["ticker"], gm["sub_industry"]))
    sector_of = dict(zip(gm["ticker"], gm["sector"]))
    cols = [c for c in rets.columns if c in sub_of]
    log(f"  {len(cols)} of {rets.shape[1]} symbols have a current sub-industry")
    R = rets[cols]
    M = (mask[cols] & R.notna()).values
    Rz = R.where(M).fillna(0.0).values
    groups = sorted(set(sub_of[c] for c in cols))
    gidx = {g: [j for j, c in enumerate(cols) if sub_of[c] == g] for g in groups}
    gsum = np.column_stack([Rz[:, gidx[g]].sum(1) for g in groups])
    gn = np.column_stack([M[:, gidx[g]].sum(1) for g in groups])
    tot_sum, tot_n = Rz.sum(1), M.sum(1)
    mkt_ex = (tot_sum[:, None] - gsum) / np.maximum(tot_n[:, None] - gn, 1)
    dvbar = dv[cols].rolling(63, min_periods=40).mean().shift(1).values
    last_valid = R.apply(lambda s: s.last_valid_index())
    T = len(R)
    gpos = {g: k for k, g in enumerate(groups)}

    events = []
    for j, c in enumerate(cols):
        k = gpos[sub_of[c]]
        n_peers = gn[:, k] - M[:, j]
        peer = (gsum[:, k] - Rz[:, j] * M[:, j]) / np.maximum(n_peers, 1)
        own_ab = Rz[:, j] - peer
        peer_ab = peer - mkt_ex[:, k]
        hit = np.where(M[:, j] & (Rz[:, j] < -0.15) & (own_ab < -0.12) & (n_peers >= 3))[0]
        last = -999
        lv = R.index.get_loc(last_valid[c])
        for t in hit:
            if t - last < 20:
                continue
            last = t
            if t < 63 or t + 20 >= T:
                continue
            if np.isfinite(Rz[t + 1, j]) and M[t + 1, j] and Rz[t + 1, j] > 0.25:
                continue
            members = [jj for jj in gidx[sub_of[c]] if M[t, jj]]
            sizes = dvbar[t, members]
            ok = np.isfinite(sizes)
            share = np.nan
            if ok.sum() >= 2 and np.isfinite(dvbar[t, j]):
                share = dvbar[t, j] / sizes[ok].sum()
            _, hhi, _ = entropy_norm(sizes[ok])
            rank = int((sizes[ok] > dvbar[t, j]).sum() + 1) if np.isfinite(dvbar[t, j]) else np.nan
            events.append({
                "date": R.index[t], "symbol": c, "sector": sector_of[c], "sub_industry": sub_of[c],
                "own_ret_d0": Rz[t, j], "own_ab_d0": own_ab[t],
                "peer_car_d0": peer_ab[t], "peer_car_0_5": peer_ab[t:t + 6].sum(),
                "peer_car_0_20": peer_ab[t:t + 21].sum(), "peer_car_1_20": peer_ab[t + 1:t + 21].sum(),
                "firm_share": share, "firm_rank": rank, "sub_hhi": hhi, "n_peers": int(n_peers[t]),
                "delisted_within_60d": bool(lv <= t + 60 and lv < T - 61),
            })
    ev = pd.DataFrame(events)
    ev["cluster"] = ev.groupby(["sub_industry", "date"])["symbol"].transform("count")
    ev = ev[ev["cluster"] == 1].drop(columns="cluster").reset_index(drop=True)
    ev.to_csv(OUT / "us_events.csv", index=False)
    log(f"  {len(ev)} isolated crash events, {ev['sub_industry'].nunique()} sub-industries")

    res = {"n_events": len(ev), "all": summ(ev).to_dict()}
    by_sector = ev.groupby("sector").apply(summ).sort_values("peer_car_0_20")
    by_sub = ev.groupby("sub_industry").apply(summ)
    by_sub["sector"] = ev.groupby("sub_industry")["sector"].first()
    by_sub = by_sub[by_sub["n_events"] >= 8].sort_values("peer_car_0_20")
    by_sector.to_csv(OUT / "us_by_sector.csv")
    by_sub.to_csv(OUT / "us_replaceability_map.csv")
    log("\nAll:\n" + summ(ev).round(4).to_string())
    log("\nBy sector:\n" + by_sector.round(4).to_string())
    log("\nReplaceability map (sub-industries with >=8 events):\n" + by_sub.round(4).to_string())

    # A2 — does market share explain the peer reaction?
    ev["year"] = ev["date"].dt.year
    ev["leader"] = (ev["firm_rank"] == 1).astype(float)
    base = ev[["firm_share", "sub_hhi", "own_ab_d0"]]
    sec_d = pd.get_dummies(ev["sector"], prefix="d_sec", drop_first=True).astype(float)
    big = ev["sub_industry"].map(ev["sub_industry"].value_counts()) >= 5
    sub_d = pd.get_dummies(ev["sub_industry"].where(big, "other"), prefix="d_sub", drop_first=True).astype(float)
    regs = {}
    for y in ["peer_car_d0", "peer_car_0_20"]:
        regs[y] = {
            "share_hhi": fit(ev[y], base),
            "share_hhi_leader": fit(ev[y], pd.concat([base, ev[["leader"]]], axis=1)),
            "sector_only": fit(ev[y], pd.concat([ev[["own_ab_d0"]], sec_d], axis=1)),
            "subind_only": fit(ev[y], pd.concat([ev[["own_ab_d0"]], sub_d], axis=1)),
            "share_hhi_plus_sector": fit(ev[y], pd.concat([base, sec_d], axis=1)),
        }
    log("\nA2 regressions:\n" + json.dumps(regs, indent=1))
    ev["share_tercile"] = pd.qcut(ev["firm_share"], 3, labels=["small share", "mid share", "large share"])
    by_share = ev.groupby("share_tercile", observed=True).apply(summ)
    by_share.to_csv(OUT / "us_by_share_tercile.csv")
    log("\nBy firm's share of its sub-industry:\n" + by_share.round(4).to_string())
    res.update({"by_sector": by_sector.to_dict("index"), "replaceability_map": by_sub.to_dict("index"),
                "regressions": regs, "by_share_tercile": by_share.to_dict("index")})

    # A3 — is replaceability a stable trait of an industry?
    pers = {}
    for level in ["sector", "sub_industry"]:
        a = ev[ev["date"] < SPLIT].groupby(level)
        b = ev[ev["date"] >= SPLIT].groupby(level)
        for col in ["peer_car_d0", "peer_car_0_20"]:
            ma, mb = a[col].mean(), b[col].mean()
            na, nb = a.size(), b.size()
            idx = [g for g in ma.index if g in mb.index and na[g] >= 4 and nb[g] >= 4]
            if len(idx) >= 5:
                pers[f"{level}:{col}"] = {
                    "n_groups": len(idx),
                    "pearson": safe(np.corrcoef(ma[idx], mb[idx])[0, 1]),
                    "spearman": safe(pd.Series(ma[idx]).rank().corr(pd.Series(mb[idx]).rank())),
                }
    log("\nA3 persistence (first half vs second half):\n" + json.dumps(pers, indent=1))
    res["persistence"] = pers

    # A4 — crashes followed by delisting (closest to an actual death)
    dead = ev[ev["delisted_within_60d"]]
    res["delisted_within_60d"] = summ(dead).to_dict() if len(dead) > 2 else {"n_events": len(dead)}
    log(f"\nA4 crashes followed by delisting within 60 days: {len(dead)}")
    if len(dead):
        log(dead[["date", "symbol", "sub_industry", "own_ret_d0", "peer_car_d0", "peer_car_0_20"]]
            .round(4).to_string())
    return res


# ----------------------------------------------------------------------------
# Part B — case studies
# ----------------------------------------------------------------------------
NBFC = ["DHFL", "LICHSGFIN", "PNBHOUSING", "BAJFINANCE", "SRTRANSFIN", "CHOLAFIN",
        "M&MFIN", "EDELWEISS", "REPCOHOME", "CANFINHOME"]
PVT_BANKS = ["ICICIBANK", "AXISBANK", "KOTAKBANK", "INDUSINDBK", "RBLBANK", "HDFCBANK",
             "FEDERALBNK", "IDFCFIRSTB", "BANDHANBNK"]
CASES = [
    dict(id="satyam", market="India", firm="SATYAMCOMP", date="2009-01-07",
         shock="Accounting fraud confession by the chairman",
         groups={"IT services rivals": ["INFY", "TCS", "WIPRO", "HCLTECH", "TECHM", "MPHASIS"]}),
    dict(id="jet_airways", market="India", firm="JETAIRWAYS", date="2019-04-17",
         shock="Airline suspends all flights (cash runs out)",
         groups={"Airline rivals": ["INDIGO", "SPICEJET"]}),
    dict(id="ilfs", market="India", firm=None, date="2018-09-21",
         shock="NBFC panic after IL&FS defaults (IL&FS itself unlisted; day 0 = panic day)",
         groups={"NBFC / housing-finance lenders": NBFC}),
    dict(id="dhfl", market="India", firm="DHFL", date="2019-06-04",  # missed payment 4 June
         shock="DHFL misses bond payments",
         groups={"NBFC / housing-finance lenders": [x for x in NBFC if x != "DHFL"]}),
    dict(id="yes_bank", market="India", firm="YESBANK", date="2020-03-06",
         shock="RBI moratorium on Yes Bank (COVID crash under way: read with care)",
         groups={"Private-bank rivals": PVT_BANKS}),
    dict(id="adani", market="India", firm="ADANIENT", date="2023-01-25",
         shock="Hindenburg short-seller report on the Adani group",
         groups={"Adani group companies": ["ADANIPORTS", "ADANIPOWER", "ADANIGREEN", "ADANIENSOL",
                                           "ACC", "AMBUJACEM"],
                 "Sector rivals (cement, power, ports)": ["ULTRACEMCO", "TATAPOWER", "NTPC",
                                                          "POWERGRID", "GPPL"]}),
    dict(id="pge", market="US", firm="PCG", date="2019-01-14",
         shock="PG&E announces bankruptcy over wildfire liabilities",
         groups={"California utilities (same regulator, same fire risk)": ["EIX", "SRE"]}),
    dict(id="svb", market="US", firm=None, date="2023-03-09",
         shock="SVB collapse (SVB/Signature not in the data; day 0 = SVB's crash day)",
         groups={"Regional-bank peers": ["ZION", "KEY", "CMA", "FITB", "RF", "HBAN", "TFC",
                                         "CFG", "MTB"]}),
]


def run_case(case: dict, rets: pd.DataFrame, dv: pd.DataFrame, universe: pd.DataFrame) -> tuple[list, list]:
    dates = rets.index
    firm = case["firm"]
    # day 0 = first trading day on or after the date the news became public
    d0 = int(dates.searchsorted(pd.Timestamp(case["date"])))
    if firm is not None and (firm not in rets.columns or rets[firm].iloc[d0:d0 + 3].isna().all()):
        firm = None
    allp = {s for g in case["groups"].values() for s in g} | ({firm} if firm else set())
    # peers: a move beyond +/-45% in a day is almost always an unadjusted split/bonus
    peer_cols = [s for s in allp - ({firm} if firm else set()) if s in rets.columns]
    pr = rets[peer_cols]
    bad = pr.iloc[d0 - 260:d0 + 21].abs() > 0.45
    for s in peer_cols:
        for dt in bad.index[bad[s].values]:
            log(f"  [{case['id']}] dropped {s} {dt.date()} return {pr.at[dt, s]:.3f} (likely split/bonus)")
    rets = rets.copy()
    rets[peer_cols] = pr.where(pr.abs() <= 0.45)
    uni = universe.iloc[d0].copy()
    uni[[c for c in allp if c in uni.index]] = False
    mkt = rets.loc[:, uni.values].mean(axis=1)

    def car(series: pd.Series, a: int, b: int) -> float:
        return float(series.iloc[d0 + a:d0 + b + 1].sum())

    def bhar(sym: str, a: int, b: int) -> float:
        """Buy-and-hold return of the stock minus the market over [a, b]."""
        rs = rets[sym].iloc[d0 + a:d0 + b + 1].fillna(0)
        rm = mkt.iloc[d0 + a:d0 + b + 1].fillna(0)
        return float((1 + rs).prod() - (1 + rm).prod())

    firm_ab = (rets[firm] - mkt) if firm else pd.Series(np.nan, index=dates)
    rows, peer_rows = [], []
    for gname, peers in case["groups"].items():
        avail = [s for s in peers if s in rets.columns and rets[s].iloc[d0 - 250:d0].notna().sum() > 100]
        pab_each = rets[avail].sub(mkt, axis=0)
        pab = pab_each.mean(axis=1)
        sd = pab.iloc[d0 - 260:d0 - 10].std()
        row = {"case": case["id"], "market": case["market"], "shock": case["shock"], "firm": firm,
               "news_date": case["date"], "day0": str(dates[d0].date()), "peer_group": gname,
               "n_peers": len(avail), "peers_used": " ".join(avail),
               "peers_missing": " ".join(s for s in peers if s not in avail),
               "firm_ret_d0": float(rets[firm].iloc[d0]) if firm else np.nan,
               "firm_bhar_0_20": bhar(firm, 0, 20) if firm else np.nan}
        for a, b in [(0, 0), (0, 5), (0, 20), (-20, -1)]:
            v = car(pab, a, b)
            row[f"peer_car_{a}_{b}"] = v
            row[f"t_{a}_{b}"] = v / (sd * np.sqrt(b - a + 1)) if sd > 0 else np.nan
        row["peer_bhar_0_20"] = float(np.mean([bhar(s, 0, 20) for s in avail])) if avail else np.nan
        row["pct_peers_up_0_20"] = float(np.mean([bhar(s, 0, 20) > 0 for s in avail])) if avail else np.nan
        rows.append(row)
        for s in avail:
            peer_rows.append({"case": case["id"], "peer_group": gname, "peer": s,
                              "car_0_0": car(pab_each[s], 0, 0), "car_0_5": car(pab_each[s], 0, 5),
                              "bhar_0_20": bhar(s, 0, 20), "car_pre_20": car(pab_each[s], -20, -1)})
    return rows, peer_rows


def part_b(us: tuple, india: tuple) -> dict:
    log("Part B: case studies")
    rows, peers = [], []
    for case in CASES:
        rets, dv, uni = us if case["market"] == "US" else india
        r, pr = run_case(case, rets, dv, uni)
        rows += r
        peers += pr
    df, pdf = pd.DataFrame(rows), pd.DataFrame(peers)
    df.to_csv(OUT / "cases.csv", index=False)
    pdf.to_csv(OUT / "cases_peers.csv", index=False)
    show = ["case", "peer_group", "day0", "n_peers", "firm_ret_d0", "firm_bhar_0_20",
            "peer_car_0_0", "t_0_0", "peer_car_0_5", "t_0_5", "peer_car_0_20", "t_0_20",
            "peer_bhar_0_20", "pct_peers_up_0_20", "peer_car_-20_-1"]
    log("\n" + df[show].round(3).to_string())
    log("\nPer-peer CARs:\n" + pdf.round(3).to_string())
    return {"cases": df.to_dict("records"), "peers": pdf.to_dict("records")}


def main() -> None:
    summary = {}
    log("Loading US (raw, $1 floor)")
    rets, dv = load(DATA / "extended_prices.parquet", 1.0)
    mask = us_pit_mask(rets)
    summary["part_a"] = part_a(rets, mask, dv)
    us = (rets, dv, mask)

    log("Loading India (NSE survivorship-free bhavcopy + adjusted Yahoo closes)")
    rin, dvin = load(DATA / "nse_survivorship_free.parquet", None)
    # The bhavcopy panel misses some split/bonus adjustments (CHOLAFIN 2019, INFY
    # bonuses) and lacks INFY before 2012 and SPICEJET before 2020. Prefer the
    # adjusted Yahoo closes where a stock has them; fall back to bhavcopy for
    # delisted firms (Satyam, Jet Airways, DHFL ...). Universe/size from bhavcopy.
    ry, _ = load(DATA / "nse_prices_clean.parquet", None)
    cols = rin.columns.union(ry.columns)
    rin = ry.reindex(index=rin.index, columns=cols).combine_first(rin.reindex(columns=cols))
    dvin = dvin.reindex(columns=cols)
    dvbar = dvin.rolling(63, min_periods=20).mean().shift(1)
    top = dvbar.rank(axis=1, ascending=False) <= 300
    uni_in = top & rin.notna()
    summary["part_b"] = part_b(us, (rin, dvin, uni_in))

    with open(OUT / "summary.json", "w") as f:
        json.dump(summary, f, indent=2,
                  default=lambda o: safe(o) if isinstance(o, (np.integer, np.floating)) else str(o))
    log("Done. Results in results/death_test/")


if __name__ == "__main__":
    main()
