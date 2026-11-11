"""
Phase 4 — figures for the death-test paper (2026-11-11).

  fig1_case_paths.png      cumulative abnormal return of peers, days -20..+20, one
                           panel per case: replaceable rivals (blue) vs peers that
                           share a dependency with the failed firm (orange)
  fig2_replaceability_map.png  US sub-industries (>= 8 crashes): mean peer reaction
                           on day 0 and over days 0-20
  fig3_share_terciles.png  peer reaction by the crashing firm's share of its
                           sub-industry, with date-cluster bootstrap 95% CIs

Palette: reference dataviz palette (validated): rivals #2a78d6, dependent peers
#eb6834; diverging poles red #e34948 / blue #2a78d6; ink #0b0b0b / #52514e.
Run: ~/.venvs/strategyhub/bin/python scripts/death_test_figures.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from death_test import CASES, load, load_india  # noqa: E402
from entropy_research import DATA, us_pit_mask  # noqa: E402

FIG = ROOT / "results" / "death_test" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
BLUE, ORANGE, RED = "#2a78d6", "#eb6834", "#e34948"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK, "axes.titlesize": 9.5,
    "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": SURF,
    "axes.facecolor": SURF, "savefig.facecolor": SURF, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.axisbelow": True,
})

# which peer groups share a dependency with the failed firm (RESEARCH_NOTE §4b reading)
DEPENDENT = {"ilfs", "dhfl", "yes_bank", "pge", "svb"}
TITLES = {"satyam": "Satyam 2009 (fraud)", "jet_airways": "Jet Airways 2019 (shutdown)",
          "ilfs": "IL&FS 2018 (lender default)", "dhfl": "DHFL 2019 (missed payments)",
          "yes_bank": "Yes Bank 2020 (moratorium)", "adani": "Adani 2023 (short-seller report)",
          "pge": "PG&E 2019 (wildfire liability)", "svb": "SVB 2023 (deposit run)"}


def case_paths(case: dict, rets: pd.DataFrame, uni: pd.DataFrame, a: int = -20, b: int = 20) -> dict:
    """Equal-weighted peer abnormal return (vs universe), cumulated and set to 0 at day -1.

    The end value is the days 0-20 cumulative abnormal return; the path before day 0
    shows any run-up or slide before the news (it ends at 0 on day -1).
    """
    dates = rets.index
    d0 = int(dates.searchsorted(pd.Timestamp(case["date"])))
    firm = case["firm"]
    allp = {s for g in case["groups"].values() for s in g} | ({firm} if firm else set())
    peer_cols = [s for s in allp - ({firm} if firm else set()) if s in rets.columns]
    rets = rets.copy()
    rets[peer_cols] = rets[peer_cols].where(rets[peer_cols].abs() <= 0.45)
    u = uni.iloc[d0].copy()
    u[[c for c in allp if c in u.index]] = False
    mkt = rets.loc[:, u.values].mean(axis=1)
    out = {}
    for g, peers in case["groups"].items():
        avail = [s for s in peers if s in rets.columns and rets[s].iloc[d0 - 250:d0].notna().sum() > 100]
        ab = rets[avail].sub(mkt, axis=0).mean(axis=1).iloc[d0 + a:d0 + b + 1].fillna(0)
        cum = pd.Series(ab.cumsum().values, index=range(a, b + 1))
        out[g] = cum - cum.loc[-1]          # anchored: 0 on the day before the news
    return out


def fig1() -> None:
    rus, _ = load(DATA / "extended_prices.parquet", 1.0)
    mus = us_pit_mask(rus)
    rin, _, uin = load_india()
    fig, axes = plt.subplots(2, 4, figsize=(11, 5.2), sharex=True)
    for ax, case in zip(axes.ravel(), CASES):
        rets, uni = (rus, mus) if case["market"] == "US" else (rin, uin)
        paths = case_paths(case, rets, uni)
        for g, p in paths.items():
            dep = case["id"] in DEPENDENT or "Adani group" in g
            col = ORANGE if dep else BLUE
            ax.plot(p.index, p.values * 100, color=col, lw=2, solid_capstyle="round")
            ax.annotate(f"{p.values[-1] * 100:+.0f}%", (p.index[-1], p.values[-1] * 100),
                        xytext=(3, 0), textcoords="offset points", va="center", fontsize=8, color=INK)
        ax.axvline(0, color=INK2, lw=0.8, ls=(0, (2, 2)))
        ax.axhline(0, color=INK2, lw=0.8)
        ax.set_title(TITLES[case["id"]], loc="left")
        ax.set_xlim(-20, 25)
        ax.set_xticks([-20, -10, 0, 10, 20])
    fig.supxlabel("trading days relative to the news (day 0 = first trading day after it was public)",
                  color=INK2, fontsize=9)
    fig.supylabel("peers' cumulative abnormal return (%), set to 0 on the day before the news",
                  color=INK2, fontsize=9)
    handles = [plt.Line2D([], [], color=BLUE, lw=2), plt.Line2D([], [], color=ORANGE, lw=2)]
    fig.legend(handles, ["rivals whose output can replace the failed firm's",
                         "peers that share a dependency (funding, deposits, owner, liability)"],
               loc="upper center", ncol=2, frameon=False, fontsize=9, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(FIG / "fig1_case_paths.png", dpi=200)
    plt.close(fig)


def fig2() -> None:
    m = pd.read_csv(ROOT / "results" / "death_test" / "us_replaceability_map.csv", index_col=0)
    m = m.sort_values("peer_car_d0")
    fig, axes = plt.subplots(1, 2, figsize=(10, 0.32 * len(m) + 1.4), sharey=True)
    y = np.arange(len(m))
    for ax, col, ttl in [(axes[0], "peer_car_d0", "Day 0"), (axes[1], "peer_car_0_20", "Days 0–20")]:
        v = m[col].values * 100
        ax.barh(y, v, color=[RED if x < 0 else BLUE for x in v], height=0.62, edgecolor=SURF, linewidth=1)
        ax.axvline(0, color=INK2, lw=0.8)
        ax.set_title(f"{ttl}: mean peer abnormal return (%)", loc="left")
        ax.grid(axis="y", visible=False)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([f"{s} ({int(n)})" for s, n in zip(m.index, m["n_events"])], fontsize=8)
    fig.text(0.01, 0.005, "US S&P 500, 2000–2024; sub-industries with at least 8 isolated crashes "
             "(number in brackets). Red = rivals fall, blue = rivals gain.", color=INK2, fontsize=7.5)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(FIG / "fig2_replaceability_map.png", dpi=200)
    plt.close(fig)


def fig3() -> None:
    ev = pd.read_csv(ROOT / "results" / "death_test" / "us_events.csv", parse_dates=["date"])
    ev = ev.dropna(subset=["firm_share"])
    ev["terc"] = pd.qcut(ev["firm_share"], 3, labels=False)
    rng = np.random.default_rng(20261111)
    ud, gi = np.unique(ev["date"].values, return_inverse=True)
    fig, axes = plt.subplots(1, 2, figsize=(8, 3.2))
    labels = ["small share", "mid share", "large share"]
    for ax, col, ttl in [(axes[0], "peer_car_d0", "Day 0"), (axes[1], "peer_car_0_20", "Days 0–20")]:
        means = ev.groupby("terc")[col].mean().values * 100
        boots = []
        for _ in range(2000):
            dr = rng.integers(0, len(ud), len(ud))
            idx = np.concatenate([np.where(gi == g)[0] for g in dr])
            boots.append(ev.iloc[idx].groupby("terc")[col].mean().reindex(range(3)).values * 100)
        lo, hi = np.nanpercentile(boots, [2.5, 97.5], axis=0)
        x = np.arange(3)
        ax.bar(x, means, color=BLUE, width=0.55, edgecolor=SURF, linewidth=1)
        ax.errorbar(x, means, yerr=[means - lo, hi - means], fmt="none", ecolor=INK, elinewidth=1, capsize=3)
        for xi, mv in zip(x, means):
            ax.annotate(f"{mv:+.2f}%", (xi + 0.3, mv), ha="left", va="center", fontsize=8, color=INK)
        ax.axhline(0, color=INK2, lw=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_xlim(-0.5, 2.95)
        ax.margins(y=0.12)
        ax.set_title(f"{ttl}: peers' abnormal return (%)", loc="left")
        ax.grid(axis="x", visible=False)
    fig.text(0.01, 0.01, "266 US crashes, by the crashing firm's share of its sub-industry's trading value. "
             "Bars: 95% CIs, bootstrap by date.", color=INK2, fontsize=7.5)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(FIG / "fig3_share_terciles.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    print("figures in", FIG)
