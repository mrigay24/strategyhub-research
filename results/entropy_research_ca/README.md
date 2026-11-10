# India entropy Test 2 — rerun on the corrected NSE panel (2026-11-09)

Script: `scripts/entropy_india_rerun.py` (unchanged `entropy_research.entropy_series` / `test2_analyse`, different panel).
Old results in `results/entropy_research/` are untouched. Variants: `raw` (reproduces the old India numbers exactly),
`nohole` (the 195-day return on 2012-01-02 zeroed), `adj_nohole` (splits/bonuses back-adjusted + hole zeroed),
each also `_trimmed` (drops the 13 month-ends 2011-06 … 2012-12 whose 252-day window touches the 2011-H2 data hole).
Background: `results/nse_data_audit/README.md`.

## Result
* **The 2012 dip was a data artefact.** Co-movement (eigenvalue) entropy was 0.73 in mid-2011, 0.635 in March 2012 and
  back to 0.76 by March 2013. Every month-end from 2012-01 to 2012-12 has a 252-day window containing 2012-01-02, the one
  "daily" return that is really a 195-day return for every stock. That single common observation inflates the first
  eigenvalue and lowers the entropy. With it zeroed, 2012 reads 0.71–0.74 (yearly mean 0.645 → 0.729). All other years
  move by ≤ 0.005 (splits/bonuses barely matter here).
* **The conclusions do not change.** India entropy still has no predictive power beyond trailing volatility:

| entropy z-score coefficient (Newey-West t) | old (raw) | adj_nohole | adj_nohole, trimmed |
|---|---|---|---|
| next-63-day volatility | 0.006 (t 0.60) | 0.001 (t 0.09) | 0.000 (t 0.03) |
| next-126-day max drawdown | −0.018 (t −1.05) | −0.019 (t −1.03) | −0.020 (t −1.06) |
| next-63-day return | −0.033 (t −1.36) | −0.044 (t −1.57) | −0.046 (t −1.55) |

  Quintiles (Q1 low vs Q5 high entropy): forward drawdown −21.7 % vs −18.8 % (old) → −21.0 % vs −18.1 % (corrected);
  forward volatility 25.9 % vs 21.6 % → 26.9 % vs 22.1 %. Same direction, still not significant.
* **Trading-value (dv) measures were never affected** (price × volume is split-invariant): the yearly effective-N series
  matches the old run to within 0.5 stocks in every year (India 2006 → 2015 → 2024: 51 → 96 → 118, unchanged).
* **Not repaired:** the 2012 universe is still half size (≈ 196 names with ≥ 95 % coverage vs ≈ 265), because the
  universe itself needs a rebuild from the raw bhavcopy panel. Use the `_trimmed` columns for anything that
  depends on 2011-06 … 2012-12.
