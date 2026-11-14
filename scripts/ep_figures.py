"""Figures for paper 3's proposal (static PNGs; palette validated with the dataviz
validator: #2a78d6, #eb6834, #1baf7a pass in light mode; aqua's contrast warning is met by
direct labels).
  fig1: India 2010-2020, net monthly Sharpe ratio of 1/N vs optimisers vs entropy rules
  fig2: the entropy frontier, out-of-sample CEQ (gamma 2.5) against effective N, by signal,
        India and US, with the theory's full-information optimum marked
Run: python scripts/ep_figures.py"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
S = json.loads((ROOT / "results" / "entropy_portfolio" / "real" / "summary.json").read_text())
OUT = ROOT / "docs" / "entropy_portfolio"
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "figure.facecolor": SURF,
                     "axes.facecolor": SURF, "savefig.facecolor": SURF})

# ---------------------------------------------------------------- figure 1
sm = S["india"]["summary"]
rows = [("1/N (equal weight)", "1/N", C2),
        ("Sample mean-variance", "mv", C1), ("Sample min-variance", "min", C1),
        ("Min-variance, Ledoit-Wolf", "min-LW", C1), ("Min-variance, 2-norm (CV)", "min-norm2-CV", C1),
        ("Min-variance, long-only", "min-c", C1), ("Mean-variance, long-only", "mv-c", C1),
        ("Kan-Zhou three-fund", "KZ3", C1), ("Tu-Zhou combination", "TZ", C1),
        ("Entropy rule: none", "none:R1", C3), ("Entropy rule: momentum", "mom:R1", C3),
        ("Entropy rule: low volatility", "lowvol:R1", C3)]
fig, ax = plt.subplots(figsize=(7.2, 4.6))
y = np.arange(len(rows))[::-1]
for yi, (lab, k, col) in zip(y, rows):
    v = sm[k]["net"]["sharpe"]
    ax.barh(yi, v, height=0.62, color=col, edgecolor=SURF, linewidth=2)
    ax.text(v + (0.004 if v >= 0 else -0.004), yi, f"{v:.3f}", va="center",
            ha="left" if v >= 0 else "right", color=INK, fontsize=9)
ax.set_yticks(y)
ax.set_yticklabels([r[0] for r in rows], color=INK)
ax.axvline(0, color=INK2, linewidth=0.8)
ax.grid(axis="x", color=GRID, linewidth=0.6)
ax.set_axisbelow(True)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.set_xlabel("Net monthly Sharpe ratio (after Indian costs)")
ax.set_xlim(-0.16, 0.19)
fig.suptitle("India, top 100 stocks, Feb 2010 – Dec 2020: 124 months out of sample",
             x=0.01, ha="left", color=INK, fontsize=10.5)
from matplotlib.patches import Patch  # noqa: E402
ax.legend(handles=[Patch(color=C2, label="1/N"), Patch(color=C1, label="Information-free optimisers"),
                   Patch(color=C3, label="Entropy rule (pre-registered R1)")],
          loc="lower left", frameon=False, fontsize=8.5)
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(OUT / "fig1_india_1N_vs_optimisation.png", dpi=180)

# ---------------------------------------------------------------- figure 2
fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.9), sharey=False)
names = {"none": "none (36-m mean)", "mom": "momentum 12-1", "lowvol": "low volatility"}
cols = {"lowvol": C3, "mom": C2, "none": C1}
for ax, mk, title in zip(axes, ("india", "us"), ("India 2010–2020", "US 2005–2020")):
    for s in ("lowvol", "mom", "none"):
        h = S[mk]["H3"][s]
        x = np.array(h["levels"])
        yv = np.array(h["ceq_gross_pct"])
        ax.plot(x, yv, color=cols[s], linewidth=2, marker="o", markersize=4,
                markeredgecolor=SURF, markeredgewidth=1)
        j = int(np.argmax(yv))
        ax.plot(x[j], yv[j], marker="o", markersize=9, color=cols[s],
                markeredgecolor=SURF, markeredgewidth=2, zorder=5)
        p = h["full_info_pred"]
        yp = np.interp(p, x[::-1], yv[::-1])
        ax.plot(p, yp, marker="v", markersize=9, color=SURF, markeredgecolor=cols[s],
                markeredgewidth=2, zorder=6)
        ax.annotate(f"{names[s]}\nIC {h['eval_ic_mean']:.3f}".replace("-", "−"),
                    (x[-1], yv[-1]), xytext=(6, 0), textcoords="offset points",
                    va="center", fontsize=8, color=INK)
    ax.set_xlim(1.03, -0.42)
    ax.set_xticks([1.0, 0.8, 0.6, 0.4, 0.2, 0.0])
    ax.set_xlabel("Effective N as a share of N (1 = equal weight)")
    ax.grid(color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_title(title, loc="left", color=INK, fontsize=10.5)
    if mk == "us":
        ax.set_ylim(0.1, 0.8)
axes[0].set_ylabel("Out-of-sample CEQ, % a month (γ = 2.5)")
from matplotlib.lines import Line2D  # noqa: E402
fig.legend(handles=[Line2D([], [], marker="o", color=INK2, linestyle="", markersize=9,
                           label="best level (ex post, diagnostic)"),
                    Line2D([], [], marker="v", color=SURF, markeredgecolor=INK2,
                           markeredgewidth=2, linestyle="", markersize=9,
                           label="theory's full-information optimum")],
           loc="lower center", ncol=2, frameon=False, fontsize=8.5)
fig.suptitle("The entropy frontier: more information, fewer effective stocks — but less "
             "concentration than theory predicts", x=0.01, ha="left", color=INK, fontsize=10.5)
fig.tight_layout(rect=(0, 0.07, 1, 0.95))
fig.savefig(OUT / "fig2_entropy_frontier.png", dpi=180)
print("saved")
