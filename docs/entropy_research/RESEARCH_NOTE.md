# Entropy, Replaceability and the "Death Test": Research Note

**Started:** 9 November 2026 · **Author:** Mrigay Pathak · **Status:** pilot + death test v2 + 8 case studies done; paper question decided (§6) and red-teamed (§4c); literature checked (§5); out-of-sample test pre-registered, not yet run
**Code:** `scripts/entropy_research.py`, `scripts/death_test.py` · **Outputs:** `results/entropy_research/`, `results/death_test/`
**Pre-registration:** `docs/entropy_research/PREREGISTRATION.md` · **Next session prompt:** `docs/entropy_research/NEXT_SESSION_PROMPT.md`

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
| Importance = shared dependency | **Hypothesis, consistent with all 8 cases; not new for banks** | Not yet tested out of sample. Rules fixed in `PREREGISTRATION.md`; for banks the idea goes back to Aharony & Swary 1983 (§5) |
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

## 4c. Red-team pass (10 Nov): can the paper's question survive a finance professor?

Before the out-of-sample test, the question itself was attacked once. **Verdict: no
objection is fatal, so the question in §6 stays as decided.** Each objection does force a
change in wording or in the design of the test.

### The three strongest objections

**1. "You are measuring a common shock, not the firm's importance." (identification)**

- When rivals fall after a collapse, two different things could be happening:
  - the collapse *damaged* them (contagion);
  - the collapse *revealed* a weakness they already shared (information).
- Price data cannot separate the two. Lang & Stulz (1992) said so, and Helwege & Zhang
  (2016) built a whole paper on the split.
- Worse, "shared dependency" can become circular. If SVB fails because of something every
  regional bank has, then "banks that have it fall" is close to true by definition.
- **Fatal?** No. The question (do rivals gain or lose, and does share explain which?) is
  descriptive and can be answered. What cannot be defended is the causal sentence "a
  firm's importance comes from what others depend on *through it*".
- **What changes:**
  - The claim becomes a *prediction* claim: the kind of link rivals have to the failed
    firm predicts the sign of their return; market share does not.
  - The test drops collapses whose trigger hit the whole industry at once (a new law, a
    pandemic). Only firm-specific triggers count.
  - The cleanest evidence is a contrast inside one event: the same collapse, group
    affiliates against same-industry rivals.

**2. "'Shared dependency' is just another word for 'bank'." (confound)**

- Of the six peer groups read as "shared dependency" in §4b, four are lenders (IL&FS,
  DHFL, Yes Bank, SVB). All three read as "replaceable" (Satyam's rivals, Jet's rival,
  Adani's sector rivals) are non-financial.
- Bank contagion has been documented for forty years: Aharony & Swary (1983), Iyer &
  Peydró (2011), Choi, Goldsmith-Pinkham & Yorulmazer (2023) for SVB.
- If the label only works because it marks financial firms, the paper adds nothing to
  "banks are special".
- **Fatal?** No, but this objection decides whether the hypothesis is new.
- **What changes:** the pre-registration splits every result into financial and
  non-financial, tests the label *inside* each half, and runs a horse race against the
  dumb rule "financial firm ⇒ rivals fall".

**3. "Your 'market share' is not market share, and nothing in your sample died."
(measurement and sample)**

- "Share" here is a firm's share of *trading value* among S&P 500 members in its
  sub-industry. It ignores revenue, private firms, foreign firms and smaller listed firms.
- Ali, Klasa & Yeung (2009) show that even concentration built from all listed firms'
  sales has a correlation of only 13% with the Census measure. A noisy variable will
  always "explain little".
- Lang & Stulz (1992) found that concentration *does* flip the sign (rivals gain in
  concentrated, low-debt industries). Contradicting a classic needs a better measure than
  ours.
- Part A has 266 crashes at firms that are still in the index today. None was followed by
  a delisting within 60 days, and 148 of the 266 are in Health Care and IT, which mostly
  means earnings news. That is not "death".
- "Industry explains 10× more" compares two noisy variables with twenty dummies, and HHI
  hardly varies inside a sub-industry.
- **Fatal?** No, but the claims must shrink.
- **What changes:**
  - Say "we find no evidence that share, as we can measure it, explains the 20-day
    reaction", not "share does not matter".
  - Use "collapses", not "dies", for Part A.
  - The out-of-sample test also records each failed firm's industry rank as reported in
    the news, so share is tested with a second, independent measure.
  - Phase 3 adds delisted firms.

**Smaller points that also shaped the pre-registration:**
- The person or model writing the labels already knows how the famous cases ended. The
  rule is therefore a checklist of facts visible on day 0, and a blind second coder
  re-labels anonymised descriptions.
- Collapses cluster in crashes (2008, March 2020), when bank stocks fall more than the
  market anyway. Results are reported with and without a beta adjustment and with crisis
  windows removed.
- With perhaps 30–60 events the test can only detect a large difference (about 10
  percentage points). A null result will not rule out a small effect.

### Sharpened framing (question unchanged)

> **The sign of the rival reaction is predicted by the kind of link rivals have to the
> failed firm, not by its market share.** Rivals who only sell the same product are
> unharmed or gain. Rivals who share its funding market, its legal liability or its owner
> fall.

- This is a claim about *prediction from facts known on day 0*. It does not say whether
  the collapse caused the damage or revealed it. For an investor asking "what happens to
  the others?", the answer is the same either way.
- Suggested title change, one word: *…When a Firm **Collapses***. Part A contains no
  deaths.

## 5. Is this new? Literature map

**Checked 10 November 2026** by web search (publisher, RePEc, NBER and SSRN listings).
Full texts could not be opened in that session, so findings are from abstracts. Entries
marked † still need a look at the paper itself before they are quoted.

### References from the pilot (corrected)

| Area | Reference | Finding, as the abstract states it | How it relates |
|---|---|---|---|
| Concentration and returns | Hou & Robinson (2006), "Industry Concentration and Average Stock Returns", *Journal of Finance* 61(4), 1927–1956 | Firms in more concentrated industries earn lower returns, after controlling for size, book-to-market and momentum | Tests the "own low-entropy businesses" paradox |
| Rising concentration | Grullon, Larkin & Michaely (2019), "Are US Industries Becoming More Concentrated?", *Review of Finance* 23(4), 697–743 | More than three-quarters of US industries became more concentrated over two decades | The "concentration emerges" claim |
| Big firms move the economy | Gabaix (2011), "The Granular Origins of Aggregate Fluctuations", *Econometrica* 79(3), 733–772 | Shocks to the 100 largest US firms explain **about one-third** of output swings (was: "a large share") | A low-entropy economy means firm shocks don't average out |
| Network position | Acemoglu, Carvalho, Ozdaglar & Tahbaz-Salehi (2012), "The Network Origins of Aggregate Fluctuations", *Econometrica* 80(5), 1977–2016 | Sector shocks can add up to aggregate swings when a few sectors supply many others (strong asymmetry in the input–output network) | Importance = network position, not size |
| **Replaceability, measured** | **Barrot & Sauvagnat (2016), "Input Specificity and the Propagation of Idiosyncratic Shocks in Production Networks", *QJE* 131(3), 1543–1592** | A natural disaster at a supplier causes large losses at its customers, **especially when** the input is specific (was: "only if") † | Closest existing work to the death test |
| Firm death and peers | Lang & Stulz (1992), "Contagion and Competitive Intra-Industry Effects of Bankruptcy Announcements", *JFE* 32(1), 45–60 | A bankruptcy announcement lowers rivals' value by about 1% on average. The drop is larger in highly indebted industries. Rivals **gain** only in industries that are both highly concentrated **and** low in debt (the old entry left out debt) | The template for the death test, and the classic that says concentration *does* matter |
| Systemic importance | Adrian & Brunnermeier (2016), "CoVaR", *AER* 106(7), 1705–1741 | Measures how much the system's tail risk rises when one institution is in distress | The death test for banks, already formalised |
| Co-movement as fragility | Kritzman, Li, Page & Rigobon (2011), "Principal Components as a Measure of Systemic Risk", *Journal of Portfolio Management* 37(4), 112–126 | The "absorption ratio" (share of variance explained by a few factors) is proposed as an early-warning signal; the authors report that its spikes preceded most large US drawdowns † | Test 2 should test *changes*, not levels |
| Credit contagion vs competition | Jorion & Zhang (2007), "Good and Bad Credit Contagion: Evidence from Credit Default Swaps", *JFE* 84(3), 860–883 | Chapter 11 filings (reorganisation) spread to rivals; Chapter 7 filings (liquidation) help rivals. Measured mainly in CDS spreads (the old entry said "type of bankruptcy and the industry") | The firm that survives in bankruptcy stays a competitor; the one that is liquidated does not |
| Supply-chain distress | Hertzel, Li, Officer & Rodgers (2008), "Inter-Firm Linkages and the Wealth Effects of Financial Distress along the Supply Chain", *JFE* 87(2), 374–387 | Distress spills beyond rivals to suppliers and customers, mainly when the filing firm's industry is also hurt † | The "dependency" channel outside the industry |
| Information transfer | Foster (1981), "Intra-Industry Information Transfers Associated with Earnings Releases", *Journal of Accounting and Economics* 3(3), 201–232 | One firm's earnings release moves the prices of other firms in its industry | The "information" confound in Part A |
| Customer–supplier links | Cohen & Frazzini (2008), "Economic Links and Predictable Returns", *Journal of Finance* 63(4), 1977–2011 | News about a customer reaches its supplier's price slowly | Dependency is priced with a lag |
| Product uniqueness from text | Hoberg & Phillips (2016), "Text-Based Network Industries and Endogenous Product Differentiation", *JPE* 124(5), 1423–1465 | Builds industries and product similarity from 10-K text (the data are posted free on the authors' site) | A direct measure of "nobody else does this" |
| Skewed stock returns | Bessembinder (2018), "Do Stocks Outperform Treasury Bills?", *JFE* 129(3), 440–457 | The best 4% of stocks account for all US net wealth creation since 1926; only 42.6% of stocks beat one-month T-bills | Explains Test 1 |
| Capability complexity | Hidalgo & Hausmann (2009), "The Building Blocks of Economic Complexity", *PNAS* 106(26), 10570–10575 | Measures a country's complexity from how diverse and how rare its exports are; capabilities are inferred, not observed | Capability entropy at country level |
| Efficiency vs resilience | Goerner, Lietaer & Ulanowicz (2009), "Quantifying Economic Sustainability: Implications for Free-Enterprise Theory, Policy and Practice", *Ecological Economics* 69(1), 76–81 | Sustainable systems need a balance of efficiency and resilience (Ulanowicz's "window of vitality") † | The sustainability bridge |
| Calm before the storm | Brunnermeier & Sannikov (2014), "A Macroeconomic Model with a Financial Sector", *AER* 104(2), 379–421 | The "volatility paradox": low outside risk invites more borrowing, so the system's own risk stays high | Explains the Test 2 result |

### Added in Phase 1: contagion through shared dependencies

| Channel | Reference | Finding | What it means for this paper |
|---|---|---|---|
| Bank failures: fraud vs common problems | Aharony & Swary (1983), "Contagion Effects of Bank Failures: Evidence from Capital Markets", *Journal of Business* 56(3), 305–322 | When a large bank fails for reasons specific to it, such as fraud, other banks' shares do **not** fall | **The closest ancestor of our hypothesis**, for banks only, 43 years ago |
| Counterparty vs information contagion | Helwege & Zhang (2016), "Financial Firm Bankruptcy and Contagion", *Review of Finance* 20(4), 1321–1362 | Both channels exist for US financial firms 1980–2010, and neither is very large. Information spillovers hit rivals in the same place or business line | Our "dependency" label mixes these two; say so |
| Interbank exposure | Iyer & Peydró (2011), "Interbank Contagion at Work: Evidence from a Natural Experiment", *Review of Financial Studies* 24(4), 1337–1377 | After a large bank failure in India, banks with more exposure to it lost more deposits, more so if they were weak | Dependency measured with real exposures, in India |
| Depositor runs | Iyer & Puri (2012), "Understanding Bank Runs: The Importance of Depositor-Bank Relationships and Networks", *AER* 102(4), 1414–1445 | In a run on a solvent bank in Gujarat after a fraud at another bank, uninsured and newer depositors ran first | The "same depositors' confidence" channel |
| SVB | Choi, Goldsmith-Pinkham & Yorulmazer (2023), "Contagion Effects of the Silicon Valley Bank Run", NBER Working Paper 31772 | Banks relying more on uninsured deposits fell more after SVB | Our SVB case, done properly, with a measured dependency |
| Collateral | Benmelech & Bergman (2011), "Bankruptcy and the Collateral Channel", *Journal of Finance* 66(2), 337–378 | An airline's bankruptcy raises other airlines' borrowing costs, more where their aircraft overlap | A shared dependency in a **non-financial** industry. It cuts against our "airline seats are replaceable" reading of Jet Airways |
| Accounting news | Gleason, Jenkins & Johnson (2008), "The Contagion Effects of Accounting Restatements", *The Accounting Review* 83(1), 83–110 | A restatement lowers the share prices of other firms in the industry, more for those with aggressive accounting | **A warning for our rule:** fraud news can hurt rivals. Satyam's rivals gaining is not guaranteed to repeat |
| Business groups: tunnelling | Bertrand, Mehta & Mullainathan (2002), "Ferreting Out Tunneling: An Application to Indian Business Groups", *QJE* 117(1), 121–148 | Owners of Indian groups move profits between group firms | Why a shared owner is a real dependency |
| Business groups: support | Gopalan, Nanda & Seru (2007), "Affiliated Firms and Financial Support: Evidence from Indian Business Groups", *JFE* 86(3), 759–795 | Groups lend to weak member firms, plausibly to stop a default from spilling onto the rest of the group | Group spillovers in India are an established idea |
| Group spillovers in prices | Korean chaebol studies (credit downgrades, forced exits, crash risk); found via search, not yet read † | Bad news at one affiliate lowers the value of the others | The "owner" channel has been tested in Korea; I found no Indian equivalent |
| Measuring concentration | Ali, Klasa & Yeung (2009), "The Limitations of Industry Concentration Measures Constructed with Compustat Data", *Review of Financial Studies* 22(10), 3839–3871 | Concentration built from listed firms only has a correlation of 13% with the Census measure | Our trading-value share is weaker still (objection 3 in §4c) |

**Indian studies of IL&FS, Yes Bank and Adani.** What the searches found:
- **Adani–Hindenburg:** several event studies, almost all of the Adani companies
  themselves; one or two add bank or sector indices. None compares group affiliates with
  same-industry rivals for the same event.
- **IL&FS:** case studies and policy papers that describe the funding squeeze on NBFCs and
  housing-finance companies. No study that sorts lenders by funding model and measures
  abnormal returns.
- **Yes Bank:** case studies (including the Yale *Journal of Financial Crises*) and press
  accounts of the falls at IndusInd and RBL. No formal event study of peer banks.
- These were web searches, not a database search (Scopus, SSRN full text). "I did not find
  it" is weaker than "it does not exist".

### Is this new? The honest paragraph

Most of the pieces exist. Rivals lose about 1% on average when a firm goes bankrupt, and
the sign depends on industry structure (Lang & Stulz 1992; Jorion & Zhang 2007). Bank
failures spread through deposits and exposures, and do not spread when the cause is
fraud at one bank (Aharony & Swary 1983; Iyer & Peydró 2011; Choi et al. 2023). Distress
in a business group threatens the other members (Gopalan, Nanda & Seru 2007). So the
*channels* in this paper are not new, and for banks the core idea is forty years old.
What this paper can add is narrower:

1. **One rule across industries.** A single checklist, applied on day 0, that says for
   any collapse whether rivals should fall. It covers funding, liability and ownership
   together, and it is set against the textbook alternative, market share.
2. **A test that could fail.** The cases and labels are fixed in git before any rival
   return is computed. Event studies in this literature are almost never pre-registered.
3. **India, with a contrast inside each event.** Group affiliates against same-industry
   rivals of the same failed firm. I found no Indian study that does this.

The paper is therefore a **synthesis and a clean test**, not a new mechanism. That is a
reasonable claim for a working paper. If the test shows the rule works only for banks,
the honest headline becomes "Aharony & Swary's result still holds, in India too".

## 6. The paper: one narrow question

**Working title:** *Market Share Is Not Importance: What Happens to Rivals When a Firm
Dies (US and India)*

**Question (decided 9 Nov):** when a company suffers its own crash, do its rivals gain or
lose, and does its market share explain which?

**Thesis the evidence currently supports** (wording tightened after the red-team pass,
§4c):
- Rivals share the first-day hit (more so for big firms), but the damage lasts only when
  they share a **critical dependency** with the failed firm (funding, deposits,
  ownership, liability).
- This is a claim about *prediction*: the kind of link predicts the sign of the rivals'
  return. It does not separate "the collapse damaged them" from "the collapse revealed a
  weakness they shared".
- Market share, as we can measure it (share of trading value among index members), and
  HHI explain under 1% of the first-day reaction and nothing at 20 days. Stable
  differences between industries explain about ten times more. The measure is crude, so
  this is "no evidence that share matters", not proof that it does not.

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

Related work (checked 10 Nov; see §5 for how):
- Glasserman & Lin (2024), "Assessing Look-Ahead Bias in Stock Return Predictions
  Generated by GPT Sentiment Analysis", *Journal of Financial Data Science* 6(1), 25–42.
  The 2023 date above is the preprint. The finding is subtler than "look-ahead inflates
  backtests": hiding company names removes look-ahead but also removes a "distraction"
  effect, and the two pull in opposite directions.
- Kim, Muhn & Nikolaev (2024), "Financial Statement Analysis with Large Language
  Models", working paper (Chicago Booth). Not published in a journal as far as the
  search could tell; re-check its status before citing.
- Lopez-Lira & Tang, "Can ChatGPT Forecast Stock Price Movements? Return Predictability
  and Large Language Models". A RePEc listing shows it as published in the *Journal of
  Financial Economics* (vol. 184, 2026); confirm on the journal's site before citing.

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

See `NEXT_SESSION_PROMPT.md` for the phases. Status on 10 November 2026:
1. ~~Literature check~~ done (§5).
2. ~~Red-team the question~~ done (§4c).
3. **Out-of-sample test, Stage 1:** rules committed in `PREREGISTRATION.md`.
4. **Stage 2 (next):** run the screen on the price panels (the failed firms' own returns
   only), write up each shock, label it, and commit the case list. This needs
   `data_processed/`, which exists only on Mrigay's Mac.
5. **Stage 3:** only then compute rival returns and run the test.
6. Then robustness of Part A, figures, and the paper.

Also still open from the data ground rules: switch `death_test.py`'s bhavcopy fallback to
`nse_survivorship_free_adj.parquet` and re-run it. Not done on 10 November because the
price files were not available in that session.

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
