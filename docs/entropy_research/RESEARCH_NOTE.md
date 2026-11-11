# Entropy, Replaceability and the "Death Test": Research Note

**Started:** 9 November 2026 · **Author:** Mrigay Pathak · **Status:** red-team pass (§6a) and literature check (§5) done 11 Nov; pre-registered out-of-sample test next
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

**Data update (11 Nov):** the India fallback now uses the corporate-action-corrected panel
(`nse_survivorship_free_adj.parquet`). The eight case numbers moved by at most 0.2 pp, only
through the market benchmark, and no reading changed. Part A is unchanged (266 events).

**Honest limits of Part B:**
- These are 8 famous cases chosen *after the fact*, so the "shared dependency"
  classification risks story-fitting.
- The fix: write a selection rule and a classification rule *first*, then test a fresh
  set of collapses. This is the next session's main job.

## 4c. Robustness of Part A (11 Nov, Phase 3)

**Code:** `scripts/death_test_robustness.py` · **Output:** `results/death_test/robustness.csv`

Each row is a variant of the US event study. "CI" is a 95% confidence interval from a
bootstrap that resamples event *dates*, so crashes on the same day are not treated as
independent. "Clustered t" also groups by date.

| Variant | Events | Day 0 (clustered t) | Days 0–20 [95% CI] | Large − small share, day 0 [CI] |
|---|---|---|---|---|
| Baseline (sub-industry, −15%) | 266 | **−1.20%** (−6.8) | −0.29% [−1.24, +0.62] | **−1.00 pp** [−1.79, −0.26] |
| Crash threshold −10% | 830 | −0.72% (−7.1) | −0.49% [−1.01, +0.01] | −0.62 pp [−0.97, −0.28] |
| Crash threshold −20% | 117 | −1.65% (−7.4) | −0.87% [−2.48, +0.81] | −1.03 pp [−1.87, −0.13] |
| Excluding 2008–09 and 2020 | 199 | −1.20% (−9.2) | −0.73% [−1.60, +0.12] | −0.92 pp [−1.57, −0.29] |
| **Excluding Financials** | 231 | **−0.90%** (−6.4) | −0.50% [−1.32, +0.28] | −0.69 pp [−1.26, −0.11] |
| Sector-level peers | 513 | −0.50% (−7.1) | −0.22% [−0.67, +0.23] | −0.15 pp [−0.51, +0.18] |

**Does market share explain the reaction? A fairer race.** In-sample adjusted R² flatters
models with many dummies, so we also report a 5-fold cross-validated R²: fit on 80% of
events, predict the other 20%, and repeat. Negative means worse than predicting the
average.

| Day-0 reaction | In-sample adj. R²: share + HHI | In-sample: sub-industry | **Out-of-sample R²: share + HHI** | **Out-of-sample: sub-industry** |
|---|---|---|---|---|
| Baseline (266 events) | 0.8% | 14.2% | −0.6% | **−1.3%** |
| Threshold −10% (830) | 0.1% | 12.2% | −0.5% | **+7.2%** |
| Threshold −20% (117) | 0.9% | 18.2% | −3.0% | **+6.1%** |
| Excluding Financials | 0.1% | 6.5% | −1.5% | −2.6% |

Within a sub-industry, the share coefficient on day 0 is negative but not significant
(baseline clustered t = −1.8).

**What this means, in plain words:**
1. **The day-0 hit is real and robust.** Rivals fall on the crash day in every variant,
   including without Financials (−0.90%) and without the 2008–09 and 2020 crises. So
   day-0 contagion is not just a banking story.
2. **Large firms do drag rivals more on day 0.** The gap is about 1 percentage point and
   significant in every sub-industry variant. Market share is not irrelevant; it sizes
   the *first* reaction.
3. **The 20-day effect is small, not zero.** The baseline interval [−1.2%, +0.6%] rules
   out a large lasting loss. The bigger −10% sample gives −0.5% (t ≈ −1.9), which hints
   at a small lasting drag. The paper should say "small or zero", not "fully absorbed".
4. **Correction to our own headline.** "Industry explains 10× more than share" came from
   *in-sample* R². Out of sample, in the baseline sample, *neither* predicts: the 14% was
   mostly over-fitting. With more events (−10% or −20% thresholds), sub-industry
   identity predicts about 6–7% out of sample, and share never predicts anything. The
   honest claim: **industry identity carries some out-of-sample information about the
   rival reaction; market share carries none.**
5. **Peer definition matters.** Whole-sector peers dilute the effect (−0.50%) and the
   share gap disappears. The narrower the peer group, the clearer the spillover.

**Adding delisted firms (yfinance), honestly reported.** 171 tickers that were once in
the S&P 500 are missing from the current sub-industry file. yfinance returned an industry
for 131, but:
- these are mostly firms that left the index and still trade, labelled with Yahoo's
  industry names rather than GICS;
- some tickers have been reused by other companies (MMI is now Marcus & Millichap, not
  Motorola Mobility);
- the 40 with no data include exactly the true deaths: Sears, RadioShack, Countrywide,
  Tellabs.

So this route cannot bring true deaths into Part A, and Part A is unchanged. The fix is
CRSP/Compustat historical industry codes (WRDS). Lookup:
`results/death_test/yfinance_delisted_lookup.csv`.

## 4d. The pre-registered out-of-sample test (11 Nov, Phase 2 results)

**Rules:** `PREREGISTRATION.md` §1–§10, committed before any rival return was computed.
**Full results tables:** `PREREGISTRATION.md` §11. **Code:** `scripts/death_test_oos.py run`
(as committed) and `scripts/death_test_oos_sensitivity.py` (the one check that is *not*
pre-registered). **Outputs:** `results/death_test_oos/`.

**What we did.** We took 40 collapses we had never studied, chosen by a fixed rule. For
each, we labelled the case from the day-0 news alone: "shared dependency" (SD: the rivals
share the failed firm's funding market, depositors or legal liability) or
"output-replaceable" (OR: they don't). Only then did we compute how the rivals' stocks did
over the next 20 trading days. The registered sample is 26 cases; the full population,
after deviation D1, is 40.

**What came out, in plain words.**

1. **The rule finds very few shared-dependency collapses.** Only 4 of 40 (Citi, Bank of
   America, Lakshmi Vilas Bank, DHFL 2019). Most firms that collapse on their own news do
   so for their own reasons: fraud, governance, their own losses.
2. **Where the rule says "shared dependency", rivals did fall, but mostly in 2008–09.**
   Rivals of Citi fell 13.5% against the market and rivals of BofA 22.6%. The two Indian
   SD cases barely moved: −0.6% and −0.4%. Without the 2008–09 and 2020 crisis months, SD
   rivals did slightly *better* than OR rivals (−0.5% vs −1.7%). So the SD effect we see
   is the 2008 bank crisis, not a general law.
3. **H1 cannot be tested.** The rule fixed in advance needs at least 5 SD cases, and both
   versions have fewer. The verdict is **"too few cases to test"**. For description only:
   SD minus OR is −14.3 pp (registered) and −5.9 pp (full, permutation *p* 0.15).
4. **The "replaceable rivals do not lose" half of the rule failed.** Rivals of OR firms
   fell in 55% of cases, by about 3.5% on average (median −0.8%). The hit rate was 44–46%,
   no better than a coin. Under the pre-registered T3 reading, the rule works neither
   inside nor outside finance: **"the rule fails out of sample."** That part of our Part B
   story (Satyam's rivals gained) does not generalise. Most rivals of a failed firm drift
   a little lower, rather than gaining.
5. **Market share does not predict the rival reaction.** In the regression of the outcome
   on the label and share, share has *t* ≈ −1 in both versions, and the Spearman
   correlation is −0.1. This agrees with §4c: share carries no out-of-sample information.
   The share result is the robust finding.
6. **Day-0 contagion again.** On the collapse day, rivals fell in about 3 of 4 cases
   whatever the label, as in the large sample.
7. **Business groups.** All 3 Indian group sets fell (mean −28%), as predicted. With 3
   sets, though, the best possible *p* is 0.125.

**The one check that is not pre-registered.** Some cases overlap: Regions, Fifth Third and
Huntington failed within two days of each other and are each other's rivals. Dropping the
later case of each such pair (Fifth Third, Huntington, DHFL 2019) widens the full-sample
gap to −10.2 pp (*p* 0.050). This check was chosen after the results were seen and rests on
3 SD cases. It does not change any verdict, and the paper must not use it as support.

**What this does to the thesis.**
- **Held up:** market share does not predict how rivals fare (in the large sample and out
  of sample). Rivals share the first-day hit. Group firms fall together.
- **Not established:** that a shared dependency, read from the news, predicts which rivals
  lose. It is promising (the two large bank rescues), but rare, and untestable with 4
  cases.
- **Failed:** that rivals of a "replaceable" firm hold up. On average, they drift down a
  little.

**Honest framing for the paper:** "Market share does not predict how rivals fare. Industry
identity predicts a little. A dependency rule applied from the news is promising but not
established out of sample, and its 'replaceable rivals are safe' half failed."

## 5. Is this new? Literature map (verified 11 Nov 2026)

Every entry below was checked against a journal page or a reliable index (RePEc/IDEAS,
NBER, arXiv). Full notes are in the Phase 1 report summarised in §5c. Two items are
marked **check before citing**: read the paper itself before quoting them.

### 5a. The original table, corrected

| Area | Reference (verified) | What it actually finds | How it relates |
|---|---|---|---|
| Concentration and returns | Hou & Robinson (2006), "Industry Concentration and Average Stock Returns", *J. Finance* 61(4), 1927–56 | Firms in *less* concentrated industries earn higher average returns. Later challenged by Ali, Klasa & Yeung (2009), so cite it as contested | The "own low-entropy businesses" paradox |
| Rising concentration | Grullon, Larkin & Michaely (2019), "Are US Industries Becoming More Concentrated?", *Review of Finance* 23(4), 697–743 | HHI rose in over 75% of US industries over about two decades, with higher margins | "Concentration emerges" |
| Big firms move the economy | Gabaix (2011), "The Granular Origins of Aggregate Fluctuations", *Econometrica* 79(3), 733–72 | Idiosyncratic shocks to the 100 largest US firms explain about a third of output swings | Firm shocks don't average out |
| Network position | Acemoglu, Carvalho, Ozdaglar & Tahbaz-Salehi (2012), "The Network Origins of Aggregate Fluctuations", *Econometrica* 80(5), 1977–2016 | Shocks to central supplier sectors can create aggregate fluctuations | Importance = network position, not size |
| Input specificity | Barrot & Sauvagnat (2016), "Input Specificity and the Propagation of Idiosyncratic Shocks in Production Networks", *QJE* 131(3), 1543–92 | When a disaster hits a supplier, its customers lose output and value **only when the input is specific**. "Replaceability" is our word, not theirs | Closest design to the death test |
| Firm death and rivals | Lang & Stulz (1992), "Contagion and Competitive Intra-Industry Effects of Bankruptcy Announcements", *JFE* 32(1), 45–60 | Rivals lose about 1% on average (contagion). Rivals gain only in **concentrated, low-leverage** industries. **Check before citing** the subsample number (+2.2% in one secondary source) | The template. They explain the sign by industry concentration and leverage, not by the failed firm's share |
| Systemic importance | Adrian & Brunnermeier (2016), "CoVaR", *AER* 106(7), 1705–41 | The system's value-at-risk conditional on one institution being in distress | The death test for banks, formalised |
| Co-movement | Kritzman, Li, Page & Rigobon (2011), "Principal Components as a Measure of Systemic Risk", *J. Portfolio Mgmt* 37(4), 112–26 | A high or rising "absorption ratio" signals a tightly coupled, fragile market | Test 2 should test changes |
| Credit contagion vs competition | Jorion & Zhang (2007), "Good and Bad Credit Contagion: Evidence from Credit Default Swaps", *JFE* 84(3), 860–83 | Using CDS spreads: **Chapter 11** filings bring contagion, **Chapter 7** liquidations bring a competitive effect | "The type of death decides the sign", not size |
| Supply-chain distress | Hertzel, Li, Officer & Rodgers (2008), "Inter-firm Linkages and the Wealth Effects of Financial Distress along the Supply Chain", *JFE* 87(2), 374–87 | A bankrupt firm's suppliers lose value, starting before the filing, mostly where goods are specialised | A dependency result |
| Information transfer | Foster (1981), "Intra-industry Information Transfers Associated with Earnings Releases", *J. Accounting & Economics* 3(3), 201–32 | One firm's earnings release moves some of its industry peers | The information confound |
| Customer–supplier links | Cohen & Frazzini (2008), "Economic Links and Predictable Returns", *J. Finance* 63(4), 1977–2011 | Customers' news reaches suppliers' prices with a lag | Dependency priced slowly |
| Text-based peers | Hoberg & Phillips (2016), "Text-Based Network Industries and Endogenous Product Differentiation", *JPE* 124(5), 1423–65 | Firm-specific competitor sets built from 10-K product text | Better peer groups (future work) |
| Skewed returns | Bessembinder (2018), "Do Stocks Outperform Treasury Bills?", *JFE* 129(3), 440–57 | The best 4% of US listed firms explain all net wealth creation since 1926; about 57% of stocks lag T-bills | Explains Test 1 |
| Economic complexity | Hidalgo & Hausmann (2009), "The Building Blocks of Economic Complexity", *PNAS* 106(26), 10570–75 | Measures a country's complexity from the diversity and ubiquity of its exports | Capability concentration (loose link) |
| Efficiency vs resilience | Goerner, Lietaer & Ulanowicz (2009), "Quantifying Economic Sustainability", *Ecological Economics* 69(1), 76–81 | A network measure that balances efficiency and resilience (their phrase is "window of **viability**") | Sustainability bridge; cite once |
| Volatility paradox | Brunnermeier & Sannikov (2014), "A Macroeconomic Model with a Financial Sector", *AER* 104(2), 379–421 | Risk builds up in low-volatility times | Explains Test 2 |
| LLM look-ahead | Glasserman & Lin (2023), arXiv 2309.17322 (working paper) | Look-ahead bias matters less than a "distraction" effect; anonymising helps. Our earlier summary overstated it | AI section |
| LLM statement analysis | Kim, Muhn & Nikolaev (2024), arXiv 2407.17866 / Chicago BFI WP (working paper) | GPT-4 on anonymised statements predicts earnings direction better than the median analyst | AI section |
| LLM return prediction | Lopez-Lira & Tang (2023), SSRN 4412788 (working paper, many versions) | LLM headline scores predict next-day returns | AI section |

### 5b. New references the paper needs

**Contagion through shared dependencies**
- Aharony & Swary (1983), "Contagion Effects of Bank Failures: Evidence from Capital
  Markets", *J. Business* 56(3), 305–22. Large US bank failures: **when the failure comes
  from bank-specific problems such as fraud, other banks are not hit.** This is the
  closest old result to our rule (a fraud does not spread; a shared weakness does).
- Kaminsky & Reinhart (2000), "On Crises, Contagion, and Confusion", *J. Int'l Economics*
  51(1), 145–68. Crises spread across countries through **common bank lenders**. The
  "common creditor" idea, for countries.
- Jorion & Zhang (2009), "Credit Contagion from Counterparty Risk", *J. Finance* 64(5),
  2053–87. Chapter 11 filings hurt the failed firm's **creditors**, more for large
  exposures.
- Helwege & Zhang (2016), "Financial Firm Bankruptcy and Contagion", *Review of Finance*
  20(4), 1321–62. When financial firms fail, **information contagion** hits rivals in the
  same lines of business; counterparty contagion is modest.
- Hertzel & Officer (2012), "Industry Contagion in Loan Spreads", *JFE* 103(3), 493–506.
  Rivals' loan spreads rise around a bankruptcy, less in concentrated industries.
- Benmelech, Bergman, Milanez & Mukharlyamov (2019), "The Agglomeration of Bankruptcy",
  *RFS* 32(7), 2541–86. A chain's liquidation closes *neighbouring* stores of other firms:
  a shared-location dependency.
- Baranchuk & Rebello (2018), "Spillovers from Good-News and Other Bankruptcies", *JFE*
  129(2), 228–49. When a filing is good news for rivals and when it is not.
- Diamond & Dybvig (1983), *JPE* 91(3), 401–19 (bank runs); Iyer & Puri (2012),
  "Understanding Bank Runs", *AER* 102(4), 1414–45 (an Indian co-operative bank run
  spread through depositor networks); Iyer & Peydró (2011), "Interbank Contagion at
  Work", *RFS* 24(4), 1337–77 (banks with more interbank exposure to a failed Indian bank
  lost more deposits).

**Business groups (the "owner" channel)**
- Bertrand, Mehta & Mullainathan (2002), "Ferreting Out Tunneling", *QJE* 117(1),
  121–48. Resources move between Indian group firms (tunnelling).
- Gopalan, Nanda & Seru (2007), "Affiliated Firms and Financial Support", *JFE* 86(3),
  759–95. Intragroup loans flow to weaker affiliates, so group firms are financially
  linked. **Check before citing** any claim that one group firm's default hurts the
  others; the check could not confirm it.
- Khanna & Palepu (2000), *J. Finance* 55(2), 867–91; Khanna & Yafeh (2007), "Business
  Groups in Emerging Markets: Paragons or Parasites?", *J. Economic Literature* 45(2),
  331–72.

**Rival reactions and industry structure**
- Ferris, Jayaraman & Makhija (1997), *J. Corporate Finance* 3(4), 367–95: rivals fall on
  average; Cheng & McDonald (1996), *Financial Review* 31(4), 783–807: airline rivals
  gain, railroad rivals lose; Arthurs et al. (2017), *Academy of Management
  Proceedings*: more technology overlap with the failed firm means more contagion.

**India episodes**
- Adani: Ganguly, Mishra & Platt (2025), *Applied Economics Letters*. Indian indices fell
  after the Hindenburg report, firms with pledged shares fell more, and politically
  connected firms rose. This is the only published Indian spillover event study found.
- IL&FS / NBFCs: Anshuman & Sharma (2020), "Financial Fragility in Retail-NBFCs", IIM
  Bangalore WP 604. NBFCs depended on short-term money from liquid debt mutual funds,
  which is exactly our shared-funding channel.
- Yes Bank: Agrawal (2025), working paper (AEA 2026 programme). The rescue raised credit
  risk at other *private* banks relative to state-owned ones.
- Satyam: no study of rival IT firms' returns was found (Chakrabarti & Sarkar 2010 and
  Sane 2017 study governance and investor behaviour instead). Our Satyam result is new.

### 5c. Is this new? (honest answer)

**What already exists.**
- The question "do rivals gain or lose when a firm fails?" is 30 years old (Lang & Stulz
  1992; Ferris et al. 1997; Jorion & Zhang 2007).
- The average answer, "rivals usually lose", is well established.
- Several papers show that *what kind of event* it is matters: fraud versus a shared
  weakness at banks (Aharony & Swary 1983), Chapter 7 versus Chapter 11 (Jorion & Zhang
  2007), information versus counterparty links (Helwege & Zhang 2016).
- Bank-run and common-creditor contagion are well documented, including in India
  (Iyer & Peydró 2011; Iyer & Puri 2012).

**What this paper adds.**
1. **A direct test of market share.** The check found no paper that regresses rival
   reactions on the *failed firm's own* share and compares it with industry identity.
   Lang & Stulz use industry concentration and leverage instead.
2. **One rule across finance and non-finance.** Shared funding, depositors, ownership
   and liability are treated as one idea ("what rivals share with the failed firm"),
   instead of separate bank, supply-chain and group literatures.
3. **A pre-registered out-of-sample test.** No pre-registered corporate-finance event
   study was found (with the qualifier "none found in our search").
4. **India.** Rival-level evidence for Satyam, IL&FS, DHFL, Yes Bank and Adani is thin
   or missing. Only Adani has a published spillover study, and it is about indices and
   political connections, not rivals versus group firms.

**What it does not add.** The idea that bank failures spread is not new, and the
paper must say so. The contribution is the comparison with market share, the single
rule, the pre-registration and the Indian evidence.

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

### 6a. Red-team pass (11 Nov, before the literature check)

The one time the question itself is allowed to be challenged. These are the three
strongest objections a finance professor would raise, and whether any is fatal.

**Objection 1: "You are measuring information, not importance."**
- A rival's price falls when a crash *tells investors something* about the rival's own
  cash flows (Foster 1981; Lang & Stulz 1992).
- The regional banks did not *depend on* SVB. SVB's collapse showed that they had the
  same weakness: uninsured deposits and unrealised bond losses. PG&E's bankruptcy showed
  that California's wildfire-liability rule also applied to Edison.
- So "shared dependency" could just mean "the shock revealed a common exposure". Put
  that way, "rivals fall when the shock hits something they share" sounds circular.
- **Verdict: not fatal, but the wording must change.**
  - The question was never "how important was the firm in some deep sense". It is "do
    rivals gain or lose, and does market share explain which?" That question has an
    answer whatever the channel is.
  - The circularity charge is exactly what the pre-registered test answers. If a label
    written from a news paragraph, *before* anyone looks at rival returns, predicts the
    sign of the rival reaction, it is a useful rule, not a circle. A circular rule could
    not fail; this one can.
  - Prices cannot tell apart **transmission** (the failure itself damages rivals: IL&FS
    froze the funding market other lenders used) and **revelation** (the failure shows
    rivals have the same weakness: SVB). The paper will say so plainly. Both mean rivals
    lose, and neither has anything to do with market share.
  - In the technical sections, use "spillover" instead of "importance". Keep
    "importance" for the motivation and the title.
  - The classification rule must be about **structure**: what the rivals share with the
    failed firm (a funding market, a depositor base, an owner, a liability rule that
    legally applies to them too). It must not be about whether rivals "seemed affected".

**Objection 2: "Your 'shared dependency' label is just a Financials dummy, and bank
contagion has been known for 40 years."**
- Four of the six shared-dependency readings are lenders or banks (IL&FS, DHFL, Yes
  Bank, SVB). Bank-failure contagion is old news (Aharony & Swary 1983).
- If the rule only works inside finance, the general claim shrinks to "bank runs
  spread".
- **Verdict: not fatal, but it is the biggest risk to the *general* claim.** The fix is
  a pre-registered split: hit rate and mean difference reported separately for
  financial and non-financial failed firms, with the meaning of each outcome written
  down in advance. Part A is also re-run excluding Financials (Phase 3). India's business
  groups (the "owner" channel) and liability events outside finance are where the
  general claim gets its real test.

**Objection 3: "Your 'market share' is a weak proxy, so of course it explains little."**
- "Share" here is the firm's share of 63-day *trading value* among S&P 500 members of
  its *current* GICS sub-industry. It is not revenue share or market cap. It ignores
  private, foreign and non-index rivals.
- A noisy measure explains less than the true variable would (attenuation bias). Three
  noisy variables against about 25 sub-industry dummies is not a fair race.
- Our own tercile table shows that share *does* matter on day 0 (−0.77% for small-share
  firms, −1.77% for large-share firms).
- The "fades by day 20" result has low power: t = −0.6 is not the same as "zero".
- **Verdict: not fatal, but the claim must be narrower.** The paper will say: "share
  predicts the size of the *first-day* hit, not whether the damage *lasts*; industry
  identity explains far more than our share proxy." It will not say "share doesn't
  matter". Phase 3 adds a fairer race (out-of-sample R², share within sub-industry) and
  confidence intervals for the 20-day effect, and the paper names revenue shares from
  CRSP/Compustat as the fix.

**Smaller objections, handled in the design:**
- Eight cases picked after the fact: the pre-registered test.
- Confounding events: Yes Bank fell during the COVID crash; SVB came with Credit Suisse.
  These are flagged case by case.
- Market-adjusted returns ignore beta. High-beta bank stocks look worse in a falling
  market for no special reason, so the out-of-sample test adds a market-model
  (beta-adjusted) version.
- Peers come from today's GICS list, so they are survivors.

**Is any objection fatal? No.** The question stays as decided. The thesis is sharpened
to:

> When a firm collapses, whether its rivals lose or gain is predicted by **what they
> share with it** (a funding market, a depositor base, an owner, or a legal liability),
> not by its market share. Market share predicts only how big the first-day hit is. We
> do not claim to separate "the failure damaged rivals" from "the failure revealed that
> rivals had the same weakness"; both mean rivals lose.

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
3. Backtests of LLM judgments risk **look-ahead bias**: the model may already know what
   happened. (Glasserman & Lin 2023, an arXiv working paper, find that a "distraction"
   effect from knowing the company matters more than look-ahead in their test, and that
   anonymising helps.)
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
