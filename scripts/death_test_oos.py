"""
Pre-registered out-of-sample "death test" (2026-11-11).

Rules: docs/entropy_research/PREREGISTRATION.md. Part 1 (the rules) was committed
before this script first ran.

Stage `select`
    Finds candidate collapses (PREREGISTRATION §3) from each firm's OWN returns and
    the market return only. No rival returns are computed here.
    Output: results/death_test_oos/candidates_{india,us}.csv (+ _all versions
    before the size cap) and selection.log.

Stage `universe`
    Lists, for each news-checked case, the names that were in the universe on day 0
    with their traded value (India) or the S&P members of the sub-industry (US), so
    rivals can be picked from names only. No returns.

Stage `run` is added together with the Part 2 commit of PREREGISTRATION.md.

Run:  ~/.venvs/strategyhub/bin/python scripts/death_test_oos.py select
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from death_test import CASES, load, load_india  # noqa: E402
from entropy_research import DATA, log, us_pit_mask  # noqa: E402

OUT = ROOT / "results" / "death_test_oos"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20261111
CAP = 60
WIN = 20            # route-1 window length (trading days)
FOLLOW = 21         # trading days of data required after the window
EPISODE = 250       # one event per stock per 250 trading days
EXIT_WIN = 60       # route-2 look-back
EXCL = 60           # exclusion radius around the eight used cases
HOLE = (pd.Timestamp("2011-06-22"), pd.Timestamp("2012-01-31"))
START = {"India": pd.Timestamp("2006-01-02"), "US": pd.Timestamp("2000-01-03")}
LAST_START = pd.Timestamp("2024-12-31")


def gross(R: np.ndarray, w: int) -> tuple[np.ndarray, np.ndarray]:
    """Compounded gross return and count of valid returns over every w-day window.

    Row t of the output covers rows t .. t+w-1 of R. Missing returns count as 0.
    """
    valid = np.isfinite(R)
    lr = np.log1p(np.where(valid, R, 0.0))
    cs = np.vstack([np.zeros((1,) + lr.shape[1:]), np.cumsum(lr, axis=0)])
    cv = np.vstack([np.zeros((1,) + lr.shape[1:]), np.cumsum(valid, axis=0)])
    return np.exp(cs[w:] - cs[:-w]), cv[w:] - cv[:-w]


def used_case_windows(dates: pd.DatetimeIndex, market: str) -> list[tuple[int, set, str]]:
    out = []
    for c in CASES:
        if c["market"] != market:
            continue
        d0 = int(dates.searchsorted(pd.Timestamp(c["date"])))
        syms = {s for g in c["groups"].values() for s in g} | ({c["firm"]} if c["firm"] else set())
        out.append((d0, syms, c["id"]))
    return out


def find(R: pd.DataFrame, U: pd.DataFrame, dv: pd.DataFrame, market: str) -> pd.DataFrame:
    dates, cols = R.index, R.columns
    T = len(dates)
    Rv = R.values
    inU = U.values.astype(bool)
    inU = inU | np.vstack([np.zeros((1, inU.shape[1]), bool), inU[:-1]])  # day t or t-1
    mkt = R.where(U).mean(axis=1).fillna(0.0).values
    dvbar = dv.reindex_like(R).rolling(63, min_periods=20).mean().shift(1)
    rank = dvbar.rank(axis=1, ascending=False).values

    Gs, nv = gross(Rv, WIN)
    Gm, _ = gross(mkt[:, None], WIN)
    bhar = Gs - Gm                                   # row t = window t..t+19
    t_idx = np.arange(len(bhar))
    end = t_idx + WIN - 1
    ok_t = (dates[t_idx] >= START[market]) & (dates[t_idx] <= LAST_START) & (end + FOLLOW <= T - 1)
    hole = (dates[np.minimum(end, T - 1)] >= HOLE[0]) & (dates[t_idx] <= HOLE[1])
    ok_t &= ~hole
    hit = (bhar < -0.50) & (nv >= 10) & inU[: len(bhar)] & ok_t[:, None]

    rows = []
    for j, c in enumerate(cols):
        last = -10 ** 9
        for t in np.where(hit[:, j])[0]:
            if t - last < EPISODE:
                continue
            last = t
            w = Rv[t:t + WIN, j]
            k = int(np.nanargmin(np.where(np.isfinite(w), w, np.inf)))
            rows.append({"market": market, "route": 1, "symbol": c,
                         "win_start": dates[t].date(), "win_end": dates[t + WIN - 1].date(),
                         "bhar_win": bhar[t, j], "own_bh": Gs[t, j] - 1, "mkt_bh": Gm[t, 0] - 1,
                         "worst_day": dates[t + k].date(), "worst_ret": w[k],
                         "dv_rank_start": rank[t, j], "t": t})

    # Route 2: the stock stops trading after a fall
    last_valid = R.apply(lambda s: s.last_valid_index())
    for j, c in enumerate(cols):
        lv = last_valid[c]
        if lv is None or pd.isna(lv):
            continue
        L = dates.get_loc(lv)
        if L > T - 1 - EXIT_WIN or L - EXIT_WIN + 1 < 0:
            continue
        a = L - EXIT_WIN + 1
        if dates[L] < START[market] or dates[a] > LAST_START:
            continue
        if not inU[a:L + 1, j].any():
            continue
        if (dates[L] >= HOLE[0]) and (dates[a] <= HOLE[1]):
            continue
        g = np.nanprod(1 + Rv[a:L + 1, j]) - np.prod(1 + mkt[a:L + 1])
        if g >= -0.30:
            continue
        rows.append({"market": market, "route": 2, "symbol": c,
                     "win_start": dates[a].date(), "win_end": dates[L].date(),
                     "bhar_win": g, "own_bh": np.nanprod(1 + Rv[a:L + 1, j]) - 1,
                     "mkt_bh": np.prod(1 + mkt[a:L + 1]) - 1, "worst_day": pd.NaT,
                     "worst_ret": np.nan, "dv_rank_start": rank[a, j], "t": a})
    ev = pd.DataFrame(rows).sort_values(["symbol", "t"]).reset_index(drop=True)

    # merge a route-2 exit into a route-1 episode of the same stock that ends <= 60 days before it
    keep = []
    for sym, g in ev.groupby("symbol", sort=False):
        r1 = g[g["route"] == 1]
        for i, r in g.iterrows():
            if r["route"] == 2 and len(r1):
                ends = r1["t"] + WIN - 1
                last_ret = r["t"] + EXIT_WIN - 1
                if ((last_ret - ends >= 0) & (last_ret - ends <= EXIT_WIN)).any():
                    ev.loc[r1.index[(last_ret - ends >= 0) & (last_ret - ends <= EXIT_WIN)], "route"] = 12
                    continue
            keep.append(i)
    ev = ev.loc[keep].copy()

    # exclusions: the eight used cases
    ev["excluded_by"] = ""
    for d0, syms, cid in used_case_windows(dates, market):
        near = (ev["symbol"].isin(syms)) & ((ev["t"] - d0).abs() <= EXCL)
        ev.loc[near, "excluded_by"] = cid
    return ev.sort_values("t").reset_index(drop=True)


def select() -> None:
    lines = []

    def say(msg: str) -> None:
        log(msg)
        lines.append(msg)

    rin, dvin, uni_in = load_india()
    log("Loading US (raw, $1 floor)")
    rus, dvus = load(DATA / "extended_prices.parquet", 1.0)
    mask = us_pit_mask(rus)
    top = dvin.rolling(63, min_periods=20).mean().shift(1).rank(axis=1, ascending=False) <= 300
    for market, (R, U, dv) in {"India": (rin, top, dvin), "US": (rus, mask, dvus)}.items():
        ev = find(R, U, dv, market)
        ev.to_csv(OUT / f"candidates_{market.lower()}_all.csv", index=False)
        n_ex = int((ev["excluded_by"] != "").sum())
        pool = ev[ev["excluded_by"] == ""]
        say(f"{market}: {len(ev)} candidates (route 1: {int((ev['route'] == 1).sum())}, "
            f"route 2 only: {int((ev['route'] == 2).sum())}, both: {int((ev['route'] == 12).sum())}); "
            f"{n_ex} excluded as part of the eight used cases; {len(pool)} remain")
        if len(pool) > CAP:
            pool = pool.sample(CAP, random_state=SEED).sort_values("t")
            say(f"  size cap: random sample of {CAP} drawn (seed {SEED})")
        pool.drop(columns="t").to_csv(OUT / f"candidates_{market.lower()}.csv", index=False)
    (OUT / "selection.log").write_text("\n".join(lines) + "\n")


# ----------------------------------------------------------------------------
# Stage `universe` — who was in the universe on day 0 (names and size only)
# ----------------------------------------------------------------------------
def universe(market: str, day0: str, symbols: list) -> None:
    """Membership, traded-value rank and count of PRE-day-0 returns. No returns after day 0."""
    if market == "India":
        R, dv, U = load_india()
        top = dv.rolling(63, min_periods=20).mean().shift(1)
    else:
        R, dv = load(DATA / "extended_prices.parquet", 1.0)
        U = us_pit_mask(R)
        top = dv.rolling(63, min_periods=20).mean().shift(1)
    d0 = int(R.index.searchsorted(pd.Timestamp(day0)))
    rank = top.iloc[d0].where(U.iloc[d0]).rank(ascending=False)
    print(f"{market} day 0 = {R.index[d0].date()}; universe size {int(U.iloc[d0].sum())}")
    if not symbols:
        print(" ".join(rank.dropna().sort_values().index))
        return
    for s in symbols:
        if s not in R.columns:
            print(f"  {s:12s} not in data")
            continue
        n = int(R[s].iloc[max(d0 - 250, 0):d0].notna().sum())
        print(f"  {s:12s} in universe: {bool(U[s].iloc[d0])!s:5s} rank {rank.get(s, np.nan):6.0f}  "
              f"pre-day-0 returns: {n}")


# ----------------------------------------------------------------------------
# Stage `run` — written and committed with PREREGISTRATION Part 2, before it ran
# ----------------------------------------------------------------------------
CASE_FILE = ROOT / "docs" / "entropy_research" / "oos_cases.csv"
NPERM = 20000
CRISIS = [("2008-01-01", "2009-12-31"), ("2020-02-01", "2020-04-30")]


def outcome(rets: pd.DataFrame, uni: pd.DataFrame, dvbar: pd.DataFrame, d0: int, firm: str,
            peers: list, exclude: set, tag: str, logs: list) -> tuple[dict, list]:
    """PREREGISTRATION §6: rival BHAR over days 0-20 against the equal-weighted universe."""
    avail = [s for s in peers if s in rets.columns and rets[s].iloc[max(d0 - 250, 0):d0].notna().sum() >= 100]
    pr = rets[avail].copy()
    win = pr.iloc[max(d0 - 260, 0):d0 + 21]
    bad = win.abs() > 0.45
    for s in avail:
        for dt in bad.index[bad[s].values]:
            logs.append(f"  [{tag}] dropped {s} {dt.date()} return {pr.at[dt, s]:.3f} (likely corporate action)")
    pr = pr.where(pr.abs() <= 0.45)
    u = uni.iloc[d0].copy()
    u[[c for c in (exclude | {firm}) if c in u.index]] = False
    mkt = rets.loc[:, u.values].mean(axis=1)
    m = mkt.iloc[d0:d0 + 21].fillna(0)
    est = slice(max(d0 - 260, 0), d0 - 10)
    rows = []
    for s in avail:
        r = pr[s].iloc[d0:d0 + 21].fillna(0)
        x = pd.concat([pr[s].iloc[est], mkt.iloc[est]], axis=1).dropna()
        beta = np.cov(x.iloc[:, 0], x.iloc[:, 1])[0, 1] / x.iloc[:, 1].var() if len(x) > 60 else 1.0
        ab = pr[s] - mkt
        rows.append({"peer": s, "bhar_0_20": (1 + r).prod() - (1 + m).prod(),
                     "bhar_mm_0_20": (1 + r).prod() - (1 + beta * m).prod(), "beta": beta,
                     "car_0_0": ab.iloc[d0], "car_0_5": ab.iloc[d0:d0 + 6].sum()})
    p = pd.DataFrame(rows)
    fs = dvbar[firm].iloc[d0] if firm in dvbar.columns else np.nan
    ps = dvbar[avail].iloc[d0].sum() if avail else np.nan
    res = {"n_peers": len(avail), "peers_used": " ".join(avail),
           "peers_missing": " ".join(s for s in peers if s not in avail)}
    if len(p):
        res.update({"bhar_0_20": p["bhar_0_20"].mean(), "bhar_mm_0_20": p["bhar_mm_0_20"].mean(),
                    "median_bhar_0_20": p["bhar_0_20"].median(),
                    "pct_peers_neg": (p["bhar_0_20"] < 0).mean(),
                    "car_0_0": np.nanmean(p["car_0_0"]), "car_0_5": np.nanmean(p["car_0_5"]),
                    "firm_share": fs / (fs + ps) if np.isfinite(fs) and ps > 0 else np.nan})
    return res, rows


def perm_test(y: np.ndarray, sd: np.ndarray, rng) -> tuple[float, float]:
    """One-sided: is mean(SD) - mean(OR) more negative than chance?"""
    obs = y[sd].mean() - y[~sd].mean()
    k, n = sd.sum(), len(y)
    diffs = np.empty(NPERM)
    for i in range(NPERM):
        idx = rng.permutation(n)
        diffs[i] = y[idx[:k]].mean() - y[idx[k:]].mean()
    return obs, float((diffs <= obs).mean())


def tests(df: pd.DataFrame, col: str = "bhar_0_20") -> dict:
    from scipy import stats
    d = df.dropna(subset=[col])
    sd = (d["label"] == "SD").values
    y = d[col].values
    hit = np.where(sd, y < 0, y >= 0)
    out = {"n": len(d), "n_SD": int(sd.sum()), "n_OR": int((~sd).sum()),
           "mean_SD": float(y[sd].mean()) if sd.any() else np.nan,
           "mean_OR": float(y[~sd].mean()) if (~sd).any() else np.nan,
           "hit_rate": float(hit.mean()) if len(d) else np.nan,
           "hit_rate_SD": float(hit[sd].mean()) if sd.any() else np.nan,
           "hit_rate_OR": float(hit[~sd].mean()) if (~sd).any() else np.nan}
    if sd.sum() >= 3 and (~sd).sum() >= 3:
        obs, p = perm_test(y, sd, np.random.default_rng(SEED))
        tab = [[int((y[sd] < 0).sum()), int((y[sd] >= 0).sum())],
               [int((y[~sd] < 0).sum()), int((y[~sd] >= 0).sum())]]
        out.update({"diff": obs, "perm_p": p,
                    "fisher_p": float(stats.fisher_exact(tab, alternative="greater")[1])})
    return out


def verdict(t: dict) -> str:
    if t["n_SD"] < 5 or t["n_OR"] < 5:
        return "too few cases to test"
    if t["perm_p"] >= 0.05:
        return "not supported"
    if t["hit_rate_SD"] > 0.5 and t["hit_rate_OR"] > 0.5:
        return "supported"
    return "partly supported"


def works(t: dict) -> bool:
    """PREREGISTRATION §7 T3 definition of 'works' in a subgroup."""
    if t["n_SD"] >= 3 and t["n_OR"] >= 3:
        return bool(t["diff"] < 0 and t["hit_rate_SD"] > 0.5 and t["hit_rate_OR"] > 0.5)
    if t["n_SD"] >= 3:
        return bool(t["hit_rate_SD"] >= 2 / 3)
    if t["n_OR"] >= 3:
        return bool(t["hit_rate_OR"] >= 2 / 3)
    return False


def run(case_file: Path = CASE_FILE, out_dir: Path = OUT) -> None:
    import json
    from scipy import stats
    cases = pd.read_csv(case_file, dtype=str).fillna("")
    logs: list = []
    rin, dvin, uni_in = load_india()
    rus, dvus = load(DATA / "extended_prices.parquet", 1.0)
    mask = us_pit_mask(rus)
    data = {"India": (rin, uni_in, dvin.rolling(63, min_periods=20).mean().shift(1)),
            "US": (rus, mask, dvus.rolling(63, min_periods=20).mean().shift(1))}
    rows, peer_rows = [], []
    for _, c in cases[cases["status"].isin(["case", "industry_shock"])].iterrows():
        R, U, dvb = data[c["market"]]
        d0 = int(R.index.searchsorted(pd.Timestamp(c["day0"])))
        rivals, group = c["rivals"].split(), c["group"].split()
        excl = set(rivals) | set(group)
        for kind, peers in [("rivals", rivals), ("group", group)]:
            if not peers:
                continue
            res, pr = outcome(R, U, dvb, d0, c["symbol"], peers, excl, f"{c['case_id']}:{kind}", logs)
            rows.append({**{k: c[k] for k in ["case_id", "market", "symbol", "status", "day0", "financial",
                                               "label", "channel"]},
                         "peer_set": kind, "day0_used": str(R.index[d0].date()), **res})
            peer_rows += [{"case_id": c["case_id"], "peer_set": kind, **p} for p in pr]
    out = pd.DataFrame(rows)
    out.to_csv(out_dir / "outcomes.csv", index=False)
    pd.DataFrame(peer_rows).to_csv(out_dir / "outcomes_peers.csv", index=False)

    main_set = out[(out["status"] == "case") & (out["peer_set"] == "rivals") & (out["n_peers"] >= 3)].copy()
    res = {"T1_T2": tests(main_set)}
    res["verdict_H1"] = verdict(res["T1_T2"])
    fin = main_set[main_set["financial"] == "Y"]
    non = main_set[main_set["financial"] != "Y"]
    res["T3_financial"], res["T3_nonfinancial"] = tests(fin), tests(non)
    wf, wn = works(res["T3_financial"]), works(res["T3_nonfinancial"])
    res["T3_meaning"] = ("general claim stands" if wf and wn else
                         "claim narrows to financial contagion" if wf else
                         "works only outside financials" if wn else "rule fails out of sample")
    grp = out[(out["status"] == "case") & (out["peer_set"] == "group") & (out["n_peers"] >= 2)]
    if len(grp):
        k = int((grp["bhar_0_20"] < 0).sum())
        res["T4_group"] = {"n": len(grp), "mean": float(grp["bhar_0_20"].mean()), "n_neg": k,
                           "sign_p": float(stats.binomtest(k, len(grp), 0.5, alternative="greater").pvalue)}
    s = main_set.dropna(subset=["firm_share", "bhar_0_20"])
    if len(s) >= 8:
        rho, p = stats.spearmanr(s["firm_share"], s["bhar_0_20"])
        X = np.column_stack([np.ones(len(s)), (s["label"] == "SD").astype(float), s["firm_share"]])
        y = s["bhar_0_20"].values
        xtx = np.linalg.pinv(X.T @ X)
        b = xtx @ X.T @ y
        u = y - X @ b
        cov = xtx @ (X * u[:, None] ** 2).T @ X @ xtx * len(y) / (len(y) - 3)
        t = b / np.sqrt(np.diag(cov))
        res["T5_share"] = {"n": len(s), "spearman_share": float(rho), "spearman_p": float(p),
                           "coef_SD": float(b[1]), "t_SD": float(t[1]),
                           "coef_share": float(b[2]), "t_share": float(t[2])}
    rob = {}
    for col in ["bhar_mm_0_20", "median_bhar_0_20", "car_0_0", "car_0_5"]:
        rob[col] = tests(main_set, col)
    crisis = np.zeros(len(main_set), bool)
    for a, b_ in CRISIS:
        crisis |= main_set["day0_used"].between(a, b_).values
    rob["ex_crises"] = tests(main_set[~crisis])
    rob["US_only"] = tests(main_set[main_set["market"] == "US"])
    rob["India_only"] = tests(main_set[main_set["market"] == "India"])
    ind = out[(out["status"] == "industry_shock") & (out["peer_set"] == "rivals")]
    rob["industry_shocks"] = {"n": len(ind), "mean_bhar_0_20": float(ind["bhar_0_20"].mean()) if len(ind) else None}
    res["robustness"] = rob
    with open(out_dir / "tests.json", "w") as f:
        json.dump(res, f, indent=2, default=float)
    (out_dir / "run.log").write_text("\n".join(logs) + "\n")
    log(json.dumps(res, indent=1, default=float))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["select", "universe", "run"])
    ap.add_argument("--market", default="India")
    ap.add_argument("--day0", default=None)
    ap.add_argument("--symbols", nargs="*", default=[])
    ap.add_argument("--cases", type=Path, default=CASE_FILE, help="case file (testing only)")
    ap.add_argument("--out", type=Path, default=OUT, help="output folder (testing only)")
    a = ap.parse_args()
    if a.stage == "select":
        select()
    elif a.stage == "universe":
        universe(a.market, a.day0, a.symbols)
    else:
        a.out.mkdir(parents=True, exist_ok=True)
        run(a.cases, a.out)


if __name__ == "__main__":
    main()
