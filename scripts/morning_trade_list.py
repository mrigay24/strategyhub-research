"""
Morning Trade List — Prop Trading Edition
==========================================
Run each morning before market open to get today's ranked buy list.

Usage:
    .venv/bin/python scripts/morning_trade_list.py

    # Specify account size (default $10,000):
    .venv/bin/python scripts/morning_trade_list.py --account 25000

    # Refresh live signals first, then generate list:
    .venv/bin/python scripts/morning_trade_list.py --refresh

    # Use specific strategies only:
    .venv/bin/python scripts/morning_trade_list.py --strategies low_volatility_shield rsi_mean_reversion

Output:
    - Console: ranked buy list with earnings flags, sector warnings, sentiment
    - results/live_signals/morning_trade_list.csv
    - results/live_signals/morning_trade_list.json
"""

import sys
import json
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import defaultdict

import pandas as pd
import numpy as np
import yfinance as yf

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

SIGNALS_PATH    = Path("results/live_signals/current_signals.json")
OUTPUT_DIR      = Path("results/live_signals")
DEFAULT_ACCOUNT = 10_000

TIER1 = {"low_volatility_shield", "rsi_mean_reversion"}
TIER2 = {
    "large_cap_momentum", "52_week_high_breakout", "quality_momentum",
    "composite_factor_score", "value_momentum_blend", "quality_low_vol",
}

# Sector concentration threshold — warn if any sector > this % of portfolio
SECTOR_WARN_PCT = 40.0
EARNINGS_WINDOW = 3   # days ahead to check for earnings
NEWS_LOOKBACK   = 5   # most recent N headlines per stock

POSITIVE_WORDS = {
    "beat", "beats", "surge", "surges", "record", "growth", "strong",
    "upgrade", "upgraded", "outperform", "raised", "raises", "higher",
    "gain", "gains", "rally", "rallies", "bullish", "expands", "profit",
    "revenue", "dividend", "buyback", "approval", "approved",
}
NEGATIVE_WORDS = {
    "miss", "misses", "fall", "falls", "decline", "loss", "losses",
    "weak", "downgrade", "downgraded", "underperform", "cut", "cuts",
    "lower", "drop", "drops", "crash", "bearish", "lawsuit", "sued",
    "investigation", "recall", "warning", "layoff", "layoffs", "bankruptcy",
}

# ── Signal Loading ─────────────────────────────────────────────────────────────

def load_signals(path: Path) -> dict:
    if not path.exists():
        log.error(f"No signal file found at {path}")
        log.error("Run: .venv/bin/python scripts/generate_live_signals.py")
        sys.exit(1)
    with open(path) as f:
        data = json.load(f)
    age_hours = (datetime.now() - datetime.fromisoformat(data["generated_at"])).total_seconds() / 3600
    if age_hours > 24:
        log.warning(f"Signals are {age_hours:.1f}h old — consider --refresh")
    else:
        log.info(f"Signals from {age_hours:.1f}h ago  ({data['signal_date']})")
    return data


# ── Consensus Scoring ─────────────────────────────────────────────────────────

def build_consensus_scores(signals: dict, strategy_filter) -> pd.DataFrame:
    scores, appearances, strategies_for, weights_for = (
        defaultdict(float), defaultdict(int),
        defaultdict(list), defaultdict(list),
    )
    strats = signals["strategies"]
    if strategy_filter:
        strats = {k: v for k, v in strats.items() if k in strategy_filter}

    for strat_name, result in strats.items():
        if "error" in result or not result.get("holdings"):
            continue
        holdings = result["holdings"]
        for h in holdings:
            sym  = h["symbol"]
            base = 3.0 if strat_name in TIER1 else (2.0 if strat_name in TIER2 else 1.0)
            weight_bonus = h["weight"] / (holdings[0]["weight"] + 1e-9)
            scores[sym]          += base + weight_bonus
            appearances[sym]     += 1
            strategies_for[sym].append(strat_name)
            weights_for[sym].append(round(h["weight"], 4))

    if not scores:
        log.error("No valid signals found.")
        sys.exit(1)

    rows = [
        {
            "symbol":          sym,
            "consensus_score": round(score, 2),
            "n_strategies":    appearances[sym],
            "strategies":      ", ".join(sorted(strategies_for[sym])),
            "avg_weight":      round(float(np.mean(weights_for[sym])), 4),
        }
        for sym, score in scores.items()
    ]
    df = pd.DataFrame(rows).sort_values("consensus_score", ascending=False).reset_index(drop=True)
    df.index += 1
    df.index.name = "rank"
    return df


# ── 1. EARNINGS FILTER ────────────────────────────────────────────────────────

def _check_earnings(sym: str, today: date, cutoff: date):
    """Return sym if it reports earnings within the window, else None."""
    try:
        cal = yf.Ticker(sym).calendar
        if cal is None:
            return None
        # Newer yfinance returns dict, older returns DataFrame
        if isinstance(cal, dict):
            dates = cal.get("Earnings Date", [])
            if not hasattr(dates, "__iter__"):
                dates = [dates]
        else:
            if "Earnings Date" in cal.columns:
                dates = cal["Earnings Date"].dropna().tolist()
            elif not cal.empty:
                dates = cal.iloc[0].dropna().tolist()
            else:
                return None

        for ed in dates:
            if hasattr(ed, "date"):
                ed = ed.date()
            elif isinstance(ed, str):
                ed = date.fromisoformat(ed[:10])
            if today <= ed <= cutoff:
                return sym
    except Exception:
        pass
    return None


def get_earnings_blacklist(symbols: list, window_days: int = EARNINGS_WINDOW) -> set:
    """Return set of symbols reporting earnings within next N days."""
    today  = date.today()
    cutoff = today + timedelta(days=window_days)
    blacklist = set()

    log.info(f"Checking earnings calendars for {len(symbols)} symbols (next {window_days} days)...")
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(_check_earnings, sym, today, cutoff): sym for sym in symbols}
        for fut in as_completed(futures):
            result = fut.result()
            if result:
                blacklist.add(result)

    if blacklist:
        log.warning(f"Earnings blacklist ({len(blacklist)}): {', '.join(sorted(blacklist))}")
    else:
        log.info("No earnings in the next 3 days for top candidates ✓")
    return blacklist


# ── 2. SECTOR CONCENTRATION ───────────────────────────────────────────────────

def _fetch_sector(sym: str):
    try:
        info = yf.Ticker(sym).info
        return sym, info.get("sector", "Unknown")
    except Exception:
        return sym, "Unknown"


def get_sector_data(symbols: list) -> dict:
    """Return {symbol: sector} for all symbols."""
    log.info(f"Fetching sector data for {len(symbols)} symbols...")
    sectors = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        for sym, sector in ex.map(_fetch_sector, symbols):
            sectors[sym] = sector
    return sectors


def check_sector_concentration(df: pd.DataFrame, sectors: dict) -> dict:
    """
    Return sector breakdown by portfolio allocation %.
    Flags any sector above SECTOR_WARN_PCT.
    """
    df = df.copy()
    df["sector"] = df["symbol"].map(sectors).fillna("Unknown")
    breakdown = (
        df.groupby("sector")["allocation_pct"]
        .sum()
        .sort_values(ascending=False)
        .round(1)
        .to_dict()
    )
    warnings = {s: pct for s, pct in breakdown.items() if pct >= SECTOR_WARN_PCT}
    return {"breakdown": breakdown, "warnings": warnings}


# ── 3. NEWS SENTIMENT ─────────────────────────────────────────────────────────

def _fetch_sentiment(sym: str):
    """Score a symbol's recent news headlines. Returns (sym, score, headlines)."""
    try:
        news = yf.Ticker(sym).news
        if not news:
            return sym, 0.0, []

        total, count = 0, 0
        headlines = []
        for article in news[:NEWS_LOOKBACK]:
            title = article.get("title", "").lower()
            if not title:
                continue
            pos = sum(1 for w in POSITIVE_WORDS if w in title)
            neg = sum(1 for w in NEGATIVE_WORDS if w in title)
            total += pos - neg
            count += 1
            headlines.append(article.get("title", ""))

        score = round(total / max(count, 1), 2)
        return sym, score, headlines[:3]
    except Exception:
        return sym, 0.0, []


def get_news_sentiment(symbols: list) -> dict:
    """Return {symbol: {score, headlines}} for all symbols."""
    log.info(f"Fetching news sentiment for {len(symbols)} symbols...")
    sentiment = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        for sym, score, headlines in ex.map(_fetch_sentiment, symbols):
            sentiment[sym] = {"score": score, "headlines": headlines}
    return sentiment


# ── Position Sizing ───────────────────────────────────────────────────────────

def add_position_sizing(df: pd.DataFrame, account_size: float, top_n: int = 20) -> pd.DataFrame:
    top          = df.head(top_n).copy()
    total_score  = top["consensus_score"].sum()
    raw_weights  = top["consensus_score"] / total_score
    capped       = raw_weights.clip(upper=0.10)
    norm_weights = capped / capped.sum()
    top["allocation_pct"]    = (norm_weights * 0.80 * 100).round(1)
    top["allocation_dollar"] = (norm_weights * 0.80 * account_size).round(0).astype(int)
    return top


# ── Prop Firm Risk Check ──────────────────────────────────────────────────────

def prop_firm_checklist(df: pd.DataFrame) -> dict:
    total_allocated = df["allocation_pct"].sum()
    portfolio_daily = total_allocated / 100 * 0.02
    return {
        "n_positions":         len(df),
        "total_allocated_pct": round(total_allocated, 1),
        "cash_buffer_pct":     round(100 - total_allocated, 1),
        "max_single_pos_pct":  round(df["allocation_pct"].max(), 1),
        "est_max_daily_loss":  round(portfolio_daily * 100, 2),
        "ftmo_safe":           bool(portfolio_daily < 0.045),
        "apex_safe":           bool(portfolio_daily < 0.025),
        "topstep_safe":        bool(portfolio_daily < 0.018),
    }


# ── Output ────────────────────────────────────────────────────────────────────

def sentiment_label(score: float) -> str:
    if score >= 1.0:   return "📈 POS"
    if score <= -1.0:  return "📉 NEG"
    return "  ─  "


def print_trade_list(df: pd.DataFrame, signals_meta: dict, account_size: float,
                     risk: dict, earnings_bl: set, sector_info: dict,
                     sentiment: dict) -> None:
    today = date.today().strftime("%B %d, %Y")
    sep   = "─" * 80

    print(f"\n{'═' * 80}")
    print(f"  STRATEGYHUB — MORNING TRADE LIST")
    print(f"  {today}  |  Account: ${account_size:,.0f}  |  Signal Date: {signals_meta['signal_date']}")
    print(f"{'═' * 80}\n")

    # ── Prop firm safety ──
    print("  PROP FIRM COMPATIBILITY")
    print(sep)
    print(f"  FTMO    (5% daily limit):   {'✅ SAFE' if risk['ftmo_safe']    else '⚠️  RISK'}")
    print(f"  Apex    (3% daily limit):   {'✅ SAFE' if risk['apex_safe']    else '⚠️  RISK'}")
    print(f"  TopStep (2% daily limit):   {'✅ SAFE' if risk['topstep_safe'] else '⚠️  RISK'}")
    print(f"  Est. max daily loss:  {risk['est_max_daily_loss']:.2f}%   |   Cash buffer: {risk['cash_buffer_pct']}%")
    print()

    # ── Sector concentration ──
    print("  SECTOR CONCENTRATION")
    print(sep)
    for sector, pct in sector_info["breakdown"].items():
        warn = "  ⚠️  CONCENTRATED" if pct >= SECTOR_WARN_PCT else ""
        print(f"  {sector:<30}  {pct:>5.1f}%{warn}")
    print()

    # ── Trade list ──
    print("  TOP BUY CANDIDATES")
    print(sep)
    print(f"  {'#':>3}  {'SYMBOL':<7}  {'SCORE':>6}  {'N':>2}  {'ALLOC%':>6}  {'$AMOUNT':>8}  {'SENT':>6}  STATUS")
    print(sep)

    for rank, row in df.iterrows():
        sym          = row["symbol"]
        n            = row["n_strategies"]
        badge        = "★★" if n >= 5 else ("★ " if n >= 3 else "  ")
        sent         = sentiment.get(sym, {}).get("score", 0.0)
        sent_lbl     = sentiment_label(sent)
        earnings_flag = "  ⚠️ EARNINGS" if sym in earnings_bl else ""

        print(
            f"  {rank:>3}  {sym:<7}  {row['consensus_score']:>6.1f}  "
            f"{n:>2} {badge}  {row['allocation_pct']:>5.1f}%  "
            f"${row['allocation_dollar']:>7,}  {sent_lbl}{earnings_flag}"
        )

    print(sep)
    print(f"  Deployed: {risk['total_allocated_pct']}% (${account_size * risk['total_allocated_pct'] / 100:,.0f})"
          f"   |   Cash: {risk['cash_buffer_pct']}% (${account_size * risk['cash_buffer_pct'] / 100:,.0f})")
    print(f"  Universe: {signals_meta['n_symbols']} stocks  |  Source: {signals_meta['data_source']}")

    # ── Earnings warnings ──
    if earnings_bl:
        print()
        print(f"  ⚠️  EARNINGS WARNING — avoid these until after report:")
        for sym in sorted(earnings_bl):
            print(f"     {sym}")

    # ── News highlights ──
    print()
    print("  RECENT NEWS (top 5 stocks)")
    print(sep)
    shown = 0
    for rank, row in df.iterrows():
        if shown >= 5:
            break
        sym      = row["symbol"]
        headlines = sentiment.get(sym, {}).get("headlines", [])
        score     = sentiment.get(sym, {}).get("score", 0.0)
        if headlines:
            print(f"  {sym} (sentiment: {score:+.1f})")
            for h in headlines:
                print(f"    • {h[:75]}")
        shown += 1

    print(f"\n{'═' * 80}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Morning trade list for prop trading")
    parser.add_argument("--account",    type=float, default=DEFAULT_ACCOUNT)
    parser.add_argument("--top",        type=int,   default=20)
    parser.add_argument("--strategies", nargs="+",  default=None)
    parser.add_argument("--refresh",    action="store_true",
                        help="Pull fresh Yahoo Finance data before building list")
    args = parser.parse_args()

    if args.refresh:
        log.info("Refreshing live signals...")
        import subprocess
        subprocess.run([sys.executable, "scripts/generate_live_signals.py"], check=True)

    # ── Load & score ──
    data     = load_signals(SIGNALS_PATH)
    df       = build_consensus_scores(data, args.strategies)
    df_sized = add_position_sizing(df, args.account, top_n=args.top)
    risk     = prop_firm_checklist(df_sized)

    symbols  = df_sized["symbol"].tolist()

    # ── Enrich in parallel (earnings + sectors + sentiment) ──
    log.info("Enriching with earnings / sector / news data...")
    with ThreadPoolExecutor(max_workers=3) as ex:
        fut_earnings  = ex.submit(get_earnings_blacklist, symbols)
        fut_sectors   = ex.submit(get_sector_data, symbols)
        fut_sentiment = ex.submit(get_news_sentiment, symbols)

        earnings_bl  = fut_earnings.result()
        sectors      = fut_sectors.result()
        sentiment    = fut_sentiment.result()

    sector_info = check_sector_concentration(df_sized, sectors)

    # ── Print ──
    print_trade_list(df_sized, data, args.account, risk,
                     earnings_bl, sector_info, sentiment)

    # ── Save ──
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df_sized["sector"]    = df_sized["symbol"].map(sectors).fillna("Unknown")
    df_sized["sentiment"] = df_sized["symbol"].map(
        lambda s: sentiment.get(s, {}).get("score", 0.0)
    )
    df_sized["earnings_warning"] = df_sized["symbol"].isin(earnings_bl)
    df_sized.to_csv(OUTPUT_DIR / "morning_trade_list.csv")

    out = {
        "generated_at":     datetime.now().isoformat(),
        "signal_date":      data["signal_date"],
        "account_size":     args.account,
        "risk_metrics":     risk,
        "sector_breakdown": sector_info["breakdown"],
        "sector_warnings":  list(sector_info["warnings"].keys()),
        "earnings_warning": sorted(earnings_bl),
        "trade_list":       df_sized.reset_index().to_dict(orient="records"),
    }
    with open(OUTPUT_DIR / "morning_trade_list.json", "w") as f:
        json.dump(out, f, indent=2, default=str)

    log.info(f"Saved → {OUTPUT_DIR}/morning_trade_list.{{csv,json}}")


if __name__ == "__main__":
    main()
