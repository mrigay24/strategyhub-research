# Group-name check (12 Nov 2026)

**Question:** do non-standardised group names in the verified map
(`results/group_dependency/group_map_v2.csv`) inflate the "effective number of owner
groups"?

**Method:** take the 926 distinct Family/Corporate group names (1,355 rows), normalise them
(lower case, drop brackets and words like "group", "family", "ltd"), and compare. Also list
names that share a first word, for a check by hand.

**Result: no naive duplicates.** Every collision is a deliberate split into family
branches, which the map records as separate owners. Separate is correct, because after a
split each branch runs its own companies:

| Shared name | Branches kept separate |
|---|---|
| Bajaj | Rahul Bajaj family; Shekhar Bajaj (Electricals); Niraj Bajaj (Mukand); Kushagra Bajaj (Hindusthan) |
| Jindal | Ratan, Naveen, Prithviraj |
| TVS | Venu Srinivasan; Sundaram Finance; Sundram Fasteners; Srichakra; TVS Mobility |
| Reliance | Mukesh Ambani; Anil Ambani (ADAG) |
| Also | Modi (KK / BK), Minda (Ashok / Nirmal), Finolex (Prakash / Deepak Chhabria), Oswal |

The other first-word collisions are unrelated companies, e.g. Sun Pharma vs Sun TV,
Apollo Hospitals vs Apollo Tyres.

**What this means for the headline:**
- The earlier caveat, that non-standardised names may overstate effective N of groups,
  is **mostly resolved**.
- The remaining judgement call is the family-branch definition. Merging branches would
  lower the group count further, so the published G1 numbers are the conservative choice.
- Script used: an inline pandas check, recorded here. It is not a pipeline step.
