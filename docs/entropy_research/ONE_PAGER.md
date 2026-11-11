# When a firm dies, what happens to its rivals?

**Mrigay Pathak, Indiana University · November 2026 · one-page summary of the working paper
*Market Share Is Not Importance* (`PAPER_DRAFT.md`)**

**The problem.** When a company collapses (a fraud, a default, an auditor walking out),
investors, lenders and regulators must decide that day whether the damage will spread to
its rivals. The usual shortcut is size: a firm with a big market share is assumed to
matter more.

**What I tested.**
1. Does the failed firm's market share predict how its rivals' stocks react? I used 266
   large one-day drops of S&P 500 firms, 2000–2024 (bad news, not deaths: none was
   delisted within 60 days).
2. A rule of my own, written down and made public *before* I looked at any results.
   Rivals should lose when they **share a critical dependency** with the failed firm (the
   same funding market, depositors, owner or legal liability). They should not lose when
   the firm's product is simply **replaceable**. I labelled 40 new US and Indian collapses
   from the day-0 news alone, then measured how the rivals did.

**What I found.**

| Question | Answer | Key number |
|---|---|---|
| Do rivals fall on the crash day? | Yes, almost always | −1.2% on average; rivals fell in 71% of crashes |
| Does a bigger failed firm hurt rivals more on day 0? | Yes, on day 0 only | −1.8% (largest third) vs −0.8% (smallest third) |
| Does market share *predict* the rival reaction out of sample? | **No** | Cross-validated R² below zero in every sample; *t* ≈ −1 in the 40 new cases |
| Does industry identity predict it? | Barely | Out-of-sample R² −5% to +7% on day 0, negative at 20 days |
| Did "shared dependency" collapses hurt rivals more? (pre-registered) | Direction yes, but **too few cases to test** | Only 4 of 40 qualified; rivals −9.3% vs −3.4% over a month (*p* = 0.15) |
| Did rivals of "replaceable" firms gain? (pre-registered) | **No: this half of the rule failed** | Rivals fell in 55% of those 36 cases (−3.4% on average; not significant outside finance) |

**The figure to look at:** Figure 4 in the paper (`results/death_test_oos/fig4_oos_outcomes.png`).
It shows one dot per new collapse. The two big losses on the "shared dependency" line are
Citi and Bank of America in 2008–09. The two Indian cases sit near zero, and several
"replaceable" regional banks lost even more in the same weeks.

**What it means, honestly.**
- **Held up:** market share is a poor measure of how much a firm matters to its rivals. It
  sizes the first-day hit, and nothing detectable after that (the test is not precise
  enough to rule out small effects).
- **Not established:** rivals of the two 2008–09 bank rescues lost heavily, but rivals of
  "replaceable" banks lost almost as much in the same weeks. Shared-dependency collapses
  are rare (4 of 40, from 3 episodes), the test could only detect gaps of about 14
  points, and outside the crisis the effect disappeared.
- **Failed:** "replaceable rivals gain". On average, they did not gain; they drifted a
  little lower.

**Why this design matters.** The eight famous cases I started with (Satyam, Adani, IL&FS,
Yes Bank, SVB…) fit the story perfectly, but they were picked after the fact. Committing
the rules first, in a public repository, is what let the test fail. It did fail on half of
its prediction, and the paper says so.

**What would settle it:** many more shared-dependency failures (CRSP from 1926, more
emerging markets), revenue-based market shares (Compustat), and an independent labeller.
