# When a firm dies, what happens to its rivals?

**Mrigay Pathak, Indiana University · November 2026 · one-page summary of the working paper
*Market Share Is Not Importance* (`PAPER_DRAFT.md`)**

**The problem.** When a company collapses (a fraud, a default, an auditor walking out),
investors, lenders and regulators must decide that day whether the damage will spread to
its rivals. The usual shortcut is size: a firm with a big market share is assumed to
matter more.

**What I tested.**
1. Does the failed firm's market share predict how its rivals' stocks react? I used 266
   isolated crashes of S&P 500 firms, 2000–2024.
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
| Does industry identity predict it? | A little | 6–7% out-of-sample R² with −10% or −20% crash thresholds |
| Did "shared dependency" collapses hurt rivals more? (pre-registered) | Direction yes, but **too few cases to test** | Only 4 of 40 qualified; rivals −9.3% vs −3.4% over a month (*p* = 0.15) |
| Did rivals of "replaceable" firms hold up? (pre-registered) | **No: this half of the rule failed** | Rivals fell in 55% of those 36 cases |

**The figure to look at:** Figure 4 in the paper (`results/death_test_oos/fig4_oos_outcomes.png`).
It shows one dot per new collapse. The two big losses on the "shared dependency" line are
Citi and Bank of America in 2008–09. The two Indian cases sit near zero.

**What it means, honestly.**
- **Held up:** market share is not a good measure of how much a firm matters to its
  rivals. It sizes the first-day hit and predicts nothing after that.
- **Promising, not established:** "what rivals share with the failed firm" matched the
  biggest losses (the 2008–09 bank rescues), but shared-dependency collapses are rare, and
  outside that crisis the effect disappeared.
- **Failed:** "replaceable rivals are safe". On average, rivals of a failed firm drift a
  little lower rather than gaining.

**Why this design matters.** The eight famous cases I started with (Satyam, Adani, IL&FS,
Yes Bank, SVB…) fit the story perfectly, but they were picked after the fact. Committing
the rules first, in a public repository, is what let the test fail. It did fail on half of
its prediction, and the paper says so.

**What would settle it:** many more shared-dependency failures (CRSP from 1926, more
emerging markets), revenue-based market shares (Compustat), and an independent labeller.
