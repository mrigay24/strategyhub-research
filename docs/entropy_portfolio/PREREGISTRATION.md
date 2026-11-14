# Pre-registration: paper 3, "Hold as much entropy as you have ignorance"

*Committed 13 Nov 2026, before any real-data portfolio result was computed. Earlier phases
used only the Kenneth French replication data and simulated data. The only real-data facts
looked at before this commit are column names and date ranges. Any later change is logged
under "Deviations", with its date.*

## 1. Data

| | India (primary) | US (second market) |
|---|---|---|
| Prices | `data_processed/nse_survivorship_free_adj_nohole.parquet` (daily OHLCV, 2005-01-03 to 2025-06-30, corporate actions audited, KB §42) | `data_processed/extended_prices.parquet` (raw daily, 2000-01-03 to 2024-12-30); closes below $1 set to missing |
| Daily returns | `close.pct_change(fill_method=None)` on the pivoted panel | same |
| Membership | none beyond the liquidity rank (survivorship-free file) | point-in-time S&P 500 from `sp500_universe_lookup.csv` (the `us_pit_mask` logic of `scripts/entropy_research.py`) |
| Universe at month-end t | top **100** by 63-day average traded value (close × volume), among stocks with a close on t's last trading day, a close 12 months earlier, and ≥ 200 valid daily returns in the past 252 days | same rule within point-in-time S&P 500 members |
| Risk-free | **Proxy: 6.5% a year constant** (0.526% a month); see Deviation D1 | Kenneth French `RF` (1-month T-bill) |
| Pre-holdout evaluation | return months **2010-02 to 2020-12** | return months **2005-02 to 2020-12** |
| Holdout (touched once, at the end) | **2021-01 to 2025-06** (data end) | **2021-01 to 2024-12** (data end) |

- **Monthly stock returns** compound the daily returns within the month. After a delisting
  the position earns zero (cash at the last price). Excess return = return − risk-free.
- **Evaluation windows.** The first signal month is 2007-01 (India) and 2002-01 (US), when
  the slowest signal ("none", 24 months minimum) first exists. Real-time rules need 36
  months of realised IC, so they start 37 months later. All rules and baselines are
  compared on the same months.

## 2. Signals (prices only, textbook definitions)

Each is computed at month-end t from data up to t, then converted to normal scores
z = Φ⁻¹((rank − ½)/N) within the universe.

- **none:** mean monthly return over the past 36 months (≥ 24 required). This is the
  naive plug-in investor's forecast.
- **mom:** 12–1 momentum, the return from month-end t−12 to month-end t−1.
- **lowvol:** minus the standard deviation of daily returns over the past 252 days
  (≥ 200 required).

**Ex-ante information.** IC_s is the Spearman correlation of z_s with the month-(s+1)
returns. At month t only IC_s with s ≤ t−1 are used, over a 36-month window. D_s is the
cross-sectional sd of month-(s+1) returns, winsorised at the 1st and 99th percentiles.
R_e,s+1 is the 1/N return.

## 3. Portfolios

- **The entropy dial** (diagnostic): the Gibbs tilt wᵢ ∝ exp(βzᵢ), in the textbook
  direction of each signal, at fixed levels N_eff/N ∈ {1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4,
  0.3, 0.2, 0.1, 0.05}. **These curves are diagnostics only.** Picking a level by looking
  at them is in-sample.
- **Real-time rules** (decided in advance; evaluated):
  - **R1, theory (κ = 1), primary.** ĉ = (31/36)·max(0, 1 − 1/t̂²), with t̂ the t-statistic
    of the 36-month mean IC (ĉ = 0 if the mean IC ≤ 0). β\* maximises THEORY eq. (5.1)
    with:
    - μ_f = ĉ·ĪC·D̄;
    - D̄²σ²_ρ = D̄²·max(var(IC) − 1/(N−1), 0);
    - σ_ef = cov(R_e, IC·D) over the same 36 months;
    - γ = 2.5.
    The portfolio is Gibbs(β\*).
  - **R2, no-shrinkage plug-in.** As R1 with c = 1 whenever the mean IC > 0 (else 1/N).
    This was added after the simulation (THEORY §8), before any real data.
  - **R3, nested cross-validation.** Each month, choose the dial level (including 1/N)
    with the highest CEQ (γ = 2.5) over its own realised returns in the past 36 months.
  - **R1G, Grinold variant (secondary).** As R1, but with t̂² = 36·N·ĪC² and σ²_ρ = 0.
- **Baselines** on the same universe. All use the past 252 daily returns, scaled to
  monthly (×21); the plug-in rules use T = 252 in daily units.
  - 1/N.
  - Sample mean–variance, relative weights x/|1′x| (DGU).
  - Sample minimum variance.
  - Minimum variance with Ledoit–Wolf (2004) shrinkage.
  - Minimum variance with a 2-norm constraint, cross-validated (5 folds, minimum
    out-of-fold variance).
  - Long-only minimum variance (Jagannathan–Ma).
  - Long-only mean–variance (γ = 2.5).
  - Kan–Zhou three-fund (relative weights).
  - Tu–Zhou combination of 1/N and mean–variance (γ = 2.5, relative weights).

## 4. Costs

- **Turnover** = Σ|w_t − w_{t−1}⁺| (drifted weights). The cost is charged in the month of
  trading.
- **India, statutory, per side.** Approximate official schedule:
  - securities transaction tax 0.125% to May 2013, then 0.100%;
  - exchange transaction charge 0.00325%;
  - SEBI fee 0.0001%;
  - stamp duty 0.015% on buys (counted as 0.0075% per side);
  - GST of 18% on the exchange and SEBI charges.
  - Brokerage is taken as zero (discount delivery broking).
  - Total ≈ 0.111% per side from June 2013 and ≈ 0.136% before.
- **India, market impact, per side,** by liquidity tercile within the top 100 (rank by
  63-day traded value): 5 bps for the top third, 10 bps for the middle third, 20 bps for
  the bottom third.
- **US:** 10 bps per side (primary), with 25 and 50 bps as sensitivity.

## 5. Hypotheses, tests and decision rules

Primary criterion: monthly CEQ at γ = 2.5, net of costs. The Sharpe ratio is reported
alongside. Sharpe differences are tested with the Ledoit–Wolf (2008) studentised circular
block bootstrap (b = 5 months, 4,999 resamples; see deviation D2) and with
Jobson–Korkie–Memmel.

**H1. The 1/N puzzle holds in India with plug-in mean–variance.**
- Supported if, in India over 2010-02 to 2020-12 (gross of costs, as in DGU), sample
  mean–variance has a lower Sharpe ratio than 1/N with LW bootstrap p < 0.05.
- The US is reported the same way, as a replication.

**H2. The ex-ante entropy rule (R1) beats or matches 1/N and mean–variance, net of costs.**
- **Matches 1/N:** R1's net CEQ ≥ 1/N's, and R1's net Sharpe is not significantly below
  1/N's (LW p ≥ 0.05).
- **Beats 1/N:** the Sharpe difference is also positive with p < 0.05.
- **Beats mean–variance:** R1's net Sharpe exceeds sample mean–variance's with p < 0.05.
- This is judged per signal (none, mom, lowvol) and per market. "Supported" means it holds
  for at least two of the three signals in India.
- The simulation's power analysis says a significant win needs about 300–1,000 months at
  IC 0.02–0.03. **We expect "matches", not "beats".** A null on "beats" will be reported
  as low power, not as no effect.
- **Multiple testing.**
  - Hansen's (2005) SPA test, consistent p-value: all real-time rules (R1, R2, R3, R1G × 3
    signals = 12 models) against 1/N. The loss is the per-month mean–variance utility
    differential uₜ = rₜ − (γ/2)(rₜ − r̄)²; stationary bootstrap, mean block 6, 4,999
    resamples.
  - PBO (Bailey et al. 2017, CSCV with 16 blocks) over the 33 dial variants (11 levels ×
    3 signals), using the Sharpe ratio.

**H3. The optimal effective N falls as ex-ante information rises, by the amount theory
predicts.**
- **H3a, direction.** Across the six signal–market cases, the Spearman correlation
  between the evaluation-window mean IC and the ex-post best dial level is negative.
  This is reported descriptively, since six points carry little power.
- **H3b, amount (structural).** For each case, the full-information prediction is compared
  with the ex-post best level (CEQ, γ = 2.5).
  - The prediction is THEORY eq. (5.1) with c = 1, using the evaluation-window IC mean and
    variance, D̄ and σ_ef, at N = 100 normal scores.
  - The comparison uses a 90% stationary-bootstrap interval (mean block 6, 2,000
    resamples) for the argmax level.
  - Supported if the prediction falls inside the interval in at least 4 of the 6 cases.
- **H3c, information matching (real time).** The theory says R1 (κ = 1) does at least as
  well as R2 (no shrinkage). The simulation says the opposite when the signal is real. We
  report the net CEQ ranking of R1, R2 and R3 per case, and the LW test of R1 vs R2. A win
  for R2 is a failure of the proportional "ignorance share" rule; a win for R1 supports
  it.
- **H3d, calibration.** Pool the three signals within each market and regress the
  realised unit-tilt return fₜ₊₁ = IC_t·D_t on the shrunk forecast ĉ_t·ĪC_t·D̄_t, with
  Newey–West standard errors (6 lags).
  - Supported if the slope's 95% interval contains 1 and excludes 0.
  - The same regression on the unshrunk forecast is reported, since theory predicts a
    slope below 1 for it.

## 6. Holdout

After the pre-holdout run is written up (NOTE.md), the identical code is run once on the
holdout months. The commit hash is recorded in the holdout output. The holdout reports the
same tables for H1, H2 and H3c. With 48–54 months it has little power, so it is read as
"same sign or not".

## 7. What we will conclude

- **H1 supported, H2 "matches", H3b supported:** the paper claims that entropy matched to
  information is a safe default. It never does worse than 1/N, and the theory says where
  the optimum lies.
- **H3c lost by R1:** the paper says plainly that the proportional rule over-diversifies.
  The surviving version of the thesis is the threshold: with no information, hold 1/N.
- **H3b fails:** the structural model is wrong in real data. The likely reason is
  correlated residuals (THEORY §7.2), and the paper reports by how much.
- **Any null is reported.** We say "consistent with", never "proves".

## 8. Reproducibility

All seeds are fixed (`ep_lib.SEED`). One command per phase:
- `scripts/ep_replicate_dgu.py`
- `scripts/ep_simulate.py`
- `scripts/ep_real_data.py` (pre-holdout)
- `scripts/ep_real_data.py --holdout`

## Deviations

- **D1 (13 Nov 2026, before data).** The RBI DBIE 91-day T-bill fetch failed: the site is a
  JavaScript application and no CSV endpoint was reachable. FRED's India T-bill series
  (INTGSTINM193N) and the OECD 3-month rate (IR3TIB01INM156N) returned 404 or a bot
  challenge. Proxy: a constant 6.5% a year, roughly the average Indian 91-day T-bill yield
  over 2005–2025. A constant risk-free rate cancels exactly in CEQ *differences* between
  fully invested strategies. Sharpe ratio levels shift with it.
- **D2 (13 Nov 2026, before data).** Ledoit–Wolf (2008) bootstrap, simplified:
  - a Newey–West HAC standard error for the original statistic and a block-based standard
    error inside the bootstrap, instead of the prewhitened QS kernel;
  - the block size is fixed at b = 5 instead of calibrated (see LITERATURE §4).
