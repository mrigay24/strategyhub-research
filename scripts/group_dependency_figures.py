"""
Paper 2 figure: pilot coefficients (sibling in another industry S, sibling in the same
industry SI, industry rival R), crash day and 21-day BHAR, verified map v2 (filled) and
v1 (hollow), 95% intervals from month-clustered standard errors.

Reads results/group_dependency/tests.json (v1) and v2/tests.json.
Writes results/group_dependency/figures/fig_pilot_coefficients.png.
Also fig_effn_market.png: effective N of stocks vs owner groups (G1, G2), top 500 by
market cap, from results/group_concentration/v2/headline_by_period.csv (verified map v2).
Palette: reference dataviz palette, slot 1 blue #2a78d6 (single hue; v1/v2 by fill).
Run:  ~/.venvs/strategyhub/bin/python scripts/group_dependency_figures.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GD = ROOT / "results" / "group_dependency"
OUT = GD / "figures"
OUT.mkdir(exist_ok=True)
BLUE = "#2a78d6"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK, "axes.titlesize": 9.5,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.grid": True, "axes.grid.axis": "x", "grid.color": GRID, "grid.linewidth": 0.6})
CLASSES = [("S", "Sibling, other industry"), ("SI", "Sibling, same industry"), ("R", "Industry rival, other group")]


def coefs(path: Path, key: str) -> dict:
    d = json.load(open(path))
    r = d["primary"]["regression"] if key == "primary" else d["robustness"][key]
    return {c: (r["coef"][c] * 100, r["se"]["month"][c] * 100) for c, _ in CLASSES}


def main() -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.7), sharey=True)
    panels = [("R3_day0_AR", "Crash day: abnormal return (pp)"), ("primary", "Days 0-20: BHAR, registered test (pp)")]
    for ax, (key, title) in zip(axes, panels):
        for off, (path, face, lab) in zip([0.13, -0.13], [(GD / "v2" / "tests.json", BLUE, "verified map (v2)"),
                                                          (GD / "tests.json", SURF, "original map (v1)")]):
            c = coefs(path, key)
            for i, (cls, _) in enumerate(CLASSES):
                b, se = c[cls]
                y = len(CLASSES) - 1 - i + off
                ax.plot([b - 1.96 * se, b + 1.96 * se], [y, y], color=BLUE, lw=2, solid_capstyle="round", zorder=2)
                ax.scatter([b], [y], s=50, facecolor=face, edgecolor=BLUE, linewidth=1.8, zorder=3,
                           label=lab if i == 0 else None)
                if face == BLUE:
                    ax.annotate(f"{b:+.1f}", (b, y), xytext=(0, 6), textcoords="offset points",
                                ha="center", va="bottom", fontsize=7.5, color=INK)
        ax.axvline(0, color=INK2, lw=0.8)
        ax.set_title(title, loc="left")
        ax.set_ylim(-0.6, len(CLASSES) - 0.35)
    axes[0].set_yticks(range(len(CLASSES)))
    axes[0].set_yticklabels([lab for _, lab in CLASSES][::-1])
    for ax in axes:
        ax.tick_params(axis="y", length=0)
    axes[1].legend(loc="lower left", frameon=False, fontsize=7.5, handletextpad=0.2)
    fig.text(0.01, 0.01, "Coefficients vs unrelated stocks with the same pre-event correlation; event fixed "
             "effects; bars = 95% intervals (clustered by month).", color=INK2, fontsize=6.8)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(OUT / "fig_pilot_coefficients.png", dpi=200)


def market() -> None:
    import pandas as pd
    h = pd.read_csv(ROOT / "results" / "group_concentration" / "v2" / "headline_by_period.csv", parse_dates=["period"])
    h = h[h["universe"] == "top500"]
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    for col, colr, lab in [("effN_stocks", "#2a78d6", "stocks"), ("effN_groups_G1", "#eb6834", "owner groups (G1)"),
                           ("effN_groups_G2", "#1baf7a", "owner groups, state as one owner (G2)")]:
        ax.plot(h["period"], h[col], color=colr, lw=2, marker="o", ms=4, label=lab)
        last = h.iloc[-1]
        ax.annotate(f"{last[col]:.0f}  {lab}", (last["period"], last[col]), xytext=(6, 0),
                    textcoords="offset points", va="center", fontsize=7.5, color=INK)
    ax.set_ylim(0, 260)
    ax.set_xlim(h["period"].min() - pd.Timedelta(days=60), h["period"].max() + pd.Timedelta(days=1250))
    ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in range(2018, 2027, 2)])
    ax.set_xticklabels([str(y) for y in range(2018, 2027, 2)])
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.spines["left"].set_visible(True)
    ax.set_ylabel("effective N = exp(entropy)")
    ax.set_title("India, top 500 companies by market cap: effective number of stocks vs owner groups", loc="left")
    ax.legend(loc="lower left", frameon=False, fontsize=7.5)
    fig.text(0.01, 0.01, "AMFI 6-month average market caps, half-years Dec 2017 - Jun 2026; verified group map (v2).",
             color=INK2, fontsize=6.8)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT / "fig_effn_market.png", dpi=200)


if __name__ == "__main__":
    main()
    market()
