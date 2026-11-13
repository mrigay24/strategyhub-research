# Study Guide: the death-test paper

This guide is for you, Mrigay. Part 1 is the finished paper's result and pitch. Parts 2–3
cover the ideas you need to own and what to read. Part 7 has the questions a professor
will ask, and Part 8 the steps from here. **Part 9 is paper 2 (business groups: shared owners, shared crashes?).** Parts 4–6 record how the paper was built and
checked.

---

## Part 1 — The paper in 60 seconds (memorise this)

**Status (11 Nov 2026): the paper is finished.** The files are in `docs/entropy_research/`:
- `PAPER_DRAFT.md` and `.docx`;
- `ONE_PAGER.md`;
- `EMAIL_DRAFTS.md` (nothing has been sent);
- `REFEREE_REPORT.md`.

**Question.** When a company suffers its own crash, do its rivals gain or lose? And does
the company's market share explain which?

**What the paper claims (final):**

> Market share is a poor measure of a firm's importance to its rivals. What rivals
> *share* with a failed firm (funding, depositors, an owner) is a candidate worth a
> properly powered test, not an established answer.

This is weaker than where you started ("importance = shared dependency"). The
pre-registered test is why.

**Evidence.**

1. **US, 266 large one-day crashes of S&P 500 firms (2000–2024).**
   - On the crash day, rivals in the same GICS sub-industry fall **−1.2%** against the
     market. That is about 1 point more when the crashing firm is in the top third by
     share.
   - After 20 days the damage is small or zero: −0.3%, with a 95% interval of −1.2% to
     +0.6%.
   - **Market share has no out-of-sample predictive power** for the rivals' reaction.
     Sub-industry identity does little better: −5% to +7% on day 0, negative at 20 days.
   - The day-0 hit survives without Financials (−0.9%) and without the crises.
   - None of these firms was delisted within 60 days. So this part measures how bad news
     spreads, not deaths.
2. **Eight famous collapses (chosen after the fact, so they are motivation, not proof).**
   - Damage spread where rivals shared a dependency: IL&FS, Yes Bank, SVB, the Adani
     group, PG&E.
   - Rivals gained where the output was replaceable: Satyam's rivals +12.6%, Adani's
     outside rivals +7.7%.
3. **A pre-registered test on 40 new US and Indian collapses.** 26 were registered and 14
   were added in a disclosed extension. You approved the labels before any return was
   computed.
   - **Applied strictly, the rule found only 4 of 40 "shared dependency" cases:**
     Citigroup and Bank of America (2008–09), Lakshmi Vilas Bank and DHFL (2019).
     - Most firms collapse for reasons of their own: fraud, governance, auditor
       resignations, pledged shares.
   - Those 4 cases' rivals lost **−9.3%** over 20 days, against **−3.4%** for the other 36.
     - The gap is 5.9 points, with p = 0.15, so not significant.
     - Almost all of the gap comes from the two US bank rescues.
     - Within the 2008–09 crisis the label did **not** sort outcomes. The biggest losses
       were regional banks labelled "replaceable".
   - **The verdict fixed in advance: "too few cases to test."**
   - **The "replaceable" half failed its own test.** Those rivals did not gain: mean
     −3.4%, median −0.8%, down in 20 of 36. Strictly, they "didn't gain"; they didn't
     clearly lose either, since neither mean is distinguishable from zero.
   - **Market share again predicted nothing** (t ≈ −1).
   - **Indian business groups:** all 3 group sets fell (average −28%). With only 3 sets the
     best possible p is 0.125, so this is consistent with the owner channel, not evidence
     for it.
   - **Power was low by design.** The test could detect only gaps of about 14 points.
     Confirming a 6-point gap would need about **23** shared-dependency cases.
   - **An AI labeller** given the same rule agreed on 37–38 of 40 labels. Hiding the
     names did not stop it from recognising the firms, so hindsight can't be ruled out.

**One-sentence pitch to a professor (honest version):** "I tested whether a failed
firm's market share predicts how its rivals react. In 266 US crashes and a
pre-registered test on 40 US and Indian collapses, it doesn't. My alternative, shared
dependency, couldn't be confirmed, because strict rules found only 4 cases. How would you
get enough cases to test it properly?"

**The value proposition now.** Three things are solid and useful:
1. **A finding:** market share is not a good guide to how much a failure hurts rivals.
   - Rivals usually share the first-day fall rather than gain.
   - Investors shouldn't size a hedge on rivals by the failed firm's share beyond day 1.
2. **A method:** the literature check found no other pre-registered event study of
   contagion after failures.
   - Yours is public (rules, case list, code), and it reports its own failure.
   - It also caught its own over-fitting, the withdrawn "10×" claim.
   - That is a credibility signal professors notice.
3. **A clear next step that needs them:** the dependency rule needs about 20–25 cases.
   That means a longer sample (CRSP back to 1926 through WRDS) or more emerging markets.
   This is the natural ask in your emails. You are not asking them to admire a result;
   you are offering a tested protocol and asking how to scale it.

**Why a negative result is still worth sending:**
- It is honest.
- The market-share null is a real finding.
- It shows you can run research properly: pre-register, report failure, correct
  yourself.

For a student approaching professors, that last point counts more than a flashy
result.

**Before sending anything, two fixes:**
1. **Length.** About 10,900 words, roughly 25 pages, against the 10–15 page target. A
   professor is more likely to read a shorter version.
2. **Read `REFEREE_REPORT.md`.** It lists the 8 strongest objections and how each was
   answered. These are the questions you will get.

---

## Part 2 — Ideas you must own (plain language, with your own numbers)

Each idea has a one-line meaning and a small example. If you can explain all of these
out loud, you can defend the paper.

### 2.1 Measuring concentration: share, HHI, entropy, effective N

Take an industry with 4 firms whose shares are 40%, 30%, 20% and 10%.

- **HHI** is the sum of the squared shares:
  0.4² + 0.3² + 0.2² + 0.1² = 0.16 + 0.09 + 0.04 + 0.01 = **0.30**.
  - Monopoly = 1.
  - Many equal firms → close to 0.
- **Effective N = 1/HHI = 3.3.** The industry behaves as if it had 3.3 equal firms.
- **Entropy H = −Σ w ln w = 1.28.** Divided by ln 4 = 1.39, that gives a **normalised
  entropy of 0.92**.
  - 1 = perfectly even.
  - 0 = one firm has everything.
  - Entropy and HHI tell the same story with different weighting. Entropy pays more
    attention to the small firms.
- **Your share proxy:** you don't have revenues or market caps, so "share" here is the
  firm's share of the sub-industry's **63-day dollar trading volume** (price × volume).
  This is a limitation a professor will ask about (Part 6).

### 2.2 Abnormal return: the basic unit of the whole paper

- **Abnormal return = what the stock did − what the market did that day.**
- Example: if rivals fell 3.0% on a day the market fell 1.8%, their abnormal return is
  −1.2%.
- You subtract the market so a bad day for *everyone* doesn't look like contagion.
- In your code, "market" means the equal-weighted average of all other stocks, excluding
  the crashing firm and its sub-industry.

### 2.3 Event study: line up many events on "day 0"

- Day 0 is the first trading day after the news is public. You then average across all
  events.
- Day −20 to −1 is the **pre-event window**. It shows whether the news leaked or was
  expected (Jet Airways: IndiGo rose +14.8% *before* the shutdown).
- This method is 50+ years old and standard. MacKinlay (1997) is the textbook (Part 3).

### 2.4 CAR vs BHAR: two ways to add up returns over days 0–20

- **CAR** adds the daily abnormal returns.
- **BHAR** compounds them: buy-and-hold, minus what the market did over the same period.
- Example: a stock goes −50% one day and then +50% the next.
  - CAR = −50 + 50 = **0**.
  - BHAR = 0.5 × 1.5 − 1 = **−25%**, which is what an investor actually lost.
- For big crashes BHAR is the honest measure, and the case table uses BHAR. CAR is used
  for the short windows.

### 2.5 t-statistic: "how surprised should I be?"

- **t = the average effect ÷ its typical noise.**
  - |t| > 2 means roughly a 5% chance of seeing an effect this big if the true effect
    were zero.
  - |t| > 3 is strong.
- −7.6 for the US day-0 effect is very strong.
- **Satyam's +12.6% has t 1.4.** That is a big number but not statistically strong: one
  event, six rivals, a volatile time.
  - Don't say "significant" about single cases.
  - Say "large" and "consistent in direction" (5 of 6 rivals up).

### 2.6 Contagion vs competitive effect

These are the two opposing forces, from Lang & Stulz (1992):
- **Contagion:** the crash is bad news for rivals too. Customers get scared, lenders pull
  back, or the crash reveals a problem the whole industry shares.
- **Competitive effect:** rivals gain, because they take the dead firm's customers.

Each event shows the *net* of the two. Your contribution is a rule for predicting
**which one wins**: shared dependency means contagion wins; replaceable output means
the competitive effect wins.

### 2.7 Three reasons rivals might fall on day 0 (the hardest point, know it cold)

1. **Information:** the crash tells the market something about the whole industry, such
   as weak demand (Foster 1981).
2. **Dependency:** rivals rely on the same funding, depositors, owner or regulator.
3. **Fear:** investors sell the whole group without discriminating.

Days 0–20 help separate them:
- Fear and minor information **fade**.
- Real dependency damage **lasts**.

That is why the pre-registered prediction is about the **20-day BHAR**, not day 0. In
the US large sample, the day-0 hit fades to almost nothing. That suggests most ordinary
crashes are fear or information, not dependency.

### 2.8 Adjusted R²: "how much does this explain?"

- R² is the share of the variation in the rivals' reaction that the variables explain.
- *Adjusted* R² penalises you for adding variables, so a model with 37 sub-industry
  labels doesn't win just by having more knobs.
- Your in-sample result: share + HHI = 0.8%, sector = 8%, sub-industry = 14%. That
  looked like "industry beats size by 10×".
- **The lesson: in-sample R² can fool you.** The paper session ran a fairer test,
  5-fold cross-validation: fit on 80% of events, predict the other 20%, repeat.
  - In the baseline 266 events, *neither* variable predicts out of sample. The 14% was
    mostly over-fitting: 37 labels memorising noise.
  - With more events (the −10% and −20% thresholds), sub-industry predicts about 6–7%
    out of sample. Share never predicts anything.
- The honest claim: **industry identity carries some out-of-sample information; market
  share carries none.**
- This correction is good for you. A professor will trust a paper that caught its own
  over-fitting.

### 2.9 Persistence (Spearman rank correlation)

- Rank sub-industries by their average day-0 peer reaction in 2000–12 and again in
  2012–24. Spearman measures how similar the two rankings are: 1 = identical order.
- Your result: 0.79 for sub-industries (only 7 qualify) and 0.90 for sectors (only 5).
- So the trait looks **stable** for the day-0 reaction. But it rests on few industries,
  so call it "suggestive".
- The 20-day ranking is not stable (≈ 0).

### 2.10 Pre-registration: why the git timestamp matters

- If you look at outcomes and then decide the rules, you can always find a story that
  fits. This is called the "garden of forking paths".
- Pre-registration means you write the rules first:
  - which cases count;
  - how they are labelled;
  - what you predict;
  - how you test it.
- You **commit them to git before computing any results**. The commit timestamp proves
  the order.
- Afterwards you report the result whatever it is.
- **The rule you must never break:** labels come from *news descriptions of the cause*,
  never from how the rivals' stocks moved.

### 2.11 Permutation test: the right test for a small sample

- Suppose 10 "dependency" cases average −12% and 10 "replaceable" cases average +3%: a
  15-point gap.
- Shuffle the labels randomly 10,000 times and recompute the gap each time.
- If only 1% of shuffles produce a gap of 15 points or more, then **p = 0.01**.
- It makes no assumptions about the shape of returns, so it suits a small number of
  messy cases.
- **Realistic expectation:** with 15–30 cases, p around 0.05–0.15 is plausible even if the
  idea is right. The **hit rate** (how many cases go in the predicted direction) matters
  as much as p.

### 2.12 Clustering and bootstrap (Phase 3 robustness)

- Crashes on the same day (for example in Oct 2008) are not independent. Treating them
  as independent makes t-stats too big.
- **Clustering by date** corrects for that.
- **Bootstrap** re-samples the events thousands of times to get a confidence interval,
  without assuming a bell curve.
- If the −1.2% result survives both, it is solid.

### 2.13 Data traps you already hit (good stories for interviews)

- **Survivorship bias:** if dead firms are missing from your data, you can't study
  death.
  - The S&P sub-industry map only covers *current* members, so delisted firms are
    missing from Part A.
  - Phase 3 tries to fix this.
- **Splits and bonuses:** an Indian 1:1 bonus halves the share price overnight. In
  unadjusted data it looks like a −50% crash (Infosys three times, Cholamandalam −80%).
  - Fixing it *raised* your India market-neutral alpha from 10.5% to 15.2% a year.
  - The fake crashes had been hitting good stocks.
- **The 20% "clean" filter deletes real crashes.** For crash studies, use the raw price
  file with a $1 floor.
- **Look-ahead bias:** using information that wasn't available at the time.
  - Day 0 must be "the first day after the news", never "the worst day nearby".
  - The same problem applies to LLMs: they already know how Adani ended.

---

## Part 3 — What to read, in order

Use your IU library login: JSTOR, ScienceDirect and Wiley all work through it. SSRN is
free.

### Tier 0 — your own material (30 min, do now)

1. `docs/entropy_research/RESEARCH_NOTE.md` §1, §4b and §6: the question, the results
   and the paper plan.
2. `results/death_test/cases.csv`: open it in Excel and look at the numbers yourself.

### Tier 1 — must read before emailing anyone (about 2 hours)

| Paper | Read | Look for |
|---|---|---|
| **MacKinlay (1997), "Event Studies in Economics and Finance," *Journal of Economic Literature*** | Sections 1–4 (≈ 30 min) | How abnormal returns, the estimation window and test statistics work. This is the method your whole paper uses. |
| **Lang & Stulz (1992), "Contagion and Competitive Intra-Industry Effects of Bankruptcy Announcements," *Journal of Financial Economics*** | Abstract, intro, the main results table, conclusion (≈ 45 min) | On average rivals lose (contagion). In **concentrated** industries with **low-debt** rivals, rivals can gain. Their explanation is concentration and leverage; yours is dependency. This is the paper you are extending. |
| **Barrot & Sauvagnat (2016), "Input Specificity and the Propagation of Idiosyncratic Shocks in Production Networks," *Quarterly Journal of Economics*** | Abstract, intro, how they define "specific" inputs (≈ 45 min) | Natural disasters at suppliers hurt customers **only when the input is hard to replace**. That is your replaceability idea, already proven for supply chains. You extend it to rivals, finance and ownership. |

**Shortcuts if you don't want to read the full papers.** There are no videos of these
three papers. Instead:
- Barrot wrote a 5-minute plain-English column on his paper, "How do financial shocks
  spread between companies?" (World Economic Forum, Feb 2015). Read that instead of the
  QJE paper.
- For Lang & Stulz, read only the abstract and introduction (≈ 15 min).
- Or ask the paper session in Phase 1 to put a half-page plain summary of each paper into
  RESEARCH_NOTE.md.
- For the statistics, StatQuest on YouTube (p-values, hypothesis testing) is the best
  explainer.

**The non-negotiable minimum** is about 30 minutes. You need to be able to say, in your
own words, what Lang & Stulz and Barrot & Sauvagnat found and how your paper differs. A
professor will ask.

### Tier 2 — skim the abstracts and intros (≈ 45 min total)

| Paper | Why it matters to you |
|---|---|
| Jorion & Zhang (2007), "Good and Bad Credit Contagion," *JFE* | Which kind of bankruptcy brings contagion and which a competitive effect, measured with credit default swaps. Closest to your question in credit markets. |
| Hertzel, Li, Officer & Rodgers (2008), *JFE* | Distress spreads to **suppliers and customers**: dependency along the supply chain. |
| Bertrand, Mehta & Mullainathan (2002), "Ferreting Out Tunneling," *QJE* | Indian business groups move money between group firms. This is why the Adani group fell together: the *owner* was the shared dependency. |
| Diamond & Dybvig (1983), "Bank Runs, Deposit Insurance, and Liquidity," *JPE* | The classic bank-run model, behind Yes Bank and SVB. Know the idea; you don't need the maths. |
| Hou & Robinson (2006), "Industry Concentration and Average Stock Returns," *JF* | Concentrated industries earn lower returns. Relevant to the investor paradox ("a high-entropy portfolio of firms in low-entropy markets"). |

### Tier 3 — know they exist (one line each is enough)

- **Gabaix (2011):** big firms' shocks move the whole economy.
- **Acemoglu et al. (2012):** shocks spread through input–output networks.
- **Adrian & Brunnermeier (2016), CoVaR:** a death test for banks.
- **Foster (1981):** earnings news spreads to peers. This is the "information" channel
  in §2.7.
- **Cohen & Frazzini (2008):** markets are slow to price supplier–customer links.
- **Hoberg & Phillips (2016):** text-based peer groups from 10-K filings.
- **Bessembinder (2018):** most stocks lose to T-bills, and a few create all the wealth.
  This explains your Test 1.
- **Goerner, Lietaer & Ulanowicz (2009):** efficiency vs resilience in ecology. This is
  your bridge to your uncle.
- **Kritzman et al. (2011):** absorption ratio.
- **Brunnermeier & Sannikov (2014):** risk builds up in calm periods.

Phase 1 of the paper session checks every one of these references. Trust its corrected
list over this one.

---

## Part 4 — How the work is built (so you can follow the session)

### 4.1 Files

| What | Where |
|---|---|
| Plan the session follows | `docs/entropy_research/NEXT_SESSION_PROMPT.md` |
| Research note, the master record | `docs/entropy_research/RESEARCH_NOTE.md` |
| US test + 8 cases (code) | `scripts/death_test.py` |
| Their results | `results/death_test/` (`cases.csv`, `cases_peers.csv`, `us_replaceability_map.csv`, `run.log`) |
| Pre-registration (Phase 2 writes it) | `docs/entropy_research/PREREGISTRATION.md` |
| Out-of-sample test (Phase 2 writes it) | `scripts/death_test_oos.py` |
| Earlier entropy pilot (appendix) | `scripts/entropy_research.py`, `results/entropy_research/`; India rerun on corrected prices in `results/entropy_research_ca/` |
| India data fix | KNOWLEDGE_BASE §42; `results/nse_data_audit/` |

### 4.2 What `death_test.py` does

**Part A (US):**
1. Load US prices (raw file, $1 floor). Keep only stocks that were in the S&P 500 at the
   time.
2. Find crashes: the firm fell more than 15% in a day and more than 12% beyond the
   market. That leaves 266 events.
3. Peers = the other firms in the same GICS sub-industry. Measure their abnormal return
   on day 0, days 0–5 and days 0–20.
4. Regress the peer reaction on market share and HHI, then on sector and sub-industry,
   and compare how much each explains.

**Part B (8 cases):** for each named collapse, peers' returns over the 20 days before and
after, plus each peer's own number.

### 4.3 The 6 phases and roughly how long each takes

| Phase | What happens | Your job |
|---|---|---|
| 1. Literature (≈ 1–2 h) | Verifies references, searches for prior work on shared-dependency contagion and the Indian cases | Read its "Is this new?" paragraph. If it finds a paper that already did exactly this, **stop and decide** with it. |
| 2. Pre-registration (≈ 2–4 h) | Writes the rules, commits, finds new cases, labels them from news, runs the test | **The most important checkpoint.** See Part 5. |
| 3. Robustness (≈ 1–2 h) | Other thresholds, clustered and bootstrap errors, excluding crises, sector peers, adding dead firms | Check that the −1.2% survives. |
| 4. Figures (≈ 1 h) | Event-time lines, replaceability map, share terciles | Check that you can explain each figure in one sentence. |
| 5. Paper (≈ 3–4 h) | Draft, .docx, one-pager, email drafts | Read all of it yourself. See Part 6. |
| 6. AI death test (optional) | An LLM labels the cases; compare with yours | Only if Phases 1–5 are solid. |

---

## Part 5 — Moves you can make (copy-paste these into the session)

Ranked by value. The first two must be sent **before the pre-registration is committed**,
which happens early in Phase 2. **Send them right away.**

**Move 1 — the biggest objection, pre-registered (high conviction, send now):**

> Before you commit PREREGISTRATION.md, add a pre-registered secondary test. A reviewer
> will say "shared dependency" just means "it's a bank". So report the hit rate and the
> mean difference separately for financial and non-financial failed firms. Also say in
> advance what each outcome would mean: if dependency only works within financials, the
> claim narrows to "financial contagion"; if it also works for non-financial cases
> (ownership, liability, a shared supplier), the general claim stands. Also run Part A
> excluding Financials in Phase 3.

*Why:* 4 of your 6 "dependency" cases are financial (IL&FS, DHFL, Yes Bank, SVB). Only
Adani (ownership) and PG&E (liability) are not. If the paper can't answer this, the
first professor who reads it will.

**Move 2 — an objective dependency measure (medium conviction, send now if you want it):**

> Also pre-register a continuous, market-based dependency measure: each peer's
> correlation of abnormal returns with the failed firm over days −260 to −10. Prediction:
> within a case, peers with higher pre-event correlation lose more over days 0–20.
> Report it alongside the news-based labels.

*Why:* in IL&FS, the lenders that depended on the same wholesale funding crashed and the
strong ones didn't. This tests whether you can see that dependency *before* the event,
using only prices. That gives you within-case evidence on top of the across-case
labels.

*Cost:* about 1 hour of session time.

**Move 3 — own the labels (checkpoint):**

> After writing the case list and the one-paragraph shock descriptions, show me the
> cases with their labels before computing any peer returns.

*Why:* the labels are the paper's weakest joint. Read each description and ask whether
you would give the same label from the description alone. If you disagree, say so
*now*. After the results come out, changing labels is cheating.

**Move 4 — framing (Phase 5):**

> Lead the abstract with the decision problem and two results: market share has no
> out-of-sample predictive power for the rival reaction, and the pre-registered hit
> rate. Keep Zero to One to two sentences in the intro.

(Already sent to the paper session on 11 Nov, together with the value proposition, a
referee-report pass and number traceability.)

**Moves to resist (scope creep that would kill the 2–3 day timeline):**
- adding a return-prediction strategy or a firm-level score;
- asking for WRDS data now (that comes after a professor engages);
- expanding the AI section beyond Phase 6;
- adding cases by hand because you remember an interesting one. Every case must come
  from the selection rule.

---

## Part 6 — What to check (red flags)

**During Phase 2, the order must be: pre-registration committed → then results.** Check
it yourself:

```bash
git log --format="%h %ad %s" --date=iso -- docs/entropy_research/PREREGISTRATION.md results/death_test_oos scripts/death_test_oos.py
```

The PREREGISTRATION commit must be the oldest line.

Red flags:
- The pre-registration file changes *after* any results exist.
- A label is justified with how the peers' stocks moved.
- Cases are dropped after the results ("bad data") without the reason being logged.
- A single case's t-stat is called "significant".
- Day 0 is chosen as the worst day instead of the news day.
- Peer moves beyond ±45% appear without a log line. Those are probably splits.
- The clean price file is used for crashes.
- The words "proves" or "causes" in the paper. Use "consistent with" and "predicts".

### What each Phase 2 outcome means (decide now, so you don't rationalise later)

| Outcome | What the paper becomes |
|---|---|
| **Confirmed:** direction right in ≥ 75% of cases, permutation p < 0.05 | Strong working paper. Lead with it. |
| **Mixed:** direction right but p > 0.05 | "Suggestive out-of-sample support". The main contribution is Part A + the framework + the cases. Still worth sending. |
| **Fails:** no difference, or the wrong direction | An honest paper: "Market share explains little, industry identity explains more, and the dependency explanation did not survive out of sample." Professors respect this. **Do not relabel to rescue it.** |

**What actually happened (11 Nov).** The main hypothesis got the verdict fixed in
advance, "too few cases to test" (4 shared-dependency cases of 40). The "replaceable"
half failed its sign test, and the market-share null held.
- That is closest to **Fails**, and the paper was written that way: "a careful
  negative".
- No label was changed after the results.
- Moves 1, 3 and 4 were all used. Move 1 (the financial vs non-financial split) gave
  the pre-registered reading "the rule fails out of sample".

---

## Part 7 — Questions a professor will ask (and your answers)

**1. "How is this different from Lang & Stulz?"**
- They explain rivals' reactions with *industry* concentration and leverage, using US
  bankruptcies from the 1970s–80s.
- You test the failed firm's *own* market share directly, out of sample, and it has no
  predictive power.
- You also wrote down an alternative rule in advance and tested it on new cases from
  the US and India.

**2. "So you found nothing?"**
You found four things:
1. Market share doesn't predict the spillover, in 266 + 40 cases.
2. Rivals usually share the first-day fall rather than gain, even when the failed firm's
   output is easy to replace.
3. Strict rules find shared-dependency collapses rarely.
4. Testing the idea properly needs about 20–25 cases.

A clean negative with a public protocol is a result.

**3. "Why only 4 shared-dependency cases?"**
- Most firms collapse for their own reasons: fraud, governance, auditor resignations,
  pledged shares.
- A rule applied strictly from day-0 news rarely finds a shared funding failure.
- More cases need a longer sample (CRSP from 1926) or more emerging markets. Ask them
  how they would get there.

**4. "Isn't shared dependency just 'banks are contagious'?"**
In your data, mostly yes:
- All 4 shared-dependency cases were financial firms.
- The rule labelled no non-financial collapse as shared dependency.
- But the day-0 spillover in the large sample is *not* only banks: it survives without
  Financials (−0.9%).

**5. "Why do rivals fall on day 0 if the damage fades?"**
- Mostly information and fear (§2.7): the crash tells the market something about the
  industry.
- Your hypothesis was that only a shared dependency causes *lasting* damage. The
  out-of-sample test couldn't confirm it.

**6. "Your 8 cases are cherry-picked."**
- Yes. That's why you ran a pre-registered test on 40 new cases.
- It did not confirm the pattern, and the paper says so.

**7. "How do you measure market share without revenue?"**
- Through each firm's share of 63-day trading value among index members. It is a proxy.
- A noisy measure pushes its coefficient toward zero. So the right claim is "this
  measure of share has no predictive power", not "true market share never matters".
- The fix is Compustat revenue through WRDS. Ask whether IU has access.

**8. "What about survivorship bias? Dead firms are the whole point."**
- The US peer groups come from today's GICS file, so they are survivors. True deaths
  need CRSP/Compustat historical codes.
- The India data is survivorship-free. You found and fixed a split-adjustment problem in
  it.

**9. "Did an AI do this?"** Answer plainly:
- You chose the question and the framework.
- You approved every case label before results existed.
- You used Claude as a research assistant for code, data work and drafting.
- The paper says this in its limitations.

Never hide it. Professors respect a clear, honest answer.

---

## Part 8 — From here (paper finished, 11 Nov)

| Step | What | Time |
|---|---|---|
| 1 | Read the paper's abstract, §6.3 (the pre-registered result), §9 (limitations) and §10 (conclusion), plus `REFEREE_REPORT.md` | ≈ 1 h |
| 2 | Read Lang & Stulz and Barrot & Sauvagnat, or the shortcuts in Part 3 | 30 min – 2 h |
| 3 | Decide how to trim the paper to about 15 pages. Appendices can carry the detail | your call |
| 4 | Rewrite `EMAIL_DRAFTS.md` in your own voice. Lead with the market-share finding and end with the ask: how to get 20–25 cases | ≈ 1 h |
| 5 | Rehearse Part 7 out loud, then send when *you* are ready. Nothing is sent automatically | — |

---

## Part 9 — Paper 2: shared owners, shared crashes? (business groups in India)

*Updated 12 Nov evening, after the portfolio test and the referee pass. The draft's working
title "Count Groups, Not Stocks" is being revised, because the portfolio test did not
support it.*

### 9.1 The paper in 60 seconds

**Question.** Many Indian listed companies share an owner (a family, holding company or
parent). Does sharing an owner create crash risk that price-based risk tools miss? And
does it matter for diversified portfolios?

**Claim (final, honest):**
1. **For stocks, yes.** Sharing an owner is a real crash channel that calm-period
   correlation misses. It is concentrated in financially stressed groups.
2. **For diversified portfolios, not measurably.** Concentrating a 30–60-stock portfolio
   in fewer owners did not deepen crisis losses beyond chance.

So "count groups, not stocks" is **not** a general portfolio rule. It matters for big
single-group positions and stressed groups.

**Evidence:**
1. **Pre-registered crash test, verified map.**
   - 113 crash events in 49 groups, 2006–2025.
   - Over the next month, sister companies in unrelated industries lose **4.7 points
     more** than stocks that normally move just as closely with the crashing firm
     (t −2.66). It survives the strictest check, a bootstrap that resamples whole groups
     (p ≈ 0.03–0.04).
   - Industry rivals lose almost nothing extra (−0.4).
2. **What weakens it:**
   - **It's concentrated.** Ten of 72 events carry almost all of it: Adani 2023,
     Indiabulls, Anil Ambani firms. Tata and Aditya Birla show nothing.
   - **Without paper 1's famous episodes** it is weak (t −1.71).
   - **The crash-day part does NOT survive the group-level check** (p ≈ 0.09–0.12). Much
     of it is news that hits the whole group at once. So the paper now says "group-level
     crash co-movement", not "contagion".
3. **Market concentration:** the top 500 behave like **231** companies but **156** owner
   groups, or **82** with the government as one owner.
4. **Funds:** the median active fund holds only about 10% fewer owner groups than stocks.
   Managers already spread across owners.
5. **Portfolio test (pre-registered), NOT supported.**
   - 6,000 matched pairs, a "concentrated" vs a "dispersed" twin (31 vs 43 effective
     groups), across six crises. Both twins have the same industries, volatility and
     correlation-based diversification.
   - The concentrated twin lost only **0.3 points more** (placebo p 0.125). It was
     slightly worse in 2008–09 and COVID, but within chance.
   - In 60,000 random portfolios, owner-based effective N added **nothing** beyond
     volatility.

**One-sentence pitch (honest):** "In India, when a business-group firm crashes, its
sister companies in unrelated industries fall more than their normal correlation
predicts, mainly in stressed groups. But for diversified portfolios, spreading across
more owners didn't measurably reduce crisis losses. Owner risk is a position-level risk,
not a portfolio rule."

**Why the negative portfolio result is still valuable:** it answers the practical
question ("should funds diversify by owner?") with a pre-registered *no, not at
realistic levels*. And it locates where owner risk does matter: single-group positions
and stressed groups.

### 9.2 New ideas you must own

- **Business group / promoter group.** Companies controlled by the same family, holding
  company or parent. SEBI shareholding-pattern filings list each company's "promoter and
  promoter group". That is how the map was checked.
- **Sibling vs rival.** A sibling shares the owner but is in a different industry. A
  rival shares the industry but not the owner. Comparing the two separates "owner risk"
  from "industry news".
- **"Beyond correlation" (the key control).** Siblings already move more closely together
  than random stocks: calm correlation 0.15 vs 0.06. The test compares each sibling with
  stocks of the *same* calm correlation. If correlation explained everything, the sibling
  effect would vanish. It didn't.
- **Clustering and the wild cluster bootstrap.** Events in the same group aren't
  independent: the same siblings recur, e.g. Reliance Communications appears in 9 events.
  The strictest check resamples whole groups. The month-long effect passes, the crash-day
  effect doesn't. **This is the most important methodological lesson of paper 2:** the
  right unit of independence was the group, not the event.
- **Transmission vs revelation.** Did one firm's fall *cause* the siblings' fall, or did
  the news *reveal* a group-wide problem? Prices can't tell. Hence "co-movement", not
  "contagion".
- **Effective N over owners (G1/G2/G3).** The same entropy formula as paper 1, with
  weights summed by owner group.
  - G1 counts family and corporate groups.
  - G2 also counts the state as one owner.
  - G3 groups MNC subsidiaries by parent.
- **Meucci's "effective number of bets" (ENB).** The standard correlation-based
  diversification measure. Owner-based effective N did not beat it.
- **Twin portfolios.** A base portfolio and two matched twins (same ENB and volatility
  within ±5%, same share of group stocks):
  - the concentrated twin swaps in stocks from owners *already held*;
  - the dispersed twin swaps in stocks from *new* owners.

  Concentrated minus dispersed isolates concentration from simply holding group
  companies.
- **Placebo groups.** Shuffle owner labels randomly and rerun many times. A real effect
  must beat nearly all shuffles. The portfolio test didn't (p 0.125).
- **Minimum detectable effect.** The portfolio design could detect only gaps of about
  0.5–0.75 points. The observed 0.3 is below that, so the honest wording is "not
  measurable at this precision", not "proven zero".
- **Promoter pledges.** A promoter borrowing against their own shares. It is the natural
  "fragile group" signal, but the data didn't cover the portfolio formation dates, so it
  wasn't tested.

### 9.3 Numbers to memorise

| Number | What it is |
|---|---|
| −4.7 pp (t −2.66; group bootstrap p ≈ 0.03–0.04) | Sibling extra loss over a month |
| −0.4 pp | Industry rival extra loss (nothing) |
| t −1.71 | The month-long effect without the famous episodes (weak) |
| p ≈ 0.09–0.12 | Crash-day effect under group-level inference (not robust) |
| 231 / 156 / 82 | Top 500: stocks / owner groups / with the state as one owner |
| 1.10 | Median fund's stocks-to-owner-groups ratio |
| −0.3 pp (p 0.125) | Portfolio test: concentrated vs dispersed twin (not supported) |

### 9.4 What to read for paper 2 (abstracts and intros only)

- **Kwon et al. (2019), *Emerging Markets Finance and Trade*.** Crash risk spreads inside
  Korean chaebols. Your closest competitor. You differ through event-level crashes,
  siblings vs rivals, an explicit correlation control, pre-registration, and a portfolio
  test.
- **Gopalan, Nanda & Seru (2007), *Journal of Financial Economics*.** Indian group firms
  support each other with intragroup loans. After the first bankruptcy in a group, the
  other members' financing, investment and profits fall. This is the Indian mechanism.
- **Khanna & Thomas (2009), *Journal of Financial Economics*.** Firms linked by ownership
  and board interlocks move together (Chile): the "group firms co-move" starting point.
- **Meucci (2009), "Managing Diversification", *Risk*.** The effective number of bets, the
  benchmark your owner measure lost to.
- **Greenwood & Thesmar (2011), *Journal of Financial Economics*.** "Stock price
  fragility" from concentrated, correlated *investors*. A cousin of your idea.

Links are in `docs/group_dependency/NOTE.md` §2.

### 9.5 Questions a professor will ask about paper 2

**1. "Isn't this just Adani?"**
Largely the stressed groups, yes, and the paper says so. Ten of 72 events carry the
month-long effect, and without the famous episodes it is weak. No single group drives it:
dropping any one group leaves it significant. The honest claim is "owner risk exists and
correlation misses it; it bites when the group is fragile."

**2. "Group firms co-moving is known."**
On average days, yes (Khanna & Thomas; Korea). What's new:
- crash events;
- siblings in *unrelated* industries compared with rivals;
- a calm-correlation control and group-level inference;
- pre-registration;
- a portfolio test of whether it matters.

**3. "Is it contagion?"**
No claim of causation. Much of the crash-day move is news about the whole group. The
paper says "group-level crash co-movement", and only the month-long effect survives
group-level inference.

**4. "So should investors count groups, not stocks?"**
Not for diversified portfolios. Your own pre-registered test found no measurable
crisis-loss difference at realistic concentration levels. It matters for large
single-group positions and for groups under financial stress.

**5. "An AI built your group map?"**
- The first version was built from memory, and the paper says so.
- It was then checked against NSE shareholding-pattern filings: 544 confirmed, 24
  corrected, 251 unverifiable, 858 not checked (mostly standalone companies).
- The month-long result held on the verified map.

**6. "Why don't funds show the concentration?"**
Active managers already spread across owners (ratio 1.10 vs 1.48 for the cap-weighted
market). Whether index investors' owner concentration matters in an owner-specific
crisis is untested: Hindenburg 2023 was too mild a market fall to tell.

**7. "What would you do next?"**
- A pledge-based "fragile group" measure with full historical pledge data (SEBI
  filings).
- Korea as an out-of-sample market (chaebols).
- An exogenous-shock design to separate transmission from revelation, for example a
  promoter's personal legal case. Ask the professor how they would do this.

---

## Glossary (one line each)

| Term | Meaning |
|---|---|
| Abnormal return | Stock return minus market return that day |
| CAR | Sum of daily abnormal returns over a window |
| BHAR | Buy-and-hold return minus the market's buy-and-hold return; the honest measure for big moves |
| Day 0 | First trading day after the news is public |
| Event study | Line up many events at day 0 and average what happens |
| t-statistic | Effect ÷ noise; above 2 in absolute value is unlikely by chance |
| HHI | Sum of squared market shares; 1 = monopoly |
| Effective N | 1/HHI; "how many equal firms it behaves like" |
| Entropy (normalised) | Evenness of shares; 1 = perfectly even, 0 = one firm has everything |
| GICS sub-industry | The finest standard industry classification (≈ 126 groups in the S&P 500) |
| Contagion effect | Rivals lose when a firm fails |
| Competitive effect | Rivals gain when a firm fails |
| Shared dependency | Rivals rely on the same funding, depositors, owner or regulator as the failed firm |
| Output-replaceable | Rivals can supply what the failed firm made |
| Adjusted R² | Share of variation explained, penalised for extra variables |
| Spearman correlation | How similar two rankings are |
| Pre-registration | Rules written and timestamped before seeing results |
| Permutation test | Shuffle labels many times to see how often chance produces the result |
| Hit rate | Share of cases that went in the predicted direction |
| Clustered standard errors | Error bars that allow events on the same day to be related |
| Bootstrap | Resample events many times to build a confidence interval |
| Survivorship bias | Missing dead firms makes the past look better than it was |
| Look-ahead bias | Using information that wasn't available at the time |
| Bonus issue / split | More shares at a lower price, no change in value; unadjusted data shows a fake crash |
| Business / promoter group | Companies controlled by the same family, holding company or parent |
| Sibling (paper 2) | A same-owner company in a different industry |
| Effective N of owner groups | exp(entropy) of portfolio weights summed by owner group |
| Meucci ENB | Effective number of bets: entropy of risk across independent factors |
| Twin portfolios | Matched portfolios that differ only in how concentrated they are by owner |
| Promoter pledge | A promoter borrowing against their own shares; a stress signal |
