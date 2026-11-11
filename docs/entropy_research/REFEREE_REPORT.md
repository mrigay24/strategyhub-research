# Referee report and response

*The report below was written on 11 November 2026 by a fresh AI subagent (Claude Opus),
asked to act as a senior finance referee. It was given only `PAPER_DRAFT.md` and the
`results/` files (plus the scripts that made them), and none of the author's notes or
conclusions. It is reproduced unedited. The response table follows it. Diagnostics added in
response are in `scripts/death_test_referee_checks.py` →
`results/death_test_oos/referee_checks.json`. None was pre-registered, and none changes a
pre-registered verdict.*

---

# Referee report

**Paper:** "Market Share Is Not Importance: What Happens to Rivals When a Firm Dies (US and India)", working paper draft, November 2026

**Recommendation:** Major revision

## Summary

The paper asks whether a failed firm's market share predicts how its rivals' stocks react, and proposes an ex-ante "shared dependency" (SD) label as the alternative to "output-replaceable" (OR). Part A studies 266 isolated one-day crashes of S&P 500 members from 2000 to 2024, with peers taken from the current GICS sub-industry. On day 0, rivals fall 1.20% against the market (clustered *t* −6.8), and more when the crashing firm is in the top share tercile (−1.77% vs −0.77%). By day 20 the effect is gone (−0.29%, CI [−1.24, +0.62]), and share plus HHI has negative cross-validated R². Eight hand-picked collapses motivate the SD rule. A pre-registered test on 40 new collapses (26 registered plus 14 under deviation D1) finds only 4 SD cases, whose rivals do 5.9 pp worse (*p* = 0.15). The verdicts are "too few cases to test" (H1) and "rule fails" (T3); share has *t* ≈ −1.

## Overall assessment

The paper is unusually transparent: the protocol was registered before outcomes were computed, deviations are disclosed, failures are reported, and every number I checked traces to a file. But the text claims more than the inference supports. The negative claims about share are stated as evidence of absence, yet the tests have little power and the paper's own tercile sort shows share matters on day 0. The "OR fails" verdict is nearly automatic under the chosen criterion. The SD "promise" rests on two US megabanks in one crisis, in which OR-labelled regional banks lost more. Part A contains no deaths. This is a careful pilot with a negative result. A field journal would need historical peers, revenue shares, many more SD cases and inference that allows for dependence between cases.

## Spot-check of reported numbers

These all match the files: 266 events, 37 sub-industries and 241 dates; the day-0 mean, *t* and 71% figure; the terciles and gap; all 16 cells of Table 2 and all rows of Table 5; Spearman 0.786 (7 groups); the Table 3 BHARs for Satyam, Adani, IL&FS and SVB; Table 4 (−5.86 pp, *p* 0.1523, Fisher 0.116, T5 *t*); every cell of Table 6 and the OR CI; the overlap check (−10.2 pp, *p* 0.04995); 11 of 20 US cases in September 2008 to March 2009; and Appendix A, Test 1.

I found no material mismatch. Small ones:

- The Table 3 *t*-statistics are for the CAR, not the BHAR shown (m1).
- "All (~390)": the files give 310–463 members per window, with a mean of 373.
- The 2011 data hole ends on 30 December 2011 in the text but 31 January 2012 in the script.
- The figure numbers do not match the file names.

## Major comments

**M1. Part A is not about firm deaths, and it conditions on survival.** A firm enters only if it has a sub-industry in the *current* GICS file, so firms that later failed or were delisted cannot enter. The script's own check (`delisted_within_60d`) finds **0 of 266** events delisted within 60 days. The median fall is −19%, and only 3 events fall more than 50%. Energy contributes one event in 25 years, and 2014 contributes none. These are earnings-type shocks to survivors. The relevant benchmark is intra-industry information transfer (Foster 1981; Thomas and Zhang 2008), where rivals of larger announcers react more, which is exactly what Table 1 shows. *Fix:* report the zero-deaths result, call Part A "large idiosyncratic drops", and keep "dies" for Section 6 only. *New data:* historical SIC/GICS codes and CRSP delisting codes.

**M2. "Share carries none" contradicts the paper's own numbers.**

- In Part A, the day-0 share gap excludes zero in 5 of 6 variants. The pooled regression in `summary.json` gives share *t* = −2.2, and within sub-industry *t* = −1.8. A small real effect has cross-validated R² ≤ 0 whenever its true R² is below about *k*/*n*, so a negative cross-validated R² is not evidence of no information.
- In the out-of-sample test, T5 gives −0.14 (SE ≈ 0.14), with a 95% CI of about [−0.42, +0.13]. A 20 pp share difference is compatible with anything from +2.7 to −8.3 pp. The point estimate (−2.8 pp) equals the OR mean.
- Share correlates −0.33 with the number of peers. In India it depends on how many rivals were hand-picked (IBHFL 0.53; Maytas and LVB 0.00).

*Fix:* say instead that "share's incremental power is small (R² < 1%), confined to day 0 and undetectable at 20 days". Report CIs and an equivalence bound, control for the number of peers, and retitle. *New data:* Compustat revenue shares.

**M3. The cross-validation leaks, and the industry result is reported selectively.** `cv_r2` uses random folds, while events cluster in 2000–02, 2008–09 and 2020–24, so fitted sub-industry means leak across folds from the same episode. Sub-industry cross-validated R² is positive only at the −10% and −20% thresholds. It is negative everywhere else: −1.3% at baseline, −2.6% excluding Financials, −0.7% excluding crises, −5.1% with sector peers, and −17.7% at the 20-day horizon. The abstract cites only the two favourable variants. *Fix:* use leave-one-year-out cross-validation, report every variant at both horizons, and write "industry's out-of-sample R² ranges from −5% to +7%".

**M4. The out-of-sample cases are not independent.**

- 21 of the 40 cases fall in five 30-day clusters. These include seven cases between 16 and 29 January 2009, three Indian cases on 25 February 2013 and three Anil Ambani firms on 4 February 2019.
- RF, FITB and HBAN09 have nearly identical rival sets.
- RPOWER and RELINFRA count twice. They are two OR cases (+1.7% and −0.0%) with three shared rivals, and they are also the two group firms (about −55% each) that drive RCOM's T4 outcome.
- The four SD cases are really three episodes, because LVB and DHFL are one day apart.

A permutation across all 40 cases assumes they are exchangeable, which they are not. *Fix (existing files):* run an episode-stratified permutation. My version, with 30-day episodes, gives within-episode SD − OR gaps of +5.3, −24.8 and −4.8 pp (mean −8.1, *p* ≈ 0.16). Recode RPOWER and RELINFRA as owner-channel cases, and report the effective number of SD episodes.

**M5. Where SD has cases, the label does not sort the outcomes, and two sentences in the text are wrong.** The three largest losses are OR cases: RF −29.3%, HBAN −28.1% and FITB −25.3%. BAC ranks fourth and Citi seventh. So Section 1 ("the largest out-of-sample losses came where rivals were funded in the same markets...") and Section 8 ("flagged the largest losses") are incorrect. In January 2009, BAC's rivals lost 22.6%, against −17.7% across the six OR cases.

Citi's 2008 advantage over HIG, CI and LNC comes from rival sets drawn from the current GICS file. Cigna's "rivals" are CVS, DaVita, LabCorp and Quest, and State Street's are asset managers. Day-0 rival abnormal returns of −5% to −9% on 20–22 January 2009 indicate sector-wide shocks, yet GNW (29 September 2008) was screened out as one. *Fix:* correct both sentences, add a within-crisis comparison, and apply the industry-shock screen consistently. *New data:* point-in-time industry codes.

**M6. The OR verdict is nearly automatic, and the test was underpowered by design.** If the true OR effect is zero, the expected hit rate is 50%. A ">50%" threshold then fails half the time, and the "≥2/3" threshold for non-financials fails almost always. In the data:

- Non-financial OR cases average −1.6%, CI [−4.2, +0.9], with 10 hits in 22 (binomial *p* = 0.83).
- Financial OR cases average −6.2%, CI [−14.0, +1.7].

That shows "no gain", not "loss". On power: with outcome SD ≈ 10.5% and 4 SD cases against 36 OR, the minimum detectable gap (one-sided 5%, 80% power) is about 14 pp, and about 12 pp even with 5 SD cases. *Fix:* keep the verdicts verbatim but rewrite the readings in Sections 1, 6.3 and 10, and delete "'replaceable rivals are safe' half is wrong". Add a power section, and use an equivalence test for OR in the next registration.

**M7. The out-of-sample and blinding claims have gaps.**

- (a) Episodes were excluded by symbol ±60 days, not by episode. This let in IN-ATGL (an Adani group firm on the Adani case's day 0), IN-DHFL19 (the DHFL case firm four months later) and IN-MAYTAS (the Satyam–Maytas deal, three weeks before Satyam). Dropping these three leaves SD at −12.2% and OR at −3.6%. The results hold, but the paper should show this.
- (b) An AI assistant drafted the paragraphs and the author approved them. Both knew how 2008–09 and the 2019 NBFC crisis unfolded. Independent coders should label paragraphs with names and dates masked, and the paper should report kappa.
- (c) Git timestamps can be set by the author. Cite server-side push times, or deposit the protocol on OSF.
- (d) The abstract leads with the D1 sample, but Table 4 calls the registered sample primary. Add a flow table showing how 195 candidates became 40 cases plus 8 shocks, with counts for each exclusion reason.

**M8. The contribution is overstated.** The paper omits Benmelech and Bergman (2011), whose collateral channel from bankruptcies to rivals is a non-financial shared dependency and exactly this paper's idea. It also omits Hertzel and Officer (2012), Cheng and McDonald (1996), Jacobson and von Schedvin (2015) and Kolay, Lemmon and Tashjian (2016). Barrot and Sauvagnat also report spillovers to other suppliers of the same customers, which is closer to "horizontal" than the paper says. The claim "no pre-registered corporate-finance event study" should acknowledge the *JAR* registered reports. The rule codes the Lang–Stulz split plus the Jorion–Zhang and Helwege–Zhang channels, so the novelty is the protocol, not the rule. Excluding crises, SD averages −0.5% against −1.7% for OR, so "most promising candidate" (Section 10) should be toned down.

## Minor comments

- **m1.** The Table 3 *t*-statistics use the CAR (Adani group CAR −61.3% against BHAR −41.9%) and the standard deviation from the estimation window. Event-induced variance (Boehmer, Musumeci and Poulsen 1991) inflates the *t*-statistics for Yes Bank, SVB and Adani.
- **m2.** Part A is adjusted for the market only. Add a market-model variant; the beta code already exists in the out-of-sample script.
- **m3.** Clustering by date (241 clusters for 266 events) is nearly the same as assuming independence. Cluster by month (134) or sub-industry (37).
- **m4.** Quantify the effect of the ±45% filter on RF, FITB and HBAN09 (6 February 2009). Note that missing rival returns are set to 0.
- **m5.** Table 2 should state that both models include the failed firm's own day-0 abnormal return, and that sub-industries with fewer than 5 events are pooled.
- **m6.** Section 6.3 says the failure is "not concentrated in one kind of firm", but the numbers are −1.6% against −6.2%.
- **m7.** PSKY21 (ViacomCBS, 26 March 2021) was the Archegos liquidation. That is a common-holder channel (Coval and Stafford 2007) that the rule does not cover.
- **m8.** Appendix A belongs to another paper; drop it, or fix "~390" and explain why the mean return rises with N (8.7% to 11.7%).
- **m9.** Describe the 250-day one-event rule used in selection. In `build_events`, `last = t` is set before the bad-print filter, so a discarded print still blocks the next 20 days.
- **m10.** Complete the Ganguly–Mishra–Platt reference, and write "the author" rather than the name in Section 6.1.

---

# Response to the referee

| # | Comment (short) | Response | Where in the draft |
|---|---|---|---|
| M1 | Part A has no deaths (0 of 266 delisted within 60 days), and it conditions on survival | **Accepted.** We now say so in the abstract, the introduction, Section 4 and the limitations. Part A is renamed "large idiosyncratic drops" and framed as intra-industry information transfer (Foster 1981; Thomas and Zhang 2008). "Deaths" refers only to Sections 5–6. *New data needed:* historical industry codes and CRSP delisting returns. | Abstract; §1; §4 (title and first paragraph); §9 |
| M2 | "Share carries none" contradicts the day-0 gap and in-sample *t* = −2.2; the out-of-sample share null is uninformative | **Accepted.** New wording: share's incremental power is "small, confined to day 0 and undetectable out of sample". The draft reports the in-sample *t* = −2.2. It adds the 95% interval for the out-of-sample share coefficient (−0.42 to +0.13; a 20-point share gap is compatible with −8.3 to +2.7 pp) and explains why a negative CV R² does not prove zero. **Not done:** a control for the number of peers, which would be a further unregistered regression. **Title kept** (the author's working title); "Is Market Share a Measure of Importance?" is a possible alternative if the author prefers. | Abstract; §1; §4; §6.3 "Dependence and power" |
| M3 | Random-fold CV leaks across episodes; the industry 6–7% is selectively reported | **Accepted in part.** Table 2 now shows every variant and the 20-day horizon (sub-industry −17.7% at 20 days). The abstract and introduction now say "−5% to +7% on day 0, negative at 20 days", and the text notes that random folds flatter the sub-industry model. **Not done:** leave-one-year-out CV, because it needs a re-run of Part A; it is listed as the stricter test. | Abstract; §1; §4, Table 2 |
| M4 | The 40 cases are not independent; the permutation *p* is invalid | **Accepted.** New paragraph with episodes (24 episodes; 21 cases in 5 multi-case episodes; the SD cases come from 3 episodes). It notes the RPOWER/RELINFRA double count, and reports an episode-stratified permutation: within-episode gaps +5.3, −24.8 and −4.8 pp, mean −8.1 pp, *p* = 0.155, which reproduces the referee's figure. **Not done:** recoding RPOWER/RELINFRA as owner-channel cases, because labels are fixed by the pre-registration; the double count is disclosed instead. | §6.3 "Dependence and power"; §9 |
| M5 | Within the crisis, SD does not sort outcomes; two sentences were wrong | **Accepted; both sentences corrected.** §6.3 now states that the three largest losses are OR banks and gives the within-episode comparison (BAC 22.6% vs 17.7% for the six OR cases; Citi 13.5% vs +11.3% for three OR insurers, partly an artefact of current-GICS rival sets). §1 ("who uses it") now says the five largest losses were all 2008–09 US financials, whatever their label. §8 now says SD "did not flag the largest" losses. The industry-shock screen inconsistency (January 2009 vs Genworth) is in the limitations. | §1; §6.3; §8; §9 |
| M6 | The OR "fails" verdict is nearly automatic; the design was underpowered | **Accepted.** The verdicts are kept verbatim, as the pre-registration requires, but the reading is rewritten: OR rivals "did not gain, not that they lost". The draft gives sub-group intervals (non-financial −4.2% to +0.9%; financial −14.0% to +1.7%) and deletes the "'replaceable rivals are safe' half is wrong" line. New power paragraph: the minimum detectable gap is 13.8 pp (4 vs 36) and 12.6 pp (5 vs 35), and about 23 SD cases would be needed for the observed gap. An equivalence test is recommended for the next registration. | Abstract; §1; §6.3; §10 |
| M7 | Leaked case-study episodes; hindsight in labels; git timestamps; registered vs D1 in the abstract; no flow table | **Accepted.** (a) The three overlaps are named, and dropping them is reported (SD −12.2%, OR −3.6%). (b) Hindsight is disclosed, with masked independent coding named as the fix. Phase 6 runs an LLM labeller. (c) The draft now says commit times are author-set, points to GitHub push records, and plans an OSF deposit next round. (d) The abstract now leads with the registered sample (2 SD, −18.0% vs −3.7%), with the full population in brackets, and Table 4a gives the flow from 195 candidates to 26 + 14 cases. | Abstract; §6.1 (Table 4a, overlap paragraph, labels) |
| M8 | Novelty overstated; missing references | **Accepted.** Added Benmelech and Bergman (2011), Hertzel and Officer (2012), Cheng and McDonald (1996), Jacobson and von Schedvin (2015), Kolay, Lemmon and Tashjian (2016), Thomas and Zhang (2008), Coval and Stafford (2007), and the JAR registered-reports experiment (Bloomfield, Rennekamp and Steenhoven 2018). The contribution now says the rule's ingredients are not new and the novelty is the protocol. The Barrot–Sauvagnat bullet acknowledges their spillovers to other suppliers. "Most promising candidate" is now "a candidate worth a properly powered test". | §1 Contribution; §10; References |
| m1 | Table 3 *t* uses CAR; event-induced variance | Accepted: the caption says so and cites Boehmer, Musumeci and Poulsen (1991). | §5, Table 3 note |
| m2 | Part A is market-adjusted only | Acknowledged in the limitations; a beta-adjusted Part A is future work. | §9 |
| m3 | Date clustering is nearly independence | Acknowledged in the limitations (month or sub-industry clusters). | §9 |
| m4 | Quantify the ±45% filter; missing returns set to 0 | The direction is stated (it works against OR) and missing-as-zero is now disclosed. **Not quantified**: that would be a further unregistered re-run. | §7 |
| m5 | Table 2 should state the controls and the pooling | Done. | §4 |
| m6 | "Not concentrated in one kind of firm" vs −1.6% / −6.2% | Sentence replaced. | §6.3 |
| m7 | PSKY21 is a common-holder channel | Added to the limitations (Coval and Stafford 2007). | §9 |
| m8 | Appendix A: "~390", mean rising with N | Fixed ("310–463 per window") and explained (compounding). Kept as a short appendix because the project's motivation section refers to it. | Appendix A |
| m9 | Describe the 250-day rule; `build_events` bad-print quirk | The 250-day rule is now described. The quirk (a discarded print still blocks the next 20 days) is acknowledged here. It can only remove events, and Part A is not re-run. | §6.1 |
| m10 | Complete the Ganguly reference; "the author" | Done: full title from the journal listing. The paper's findings could not be verified, so the draft now cites only its scope. "The author" is used in §6.1. | §2; §6.1; References |
| — | Hole end date; figure numbers vs file names | Hole wording fixed. Figure numbers follow the paper's order; file names are unchanged. | §3 |

**Verdicts after revision (unchanged):** H1 "too few cases to test" in both versions; T3
"the rule fails out of sample" in both; H4 (share does not predict) holds in both.
