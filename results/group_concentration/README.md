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
