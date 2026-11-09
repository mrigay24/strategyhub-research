"""
Entropy / replaceability research — pilot tests (started 2026-11-09).

Idea being tested (Mrigay's framework, from Zero to One p.34):
  * Entropy of a distribution of weights/shares measures how much any single
    firm's identity matters. High entropy = interchangeable firms; low entropy =
    a few firms carry the system.
  * Claim A (portfolio): an investor without forecasting skill does best with a
    HIGH-entropy (diversified) portfolio.
  * Claim B (system): real economic systems drift toward LOW entropy
    (concentration emerges), and low entropy means fragility.
  * Claim C (death test): what matters is not market share but replaceability:
    if a firm is hit, do its rivals absorb the loss (replaceable) or share it?

Three pilot tests, using only price + volume data already in this repo:
  Test 1  Random N-stock portfolios vs the full equal-weight universe
          (portfolio entropy = ln N). Also: does a buy-and-hold portfolio's
          entropy fall on its own? (Claim A + emergent concentration, Claim B)
  Test 2  Market "co-movement entropy" (eigenvalue entropy of the 1-year
          correlation matrix) and trading-value entropy, US and India, and
          whether low entropy predicts bigger future drawdowns / volatility
          after controlling for current volatility. (Claim B: low entropy = fragile)
  Test 3  Death-test pilot: when one S&P 500 stock has a large idiosyncratic
          crash, how do same-sector peers react? (Claim C)

Outputs: results/entropy_research/*.csv and summary.json

Known limitations (write these into the paper, do not hide them):
  * No market caps in the data, so "size" uses 63-day average dollar volume.
  * Delisted stocks are held as cash at their last price (true delisting
    returns are often worse), which flatters concentrated portfolios slightly.
  * Sectors are 11 GICS sectors from the CURRENT S&P 500 list only, so Test 3
    ignores delisted firms and treats whole sectors as "rivals".

Run:  .venv/bin/python scripts/entropy_research.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data_processed"
OUT = ROOT / "results" / "entropy_research"
OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(42)
T0 = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - T0:6.1f}s] {msg}", flush=True)


def safe(x):
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return x
    return None if (np.isnan(x) or np.isinf(x)) else round(x, 6)


def entropy_norm(w: np.ndarray) -> tuple[float, float, float]:
    """Return (normalised Shannon entropy H/lnN, HHI, effective N = 1/HHI)."""
    w = np.asarray(w, dtype=float)
    w = w[np.isfinite(w) & (w > 0)]
    if len(w) < 2:
        return np.nan, np.nan, np.nan
    w = w / w.sum()
    h = -(w * np.log(w)).sum()
    hhi = (w ** 2).sum()
    return h / np.log(len(w)), hhi, 1.0 / hhi


def ols_hac(y: np.ndarray, X: np.ndarray, lags: int = 3):
    """OLS with Newey-West standard errors (no statsmodels in the venv)."""
    X = np.column_stack([np.ones(len(X)), X])
    ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
    y, X = y[ok], X[ok]
    n, k = X.shape
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ X.T @ y
    u = y - X @ beta
    xu = X * u[:, None]
    s = xu.T @ xu
    for lag in range(1, lags + 1):
        w = 1 - lag / (lags + 1)
        g = xu[lag:].T @ xu[:-lag]
        s += w * (g + g.T)
    cov = xtx_inv @ s @ xtx_inv
    se = np.sqrt(np.diag(cov))
    r2 = 1 - (u ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return beta, beta / se, r2, n


# ----------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------
def load_panel(path: Path, max_abs_ret: float, price_floor: float | None = None):
    """Wide returns + dollar volume.

    For the US we deliberately use the RAW file (extended_prices.parquet) with
    the $1 price floor, not extended_prices_clean.parquet: the clean file's 20%
    return filter deletes genuine single-day crashes, which are exactly the
    events Test 3 needs. Moves beyond +/-50% are still treated as bad ticks.
    """
    raw = pd.read_parquet(path, columns=["date", "symbol", "close", "volume"])
    raw["date"] = pd.to_datetime(raw["date"])
    if price_floor is not None:
        raw = raw[raw["close"] >= price_floor]
    close = raw.pivot_table(index="date", columns="symbol", values="close")
    volume = raw.pivot_table(index="date", columns="symbol", values="volume")
    rets = close.pct_change(fill_method=None)
    rets = rets.where(rets.abs() <= max_abs_ret)  # kill split/bad-tick artefacts
    dv = (close * volume).reindex_like(rets)
    return rets, dv


def us_pit_mask(rets: pd.DataFrame) -> pd.DataFrame:
    lk = pd.read_csv(DATA / "sp500_universe_lookup.csv", parse_dates=["date"])
    periods = lk["date"].dt.to_period("M")
    cols = rets.columns
    m = pd.DataFrame(False, index=periods, columns=cols)
    for p, tick in zip(periods, lk["tickers"]):
        names = [t for t in str(tick).split(",") if t in m.columns]
        m.loc[p, names] = True
    daily = m.reindex(rets.index.to_period("M")).fillna(False).astype(bool)
    daily.index = rets.index
    return daily & rets.notna()


def month_end_positions(index: pd.DatetimeIndex) -> np.ndarray:
    per = index.to_period("M")
    pos = np.where(per[1:] != per[:-1])[0]
    return np.append(pos, len(index) - 1)


# ----------------------------------------------------------------------------
# Test 1 — portfolio entropy: random N-stock portfolios vs the full universe
# ----------------------------------------------------------------------------
def test1_portfolio_entropy(rets: pd.DataFrame, mask: pd.DataFrame) -> dict:
    log("Test 1: random concentrated portfolios vs full universe")
    mret = (1 + rets).resample("M").prod(min_count=1) - 1
    mmask = mask.resample("M").max()
    sizes = [1, 2, 5, 10, 20, 30, 50, 100, 200]
    trials = 5000
    rows, skew_rows = [], []
    for start in [2000, 2005, 2010, 2015, 2020]:
        win = mret.loc[f"{start}-01":f"{start + 4}-12"]
        first = win.index[0]
        members = [c for c in win.columns if mmask.loc[first, c] and np.isfinite(win.loc[first, c])]
        sub = win[members].fillna(0.0)  # after delisting the money sits in cash
        g = (1 + sub).prod().values  # 5-year growth of $1 in each stock
        m = len(g)
        years = len(win) / 12
        bench = g.mean()
        bench_ann = bench ** (1 / years) - 1
        # emergent concentration: weights of the buy-and-hold universe at the end
        h_end, hhi_end, effn_end = entropy_norm(g)
        # Bessembinder-style skew facts
        gains = np.sort(g - 1)[::-1]
        top10 = gains[: int(np.ceil(0.1 * m))].sum()
        skew_rows.append({
            "window": f"{start}-{start + 4}", "n_stocks": m,
            "ew_universe_ann_return": bench_ann,
            "pct_stocks_beating_universe": float((g > bench).mean()),
            "pct_stocks_losing_money": float((g < 1).mean()),
            "median_stock_ann_return": float(np.median(g) ** (1 / years) - 1),
            "share_of_net_gain_from_top10pct": float(top10 / gains.sum()) if gains.sum() > 0 else np.nan,
            "start_entropy_norm": 1.0, "end_entropy_norm": h_end,
            "start_effective_n": m, "end_effective_n": effn_end,
        })
        for n in sizes:
            if n > m:
                continue
            idx = RNG.random((trials, m)).argsort(axis=1)[:, :n]
            port = g[idx].mean(axis=1)
            ann = port ** (1 / years) - 1
            rows.append({
                "window": f"{start}-{start + 4}", "N": n,
                "portfolio_entropy_norm": np.log(n) / np.log(m) if n > 1 else 0.0,
                "HHI": 1 / n,
                "median_ann_return": float(np.median(ann)),
                "mean_ann_return": float(ann.mean()),
                "p5_ann_return": float(np.percentile(ann, 5)),
                "p95_ann_return": float(np.percentile(ann, 95)),
                "prob_beat_universe": float((port > bench).mean()),
                "prob_lag_universe_by_3pct_pa": float((ann < bench_ann - 0.03).mean()),
                "universe_ann_return": bench_ann,
            })
    df = pd.DataFrame(rows)
    skew = pd.DataFrame(skew_rows)
    df.to_csv(OUT / "test1_random_portfolios.csv", index=False)
    skew.to_csv(OUT / "test1_stock_skew_and_drift.csv", index=False)
    avg = df.groupby("N")[["portfolio_entropy_norm", "median_ann_return", "mean_ann_return",
                           "universe_ann_return", "prob_beat_universe",
                           "prob_lag_universe_by_3pct_pa", "p5_ann_return"]].mean()
    avg.to_csv(OUT / "test1_summary_by_N.csv")
    log("\n" + avg.round(3).to_string())
    log("\n" + skew.round(3).to_string())
    return {"by_N": avg.reset_index().to_dict("records"), "skew": skew.to_dict("records")}


# ----------------------------------------------------------------------------
# Test 2 — market entropy and fragility
# ----------------------------------------------------------------------------
def entropy_series(rets: pd.DataFrame, mask: pd.DataFrame, dv: pd.DataFrame,
                   label: str, top_n: int | None) -> pd.DataFrame:
    log(f"Test 2 [{label}]: monthly entropy series")
    dates = rets.index
    ew = (rets.where(mask)).mean(axis=1)  # equal-weight universe return
    rows = []
    for e in month_end_positions(dates):
        if e < 252 or e + 126 >= len(dates):
            continue
        members = mask.columns[mask.iloc[e].values]
        dvbar = dv.iloc[e - 62:e + 1][members].mean()
        if top_n is not None:
            members = dvbar.nlargest(top_n).index
        win = rets.iloc[e - 251:e + 1][members]
        win = win.loc[:, win.notna().mean() >= 0.95].fillna(0.0)
        win = win.loc[:, win.std() > 0]
        n = win.shape[1]
        if n < 50:
            continue
        lam = np.clip(np.linalg.eigvalsh(np.corrcoef(win.values.T)), 1e-12, None)
        p = lam / lam.sum()
        h_eig = -(p * np.log(p)).sum() / np.log(n)
        top1 = lam.max() / lam.sum()
        k = max(1, n // 5)
        absorption = np.sort(lam)[::-1][:k].sum() / lam.sum()
        h_dv, hhi_dv, effn_dv = entropy_norm(dvbar.reindex(win.columns).values)
        trail = ew.iloc[e - 62:e + 1]
        f63 = ew.iloc[e + 1:e + 64]
        f126 = ew.iloc[e + 1:e + 127]
        path = (1 + f126).cumprod()
        rows.append({
            "date": dates[e], "n": n,
            "eig_entropy_norm": h_eig, "first_eig_share": top1, "absorption_ratio": absorption,
            "dv_entropy_norm": h_dv, "dv_hhi": hhi_dv, "dv_effective_n": effn_dv,
            "trail_vol_63": trail.std() * np.sqrt(252),
            "trail_ret_63": (1 + trail).prod() - 1,
            "fwd_vol_63": f63.std() * np.sqrt(252),
            "fwd_ret_63": (1 + f63).prod() - 1,
            "fwd_ret_126": (1 + f126).prod() - 1,
            "fwd_mdd_126": (path / path.cummax() - 1).min(),
        })
    df = pd.DataFrame(rows).set_index("date")
    df.to_csv(OUT / f"test2_entropy_series_{label}.csv")
    return df


def test2_analyse(df: pd.DataFrame, label: str) -> dict:
    out = {"label": label, "months": len(df),
           "start": str(df.index.min().date()), "end": str(df.index.max().date())}
    df = df.copy()
    df["eig_q"] = pd.qcut(df["eig_entropy_norm"], 5, labels=["Q1 low", "Q2", "Q3", "Q4", "Q5 high"])
    qt = df.groupby("eig_q", observed=True)[["eig_entropy_norm", "trail_vol_63", "fwd_vol_63",
                                             "fwd_ret_63", "fwd_mdd_126"]].mean()
    qt.to_csv(OUT / f"test2_quintiles_{label}.csv")
    log(f"\n[{label}] co-movement entropy quintiles\n" + qt.round(3).to_string())
    z = (df["eig_entropy_norm"] - df["eig_entropy_norm"].mean()) / df["eig_entropy_norm"].std()
    regs = {}
    for ycol, lags in [("fwd_vol_63", 3), ("fwd_mdd_126", 6), ("fwd_ret_63", 3)]:
        b, t, r2, n = ols_hac(df[ycol].values, np.column_stack([df["trail_vol_63"].values, z.values]), lags)
        b0, t0, r20, _ = ols_hac(df[ycol].values, df[["trail_vol_63"]].values, lags)
        regs[ycol] = {"coef_entropy_z": safe(b[2]), "t_entropy": safe(t[2]),
                      "coef_trail_vol": safe(b[1]), "t_trail_vol": safe(t[1]),
                      "r2_with_entropy": safe(r2), "r2_vol_only": safe(r20), "n": int(n)}
    log(f"[{label}] regressions (outcome ~ trailing vol + entropy z, Newey-West t):\n"
        + json.dumps(regs, indent=1))
    yearly = df[["eig_entropy_norm", "dv_entropy_norm", "dv_effective_n", "n"]].resample("A").mean()
    yearly.index = yearly.index.year
    yearly.to_csv(OUT / f"test2_yearly_{label}.csv")
    out["quintiles"] = qt.reset_index().astype({"eig_q": str}).to_dict("records")
    out["regressions"] = regs
    out["yearly"] = yearly.reset_index().rename(columns={"date": "year"}).to_dict("records")
    out["corr_eig_vs_dv_entropy"] = safe(df["eig_entropy_norm"].corr(df["dv_entropy_norm"]))
    return out


# ----------------------------------------------------------------------------
# Test 3 — death-test pilot: peer reaction to a firm's idiosyncratic crash
# ----------------------------------------------------------------------------
def test3_death_test(rets: pd.DataFrame, mask: pd.DataFrame, dv: pd.DataFrame) -> dict:
    log("Test 3: death-test pilot (peer reaction to idiosyncratic crashes)")
    sec = pd.read_csv(ROOT / "data_raw" / "sp500_constituents" / "sp500_current.csv")
    sec["ticker"] = sec["ticker"].str.replace(".", "-", regex=False)
    sector_of = dict(zip(sec["ticker"], sec["sector"]))
    cols = [c for c in rets.columns if c in sector_of]
    R = rets[cols]
    M = mask[cols] & R.notna()
    Rz = R.where(M).fillna(0.0)
    sectors = sorted(set(sector_of[c] for c in cols))
    sec_cols = {s: [c for c in cols if sector_of[c] == s] for s in sectors}
    tot_sum, tot_n = Rz.sum(axis=1), M.sum(axis=1)
    s_sum = pd.DataFrame({s: Rz[c].sum(axis=1) for s, c in sec_cols.items()})
    s_n = pd.DataFrame({s: M[c].sum(axis=1) for s, c in sec_cols.items()})
    mkt_ex = (tot_sum.values[:, None] - s_sum.values) / np.maximum(tot_n.values[:, None] - s_n.values, 1)
    mkt_ex = pd.DataFrame(mkt_ex, index=R.index, columns=sectors)
    dvbar = dv[cols].rolling(63, min_periods=40).mean().shift(1)

    # peer (sector ex-firm) return and its abnormal version
    events = []
    ri, mi = Rz.values, M.values
    ss, sn, mx = s_sum.values, s_n.values, mkt_ex.values
    col_pos = {c: j for j, c in enumerate(cols)}
    sec_pos = {s: k for k, s in enumerate(sectors)}
    peer_ret = {}
    for c in cols:
        j, k = col_pos[c], sec_pos[sector_of[c]]
        denom = np.maximum(sn[:, k] - mi[:, j], 1)
        peer_ret[c] = (ss[:, k] - ri[:, j] * mi[:, j]) / denom
    for c in cols:
        j, k = col_pos[c], sec_pos[sector_of[c]]
        own_ab = ri[:, j] - peer_ret[c]
        hit = np.where(mi[:, j] & (ri[:, j] < -0.15) & (own_ab < -0.12) & (sn[:, k] >= 10))[0]
        last = -999
        for t in hit:
            if t - last < 20:  # one event per crash episode
                continue
            last = t
            if t < 1 or t + 20 >= len(R):
                continue
            if ri[t + 1, j] > 0.25:  # immediate reversal = likely a bad print
                continue
            peer_ab = peer_ret[c] - mx[:, k]
            share = dvbar.iloc[t][sec_cols[sector_of[c]]]
            share = share[M.iloc[t][sec_cols[sector_of[c]]].values]
            hdv, hhi, _ = entropy_norm(share.values)
            own_share = share.get(c, np.nan) / share.sum() if share.sum() > 0 else np.nan
            rank = share.rank(ascending=False).get(c, np.nan)
            events.append({
                "date": R.index[t], "symbol": c, "sector": sector_of[c],
                "own_ret_d0": ri[t, j], "own_ab_d0": own_ab[t],
                "peer_car_d0": peer_ab[t],
                "peer_car_0_5": peer_ab[t:t + 6].sum(),
                "peer_car_1_20": peer_ab[t + 1:t + 21].sum(),
                "own_car_1_20": (ri[t + 1:t + 21, j] - peer_ret[c][t + 1:t + 21]).sum(),
                "firm_dv_share_in_sector": own_share, "firm_rank_in_sector": rank,
                "sector_dv_entropy_norm": hdv, "sector_dv_hhi": hhi, "n_peers": int(sn[t, k] - 1),
            })
    ev = pd.DataFrame(events)
    # same-day clusters in one sector look like industry news, not one firm's death
    ev["cluster"] = ev.groupby(["sector", "date"])["symbol"].transform("count")
    ev = ev[ev["cluster"] == 1].drop(columns="cluster")
    ev.to_csv(OUT / "test3_events.csv", index=False)
    log(f"Test 3: {len(ev)} isolated idiosyncratic crash events")

    def summ(g: pd.DataFrame) -> pd.Series:
        n = len(g)
        out = {"n_events": n, "own_ab_d0": g["own_ab_d0"].mean()}
        for col in ["peer_car_d0", "peer_car_0_5", "peer_car_1_20"]:
            x = g[col].dropna()
            out[col] = x.mean()
            out[f"t_{col}"] = x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan
        out["pct_peer_d0_negative"] = (g["peer_car_d0"] < 0).mean()
        return pd.Series(out)

    by_sector = ev.groupby("sector").apply(summ).sort_values("peer_car_d0")
    ev["firm_size"] = np.where(ev["firm_rank_in_sector"] <= 5, "top-5 in sector", "rest")
    by_size = ev.groupby("firm_size").apply(summ)
    ev["sector_conc"] = pd.qcut(ev["sector_dv_hhi"], 3, labels=["fragmented (high H)", "middle", "concentrated (low H)"])
    by_conc = ev.groupby("sector_conc", observed=True).apply(summ)
    allr = summ(ev)
    by_sector.to_csv(OUT / "test3_by_sector.csv")
    by_size.to_csv(OUT / "test3_by_firm_size.csv")
    by_conc.to_csv(OUT / "test3_by_sector_concentration.csv")
    log("\nAll events\n" + allr.round(4).to_string())
    log("\nBy sector\n" + by_sector.round(4).to_string())
    log("\nBy firm size\n" + by_size.round(4).to_string())
    log("\nBy sector concentration\n" + by_conc.round(4).to_string())
    return {
        "all": {k: safe(v) for k, v in allr.items()},
        "by_sector": {s: {k: safe(v) for k, v in r.items()} for s, r in by_sector.iterrows()},
        "by_firm_size": {s: {k: safe(v) for k, v in r.items()} for s, r in by_size.iterrows()},
        "by_sector_concentration": {str(s): {k: safe(v) for k, v in r.items()} for s, r in by_conc.iterrows()},
    }


def main() -> None:
    summary = {}
    log("Loading US panel")
    rets, dv = load_panel(DATA / "extended_prices.parquet", max_abs_ret=0.5, price_floor=1.0)
    mask = us_pit_mask(rets)
    log(f"US: {rets.shape[0]} days x {rets.shape[1]} symbols, avg members/day {mask.sum(1).mean():.0f}")

    summary["test1"] = test1_portfolio_entropy(rets, mask)
    us = entropy_series(rets, mask, dv, "US", top_n=None)
    summary["test2_us"] = test2_analyse(us, "US")
    summary["test3"] = test3_death_test(rets, mask, dv)
    del rets, dv, mask

    log("Loading India (NSE survivorship-free) panel")
    rin, dvin = load_panel(DATA / "nse_survivorship_free.parquet", max_abs_ret=0.5)
    min_in = rin.notna()
    india = entropy_series(rin, min_in, dvin, "India", top_n=300)
    summary["test2_india"] = test2_analyse(india, "India")

    with open(OUT / "summary.json", "w") as f:
        json.dump(summary, f, indent=2,
                  default=lambda o: safe(o) if isinstance(o, (np.integer, np.floating)) else str(o))
    log("Done. Results in results/entropy_research/")


if __name__ == "__main__":
    main()
