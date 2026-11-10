"""
NSE corporate-action audit — find & classify unadjusted splits / bonuses
========================================================================
Background (2026-11-09): while doing event studies we found that the
survivorship-free NSE panels (data_processed/nse_survivorship_free*.parquet)
still contain one-day -50%..-80% moves that are really unadjusted splits and
bonus issues (CHOLAFIN 1:5 on 2019-06-14, INFY bonuses on 2014-12-02 /
2015-06-15 / 2018-09-04, ...). `run_nse_longshort.py` only clips returns at
[-95%, +200%], so these pass straight into factor scores, leg returns and the
equal-weight benchmark.

This module (import-only helpers + a CLI) does STEP 1 of the audit:

  1. scan a long-format parquet (date, symbol, open, high, low, close, volume)
     for moves between CONSECUTIVE rows of a symbol beyond +/-40%
     (plus an "extended" tier of -20..-40% moves that sit on a clean bonus /
     split ratio AND that Yahoo contradicts);
  2. classify each as corporate action vs genuine crash/jump vs bad tick using
        (a) nearness to a "nice" ratio (1:2, 1:3, 1:4, 1:5, 1:10, 2:3 ...),
        (b) whether the move persists (a spike that reverts is a bad tick),
        (c) the split/dividend-ADJUSTED Yahoo close in nse_prices_clean.parquet
            (324 of the survivorship-free names exist there). If Yahoo shows
            no big move on the same date while the bhavcopy close fell 50-80%,
            the bhavcopy close is unadjusted -> confirmed corporate action;
  3. write results/nse_data_audit/corporate_action_suspects.csv.

`classify_events()` is reused by scripts/build_nse_adjusted_panels.py to build
the corrected panels, so the CSV and the fix can never disagree.

Run:
    .venv/bin/python scripts/nse_ca_audit.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DATA = ROOT / "data_processed"
PANELS = {
    "top500": DATA / "nse_survivorship_free.parquet",
    "top150": DATA / "nse_survivorship_free_top150.parquet",
}
YAHOO = DATA / "nse_prices_clean.parquet"
OUT_DIR = ROOT / "results" / "nse_data_audit"

# ── thresholds ────────────────────────────────────────────────────────────────
BIG = 0.40               # |close-to-close move| that makes a row a suspect
EXT_LO = 0.20            # extended tier: drops of 20..40% ...
NICE_TOL = 0.08          # "clean ratio" tolerance when Yahoo can also vouch for / against the move
NICE_TOL_LOOSE = 0.15    # no-Yahoo, consecutive-day drop: a split day often also carries a +/-10% real move
NICE_TOL_TIGHT = 0.03    # snap-to-nice tolerance for Yahoo-derived factors
NICE_TOL_LONGGAP = 0.02  # razor-tight: only trust a ratio across a >5-day hole if it is this clean
DEEP_Q = 0.35            # q <= 0.35 (a -65% or worse day) is accepted as a split without the turnover test
TURN_VETO = 3.0          # post/pre traded-VALUE ratio above this = a crash with a volume blow-up, not a split
YAHOO_QUIET = 0.25       # Yahoo |ret| below this while bhavcopy |ret|>40% => Yahoo saw no crash
YAHOO_SAME = 0.15        # Yahoo ret within this of the bhavcopy ret => Yahoo agrees with the move
SHORT_GAP = 5            # calendar days: "consecutive trading days" (weekends/holidays)
REVERT_WINDOW = 10       # rows after the event inspected for a reversal
REVERT_BAND = (0.80, 1.25)   # post-event close back inside this band of the pre-event close => bad tick

# post/pre price ratios produced by Indian splits, bonuses and combinations
#   1:1 bonus / 10->5 split = 0.5 ; 2:1 bonus = 1/3 ; 3:1 = 0.25 ; 10->2 / 4:1 = 0.2 ;
#   3:2 bonus / 5->2 = 0.4 ; 10->1 = 0.1 ; 10->0.5 / 20:1 = 0.05 ; 100->1 = 0.01
#   1:2 bonus = 2/3 ; 1:3 = 3/4 ; 1:4 = 4/5 ; 2:3 = 0.6
NICE_DOWN = np.array([0.5, 1 / 3, 0.25, 0.2, 0.4, 1 / 6, 1 / 8, 0.1, 0.05, 0.02, 0.01,
                      2 / 3, 0.75, 0.8, 0.6])
NICE_UP = np.array([2.0, 3.0, 4.0, 5.0, 10.0])      # reverse splits / consolidations
NICE_ALL = np.concatenate([NICE_DOWN, NICE_UP])


def nearest_nice(q: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """For each ratio q return (nearest clean ratio, relative deviation |q/n-1|)."""
    q = np.asarray(q, dtype=float)
    dev = np.abs(q[:, None] / NICE_ALL[None, :] - 1.0)
    j = dev.argmin(axis=1)
    return NICE_ALL[j], dev[np.arange(len(q)), j]


def _prep_panel(df: pd.DataFrame) -> pd.DataFrame:
    d = df[["date", "symbol", "close"] + (["volume"] if "volume" in df.columns else [])].copy()
    d["date"] = pd.to_datetime(d["date"])
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    g = d.groupby("symbol", sort=False)
    d["prev_close"] = g["close"].shift(1)
    d["prev_date"] = g["date"].shift(1)
    d["gap_days"] = (d["date"] - d["prev_date"]).dt.days
    d["q"] = d["close"] / d["prev_close"]                 # post / pre price ratio
    d["ret"] = d["q"] - 1.0
    # was the previous row the previous *panel* trading day? (=> the backtest engine
    # actually computes this return; across a NaN hole pct_change gives NaN)
    alld = np.sort(d["date"].unique())
    pos = pd.Series(np.arange(len(alld)), index=alld)
    d["engine_visible"] = (d["date"].map(pos) - d["prev_date"].map(pos)) == 1
    # forward path (to separate a persistent level shift from a one-day bad tick)
    fwd = {}
    for k in range(1, REVERT_WINDOW + 1):
        c = g["close"].shift(-k)
        dd = (g["date"].shift(-k) - d["date"]).dt.days
        fwd[k] = (c / d["prev_close"]).where(dd <= 20)
    F = pd.DataFrame(fwd)
    inside = (F >= REVERT_BAND[0]) & (F <= REVERT_BAND[1])
    d["reverts"] = inside.any(axis=1)
    d["n_fwd_rows"] = F.notna().sum(axis=1)
    return d


def _turnover_continuity(d: pd.DataFrame, cand_idx: np.ndarray) -> np.ndarray:
    """turn_ratio = [median share volume of the 10 rows after / before the event] x q.
    A split multiplies the share count by 1/q, so traded VALUE (price x volume) is
    continuous => turn_ratio ~ 1 (empirically 0.3-1.4 on Yahoo-confirmed splits). A real
    crash blows traded value up (median ~3 on spike/reversal cases). NaN if too few rows."""
    if "volume" not in d.columns or len(cand_idx) == 0:
        return np.full(len(cand_idx), np.nan)
    n = len(d)
    vol = d["volume"].to_numpy(float)
    code = pd.factorize(d["symbol"])[0]
    day = d["date"].to_numpy("datetime64[D]").astype(np.int64)

    def med(offs):
        idx = cand_idx[:, None] + offs[None, :]
        inb = (idx >= 0) & (idx < n)
        ic = np.clip(idx, 0, n - 1)
        ok = inb & (code[ic] == code[cand_idx][:, None]) & (np.abs(day[ic] - day[cand_idx][:, None]) <= 30)
        v = np.where(ok & (vol[ic] > 0), vol[ic], np.nan)
        with np.errstate(all="ignore"):
            m = np.nanmedian(v, axis=1)
        m[ok.sum(axis=1) < 3] = np.nan
        return m

    pre = med(np.arange(-10, 0))
    post = med(np.arange(1, 11))
    q = (d["close"] / d["prev_close"]).to_numpy()[cand_idx]
    return post / pre * q


def _yahoo_bridge(d: pd.DataFrame, yahoo: pd.DataFrame) -> pd.Series:
    """Yahoo (split+dividend ADJUSTED) return from its last row on/before the
    event's prior bhavcopy date to its first row on/after the event date.
    NaN if the symbol/dates are not in Yahoo or Yahoo's own rows are >6 days away."""
    y = yahoo[["date", "symbol", "close"]].copy()
    y["date"] = pd.to_datetime(y["date"])
    y = y.sort_values(["symbol", "date"])
    out = pd.Series(np.nan, index=d.index)
    ysyms = set(y["symbol"].unique())
    ev = d[d["symbol"].isin(ysyms)]
    for sym, grp in ev.groupby("symbol"):
        ys = y[y["symbol"] == sym]
        yd = ys["date"].to_numpy()
        yc = ys["close"].to_numpy()
        for idx, row in grp.iterrows():
            i0 = np.searchsorted(yd, np.datetime64(row["prev_date"]), side="right") - 1
            i1 = np.searchsorted(yd, np.datetime64(row["date"]), side="left")
            if i0 < 0 or i1 >= len(yd):
                continue
            if (row["prev_date"] - pd.Timestamp(yd[i0])).days > 6 or (pd.Timestamp(yd[i1]) - row["date"]).days > 6:
                continue
            out.at[idx] = yc[i1] / yc[i0] - 1.0
    return out


# Documented genuine crashes the data-driven rules cannot separate from a split
# (no Yahoo history; the ratio happens to sit within 15% of a clean one).
MANUAL_GENUINE = {
    ("SATYAMCOMP", "2009-01-07"): "Satyam accounting-fraud disclosure, -78% in one session (real loss, not a split)",
}


def classify_events(panel: pd.DataFrame, yahoo: pd.DataFrame | None, label: str = "") -> pd.DataFrame:
    """Return one row per suspect event with features + verdict + adjustment factor.

    Population: consecutive rows of one symbol whose close-to-close move exceeds +/-40%
    ("primary_gt40", any gap), plus "extended_20_40": drops of 20-40% on short gaps
    (bonus 2:3 / 3:4 / 4:5 sized actions) that only count if Yahoo contradicts them.

    Verdicts
      CA_CONFIRMED_YAHOO  Yahoo's split-adjusted close shows no such move (|ret|<25%) while the
                          bhavcopy close moved >=15pp differently  -> unadjusted corporate action
      CA_LIKELY_NICE      no Yahoo cover (or Yahoo equally unadjusted), a persistent one-day DROP
                          within 15% of a clean split/bonus ratio, traded-value continuous
      BAD_TICK            price came back to its pre-event level inside 10 rows (spike / reversal)
      GENUINE_LIKELY      Yahoo shows the same move and the ratio is not clean (or a jump up)
      UNCERTAIN           persistent, not clean / no independent evidence (left untouched)

    adj_factor = multiplier for every PRE-event price (<1 for splits) that makes the series
    continuous; NaN unless the verdict is a corporate action.
    """
    d = _prep_panel(panel)
    big = d["ret"].abs() > BIG
    ext = (d["ret"] < -EXT_LO) & (d["ret"] >= -BIG) & (d["gap_days"] <= SHORT_GAP)
    sel = (big | ext) & d["prev_close"].notna()
    cand_idx = np.flatnonzero(sel.to_numpy())
    cand = d.loc[sel].copy()
    cand["tier"] = np.where(cand["ret"].abs() > BIG, "primary_gt40", "extended_20_40")
    cand["turn_ratio"] = _turnover_continuity(d, cand_idx)

    n_val, n_dev = nearest_nice(cand["q"].to_numpy())
    cand["nice_ratio"] = n_val
    cand["nice_dev"] = n_dev
    cand["is_nice"] = cand["nice_dev"] <= NICE_TOL

    if yahoo is not None:
        cand["yahoo_ret"] = _yahoo_bridge(cand, yahoo)
    else:
        cand["yahoo_ret"] = np.nan
    yr = cand["yahoo_ret"]
    # Yahoo has its own artefacts (e.g. +889% where it mis-dated a split): ignore wild values
    yr = yr.where((yr > -0.97) & (yr < 1.5))
    cand["yahoo_ret"] = yr
    short = (cand["gap_days"] <= SHORT_GAP).to_numpy()
    down = (cand["q"] < 1).to_numpy()
    cand["yahoo_quiet"] = (yr.notna() & (yr.abs() < YAHOO_QUIET)
                           & ((yr - cand["ret"]).abs() > YAHOO_SAME))
    cand["yahoo_agrees"] = yr.notna() & ((yr - cand["ret"]).abs() <= YAHOO_SAME)
    yq = cand["yahoo_quiet"].to_numpy()
    ya = cand["yahoo_agrees"].to_numpy()
    rev = cand["reverts"].to_numpy()
    nd = cand["nice_dev"].to_numpy()
    tr = cand["turn_ratio"].to_numpy()
    prim = (cand["tier"] == "primary_gt40").to_numpy()

    v = np.full(len(cand), "UNCERTAIN", dtype=object)
    # 1) no independent evidence, consecutive-day persistent DROP near a clean ratio
    # A -65% or deeper one-day close-to-close drop is not a market move on NSE (price bands cap most
    # names at +/-20%); the traded-value veto only arbitrates the milder -40..-65% (1:1 bonus-sized) cases,
    # where real crashes (Oct-2008, DHFL 2018) show a 4-5x traded-value blow-up that splits do not.
    deep = cand["q"].to_numpy() <= DEEP_Q
    no_veto = deep | ~(np.isfinite(tr) & (tr > TURN_VETO))
    v[prim & short & down & ~rev & (nd <= NICE_TOL_LOOSE) & no_veto & ~ya] = "CA_LIKELY_NICE"
    # 2) Yahoo says "same move": only a corporate action if the ratio is tight (Yahoo unadjusted too)
    v[prim & short & down & ~rev & ya & (nd <= NICE_TOL) & no_veto] = "CA_LIKELY_NICE"
    v[prim & ya & ~((nd <= NICE_TOL) & short & down & ~rev & no_veto)] = "GENUINE_LIKELY"
    # 3) long gap: razor-tight ratio only
    v[prim & ~short & down & ~rev & ~ya & (nd <= NICE_TOL_LONGGAP)] = "CA_LIKELY_NICE"
    # 4) reversals
    v[prim & rev & ~yq] = "BAD_TICK"
    # 5) Yahoo-quiet trumps everything (independent, split-adjusted evidence)
    v[yq & prim] = "CA_CONFIRMED_YAHOO"
    # extended tier: Yahoo-contradicted AND a clean bonus-sized ratio
    v[~prim] = np.where(yq[~prim] & (nd[~prim] <= 0.10), "CA_CONFIRMED_YAHOO", "GENUINE_LIKELY")
    cand["verdict"] = v
    cand["note"] = ""
    for (s_, dt_), why in MANUAL_GENUINE.items():
        m = (cand["symbol"] == s_) & (cand["date"] == pd.Timestamp(dt_))
        cand.loc[m, "verdict"] = "GENUINE_LIKELY"
        cand.loc[m, "note"] = "manual: " + why

    # adjustment factor (post/pre) for the verdicts we will repair
    fac = np.full(len(cand), np.nan)
    ca = cand["verdict"].isin(["CA_CONFIRMED_YAHOO", "CA_LIKELY_NICE"]).to_numpy()
    # best estimate = bhavcopy ratio divided by Yahoo's real same-day move (= pure split factor)
    from_yahoo = (cand["q"] / (1.0 + cand["yahoo_ret"])).to_numpy()
    ok_y = np.isfinite(from_yahoo) & (from_yahoo > 0)
    snap_y, dev_y = nearest_nice(np.where(ok_y, from_yahoo, 1.0))
    use_y = ca & yq & ok_y
    fac[use_y] = np.where(dev_y[use_y] <= NICE_TOL_TIGHT, snap_y[use_y], from_yahoo[use_y])
    use_n = ca & ~use_y
    fac[use_n] = cand["nice_ratio"].to_numpy()[use_n]
    cand["adj_factor"] = fac
    cand["adj_basis"] = np.where(use_y, "yahoo_ratio_snapped", np.where(use_n, "snapped_nice_ratio", ""))
    cand.insert(0, "panel", label)
    return cand


def build_suspect_table(panels: dict[str, pd.DataFrame], yahoo: pd.DataFrame | None) -> pd.DataFrame:
    parts = [classify_events(df, yahoo, label) for label, df in panels.items()]
    allr = pd.concat(parts, ignore_index=True)
    key = ["symbol", "date"]
    # one row per (symbol,date); record which panel(s) contain it
    memb = allr.groupby(key)["panel"].apply(lambda s: "+".join(sorted(set(s)))).rename("in_panels")
    first = allr.sort_values("panel").drop_duplicates(key, keep="first").drop(columns="panel")
    first = first.merge(memb, on=key)
    return first


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    yahoo = pd.read_parquet(YAHOO)
    panels = {k: pd.read_parquet(p) for k, p in PANELS.items()}
    tbl = build_suspect_table(panels, yahoo)

    cols = ["symbol", "date", "in_panels", "tier", "prev_date", "gap_days", "engine_visible",
            "prev_close", "close", "ret", "q", "nice_ratio", "nice_dev", "is_nice", "reverts",
            "turn_ratio", "yahoo_ret", "yahoo_quiet", "yahoo_agrees", "verdict", "adj_factor", "adj_basis", "note"]
    tbl = tbl[cols].sort_values(["date", "symbol"]).reset_index(drop=True)
    for c in ("ret", "q", "nice_dev", "yahoo_ret", "turn_ratio"):
        tbl[c] = tbl[c].round(4)
    tbl["adj_factor"] = tbl["adj_factor"].round(5)
    out = OUT_DIR / "corporate_action_suspects.csv"
    tbl.to_csv(out, index=False)

    print("=" * 78)
    print("NSE CORPORATE-ACTION AUDIT")
    print("=" * 78)
    for lab, df in panels.items():
        sub = tbl[tbl["in_panels"].str.contains(lab)]
        pr = sub[sub["tier"] == "primary_gt40"]
        print(f"\n[{lab}] rows={len(df):,} symbols={df['symbol'].nunique()}  suspects: "
              f"{len(pr)} primary (>40%) + {(sub['tier']=='extended_20_40').sum()} extended")
        print(pr["verdict"].value_counts().to_string())
    print(f"\nsaved {out.relative_to(ROOT)}  ({len(tbl)} unique (symbol,date) rows)")
    for sym, dt in [("CHOLAFIN", "2019-06-14"), ("INFY", "2014-12-02"), ("INFY", "2015-06-15"), ("INFY", "2018-09-04")]:
        r = tbl[(tbl["symbol"] == sym) & (tbl["date"] == dt)]
        print("  known example:", sym, dt, "->",
              r[["ret", "nice_ratio", "yahoo_ret", "verdict", "adj_factor"]].to_dict("records") if len(r) else "NOT FOUND")


if __name__ == "__main__":
    main()
