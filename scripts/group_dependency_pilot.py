"""
Paper 2 pilot: business groups and hidden concentration (India).
Plan: docs/group_dependency/PILOT_PLAN.md · Rules: docs/group_dependency/PREREGISTRATION.md

Subcommands, in the order the pre-registration fixes (each step is committed first):

  universe   Phase 2. Symbol universe from TRADED VALUE ONLY (close x volume); no returns.
             -> results/group_dependency/universe.csv
  events     Part 2. Select crash events from the TRIGGER firms' own returns only
             (PREREGISTRATION §3) and draw the random news-check sample (§3.4).
             No comparison stock's return, correlation or outcome is computed.
             -> events.csv, news_sample.csv, removed_returns.csv
  run        Part 3. The pre-registered tests (§6-§8), once.
             -> pairs.parquet, tests.json, tail_pairs_summary.csv, ...

Run:  ~/.venvs/strategyhub/bin/python scripts/group_dependency_pilot.py <step>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data_processed"
PANEL = DATA / "nse_survivorship_free_adj.parquet"
OUT = ROOT / "results" / "group_dependency"
OUT.mkdir(parents=True, exist_ok=True)
CA_SUSPECTS = ROOT / "results" / "nse_data_audit" / "corporate_action_suspects.csv"

TOP_N = 500
START, END = "2005-01-01", "2025-12-31"
SEED = 20261111
MAIN_TYPES = {"Family", "Corporate"}
WIDE_TYPES = {"Family", "Corporate", "MNC", "State", "PE"}
HOLE = (pd.Timestamp("2011-06-22"), pd.Timestamp("2012-01-31"))
EV_FIRST, EV_LAST = pd.Timestamp("2006-01-02"), pd.Timestamp("2025-05-30")
OWN_THR, AB_THR, REV_THR, MAX_ABS = -0.15, -0.12, 0.25, 0.45
CALM_LEN, CALM_END, CALM_MIN = 252, 10, 150     # days -261..-10, >=150 paired obs
WIN, WIN_MIN = 20, 15                           # days 0..+20, >=15 valid returns
EPISODE = 20
PAPER1_EPISODES = [("Adani", "2023-01-25"), ("Reliance ADAG (Anil Ambani)", "2019-02-04"),
                   ("Reliance ADAG (Anil Ambani)", "2019-06-12"),
                   ("Indiabulls (Sameer Gehlaut)", "2019-09-06")]


def log(msg: str) -> None:
    print(msg, flush=True)


def safe(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return x
    return None if not np.isfinite(x) else x


# ----------------------------------------------------------------------------
# Phase 2: universe from traded value only
# ----------------------------------------------------------------------------
def traded_value_panel() -> pd.DataFrame:
    raw = pd.read_parquet(PANEL, columns=["date", "symbol", "close", "volume"])
    raw["date"] = pd.to_datetime(raw["date"])
    raw["tv"] = raw["close"] * raw["volume"]
    return raw.pivot_table(index="date", columns="symbol", values="tv")


def build_universe() -> pd.DataFrame:
    tv = traded_value_panel()
    tv63 = tv.rolling(63, min_periods=40).mean()
    per = tv63.index.to_period("M")
    month_end = tv63.index[np.append(np.where(per[1:] != per[:-1])[0], len(per) - 1)]
    me = tv63.loc[month_end].loc[START:END]
    rank = me.rank(axis=1, ascending=False)
    inn = rank <= TOP_N
    rows = []
    for s in inn.columns[inn.any()]:
        months = inn.index[inn[s]]
        rows.append({"symbol": s, "first_top500": months.min().date().isoformat(),
                     "last_top500": months.max().date().isoformat(),
                     "n_months_top500": int(len(months)), "best_rank": int(rank[s].min()),
                     "first_trade": tv[s].first_valid_index().date().isoformat(),
                     "last_trade": tv[s].last_valid_index().date().isoformat(),
                     "median_tv63_cr": float(me.loc[months, s].median() / 1e7)})
    u = pd.DataFrame(rows).sort_values("best_rank").reset_index(drop=True)
    u.to_csv(OUT / "universe.csv", index=False)
    log(f"universe: {len(u)} symbols ever in the top {TOP_N} at a month-end")
    return u


# ----------------------------------------------------------------------------
# Shared loaders (PREREGISTRATION §2)
# ----------------------------------------------------------------------------
def etf_symbols() -> set:
    gm = pd.read_csv(OUT / "group_map.csv", dtype=str).fillna("")
    return set(gm.loc[gm["group"] == "ETF (not a company)", "symbol"])


class Panel:
    def __init__(self) -> None:
        raw = pd.read_parquet(PANEL, columns=["date", "symbol", "close", "volume"])
        raw["date"] = pd.to_datetime(raw["date"])
        etfs = etf_symbols()
        raw = raw[~raw["symbol"].isin(etfs)]
        log(f"  dropped {len(etfs)} ETF / fund-unit symbols from the panel")
        close = raw.pivot_table(index="date", columns="symbol", values="close").sort_index()
        vol = raw.pivot_table(index="date", columns="symbol", values="volume").reindex_like(close)
        rets = close.pct_change(fill_method=None)
        gap = close.index.to_series().diff().dt.days
        hole_rows = gap[gap > 10].index
        rets.loc[hole_rows] = np.nan
        log(f"  set {len(hole_rows)} date(s) to missing for a >10-day gap: "
            f"{[str(d.date()) for d in hole_rows]}")
        big = rets.abs() > MAX_ABS
        removed = rets[big].stack().rename("ret").reset_index()
        removed.columns = ["date", "symbol", "ret"]
        removed.to_csv(OUT / "removed_returns.csv", index=False)
        log(f"  removed {len(removed)} one-day returns beyond ±45% (removed_returns.csv)")
        self.rets = rets.where(~big)
        self.tv = (close * vol).where(close.notna())
        self.tv63raw = self.tv.rolling(63, min_periods=40).mean()
        self.tv63 = self.tv63raw.shift(1)                      # lagged one day
        self.uni = (self.tv63.rank(axis=1, ascending=False) <= TOP_N) & self.rets.notna()
        self.mkt = self.rets.where(self.uni).mean(axis=1)
        self.ar = self.rets.sub(self.mkt, axis=0)
        self.dates = self.rets.index
        self.syms = self.rets.columns
        self.col = {s: k for k, s in enumerate(self.syms)}


class GroupMap:
    def __init__(self, syms) -> None:
        gm = pd.read_csv(OUT / "group_map.csv", dtype=str).fillna("")
        gm["start"] = pd.to_datetime(gm["start"])
        gm["end"] = pd.to_datetime(gm["end"])
        self.gm = gm
        self.industry = gm.groupby("symbol")["industry"].first().to_dict()
        self.same_co: dict[str, set] = {}
        for s, o in zip(gm["symbol"], gm["same_company_as"]):
            for x in [t.strip() for t in o.replace(";", " ").split() if t.strip()]:
                self.same_co.setdefault(s, set()).add(x)
                self.same_co.setdefault(x, set()).add(s)
        self.rows = {s: g.sort_values("start") for s, g in gm.groupby("symbol")}
        missing = [s for s in syms if s not in self.rows]
        if missing:
            log(f"  {len(missing)} panel symbols are not in the group map (not in the universe)")

    def at(self, sym: str, t: pd.Timestamp) -> tuple[str, str, str]:
        g = self.rows.get(sym)
        if g is None:
            return "", "", ""
        m = g[(g["start"] <= t) & (g["end"] >= t)]
        if len(m) == 0:
            return "", "", ""
        r = m.iloc[-1]
        return r["group"], r["group_type"], r["confidence"]

    def frame_at(self, t: pd.Timestamp) -> pd.DataFrame:
        m = self.gm[(self.gm["start"] <= t) & (self.gm["end"] >= t)]
        return m.drop_duplicates("symbol", keep="last").set_index("symbol")


def touches_hole(dates: pd.DatetimeIndex, p: int) -> bool:
    lo, hi = dates[max(p - 1, 0)], dates[min(p + WIN, len(dates) - 1)]
    return not (hi < HOLE[0] or lo > HOLE[1])


# ----------------------------------------------------------------------------
# Part 2: events from trigger returns only (PREREGISTRATION §3)
# ----------------------------------------------------------------------------
def select_events() -> pd.DataFrame:
    log("Loading panel")
    P = Panel()
    G = GroupMap(P.syms)
    ca = pd.read_csv(CA_SUSPECTS, usecols=["symbol", "date", "verdict"])
    ca = ca[ca["verdict"].isin(["UNCERTAIN", "BAD_TICK", "CA_LIKELY_NICE", "CA_CONFIRMED_YAHOO"])]
    ca_set = set(zip(ca["symbol"], pd.to_datetime(ca["date"])))
    R, U, A = P.rets.values, P.uni.values, P.ar.values
    ind = np.array([G.industry.get(s, "") for s in P.syms])
    cand = np.argwhere(U & (R <= OWN_THR) & (A <= AB_THR))
    log(f"  {len(cand)} universe stock-days with return <= -15% and AR <= -12%")
    rows, drop = [], {}

    def dropped(k):
        drop[k] = drop.get(k, 0) + 1

    for p, j in cand:
        t, s = P.dates[p], P.syms[j]
        grp, gtype, conf = G.at(s, t)
        if gtype not in MAIN_TYPES:
            dropped("not a Family/Corporate group firm")
            continue
        fr = G.frame_at(t)
        members = [m for m in fr.index[fr["group"] == grp] if m in P.col]
        same_co = G.same_co.get(s, set())
        sibs_u = [m for m in members if m != s and m not in same_co and U[p, P.col[m]]]
        if not sibs_u:
            dropped("no other group firm in the universe on day 0")
            continue
        same_ind = (ind == ind[j]) & U[p] & ~np.isin(P.syms, members)
        n_ind = int(same_ind.sum())
        ind_adj = R[p, j] - np.nanmean(R[p, same_ind]) if n_ind >= 3 else np.nan
        if n_ind >= 3 and not ind_adj <= AB_THR:
            dropped("industry-adjusted return above -12%")
            continue
        nxt = R[p + 1, j] if p + 1 < len(P.dates) else np.nan
        if np.isfinite(nxt) and nxt > REV_THR:
            dropped("next-day reversal above +25%")
            continue
        if (s, t) in ca_set:
            dropped("in the corporate-action audit list")
            continue
        if t < EV_FIRST or t > EV_LAST or p + WIN >= len(P.dates):
            dropped("day 0 outside 2006-01-02 .. 2025-05-30")
            continue
        if touches_hole(P.dates, p):
            dropped("window touches the 2011 hole")
            continue
        rows.append({"pos": int(p), "date": t, "symbol": s, "group": grp, "group_type": gtype,
                     "group_confidence": conf, "industry": ind[j], "own_ret_d0": R[p, j],
                     "own_ar_d0": A[p, j], "ind_adj_d0": ind_adj, "n_industry_ex_group": n_ind,
                     "n_group_in_universe": len(sibs_u) + 1, "next_day_ret": nxt,
                     "tv63_lag": P.tv63.values[p, j]})
    q = pd.DataFrame(rows).sort_values(["group", "pos", "tv63_lag"], ascending=[True, True, False])
    log(f"  qualifying days: {len(q)}; dropped: {json.dumps(drop)}")
    keep, n_same_day, n_in_episode = [], 0, 0
    for grp, g in q.groupby("group", sort=False):
        start = -10 ** 9
        for _, r in g.iterrows():
            if r["pos"] == start:
                n_same_day += 1
                continue
            if r["pos"] - start <= EPISODE:
                n_in_episode += 1
                continue
            start = r["pos"]
            keep.append(r)
    ev = pd.DataFrame(keep).sort_values("pos").reset_index(drop=True)
    ev.insert(0, "event_id", [f"E{k:04d}" for k in range(1, len(ev) + 1)])
    ev["date"] = pd.to_datetime(ev["date"]).dt.date
    ev.to_csv(OUT / "events.csv", index=False)
    log(f"  events: {len(ev)} from {ev['group'].nunique()} groups "
        f"(same-day co-qualifiers folded in: {n_same_day}; later days inside an episode: {n_in_episode})")
    rng = np.random.default_rng(SEED)
    take = ev if len(ev) <= 30 else ev.iloc[np.sort(rng.choice(len(ev), 30, replace=False))]
    ns = take[["event_id", "date", "symbol", "group", "industry", "own_ret_d0"]].copy()
    for c in ["news_label", "news_summary", "news_source"]:
        ns[c] = ""
    ns.to_csv(OUT / "news_sample.csv", index=False)
    with open(OUT / "events_summary.json", "w") as f:
        json.dump({"n_candidate_stock_days": int(len(cand)), "dropped": drop,
                   "n_qualifying_days": int(len(q)), "n_same_day_folded": n_same_day,
                   "n_inside_episode": n_in_episode, "n_events": int(len(ev)),
                   "n_groups": int(ev["group"].nunique()),
                   "events_per_year": ev.groupby(pd.to_datetime(ev["date"]).dt.year).size().to_dict()},
                  f, indent=2, default=str)
    return ev


# ----------------------------------------------------------------------------
# Part 3: the pre-registered tests
# ----------------------------------------------------------------------------
def build_pairs(P: Panel, G: GroupMap, ev: pd.DataFrame) -> pd.DataFrame:
    R, U, A, TVr = P.rets.values, P.uni.values, P.ar.values, P.tv.values
    ind = np.array([G.industry.get(s, "") for s in P.syms])
    out = []
    for _, e in ev.iterrows():
        p, i_sym = int(e["pos"]), e["symbol"]
        i = P.col[i_sym]
        t = P.dates[p]
        fr = G.frame_at(t)
        grp_of = fr["group"].to_dict()
        typ_of = fr["group_type"].to_dict()
        conf_of = fr["confidence"].to_dict()
        g_i, t_i = grp_of.get(i_sym, ""), typ_of.get(i_sym, "")
        excl = {i_sym} | G.same_co.get(i_sym, set())
        cand = np.where(U[p - 1])[0]
        cand = np.array([j for j in cand if P.syms[j] not in excl])
        lo, hi = p - CALM_LEN - CALM_END + 1, p - CALM_END + 1      # days -261 .. -10
        ai = A[lo:hi, i]
        aj = A[lo:hi][:, cand]
        both = np.isfinite(ai)[:, None] & np.isfinite(aj)
        n_calm = both.sum(0)
        x = np.where(both, ai[:, None], np.nan)
        y = np.where(both, aj, np.nan)
        xm, ym = np.nanmean(x, 0), np.nanmean(y, 0)
        cov = np.nanmean((x - xm) * (y - ym), 0)
        sx, sy = np.nanstd(x, 0), np.nanstd(y, 0)
        rho = cov / (sx * sy)
        beta = cov / sx ** 2
        rw = R[p:p + WIN + 1][:, cand]
        n_win = np.isfinite(rw).sum(0)
        ok = (n_calm >= CALM_MIN) & (n_win >= WIN_MIN) & np.isfinite(rho)
        cand, rho, beta, n_calm = cand[ok], rho[ok], beta[ok], n_calm[ok]
        rw = rw[:, ok]
        # market for reported means: universe ex trigger group and ex trigger industry
        g_members = {s for s, g in grp_of.items() if g == g_i and t_i in MAIN_TYPES}
        mask_m = U[p:p + WIN + 1] & ~np.isin(P.syms, list(g_members | {i_sym}))[None, :] \
            & (ind != ind[i])[None, :]
        m_ex = np.nanmean(np.where(mask_m, R[p:p + WIN + 1], np.nan), axis=1)
        bh_m = np.prod(1 + np.nan_to_num(m_ex))
        bhar = np.prod(1 + np.nan_to_num(rw), axis=0) - bh_m
        car = np.nansum(A[p:p + WIN + 1][:, cand], axis=0)
        ar0 = A[p, cand]
        tvc = TVr[lo:hi][:, cand]
        amihud = np.nanmean(np.where(tvc > 0, np.abs(R[lo:hi][:, cand]) / tvc, np.nan), 0) * 1e9
        size = P.tv63raw.values[p - 11, cand]
        ri = np.nan_to_num(R[p:p + WIN + 1, i])
        trig_bhar = np.prod(1 + ri) - bh_m
        for k, j in enumerate(cand):
            s = P.syms[j]
            g_j, t_j = grp_of.get(s, ""), typ_of.get(s, "")
            same_ind = ind[j] == ind[i] and ind[i] != ""
            same_g = (g_j == g_i) and t_i in MAIN_TYPES and t_j in MAIN_TYPES and g_i != ""
            same_gw = (g_j == g_i) and t_i in WIDE_TYPES and t_j in WIDE_TYPES and g_i != ""
            cls = ("SI" if same_ind else "S") if same_g else ("R" if same_ind else "B")
            clsw = ("SI" if same_ind else "S") if same_gw else ("R" if same_ind else "B")
            out.append((e["event_id"], str(t.date()), i_sym, g_i, ind[i], s, g_j, t_j, ind[j],
                        cls, clsw, conf_of.get(i_sym, ""), conf_of.get(s, ""),
                        bhar[k], car[k], ar0[k], rho[k], beta[k], int(n_calm[k]),
                        np.log(size[k]) if size[k] > 0 else np.nan,
                        np.log(amihud[k]) if amihud[k] > 0 else np.nan,
                        trig_bhar, A[p, i]))
    cols = ["event_id", "date", "trigger", "trigger_group", "trigger_industry", "stock", "group",
            "group_type", "industry", "cls", "cls_wide", "conf_trigger", "conf_stock",
            "bhar_0_20", "car_0_20", "ar_d0", "rho", "beta_calm", "n_calm", "log_size",
            "log_amihud", "trigger_bhar_0_20", "trigger_ar_d0"]
    return pd.DataFrame(out, columns=cols)


def ols_fe(d: pd.DataFrame, y: str, xs: list[str], clusters: dict[str, pd.Series],
           weights=None) -> dict:
    """OLS with event fixed effects (within transformation), cluster-robust SEs."""
    d = d.dropna(subset=[y] + xs)
    Z = d[[y] + xs].astype(float)
    Zd = Z - Z.groupby(d["event_id"]).transform("mean")
    X, Y = Zd[xs].values, Zd[y].values
    n, k = X.shape
    xtx_inv = np.linalg.pinv(X.T @ X)
    b = xtx_inv @ X.T @ Y
    u = Y - X @ b
    res = {"n": int(n), "n_events": int(d["event_id"].nunique()),
           "coef": {x: safe(v) for x, v in zip(xs, b)}, "se": {}, "t": {}}
    for name, cl in clusters.items():
        g = cl.loc[d.index].values
        sc = pd.DataFrame(X * u[:, None]).groupby(g).sum().values
        G_ = sc.shape[0]
        meat = sc.T @ sc
        V = xtx_inv @ meat @ xtx_inv * (G_ / max(G_ - 1, 1)) * ((n - 1) / max(n - k, 1))
        se = np.sqrt(np.diag(V))
        res["se"][name] = {x: safe(v) for x, v in zip(xs, se)}
        res["t"][name] = {x: safe(bb / ss) for x, bb, ss in zip(xs, b, se)}
        res.setdefault("n_clusters", {})[name] = int(G_)
        if "S" in xs and "R" in xs:
            ia, ib = xs.index("S"), xs.index("R")
            dv = V[ia, ia] + V[ib, ib] - 2 * V[ia, ib]
            res.setdefault("t_S_minus_R", {})[name] = safe((b[ia] - b[ib]) / np.sqrt(dv))
    if "S" in xs and "R" in xs:
        res["S_minus_R"] = safe(b[xs.index("S")] - b[xs.index("R")])
    return res


def add_dummies(d: pd.DataFrame, col: str = "cls") -> pd.DataFrame:
    d = d.copy()
    for c in ["S", "SI", "R"]:
        d[c] = (d[col] == c).astype(float)
    return d


def clusters_of(d: pd.DataFrame) -> dict[str, pd.Series]:
    dt = pd.to_datetime(d["date"])
    return {"month": dt.dt.to_period("M").astype(str), "event": d["event_id"],
            "date": d["date"], "group": d["trigger_group"]}


def permutation_S(d: pd.DataFrame, xs: list[str], y: str, n_perm: int, seed: int) -> dict:
    d = d.dropna(subset=[y] + xs).reset_index(drop=True)
    ev = d["event_id"].values
    codes, uniq = pd.factorize(ev)
    other = [x for x in xs if x != "S"]
    Z = d[[y] + other].astype(float)
    Zd = (Z - Z.groupby(codes).transform("mean")).values
    Yd, Od = Zd[:, 0], Zd[:, 1:]

    def beta_s(svec):
        sd = svec - pd.Series(svec).groupby(codes).transform("mean").values
        X = np.column_stack([sd, Od])
        return np.linalg.lstsq(X, Yd, rcond=None)[0][0]

    s_real = d["S"].values.astype(float)
    b_real = beta_s(s_real)
    pool_idx = {}
    for k in range(len(uniq)):
        idx = np.where((codes == k) & d["cls"].isin(["S", "B"]).values)[0]
        ns = int(s_real[idx].sum())
        if ns > 0:
            pool_idx[k] = (idx, ns)
    rng = np.random.default_rng(seed)
    draws = np.empty(n_perm)
    for b in range(n_perm):
        s = np.zeros(len(d))
        for k, (idx, ns) in pool_idx.items():
            s[rng.choice(idx, ns, replace=False)] = 1.0
        draws[b] = beta_s(s)
    return {"beta_S": safe(b_real), "p_one_sided": safe(float(np.mean(draws <= b_real))),
            "perm_mean": safe(draws.mean()), "perm_sd": safe(draws.std()),
            "perm_q05": safe(np.quantile(draws, 0.05)), "n_perm": n_perm}


def event_level_R8(d: pd.DataFrame, y: str) -> dict:
    from scipy import stats
    d = d.dropna(subset=[y, "rho", "log_size", "log_amihud"])
    ctr = ["rho", "log_size", "log_amihud"]
    Z = d[[y] + ctr].astype(float)
    mb = d["cls"] == "B"
    means_b = Z[mb].groupby(d.loc[mb, "event_id"]).mean()
    Zb = Z[mb] - means_b.loc[d.loc[mb, "event_id"]].values
    gam = np.linalg.lstsq(Zb[ctr].values, Zb[y].values, rcond=None)[0]
    ms = d["cls"] == "S"
    sub = d[ms & d["event_id"].isin(means_b.index)]
    mb_e = means_b.loc[sub["event_id"]].values
    resid = (sub[y].values - mb_e[:, 0]) - (sub[ctr].values - mb_e[:, 1:]) @ gam
    per_ev = pd.Series(resid, index=sub.index).groupby(sub["event_id"]).mean()
    t, p2 = stats.ttest_1samp(per_ev, 0.0)
    neg = int((per_ev < 0).sum())
    sign_p = stats.binomtest(neg, len(per_ev), 0.5, alternative="greater").pvalue
    return {"n_events": int(len(per_ev)), "mean_resid": safe(per_ev.mean()),
            "median_resid": safe(per_ev.median()), "t": safe(t), "p_two_sided": safe(p2),
            "share_negative": safe(neg / len(per_ev)), "sign_p_one_sided": safe(sign_p)}


def class_means(d: pd.DataFrame, col: str = "cls") -> dict:
    out = {}
    for c, g in d.groupby(col):
        out[c] = {"n_pairs": int(len(g)), "n_events": int(g["event_id"].nunique()),
                  "mean_rho": safe(g["rho"].mean())}
        for y in ["bhar_0_20", "car_0_20", "ar_d0"]:
            out[c][f"mean_{y}"] = safe(g[y].mean())
            out[c][f"median_{y}"] = safe(g[y].median())
    return out


def verdict(main: dict, perm: dict, no_rho: dict, perm_no_rho: dict, n_ev_s: int,
            n_groups_s: int) -> dict:
    if n_ev_s < 30 or n_groups_s < 10:
        return {"verdict": "STOP", "reason": "too few events to test",
                "n_events_with_S": n_ev_s, "n_groups_with_S": n_groups_s}
    bS, bR = main["coef"]["S"], main["coef"]["R"]
    tS = main["t"]["month"]["S"]
    r1, r2, r3 = (bS < 0 and tS <= -1.96), perm["p_one_sided"] < 0.05, bS <= bR
    sig_no_rho = (no_rho["coef"]["S"] < 0 and no_rho["t"]["month"]["S"] <= -1.96
                  and perm_no_rho["p_one_sided"] < 0.05)
    if r1 and r2 and r3:
        v, why = "GO", "beta_S negative and significant after the calm-correlation control, and <= beta_R"
    elif r1 and r2:
        v, why = "STOP", "group effect smaller than industry"
    elif sig_no_rho:
        v, why = "STOP", "calm correlation explains it"
    else:
        v, why = "STOP", "no group effect"
    return {"verdict": v, "reason": why, "rule1_beta_S_neg_t_le_-1.96": bool(r1),
            "rule2_perm_p_lt_0.05": bool(r2), "rule3_beta_S_le_beta_R": bool(r3),
            "beta_S_sig_without_rho": bool(sig_no_rho), "n_events_with_S": n_ev_s,
            "n_groups_with_S": n_groups_s}


def tail_dependence(P: Panel, G: GroupMap, n_perm: int = 1000) -> dict:
    """PREREGISTRATION §7: excess tail dependence over calm-correlation Gaussian."""
    from scipy.stats import norm
    A = P.ar.where(P.uni).loc["2005-01-01":"2025-06-30"]
    syms = list(A.columns)
    V = np.isfinite(A.values)
    X = np.nan_to_num(A.values)
    q05 = np.array([np.nanquantile(A.values[:, j], 0.05) if V[:, j].sum() > 50 else np.nan
                    for j in range(len(syms))])
    D = (V & (A.values <= q05[None, :])).astype(float)
    Vf = V.astype(float)
    n_all = Vf.T @ Vf
    joint = (D.T @ D) / np.maximum(n_all, 1)
    m = P.mkt.loc[A.index].values
    lo, hi = np.nanquantile(m, 0.10), np.nanquantile(m, 0.90)
    calm = (m >= lo) & (m <= hi)
    Vc, Xc = Vf[calm], X[calm] * Vf[calm]
    n = Vc.T @ Vc
    sx = Xc.T @ Vc
    sxx = (Xc ** 2).T @ Vc
    sxy = Xc.T @ Xc
    num = n * sxy - sx * sx.T
    den = np.sqrt(np.maximum(n * sxx - sx ** 2, 0) * np.maximum(n * sxx.T - sx.T ** 2, 0))
    with np.errstate(invalid="ignore", divide="ignore"):
        rho = num / den
    # Gaussian orthant probability P(Z1<=z, Z2<=z; r) = Phi(z)^2 + int_0^r phi2(z,z,s) ds
    z = norm.ppf(0.05)
    grid = np.linspace(-0.999, 0.999, 3997)
    dens = np.exp(-z ** 2 / (1 + grid)) / (2 * np.pi * np.sqrt(1 - grid ** 2))
    cum = np.concatenate([[0], np.cumsum((dens[1:] + dens[:-1]) / 2 * np.diff(grid))])
    cum0 = np.interp(0.0, grid, cum)
    implied_grid = norm.cdf(z) ** 2 + (cum - cum0)
    iu = np.triu_indices(len(syms), 1)
    keep = (n_all[iu] >= 750) & np.isfinite(rho[iu])
    a, b = iu[0][keep], iu[1][keep]
    r = rho[a, b]
    excess = joint[a, b] - np.interp(r, grid, implied_grid)
    # same-group share of overlapping valid days (time-varying labels)
    gnames = sorted(set(G.gm.loc[G.gm["group_type"].isin(MAIN_TYPES), "group"]))
    gcode = {g: k for k, g in enumerate(gnames)}
    grp_mat = np.full(A.shape, -1, dtype=np.int32)
    for s_, g in G.gm.groupby("symbol"):
        if s_ not in P.col:
            continue
        j = syms.index(s_)
        for _, row in g.iterrows():
            if row["group_type"] in MAIN_TYPES:
                mm = (A.index >= row["start"]) & (A.index <= row["end"])
                grp_mat[mm, j] = gcode[row["group"]]
    share_same = np.zeros((len(syms), len(syms)))
    for g in np.unique(grp_mat[grp_mat >= 0]):
        M = ((grp_mat == g) & V).astype(float)
        cols = np.where(M.any(0))[0]
        if len(cols) < 2:
            continue
        share_same[np.ix_(cols, cols)] += M[:, cols].T @ M[:, cols]
    share_same = share_same / np.maximum(n_all, 1)
    sh = share_same[a, b]
    ind = np.array([G.industry.get(s_, "") for s_ in syms])
    same_ind = (ind[a] == ind[b]) & (ind[a] != "")
    same_g = sh >= 0.80
    part = (sh > 0.01) & (sh < 0.80)
    cls = np.where(same_g & same_ind, "both", np.where(same_g, "same_group",
                   np.where(same_ind, "same_industry", "neither")))
    df = pd.DataFrame({"a": np.array(syms)[a], "b": np.array(syms)[b], "rho_calm": r,
                       "joint_tail": joint[a, b], "excess": excess, "cls": cls,
                       "share_same_group": sh})
    df = df[~part]
    summ = df.groupby("cls").agg(n_pairs=("excess", "size"), mean_excess=("excess", "mean"),
                                 median_excess=("excess", "median"),
                                 mean_joint=("joint_tail", "mean"), mean_rho=("rho_calm", "mean"))
    summ.to_csv(OUT / "tail_pairs_summary.csv")
    Xr = np.column_stack([np.ones(len(df)), (df["cls"] == "same_group").astype(float),
                          (df["cls"] == "same_industry").astype(float),
                          (df["cls"] == "both").astype(float), df["rho_calm"].values])
    coef = np.linalg.lstsq(Xr, df["excess"].values, rcond=None)[0]
    # permutation: static majority label per stock, reshuffled across stocks (sizes kept)
    stat_lab = []
    for j in range(len(syms)):
        col_ = grp_mat[:, j][V[:, j]]
        col_ = col_[col_ >= 0]
        stat_lab.append(int(np.bincount(col_).argmax()) if len(col_) else -1)
    stat_lab = np.array(stat_lab)
    cnt = pd.Series(stat_lab[stat_lab >= 0]).value_counts()
    multi = set(cnt[cnt >= 2].index)
    lab = np.where(np.isin(stat_lab, list(multi)), stat_lab, -1)
    pa_all, pb_all = a, b
    ex_all, ind_diff = excess, ~same_ind

    def stat(l):
        sel = (l[pa_all] == l[pb_all]) & (l[pa_all] >= 0) & ind_diff
        return ex_all[sel].mean() if sel.any() else np.nan

    real = stat(lab)
    rng = np.random.default_rng(SEED)
    holders = np.where(lab >= 0)[0]
    universe_idx = np.arange(len(syms))
    draws = []
    for _ in range(n_perm):
        newlab = np.full(len(syms), -1)
        newlab[rng.choice(universe_idx, len(holders), replace=False)] = rng.permutation(lab[holders])
        draws.append(stat(newlab))
    draws = np.array(draws)
    return {"n_pairs": int(len(df)), "by_class": summ.reset_index().to_dict("records"),
            "ols_coef": {"const": safe(coef[0]), "same_group": safe(coef[1]),
                         "same_industry": safe(coef[2]), "both": safe(coef[3]),
                         "rho_calm": safe(coef[4])},
            "perm_static_labels": {"mean_excess_same_group_other_industry": safe(real),
                                   "perm_mean": safe(np.nanmean(draws)),
                                   "p_one_sided": safe(float(np.nanmean(draws >= real))),
                                   "n_perm": n_perm}}


def run_tests() -> dict:
    log("Loading panel")
    P = Panel()
    G = GroupMap(P.syms)
    ev = pd.read_csv(OUT / "events.csv")
    ev["date"] = pd.to_datetime(ev["date"])
    log(f"  {len(ev)} events")
    d = build_pairs(P, G, ev)
    d.to_parquet(OUT / "pairs.parquet", index=False)
    has_sib = d[d["cls"].isin(["S", "SI"])]["event_id"].unique()
    d = d[d["event_id"].isin(has_sib)].reset_index(drop=True)
    d = add_dummies(d)
    ev_s = d[d["cls"] == "S"]
    n_ev_s, n_g_s = ev_s["event_id"].nunique(), ev_s["trigger_group"].nunique()
    log(f"  events with >=1 S or SI stock: {d['event_id'].nunique()}; with >=1 S: {n_ev_s} "
        f"from {n_g_s} groups; pairs: {len(d)}")
    XS = ["S", "SI", "R", "rho", "log_size", "log_amihud"]
    XS0 = ["S", "SI", "R", "log_size", "log_amihud"]
    cl = clusters_of(d)
    res = {"counts": {"n_events_input": int(len(ev)), "n_events_used": int(d["event_id"].nunique()),
                      "n_events_with_S": int(n_ev_s), "n_groups_with_S": int(n_g_s),
                      "n_pairs": int(len(d)),
                      "pairs_by_class": d["cls"].value_counts().to_dict()},
           "class_means": class_means(d)}
    main = ols_fe(d, "bhar_0_20", XS, cl)
    no_rho = ols_fe(d, "bhar_0_20", XS0, cl)
    log("  primary regression done; permutations ...")
    perm = permutation_S(d, XS, "bhar_0_20", 2000, SEED)
    perm0 = permutation_S(d, XS0, "bhar_0_20", 2000, SEED)
    res["primary"] = {"regression": main, "permutation": perm}
    res["R10_no_rho"] = {"regression": no_rho, "permutation": perm0}
    res["verdict"] = verdict(main, perm, no_rho, perm0, int(n_ev_s), int(n_g_s))
    log(f"  VERDICT: {res['verdict']}")
    # robustness (§8)
    rob = {}
    dt = pd.to_datetime(d["date"])
    crisis = ((dt >= "2008-01-01") & (dt <= "2009-12-31")) | ((dt >= "2020-02-01") & (dt <= "2020-04-30"))
    rob["R1_no_crises"] = ols_fe(d[~crisis], "bhar_0_20", XS, clusters_of(d[~crisis]))
    p1 = pd.Series(False, index=d.index)
    tpos = {t: k for k, t in enumerate(P.dates)}
    pos_d = dt.map(lambda x: tpos.get(x, np.nan))
    for grp, day in PAPER1_EPISODES:
        k0 = P.dates.searchsorted(pd.Timestamp(day))
        p1 |= (d["trigger_group"] == grp) & ((pos_d - k0).abs() <= 60)
    rob["R2_no_paper1_episodes"] = {"n_events_dropped": int(d.loc[p1, "event_id"].nunique()),
                                    **ols_fe(d[~p1], "bhar_0_20", XS, clusters_of(d[~p1]))}
    rob["R3_day0_AR"] = ols_fe(d, "ar_d0", XS, cl)
    rob["R3_car_0_20"] = ols_fe(d, "car_0_20", XS, cl)
    d["implied_bhar"] = d["beta_calm"] * d["trigger_bhar_0_20"]
    d["implied_d0"] = d["beta_calm"] * d["trigger_ar_d0"]
    rob["R3_bhar_plus_implied"] = ols_fe(d, "bhar_0_20", XS + ["implied_bhar"], cl)
    rob["R3_day0_plus_implied"] = ols_fe(d, "ar_d0", XS + ["implied_d0"], cl)
    dw = add_dummies(d, "cls_wide")
    dw = dw[dw["event_id"].isin(dw[dw["cls_wide"].isin(["S", "SI"])]["event_id"].unique())]
    rob["R4_wide_groups"] = ols_fe(dw, "bhar_0_20", XS, clusters_of(dw))
    rob["R4_wide_groups"]["class_means"] = class_means(dw, "cls_wide")
    rob["R5_clusterings"] = {k: main["t"][k] for k in main["t"]}
    hc = d[(d["conf_trigger"] == "high") & (d["conf_stock"] == "high")]
    rob["R6_high_confidence"] = ols_fe(hc, "bhar_0_20", XS, clusters_of(hc))
    ns = pd.read_csv(OUT / "news_sample.csv")
    clean = ns[ns["news_label"].astype(str).str.strip().str.lower().str[:1] != "b"]["event_id"]
    d7 = d[d["event_id"].isin(clean)]
    rob["R7_news_checked_clean"] = (ols_fe(d7, "bhar_0_20", XS, clusters_of(d7))
                                    if d7["S"].sum() > 0 else {"n": 0})
    rob["R7_news_labels"] = ns["news_label"].value_counts().to_dict()
    rob["R8_event_level"] = event_level_R8(d, "bhar_0_20")
    d["rho_dec"] = pd.qcut(d["rho"], 10, labels=False)
    dec = pd.get_dummies(d["rho_dec"], prefix="rhodec", drop_first=True).astype(float)
    d9 = pd.concat([d, dec], axis=1)
    rob["R9_rho_deciles"] = ols_fe(d9, "bhar_0_20", ["S", "SI", "R", "log_size", "log_amihud"]
                                   + list(dec.columns), clusters_of(d9))
    res["robustness"] = rob
    log("  tail dependence (§7) ...")
    res["tail_dependence"] = tail_dependence(P, G)
    with open(OUT / "tests.json", "w") as f:
        json.dump(res, f, indent=2, default=lambda o: safe(o) if isinstance(o, (np.integer, np.floating)) else str(o))
    log("Done. results/group_dependency/tests.json")
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["universe", "events", "run"])
    a = ap.parse_args()
    {"universe": build_universe, "events": select_events, "run": run_tests}[a.step]()


if __name__ == "__main__":
    main()
