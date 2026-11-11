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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["select"])
    a = ap.parse_args()
    if a.stage == "select":
        select()


if __name__ == "__main__":
    main()
