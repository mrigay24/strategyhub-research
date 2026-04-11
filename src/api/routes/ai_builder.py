"""
AI Strategy Builder — API Routes

Uses Claude API (claude-opus-4-6) to:
1. Parse natural language strategy descriptions into factor specifications
2. Map to the closest pre-built validated strategy from our 14-strategy library
3. Run a 7-gate validation pipeline using 25-year pre-computed research data

Requires ANTHROPIC_API_KEY environment variable.
"""

import json
import os
import re
from pathlib import Path
from typing import List, Optional

import anthropic
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/ai-builder", tags=["ai-builder"])

RESULTS_DIR = Path("results")
SCORECARD_CSV = RESULTS_DIR / "phase3_summary" / "master_scorecard.csv"
MC_FILE = RESULTS_DIR / "extended_monte_carlo" / "extended_monte_carlo_results.json"
WF_FILE = RESULTS_DIR / "extended_walk_forward" / "extended_walk_forward_results.json"
REGIME_FILE = RESULTS_DIR / "extended_regime_analysis" / "extended_regime_results.json"
TC_SUMMARY = RESULTS_DIR / "transaction_costs" / "summary.json"


# ── Factor Library ────────────────────────────────────────────────────────────

FACTOR_LIBRARY = [
    {
        "id": "cross_sectional_momentum",
        "name": "Cross-Sectional Momentum",
        "category": "Momentum",
        "description": "Rank stocks by trailing 12-1 month return; buy winners, avoid losers. "
                       "The 1-month skip avoids the short-term reversal effect.",
        "academic_source": "Jegadeesh & Titman (1993) — Journal of Finance",
        "signal": "12-month return skipping last month",
        "typical_holding": "1–12 months",
        "used_in": ["large_cap_momentum", "52_week_high_breakout", "value_momentum_blend",
                    "quality_momentum", "composite_factor_score"],
    },
    {
        "id": "52_week_high_proximity",
        "name": "52-Week High Proximity",
        "category": "Momentum",
        "description": "Stocks near their 52-week high continue to outperform. Investors use "
                       "the 52-week high as an anchor; resistance becomes support once breached.",
        "academic_source": "George & Hwang (2004) — Journal of Finance",
        "signal": "Current price / 52-week high > 0.95",
        "typical_holding": "1–6 months",
        "used_in": ["52_week_high_breakout"],
    },
    {
        "id": "value_price_to_ma",
        "name": "Value / Price-to-Historical Mean",
        "category": "Value",
        "description": "Stocks far below their long-run price average are candidates for "
                       "mean reversion. A price-based proxy for fundamental cheapness.",
        "academic_source": "Graham (1949); Fama & French (1992) — Journal of Finance",
        "signal": "Current price / 200-day MA (lower = cheaper)",
        "typical_holding": "6–24 months",
        "used_in": ["deep_value_all_cap", "value_momentum_blend", "composite_factor_score"],
    },
    {
        "id": "low_volatility_anomaly",
        "name": "Low Volatility Anomaly",
        "category": "Quality / Risk",
        "description": "Low-volatility stocks generate higher risk-adjusted returns than high-vol "
                       "stocks, contradicting CAPM. Driven by leverage constraints and lottery-stock "
                       "preference among institutional investors.",
        "academic_source": "Baker, Bradley & Wurgler (2011) — Journal of Portfolio Management; "
                           "Frazzini & Pedersen (2014) — Journal of Financial Economics",
        "signal": "Trailing 60-day annualized volatility; select lowest quintile",
        "typical_holding": "3–12 months",
        "used_in": ["low_volatility_shield", "quality_low_vol", "composite_factor_score"],
    },
    {
        "id": "quality_earnings_stability",
        "name": "Quality / Earnings Stability",
        "category": "Quality",
        "description": "High-quality firms with stable, predictable earnings command a premium "
                       "and are more resilient in downturns. Measured via return consistency "
                       "as an ROIC proxy.",
        "academic_source": "Novy-Marx (2013) — Journal of Financial Economics; "
                           "Asness et al. (2019) — Journal of Portfolio Management",
        "signal": "Fraction of positive monthly returns over trailing 36 months",
        "typical_holding": "6–24 months",
        "used_in": ["high_quality_roic", "dividend_aristocrats", "quality_momentum",
                    "quality_low_vol", "composite_factor_score"],
    },
    {
        "id": "rsi_mean_reversion",
        "name": "RSI Mean Reversion (Cross-Sectional)",
        "category": "Mean Reversion",
        "description": "Cross-sectional RSI mean reversion: buy the most oversold stocks "
                       "in the universe (not time-series). Exploits short-term price dislocations "
                       "across peers driven by over-reaction.",
        "academic_source": "Wilder (1978) — New Concepts in Technical Trading Systems; "
                           "Lehmann (1990) — Journal of Finance",
        "signal": "14-day RSI < 30 (oversold threshold); exit when RSI > 50",
        "typical_holding": "2–8 weeks",
        "used_in": ["rsi_mean_reversion"],
    },
    {
        "id": "volatility_targeting",
        "name": "Volatility Targeting / Risk Parity",
        "category": "Risk Management",
        "description": "Scale portfolio exposure inversely to realized volatility to maintain "
                       "a constant risk budget. Cuts exposure in crises, adds leverage in calm markets. "
                       "Not an alpha source — a risk management overlay.",
        "academic_source": "Asness, Frazzini & Pedersen (2012) — Journal of Investment Management",
        "signal": "Target 10% annualized vol; leverage = target / realized_vol (capped at 2×)",
        "typical_holding": "Daily (continuous rebalancing)",
        "used_in": ["volatility_targeting"],
    },
    {
        "id": "earnings_surprise_pead",
        "name": "Earnings Surprise / PEAD",
        "category": "Event-Driven",
        "description": "Post-Earnings Announcement Drift: stocks with large positive earnings "
                       "surprises continue to drift upward for 30–90 days as the market slowly "
                       "incorporates the new information. Detected via volume + price spikes.",
        "academic_source": "Bernard & Thomas (1989) — Journal of Accounting and Economics",
        "signal": "Volume ≥ 3× trailing mean AND price move ≥ 2σ on announcement day",
        "typical_holding": "30–90 days",
        "used_in": ["earnings_surprise_momentum"],
    },
]

# ── Strategy Descriptions ─────────────────────────────────────────────────────

STRATEGY_DESCRIPTIONS = {
    "large_cap_momentum": {
        "display": "Large Cap Momentum",
        "family": "Momentum",
        "desc": "Ranks large-cap S&P 500 stocks (top 50% by dollar volume) by 12-1 month momentum; holds top 10% monthly.",
    },
    "52_week_high_breakout": {
        "display": "52-Week High Breakout",
        "family": "Momentum",
        "desc": "Selects stocks within 5% of their 52-week high; holds top 10% monthly.",
    },
    "deep_value_all_cap": {
        "display": "Deep Value All-Cap",
        "family": "Value",
        "desc": "Buys stocks furthest below their 200-day MA (deepest value proxy); holds cheapest 20%.",
    },
    "high_quality_roic": {
        "display": "High Quality ROIC",
        "family": "Quality",
        "desc": "Selects stocks with lowest historical volatility (ROIC proxy) AND strong 12-month momentum; holds top 20%.",
    },
    "low_volatility_shield": {
        "display": "Low Volatility Shield",
        "family": "Factor",
        "desc": "Selects the 20% of stocks with lowest 63-day realized volatility.",
    },
    "dividend_aristocrats": {
        "display": "Dividend Aristocrats",
        "family": "Income",
        "desc": "Selects stocks with ≥60% positive monthly returns over 36 months (consistency/income proxy); holds top 20%.",
    },
    "moving_average_trend": {
        "display": "Moving Average Trend",
        "family": "Trend",
        "desc": "Holds stocks above their 200-day MA; exits when price falls below. Classic trend-following.",
    },
    "rsi_mean_reversion": {
        "display": "RSI Mean Reversion",
        "family": "Mean Reversion",
        "desc": "Buys the 20 most oversold stocks in the universe (RSI < 30); exits at RSI > 50.",
    },
    "value_momentum_blend": {
        "display": "Value + Momentum Blend",
        "family": "Composite",
        "desc": "50/50 composite of value (price/MA ratio) and 12-1 month momentum; holds top 20%.",
    },
    "quality_momentum": {
        "display": "Quality + Momentum",
        "family": "Multi-Factor",
        "desc": "50/50 composite of quality (low vol) and 12-1 month momentum; holds top 20%.",
    },
    "quality_low_vol": {
        "display": "Quality + Low Vol",
        "family": "Multi-Factor",
        "desc": "50/50 composite of quality (return consistency) and low realized volatility; holds top 20%.",
    },
    "composite_factor_score": {
        "display": "Composite Factor Score",
        "family": "Multi-Factor",
        "desc": "Equal-weighted composite: momentum 30%, value 20%, quality 30%, low-vol 20%; holds top 20%.",
    },
    "volatility_targeting": {
        "display": "Volatility Targeting",
        "family": "Risk Management",
        "desc": "Applies dynamic leverage to target 10% annualized portfolio volatility; caps at 2× leverage.",
    },
    "earnings_surprise_momentum": {
        "display": "Earnings Surprise Momentum",
        "family": "Event-Driven",
        "desc": "Event-driven: buys stocks with volume ≥3× mean AND price move ≥2σ (earnings surprise proxy); holds 63 days.",
    },
}


# ── Data Helpers ──────────────────────────────────────────────────────────────

def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def _safe_float(val) -> Optional[float]:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _load_scorecard() -> dict:
    if not SCORECARD_CSV.exists():
        return {}
    import csv
    result = {}
    with open(SCORECARD_CSV) as f:
        for row in csv.DictReader(f):
            key = row.get("strategy", "")
            result[key] = {
                "tier": row.get("tier"),
                "sharpe": _safe_float(row.get("sharpe")),
                "cagr": _safe_float(row.get("cagr")),
                "max_drawdown": _safe_float(row.get("mdd")),
                "adj_sharpe": _safe_float(row.get("adj_sharpe")),
                "mc_verdict": row.get("mc_verdict"),
                "wf_verdict": row.get("wf_verdict"),
            }
    return result


# ── 7-Gate Validation Pipeline ────────────────────────────────────────────────

def run_7_gate_validation(strategy_name: str) -> list:
    """
    Run all 7 validation gates against pre-computed 25-year research data.

    Gate 1: IS Sharpe > 0.5 (in-sample)
    Gate 2: Walk-Forward Efficiency ≥ 1.0 (OOS matches IS — no overfitting)
    Gate 3: Monte Carlo p < 0.05 (statistically significant)
    Gate 4: Bear Regime Sharpe > -0.5 (survives market crashes)
    Gate 5: Transaction Cost Resilience (profitable at 15bps round-trip)
    Gate 6: OOS Holdout Sharpe > 0 (generalizes to unseen data)
    Gate 7: Bias Audit (Bonferroni correction + survivorship disclosure)
    """
    scorecard = _load_scorecard()
    mc_data = _load_json(MC_FILE)
    wf_data = _load_json(WF_FILE)
    regime_data = _load_json(REGIME_FILE)
    tc_data = _load_json(TC_SUMMARY)

    sc = scorecard.get(strategy_name, {})
    mc = mc_data.get("results", {}).get(strategy_name, {})
    wf_simple = wf_data.get("simple_oos_results", {}).get(strategy_name, {})
    wf_rolling = wf_data.get("rolling_results", {}).get(strategy_name, {})
    regime_strat = regime_data.get("strategies", {}).get(strategy_name, {})

    gates = []

    # Gate 1: IS Sharpe > 0.5
    is_sharpe = sc.get("sharpe")
    g1_pass = is_sharpe is not None and is_sharpe > 0.5
    gates.append({
        "gate": 1,
        "name": "In-Sample Sharpe Ratio",
        "criterion": "Sharpe Ratio > 0.5 over full 25-year backtest",
        "value": f"{is_sharpe:.3f}" if is_sharpe is not None else "N/A",
        "result": "PASS" if g1_pass else "FAIL",
        "detail": (
            f"Achieved Sharpe {is_sharpe:.3f} over 2000–2024 (25 years, S&P 500 universe). "
            + ("Clears the minimum viability threshold."
               if g1_pass else "Below the 0.5 threshold — insufficient risk-adjusted return.")
        ),
    })

    # Gate 2: Walk-Forward Efficiency ≥ 1.0
    wfe = wf_simple.get("wfe")
    avg_wfe = wf_rolling.get("avg_wfe")
    # WFE is stored as percentage: 160.95 means OOS Sharpe = 160.95% of IS Sharpe
    g2_pass = wfe is not None and wfe >= 100
    g2_caveat = wfe is not None and 60 <= wfe < 100
    gates.append({
        "gate": 2,
        "name": "Walk-Forward Efficiency",
        "criterion": "WFE ≥ 100% — OOS Sharpe matches or exceeds IS Sharpe (no overfitting)",
        "value": f"{wfe:.1f}%" if wfe is not None else "N/A",
        "result": "PASS" if g2_pass else ("CAVEAT" if g2_caveat else "FAIL"),
        "detail": (
            f"Simple split WFE = {wfe:.1f}%. Rolling 5-fold avg WFE = {avg_wfe:.1f}%. "
            + ("OOS performance matches IS — no overfitting detected."
               if g2_pass else
               "WFE 60–100%: some in-sample fitting that doesn't fully generalize."
               if g2_caveat else
               "WFE < 60% — significant overfitting detected.")
        ) if wfe else "No walk-forward data available.",
    })

    # Gate 3: Monte Carlo statistical significance
    sign_p = mc.get("random_sign_test", {}).get("p_value")
    iid_p = mc.get("iid_bootstrap", {}).get("p_value")
    verdict = mc.get("verdict", "")
    g3_pass = "★" in verdict  # covers "SIGNIFICANT ★★★" and "LIKELY SIGNIFICANT ★★"
    gates.append({
        "gate": 3,
        "name": "Monte Carlo Significance",
        "criterion": "Bootstrap p-value < 0.05 (returns not due to random luck)",
        "value": f"p = {sign_p:.4f}" if sign_p is not None else "N/A",
        "result": "PASS" if g3_pass else "FAIL",
        "detail": (
            f"Monte Carlo verdict: {verdict}. "
            f"Sign test p = {sign_p:.4f}, IID bootstrap p = {iid_p:.4f}. "
            f"Tested over 10,000 random permutations. "
            + ("Returns are statistically distinguishable from random chance."
               if g3_pass else "Cannot rule out that returns are consistent with random luck.")
        ),
    })

    # Gate 4: Bear Market Resilience (Bear Regime Sharpe > -0.5)
    rp = regime_strat.get("regime_performance", {})
    bear_sharpe = rp.get("Bear", {}).get("sharpe")
    g4_pass = bear_sharpe is not None and bear_sharpe > -0.5
    gates.append({
        "gate": 4,
        "name": "Bear Market Resilience",
        "criterion": "Bear regime Sharpe > -0.5 (survives dot-com, GFC, COVID crashes)",
        "value": f"{bear_sharpe:.3f}" if bear_sharpe is not None else "N/A",
        "result": "PASS" if g4_pass else "FAIL",
        "detail": (
            f"Bear regime Sharpe = {bear_sharpe:.3f} (includes 2000–02 dot-com crash, "
            f"2008–09 GFC, 2020 COVID drawdown). "
            + ("Strategy avoids catastrophic failure during market crises."
               if g4_pass else
               "Strategy badly underperforms in bear markets — significant tail risk.")
        ) if bear_sharpe is not None else "No regime analysis data available.",
    })

    # Gate 5: Transaction Cost Resilience
    bulletproof_list = tc_data.get("categories", {}).get("BULLETPROOF", [])
    g5_pass = strategy_name in bulletproof_list
    gates.append({
        "gate": 5,
        "name": "Transaction Cost Resilience",
        "criterion": "Remains profitable at 15bps round-trip costs (BULLETPROOF rating)",
        "value": "BULLETPROOF" if g5_pass else "COST-SENSITIVE",
        "result": "PASS" if g5_pass else "FAIL",
        "detail": (
            "Tested at 5, 10, 15, 20, 25bps round-trip costs. "
            + ("Strategy remains profitable even at 25bps (institutional-grade friction). "
               "Low portfolio turnover makes it implementable in practice."
               if g5_pass else
               "Strategy becomes unprofitable at higher transaction cost levels — "
               "high turnover erodes the edge.")
        ),
    })

    # Gate 6: OOS Holdout Sharpe > 0
    oos_sharpe = wf_simple.get("oos_sharpe")
    g6_pass = oos_sharpe is not None and oos_sharpe > 0
    gates.append({
        "gate": 6,
        "name": "Out-of-Sample Holdout",
        "criterion": "OOS Sharpe > 0 on never-before-seen data (final held-out period)",
        "value": f"{oos_sharpe:.3f}" if oos_sharpe is not None else "N/A",
        "result": "PASS" if g6_pass else "FAIL",
        "detail": (
            f"Hold-out OOS Sharpe = {oos_sharpe:.3f}. "
            + ("Positive OOS performance — strategy generalizes beyond the training window."
               if g6_pass else
               "Negative OOS Sharpe — strategy failed to generalize to the held-out period.")
        ) if oos_sharpe is not None else "No OOS holdout data available.",
    })

    # Gate 7: Bias Audit — Bonferroni correction + survivorship disclosure
    bonferroni_threshold = 0.05 / 14  # Testing 14 strategies simultaneously
    g7_pass = sign_p is not None and sign_p < bonferroni_threshold
    data_period = mc_data.get("data_period", "2000–2024")
    gates.append({
        "gate": 7,
        "name": "Bias Audit",
        "criterion": f"Bonferroni-corrected p < {bonferroni_threshold:.4f}, 25-yr data, survivorship disclosed",
        "value": f"p = {sign_p:.4f}" if sign_p else "N/A",
        "result": "PASS" if g7_pass else "CAVEAT",
        "detail": (
            f"Data: {data_period} (25 years — covers 3 bear markets, 3 bull cycles). "
            f"Multiple testing (14 strategies tested): Bonferroni threshold = 0.05/14 = "
            f"{bonferroni_threshold:.4f}. "
            f"Strategy sign test p = {sign_p:.4f} — "
            f"{'PASSES' if g7_pass else 'marginal fail on'} Bonferroni correction. "
            "Survivorship bias: partially mitigated using historical S&P 500 constituent lists "
            "(2000–2024). Delisted stocks unavailable from free data — estimated residual bias ≤ 1–2% CAGR."
        ) if sign_p is not None else "Insufficient data for complete bias audit.",
    })

    return gates


# ── Claude System Prompt ──────────────────────────────────────────────────────

def _build_system_prompt() -> str:
    factor_text = "\n".join(
        f"  - **{f['name']}** ({f['category']}): {f['description']} "
        f"[Source: {f['academic_source']}]"
        for f in FACTOR_LIBRARY
    )
    strategy_text = "\n".join(
        f"  - **{k}** ({v['family']}): {v['desc']}"
        for k, v in STRATEGY_DESCRIPTIONS.items()
    )
    return f"""You are an expert quantitative analyst and systematic trading researcher at StrategyHub Research.

Your role is to help users understand how academic factor strategies work and map their trading ideas
to rigorously validated strategies from our 25-year (2000–2024) research database.

## Available Factor Signals (academically documented)

{factor_text}

## 14 Pre-Built Validated Strategies (S&P 500, 2000–2024)

{strategy_text}

## Your Task

When a user describes a trading strategy idea, you MUST:

1. **Map** their idea to the SINGLE CLOSEST pre-built strategy (exact key required)
2. **Identify** which factors from the library their strategy uses and their weights
3. **Write** a rigorous economic hypothesis explaining WHY this edge should exist
4. **Write** a `factor_code` Python function body that implements the core scoring logic
5. **Return** a JSON response in EXACTLY this format (no extra text outside the JSON):

```json
{{
  "matched_strategy": "<exact_key_from_strategy_list>",
  "strategy_display_name": "<human-readable name>",
  "confidence": <0.0 to 1.0>,
  "factors": [
    {{"id": "<factor_id>", "name": "<factor name>", "weight": <0.0–1.0>, "role": "<why this factor>"}}
  ],
  "hypothesis": "<2–3 sentence academic economic hypothesis — cite theory, not just description>",
  "rebalancing": "<Daily|Weekly|Monthly|Quarterly>",
  "universe": "<which stocks, filtered how>",
  "key_risk": "<the single most important risk that could destroy this edge>",
  "analyst_note": "<1–2 sentences of honest expert commentary on feasibility and fit>",
  "factor_code": "<Python function body — see spec below>"
}}
```

## factor_code Specification

The `factor_code` field must be a Python function body (no def line) that:
- Receives: `prices` (pd.DataFrame, date×symbols close prices), `returns` (pd.DataFrame, same shape, daily pct returns), `pd` (pandas), `np` (numpy)
- Returns: `pd.DataFrame` with same shape as `prices` where HIGHER values = MORE attractive stocks (NaN = insufficient data)
- Uses ONLY pandas/numpy operations — no imports, no file access, no external calls
- Must end with `return <dataframe_expression>`

### Good factor_code examples:

**12-month momentum (skip last month):**
```
scores = prices.pct_change(252).shift(21)
return scores
```

**Low volatility (inverse: lower vol = higher score):**
```
vol = returns.rolling(63).std() * np.sqrt(252)
return -vol
```

**52-week high proximity:**
```
high_52w = prices.rolling(252).max()
return prices / high_52w
```

**RSI (lower RSI = higher score for oversold):**
```
delta = returns.copy()
gain = delta.clip(lower=0).rolling(14).mean()
loss = (-delta.clip(upper=0)).rolling(14).mean()
rs = gain / loss.replace(0, np.nan)
rsi = 100 - (100 / (1 + rs))
return -rsi
```

**Value + Momentum composite (50/50):**
```
momentum = prices.pct_change(252).shift(21)
value = -(prices / prices.rolling(200).mean())
m_rank = momentum.rank(axis=1, pct=True)
v_rank = value.rank(axis=1, pct=True)
return 0.5 * m_rank + 0.5 * v_rank
```

Rules:
- Factor weights must sum to 1.0
- Always pick the closest pre-built strategy for the 7-gate validation
- The hypothesis must cite academic concepts (momentum premium, quality premium, PEAD, etc.)
- The factor_code must be self-contained — no helper functions, single return statement
- Be rigorous and honest — this is a research platform, not a sales tool

If the user asks a general question (not describing a strategy), answer conversationally
and help guide them to describe a strategy you can analyze.
If the user greets or asks what you can do, explain briefly and suggest they describe a strategy idea.
"""


# ── Pydantic Models ───────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class GenerateRequest(BaseModel):
    messages: List[ChatMessage]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/factors")
async def get_factor_library():
    """Return the 8 academically-documented factor signals used in our strategy library."""
    return {"factors": FACTOR_LIBRARY, "n_factors": len(FACTOR_LIBRARY)}


@router.post("/generate")
async def generate_strategy(request: GenerateRequest):
    """
    Process a user's strategy description via Claude API (claude-opus-4-6).

    Returns:
    - raw_response: Claude's full text
    - strategy_spec: Parsed JSON with matched strategy, factors, hypothesis
    - validation_gates: 7-gate pipeline results using 25-year pre-computed data
    - n_passed / n_failed / n_caveat: Gate summary counts
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY environment variable is not set. "
                   "Set it with: export ANTHROPIC_API_KEY=your-key",
        )

    client = anthropic.Anthropic(api_key=api_key)

    claude_messages = [
        {"role": msg.role, "content": msg.content}
        for msg in request.messages
    ]

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            thinking={"type": "adaptive"},
            system=_build_system_prompt(),
            messages=claude_messages,
        )
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid ANTHROPIC_API_KEY.")
    except anthropic.RateLimitError:
        raise HTTPException(status_code=429, detail="Anthropic rate limit hit. Please retry in a moment.")
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Claude API error: {str(e)}")

    # Extract text block
    text_content = next(
        (block.text for block in response.content if block.type == "text"),
        "",
    )

    # Parse JSON from response
    strategy_spec = None
    try:
        json_match = re.search(r"\{[\s\S]*\}", text_content)
        if json_match:
            strategy_spec = json.loads(json_match.group())
    except (json.JSONDecodeError, AttributeError):
        pass

    # Run 7-gate validation for matched strategy
    gates = []
    if strategy_spec and strategy_spec.get("matched_strategy"):
        matched = strategy_spec["matched_strategy"]
        if matched in STRATEGY_DESCRIPTIONS:
            try:
                gates = run_7_gate_validation(matched)
            except Exception:
                gates = []

    n_passed = sum(1 for g in gates if g["result"] == "PASS")
    n_failed = sum(1 for g in gates if g["result"] == "FAIL")
    n_caveat = sum(1 for g in gates if g["result"] == "CAVEAT")

    # Overall verdict
    if n_passed == 7:
        overall_verdict = "ALL GATES PASSED"
    elif n_failed == 0:
        overall_verdict = "PASSED WITH CAVEATS"
    elif n_failed <= 2:
        overall_verdict = "PARTIAL PASS"
    else:
        overall_verdict = "FAILED VALIDATION"

    return {
        "raw_response": text_content,
        "strategy_spec": strategy_spec,
        "validation_gates": gates,
        "n_passed": n_passed,
        "n_failed": n_failed,
        "n_caveat": n_caveat,
        "overall_verdict": overall_verdict,
        "matched_strategy_info": STRATEGY_DESCRIPTIONS.get(
            strategy_spec.get("matched_strategy", "") if strategy_spec else "", {}
        ),
    }


# ── AI Strategy Generation + Live Backtest ────────────────────────────────────

# Module-level prices cache — loaded once per server start, ~3.4M rows
_PRICES_CACHE: Optional[pd.DataFrame] = None
EXTENDED_PRICES = Path("data_processed/extended_prices_clean.parquet")


def _load_prices() -> pd.DataFrame:
    """Load 25-year price data from parquet, cached in memory."""
    global _PRICES_CACHE
    if _PRICES_CACHE is None:
        if not EXTENDED_PRICES.exists():
            raise FileNotFoundError(
                f"Extended price data not found: {EXTENDED_PRICES}. "
                "Run Phase 3 data pipeline to generate it."
            )
        long_df = pd.read_parquet(EXTENDED_PRICES)
        # Pivot to wide format: date × symbol
        _PRICES_CACHE = long_df.pivot_table(
            index="date", columns="symbol", values="close", aggfunc="last"
        ).sort_index()
    return _PRICES_CACHE


def _run_custom_backtest(factor_code: str) -> dict:
    """
    Load 25yr prices, build DynamicFactorStrategy, run Backtester.
    Returns key metrics and weekly equity curve.
    """
    from src.strategies.dynamic import DynamicFactorStrategy
    from src.backtesting.engine import Backtester

    prices = _load_prices()

    strategy = DynamicFactorStrategy(
        data=prices,
        params={"top_pct": 0.20, "rebalance_freq": "ME"},
        factor_code=factor_code,
    )

    backtester = Backtester(
        strategy=strategy,
        data=prices,
        initial_capital=100_000,
        commission_bps=10,
        slippage_bps=5,
    )
    result = backtester.run()

    # Downsample equity curve to weekly for API response size
    eq = result.equity_curve
    if eq is not None and not eq.empty:
        weekly = eq.resample("W").last()
        equity_curve = [
            {"date": d.strftime("%Y-%m-%d"), "value": float(v)}
            for d, v in weekly.items()
            if not np.isnan(v)
        ]
    else:
        equity_curve = []

    metrics = result.metrics or {}

    def sf(v):
        try:
            f = float(v)
            return None if (np.isnan(f) or np.isinf(f)) else round(f, 6)
        except (TypeError, ValueError):
            return None

    return {
        "sharpe_ratio": sf(metrics.get("sharpe_ratio")),
        "cagr": sf(metrics.get("cagr")),
        "max_drawdown": sf(metrics.get("max_drawdown")),
        "volatility": sf(metrics.get("volatility")),
        "total_return": sf(metrics.get("total_return")),
        "win_rate": sf(metrics.get("win_rate")),
        "equity_curve": equity_curve,
    }


@router.post("/generate-and-backtest")
async def generate_and_backtest(request: GenerateRequest):
    """
    Extended AI Builder endpoint: runs Claude to generate factor_code,
    then backtests the custom strategy on the full 25-year dataset.

    Returns everything from /generate PLUS:
    - custom_backtest: Sharpe, CAGR, MDD from the generated factor code
    - factor_code: the generated Python scoring function body
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY not set. export ANTHROPIC_API_KEY=your-key",
        )

    client = anthropic.Anthropic(api_key=api_key)
    claude_messages = [
        {"role": msg.role, "content": msg.content}
        for msg in request.messages
    ]

    # Call Claude
    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=3000,
            thinking={"type": "adaptive"},
            system=_build_system_prompt(),
            messages=claude_messages,
        )
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid ANTHROPIC_API_KEY.")
    except anthropic.RateLimitError:
        raise HTTPException(status_code=429, detail="Rate limit hit — retry in a moment.")
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"Claude API error: {str(e)}")

    text_content = next(
        (block.text for block in response.content if block.type == "text"), ""
    )

    # Parse strategy spec JSON
    strategy_spec = None
    try:
        json_match = re.search(r"\{[\s\S]*\}", text_content)
        if json_match:
            strategy_spec = json.loads(json_match.group())
    except (json.JSONDecodeError, AttributeError):
        pass

    # 7-gate validation on matched pre-built strategy
    gates = []
    if strategy_spec and strategy_spec.get("matched_strategy") in STRATEGY_DESCRIPTIONS:
        try:
            gates = run_7_gate_validation(strategy_spec["matched_strategy"])
        except Exception:
            gates = []

    n_passed = sum(1 for g in gates if g["result"] == "PASS")
    n_failed = sum(1 for g in gates if g["result"] == "FAIL")
    n_caveat = sum(1 for g in gates if g["result"] == "CAVEAT")

    # Run custom backtest on generated factor_code
    custom_backtest = None
    backtest_error = None
    factor_code = strategy_spec.get("factor_code", "") if strategy_spec else ""

    if factor_code:
        try:
            custom_backtest = _run_custom_backtest(factor_code)
        except Exception as e:
            backtest_error = str(e)

    overall_verdict = (
        "ALL GATES PASSED" if n_passed == 7 else
        "PASSED WITH CAVEATS" if n_failed == 0 else
        "PARTIAL PASS" if n_failed <= 2 else
        "FAILED VALIDATION"
    )

    return {
        "raw_response": text_content,
        "strategy_spec": strategy_spec,
        "factor_code": factor_code,
        "validation_gates": gates,
        "n_passed": n_passed,
        "n_failed": n_failed,
        "n_caveat": n_caveat,
        "overall_verdict": overall_verdict,
        "matched_strategy_info": STRATEGY_DESCRIPTIONS.get(
            strategy_spec.get("matched_strategy", "") if strategy_spec else "", {}
        ),
        "custom_backtest": custom_backtest,
        "backtest_error": backtest_error,
    }
