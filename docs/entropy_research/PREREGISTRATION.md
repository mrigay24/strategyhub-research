# Pre-registration: out-of-sample "death test"

**Paper:** *Market Share Is Not Importance: What Happens to Rivals When a Firm Dies (US and
India)* · **Author:** Mrigay Pathak · **Written:** 11 November 2026

## 0. Why this file exists, and how it is time-stamped

The eight case studies in `RESEARCH_NOTE.md` §4b were picked *after* we knew what
happened, so the "shared dependency" labels could be story-fitting. This file fixes the
rules **before** the new cases are seen. It is committed to git in two steps, and the
commit timestamps are the proof:

1. **Part 1 (this commit): the rules.** Committed before the selection code has run, so
   before anyone has seen which firms qualify.
2. **Part 2: the case list.** Every selected case with its news description, label, day 0
   and rival list (§9 below and `oos_cases.csv`). Committed after Mrigay has checked the
   labels and **before any rival's return is computed**. The analysis code
   (`scripts/death_test_oos.py run`) is committed with it.

Nothing in §1–§8 may change after Part 1. Anything that has to change later goes into
the deviation log (§10), with the reason, and both versions are reported.

## 1. Hypotheses

- **H1 (primary).** When a firm collapses for reasons of its own, its rivals do worse over
  the next 20 trading days if they share a critical dependency with it (a funding market,
  a depositor base, or a legal liability) than if they do not.
- **H2 (secondary: is it only finance?).** H1 holds separately for financial and for
  non-financial failed firms.
- **H3 (secondary: the owner channel, India).** Listed firms controlled by the same
  business group as the failed firm do badly over the next 20 trading days.
- **H4 (secondary: market share).** The failed firm's share of its rival group does *not*
  predict the rivals' 20-day reaction once the label is known.

## 2. Data

- **India:** daily returns from the same combined panel as `scripts/death_test.py`:
  - adjusted Yahoo closes (`nse_prices_clean.parquet`) first;
  - the corporate-action-corrected bhavcopy panel (`nse_survivorship_free_adj.parquet`)
    as the fallback;
  - the universe is the top 300 stocks by 63-day average traded value, lagged one day.
- **US:** raw `extended_prices.parquet` with the $1 price floor; universe = S&P 500
  point-in-time members (`sp500_universe_lookup.csv`).
- **Both:** one-day returns beyond ±95% are removed, and so are returns above +100%. The
  market is the equal-weighted average return of the universe.
- **India data hole:** the panel has a hole from 22 June 2011 to 30 December 2011, and
  the return on 2 January 2012 spans 195 days (KNOWLEDGE_BASE §42). Any window that
  touches 22 June 2011 – 31 January 2012 is skipped.

## 3. Selection rule (a)

**Route 1: a collapse in price.** A stock qualifies on day *t* if:
- it is in the universe on day *t* or day *t*−1;
- its 20-trading-day abnormal buy-and-hold return over days *t* … *t*+19 is below −50%.
  This is the stock's compounded return minus the market's compounded return. Missing
  stock returns count as zero, and at least 10 of the 20 returns must exist;
- the window starts on or after 2 January 2006 (India) or 3 January 2000 (US), and at
  least 21 trading days of data follow it.

**Route 2: the stock stops trading (suspension, default, forced delisting).** A stock is a
route-2 candidate if:
- its last return in the panel comes more than 60 trading days before the panel ends;
- it was in the universe at some point in the 60 trading days before its last return;
- its abnormal buy-and-hold return over those 60 days is below −30%.

Route-2 candidates enter only if the news check (below) shows a default, insolvency,
suspension or forced delisting. They are dropped for a merger, a voluntary delisting
offer, an index exit or a data artefact.

**One event per episode.** A stock's first qualifying day starts an episode. The same
stock cannot start another one for 250 trading days. If a route-1 window ends within 60
trading days before a route-2 last return, they are the same episode.

**Exclusions.**
- **The eight cases already used.** A candidate is dropped if its firm was the failed
  firm, a rival or a group firm in one of those eight cases, *and* its window lies
  within 60 trading days of that case's day 0. The cases are Satyam, Jet Airways,
  IL&FS, DHFL, Yes Bank, Adani, PG&E and SVB, with the dates and lists in
  `scripts/death_test.py`.
- **Size cap.** If more than **60** candidates remain in a market after the exclusions, a
  random sample of 60 is drawn (seed 20261111) and only those are news-checked. This
  keeps the news work feasible, and the rule is fixed in advance.

**News check (every candidate).** A web search establishes what happened. The candidate is
dropped if:
1. the fall is a data artefact: a split, bonus, demerger, ISIN change or bad print,
   confirmed by the news or the price path;
2. no public news explains the fall, so no day 0 can be set;
3. the cause is industry-wide or market-wide (§5, step 1). These cases are listed and
   their outcomes reported, but they are not in the primary test.

**At least 3 rivals.** A case needs at least 3 rivals (§4) with at least 100 valid
returns in the 250 trading days before day 0. Otherwise it is dropped.

**Day 0.** The first trading day on or after the date the news that started the collapse
became public. If the news came out after the market closed, day 0 is the next trading
day. If the time is unclear, use the date of the first press report. The news must fall
within 20 trading days before the window starts or inside the window. Day 0 is **never**
"the worst day nearby".

## 4. Rival sets

- **US:** the failed firm's GICS sub-industry from `sp500_subindustry.csv`. If the firm
  is missing from that file (most delisted firms are), the sub-industry is assigned by
  hand from its business description, choosing among the sub-industry names in the
  file. This is done before any rival return is computed. Rivals are all firms in the
  file with that sub-industry that are S&P 500 members on day 0. There is no fallback to
  a wider group: fewer than 3 rivals means the case is dropped.
- **India:** there is no industry file, so rivals are chosen by hand. They are picked from
  the stocks in the universe on day 0, using only names and line of business: firms that
  sell the same product or service to the same kind of customer.
  - Example: private banks for a private bank; NBFCs and housing-finance companies for an
    NBFC; real-estate developers for a developer.
  - Firms in the failed firm's own business group are **not** rivals.
  - If more than 10 qualify, keep the 10 largest by 63-day traded value on day 0.
- **India group sets (for H3):** listed firms controlled by the same promoter or group
  that are in the universe on day 0. At least 2 are needed.

## 5. Classification rule (b)

For each case we write **one paragraph describing the shock as it was known on day 0**:
- what happened and why;
- what the firm does;
- how it was funded, where that matters.

The paragraph uses **no information about how rivals' stocks moved and no later events**.
The label is decided from that paragraph alone, in two steps.

**Step 1: was it the firm's own crash?**
- **Firm-specific triggers:**
  - fraud or accounting problems;
  - a default or liquidity failure of this firm;
  - a management or governance event;
  - a regulatory action against this firm;
  - its own product, plant, contract or lawsuit;
  - a short-seller report about it or its group.
- **Industry-wide triggers:** a policy, court ruling, tax, price war, new entrant,
  commodity-price move or demand collapse that hits the whole industry at the same time.
  These are labelled **"industry shock"** and kept out of the primary test, because the
  question is about a firm's *own* crash.

**Step 2: is there a shared dependency?** The label is **"shared dependency" (SD)** if at
least one of these holds; otherwise it is **"output-replaceable" (OR)**.

- **(F) Funding.**
  - All three must hold:
    - the failed firm is a financial intermediary (bank, NBFC, housing-finance company,
      broker, insurer);
    - the trigger is a funding or solvency failure (a missed payment, a default, a
      rating cut below investment grade, a failure to roll over debt, creditors pulling
      money, or news that it may not be able to pay creditors without a rescue);
    - the rivals are financial intermediaries that fund themselves in the same market
      (commercial paper, bonds, money-market or debt mutual funds, interbank loans, or
      uninsured deposits).
  - **Non-financial failed firm:** (F) applies only if the day-0 news names a specific
    lender or financier that the failure puts at risk *and* the rivals rely on that same
    lender.
- **(D) Depositors.** All three must hold:
  - the failed firm takes deposits;
  - the trigger involves withdrawals, a withdrawal limit, a moratorium or a regulator's
    takeover;
  - the rivals take deposits too.
- **(L) Liability or regulation.**
  - The trigger is a legal liability or a regulatory finding whose legal basis applies to
    the rivals too: the same law, rule, licence condition or liability regime, so the
    rivals could face the same claim.
  - A penalty for this firm's own misconduct does **not** count.
- **(O) Owner.** Tested through the group sets (H3), not the rival sets, because the rival
  sets exclude the failed firm's group.

**Tie-break:** if the paragraph does not clearly establish (F), (D) or (L), the label is
**OR**.

**Financial or not (for H2).** "Financial" means the failed firm is a bank, NBFC,
housing-finance company, insurer, broker or asset manager. Real estate is not
financial.

**Who labels.** Claude writes the paragraphs and the labels. Mrigay checks them before any
rival return is computed. Phase 6 of the project later asks an LLM to label the same
paragraphs on its own.

## 6. Outcome and predictions (c)

- **Rival outcome.** For each rival: its compounded return over days 0–20 (21 trading
  days) minus the market's compounded return over the same days. This is the 20-day
  buy-and-hold abnormal return, **BHAR**. Missing returns count as zero.
- **Rival filter.** One-day rival returns beyond ±45% are removed as probable unadjusted
  corporate actions, and every removal is logged, as in `death_test.py`.
- **Market for the outcome.** The equal-weighted universe, excluding the failed firm, its
  rivals and its group firms.
- **Case outcome.** The equal-weighted mean of its rivals' BHARs.
- **Prediction:**
  - **SD cases:** case outcome **< 0**.
  - **OR cases:** case outcome **≥ 0**.
  - **Group sets (H3):** mean group-firm BHAR **< 0**.

## 7. Tests (d) and what counts as success

One case = one failed firm and its rival set. US and India cases are pooled.

- **T1 (primary): the difference in means.** Mean outcome of SD cases minus mean outcome
  of OR cases.
  - One-sided permutation p-value: shuffle the labels across cases 20,000 times (seed
    20261111), keeping the number of SD and OR cases fixed. *p* is the share of shuffles
    with a difference at least as negative as the real one.
- **T2: the hit rate.** The share of cases whose sign matches the prediction, overall and
  within each label. A one-sided Fisher exact test of label against sign (outcome < 0)
  goes with it.

**Verdict on H1 (fixed now):**
- **Supported:** T1 *p* < 0.05 **and** the hit rate is above 50% in both the SD and the OR
  group.
- **Partly supported:** T1 *p* < 0.05, but one group's hit rate is 50% or below. For
  example, rivals fall in both groups, only more after SD cases.
- **Not supported:** T1 *p* ≥ 0.05.
- **Too few cases to test:** either label has fewer than 5 cases. T1 is then reported as
  description only.

**T3 (H2): financial versus non-financial failed firms.**
- For each subgroup, report:
  - the number of cases by label;
  - the hit rate by label;
  - the mean difference with its permutation *p*, if each label has at least 3 cases.
- **"Works" in a subgroup** means:
  - the difference in means has the predicted sign, and the hit rate is above 50% in
    both labels; or
  - if one label has fewer than 3 cases, the hit rate in the other label is at least 2/3.
- **What each outcome means, decided now:**
  - **Works in both subgroups:** the general claim stands. What rivals share with the
    failed firm predicts their reaction inside and outside finance.
  - **Works only within financials:** the claim **narrows to financial contagion**.
    Shared funding and depositors spread a failure, but outside finance the rule does
    not predict rivals' reactions. The title and abstract will say so.
  - **Works only outside financials:** the general claim survives outside finance, and
    the financial cases need another explanation. (Not expected.)
  - **Works in neither:** the rule fails out of sample.

**T4 (H3): group sets.** Report the mean group-set BHAR, the share of group sets below
zero, and a sign test.

**T5 (H4): market share.**
- **Share** = the failed firm's 63-day traded value divided by the total for itself and
  its rivals, measured the day before day 0.
- Report the Spearman correlation between share and the case outcome, and an OLS of the
  outcome on an SD dummy plus share, with heteroskedasticity-robust t-statistics.
- **Prediction:** the SD coefficient is negative and |t| ≥ 2; share has |t| < 2.
- If share is significant and the label is not, H4 fails and the paper says so.

## 8. Robustness checks (reported, but they do not change the verdict)

- Market-model abnormal returns: each rival's beta is estimated on days −260 to −11, and
  its compounded return is compared with the compounded beta-scaled market return.
- Median rival instead of mean; the share of rivals with BHAR < 0.
- Day-0 and days 0–5 windows.
- Excluding events in 2008–09 and February–April 2020.
- US and India separately.
- The outcomes of the "industry shock" cases, described separately.

## 9. Case list (Part 2)

**Status: FINAL.** Mrigay approved all 40 labels (§9b and §9f) in chat on 11 November 2026, before any rival return was computed. Nothing in §1–§9 changes after this commit; any later change goes in §10.

*Written 11 November 2026 from news only, before any rival return was computed. The
machine-readable list is `docs/entropy_research/oos_cases.csv`. The news checks behind
the paragraphs are summarised here; facts marked "(memory)" in the checks were not
source-verified.*

### 9a. How the rules were applied

- **Selection** (`death_test_oos.py select`): 106 Indian and 89 US candidates remained
  after excluding the eight used cases. A random sample of 60 was drawn in each market
  (seed 20261111). Selection used only each firm's own returns and the market's.
- **Rule 2, "no fall to explain."** In March–May 2009 the Indian market rose about 48% in
  20 days, so 11 stocks whose own price barely moved (own 20-day return above −20%)
  counted as "falling 50% abnormally". There is no fall for any news to explain, so they
  are dropped.
- **Rule 1 and the news check.** Artefacts are dropped: splits, bonuses, demergers, rights
  issues, bad prints, and old tickers that carry another company's data.
- **At least 3 rivals.** India: rivals were chosen by hand from the stocks in the top 300
  on day 0. US: rivals are the S&P 500 members of the same sub-industry in the current
  file. Many 2000s US candidates had only 1–2 such members and are dropped; the
  sub-industry file holds today's index members only.
- **Same-day or overlapping cases are kept**, as the rules say. For example, Regions and
  Fifth Third, two days apart, are each in the other's rival set. This works *against* the
  hypothesis for OR cases. A sensitivity check that drops the later case of each such
  pair will be reported, labelled as not pre-registered.
- **Disclosure.** The candidate list itself shows which other firms crashed, so for a few
  cases it was visible that a rival also fell around the same time. Labels were assigned
  by the rule, not from that.

### 9b. The 26 cases

**India (12 cases, all OR)**

1. **IN-MAYTAS: Maytas Infra, day 0 = 17 Dec 2008. OR.** Maytas Infra builds roads,
   irrigation and metro projects. It is controlled by the Raju family, who also founded
   Satyam Computer Services. On the evening of 16 December, Satyam's board approved buying
   Maytas Infra and the unlisted Maytas Properties for about US$1.6 billion. Investors
   objected that cash was being moved to the founders' family firms, and the deal was
   withdrawn before the market opened on 17 December. The shock is about the promoter
   family's governance. Other construction contractors share no funding market, depositors,
   owner or liability with it. *Rivals:* L&T, Jaiprakash Associates, Punj Lloyd, IVRCL,
   HCC, Nagarjuna Construction, Gammon, Patel Engineering.

2. **IN-THINKSOFT: Thinksoft Global, day 0 = 16 Feb 2010. OR.** Thinksoft tests banking
   software for banks and insurers. It listed in October 2009 and its price had risen
   steeply. In mid-February the exchanges moved the stock into the trade-for-trade
   surveillance segment, and it hit lower price limits on 16 and 17 February. The trigger
   is exchange surveillance of this one stock's trading. *Rivals:* the 10 largest IT
   services firms in the universe (TCS, Wipro, Mphasis, HCL Tech, Rolta, Tech Mahindra,
   Oracle Financial Services, Polaris, Patni, 3i Infotech).

3. **IN-COREEDU: Core Education & Technologies, day 0 = 25 Feb 2013. OR.** Core sells
   IT-based education services to schools and governments. On 25 February, reports said
   lenders were selling Core shares that an investor had pledged and could not top up.
   Panic selling followed (about −60% that day), and SEBI opened a probe into the selling
   in several small and mid caps. The trigger is forced selling of this firm's pledged
   shares. *Rivals:* Educomp, Everonn, Aptech.

4. **IN-SUDAR: Sudar Industries, day 0 = 25 Feb 2013. OR.** A garment exporter, named in
   the same 25 February pledged-share panic. *Rivals:* Raymond, Arvind, Alok, Bombay
   Dyeing, S. Kumars.

5. **IN-DRDATSONS: Aanjaneya Lifecare (later Dr Datsons Labs), day 0 = 25 Feb 2013. OR.**
   A pharmaceutical maker, named in the same panic; it fell about 56% in six sessions.
   *Rivals:* the 10 largest pharma firms in the universe.

6. **IN-GITANJALI18: Gitanjali Gems, day 0 = 14 Feb 2018. OR.** A jewellery maker and
   retailer controlled by Mehul Choksi. On 14 February, Punjab National Bank disclosed a
   ₹11,400 crore fraud through letters of undertaking issued for firms of Nirav Modi and
   of Choksi's Gitanjali group, and enforcement raids followed. The fraud concerns the
   promoter's own conduct. A lender is named (PNB), but nothing on day 0 says rival
   jewellers depend on PNB, which the non-financial funding rule requires. *Rivals:* PC
   Jeweller, Titan, Rajesh Exports.

7. **IN-RCOM: Reliance Communications, day 0 = 4 Feb 2019. OR.** A telecom firm of the
   Anil Ambani (ADAG) group that had shut most mobile services in 2017–18. On 4 February
   its board said 18 months of asset sales had failed to repay lenders (debt above ₹46,000
   crore) and that it would go to the insolvency tribunal. A firm-specific debt failure:
   rivals are telecom operators with their own funding. *Rivals:* Bharti Airtel, Vodafone
   Idea, Tata Communications. *Group set (H3):* Reliance Capital, Reliance Infrastructure,
   Reliance Power.

8. **IN-RELCAP: Reliance Capital, day 0 = 12 Jun 2019. OR (borderline).** The ADAG group's
   NBFC holding company (lending, insurance, mutual fund, broking), funded by bank loans,
   bonds and commercial paper. On the evening of 11 June its auditor PwC resigned, saying
   its queries had not been answered satisfactorily, and the company called the
   observations baseless. Group debt stress was the background, but the news check found
   no missed payment, default or rating cut on day 0. The funding channel needs a funding
   or solvency failure as the trigger, so the tie-break gives OR. *Rivals:* the 10 largest
   NBFCs and housing-finance companies in the universe (incl. Indiabulls Housing, Bajaj
   Finance, DHFL, LIC Housing). *Group set:* RCom, Reliance Infrastructure, Reliance Power,
   Reliance Nippon AMC.

9. **IN-CGPOWER: CG Power, day 0 = 20 Aug 2019. OR.** A maker of transformers, switchgear
   and motors (formerly Crompton Greaves) in the Avantha group. On 20 August it disclosed
   that an internal review had found unauthorised transactions hiding about ₹635 crore of
   liabilities. Fraud by its own management. *Rivals:* BHEL, Siemens, ABB.

10. **IN-IBHFL: Indiabulls Housing Finance (now Sammaan Capital), day 0 = 6 Sep 2019. OR
    (borderline).** A housing-finance company funded by bank loans, bonds, commercial
    paper and debt mutual funds. On 6 September, reports of a public-interest petition
    alleging that the promoters diverted funds through shell companies hit the stock. The
    Delhi High Court listed the petition on 27–30 September, and the company denied the
    claims. The trigger is a fraud allegation, not a funding failure, so the rule gives OR.
    *Rivals:* HDFC, DHFL, LIC Housing, PNB Housing, Can Fin, Aavas, Repco. *Group set:*
    Indiabulls Real Estate, Indiabulls Ventures.

11. **IN-FRETAIL: Future Retail, day 0 = 6 Mar 2020. OR.** The Big Bazaar supermarket chain
    of the Future group. On 6 March a disclosure showed promoter shares pledged for
    debentures of a group entity, and lower price limits followed from 13 March. The trigger
    is promoter-group debt. The COVID crash and lockdown fall inside the window. *Rivals:*
    DMart, Trent, Aditya Birla Fashion.

12. **IN-OMAXE: Omaxe, day 0 = 29 Jun 2020. OR.** A North-India property developer with 52%
    of promoter shares pledged. On 29 June it postponed the board meeting for its annual
    results by a month, and the stock hit lower limits for two days. Firm-specific.
    *Rivals:* DLF, Godrej Properties, Oberoi Realty, Prestige.

**US (14 cases: 2 SD, 12 OR)**

13. **US-XRX: Xerox, day 0 = 3 Oct 2000. OR.** A copier maker. On 3 October it gave its
    fourth profit warning in five quarters. It then cut the dividend and said it could not
    borrow in the commercial-paper market, while denying bankruptcy rumours. Its problems
    were its own sales and billing. As a non-financial firm, no lender is named that rivals
    rely on. *Rivals:* HP, NetApp, Western Digital.

14. **US-XEL: Xcel Energy, day 0 = 26 Jul 2002. OR.** A utility holding company that owned
    NRG Energy, a merchant power producer. On 26 July, S&P cut NRG to junk, triggering about
    $1.1–1.3 billion of collateral demands, and Moody's put Xcel under review because it
    might have to support NRG. (The stock had fallen 23% on 23 July for a reason the news
    check did not find.) The failure is its own subsidiary's credit; rivals are other
    utilities. Context: the 2002 merchant-energy credit squeeze after Enron. *Rivals:* 11
    multi-utilities.

15. **US-C: Citigroup, day 0 = 19 Nov 2008. SD (funding).** The largest US bank by assets,
    funded by deposits (much of them uninsured and foreign), wholesale debt and repo. On 19
    November it said it would take the remaining $17.4 billion of assets of its structured
    investment vehicles onto its balance sheet, deepening doubts about its capital. Within
    three days its executives asked the government for help, and a rescue was announced on
    23 November. This is a solvency/confidence failure needing a rescue, and the rivals
    are banks funded in the same deposit and wholesale markets. (Borderline only on
    timing: the rescue need became explicit two days after day 0.) *Rivals:* BofA, JPMorgan,
    PNC, Truist, US Bancorp, Wells Fargo.

16. **US-HIG: Hartford Financial, day 0 = 30 Oct 2008. OR.** A property-casualty and life
    insurer. It reported a $2.6 billion Q3 loss on investments, halved its 2008 guidance,
    and analysts said it might need $2 billion of capital. That is a capital worry, with no
    failure to pay or rescue on day 0. Its rivals are P&C insurers funded by premiums.
    *Rivals:* Allstate, Cincinnati Financial, Progressive, Travelers.

17. **US-CI: Cigna, day 0 = 30 Oct 2008. OR.** A health insurer. Q3 profit fell 53% on losses
    in its run-off variable-annuity reinsurance, and it cut its outlook. This is its own
    legacy business. *Rivals (current sub-industry "Health Care Services"):* CVS, DaVita,
    LabCorp, Quest.

18. **US-BAC: Bank of America, day 0 = 16 Jan 2009. SD (funding).** It reported a Q4 loss,
    mostly from Merrill Lynch. The government announced a second capital injection of $20
    billion and a guarantee on about $118 billion of assets. The bank needed a rescue, and
    the rivals are banks funded in the same markets. *Rivals:* Citi, JPMorgan, PNC, Truist,
    US Bancorp, Wells Fargo.

19. **US-STT: State Street, day 0 = 20 Jan 2009. OR (borderline).** A custody bank funded
    mostly by large clients' uninsured deposits and wholesale money. Q4 profit fell 71%,
    and investors feared it would need capital after moving troubled conduit assets onto
    its balance sheet. There was no failure or rescue on day 0. Its rivals are mostly asset
    managers that take no deposits. 20 January was also a broad bank sell-off day.
    *Rivals:* Ameriprise, Franklin, Invesco, Northern Trust, T. Rowe Price.

20. **US-RF: Regions Financial, day 0 = 20 Jan 2009. OR.** A regional bank. Its Q4 net loss
    was $6.2 billion, mostly a $6.0 billion non-cash goodwill write-down, plus a $1.15
    billion loan-loss provision. Large losses, but no funding failure or rescue on day 0.
    Same broad bank sell-off day. *Rivals:* Fifth Third, Huntington, KeyCorp, M&T.

21. **US-FITB: Fifth Third, day 0 = 22 Jan 2009. OR.** A regional bank. Q4 loss of $2.2
    billion from a goodwill write-down and higher loan-loss reserves. *Rivals:* Huntington,
    KeyCorp, M&T, Regions.

22. **US-AFL: Aflac, day 0 = 22 Jan 2009. OR.** A supplemental insurer. A Morgan Stanley
    note questioned its capital, given $7.9 billion of hybrid securities (mostly bank
    preferreds). Aflac replied that its capital ratio was 425–475%, and its rating was cut
    one notch to AA−. No failure. *Rivals:* Globe Life (then Torchmark), MetLife,
    Principal, Prudential.

23. **US-TXT: Textron, day 0 = 29 Jan 2009. OR.** An aircraft (Cessna, Bell) and industrial
    group whose finance arm was being wound down. Q4 results showed write-downs at Textron
    Financial, a $625 million capital injection into it, job cuts and loss guidance. A
    non-financial parent. *Rivals:* Boeing, GE, General Dynamics, L3Harris, Lockheed,
    Northrop, RTX.

24. **US-EPAM: EPAM Systems, day 0 = 24 Feb 2022. OR.** Software-engineering services with a
    large share of its engineers in Ukraine, Belarus and Russia. Russia's invasion on 24
    February put its delivery centres at risk. The shock hits this firm's own geography;
    rival IT consultancies have little exposure there. *Rivals:* Accenture, Cognizant,
    Gartner, IBM.

25. **US-GL: Globe Life, day 0 = 11 Apr 2024. OR.** A life and supplemental-health insurer.
    A short seller (Fuzzy Panda) alleged misconduct in its American Income Life agency
    force. A fraud allegation about its own sales practices. *Rivals:* Aflac, MetLife,
    Principal, Prudential.

26. **US-SMCI: Super Micro Computer, day 0 = 30 Oct 2024. OR.** A server maker for AI data
    centres. Its auditor, Ernst & Young, resigned, saying it could no longer rely on
    management's representations, after a short-seller report and a delayed annual filing.
    Its own governance. *Rivals:* Apple, Dell, HPE, HP, NetApp, Seagate, Western Digital.

### 9c. Industry shocks (outcomes reported, not in the primary test)

- **US-PCG01: PG&E, 4 Jan 2001.** California energy crisis: wholesale power cost more than
  the frozen retail rates, and regulators granted only a small rate rise. The regime
  covers all California utilities.
- **US-TLAB01: Tellabs, 20 Jun 2001.** It cut Q2 revenue guidance by about 35% because
  telecom carriers cut spending: an industry-wide demand collapse.
- **US-GNW08: Genworth, 29 Sep 2008.** It fell on the day the House rejected the bank
  rescue bill, a market-wide panic.
- **IN-GITANJALI13: Gitanjali Gems, 24 Jun 2013.** Gold-import curbs covered all jewellers.
- **Listed without an outcome** (no news date, or fewer than 3 rivals): Vodafone Idea
  2019 (Supreme Court AGR ruling on all telecom licensees; only 2 rivals in the universe);
  Bhushan Steel 2008 (steel price crash, no news date); PVR and Quess 2020 (COVID);
  Delta 2020 (COVID; 2 rivals); Akamai 2000 (dot-com fall, no date).

### 9d. Dropped candidates (sampled 60 per market)

- **India:**
  - No fall: EICHERMOT, AKRUTI, STERLINBIO, RELGOLD, CIPLA, AUSTRAL, ITC, SUNPHARMA,
    HINDUNILVR, LIQUIDBEES, SHREEASHTA.
  - Artefacts: MAHSEAMLES (split), LT (bonus), ZEETELE (demerger), DABUR (bonus), WHEELS
    (rights), MASTEK (demerger); RKDL, HELIOSMATH, BSLIMITED (data ends but the stock kept
    trading).
  - No news or no day 0: NIITTECH, DHANUS, PURVA, PANACEABIO, APOLLOSIND, KGL, RESURGERE,
    RUSHIL, PLETHICO, ERAINFRA, GOENKA, GATECH, PATNI (news explains about 6% of a 53%
    abnormal fall), SELMCL (no dated news), TATASTLBSL (no dated news), SECURKLOUD (date of
    the results deferral not established).
  - Fewer than 3 rivals: PSTL (Pyramid Saimira), PCJEWELLER, KWALITY (2 dairy rivals),
    EROSMEDIA, BCG, 63MOONS and MCX (no listed rival exchanges).
- **US:**
  - Artefacts: CBE 2000 and 2001, EP 2001 and 2010, JCI 2002 and 2007 (split), CFC 2006,
    CPWR 2006, GR 2009, BMC 2012.
  - No news or no day 0: EIX 2000, VRSN 2000, A 2000, CIEN 2000, ISRG 2000, JBL 2000, ANDV
    2002, GR 2002, EP 2003, CFC 2007, CNX 2008, MEE 2008, WDC 2000, CNP 2002.
  - Fewer than 3 rivals: BKNG 2000, OI 2000, CCK 2000, GLW 2001 and 2002, CIEN 2001, AES
    2001, AMT 2001, HAL 2001, SEE 2002, EP 2002, THC 2002 and 2008, SLM 2007, AIG 2008,
    COF 2009, COTY 2020.

### 9e. What this list already shows (before any rival return)

Applied strictly, the rule labels only **2 of 26** collapses as shared dependency (Citi
and Bank of America, both 2008–09 bank rescues). Under §7, fewer than 5 cases in a label
means T1 is reported as description only ("too few cases to test"). Most single-firm
collapses in a random sample are about the firm's own conduct: fraud, governance, its own
losses. That is itself a finding about how rare true shared-dependency failures are. It
also means the out-of-sample evidence will mainly test the **OR half** of the
prediction (rivals do not lose) and H4 (market share).

### 9f. Extension under deviation D1 (14 cases: 2 SD, 12 OR)

*The same rules, applied to the 69 candidates the random draw left out. 34 were real; the
rest are artefacts (Adani Enterprises 2015 and Aditya Birla Real Estate 2019 are demergers)
or have no news. The paragraphs use day-0 facts only.*

27. **IN-ATLANTA: Atlanta Ltd, 23 Feb 2007. OR.** A road and infrastructure builder. On 22
    February, SEBI issued an interim order barring the company and its promoters from
    dealing in the shares and opened an investigation into the price rise and promoter
    buying. The regulator acted against its own trading conduct. *Rivals:* IVRCL, L&T,
    Jaiprakash, Nagarjuna, Gammon, Patel, Simplex.
28. **IN-WOCKHARDT: Wockhardt, 27 May 2014. OR.** A generic drug maker. Its results, released
    after the close on 26 May, showed profit down about 78% because US FDA import bans on
    several of its plants cut US sales, and fresh FDA concerns about another plant followed.
    These are findings about its own plants. *Rivals:* the 10 largest pharma firms in the
    universe.
29. **IN-AMTEK: Amtek Auto, 19 Aug 2015. OR.** A heavily indebted maker of forgings and
    castings. NSE said on 18 August that it would drop the stock from the derivatives
    segment, after a quarterly loss. It concerns the firm's own stock and debt, and no
    lender is named as at risk. *Rivals:* Bharat Forge, Bosch, Exide.
30. **IN-RPOWER: Reliance Power, 4 Feb 2019. OR.** An ADAG power producer. After RCom's
    insolvency announcement, lenders to the promoter group sold pledged shares. This is
    promoter-group pledge stress; Reliance Power itself did not miss a payment. *Rivals:* NTPC,
    Adani Power, Tata Power, Torrent Power, CESC, NHPC.
31. **IN-RELINFRA: Reliance Infrastructure, 4 Feb 2019. OR.** An ADAG EPC, roads and
    Delhi-distribution company, hit by the same pledge sales. *Rivals:* L&T, NCC, Tata Power,
    Torrent, CESC, IRB, Jaiprakash, HCC, KEC, Adani Energy Solutions. (The ADAG group set is
    counted once, under IN-RCOM.)
32. **IN-LVB: Lakshmi Vilas Bank, 30 Sep 2019. SD (funding), borderline.** A small private
    bank funded mainly by retail deposits. RBI had put it under prompt corrective action
    because its capital was below the minimum and its bad loans were high. It depended on a
    pending rescue merger with Indiabulls Housing, and on 30 September it fell amid reports
    of RBI curbs and doubts about that merger. Reading: needing a rescue to stay solvent is
    a solvency failure (as for Citi and BofA), and its rivals are deposit-funded banks. (The
    helper proposed OR, treating it as "capital worries only".) *Rivals:* the 10 largest
    private banks in the universe.
33. **IN-DHFL19: DHFL, 1 Oct 2019. SD (funding).** A housing-finance company funded by bank
    loans, debentures, commercial paper held largely by mutual funds, public deposits and
    securitisation. It had been in default since June. On 1 October it fell 20% on its
    exposure to HDIL and the failing PMC Bank. A lender already in default, whose rivals are
    funded in the same bond, CP and mutual-fund market. *Rivals:* the 10 largest HFCs and
    NBFCs in the universe.
34. **IN-ATGL: Adani Total Gas, 25 Jan 2023. OR.** A city-gas distributor (an Adani and
    TotalEnergies joint venture). On 24 January, after the Indian close, Hindenburg
    published its report on the Adani group. The report concerns its group. *Rivals:* IGL,
    Gujarat Gas, Mahanagar Gas. This is the same episode as the in-sample Adani case, so it
    has no group set (those firms were already used); the rivals are new evidence.
35. **US-CI02: Cigna, 25 Oct 2002. OR.** A health insurer with a run-off reinsurance book.
    After a reinsurance charge on 18 October, it warned after the close on 24 October that
    Q3 and full-year earnings would miss guidance. This is its own earnings and reserve
    problem. *Rivals (current file):* CVS, DaVita, LabCorp, Quest.
36. **US-UNM03: UnumProvident, 10 Mar 2003. OR.** A disability and life insurer. A Moody's
    report questioned how its low-rated securities and claims affected its capital, with no
    downgrade or missed payment on day 0. *Rivals:* Aflac, Torchmark, MetLife, Principal,
    Prudential.
37. **US-MBI07: MBIA, 20 Dec 2007. OR, borderline.** A bond insurer whose business rests on
    its AAA rating. On 19 December, S&P moved its outlook to negative, and MBIA disclosed
    $8.1 billion of CDO-squared exposure. The rating was at risk but not cut. *Rivals
    (assigned: P&C insurance):* Allstate, Cincinnati, Hartford, Progressive, Travelers.
38. **US-LNC08: Lincoln National, 17 Nov 2008. OR, borderline.** A life and annuity insurer.
    Hit by investment losses, it applied for TARP capital and to become a savings-and-loan
    holding company, while saying its capital was adequate. Applying for TARP is not by
    itself an inability to pay; many healthy firms applied. *Rivals:* Aflac, Torchmark,
    MetLife, Principal, Prudential.
39. **US-HBAN09: Huntington Bancshares, 22 Jan 2009. OR.** A Midwest regional bank funded
    mainly by insured deposits. It reported a Q4 2008 loss on rising credit losses, with no
    run or funding failure. *Rivals:* Fifth Third, KeyCorp, M&T, Regions (Fifth Third
    reported the same day).
40. **US-PSKY21: ViacomCBS, 26 Mar 2021. OR.** A media group (CBS, Paramount). Banks dumped
    large blocks of its shares for a client that had missed a margin call (Archegos). This
    is forced selling by one holder, not a corporate event. *Rivals (assigned: Movies &
    Entertainment):* Live Nation, Netflix, Disney.

**Industry shocks in the extension (outcomes described only):** CreditAccess Grameen and
Aditya Birla Fashion (India COVID lockdown, 24 Mar 2020), Norwegian Cruise (US travel ban,
12 Mar 2020), APA (oil price war, 9 Mar 2020). Without an outcome: Sallie Mae 2009
(federal student-loan policy; 2 rivals), Micron 2008 (no date), NetApp 2000 (no rivals).

**Dropped for fewer than 3 rivals:** Shilpi Cable, Jain Irrigation, Indiabulls Ventures,
Paytm, Opto Circuits, Vakrangee, Infibeam, Advance Auto Parts, Best Buy, VeriSign,
Williams, Quanta, ONEOK.

**Full population: 40 cases, 4 SD (Citi, BofA, Lakshmi Vilas, DHFL 2019) and 36 OR.**
This is still fewer than 5 SD, so under §7 T1 is "too few cases to test" in both versions.
Labels were not flipped to reach 5.

## 10. Deviation log

**D1 (11 Nov 2026, before any rival return was computed): the size cap is lifted.**
- **Why:** under the strict rule the registered sample of 26 cases has only 2
  shared-dependency cases, below the 5 that T1 needs. That count was known from the
  labels. No rival outcome was known.
- **Decision (Mrigay, in chat):** news-check every remaining candidate with the same rules.
  That is the 40 Indian and 29 US candidates the random draw left out that had a real own
  fall. The 6 unsampled Indian rally names with no fall are dropped by rule 2, as before.
- **Reporting:** both versions are reported, in the same tables: (i) the registered
  sample, exactly as in §9, and (ii) the full population, i.e. the registered sample plus
  the extension.
- **Verdict:** the §7 verdict rules are applied to both versions. Where the two differ,
  the paper says so.

## 11. Results (run 11 November 2026, after the Part 2 commit)

*The analysis ran once, exactly as committed in c57c331 (`scripts/death_test_oos.py run`),
with no change to the code, the labels or the rules. Outputs: `results/death_test_oos/`
(`outcomes.csv`, `outcomes_peers.csv`, `tests.json`, `run.log`). Every number below comes
from `tests.json` or `outcomes.csv` unless it is marked otherwise.*

**How to read the numbers.** For each case, the outcome is the average rival's 20-day
abnormal return (BHAR, days 0–20): the rival's compounded return minus the market's. −10%
means the typical rival did 10 percentage points worse than the market over the month
after the collapse. A "hit" is a case whose sign matches the prediction: SD rivals below
zero, OR rivals at or above zero. A coin would score about 50%.

### 11a. The pre-registered tests

| | **Registered sample (primary)** | **Full population (deviation D1)** |
|---|---|---|
| Cases (SD / OR) | 26 (2 / 24) | 40 (4 / 36) |
| Mean outcome, SD cases | **−18.0%** (Citi −13.5%, BofA −22.6%) | **−9.3%** (adds Lakshmi Vilas −0.6%, DHFL 2019 −0.4%) |
| Mean outcome, OR cases (median) | **−3.7%** (−0.8%) | **−3.4%** (−0.8%) |
| T1: SD minus OR | −14.3 pp, description only (SD < 3, no *p* computed) | −5.9 pp, permutation *p* = 0.152 (description only) |
| T2: hit rate, all cases | 13 / 26 = **50%** | 20 / 40 = **50%** |
| T2: hit rate, SD / OR | 2/2 = 100% / 11/24 = **46%** | 4/4 = 100% / 16/36 = **44%** |
| T2: Fisher exact *p* | not computed (SD < 3) | 0.116 |
| **H1 verdict (§7)** | **Too few cases to test** | **Too few cases to test** |

Under the rule fixed in Part 1, H1 cannot be tested: each version has fewer than 5 SD
cases. The verdict is the same in both versions, so there is no disagreement to report.

**T3 (H2): financial versus non-financial failed firms.**

| | Registered | Full population |
|---|---|---|
| Financial: cases (SD / OR) | 11 (2 / 9) | 18 (4 / 14) |
| Financial: hit rate SD / OR | 100% / 44% | 100% / 43% |
| Financial: SD − OR, perm *p* | −11.7 pp, not computed (SD < 3) | −3.1 pp, *p* = 0.348 |
| Non-financial: cases (SD / OR) | 15 (0 / 15) | 22 (0 / 22) |
| Non-financial: hit rate OR | 7/15 = 47% | 10/22 = 45% |
| "Works" (§7)? | neither subgroup | neither subgroup |
| **Pre-registered meaning** | **"Works in neither: the rule fails out of sample."** | **Same** |

*Why "fails".* With fewer than 3 cases in one label, §7 requires the other label's hit
rate to be at least 2/3. Outside finance there are no SD cases, and OR rivals lost in
more than half the cases (hit 45–47%). Inside finance, the full population has 4 SD
cases, but the OR hit rate is 43%, below the 50% that §7 requires. So, by the rule
written in advance, the classification rule fails out of sample. The failure is in the
OR half: rivals of "output-replaceable" failed firms did **not** reliably hold up.

**T4 (H3): business-group sets (India).** 3 group sets (RCom's ADAG group, Reliance
Capital's ADAG group, Indiabulls Housing's group). All 3 fell: −37.5%, −9.9%, −36.5%; mean
**−28.0%**. Sign test *p* = 0.125, the smallest *p* possible with 3 sets. The direction is
as predicted, but 3 sets cannot be significant. (The RCom group set holds Reliance Power
and Reliance Infrastructure, which fell the same day on the same pledge sales.)

**T5 (H4): market share.** Share = the failed firm's 63-day traded value over the total for
it and its rivals.

| | Registered (26) | Full population (40) |
|---|---|---|
| Spearman (share, outcome) | −0.14 (*p* 0.51) | −0.09 (*p* 0.58) |
| OLS: SD dummy | −13.2 pp (*t* −2.96) | −6.3 pp (*t* −1.42) |
| OLS: share | −0.15 (*t* −0.99) | −0.14 (*t* −1.01) |
| Prediction (SD \|*t*\| ≥ 2 and share \|*t*\| < 2) | met (but the SD dummy is 2 cases) | SD part not met; share part met |

A share coefficient of −0.15 means a failed firm with 30% of its group's trading rather
than 10% goes with rivals about 3 pp worse, and that estimate is not distinguishable from
zero. **H4 holds in both versions: share does not predict the 20-day rival reaction.**

### 11b. Robustness checks (§8; they do not change the verdict)

| Check | Registered: SD / OR mean (OR hit) | Full: SD / OR mean (OR hit); perm *p* |
|---|---|---|
| Market-model (beta-adjusted) BHAR | −17.9% / −3.2% (46%) | −9.7% / −2.8% (44%); *p* 0.097 |
| Median rival instead of mean | −20.2% / −4.1% (33%) | −10.0% / −3.6% (33%); *p* 0.124 |
| Day 0 only | −5.6% / −1.8% (25%) | −3.2% / −2.0% (22%); *p* 0.210 |
| Days 0–5 | −7.0% / −1.0% (50%) | −4.6% / −1.5% (44%); *p* 0.140 |
| Excluding 2008–09 and Feb–Apr 2020 | no SD left / −1.9% (47%), 15 cases | **−0.5% / −1.7%** (44%), 27 cases |
| US only | −18.0% / −4.5% (50%), 14 cases | −18.0% / −5.0% (44%), 20 cases |
| India only | no SD / −2.9% (42%), 12 cases | **−0.5% / −1.8%** (44%), 20 cases |
| Industry shocks (described only) | 4 cases, mean −3.4% | 8 cases, mean −9.0% |

What the checks say:
- **The SD–OR gap comes entirely from Citi and Bank of America in the 2008–09 crisis.**
  Without the crisis months, and in India alone, SD rivals did slightly *better* than OR
  rivals (−0.5% against −1.7% or −1.8%): the opposite of H1. Lakshmi Vilas and DHFL 2019
  count as SD "hits" only because −0.6% and −0.4% are below zero. For DHFL 2019 the median
  rival rose 2.8% and only 4 of 10 rivals fell.
- **On day 0, rivals fell in about 3 of every 4 OR cases** (OR day-0 hit rate 22–25%).
  This matches the large-sample result (§4c): rivals share the first-day hit, whatever
  the label.
- The beta-adjusted version gives the strongest gap (−6.9 pp, *p* 0.097), still above 0.05.

### 11c. Descriptive facts that are not tests (not pre-registered)

- OR mean, 95% interval (mean ± 1.96 standard errors): registered −3.7% [−8.1%, +0.7%];
  full −3.4% [−6.8%, +0.0%]. Small and negative, and not clearly different from zero.
- The 10 OR cases from September 2008 to March 2009 average −8.1% (Regions −29%,
  Huntington −28%, Fifth Third −25%, Aflac −22%). The other 26 OR cases average −1.6%
  (median −0.2%, 14 of 26 negative).
- **Rival return filter (disclosure).** The pre-registered ±45% filter removed 13 rival
  daily returns (`run.log`). Some were real moves, not corporate actions: Citi +58% on 24
  November 2008 (rescue day), KeyCorp and Huntington +50–54% on 14 October 2008, Fifth Third
  +60% and Regions +48% on 6 February 2009, Occidental −52% on 9 March 2020. The 6 February
  2009 removals fall inside the 20-day windows of Regions, Fifth Third and Huntington, three
  OR cases, and make their rival outcomes more negative. That works against the OR
  prediction. The rule was fixed in advance and was not changed.

### 11d. Sensitivity check promised in §9a (NOT pre-registered)

*Written after the pre-registered run. Code: `scripts/death_test_oos_sensitivity.py`;
output: `results/death_test_oos/sensitivity_overlap.json` and `.log`.*

Rule: if two cases' failed firms are in each other's rival sets and their day 0s are
within 20 trading days, drop the later case. Pairs found: Regions/Fifth Third (2 days),
Regions/Huntington (2 days), Fifth Third/Huntington (same day), Indiabulls Housing/DHFL
2019 (16 days). Dropped: **Fifth Third, Huntington, DHFL 2019**.

| | Registered (25: 2 SD / 23 OR) | Full (37: 3 SD / 34 OR) |
|---|---|---|
| SD / OR mean | −18.0% / −2.8% | −12.2% / −2.0% |
| Hit rate SD / OR | 100% / 48% | 100% / 47% |
| SD − OR, perm *p* | not computed | −10.2 pp, *p* = 0.050 |
| Verdict / T3 meaning | too few cases / rule fails | too few cases / rule fails |
| T5: SD *t* / share *t* | −3.24 / −0.69 | −2.08 / −0.87 |

Removing the double-counted bank cases sharpens the gap, but the verdicts do not move: SD
stays below 5 cases, and the OR hit rate stays below 50%. The *p* of 0.050 comes from a
check chosen after the data were seen, rests on 3 SD cases (two of them Citi and BofA),
and must not be read as support for H1.

### 11e. What the pre-registered test says, in one paragraph

Applied from the news alone, the rule labels **few collapses as shared dependency** (4 of
40). Those few, Citi and Bank of America above all, did see their rivals fall hard, so the
direction is as predicted. There are too few of them to test H1, though, and the gap
disappears outside the 2008–09 crisis. The other half of the rule, that rivals of
"replaceable" firms do not lose, **failed**: in 55% of those cases rivals fell, by about
3–4% on average, and the pre-registered T3 reading is "the rule fails out of sample".
**Market share did not predict rivals' reactions** in either version (|*t*| ≈ 1), which
agrees with the large-sample result. Group firms in India fell in all 3 cases. The
evidence supports "share is not the answer" more firmly than it supports "shared
dependency is the answer".
