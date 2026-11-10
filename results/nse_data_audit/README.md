# NSE corporate-action audit — did unadjusted splits/bonuses distort the India alpha?

Run date 2026-11-09 · scripts: `nse_ca_audit.py`, `build_nse_adjusted_panels.py`, `rerun_india_corrected.py`,
`india_ca_robustness.py`, `nse_prevclose_probe.py` · panels: `data_processed/nse_survivorship_free{,_top150}.parquet`

## Answer in four lines

1. **Yes, the panels were badly contaminated**: 528 one-day close-to-close drops of 40–99 % in the top-500 panel
   (172 in top-150), 553 of the 1,024 ±40 % moves are ones the backtest engine actually books as a daily return.
   The great majority are unadjusted splits/bonuses (CHOLAFIN, INFY, TCS, ASIANPAINT, EICHERMOT, SIEMENS …).
2. **The artefacts *understated* the India alpha, they did not inflate it.** They hit the long legs hardest (consistent
   with large, high-priced, frequently splitting quality / low-vol names sitting there) and dragged the equal-weight
   benchmark down ≈ 4–5 %/yr.
3. **The headline survives and gets stronger**: α 10.5 % (t 4.70) / 13.2 % (t 3.13) → **15.2 % (t 6.39) / 19.7 % (t 5.37)**
   for top-500 / top-150 on the same method. Against the real cap-weighted Nifty 500 (which our fixes cannot touch)
   the alpha is roughly unchanged in level (re-selected sleeves: top-500 16.5 % → 14.7 %, top-150 21.4 % → 19.9 %;
   holding the published sleeves fixed: 16.5 % → 18.0 %, 21.4 % → 25.8 %) and more significant (t 4.35 → 5.47, 4.08 → 4.65).
4. **Two caveats were already there and are not removed by this fix**: (a) the headline composite picks its sleeves by
   in-sample t > 1.96 — an *unselected* all-14-sleeve composite earns only **6.4–6.7 %/yr (t 4.2–4.6)** corrected
   (2.6 %, t 1.95 before); (b) a separate data hole (2011-06-22 → 2011-12-30, §3.4) is neutralised, not repaired.

---

## 1. What the scan found (`corporate_action_suspects.csv`, 1,525 rows)

Consecutive-row moves beyond ±40 % per symbol (any gap), plus an "extended" tier of −20 … −40 % drops on consecutive
days that only count if Yahoo contradicts them. Each is classified with: closeness to a clean ratio
(1:2, 1:3, 1:4, 1:5, 1:10, 2:3, 3:4 …), persistence (a spike that reverts is a bad tick), traded-value continuity
(a split multiplies share volume by 1/ratio, so price×volume is continuous; a crash blows it up), and
the split-adjusted Yahoo close in `nse_prices_clean.parquet` (324 of the names).

| tier / gap | CA confirmed by Yahoo | CA likely (clean ratio, persistent) | bad tick / reversal | genuine likely | uncertain (left untouched) |
|---|---:|---:|---:|---:|---:|
| >40 %, consecutive days (≤5 d gap), n = 500 | 191 | 271 | 15 | 4 | 19 |
| >40 %, across a >5-day hole (stock was outside the universe), n = 654 | 19 | 32 | 5 | 139 | 459 |
| −20…−40 %, consecutive days, n = 371 | 58 | – | – | 313 | – |

571 corporate actions are repaired (261 + 298 in top-500, 134 + 64 in top-150): 197 at ratio 0.5 (1:1 bonus or 10→5 split),
128 at 0.2 (1:5), 58 at 0.1 (1:10), plus 2:3, 3:2, 1:2 bonus, 3:1 … — roughly 10–55 a year over 2005-2025, more in the early years.
Known cases: CHOLAFIN 2019-06-14 (−80.2 %, ratio 0.2), INFY 2014-12-02 (−51.1 %), 2015-06-15 (−49.9 %), 2018-09-04 (−48.6 %) —
all four classified `CA_CONFIRMED_YAHOO` (Yahoo shows −1.0 %, −2.2 %, +1.8 %, +2.8 % on those days).
What stays "genuine": YES BANK 2020-03-06 (−56 %), DHFL 2018-09-21 (−43 %), Satyam 2009-01-07 (−78 %, manual veto),
the Oct-2008 crash days, COVID-rebound jumps.

## 2. Why the split adjustment missed (root cause)

`nse_bhavcopy_pipeline.py` (docstring, fact 2) and `build_nse_universe.back_adjust` assume that **on an ex-date NSE
reports PREVCLOSE as the adjusted prior close**, so `PREVCLOSE_t / CLOSE_{t-1}` equals the split factor. **That is false.**

* `nse_prevclose_probe.py` opens the raw daily bhavcopy zips for a stratified sample of 15 Yahoo-confirmed corporate
  actions, 2005 → 2025, old format and UDiFF: **PREVCLOSE on the ex-date equals the *raw* previous CLOSE in 15 / 15**
  (ratio 1.000; CHOLAFIN 2019-06-14: PREVCLOSE 1471.2 = previous CLOSE 1471.2, an adjusted value would be 294.2).
  So the ratio is always 1.0, no event is ever detected, `back_adjust` is a no-op, and every split/bonus passes through.
  The same logic, run on the saved Jan-2015 PoC sample (`data_raw/nse_bhavcopy_sample.parquet`), finds **0** events
  while the same sample contains 6 one-day drops of 45–90 % that are clearly splits/bonuses (BANKBARODA, CORPBANK, HATHWAY, TATACOFFEE …).
* `build_nse_universe.py --selftest` could not catch it: its synthetic series *builds in* an adjusted `prevclose`, i.e. it
  assumes the thing that needed verifying.
* Even a working PREVCLOSE detector would have been fragile: face-value splits get a **new ISIN a day or two after the
  ex-date** (CHOLAFIN INE121A01016 → INE121A01024 on 2019-06-17), the back-adjust is grouped by ISIN, and the
  `MAX_GAP_DAYS = 5` guard silently skips any event that sits next to a missing day.
* `run_nse_longshort.py` / the engine clip returns at [−95 %, +200 %] — they only protect against the −99 % outliers,
  not against the −50 % … −80 % bulk, and the equal-weight benchmark is an unclipped mean of the same returns.

## 3. The fix and how it was validated

`build_nse_adjusted_panels.py` back-adjusts every `CA_*` event (factor = bhavcopy ratio ÷ Yahoo's same-day move, snapped to
the clean ratio when within 3 %; clean ratio itself without Yahoo cover) on the *output* panels — no re-download needed.
Open/high/low scale like close, volume is restated in post-event shares. Variants written to `data_processed/` (git-ignored):

| file suffix | meaning |
|---|---|
| *(none)* / `raw` | panel as published (reproduces the old headline to the last digit — the harness is clean) |
| `_nohole` | raw + the 195-day return on 2012-01-02 set to zero (§3.4) |
| `_adj` | **corporate actions back-adjusted** |
| `_adj_nohole` | adj + hole neutralised (my best estimate) |
| `_zero40`, `_zero40_nohole` | **bracket**: *every* consecutive-day move beyond ±40 % forced to 0 %, genuine crashes included |

Independent validation against Yahoo's split-adjusted closes (324 shared names, 1.05 M name-days): days where our daily
return differs from Yahoo's by more than 25 pp fall **294 → 55 (adj) → 18 (adj_nohole)**; correlation of daily returns
0.926 → 0.985 → 0.992. The 18 survivors are almost all Yahoo's *own* unadjusted events (RAYMOND 2025 demerger, LT 2006-09-27,
MASTEK 2015, ADANIENT 2015, J&KBANK 2017 …), where our adjusted series is the correct one.
INFY's three bonus days go from −51.1 / −49.9 / −48.6 % to −2.2 / +0.3 / +2.8 %.

### 3.4 A second, related defect found on the way (neutralised, not repaired)
The universe builder lost **130 trading days (2011-06-22 → 2011-12-30)** and the 2012 universe is half size (236 names
instead of ≈ 480; 71 instead of 150). Cause: NSE's files only gain an `ISIN` column on 2011-06-22 (verified in the raw zips);
before that the builder uses `isin = symbol`, afterwards real ISINs, so the ISIN-keyed point-in-time ranking
(prior-year turnover per ISIN) cannot rank 2011-H2 rows. On 2012-01-02 **every stock's "daily" return is therefore a
195-day return** (market ≈ −20 %), which the engine books as one day. The `_nohole` variants zero that day.
A proper fix needs the raw panel (`data_raw/nse_bhavcopy_panel.parquet`, iCloud cloud-only) and an identity map that bridges the format change.

## 4. Before / after (India market-neutral composite, same method, same code)

Method unchanged: 14 L/S sleeves → full-sample CAPM vs the panel's equal-weight benchmark → equal-weight the
beta-neutral streams of sleeves with in-sample alpha t > 1.96. "hedge β" = mean beta of the selected sleeves (what the
neutralisation removes; the composite itself is β = 0 by construction).

**Top-500 universe** (`nse_survivorship_free`), 2005-02 → 2025-06

| variant | α %/yr | t | neutral Sharpe | hedge β | sleeves | low-vol sleeve β / α / t | EW bench CAGR |
|---|---:|---:|---:|---:|---:|---|---:|
| **published (= raw re-run)** | **10.49** | **4.70** | **0.850** | −0.377 | 6 | −0.96 / 15.1 % / 4.47 | 7.9 % |
| nohole | 11.01 | 4.96 | 0.908 | −0.360 | 6 | −0.95 / 15.9 % / 4.69 | 9.4 % |
| **adj** | **15.19** | **6.39** | **1.246** | −0.263 | 7 | −0.80 / 19.7 % / 5.61 | 11.9 % |
| **adj_nohole** | **15.45** | **6.65** | **1.302** | −0.239 | 7 | −0.79 / 20.1 % / 5.68 | 13.2 % |
| bracket zero40 | 14.24 | 6.17 | 1.190 | −0.257 | 7 | −0.84 / 18.8 % / 5.50 | 11.4 % |
| bracket zero40_nohole | 14.81 | 6.47 | 1.258 | −0.237 | 7 | −0.83 / 19.6 % / 5.67 | 12.9 % |

**Top-150 universe** (`nse_survivorship_free_top150`)

| variant | α %/yr | t | neutral Sharpe | hedge β | sleeves | low-vol sleeve β / α / t | EW bench CAGR |
|---|---:|---:|---:|---:|---:|---|---:|
| **published (= raw re-run)** | **13.20** | **3.13** | **0.592** | −1.115 | 3 | −1.23 / 13.0 % / 2.83 | 6.6 % |
| nohole | 12.94 | 3.50 | 0.661 | −0.840 | 4 | −1.22 / 14.3 % / 3.08 | 8.3 % |
| **adj** | **19.74** | **5.37** | **1.082** | −0.550 | 5 | −1.05 / 24.1 % / 4.77 | 11.0 % |
| **adj_nohole** | **18.13** | **5.48** | **1.095** | −0.444 | 6 | −1.03 / 24.5 % / 4.76 | 12.4 % |
| bracket zero40 | 17.64 | 5.05 | 1.004 | −0.573 | 5 | −1.09 / 21.8 % / 4.49 | 10.2 % |
| bracket zero40_nohole | 18.56 | 5.21 | 1.044 | −0.557 | 5 | −1.09 / 23.0 % / 4.69 | 11.9 % |

(`before_after.csv` has every column, incl. bootstrap p, vol, max drawdown, blend Sharpe, selected-sleeve lists.)
The bracket — which throws away real crashes too — lands within 1–2 pp of the corrected run, so the result does not
hinge on the classifier's judgement calls. Against the US (α 5.8 %, t 2.79, unchanged) the India/US ratio moves
from 1.7–2.3× to ≈ 2.6–3.4× (the US panel was not audited here).

## 5. Why the alpha went *up* — and why that is not a fix-induced illusion

`robustness.csv`, `decomposition_2x2.csv` (`india_ca_robustness.py`) hold the sleeve selection fixed so that a change in
*which* sleeves pass t > 1.96 is not mistaken for a data effect.

* **Real sleeve P&L.** With the published 6-sleeve set and the *old* benchmark, α rises 10.5 → 14.6 %: the long legs of
  the low-vol / quality sleeves had been eating phantom −50 … −80 % days (long-leg CAGR of the low-vol / quality sleeves
  13–16 % → 29–31 %; short legs barely move, −48…−56 % → −52…−61 %, in the adj panel). Per-sleeve L/S Sharpe: low-vol −0.02 → 0.17, quality+low-vol 0.12 → 0.48,
  52-week-high 0.59 → 1.20.
* **Benchmark repair (mechanical).** The equal-weight benchmark was dragged by the same phantom drops: 7.9 % → 13.2 % CAGR.
  Because the selected sleeves have negative beta, α = mean(y) − β·mean(x) rises mechanically with the benchmark's drift:
  +1.8 pp (top-500) / +5.7 pp (top-150) with the sleeve P&L held at its old value; sleeve and benchmark effects
  together +5.6 / +11.5 pp (interaction ≈ −0.3 / −0.5).
* **The independent check.** The real cap-weighted Nifty 500 (`^CRSLDX`) is untouched by our fixes:

| composite vs cap-weight Nifty 500 | published | adj | adj_nohole |
|---|---:|---:|---:|
| top-500, re-selected sleeves (4 → 7) | 16.46 %, t 4.35 | 14.72 %, t 5.29 | 14.70 %, t 5.47 |
| top-500, fixed published 4 sleeves | 16.46 %, t 4.35 | 18.05 %, t 4.73 | 18.02 %, t 4.76 |
| top-150, re-selected sleeves (3 → 5) | 21.40 %, t 4.08 | 20.43 %, t 4.74 | 19.91 %, t 4.65 |
| top-150, fixed published 3 sleeves | 21.40 %, t 4.08 | 26.48 %, t 4.59 | 25.83 %, t 4.52 |

  So against an independent benchmark the level is flat-to-higher and the t-stat is higher in every row. The earlier
  EW-benchmark numbers were low because the benchmark itself was corrupted, not because the strategy was weak.
* **Unselected check (all 14 sleeves, equal-weight, no t-filter)**, EW benchmark: top-500 2.59 % (t 1.95) → 6.37 % (t 4.23) /
  6.66 % (t 4.55 with hole fixed); top-150 2.06 % (t 1.12) → 7.67 % (t 4.01) / 6.86 % (t 3.81). Vs Nifty 500: 2.7 % (1.98) → 5.9–6.2 % (3.97–4.39).
  This is the number to quote if someone asks for the alpha without in-sample sleeve selection.
* Pre-existing oddity worth knowing: `volatility_targeting` and `low_volatility_shield` produce *identical* L/S streams in
  the India runs, so the "6-sleeve" composite is five distinct sleeves with low-vol double-weighted (and the top-150 "3-sleeve"
  one is two distinct sleeves). Not changed here.

## 6. What is still wrong / not covered

1. **478 uncertain events left as they are.** 459 are level breaks across >5-day holes (437 in names without Yahoo cover) —
   e.g. a stock leaving and re-entering the point-in-time universe — which the engine does not book as returns (NaN)
   but which can poison 252-day price-level scores (momentum, 52-week high, MA trend); their effect is not quantified.
   19 are consecutive-day crash/jump days such as DHFL 2018-09-21; the zero40 bracket zeroes those too and moves α by
   1–2 pp at most (top-500 15.2 → 14.2 %, top-150 19.7 → 17.6 %).
2. **Sub-40 % corporate actions in names Yahoo does not cover** (1:4 bonus = −20 %, 3:4 = −25 %, 2:3 = −33 %) cannot be
   separated from real moves without a corporate-action feed; only the 58 Yahoo-contradicted ones are fixed.
3. **ISIN-change exits.** A face-value split issues a new ISIN that has no prior-year turnover rank, so the name drops out of
   the point-in-time universe until 1 January (CHOLAFIN is absent 2019-06-17 → 2019-12-31). That removes freshly split
   names (often recent winners) for the rest of the year — a small residual universe bias, fixable only by rebuilding from the raw panel.
4. **The 2011-H2 hole / half-size 2012 universe** (§3.4) is neutralised, not repaired.
5. **Other consumers of these panels were not re-run**: `death_test.py`, `entropy_research.py`, and anything else reading
   `nse_survivorship_free*.parquet` or the Yahoo-based `nse_prices_clean.parquet` (which itself has 29 days below −40 %, several of them
   its own unadjusted events, e.g. CGCL / MOTILALOFS 2024-01-01, RAYMOND 2025-05-14). Event-study code should use the `_adj_nohole` panels or `corporate_action_suspects.csv`.
6. Dividends are still excluded (price return), as before; US-side data was not audited.

## 7. Files

* `corporate_action_suspects.csv` – the audit (features, verdict, adjustment factor, Yahoo cross-check)
* `before_after.csv`, `robustness.csv`, `decomposition_2x2.csv`, `prevclose_probe.csv`
* `../nse_longshort_ca/<panel>_<variant>/` – engine outputs; `../composites_ca/` – market-neutral + cap-weight results
* Reproduce: `nse_ca_audit.py` → `build_nse_adjusted_panels.py` → `rerun_india_corrected.py` → `india_ca_robustness.py`
  (≈ 6 minutes in total; `nse_prevclose_probe.py` reads ~30 small iCloud stubs). Old result folders were not touched.
