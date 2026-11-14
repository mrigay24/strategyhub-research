"""Phase 3: replicate DeMiguel, Garlappi & Uppal (2009, RFS) on Kenneth French data.

Protocol (DGU 2009, section 2-3): monthly excess returns; rolling estimation window of
M = 120 months; rebalance monthly; out-of-sample returns from month M+1 to the end of the
sample; sample mean-variance weights as relative weights x/|1'x| with x = S^-1 mu; minimum
variance S^-1 1 / 1'S^-1 1; Sharpe ratio = mean/sd of out-of-sample excess returns;
CEQ = mean - (gamma/2) var with gamma = 1.

Datasets reproducible from the French library (the S&P-sector and MSCI-country datasets are
not French data and are skipped):
  Industry      10 value-weighted industry portfolios + market (N = 11), 1963-07..2004-11
  MKT/SMB/HML   the three Fama-French factors (N = 3),                     1963-07..2004-11
  FF-1-factor   20 size/BM portfolios + market (N = 21),                   1963-07..2004-11
  FF-4-factor   20 size/BM portfolios + MKT, SMB, HML, UMD (N = 24),       1963-07..2004-11

Raw files are downloaded from the Kenneth French Data Library if they are not already in
data_raw/french_ff/ (the raw CSVs, not a wrapper's cached copy).

Tolerance, fixed before the first run (2026-11-13) (monthly Sharpe ratio, ours minus published):
  1/N  |diff| <= 0.010     min  |diff| <= 0.020     mv  |diff| <= 0.030
French data are revised as CRSP is updated, so an exact match is not expected; 1/N is the
cleanest check because it involves no estimation.  Outputs:
  results/entropy_portfolio/replication.json, replication_returns.csv
"""
from __future__ import annotations

import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import ep_lib as L  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data_raw" / "french_ff"
OUT = ROOT / "results" / "entropy_portfolio"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
FILES = {
    "ind": "10_Industry_Portfolios",
    "p25": "25_Portfolios_5x5",
    "ff3": "F-F_Research_Data_Factors",
    "mom": "F-F_Momentum_Factor",
}
M = 120
GAMMA = 1.0
START, END = "1963-07", "2004-11"
TOL = {"1/N": 0.010, "min": 0.020, "mv": 0.030}

# Reference numbers (monthly out-of-sample Sharpe ratios).  The printed RFS Table 3 could
# not be opened (paywall; see LITERATURE.md), so we match against two sources whose text
# we could read in full:
#  (A) DGU's own working paper (2006 version, Tables 4 and 6), same datasets and period,
#      mean-variance as relative weights x / 1'x ("fund with just risky assets", fn 14);
#  (B) Kan, Wang & Zhou (2016 working paper), replication of the published FF-1-factor and
#      FF-4-factor datasets, mean-variance normalised as x / |1'x|.
# The WP's own FF tables are not used: its N=23 set differs from the published N=21 set, and
# its N=24 table shows a units error in MOM (min-variance mean 0.00007, weight 0.997 on MOM).
REFERENCE = {
    "Industry": {"src": "DGU 2006 WP Table 4", "mv_norm": "sum",
                 "1/N": 0.13531, "mv": -0.03634, "min": 0.15536},
    "MKT/SMB/HML": {"src": "DGU 2006 WP Table 6", "mv_norm": "sum",
                    "1/N": 0.22403, "mv": 0.21859, "min": 0.24925},
    "FF-1-factor": {"src": "Kan-Wang-Zhou 2016", "mv_norm": "abs",
                    "1/N": 0.1628, "mv": -0.0227, "min": None},
    "FF-4-factor": {"src": "Kan-Wang-Zhou 2016", "mv_norm": "abs",
                    "1/N": 0.1761, "mv": 0.1443, "min": None},
}


def ensure_raw():
    RAW.mkdir(parents=True, exist_ok=True)
    for stem in FILES.values():
        csv = RAW / f"{stem}.csv"
        if csv.exists():
            continue
        with urllib.request.urlopen(BASE + stem + "_CSV.zip", timeout=60) as r:
            z = zipfile.ZipFile(io.BytesIO(r.read()))
        name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
        csv.write_bytes(z.read(name))


def read_first_monthly_block(path: Path) -> pd.DataFrame:
    """First data block of a French CSV (value-weighted monthly returns), in decimals."""
    lines = path.read_text(errors="ignore").splitlines()
    i = next(k for k, s in enumerate(lines) if s.strip().startswith(",") and k > 0)
    header = [h.strip() for h in lines[i].split(",")]
    rows = []
    for s in lines[i + 1:]:
        parts = [p.strip() for p in s.split(",")]
        if len(parts) < 2 or not parts[0].isdigit() or len(parts[0]) != 6:
            break
        rows.append(parts)
    df = pd.DataFrame(rows, columns=header[: len(rows[0])])
    df.index = pd.PeriodIndex(df.iloc[:, 0].str[:4] + "-" + df.iloc[:, 0].str[4:], freq="M")
    df = df.iloc[:, 1:].astype(float)
    df = df.where(df > -99.0) / 100.0
    df.columns = [c.strip() for c in df.columns]
    return df


def build_datasets():
    ind = read_first_monthly_block(RAW / "10_Industry_Portfolios.csv")
    p25 = read_first_monthly_block(RAW / "25_Portfolios_5x5.csv")
    ff3 = read_first_monthly_block(RAW / "F-F_Research_Data_Factors.csv")
    mom = read_first_monthly_block(RAW / "F-F_Momentum_Factor.csv")
    sl = slice(pd.Period(START, "M"), pd.Period(END, "M"))
    ind, p25, ff3, mom = ind.loc[sl], p25.loc[sl], ff3.loc[sl], mom.loc[sl]
    rf = ff3["RF"]
    mkt = ff3["Mkt-RF"].rename("MKT")
    # DGU drop the five portfolios containing the largest firms (the ME5 row), because MKT,
    # SMB and HML are almost a linear combination of the 25 portfolios.
    big = [c for c in p25.columns if c.startswith("BIG") or c.startswith("ME5")]
    p20 = p25.drop(columns=big)
    assert p20.shape[1] == 20, p20.columns
    ds = {
        "Industry": pd.concat([ind.sub(rf, axis=0), mkt], axis=1),
        "MKT/SMB/HML": ff3[["Mkt-RF", "SMB", "HML"]],
        "FF-1-factor": pd.concat([p20.sub(rf, axis=0), mkt], axis=1),
        "FF-4-factor": pd.concat([p20.sub(rf, axis=0), ff3[["Mkt-RF", "SMB", "HML"]],
                                  mom.iloc[:, 0].rename("UMD")], axis=1),
    }
    for k, v in ds.items():
        assert not v.isna().any().any(), k
    return ds, rf


def run_dataset(X: pd.DataFrame):
    R = X.values
    T, N = R.shape
    names = ["1/N", "mv", "mv|abs|", "min", "mv-c", "min-c", "mv-min(KZ)", "TZ(1/N+ML)", "min-LW",
             "min-norm2-CV"]
    rets = {k: [] for k in names}
    weights = {k: [] for k in names}
    for t in range(M, T):
        W = R[t - M:t]
        mu = W.mean(0)
        S = L.cov_mle(W)
        ws = {
            "1/N": L.w_ew(N),
            "mv": (lambda x: x / x.sum())(np.linalg.solve(S, mu)),
            "mv|abs|": L.w_mv(mu, S),
            "min": L.w_gmv(S),
            "mv-c": L.w_mv_longonly(mu, S, GAMMA),
            "min-c": L.w_gmv_longonly(S),
            "mv-min(KZ)": L.w_kz3(mu, S, M, GAMMA),
            "TZ(1/N+ML)": L.w_tz(mu, S, M, gamma=3.0)[0],
            "min-LW": L.w_gmv(L.lw_identity(W)[0]),
            "min-norm2-CV": L.w_gmv_norm2_cv(W),
        }
        for k in names:
            rets[k].append(float(ws[k] @ R[t]))
            weights[k].append(ws[k])
    idx = X.index[M:]
    return pd.DataFrame(rets, index=idx), {k: np.array(v) for k, v in weights.items()}


def main():
    ensure_raw()
    ds, rf = build_datasets()
    report, all_rets = {}, {}
    for name, X in ds.items():
        r, w = run_dataset(X)
        base = r["1/N"].values
        rows = {}
        for k in r.columns:
            x = r[k].values
            z, p = L.jkm_test(x, base) if k != "1/N" else (np.nan, np.nan)
            # turnover: DGU average sum |w_{t+1} - w_t+| using total returns for the drift
            tot = X.values[M:] + rf.loc[X.index[M:]].values[:, None]
            to = L.turnover_series(w[k], tot)[1:].mean()
            rows[k] = {"sharpe": L.sharpe(x), "p_vs_1N_jkm": p, "ceq_g1": L.ceq(x, GAMMA),
                       "turnover": float(to), "neff_renyi2_avg": float(np.mean(
                           [L.neff_renyi2(v) for v in w[k]]))}
        pub = REFERENCE[name]
        checks = {}
        for k, tol in TOL.items():
            if pub.get(k) is not None:
                col = "mv|abs|" if (k == "mv" and pub["mv_norm"] == "abs") else k
                diff = rows[col]["sharpe"] - pub[k]
                checks[k] = {"ours": rows[col]["sharpe"], "reference": pub[k], "source":
                             pub["src"], "diff": diff, "tol": tol,
                             "within": bool(abs(diff) <= tol)}
        # fragility of the mean-variance Sharpe ratio: leave-one-month-out range
        for col in ("mv", "mv|abs|"):
            x = r[col].values
            loo = [L.sharpe(np.delete(x, i)) for i in range(len(x))]
            rows[col]["loo_min"], rows[col]["loo_max"] = float(min(loo)), float(max(loo))
        report[name] = {"N": X.shape[1], "T": X.shape[0], "oos_months": len(r),
                        "start": str(X.index[0]), "end": str(X.index[-1]),
                        "strategies": rows, "checks": checks}
        all_rets[name] = r
        print(f"\n== {name}: N={X.shape[1]}, T={X.shape[0]}, OOS={len(r)}")
        for k, v in rows.items():
            pubs = ""
            for kk, c in checks.items():
                col = "mv|abs|" if (kk == "mv" and pub["mv_norm"] == "abs") else kk
                if col == k:
                    pubs = f"  ref {c['reference']:.4f} diff {c['diff']:+.4f} {'OK' if c['within'] else 'MISS'}"
            if "loo_min" in v:
                pubs += f"  LOO range [{v['loo_min']:.3f}, {v['loo_max']:.3f}]"
            print(f"  {k:14s} SR {v['sharpe']:.4f}  p {v['p_vs_1N_jkm']:.2f}  CEQ "
                  f"{v['ceq_g1']*100:.3f}%  TO {v['turnover']:.3f}{pubs}")
    (OUT / "replication.json").write_text(json.dumps(report, indent=2))
    pd.concat(all_rets, axis=1).to_csv(OUT / "replication_returns.csv")
    n_ok = sum(c["within"] for d in report.values() for c in d["checks"].values())
    n_all = sum(len(d["checks"]) for d in report.values())
    print(f"\nWithin tolerance: {n_ok}/{n_all}")


if __name__ == "__main__":
    main()
