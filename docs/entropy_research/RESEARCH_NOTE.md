# Entropy, Replaceability and the "Death Test": Research Note

**Started:** 9 November 2026 · **Author:** Mrigay Pathak · **Status:** pilot + death test v2 + 8 case studies done; paper question decided (§6); drafting next
**Code:** `scripts/entropy_research.py` · **Outputs:** `results/entropy_research/`
**Next session prompt:** `docs/entropy_research/NEXT_SESSION_PROMPT.md`

---

## 1. The idea in plain words

Inspired by *Zero to One* (p. 34).

- **Entropy** of a distribution of market shares measures how much any one firm's
  identity matters.
  - **High entropy:** many interchangeable firms. If one dies, its customers and staff
    move to the others, and nothing important is lost. This is close to perfect
    competition.
  - **Low entropy:** activity or capability sits in a few firms. If one dies, something
    real disappears with it.
- **Market share isn't the whole story.** A firm with 10% share can be the only one
  that has a certain technology, licence or factory. Its death matters more than its
  share suggests. The real variable is **replaceability**.
- **The "death test":** if firm *i* vanished tomorrow, how much of what it does could
  the rest of the system rebuild?
- **The paradox for investors:** you may want a *high-entropy portfolio* (diversified)
  made of firms that each operate in *low-entropy markets* (hard-to-replace, Thiel-style
  businesses).

## 2. Making it precise: "entropy of what?"

Entropy is a property of a **distribution**, not of "the economy". The idea has three
distributions in it, and they need to be kept apart:

| Distribution | What high entropy means | Can we measure it now? |
|---|---|---|
| **Portfolio weights** | diversified, no single stock matters | Yes (Test 1) |
| **Market activity** (size, trading, co-movement) | activity spread out, stocks move independently | Partly. We have trading value but no market caps (Test 2) |
| **Capabilities** (who can do what) | many firms can do the same thing, so each is replaceable | Only indirectly, through how prices react when a firm is hit (Test 3) |

For weights *w*: Shannon entropy H = −Σ wᵢ ln wᵢ (we report H / ln N, so 1 means
perfectly even). HHI = Σ wᵢ², and the effective number of firms is 1 / HHI.

## 3. What we tested on 9 November 2026, and what we found

Data:
- **US:** S&P 500, 2000–2024, point-in-time members, delisted stocks included, about
  393 members a day with data.
- **India:** NSE survivorship-free panel (top 300 stocks by trading value), 2006–2024.
- Only prices and volume are available. There are no market caps and no fundamentals.

### Test 1: Does a high-entropy portfolio "perform best"?

**Method.**
- Take five 5-year windows (2000–04, 2005–09, …, 2020–24).
- In each window, draw 5,000 random portfolios of N stocks from that date's actual
  index members, equal-weighted, buy and hold.
- Compare each one with holding *all* the members.

Averaged over the five windows:

| N stocks | Portfolio entropy (0–1) | Median return / yr | Chance of beating all-members | Chance of lagging it by >3 pp/yr | Worst 5% |
|---|---|---|---|---|---|
| 1 | 0.00 | 9.8% | 42% | **46%** | −13.4% |
| 5 | 0.27 | 10.8% | 43% | 34% | +2.2% |
| 10 | 0.39 | 11.1% | 44% | 25% | +5.0% |
| 20 | 0.51 | 11.4% | 46% | 16% | +7.0% |
| 50 | 0.66 | 11.6% | 47% | **5%** | +8.8% |
| 100 | 0.78 | 11.6% | 48% | 0.7% | +9.8% |
| All (~390) | 1.00 | 11.7% | — | — | — |

**What it means.** Diversification does **not** raise the *average* ending wealth.
Because the stocks are picked at random, $1 has the same expected 5-year value at every
N, by construction. What diversification raises is the **typical** outcome (the median),
and it removes the left tail.

The reason is that individual stock returns are **skewed**:
- In each window only **39–47% of stocks beat the all-members portfolio**, and 6–38% lost
  money.
- The **top 10% of stocks produced 27–77%** of all net gains (77% in 2005–09).

A concentrated portfolio usually misses the few big winners. This matches Bessembinder
(2018).

So the precise version of the claim is:

> "A high-entropy portfolio maximises the *typical* investor's outcome, not the
> *average* one."

**Emergent concentration (bonus finding).** Start perfectly equal-weighted and do
nothing. Within 5 years the portfolio's effective number of stocks shrinks on its own,
because winners grow:

| Window | Stocks at start | Effective N after 5 years | Change |
|---|---|---|---|
| 2000–04 | 310 | 212 | −32% |
| 2005–09 | 335 | 224 | −33% |
| 2010–14 | 359 | 297 | −17% |
| 2015–19 | 400 | 320 | −20% |
| 2020–24 | 463 | 276 | **−40%** |

This is your "positive feedback" point in its simplest form. Concentration appears
without anyone choosing it, and a cap-weighted index *is* this process.

### Test 2: Is a low-entropy market more fragile?

**Method.**
- At each month-end, compute the **co-movement entropy**: the entropy of the eigenvalues
  of the 1-year correlation matrix of index members.
  - Low entropy means everything moves together, as if there were one big bet.
  - High entropy means stocks move independently.
- Also compute **trading-value entropy**, a size-concentration proxy.
- Then ask whether low entropy predicts bigger drawdowns or volatility in the next 3–6
  months, *after controlling for current volatility*. Use Newey–West t-statistics.

US, by entropy quintile:

| Quintile | Entropy | Volatility now | Next-3m volatility | Next-3m return | Next-6m max drawdown |
|---|---|---|---|---|---|
| Q1 (low) | 0.48 | 28.8% | 21.2% | **+8.3%** | −10.2% |
| Q3 | 0.63 | 15.8% | 20.5% | +1.2% | −13.0% |
| Q5 (high) | 0.73 | 13.0% | 14.1% | +3.2% | −10.2% |

Regression with current volatility as a control (US, 282 months):
- **Higher** entropy goes with a *deeper* future drawdown (t = −2.1) and *lower* future
  return (t = −2.2).
- In India (221 months) the signs are the same but nothing is significant
  (|t| ≤ 1.4).

**What it means.** The simple claim "low entropy = fragile" **fails** here.
- Low co-movement entropy shows up *during* crises, when fragility has already
  happened. Rebounds follow.
- If anything, risk builds in **calm, high-entropy periods**. This is the "volatility
  paradox" (Brunnermeier & Sannikov 2014).
- **Caveats:**
  - The evidence is weak (t ≈ 2 with many tests).
  - We tested the *level*. Kritzman et al. (2011) found that *sudden rises* in
    co-movement matter, and that is still untested.
  - Co-movement is not capability concentration. It measures something different.

**US vs India trading concentration.** Effective number of stocks by trading value:

| | Early | Middle | Latest |
|---|---|---|---|
| US | 2001: 56 | 2019: 95 | **2022: 48** |
| India | 2006: 51 | 2015: 96 | **2024: 118** |

- US trading has re-concentrated into mega-caps.
- India has *broadened*.
- The universes differ (S&P 500 vs NSE top 300) and this uses trading value, not market
  cap, so treat it as a hint.

### Test 3: The death-test pilot. When a firm crashes, do rivals absorb it or share its fate?

**Method.**
- Find **538 isolated idiosyncratic crashes**: an S&P 500 stock falls more than 15% in a
  day and at least 12% more than its sector.
- Keep only one crash per sector per day, so industry-wide news days are excluded.
- Measure the market-adjusted return of its same-sector peers.

Reading the peer reaction:
- **Peers rise:** a competitive effect. Rivals take its business, so the firm is
  replaceable.
- **Peers fall:** contagion, or shared fate.

| | Events | Peers, same day | t | Peers, days 0–5 | Peers, days 1–20 | % of events where peers fell |
|---|---|---|---|---|---|---|
| **All** | 538 | **−0.50%** | −7.8 | −0.49% | +0.43% | 67% |
| Financials | 44 | −1.19% | −3.2 | −0.32% | +1.13% | **82%** |
| Info Tech | 146 | −0.84% | −6.1 | −0.45% | +1.09% | 71% |
| Health Care | 98 | −0.31% | −2.7 | −0.43% | −0.51% | 70% |
| Industrials | 47 | −0.14% | −1.3 | **+0.43%** | **+0.97% (t 2.4)** | 53% |
| Materials | 29 | −0.05% | −0.2 | +0.27% | +0.97% | 62% |
| Top-5 firm in its sector | 73 | −0.65% | −3.5 | −0.80% | +0.45% | 73% |
| All other firms | 465 | −0.48% | −7.0 | −0.44% | +0.43% | 66% |

**What it means (first pass).**
1. On average, **shared fate beats replacement.** When one firm crashes, its peers fall
   with it.
2. This varies a lot by sector.
   - **Financials** are the clearest "not replaceable / systemic" case, as theory
     predicts: banks share funding and confidence.
   - **Industrials** show a hint of the competitive effect: peers gain over the next
     month.
3. A crash at a **top-5 firm** hurts peers a bit more, but the difference is not
   significant.
4. **Sector concentration (HHI) does not line up with the peer reaction.** Fragmented,
   middle and concentrated sectors give −0.23%, −0.89% and −0.40%. This fits your claim
   that market share ≠ importance, but 11 sectors are far too coarse to conclude
   anything.

**The core problem the paper must solve.** A peer falling on day 0 mixes two things:
- **(a) Importance:** the firm mattered to the system.
- **(b) Information:** the crash revealed bad news about the whole industry.

Lang & Stulz (1992) faced exactly this. The clean way to separate them is to use shocks
that carry **no industry news**: natural disasters, fires, fraud, accidents, a sudden
regulatory ban. Then look at **customers and suppliers**, not just rivals. This is the
design of Barrot & Sauvagnat (2016).

## 4. Scorecard of the claims so far

| Claim | Verdict | Evidence |
|---|---|---|
| A high-entropy portfolio is best for an investor without skill | **Supported, with a correction** | Same average return, much better median and tail (Test 1) |
| Concentration emerges on its own | **Supported** | Effective N falls 17–40% in 5 years with no trading (Test 1) |
| Low entropy = fragile market | **Not supported as stated** | Low co-movement entropy is a symptom of crises, not a warning. Calm periods hide the risk (Test 2) |
| Market share ≠ importance | **Supported, with a correction** | Share matters for the day-0 hit, not for lasting damage. Industry identity explains ~10× more (§4b). Satyam (big, absorbed) vs IL&FS (spread) |
| Importance = shared dependency | **New hypothesis, consistent with all 8 cases** | Not yet tested out of sample; that is the next step (§4b) |
| Some firms are replaceable, others structurally important | **Measurable** | Peer reactions differ sharply by sector (Financials vs Industrials) (Test 3) |

## 4b. Death test v2 and eight case studies (9 Nov, evening)

**Code:** `scripts/death_test.py` · **Outputs:** `results/death_test/`

### Part A: US, peers = GICS sub-industry

**Sample:** 266 isolated crashes in 37 sub-industries.

| | Peers, same day | Peers, days 0–20 | % of events where peers fell on day 0 |
|---|---|---|---|
| All crashes | **−1.20% (t −7.6)** | −0.29% (t −0.6) | 71% |
| Crashing firm has a small share of its sub-industry | −0.77% | −0.56% | 63% |
| Mid share | −1.07% | −0.29% | 70% |
| **Large share** | **−1.77%** | −0.01% | **81%** |

**Does market share explain the peer reaction?** Compare how much of the same-day
reaction each set of variables explains (adjusted R²):

| Explanatory variables | Adjusted R² |
|---|---|
| Firm's share + sub-industry HHI | **0.8%** |
| Which sector it is | 8% |
| Which sub-industry it is | **14%** |

**Is it a stable trait of an industry?** Rank the industries by their average same-day
peer reaction in 2000–12 and again in 2012–24, then compare the two rankings:
- sub-industries: Spearman **0.79** (only 7 qualify);
- sectors: 0.90 (5 qualify).
- The 20-day reaction is *not* stable (≈0).

**What it means:**
1. Peers do share the crash on day 0, and more so when the crashing firm is big. So
   market share matters for the **first reaction**.
2. Within a month the damage has mostly **faded**. For the typical crash, nothing the
   rivals depended on was destroyed.
3. *Which industry* it is explains about 10× more than market share or HHI, and that
   industry pattern repeats across decades.

### Part B: eight famous collapses

**Method:**
- Day 0 = the first trading day after the news.
- Peers are measured against the market.
- 20-day = buy-and-hold over days 0–20.
- India uses adjusted Yahoo closes where they exist, and the bhavcopy panel for delisted
  firms.

| Case | Shock | Peer group | Peers over 20 days | Peers up | Reading |
|---|---|---|---|---|---|
| **Satyam 2009** | Fraud at India's #4 IT firm (stock −78% on day 0) | 6 IT rivals | **+12.6%** (t 1.4) | 5 of 6 (Infosys +28%, TCS +18%) | **Replaceable:** rivals took its clients |
| **Jet Airways 2019** | Airline shuts down (−31%) | IndiGo | ~0 on and after the event, but **+14.8% in the 20 days before** | — | **Replaceable**, and priced in early (collapse was expected) |
| **Adani 2023** | Hindenburg report (Adani Ent −56% over 20 days) | 6 Adani-group firms | **−42%** (t −9.6) | 0 of 6 | **Shared fate through ownership and funding** |
| | | 5 sector rivals (UltraTech, Tata Power, NTPC, Power Grid, Pipavav) | **+7.7%** (t 2.0) | **5 of 5** | **The businesses were replaceable**; the group was the weak point |
| **IL&FS 2018** | Unlisted lender defaults; NBFC panic | 9 NBFC / housing-finance lenders | **−14.8%** (t −4.7) | 2 of 9 | Split by **funding model**: wholesale-funded lenders crashed (DHFL −53%, PNB Housing −27%, Edelweiss −26%); strong ones did not (Bajaj Fin −2%, M&M Fin +2%, LIC HF +5%) |
| **DHFL 2019** | Misses bond payments | 8 lenders | −0.8% | 3 of 8 | By then already priced; **no further spread** |
| **Yes Bank 2020** | RBI moratorium (−56%) | 9 private banks | **−19.5%** (t −6.7) | 1 of 9 (HDFC Bank +2.5%) | Shared fate among **weak-deposit** banks (IndusInd −38%, RBL −35%); flight to quality. Note the COVID crash happened at the same time |
| **PG&E 2019** (US) | Wildfire bankruptcy (−52%) | Edison, Sempra | −6.7% | 0 of 2 | Shared **liability / regulatory** risk |
| **SVB 2023** (US) | Bank collapse | 9 regional banks | **−24.5%** (t −4.6) | 0 of 9 | Shared fate: **deposit runs** |

**The pattern across all eight:**
- A firm's death **spreads** when others share a **critical dependency** with it:
  - the same funding market;
  - the same depositors' confidence;
  - the same owner;
  - the same liability or regulator.
- It is **absorbed** when what the firm *produced* can be supplied by rivals: IT
  services, airline seats, cement, power.
- **Size is not the driver.** Satyam was India's #4 IT firm and was absorbed. IL&FS's
  shock hit small housing-finance firms hard.

This sharpens your thesis:

> **A firm's importance comes from what others depend on through it, not from its
> market share.**

**Honest limits of Part B:**
- These are 8 famous cases chosen *after the fact*, so the "shared dependency"
  classification risks story-fitting.
- The fix: write a selection rule and a classification rule *first*, then test a fresh
  set of collapses. This is the next session's main job.

## 5. Is this new? Literature map

Check every entry in Phase 1 before citing it in the paper.

| Area | Key reference | One-line finding | How it relates to your idea |
|---|---|---|---|
| Concentration and returns | Hou & Robinson (2006), *Journal of Finance* | Firms in concentrated industries earn *lower* average returns | Tests your "own low-entropy businesses" paradox directly |
| Rising concentration | Grullon, Larkin & Michaely (2019), *Review of Finance* | Most US industries have become more concentrated since the late 1990s | The "concentration emerges" claim |
| Big firms move the economy | Gabaix (2011), *Econometrica*, "Granular Origins" | Shocks to the largest firms explain a large share of GDP swings | A low-entropy economy means firm shocks don't average out |
| Network position | Acemoglu, Carvalho, Ozdaglar & Tahbaz-Salehi (2012), *Econometrica* | Shocks to central sectors spread through the input–output network | Importance = network position, not size |
| **Replaceability, measured** | **Barrot & Sauvagnat (2016), *QJE*** | When a natural disaster hits a supplier, its customers suffer **only if the input is specific** (hard to replace) | **Closest existing work to your death test.** Read this first |
| Firm death and peers | Lang & Stulz (1992), *Journal of Financial Economics* | Bankruptcies usually hurt rivals (contagion), but in concentrated industries rivals can gain (competitive effect) | The template for Test 3 |
| Systemic importance | Adrian & Brunnermeier (2016), *AER*, "CoVaR" | How much one institution's distress raises system-wide tail risk | The death test for banks, already formalised |
| Co-movement as fragility | Kritzman, Li, Page & Rigobon (2011), *Journal of Portfolio Management* | Sharp rises in the "absorption ratio" preceded drawdowns | Test 2 should test *changes*, not levels |
| Credit contagion vs competition | Jorion & Zhang (2007), *Journal of Financial Economics* | Contagion or competitive effect depends on the type of bankruptcy and the industry | Directly on the death test. Check |
| Supply-chain distress | Hertzel, Li, Officer & Rodgers (2008), *Journal of Financial Economics* | Distress hurts suppliers and customers, not only rivals | The "dependency" channel |
| Intra-industry information transfer | Foster (1981), *Journal of Accounting and Economics* | One firm's earnings news moves its peers | The "information" confound in Part A |
| Customer–supplier links and returns | Cohen & Frazzini (2008), *Journal of Finance* | Customers' news reaches suppliers' prices slowly | Dependency is priced with a lag |
| Product uniqueness from text | Hoberg & Phillips (2016), *Journal of Political Economy* | Measure how similar firms' products are from 10-K text (free data) | A direct measure of "nobody else does this" |
| Skewed stock returns | Bessembinder (2018), *Journal of Financial Economics* | A small share of stocks created all net wealth; most stocks lag T-bills | Explains Test 1 |
| Capability complexity | Hidalgo & Hausmann (2009), *PNAS* | Countries differ by how rare and complex their capabilities are | Capability entropy at country level |
| Efficiency vs resilience | Goerner, Lietaer & Ulanowicz (2009), *Ecological Economics* | Economies, like ecosystems, need a balance between streamlined efficiency and redundancy ("window of vitality") | **Your sustainability bridge.** The same entropy maths, from ecology |
| Calm before the storm | Brunnermeier & Sannikov (2014), *AER* | Risk builds up when measured volatility is low | Explains the Test 2 result |

**Where the gap probably is** (to confirm in Phase 1): a **firm-level, market-implied
replaceability score**, estimated from how peers and customers' prices react to that
firm's own shocks. It would be compared directly with market share and HHI, tested for
what it says about risk and returns, and applied to **India**. India has business groups
and famous natural experiments, and almost no work of this kind.

## 6. The paper: one narrow question

**Working title:** *Market Share Is Not Importance: What Happens to Rivals When a Firm
Dies (US and India)*

**Question (decided 9 Nov):** when a company suffers its own crash, do its rivals gain or
lose, and does its market share explain which?

**Thesis the evidence currently supports:**
- Rivals share the first-day hit (more so for big firms), but the damage lasts only when
  they share a **critical dependency** with the failed firm (funding, deposits,
  ownership, liability).
- Industry identity explains about 10× more than market share or HHI.

**Scope decision for a 2–3 day working paper:**
- **Cut:** the firm-level return-prediction score.
- **Shrink to a "future work" section:** the AI section.
- **Move to an appendix or motivation:** Tests 1–2 (portfolio and market entropy).

**Paper structure:**
1. Framework
2. US large sample (Part A)
3. Case studies (Part B)
4. Pre-registered out-of-sample cases
5. Implications for investors
6. Limitations

*Original, broader question, kept for reference:* does a firm's replaceability carry
information beyond market share and HHI about risk, returns and resilience?

**Design:**
1. **Better peer groups:** GICS sub-industry, or Hoberg–Phillips text-based peers.
2. **Clean shocks:**
   - US: idiosyncratic crashes with industry news removed, true delistings, and natural
     disasters if we get location data.
   - India: Satyam (2009), IL&FS (2018), DHFL (2019), Yes Bank (2020), Adani–Hindenburg
     (2023).
3. **Score:** a rolling, point-in-time "peer sensitivity" for each firm.
4. **Test:** does the score predict future co-movement, drawdowns or returns beyond size
   and HHI?
5. **AI section:** compare the score with what an LLM *thinks* the firm's
   replaceability is (§7).

**Data that would make this a real paper:**
- **WRDS**, which IU very likely subscribes to (ask the Kelley or IU library):
  - CRSP: market caps and true delisting returns.
  - Compustat: revenue, for real HHI.
  - Compustat Segments: who sells to whom.
- **Hoberg–Phillips data library:** free.

With these, two of today's biggest limitations go away: no market caps, and coarse
sectors.

## 7. Making AI equity research better: how it ties in

Where AI equity research is weak today:
1. It **summarises** instead of making falsifiable predictions.
2. It talks about "moats" generically, without measurable claims.
3. Backtests of LLM judgments suffer from **look-ahead bias**: the model already knows
   what happened (Glasserman & Lin 2023).
4. There is no track record or calibration.

**A tangible experiment that uses this framework:**
- Turn the death test into a **structured question set** an LLM answers for each
  company:
  - What disappears if this firm vanishes tomorrow?
  - Who absorbs its customers?
  - How many years would it take to rebuild its capability?
  - Who depends on it?
  - Give a 0–10 replaceability score, with reasons.
- **Validate** the LLM score against the market-implied score from §6.
- The interesting cases are where they **disagree**. Either the AI sees a hidden
  capability the market misprices, or the AI is wrong. Both are publishable.
- **Avoid look-ahead:** score only events after the model's training cutoff, or
  anonymise the firm.

This is the same philosophy as your AI Strategy Builder's 7-gate validation: **AI
proposes, data verifies.**

Related work: Kim, Muhn & Nikolaev (2024), "Financial Statement Analysis with Large
Language Models"; Lopez-Lira & Tang (2023), "Can ChatGPT Forecast Stock Price
Movements?".

## 8. Who to talk to, and with what angle

| Person | Angle that fits them | What to send |
|---|---|---|
| **Kelley finance professor** | Empirical: does replaceability carry information beyond HHI? (Hou–Robinson, Lang–Stulz) | One page plus the Test 3 table, and the question "what would you test first?" |
| **Tsinghua professor at IU** | Capability concentration and "chokepoint" firms: semiconductor export controls are a death test at national scale | The capability-entropy framing (§2) and the India cases |
| **Uncle at NTU (sustainability)** | Efficiency vs resilience: Ulanowicz's ecology maths applied to economies; supply-chain resilience | §1, §4 and the Goerner–Lietaer–Ulanowicz link |

**How to approach them:** don't send a grand theory. Send one page, one result, and one
specific question. Professors respond to "here is what I found, here is what I can't
separate, how would you do it?"

## 9. Next steps

See `NEXT_SESSION_PROMPT.md`. In order:
1. Literature check
2. Sub-industry death test
3. India cases
4. Firm-level score
5. AI death-test design
6. Paper skeleton and one-pager

## Limitations of the pilot (keep this list honest)

- No market caps: "size" is 63-day average dollar volume.
- Delisted stocks are held as cash at their last price. True delisting returns are often
  worse, which slightly flatters concentrated portfolios in Test 1.
- Test 3 uses 11 GICS sectors from the **current** S&P 500 list:
  - delisted firms are not in the sector map, so they are missing as events and as
    peers;
  - whole sectors are treated as "rivals".
- Test 3 uses the raw price file with a $1 floor and a ±50% bad-tick filter, because the
  clean file's 20% filter deletes real crashes. One-day reversals above 25% are dropped
  as bad prints.
- Test 2 uses overlapping 3- and 6-month outcomes (Newey–West corrected) and many tests.
  Treat t ≈ 2 as weak.
- The India co-movement series uses the top 300 by trading value, while the India
  outcome index is the equal-weighted average of all stocks in the panel.
