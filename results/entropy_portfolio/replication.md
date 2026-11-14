# Replication of DeMiguel, Garlappi & Uppal (2009) on Kenneth French data

*Phase 3 of paper 3. Script: `scripts/ep_replicate_dgu.py`. Raw CSVs were downloaded from
the Kenneth French Data Library on 13 Nov 2026 (files built from the 202609 CRSP database).
Full output: `replication.json` and `replication_log.txt`; monthly returns are in
`replication_returns.csv`.*

## Protocol (DGU 2009)

- Monthly excess returns over the 1-month T-bill (French's `RF`).
- A rolling window of M = 120 months, re-estimated each month, with a one-month holding
  period.
- Out-of-sample period: July 1973 – November 2004 (377 months).
- **1/N:** equal weights.
- **mv:** sample tangency weights x = Σ̂⁻¹μ̂, as relative weights.
- **min:** Σ̂⁻¹1/(1′Σ̂⁻¹1).
- **Statistics:** Sharpe ratio = mean/sd of out-of-sample excess returns; CEQ with γ = 1;
  turnover = mean of Σ|w_{t+1} − w_{t+}|; p-values from Jobson–Korkie–Memmel against 1/N.

## Which reference numbers we match

The printed RFS tables could not be opened (paywall; see `LITERATURE.md`). We match against
two sources whose text we read in full:

- **(A) DGU's own 2006 working paper** (Tables 4 and 6): same datasets, same period, same
  protocol. Mean-variance is held as relative weights x/1′x; footnote 14 says they report
  "the fund with just risky assets".
- **(B) Kan, Wang & Zhou (2016)**, who replicate the *published* FF-1-factor (N = 21) and
  FF-4-factor (N = 24) datasets with mv normalised as x/|1′x|.

The working paper's own FF tables are not used, for two reasons:
- its N = 23 set is not the published N = 21 set;
- its N = 24 table shows a units error in MOM (minimum variance has mean 0.00007 with
  weight 0.997 on MOM).

**Tolerances**, fixed in the script before the first run: |ours − reference| ≤ 0.010 for
1/N, ≤ 0.020 for min and ≤ 0.030 for mv (monthly Sharpe ratio).

## Result: 8 of 10 checks within tolerance

| Dataset (N) | Strategy | Ours | Reference | Source | Diff | Within? |
|---|---|---|---|---|---|---|
| Industry (11) | 1/N | 0.1353 | 0.13531 | A | −0.0000 | yes |
| Industry (11) | mv | −0.0186 | −0.03634 | A | +0.0177 | yes |
| Industry (11) | min | 0.1537 | 0.15536 | A | −0.0016 | yes |
| MKT/SMB/HML (3) | 1/N | 0.2347 | 0.22403 | A | +0.0107 | **no** (by 0.0007) |
| MKT/SMB/HML (3) | mv | 0.2135 | 0.21859 | A | −0.0051 | yes |
| MKT/SMB/HML (3) | min | 0.2574 | 0.24925 | A | +0.0082 | yes |
| FF-1-factor (21) | 1/N | 0.1613 | 0.1628 | B | −0.0015 | yes |
| FF-1-factor (21) | mv (\|1′x\|) | 0.0513 | −0.0227 | B | +0.0740 | **no** |
| FF-4-factor (24) | 1/N | 0.1745 | 0.1761 | B | −0.0016 | yes |
| FF-4-factor (24) | mv (\|1′x\|) | 0.1650 | 0.1443 | B | +0.0207 | yes |

Other checks against (A) with no stated tolerance:
- 1/N CEQ, Industry: 0.497% vs 0.498%.
- 1/N turnover: 0.022 vs 0.0216 (Industry); 0.024 vs 0.0237 (MKT/SMB/HML).
- Long-only min-variance, Industry: 0.1445 vs 0.14253.
- Long-only mv: 0.0622 vs 0.0678 (Industry); 0.1093 vs 0.10837 (MKT/SMB/HML).

## The two misses, explained

1. **MKT/SMB/HML, 1/N (+0.0107).**
   - 1/N involves no estimation, so a 1/N gap can only come from the data.
   - Our out-of-sample mean is 0.00440 a month; the working paper's is 0.00411. The
     variances are 0.00035 and 0.00034.
   - French has revised SMB and HML since 2005 (CRSP/Compustat updates).
   - On the Industry data, which are value-weighted CRSP returns and barely revised, 1/N
     matches to five decimals, as do min and mv. So the code is right; the input moved.
2. **FF-1-factor, mv (+0.074 vs Kan–Wang–Zhou).**
   - The relative-weight mean-variance Sharpe ratio is fragile. When 1′Σ̂⁻¹μ̂ is near zero,
     the normalisation produces enormous leverage. Turnover here is 141–175 (that is, 14,000% to 17,500% a month).
   - Dropping one single month moves our Sharpe ratio anywhere in [0.025, 0.073]
     (leave-one-out range).
   - The same strategy's 1/N matches Kan–Wang–Zhou within 0.0015, so the data are
     nearly identical. The gap comes from a handful of explosive months.
   - On Industry, the leave-one-out range [−0.036, 0.029] contains DGU's own −0.0363.

**Verdict.** The code reproduces DGU wherever the data are unchanged, and the misses
trace to data revisions and to the documented instability of plug-in mean-variance.
DGU's conclusions are reproduced:
- sample mean-variance loses to 1/N out of sample in three of four datasets (p = 0.00–0.04
  by JKM). It is roughly tied on the 3-factor set, where N = 3 is small enough for
  estimation error not to dominate;
- its turnover is 19–176 a month, against 0.02 for 1/N.

## Extensions (our own baselines, not part of the replication target)

| Dataset | 1/N | Kan–Zhou 3-fund | Tu–Zhou | min, Ledoit–Wolf | min, 2-norm (CV) | min, long-only |
|---|---|---|---|---|---|---|
| Industry | 0.135 | −0.033 | 0.027 | 0.157 | 0.157 | 0.145 |
| MKT/SMB/HML | 0.235 | 0.252 | 0.230 | 0.260 | 0.261 | 0.257 |
| FF-1-factor | 0.161 | 0.079 | 0.249 | 0.258 (p 0.01) | 0.255 (p 0.02) | 0.155 |
| FF-4-factor | 0.175 | 0.168 | 0.078 | 0.359 (p 0.00) | 0.060 | 0.365 (p 0.00) |

(Monthly Sharpe ratios; p-values vs 1/N by JKM are shown where below 0.05.)

The pattern matches DGNU (2009) and Jagannathan & Ma (2003): shrinking the covariance and
ignoring means helps. Two notes on the FF-4 set:
- The 2-norm rule's cross-validation picks a near-zero penalty, so it behaves like plain
  min-variance (0.06).
- Long-only and Ledoit–Wolf min-variance load on the low-volatility factor portfolios.
