# Group map: rules and columns

*Written 11 Nov 2026, before any lookup and before any return was computed for this pilot.
Plan: `docs/group_dependency/PILOT_PLAN.md` (Phase 2).*

## Universe

`universe.csv` lists every symbol that was in the **top 500 by 63-day average traded value
(close × volume) at any month-end, Jan 2005 to Jun 2025**, in the corrected survivorship-free
panel `data_processed/nse_survivorship_free_adj.parquet`. Built by
`scripts/group_dependency_pilot.py universe` from traded value only: no returns. 1,609 symbols.

The panel keys each security by ISIN from June 2011 on and labels it with its most recent
symbol, so later renames are already merged. Before 2007 the old NSE files carry no ISIN, so
a pre-2007 rename can appear as two symbols for one company. Such pairs are flagged in
`same_company_as` and are never treated as two different firms.

Company names come from NSE's public lists (`EQUITY_L.csv`, `namechange.csv`,
`symbolchange.csv`, `delisted.csv`, downloaded 11 Nov 2026 from nsearchives.nseindia.com);
1,430 of 1,609 symbols matched. The rest were identified by hand.

## Columns of `group_map.csv`

One row per symbol and control period. A symbol whose controller changed has several rows.

| Column | Meaning |
|---|---|
| `symbol` | Panel symbol |
| `company_name` | Company name (latest) |
| `group` | Controlling promoter group in that period, canonical name (see below) |
| `group_type` | `Family`, `Corporate`, `MNC`, `State`, `PE`, `Professional` or `Unknown` |
| `start`, `end` | Control period, ISO dates, clipped to 2005-01-01 … 2025-06-30. Month precision is fine (first of month) |
| `industry` | One of the 41 industries below |
| `confidence` | `high` / `medium` / `low` for the group label |
| `source` | Where the label comes from (URL, or a short name of the filing or list) |
| `notes` | Renames, mergers, demergers, why a date was chosen |
| `same_company_as` | Another panel symbol that is the same company (pre-2007 renames, duplicate listings) |

`groups.csv` gives one row per multi-member group: group, group_type, source URL(s), notes.

## Who is a "group"

1. **The label is the controller.** `group` is the promoter group that controls the firm,
   as shown in the "promoter and promoter group" part of the SEBI shareholding pattern, or
   the group's own website, annual report or a Wikipedia list of group companies.
2. **Family branches are separate groups once they split.** Mukesh Ambani's Reliance and
   Anil Ambani's Reliance ADAG are separate from the 2005–06 demerger; the Jindal
   branches (JSW, JSPL, Jindal Stainless, Jindal Saw), the Birla branches (Aditya Birla,
   CK Birla, MP Birla, KK Birla/Adventz, BK Birla), the Bajaj branches, the TVS branches,
   the Goenka branches (RPG vs RP-Sanjiv Goenka) and the Singhania/JK branches are each
   labelled by the branch in control at the time.
3. **Types.**
   - `Family`: an Indian private promoter family or individual.
   - `Corporate`: a listed Indian company without a family promoter that controls other
     listed companies (HDFC, ICICI, L&T). The parent and its listed subsidiaries share the
     label.
   - `MNC`: a foreign parent holds control (Unilever, Holcim, Suzuki, P&G …).
   - `State`: the central or a state government, or a listed public-sector parent.
     Label as `State: Government of India` for firms held directly by the centre,
     `State: <PSU parent>` for listed PSU subsidiaries (e.g. `State: ONGC` for MRPL and,
     from 2018, HPCL), `State: Government of Gujarat` etc. for state PSUs.
   - `PE`: a private-equity sponsor in control (Blackstone, Advent, Carlyle …).
   - `Professional`: no controlling promoter and no listed subsidiaries in the universe
     (e.g. ITC before 2025, Axis Bank, Infosys).
   - `Unknown`: the controller could not be established.
4. **Standalone is computed, not labelled.** Every firm gets its controller's name. A firm
   whose controller has no other universe firm at the same time is standalone. That is
   decided by code from this map, so the labeller never has to judge "is this a group?".
5. **Membership changes are dated.** Splits (Reliance 2005–06), sales (ACC and Ambuja to
   Adani, Sep 2022), takeovers (Ranbaxy to Daiichi 2008), mergers and delistings each end
   one row and, where the firm stays listed, start another.
6. **ETFs and fund units are not companies.** The traded-value universe contains some
   (NIFTYBEES, GOLDBEES, LIQUIDBEES …). They get group `ETF (not a company)`, type
   `Unknown`, and the analysis drops them from the stock universe entirely.
7. **Fixed before returns.** The map is committed before the pre-registration and before
   any return is computed. Any later change is logged as a dated deviation with its reason.

## Industries (41, close to NSE's "Industry" level; one per symbol)

Banks · Finance - NBFC & Housing Finance · Insurance · Capital Markets · IT Services &
Software · Telecom Services · Media & Entertainment · Pharmaceuticals & Biotechnology ·
Healthcare Services · Automobiles · Auto Components · Cement · Construction & Engineering ·
Realty · Power · Oil & Gas - Exploration & Production · Petroleum Refining & Marketing ·
Gas Transmission & Distribution · Ferrous Metals · Non-Ferrous Metals · Mining & Minerals ·
Chemicals · Fertilizers & Agrochemicals · Textiles & Apparel · Paper & Packaging · Consumer
Durables · Food & Beverages · Personal & Household Products · Tobacco & Diversified FMCG ·
Sugar & Agri Commodities · Retail · Hotels, Leisure & Travel · Airlines · Shipping &
Logistics · Transport Infrastructure · Electrical Equipment · Industrial Machinery &
Products · Aerospace, Defence & Shipbuilding · Building Materials · Diversified & Holding
Companies · Commercial & Other Services

Notes: tyres and batteries are Auto Components; cables and wires are Electrical Equipment;
paints and jewellery are Consumer Durables; DTH and cable TV are Media & Entertainment;
telecom towers are Telecom Services; BPO is IT Services & Software; rail freight, courier
and logistics are Shipping & Logistics; ports, airports and toll-road operators are
Transport Infrastructure; road and building contractors are Construction & Engineering.
An industry is assigned by the firm's main business over its time in the panel.

## Version 2 (12 Nov 2026): verified against filings

`group_map_v2.csv` keeps every v1 column and adds `source_url`, `filing_date`, `verified`
(yes / changed / unverifiable / not checked), `verified_scope` and `notes_v2`. Built by
`scripts/group_dependency_build_map_v2.py` from:

- **NSE shareholding-pattern XBRL filings, 2020/21 onward.** These cover 750 priority symbols:
  every firm in the pilot's 74 S-class events, every member of a multi-company group, and
  every low-confidence row. Fetched by `group_dependency_fetch_shp.py`, with promoter names
  in `shp_promoters.csv` and filing lists in `shp_filings.csv`. Name-consistency flags are
  in `shp_check.csv`, from `group_dependency_verify.py`.
- **A source check of the 135 event firms at their event dates** (`verify/p1_history.csv`).
- **Reviewed decisions with sources** (`verify/decisions.csv`): relabel, split a control
  period, confirm, or note.
- **The change log v1 → v2:** `group_map_v2_changes.csv`.

Confidence in v2 is "high" only where a document supports the label for the dates that
matter. See PREREGISTRATION §10 D1.
