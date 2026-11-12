# Referee report (paper 2) and response

*The report below was written on 12 November 2026 by a fresh AI subagent (Claude Opus),
asked to act as a senior finance referee. It was given only `PAPER2_DRAFT.md`, the
`results/group_dependency/` and `results/group_concentration/` files and the scripts that
made them. It saw none of the pilot note, the pre-registrations or the author's
conclusions. It is reproduced unedited; it reviewed the first draft, whose Section 6
followed the earlier draft design. Diagnostics added in response are in
`scripts/group_dependency_referee_checks.py` → `results/paper2_referee/referee_checks.json`.
None was pre-registered, and none changes the registered GO verdict.*

---

# Referee report

**Manuscript:** "Count Groups, Not Stocks: Business-Group Contagion and Hidden Concentration in India" (working paper draft, November 2026)

## Summary

The paper asks a question about Indian family and corporate groups. When one group firm crashes (falls at least 15% in a day, and at least 12 points more than the market and its industry), do the group's firms in other industries lose more than unrelated stocks with the same pre-event correlation? And do they lose more than the crashing firm's industry rivals?

The pre-registered event study has 113 events; 72 of them, from 29 groups, have an other-industry sibling. Over days 0–20, siblings' buy-and-hold abnormal return (BHAR) coefficient is −4.70 pp (*t* −2.66, clustered by month). Rivals' is −0.35 pp, and the siblings' crash-day coefficient is −2.16 pp. Without the seven events from the author's companion paper, the sibling BHAR coefficient is −1.85 pp (*t* −1.71).

The paper also uses AMFI market caps and a promoter map partly checked against filings. On that basis, the top 500 stocks have an exp-entropy effective number of 231, but only 156 owner groups. For 25 active funds, the ratio of stocks to groups is about 1.10.

## Overall assessment

The paper is unusually transparent. It has a pre-registration, a disclosed deviation, every registered check reported (unfavourable ones included) and a traceability appendix. I reproduced the primary regression exactly from `v2/pairs.parquet`. The question matters for index design and risk management where business groups dominate.

The headline language goes further than the evidence in four ways:

1. The crash-day effect, presented as the robust result, is mostly news that hits the whole group at once. It also fails group-level inference (wild bootstrap *p* = 0.115).
2. Identification rests on about 29 groups and a few episodes the author already knew.
3. The finding that "the verified map strengthens the result" comes from a change in which pairs are in the sample, not from cleaner labels.
4. The effective-N comparisons have no benchmark.

**Recommendation: major revision.** Reframed as "owner-level crash co-movement that pre-event correlation misses, concentrated in stressed groups," the paper would be a credible contribution.

## Spot-check of numbers

About 40 numbers match the files, including:

- event, group and pair counts;
- Tables 1–6, in both versions;
- the placebo moments;
- robustness checks R1–R9;
- leave-one-group-out, worst-event shares and group means;
- D2 (−1.3, *t* −2.40);
- fund statistics;
- map counts (21/26, 230/858, 1,017→1,149, 209→117, 95 decisions, 11,106 filings).

Mismatches:

- **(a)** "93% to over 99% of top-500 cap" matched: the top-500 range is 93.2–98.5%. Only the top 100 exceeds 99%.
- **(b)** "96 have usable comparison data": 96 is the number of events with at least one sibling (S or SI) pair that passes the data filters.
- **(c)** The "event-level permutation" is actually a within-event reshuffle of S labels among S and B stocks (`permutation_S`).
- **(d)** "The crash-day effect survives every check, *t* above 3": under the registered trigger-group clustering, *t* is −1.90 (v2) and −1.93 (v1).
- **(e)** The "calm year" is all days from −261 to −10, not calm days only.

## Major comments

**M1. The crash-day effect is mostly simultaneous group news, and the response after day 0 is not significant.**

When several group firms qualify on the same day, the code picks the one with the highest traded value as the trigger and treats the rest as siblings. In v2, 21 S/SI pairs in 10 events have a day-0 abnormal return of −12% or worse.

On 4 February 2019 (E0071), the trigger, Reliance Capital, ends the window at −2.3%. Its "siblings" RCOM, Reliance Power and Reliance Infra lose 47–56%. That is shared news, not transmission.

From the existing files, CAR 1–20 (`car_0_20 − ar_d0`) gives β_S = −3.35 pp (*t* −1.61). Dropping the co-crashing pairs halves the crash-day β to −1.05 pp. That second step selects on the outcome, so treat it as a bound.

*Fix (existing data):*
- Report CAR 1–20 as the test of transmission.
- Replace "contagion" with "group-level crash co-movement".
- Report single-qualifier events separately.
- State that the 0–20 window includes day 0.

**M2. Inference should respect dependence within groups.**

The same siblings recur across events: RCOM is a sibling in 9 events. The variation that identifies siblings comes from 29 unbalanced groups; Tata alone supplies 77 of the 227 S pairs. Clustering by trigger group gives *t* = −1.93 (BHAR), −1.90 (crash day) and −1.72 (S−R).

I ran two checks on `v2/pairs.parquet`:

- **Wild cluster bootstrap by trigger group** (restricted, Rademacher weights, 1,999 draws). The 0–20 BHAR survives (two-sided *p* = 0.040). The crash day does not (*p* = 0.115), and CAR 1–20 is borderline (*p* = 0.063).
- **Group-swap placebo.** Each event's pseudo-siblings are the other-industry members of another group present in the sample on that date. The SD is 1.10 pp and *p* < 0.001.

Group-level inference therefore reverses the paper's ranking of which result is robust.

*Fix (existing data):*
- Report this bootstrap next to month clustering.
- Give *t*(S−R) in every row.
- Describe the permutation correctly, or replace it with the group-swap placebo.

**M3. The evidence beyond the motivating episodes is thin, and the "stressed group" label is post hoc.**

The hypothesis grew out of Pathak (2026), whose episodes are in the sample. Pre-registration does not make them out of sample. In R2 (those episodes dropped):

- β_S = −1.85, with *t* −1.71;
- *t*(S−R) = −1.10;
- group bootstrap *p* = 0.059 for BHAR and 0.134 for the crash day.

Of the events, 56% are negative (sign *p* 0.205), and ten events carry the whole net effect. Keeping one event per group-year (74 events) leaves β_S at −4.90 pp (bootstrap *p* = 0.007). That is reassuring, but it still keeps the first event of every stressed episode.

*Fix:*
- Present R2 as the confirmatory test.
- Define stress ex ante and test S × stress, using pledges (`promoter_pledges.csv`) or each group's drawdown over the prior six months. *New computation.*
- Add a pre-event placebo window (days −60 to −21) to separate continuing distress drift from a response to the trigger. *New computation.*

**M4. The v1→v2 deviation was not blind, and R6 changes the sample rather than the label quality.**

The v1 results and the diagnostics naming the driving groups existed before verification (11 Nov 23:38–23:39; v2 map 12 Nov 01:56). The statement "before any return was computed on v2" therefore does not establish blinding.

The move to v2 shifted which sibling pairs count as high-confidence:

- **Moved in:** 32 pairs, mean BHAR −11.8% (Indiabulls −20.5%).
- **Moved out:** 79 pairs, mean +0.1%. Of these, 45 are Tata pairs from all six Tata events, downgraded under v2's documentation rule.

Because that rule favours firms with dated filings, the high-confidence pairs are now mostly from events in 2019 or later. Their mean BHAR is −13.2%, against about 0 for earlier events. The claim that "the labels were not what made v1 look fragile" therefore does not follow.

*Fix (existing data):*
- Lead with v1, the registered version; its estimates are nearly identical.
- Show this decomposition.
- Define confidence independently of the event's date.
- Disclose that the event-date check was done by an AI.
- Audit a random sample of the 858 unchecked firms for missed siblings.

**M5. Parent–subsidiary and holding-company links are mixed in with shared ownership.**

Ujjivan SFB → Ujjivan Financial Services is among the ten worst events, but the second firm is a holding company whose main asset was the first. Reliance Capital → Nippon AMC is a parent–subsidiary pair. These are cash-flow links, not promoter contagion.

*Fix (partly existing data):* flag pairs where one firm directly owns the other's equity (`shp_promoters.csv` for 2020 onward; annual reports before that). Report β_S without them.

**M6. The effective-N measure needs benchmarks.**

- **(a)** exp(H) of weights measures concentration, not co-movement. "Behave like 231 equal-sized stocks … 156 independent owner groups" therefore overstates. Summing weights over any coarser partition lowers N_eff, so a ratio above 1 is mechanical. Report the industry N_eff that Section 2 promises, and a null that partitions stocks at random with the same group-size distribution (existing data).
- **(b)** AMFI full market cap is not what index funds hold. It overweights promoter-heavy and state firms (LIC's free float is tiny). Either recompute with free-float factors (new data) or drop the phrase "the cap-weighted market that index funds buy".
- **(c)** The G2 figure (82) rests on an assumption that R4 cannot test. Move it out of the abstract.
- **(d)** Report Family-only groups separately. HDFC, ICICI and L&T are parent–subsidiary structures, not families.

**M7. The fund-level negative is not benchmarked, and it is partly mechanical.**

The ratio rises with how many stocks a portfolio holds, so a 50-stock fund cannot be compared with the 500-stock market. Large-cap funds (1.11–1.23) sit below the top-100 ratio (1.45). That is a positive finding the paper does not state.

Small-cap funds have only 68–84% of their weight matched to the map. Across the 25 funds, the Spearman correlation between the ratio and matched weight is 0.66, so ratios near 1 partly reflect holdings the map does not cover.

*Fix:*
- Report ratios on the matched sleeve only.
- Add a random-portfolio null with the same number of names and the same cap profile (existing data).
- Call the 25 funds what they are: a convenience sample.

**M8. Position the paper against the closest literature.**

Two papers in the reference list are never discussed, yet they are the closest antecedents to the event design:

- Bertrand, Mehta and Mullainathan (2002), on shocks propagating within Indian groups;
- Faccio, Morck and Yavuz (2021), on group members' prices incorporating other members' firm-specific shocks.

The novelty claim must be stated against these two. Risk sharing (Khanna and Yafeh 2005) predicts the opposite sign. Common institutional owners (Antón and Polk 2014) are a rival channel; testing it needs holdings data.

The policy section should check and discuss existing SEBI rules: group limits on mutual funds' debt exposure, and the 2023 disclosure trigger for foreign portfolio investors concentrated in a single corporate group.

**M9. Section 6 design.**

Twins built by swapping in stocks from groups already held also change two other things: the share of group-affiliated stocks, and which groups are held (often Tata or ADAG).

*Suggestions:*
- Hold the group-affiliated share fixed by swapping across groups.
- Use placebo groups matched on industry span.
- Report results by group.
- Add a power calculation.
- Record the commit that freezes `PREREGISTRATION_2_DRAFT.md`.

T1-x is a good guard.

## Minor comments

- **m1.** Report the registered R3_bhar_plus_implied (β_S −4.29, *t* −2.68). Controlling for calm-period beta × the trigger's return is the most direct test of whether a covariance model already sees the loss.
- **m2.** Rename "calm correlation" to "pre-event correlation". In the tail test, "calm" means days when the market return is between its 10th and 90th percentiles; harmonise the two uses.
- **m3.** "Ten events carry 99%" is a net figure. The five best events are +10% to +38%. Add a median or Huber regression.
- **m4.** Market beta and leverage are not controlled. "Noise, not bias" on market-wide days is asserted, not shown.
- **m5.** Tail test:
  - report relative frequencies (0.553% vs 0.402%, about +38%);
  - the Gaussian benchmark under-predicts for every pair type;
  - weight groups equally, since Tata dominates;
  - test same-group = same-industry.
- **m6.** The S/SI split rests on 41 industries assigned by an AI; classing ADANIENT as "Diversified" makes every Adani sibling other-industry. Show a sensitivity using NSE's industry codes.
- **m7.** The Dec 2025 and Jun 2026 effective N values extend the map past its June 2025 end. Say so.
- **m8.** Drop "independent" from "a third fewer independent owners". The title overstates the evidence.
- **m9.** Harmonise *p* < 0.001 (abstract) with *p* < 0.0005 (Table 4).
- **m10.** Complete the author names in the references for Faccio et al., Kim et al. and Kwon et al. Cite Coval–Stafford in the text, or drop it.
- **m11.** The SI coefficient (41 pairs) supports no conclusion; say so.

---

# Response to the referee

| # | Comment (short) | Response | Where |
|---|---|---|---|
| M1 | The crash-day effect is mostly simultaneous group news; the response after day 0 is not significant | **Accepted.** We report CAR 1–20 (−3.35 pp, *t* −1.61; bootstrap *p* 0.050), and −0.46 pp without the companion episodes. We report the co-crash count: in 10 events, 21 sibling pairs fell ≥12% on day 0, e.g. the Anil Ambani firms on 4 Feb 2019. "Contagion" is replaced by "group-level crash co-movement" in the text and the stated 0–20 window includes day 0. **Title kept** as given by the author. Dropping the co-crashing pairs is not reported, because it selects on the outcome. | Abstract; §1; §5.4 (Table 5b, "What this changes"); §8 |
| M2 | Inference should respect dependence within groups | **Accepted; the ranking of robust results is reversed in the text.** New Table 5b reports a restricted wild cluster bootstrap by trigger group (41 groups, 1,999 draws). BHAR 0–20 *p* = 0.033; crash day 0.085; CAR 1–20 0.050. Our draws give slightly lower *p* than the referee's (0.040 / 0.115 / 0.063), with the same conclusions. *t*(S−R) by trigger group is in the referee-checks file. The permutation is now described correctly: a within-event reshuffle of the sibling label among sibling and unrelated stocks. **Not done:** the group-swap placebo. | Abstract; §5.1; §5.4 (Table 5b); §8 |
| M3 | Thin evidence beyond the motivating episodes; "stressed group" is post hoc | **Accepted.** Without the companion episodes: BHAR −1.85 pp, *t* −1.71, bootstrap *p* 0.047 (*t* −1.58 by group); CAR 1–20 −0.46 pp. One event per group and year: −4.25 pp, *p* 0.024 (83 events; the referee's version kept 74). The text now says "stressed groups" is a post-hoc reading. **Not done (new computation):** an ex-ante stress interaction and a pre-event placebo window; both are named as the next tests. Pledge data are too thin before 2020. | §5.4; §5.6 "Reading"; §8 |
| M4 | The v1→v2 deviation was not blind; R6 changes the sample, not label quality | **Accepted.** The text states that v2 was built after the v1 results and diagnostics were known. It gives the decomposition: 79 high-confidence sibling pairs moved out (mean +0.1%, 45 of them Tata) and 32 moved in (mean −9.4%); 61% of v2 high-confidence pairs are from 2019 or later (mean −14.1% vs 0.0% before). The claim that "the labels were not what made v1 look fragile" is withdrawn. The paper discloses that the event-date check was done by an AI subagent. **Kept:** v2 still leads, as the parent session asked, with v1 shown alongside and labelled as the registered result; the estimates are nearly identical. **Not done:** a date-independent confidence rule and an audit of the 858 unchecked firms. | §5.1; §5.4; §8 |
| M5 | Parent–subsidiary and holding-company pairs are mixed in | **Accepted as a limitation**, with the Ujjivan and Reliance Capital / Nippon AMC examples. **Not done:** flagging and excluding those pairs needs cross-holding data for all years. | §8 |
| M6 | Effective N needs benchmarks; free float; G2 in the abstract; Family-only | **Accepted.** New benchmarks (latest half-year, top 500): 36 effective industries; a random-regrouping null with the same group sizes, mean 190 (90% range 180–198), so the observed 156 is below every draw; Family-only 163. The paper now says "full market cap" and that the free-float figure is not computed. The phrase about what index funds buy is removed. G2 (82) is out of the abstract. "Behave like … independent" is dropped. | Abstract; §1; §4; §8 |
| M7 | The fund negative is unbenchmarked and partly mechanical | **Accepted in part.** The paper now reports the large-cap ratios (1.11–1.23) against the top-100 market (1.45), small-cap matched weight of 68–84% with Spearman(ratio, matched weight) 0.66 and the bias toward 1, and calls the 25 funds a convenience sample. **Not done:** matched-sleeve ratios and a random-portfolio null with the same cap profile; both need the holdings files re-processed. | §4; §8 |
| M8 | Position against Bertrand et al., Faccio et al., risk sharing, Antón–Polk, SEBI rules | **Accepted.** The contribution now discusses Bertrand, Mehta and Mullainathan (2002), Faccio, Morck and Yavuz (2021), Khanna and Yafeh (2005, verified) and Antón and Polk (2014). The implications cite SEBI's August 2023 rule requiring look-through disclosure by FPIs with more than half their Indian equity in one corporate group (verified). We did not verify mutual-fund group limits, so they are not cited. | §1 Contribution; §7 |
| M9 | Section 6: twins change which groups are held | **Partly addressed by the committed design** (`PREREGISTRATION_2.md`, commit e571bc9): concentrated and dispersed twins replace the same base stocks, so group-affiliated weight is equal. The remaining point (they hold different groups) and the lack of a power calculation are now stated as design notes. Results by group are not registered. | §6 |
| m1 | Report R3 BHAR plus implied move | Done: −4.29 pp (*t* −2.68) v2, −4.10 pp (*t* −2.67) v1. | Table 5 |
| m2 | Rename "calm correlation"; harmonise with the tail test | Done: "pre-event correlation (days −261 to −10)" in the event test; "calm-day correlation" (market between its 10th and 90th percentiles) in the tail test. | §5.1; §5.5 |
| m3 | 99% is a net figure | Done: "net", with the five best events at +10% to +38%; the event median (−2.4 pp) is in Table 5. A Huber regression was not run. | §5.6 |
| m4 | Beta and leverage not controlled | Stated in the limitations; beta enters only through R3. | §8 |
| m5 | Tail test details | Relative frequencies added (0.553% vs 0.402%), plus the under-prediction for every pair type, and that same group ≈ same industry is not tested. Equal-weighting groups was not done. | §5.5 |
| m6 | Industries assigned by an AI; ADANIENT "Diversified" | Stated in the limitations (confirmed in `group_map_v2.csv`). The NSE-industry sensitivity was not run. | §8 |
| m7 | Map end date | Stated. | §4; §8 |
| m8 | "Independent"; title | "Independent" dropped; the title is kept (author's choice), and the conclusion says the honest claim is narrower than the title. | §4; §9 |
| m9 | *p* < 0.001 vs < 0.0005 | The abstract no longer quotes the permutation *p*; the table keeps "0 of 2,000, *p* < 0.0005", and the tail test keeps its own *p* < 0.001. | Abstract; Tables 4, 6 |
| m10 | Author names; Coval–Stafford | Faccio et al. completed; Kim, Kim and Lee and Kwon et al. initials not verified and left as surnames; Coval–Stafford and Khanna–Palepu (uncited) dropped. | References |
| m11 | SI coefficient | Stated: 41 pairs support no conclusion. | §5.3 |
| (a) | Matched share 93–98.5% | Corrected. | §3 |
| (b) | "96 usable" | Corrected: 96 events with at least one sibling pair passing the filters. | §5.2 |
| (c) | Permutation mislabelled | Corrected. | §5.1; Table 4 |
| (d) | "Crash-day survives every check" | Withdrawn: under trigger-group clustering *t* −1.90, bootstrap *p* 0.085. | Abstract; §1; §5.4 |
| (e) | "Calm year" | Corrected to "pre-event year (days −261 to −10)". | §5.1 |

**Verdict after revision:** the registered GO stands in both map versions. The reading
changes: the robust result is the month-long BHAR under group-level inference
(*p* = 0.033), concentrated in a few stressed-group episodes. The crash-day effect is
largely shared news and not significant once dependence within groups is allowed for.
