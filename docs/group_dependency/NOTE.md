# Paper 2 pilot note: business groups and hidden concentration (India)

*Started 11 Nov 2026. Plan: `PILOT_PLAN.md`. Rules: `PREREGISTRATION.md`. This note is
filled in phase by phase; sections marked "(pending)" are not written yet.*

## 1. The idea (pending)

## 2. Is this new? Literature check (Phase 1, 11 Nov 2026)

The pilot asks one narrow question: **after a group firm's own crash, do its group siblings
in *other* industries fall more than its industry rivals in *other* groups, once each pair's
calm-period correlation is controlled for?** And, if so, does an entropy measure built from
ownership (effective number of groups) show risk that correlation-based tools miss?

Searches were run on 11 Nov 2026 (web search, abstracts and bibliographic records; full texts
were not read, so details below are from abstracts and must be checked before citing).

### 2a. What already exists

**Business groups and stock comovement (average days, not crashes).**
- Khanna & Thomas (2009), "Synchronicity and firm interlocks in an emerging market", *JFE*
  92(2), 182–204. Chile: synchronicity rises with equity cross-holdings and shared owners,
  and most strongly with interlocking directors.
- Kim, Kim & Lee (2015), "Stock return commonality within business groups: Fundamentals or
  sentiment?", *Pacific-Basin Finance Journal* 35A, 198–224. Korea: comovement within a
  group *beyond what industry explains*, rising after 1997–98; part of it is non-fundamental
  ("habitat") trading.
- Faccio, Morck & Yavuz (2021), "Business groups and the incorporation of firm-specific
  shocks into stock prices", *JFE* 139(3), 852–871. Group affiliates' idiosyncratic returns
  respond *less* to their own commodity shocks than similar standalone firms' do.
- An Indian synchronicity study (*Emerging Markets Finance and Trade* 51(5), 2015;
  doi 10.1080/1540496X.2015.1061381) finds synchronicity with the market is *lower* for
  group-affiliated NSE firms. (That is comovement with the market, not with siblings.)

**Contagion inside groups (events).**
- Kwon, Jung, Sunwoo & Yim (2019), "Does stock price crash of firms in the same business
  group cause stock price crash in other member firms? Evidence from Korea", *EMFT* 55(7),
  1566–1592. **The closest paper.** A firm's crash risk (firm-year crash measures) is
  positively associated with crash risk at other members of its chaebol; crashes *spread*
  rather than arrive together; stronger with more intra-group trade.
- Joe & Oh (2018), "Spillover effects within business groups: the case of Korean chaebols",
  *Management Science* (doi 10.1287/mnsc.2016.2596), and Han & Lee (2016), *Pacific-Basin
  Finance Journal* 39, 84–100: credit-rating changes at one chaebol affiliate move its
  siblings' stock prices, mostly negatively.
- Cumming, Jain & Jindal (working paper, SSRN 5024025): in India, the market's reaction to
  one group firm's equity issue spills over, with the same sign, to its non-issuing siblings.
- Gopalan, Nanda & Seru (2007), "Affiliated firms and financial support: evidence from
  Indian business groups", *JFE* 86(3), 759–795: intragroup loans flow to weak affiliates,
  and **the first bankruptcy in a group is followed by lower financing, investment and
  profits at the other members** (abstract). This settles paper 1's "check before citing"
  item on Gopalan et al.
- Ganguly, Mishra & Platt (2025), *Applied Economics Letters*: after the Hindenburg report,
  Indian indices fell, firms with pledged shares fell more, politically connected firms rose.
  It studies indices and pledging, not siblings versus industry rivals.
- Bertrand, Mehta & Mullainathan (2002, *QJE*) and Khanna & Palepu (2000, *J. Finance*)
  give the background: Indian groups move resources between members (tunnelling) and group
  affiliation matters for value.

**Ownership-based fragility and diversification measures.**
- Antón & Polk (2014), "Connected stocks", *J. Finance* 69(3), 1099–1127: the number of
  shared active mutual-fund owners predicts a pair's future return correlation after
  controlling for industry and style. The same "ownership beyond industry" logic, for
  *institutional* owners and *average* correlation.
- Greenwood & Thesmar (2011), "Stock price fragility", *JFE* 102(3), 471–490: concentrated
  or correlated owners make prices fragile. Coval & Stafford (2007): fire sales by common
  mutual-fund holders.
- Meucci (2009), "Managing diversification", *Risk*: the effective number of bets is the
  exponential of the entropy of the portfolio's variance split across uncorrelated
  (principal-component) bets. It is built from the covariance matrix, so it only sees what
  past prices show.

### 2b. Is this exact test already done?

**No paper found runs this exact test.** The pieces exist separately:
- "Group firms comove beyond industry" is known (Korea, Chile), but on *average* days.
- "Crashes spread inside groups" is known for Korea (Kwon et al. 2019), with firm-year crash
  measures, and without a control for how correlated each pair already was.
- Indian intra-group spillovers are documented for equity issues (Cumming et al.) and for
  financing (Gopalan et al.), not for crash events against industry rivals.

What the pilot would add, if it holds:
1. **India, event level, siblings vs industry rivals.** Who falls with a crashing group firm:
   its owner's other firms in unrelated industries, or its competitors?
2. **"Beyond correlation" is tested directly.** Each pair's calm-period correlation is the
   control. If ownership only matters through what correlation already shows, a
   correlation-based risk model already captures it and the group label adds nothing.
3. **The entropy link.** Effective number of *groups* as a holdings-based concentration
   measure, compared with Meucci's covariance-based effective number of bets. No paper was
   found that builds diversification measures on promoter-group ownership.

**What it would not add:** that group firms are linked (Gopalan et al.), that groups comove
(Kim et al.), or that crash risk spreads inside groups (Kwon et al.). The note must cite
these as the starting point. **Decision: continue.** The test is new in its combination,
not in its parts.

Sources (searched 11 Nov 2026):
[Khanna & Thomas 2009](https://ideas.repec.org/a/eee/jfinec/v92y2009i2p182-204.html) ·
[Kim, Kim & Lee 2015](https://ideas.repec.org:443/a/eee/pacfin/v35y2015ipap198-224.html) ·
[Faccio, Morck & Yavuz 2021](https://econpapers.repec.org/RePEc:eee:jfinec:v:139:y:2021:i:3:p:852-871) ·
[EMFT 2015 India synchronicity](https://www.tandfonline.com/doi/full/10.1080/1540496X.2015.1061381) ·
[Kwon et al. 2019](https://ideas.repec.org/a/mes/emfitr/v55y2019i7p1566-1592.html) ·
[Joe & Oh 2018](https://pubsonline.informs.org/doi/references/10.1287/mnsc.2016.2596) ·
[Han & Lee 2016](https://ideas.repec.org/a/eee/pacfin/v39y2016icp84-100.html) ·
[Cumming, Jain & Jindal WP](https://doi.org/10.2139/ssrn.5024025) ·
[Gopalan, Nanda & Seru 2007](https://www.sciencedirect.com/science/article/abs/pii/S0304405X07001341) ·
[Antón & Polk 2014](https://econpapers.repec.org/RePEc:bla:jfinan:v:69:y:2014:i:3:p:1099-1127) ·
[Greenwood & Thesmar 2011](https://econpapers.repec.org/RePEc:eee:jfinec:v:102:y:2011:i:3:p:471-490) ·
[Meucci 2009](https://risk.net/node/1500233) ·
[Ganguly, Mishra & Platt 2025](https://research.jgu.edu.in/market-perceptions-and-reactions-the-ripple-effect-of-the-hindenburg-report-on-indian-companies/)

## 3. Data and the group map (pending)

## 4. The pre-registered test (pending)

## 5. Result (pending)

## 6. Go / no-go decision (pending)

## 7. Limitations (pending)
