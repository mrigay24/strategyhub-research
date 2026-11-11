# Study Guide: what to read and know while the paper is being written

This guide is for you, Mrigay. It covers four things:
- what to read, in what order;
- the ideas you need to own;
- what to check while the paper session works;
- the moves you can suggest to it.

Total reading time is about 3–4 hours. Do Part 1 now, and the rest while the session runs.

---

## Part 1 — The paper in 60 seconds (memorise this)

**Question.** When a company suffers its own crash, do its rivals gain or lose? And does
the company's market share explain which?

**Claim.** A firm's importance comes from what other firms **depend on through it**, not
from its market share.

**Evidence so far.**
1. **US, 266 company-specific crashes.**
   - On the day of a firm's crash, its closest rivals (same GICS sub-industry) fall
     **−1.2%** (t −7.6). That happens in 71% of events.
   - Bigger firms drag rivals down more (−1.8% vs −0.8%).
   - Within 20 days the damage is small or zero (−0.3%; the 95% interval runs from −1.2%
     to +0.6%).
   - **Market share has no out-of-sample predictive power** for how rivals react. Which
     sub-industry it is predicts a little: about 6–7% out of sample in the larger
     samples.
   - *Corrected on 11 Nov:* the earlier "industry explains 10× more" came from in-sample
     R², and most of it was over-fitting (see §2.8).
   - The day-0 hit survives without Financials (−0.9%) and without the 2008–09 and 2020
     crises.
2. **Eight famous collapses.**
   - Damage **spread** when rivals shared a critical dependency with the failed firm:
     - the same funding market (IL&FS);
     - the same depositors' confidence (Yes Bank, SVB);
     - the same owner (Adani group);
     - the same liability or regulator (PG&E).
   - Rivals **gained** or were unaffected when what the firm produced could be replaced:
     Satyam (rivals +12.6%), Jet Airways, and Adani's non-group rivals (+7.7%).

**Weakness.** You picked the 8 cases after you knew how they ended. The pre-registered
test (Phase 2) is what turns a story into evidence.

**One-sentence pitch to a professor:** "Market share doesn't predict whether a firm's
collapse hurts its rivals. I test a rule you can apply from the news alone: whether the
rivals shared a dependency with it, like funding, depositors or an owner. The test is
pre-registered, out of sample, on India and US collapses."

**The value proposition (why anyone should care).** On the day a company collapses,
investors, lenders and regulators all need the same answer: will the damage spread to
its rivals, or will the rivals absorb it?
- The tool they usually reach for, market share or concentration (HHI), turns out to
  have no predictive power for this.
- This paper offers a rule you can apply on day 0 from the news alone, and tests it
  honestly.

Who uses it:
- **Investors and risk managers:** which rivals to hedge, and which to buy, after a
  collapse.
- **Regulators and antitrust:** a firm matters because others *depend on it*, not
  because it is *big*. "Too connected", not "too big".
- **Researchers:** one rule that links three literatures usually studied apart (bank
  contagion, supply chains, business groups), with India evidence and the first
  pre-registered test of this kind the literature check found.

The strength of that pitch depends on the pre-registered result. Part 6 says what each
outcome means.

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

---

## Part 7 — Questions a professor will ask (and your answers)

**1. "How is this different from Lang & Stulz?"**
They explain rivals' reactions with concentration and leverage, using US bankruptcies
from the 1970s–80s. You test the failed firm's *own* market share directly, and it has
no out-of-sample predictive power. You propose *shared dependency* instead, test it with
a pre-registered out-of-sample design, and add India, where business groups create
ownership dependency. Aharony & Swary (1983) found something similar for banks: a fraud
at one bank doesn't spread, a shared weakness does. Your rule extends that idea beyond
banks.

**2. "Isn't shared dependency just 'banks are contagious'?"**
Answer with Move 1's result. Either it holds outside financials (Adani: ownership;
PG&E: liability), or you narrow the claim honestly.

**3. "How do you measure market share without revenue?"**
Through a 63-day dollar-volume share. It is a proxy, and it tracks firm size closely.
The fix is Compustat revenue through WRDS. Ask whether IU has access. This is a good
question to *ask them*.

**4. "Why do rivals fall on day 0 if the damage fades?"**
Because of fear and information (§2.7). The fade is the point: only dependency causes
*lasting* damage.

**5. "Your 8 cases are cherry-picked."**
Yes, that's why there is a pre-registered out-of-sample test, with a git timestamp as
proof.

**6. "What about survivorship bias? Dead firms are the whole point."**
- The US sub-industry map covers current members, so Phase 3 tries to add delisted firms.
- The India data is survivorship-free.
- You found and fixed a split-adjustment problem in it, and the results got *stronger*.

---

## Part 8 — Schedule (2–3 days)

| When | Session does | You do |
|---|---|---|
| **Day 1** | Phases 1–2 (literature, pre-registration, OOS test) | Send Moves 1–2 immediately. Read Tier 0 + MacKinlay. Do the Move 3 checkpoint. Read the OOS result. |
| **Day 2** | Phases 3–5 (robustness, figures, draft, one-pager, email drafts) | Read Lang & Stulz + Barrot & Sauvagnat. Skim Tier 2. Read the draft and mark what you can't explain. |
| **Day 3** | Fixes from your read-through; Phase 6 only if time remains | Rehearse Part 7 out loud. Edit the email drafts in your own voice. Send only when *you* are ready. Nothing is sent automatically. |

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
