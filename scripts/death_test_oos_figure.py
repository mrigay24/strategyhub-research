"""
Figure 4: pre-registered out-of-sample outcomes, one dot per case (descriptive only).

Reads results/death_test_oos/outcomes.csv (written by `death_test_oos.py run`).
Writes results/death_test_oos/fig4_oos_outcomes.png.
Palette as death_test_figures.py (validated): OR #2a78d6, SD #eb6834.
Run:  ~/.venvs/strategyhub/bin/python scripts/death_test_oos_figure.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "death_test_oos"
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK, "axes.titlesize": 9.5,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.grid": True, "axes.grid.axis": "x", "grid.color": GRID, "grid.linewidth": 0.6})
OFFS = {"IN-LVB": (7, 0, "left", "center"), "IN-DHFL19": (7, 0, "left", "center"),
        "US-HBAN09": (0, 8, "center", "bottom")}
CRISIS = [("2008-01-01", "2009-12-31"), ("2020-02-01", "2020-04-30")]
NAMES = {"US-C": "Citi", "US-BAC": "BofA", "IN-LVB": "Lakshmi Vilas", "IN-DHFL19": "DHFL 2019",
         "US-RF": "Regions", "US-HBAN09": "Huntington", "US-HIG": "Hartford", "IN-COREEDU": "Core Educ."}


def main() -> None:
    o = pd.read_csv(OUT / "outcomes.csv")
    m = o[(o.status == "case") & (o.peer_set == "rivals")].copy()
    m["crisis"] = False
    for a, b in CRISIS:
        m["crisis"] |= m["day0_used"].between(a, b)
    m["x"] = m["bhar_0_20"] * 100
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    rng = np.random.default_rng(7)
    for row, (lab, col) in enumerate([("OR", BLUE), ("SD", ORANGE)]):
        g = m[m.label == lab].sort_values("x")
        y = row + rng.uniform(-0.16, 0.16, len(g))
        for crisis, face in [(True, col), (False, SURF)]:
            k = (g["crisis"] == crisis).values
            ax.scatter(g["x"].values[k], y[k], s=46, facecolor=face, edgecolor=col, linewidth=1.6, zorder=3)
        mu = g["x"].mean()
        ax.plot([mu, mu], [row - 0.3, row + 0.3], color=INK, lw=2, solid_capstyle="round", zorder=4)
        ax.annotate(f"mean {mu:+.1f}%", (mu, row + 0.33), ha="center", va="bottom", fontsize=8, color=INK)
        for cid, xv, yv in zip(g.case_id, g["x"], y):
            if cid in NAMES:
                dx, dy, ha, va = OFFS.get(cid, (0, -9, "center", "top"))
                ax.annotate(NAMES[cid], (xv, yv), xytext=(dx, dy), textcoords="offset points",
                            ha=ha, va=va, fontsize=7, color=INK2)
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_yticks([0, 1])
    ax.set_yticklabels([f"Output-replaceable\n(OR, {int((m.label == 'OR').sum())} cases)",
                        f"Shared dependency\n(SD, {int((m.label == 'SD').sum())} cases)"])
    ax.tick_params(axis="y", length=0)
    ax.set_ylim(-0.65, 1.7)
    ax.set_xlabel("Average rival's 20-day abnormal return, days 0-20 (%)")
    ax.set_title("Out-of-sample cases (full population, 40): rival outcome by pre-registered label", loc="left")
    h = [plt.Line2D([], [], marker="o", ls="", ms=7, mfc=INK2, mec=INK2),
         plt.Line2D([], [], marker="o", ls="", ms=7, mfc=SURF, mec=INK2, mew=1.6)]
    ax.legend(h, ["day 0 in 2008-09 or Feb-Apr 2020", "other periods"], loc="upper left",
              frameon=False, fontsize=7.5, handletextpad=0.3)
    fig.text(0.01, 0.01, "Each dot is one failed firm; bar = label mean. Labels were set from day-0 news "
             "before any rival return was computed.",
             color=INK2, fontsize=6.8)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT / "fig4_oos_outcomes.png", dpi=200)


if __name__ == "__main__":
    main()
