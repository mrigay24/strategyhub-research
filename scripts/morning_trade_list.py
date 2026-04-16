"""
Morning Trade List — Prop Trading Edition
==========================================
Run each morning before market open to get today's ranked buy list.

Usage:
    .venv/bin/python scripts/morning_trade_list.py

    # Specify account size (default $10,000):
    .venv/bin/python scripts/morning_trade_list.py --account 25000

    # Use specific strategies only:
    .venv/bin/python scripts/morning_trade_list.py --strategies low_volatility_shield rsi_mean_reversion

    # Refresh live signals first, then generate list:
    .venv/bin/python scripts/morning_trade_list.py --refresh

Output:
    - Console: ranked buy list with dollar amounts
    - results/live_signals/morning_trade_list.csv
    - results/live_signals/morning_trade_list.json
"""

import sys
import json
import argparse
import logging
from datetime import datetime, date
from pathlib import Path
from collections import defaultdict
from typing import Optional, List

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

SIGNALS_PATH   = Path("results/live_signals/current_signals.json")
OUTPUT_DIR     = Path("results/live_signals")
DEFAULT_ACCOUNT = 10_000          # $ — change to your prop account size

# Tier 1 strategies (highest Sharpe, most robust from Phase 3 research)
TIER1 = {"low_volatility_shield", "rsi_mean_reversion"}

# Tier 2 strategies (solid, used for confirmation)
TIER2 = {
    "large_cap_momentum", "52_week_high_breakout", "quality_momentum",
    "composite_factor_score", "value_momentum_blend", "quality_low_vol",
}

# All strategies by risk level (for prop firm drawdown management)
STRATEGY_RISK = {
    "low_volatility_shield":      "LOW",
    "rsi_mean_reversion":         "LOW",
    "large_cap_momentum":         "MEDIUM",
    "52_week_high_breakout":      "MEDIUM",
    "quality_momentum":           "MEDIUM",
    "composite_factor_score":     "MEDIUM",
    "value_momentum_blend":       "MEDIUM",
    "quality_low_vol":            "LOW",
    "high_quality_roic":          "LOW",
    "deep_value_all_cap":         "MEDIUM",
    "moving_average_trend":       "MEDIUM",
    "dividend_aristocrats":       "LOW",
    "volatility_targeting":       "LOW",
    "earnings_surprise_momentum": "HIGH",
}

# ── Core Logic ────────────────────────────────────────────────────────────────

def load_signals(path: Path) -> dict:
    """Load most recent signal cache."""
    if not path.exists():
        log.error(f"No signal file found at {path}")
        log.error("Run: .venv/bin/python scripts/generate_live_signals.py")
        sys.exit(1)

    with open(path) as f:
        data = json.load(f)

    age_hours = (datetime.now() - datetime.fromisoformat(data["generated_at"])).total_seconds() / 3600
    if age_hours > 24:
        log.warning(f"Signals are {age_hours:.1f}h old — consider refreshing with --refresh")
    else:
        log.info(f"Signals generated {age_hours:.1f}h ago ({data['signal_date']})")

    return data


def build_consensus_scores(signals: dict, strategy_filter) -> pd.DataFrame:
    """
    Aggregate signals across strategies into a consensus score per stock.

    Scoring:
    - Tier 1 appearance:  3 points
    - Tier 2 appearance:  2 points
    - Tier 3 appearance:  1 point
    - Weight bonus: +0 to +1 point proportional to position weight within strategy
    - n_strategies: count of strategies recommending this stock

    Returns DataFrame sorted by consensus_score descending.
    """
    scores       = defaultdict(float)
    appearances  = defaultdict(int)
    strategies_for = defaultdict(list)
    weights_for  = defaultdict(list)

    strats = signals["strategies"]
    if strategy_filter:
        strats = {k: v for k, v in strats.items() if k in strategy_filter}

    for strat_name, result in strats.items():
        if "error" in result or not result.get("holdings"):
            continue

        holdings = result["holdings"]
        n        = len(holdings)

        for h in holdings:
            sym    = h["symbol"]
            weight = h["weight"]
            rank   = h["rank"]

            # Tier-based base score
            if strat_name in TIER1:
                base = 3.0
            elif strat_name in TIER2:
                base = 2.0
            else:
                base = 1.0

            # Weight bonus (top holding gets +1, last gets +0)
            weight_bonus = weight / (holdings[0]["weight"] + 1e-9)

            scores[sym]         += base + weight_bonus
            appearances[sym]    += 1
            strategies_for[sym].append(strat_name)
            weights_for[sym].append(round(weight, 4))

    if not scores:
        log.error("No valid signals found across any strategy.")
        sys.exit(1)

    rows = []
    for sym, score in scores.items():
        rows.append({
            "symbol":          sym,
            "consensus_score": round(score, 2),
            "n_strategies":    appearances[sym],
            "strategies":      ", ".join(sorted(strategies_for[sym])),
            "avg_weight":      round(float(np.mean(weights_for[sym])), 4),
        })

    df = pd.DataFrame(rows).sort_values("consensus_score", ascending=False).reset_index(drop=True)
    df.index += 1  # 1-based rank
    df.index.name = "rank"
    return df


def add_position_sizing(df: pd.DataFrame, account_size: float, top_n: int = 20) -> pd.DataFrame:
    """
    Add position sizing based on consensus score weighting.

    Uses score-proportional sizing capped at 10% per position.
    Total allocation = 80% of account (20% cash buffer for drawdown protection).
    """
    top = df.head(top_n).copy()

    # Score-proportional weights, capped at 10%
    total_score  = top["consensus_score"].sum()
    raw_weights  = top["consensus_score"] / total_score
    capped       = raw_weights.clip(upper=0.10)
    norm_weights = capped / capped.sum()

    # Apply 80% allocation (keep 20% cash)
    alloc_pct    = (norm_weights * 0.80 * 100).round(1)
    alloc_dollar = (norm_weights * 0.80 * account_size).round(0).astype(int)

    top["allocation_pct"]    = alloc_pct
    top["allocation_dollar"] = alloc_dollar
    return top


def prop_firm_checklist(df: pd.DataFrame, account_size: float) -> dict:
    """
    Generate prop firm risk metrics for FTMO / Apex / TopStep compliance.

    Based on typical challenge rules:
    - FTMO:   Max daily loss 5%, Max total drawdown 10%
    - Apex:   Max daily loss 3%, Max trailing drawdown varies
    - TopStep: Max daily loss 2%, Max trailing drawdown 3-6%
    """
    n_positions     = len(df)
    max_position    = df["allocation_pct"].max()
    total_allocated = df["allocation_pct"].sum()
    cash_buffer     = 100 - total_allocated

    # Estimated max 1-day loss (assuming -3% avg stock move, concentrated in top positions)
    worst_case_day  = max_position * 0.05   # 5% stock drop on largest position
    portfolio_daily = total_allocated / 100 * 0.02  # 2% avg move on full portfolio

    return {
        "n_positions":        n_positions,
        "total_allocated_pct": round(total_allocated, 1),
        "cash_buffer_pct":    round(cash_buffer, 1),
        "max_single_pos_pct": round(max_position, 1),
        "est_max_daily_loss": round(portfolio_daily * 100, 2),
        "ftmo_safe":          bool(portfolio_daily < 0.045),
        "apex_safe":          bool(portfolio_daily < 0.025),
        "topstep_safe":       bool(portfolio_daily < 0.018),
    }


def print_trade_list(df: pd.DataFrame, signals_meta: dict,
                     account_size: float, risk_metrics: dict) -> None:
    """Print formatted morning trade list to console."""

    today = date.today().strftime("%B %d, %Y")
    sep   = "─" * 72

    print(f"\n{'═' * 72}")
    print(f"  STRATEGYHUB — MORNING TRADE LIST")
    print(f"  {today}  |  Account: ${account_size:,.0f}  |  Signal Date: {signals_meta['signal_date']}")
    print(f"{'═' * 72}\n")

    # Prop firm compatibility
    print("  PROP FIRM COMPATIBILITY")
    print(sep)
    ftmo    = "✅ SAFE" if risk_metrics["ftmo_safe"]    else "⚠️  RISK"
    apex    = "✅ SAFE" if risk_metrics["apex_safe"]    else "⚠️  RISK"
    topstep = "✅ SAFE" if risk_metrics["topstep_safe"] else "⚠️  RISK"
    print(f"  FTMO (5% daily limit):     {ftmo}")
    print(f"  Apex (3% daily limit):     {apex}")
    print(f"  TopStep (2% daily limit):  {topstep}")
    print(f"  Estimated max daily loss:  {risk_metrics['est_max_daily_loss']:.2f}%")
    print(f"  Cash buffer:               {risk_metrics['cash_buffer_pct']}%")
    print()

    # Trade list
    print("  TOP BUY CANDIDATES  (consensus-ranked)")
    print(sep)
    print(f"  {'#':>3}  {'SYMBOL':<8}  {'SCORE':>6}  {'STRATEGIES':>3}  {'ALLOC%':>6}  {'AMOUNT':>8}  CONFIRMED BY")
    print(sep)

    for rank, row in df.iterrows():
        strat_count = row["n_strategies"]
        tier_badge  = "★★" if strat_count >= 5 else ("★ " if strat_count >= 3 else "  ")
        print(
            f"  {rank:>3}  {row['symbol']:<8}  {row['consensus_score']:>6.1f}  "
            f"  {strat_count:>2}   {tier_badge}  {row['allocation_pct']:>5.1f}%  "
            f"${row['allocation_dollar']:>7,}  {row['strategies'][:40]}"
        )

    print(sep)
    print(f"  Total deployed: {risk_metrics['total_allocated_pct']}% (${account_size * risk_metrics['total_allocated_pct'] / 100:,.0f})")
    print(f"  Cash reserve:   {risk_metrics['cash_buffer_pct']}% (${account_size * risk_metrics['cash_buffer_pct'] / 100:,.0f})")
    print(f"\n  Signals source: {signals_meta['data_source']} | Universe: {signals_meta['n_symbols']} stocks")
    print(f"{'═' * 72}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Morning trade list for prop trading")
    parser.add_argument("--account",    type=float, default=DEFAULT_ACCOUNT,
                        help=f"Account size in USD (default: {DEFAULT_ACCOUNT:,})")
    parser.add_argument("--top",        type=int,   default=20,
                        help="Number of top stocks to show (default: 20)")
    parser.add_argument("--strategies", nargs="+",  default=None,
                        help="Filter to specific strategies only")
    parser.add_argument("--refresh",    action="store_true",
                        help="Re-run generate_live_signals.py before building list")
    args = parser.parse_args()

    # Optionally refresh signals
    if args.refresh:
        log.info("Refreshing live signals first...")
        import subprocess
        subprocess.run([sys.executable, "scripts/generate_live_signals.py"], check=True)

    # Load signals
    data = load_signals(SIGNALS_PATH)

    # Build consensus
    log.info("Building consensus scores across strategies...")
    df = build_consensus_scores(data, args.strategies)

    # Position sizing
    df_sized = add_position_sizing(df, args.account, top_n=args.top)

    # Risk metrics
    risk = prop_firm_checklist(df_sized, args.account)

    # Print
    print_trade_list(df_sized, data, args.account, risk)

    # Save outputs
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = OUTPUT_DIR / "morning_trade_list.csv"
    df_sized.to_csv(csv_path)
    log.info(f"Saved CSV → {csv_path}")

    json_path = OUTPUT_DIR / "morning_trade_list.json"
    out = {
        "generated_at":  datetime.now().isoformat(),
        "signal_date":   data["signal_date"],
        "account_size":  args.account,
        "risk_metrics":  risk,
        "trade_list":    df_sized.reset_index().to_dict(orient="records"),
    }
    with open(json_path, "w") as f:
        json.dump(out, f, indent=2)
    log.info(f"Saved JSON → {json_path}")


if __name__ == "__main__":
    main()
