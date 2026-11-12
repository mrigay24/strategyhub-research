# Group concentration headline (PROVISIONAL)

Effective N = exp(H), H = -sum w ln w, computed per half-year on (a) stocks and (b) owner groups (weights summed by group).

## Data
- Weights: AMFI 6-month average market capitalisation lists (NSE column preferred, else BSE, else MSEI), 18 half-years, periods ending 2017-12-31 to 2026-06-30. Source page: https://www.amfiindia.com/otherdata/categorisation-of-stocks (file URLs listed in `scripts/amfi_marketcap_pipeline.py`). Parsed to `data_processed/amfi_avg_mcap.parquet` (gitignored). 4,792 to 5,427 listed companies per period.
- Group map: `results/group_dependency/group_map.csv` (v1), read only. Re-run with `--map PATH` for a verified version.
- Scripts: `scripts/amfi_marketcap_pipeline.py`, `scripts/group_concentration_headline.py`.

## Method
Join on NSE symbol (`nse_symbol` = `symbol`), with map start <= period end <= end. The map's end date is 2025-06-30 for almost all live companies; an end equal to that map-wide latest date is treated as open-ended, otherwise the 2025-12 and 2026-06 periods could not match. Universes: top 100 and top 500 companies by average market cap in each period.

Group definitions (fixed before looking at results):
- G1 (primary): Family and Corporate groups are groups; all else (MNC, State, Professional, PE, Unknown, unmatched) is standalone.
- G2: G1 plus all State firms as one owner (Government of India).
- G3: G1 plus MNC subsidiaries grouped by parent.

## Results (top 500; full table in `headline_by_period.csv`)
| period | effN stocks | effN groups G1 | G2 | G3 | stocks/groups (G1) | matched mcap share | top-500 share of total mcap |
|---|---|---|---|---|---|---|---|
| 2017-12-31 (first) | 191.9 | 134.1 | 70.7 | 132.8 | 1.43 | 96.0% | 93.2% |
| 2026-06-30 (latest) | 230.7 | 155.6 | 82.3 | 155.4 | 1.48 | 93.2% | 90.3% |

Top 100: 2017-12-31 effN stocks 70.8, G1 52.2, G2 29.6, G3 51.9, matched 97.6%; 2026-06-30 effN stocks 73.4, G1 50.6, G2 30.5, G3 50.6, matched 96.3%.

Other files: `top_groups_latest.csv` (15 largest G1 groups, latest period), `effn_stocks_vs_groups_top500.png`.

## Caveats
- The map is v1, built from memory and unverified. These are provisional numbers, to be recomputed on the verified map.
- The map's start/end dates are crude (e.g. one blanket 2025-06-30 end, treated as open-ended here).
- The universe is NSE symbols only: AMFI companies without an NSE symbol cannot match the map and count as standalone (they appear in the unmatched share).
- Group names in the map are not harmonised (the same group could appear under different labels), which would overstate effN of groups.
- Matched share is the share of the universe's market cap whose symbol is in the map in that period, whatever its group type.

## Fund level (latest monthly disclosure, October 2026)

Script: `scripts/mf_portfolio_groups.py` (parsers + computation; reuses the G1/G2/G3 definitions and group-map loading logic of `group_concentration_headline.py`). Output: `fund_level_latest.csv` (map v1) and `fund_level_latest_v2map.csv` (map v2).

**Month:** portfolio as on 31 October 2026, one month only, for each fund.

**Method:** equity holdings = ISINs of the form INE....01... in each AMC's monthly portfolio statement; weights are the reported % to net assets renormalised to the equity ISIN sleeve (cash, debt, derivatives and foreign ISINs excluded). effN = exp(H), H = -sum w ln w. ISIN -> NSE symbol via `data_processed/amfi_avg_mcap.parquet`; symbol -> group via the group map as of 2026-10-31. `matched_weight` = share of equity weight whose symbol has a group-map row; `isin_mapped_weight` (in the CSV) = share whose ISIN maps to an NSE symbol. Ratio = effN_stocks / effN_G1.

**Sources (official AMC monthly portfolio files, downloaded to `data_raw/mf_portfolios/<amc>/`, not tracked in git):**

- Nippon India: https://mf.nipponindiaim.com/InvestorServices/FactsheetsDocuments/NIMF-MONTHLY-PORTFOLIO-31-Oct-26.xls
- PPFAS: https://amc.ppfas.com/downloads/portfolio-disclosure/2026/PPFCF_PPFAS_Monthly_Portfolio_Report_October_31_2026.xlsx
- Axis: https://www.axismf.com/1/5/464/560/3622/4645/Monthly_Portfolio_31_10_2026_fc300a7239.xlsx
- SBI: https://www.sbimf.com/docs/default-source/scheme-portfolios/all-schemes-monthly-portfolio---as-on-31st-october-2026.xlsx
- DSP: https://www.dspim.com/media/pages/mandatory-disclosures/portfolio-disclosures/7064cd3e18-1794228730/dsp-monthend-portfolio-as-on-31-october-2026.zip
- Tata: https://www.tatamutualfund.com/system/files/2026-11/Monthly%20Portfolio%20as%20on%2031st%20October%202026....xlsx
- Canara Robeco: https://www.canararobeco.com/wp-content/uploads/2026/11/SC-%E2%80%93-Canara-Robeco-Small-Cap-Fund-%E2%80%93-October-2026.xlsx

| Fund | Category | N holdings | effN stocks | effN G1 | effN G2 | effN G3 | Ratio | Matched wt | Top 3 groups (G1) |
|---|---|---|---|---|---|---|---|---|---|
| Nippon India Small Cap Fund | Small cap | 259 | 189.3 | 171.7 | 136.8 | 171.7 | 1.10 | 80% | HDFC 2.7%; Tata 2.2%; INE419M01035 (standalone) 1.8% |
| Nippon India Large Cap Fund | Large cap | 68 | 44.6 | 36.2 | 30.7 | 36.2 | 1.23 | 97% | HDFC 10.9%; Tata 8.2%; ICICI 6.4% |
| Nippon India Multi Cap Fund | Multi cap | 123 | 85.7 | 75.8 | 66.7 | 75.8 | 1.13 | 88% | HDFC 7.2%; AXIS Bank Ltd. (standalone) 5.3%; Tata 5.1% |
| Nippon India Growth Mid Cap Fund | Mid cap | 100 | 79.9 | 67.8 | 49.4 | 67.8 | 1.18 | 94% | Murugappa 4.7%; Tata 4.2%; ICICI 3.4% |
| Nippon India Value Fund | Value | 88 | 57.8 | 51.5 | 39.6 | 51.5 | 1.12 | 90% | HDFC 7.6%; Tata 5.8%; Kotak (Uday Kotak) 4.8% |
| Parag Parikh Flexi Cap Fund | Flexi cap | 51 | 22.3 | 20.9 | 17.0 | 20.9 | 1.07 | 100% | HDFC 9.8%; POWER GRID CORPORATION OF INDIA LIMITED (standalone) 7.4%; ITC Ltd (standalone) 7.2% |
| Axis Small Cap Fund | Small cap | 129 | 105.6 | 102.2 | 95.7 | 102.2 | 1.03 | 84% | Torrent 2.6%; KIMS (Bhaskara Rao Bollineni) 2.5%; CCL Products (Challa family) 2.4% |
| Axis Large Cap Fund | Large cap | 48 | 32.1 | 26.9 | 26.4 | 26.9 | 1.19 | 99% | ICICI 10.1%; HDFC 8.5%; Tata 7.3% |
| Axis Flexi Cap Fund | Flexi cap | 69 | 46.3 | 42.1 | 37.9 | 42.1 | 1.10 | 93% | ICICI 8.7%; Eternal Limited (standalone) 5.4%; Bajaj (Rahul Bajaj family) 4.6% |
| Axis Midcap Fund | Mid cap | 85 | 66.5 | 61.2 | 60.3 | 61.2 | 1.09 | 86% | Federal Bank Ltd. (standalone) 4.6%; Tata 3.7%; Sona BLW Precision Forgings Limited (standalone) 3.2% |
| SBI Small Cap Fund | Small cap | 63 | 51.2 | 48.5 | 48.5 | 48.5 | 1.06 | 71% | Ather Energy Limited (standalone) 5.3%; Murugappa 5.0%; Mafatlal (Padmanabh Mafatlal) 4.3% |
| SBI Large Cap Fund (formerly Bluechip) | Large cap | 54 | 35.0 | 29.3 | 28.6 | 29.3 | 1.19 | 94% | HDFC 11.2%; ICICI 10.6%; Kotak (Uday Kotak) 5.2% |
| SBI Flexicap Fund | Flexi cap | 61 | 46.6 | 44.6 | 40.3 | 44.6 | 1.04 | 85% | ICICI 7.9%; HDFC 5.9%; Adani 4.2% |
| SBI Midcap Fund | Mid cap | 56 | 50.1 | 46.7 | 46.7 | 46.7 | 1.07 | 90% | ICICI 4.9%; Torrent 3.5%; JSW (Sajjan Jindal) 3.5% |
| DSP Small Cap Fund | Small cap | 85 | 66.9 | 66.9 | 66.2 | 66.9 | 1.00 | 68% | Lumax Auto Technologies Ltd. (standalone) 6.1%; Thangamayil Jewellery Limited (standalone) 3.6%; Kirloskar 3.5% |
| DSP Flexi Cap Fund | Flexi cap | 67 | 42.0 | 34.0 | 29.1 | 34.0 | 1.24 | 96% | ICICI 10.8%; HDFC 10.2%; Mahindra 6.2% |
| DSP Large Cap Fund | Large cap | 42 | 28.0 | 25.2 | 17.0 | 25.2 | 1.11 | 99% | HDFC 12.6%; ICICI 10.7%; Bharti (Sunil Mittal) 7.3% |
| DSP Mid Cap Fund | Mid cap | 63 | 54.1 | 47.8 | 45.9 | 47.8 | 1.13 | 94% | Murugappa 7.5%; COFORGE LIMITED (standalone) 5.2%; Bharti (Sunil Mittal) 3.6% |
| Tata Small Cap Fund | Small cap | 62 | 48.2 | 47.2 | 47.2 | 47.2 | 1.02 | 75% | Usha Martin (Jhawar family) 4.8%; Sudarshan (Rathi family) 4.6%; INE811A01038 (standalone) 4.2% |
| Tata Large Cap Fund | Large cap | 45 | 36.2 | 30.2 | 28.4 | 30.2 | 1.20 | 93% | ICICI 9.7%; Adani 8.5%; HDFC 7.3% |
| Tata Flexi Cap Fund | Flexi cap | 66 | 51.2 | 42.4 | 34.1 | 42.4 | 1.21 | 91% | HDFC 9.7%; ICICI 7.1%; Bharti (Sunil Mittal) 6.2% |
| Tata Mid Cap Fund | Mid cap | 57 | 51.4 | 47.5 | 43.3 | 47.5 | 1.08 | 92% | Bharti (Sunil Mittal) 5.7%; Hinduja 4.0%; Mankind (Juneja family) 3.6% |
| Canara Robeco Small Cap Fund | Small cap | 98 | 83.5 | 80.1 | 79.0 | 80.1 | 1.04 | 82% | Karur Vysya Bank Ltd. (standalone) 3.1%; TBO TEK LIMITED (standalone) 2.6%; RP-Sanjiv Goenka 2.5% |
| Canara Robeco Multi Cap Fund | Multi cap | 111 | 91.1 | 81.4 | 76.6 | 81.4 | 1.12 | 88% | HDFC 5.2%; ICICI 4.4%; Bharti (Sunil Mittal) 3.5% |
| Canara Robeco Value Fund | Value | 57 | 44.9 | 43.1 | 30.5 | 43.1 | 1.04 | 90% | ICICI 8.0%; HDFC 6.9%; Bharti (Sunil Mittal) 6.0% |

Funds covered: 25 across 7 AMCs. Median ratio (effN stocks / effN G1): **1.103** (range 1.000 to 1.237). Median effN stocks 51.2; median effN G1 47.2; median effN G2 43.3. Median matched weight 90.2%.

Map v2 (`group_map_v2.csv`, committed) gives identical fund-level numbers to four decimals: its 14 changed group assignments (against v1) are in names none of these funds hold.

**Not covered:** HDFC (files host returns 403 to scripted downloads), Kotak (site serves a bot-check captcha), ICICI Prudential (site not reachable from the browser tool used), Franklin Templeton (page rendered blank), Quant (monthly portfolio files not located within the time-box). Funds skipped as a result: HDFC Small Cap, HDFC Flexi Cap, Kotak Small Cap, Franklin India Smaller Companies, Quant Small Cap, ICICI Bluechip. No files from `NIAIF/` were used.

**Caveats:** one month only. Map v1 is unverified (v2 verifies part of it), so the numbers are provisional. Group names are not harmonised across map rows, which may overstate the effective number of groups (ratio biased toward 1). G3 equals G1 for every fund: no fund holds two companies of the same MNC parent in the map. Unmatched weight (no group-map row) is treated as standalone companies. Standalone labels shown as ISIN codes are ISINs absent from the AMFI file (recent listings).
