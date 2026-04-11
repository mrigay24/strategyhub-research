'use client';

import { useState, useEffect, useCallback } from 'react';
import { fetchDashboardData, StrategyBacktest, BenchmarkData } from '@/lib/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Map backend strategy names to frontend display info
const STRATEGY_DISPLAY_INFO: Record<string, {
  displayName: string;
  family: string;
  factorTags: string[];
  riskProfile: string;
  horizon: string;
  rebalanceFrequency: string;
  marketCaps: string[];
  overview: {
    concept: string;
    worksWellWhen: string;
    strugglesWhen: string;
    typicalHoldings: number;
    universe: string;
    liquidityProfile: string;
  };
  rules: { stepNumber: number; title: string; description: string }[];
}> = {
  large_cap_momentum: {
    displayName: 'Large Cap Momentum',
    family: 'Momentum Strategies',
    factorTags: ['Momentum'],
    riskProfile: 'High Risk',
    horizon: 'Medium',
    rebalanceFrequency: 'Monthly',
    marketCaps: ['Large Cap'],
    overview: {
      concept: 'Selects the top decile of large-cap stocks by 12-month trailing momentum (skipping the most recent month to avoid short-term reversal). Based on Jegadeesh & Titman (1993).',
      worksWellWhen: 'Sustained bull markets with clear sector leadership and trending conditions.',
      strugglesWhen: 'Sharp momentum reversals, market crashes, and rotation-heavy environments.',
      typicalHoldings: 50,
      universe: 'S&P 500 (large-cap filtered)',
      liquidityProfile: 'Highly liquid large-cap stocks only.',
    },
    rules: [
      { stepNumber: 1, title: 'Filter Universe', description: 'Select top 50% of stocks by dollar volume (large-cap proxy).' },
      { stepNumber: 2, title: 'Rank by Momentum', description: 'Calculate 12-month return, skip last 21 days.' },
      { stepNumber: 3, title: 'Select Winners', description: 'Go long the top 10% by momentum, equal-weighted.' },
    ],
  },
  '52_week_high_breakout': {
    displayName: '52-Week High Breakout',
    family: 'Momentum Strategies',
    factorTags: ['Momentum'],
    riskProfile: 'High Risk',
    horizon: 'Medium',
    rebalanceFrequency: 'Monthly',
    marketCaps: ['Large Cap', 'Mid Cap', 'Small Cap'],
    overview: {
      concept: 'Goes long stocks trading near their 52-week high. Based on George & Hwang (2004) — investors anchor to the 52-week high, causing underreaction to positive news.',
      worksWellWhen: 'Broad market uptrends with many stocks making new highs.',
      strugglesWhen: 'Bear markets and sharp corrections when breakouts fail.',
      typicalHoldings: 50,
      universe: 'S&P 500',
      liquidityProfile: 'All-cap stocks near their highs.',
    },
    rules: [
      { stepNumber: 1, title: 'Calculate Proximity', description: 'Ratio of current price to 252-day rolling high.' },
      { stepNumber: 2, title: 'Rank Stocks', description: 'Rank all stocks by proximity to 52-week high.' },
      { stepNumber: 3, title: 'Select Top Decile', description: 'Go long the top 10% closest to their highs.' },
    ],
  },
  deep_value_all_cap: {
    displayName: 'Deep Value All-Cap',
    family: 'Value Strategies',
    factorTags: ['Value'],
    riskProfile: 'High Risk',
    horizon: 'Long',
    rebalanceFrequency: 'Quarterly',
    marketCaps: ['Large Cap', 'Mid Cap', 'Small Cap'],
    overview: {
      concept: 'Identifies the cheapest stocks using contrarian signals: beaten-down prices and low price-to-moving-average ratios. A proxy for traditional P/E and P/B value investing.',
      worksWellWhen: 'Value rotations, economic recoveries, and mean-reversion environments.',
      strugglesWhen: 'Growth-driven markets and prolonged "value trap" environments.',
      typicalHoldings: 100,
      universe: 'S&P 500 (all caps)',
      liquidityProfile: 'Broad market with contrarian tilt.',
    },
    rules: [
      { stepNumber: 1, title: 'Contrarian Signal', description: 'Rank by negative 12-month momentum (most beaten-down = cheapest).' },
      { stepNumber: 2, title: 'Price/MA Ratio', description: 'Rank by distance below 200-day moving average.' },
      { stepNumber: 3, title: 'Select Cheapest', description: 'Go long the cheapest 20% by composite value score.' },
    ],
  },
  high_quality_roic: {
    displayName: 'High Quality ROIC',
    family: 'Quality Strategies',
    factorTags: ['Quality'],
    riskProfile: 'Low Risk',
    horizon: 'Long',
    rebalanceFrequency: 'Quarterly',
    marketCaps: ['Large Cap', 'Mid Cap'],
    overview: {
      concept: 'Selects the highest quality stocks using price-derived proxies for profitability and stability: low volatility, high risk-adjusted returns, and low max drawdown.',
      worksWellWhen: 'Risk-off environments, late-cycle markets, and flight-to-quality periods.',
      strugglesWhen: 'Speculative rallies where low-quality, high-beta stocks outperform.',
      typicalHoldings: 100,
      universe: 'S&P 500',
      liquidityProfile: 'Stable, established companies with consistent performance.',
    },
    rules: [
      { stepNumber: 1, title: 'Stability Score', description: 'Low trailing volatility (proxy for earnings stability).' },
      { stepNumber: 2, title: 'Risk-Adjusted Return', description: 'High Sharpe-like ratio (momentum / volatility).' },
      { stepNumber: 3, title: 'Resilience Filter', description: 'Low max drawdown over lookback period.' },
    ],
  },
  low_volatility_shield: {
    displayName: 'Low Volatility Shield',
    family: 'Factor Strategies',
    factorTags: ['Low Volatility'],
    riskProfile: 'Low Risk',
    horizon: 'Long',
    rebalanceFrequency: 'Monthly',
    marketCaps: ['Large Cap', 'Mid Cap'],
    overview: {
      concept: 'Exploits the low volatility anomaly — lower risk stocks have historically delivered comparable or better risk-adjusted returns. Weights by inverse volatility for tilt toward the calmest stocks.',
      worksWellWhen: 'Bear markets, corrections, and high-uncertainty environments.',
      strugglesWhen: 'Strong bull markets when high-beta stocks surge ahead.',
      typicalHoldings: 100,
      universe: 'S&P 500',
      liquidityProfile: 'Defensive, stable stocks with low price fluctuation.',
    },
    rules: [
      { stepNumber: 1, title: 'Calculate Volatility', description: '63-day trailing annualized volatility.' },
      { stepNumber: 2, title: 'Select Low Vol', description: 'Pick lowest 20% by volatility.' },
      { stepNumber: 3, title: 'Weight by Inv Vol', description: 'Inverse-volatility weighting (calmer stocks get more weight).' },
    ],
  },
  dividend_aristocrats: {
    displayName: 'Dividend Aristocrats',
    family: 'Income Strategies',
    factorTags: ['Value', 'Quality'],
    riskProfile: 'Low Risk',
    horizon: 'Long',
    rebalanceFrequency: 'Quarterly',
    marketCaps: ['Large Cap'],
    overview: {
      concept: 'Targets stocks with the most consistent positive returns — a proxy for reliable dividend growers. Combines return consistency with low monthly volatility.',
      worksWellWhen: 'Income-focused markets, rising rate environments, and quality rotations.',
      strugglesWhen: 'Growth-dominated markets where speculative stocks lead.',
      typicalHoldings: 100,
      universe: 'S&P 500',
      liquidityProfile: 'Established large-caps with stable cash flows.',
    },
    rules: [
      { stepNumber: 1, title: 'Consistency Score', description: 'Count positive monthly returns over 36 months.' },
      { stepNumber: 2, title: 'Stability Filter', description: 'Low monthly return volatility.' },
      { stepNumber: 3, title: 'Select Top Quintile', description: 'Go long stocks with highest composite consistency score.' },
    ],
  },
  moving_average_trend: {
    displayName: 'Moving Average Trend',
    family: 'Trend Strategies',
    factorTags: ['Momentum'],
    riskProfile: 'Medium Risk',
    horizon: 'Medium',
    rebalanceFrequency: 'Monthly',
    marketCaps: ['Large Cap', 'Mid Cap', 'Small Cap'],
    overview: {
      concept: 'Simple but powerful trend filter — go long stocks trading above their 200-day moving average. Equal-weights all stocks in an uptrend. Based on Meb Faber\'s "Ivy Portfolio" approach.',
      worksWellWhen: 'Broad bull markets where most stocks are trending up.',
      strugglesWhen: 'Whipsaw markets with frequent trend changes and false breakouts.',
      typicalHoldings: 250,
      universe: 'S&P 500',
      liquidityProfile: 'Broad market participation in uptrending stocks.',
    },
    rules: [
      { stepNumber: 1, title: 'Calculate 200-Day MA', description: 'Simple moving average for each stock.' },
      { stepNumber: 2, title: 'Trend Filter', description: 'Stock is "in uptrend" if price > 200-day MA.' },
      { stepNumber: 3, title: 'Equal Weight', description: 'Equal-weight all stocks currently in uptrend.' },
    ],
  },
  rsi_mean_reversion: {
    displayName: 'RSI Mean Reversion',
    family: 'Mean Reversion Strategies',
    factorTags: ['Momentum'],
    riskProfile: 'High Risk',
    horizon: 'Short',
    rebalanceFrequency: 'Weekly',
    marketCaps: ['Large Cap', 'Mid Cap'],
    overview: {
      concept: 'Cross-sectional RSI strategy that buys the most oversold stocks (RSI < 30) across the entire S&P 500 universe and exits when RSI recovers above 50.',
      worksWellWhen: 'Volatile, range-bound markets with frequent oversold bounces.',
      strugglesWhen: 'Sustained bear markets where oversold stocks keep falling.',
      typicalHoldings: 20,
      universe: 'S&P 500',
      liquidityProfile: 'Temporarily depressed stocks with recovery potential.',
    },
    rules: [
      { stepNumber: 1, title: 'Calculate RSI', description: '14-day RSI for all 500+ stocks.' },
      { stepNumber: 2, title: 'Buy Oversold', description: 'Go long stocks with RSI below 30.' },
      { stepNumber: 3, title: 'Exit on Recovery', description: 'Sell when RSI rises above 50.' },
    ],
  },
  value_momentum_blend: {
    displayName: 'Value + Momentum Blend',
    family: 'Composite Strategies',
    factorTags: ['Value', 'Momentum'],
    riskProfile: 'Medium Risk',
    horizon: 'Medium',
    rebalanceFrequency: 'Monthly',
    marketCaps: ['Large Cap', 'Mid Cap'],
    overview: {
      concept: 'Blends value and momentum — two negatively correlated factors — for diversification. Avoids "value traps" by requiring positive momentum alongside cheap valuations. Based on Asness et al. (2013).',
      worksWellWhen: 'Markets with clear factor differentiation and moderate trends.',
      strugglesWhen: 'Factor crowding, extreme momentum crashes, or deep value selloffs.',
      typicalHoldings: 100,
      universe: 'S&P 500',
      liquidityProfile: 'Diversified blend of cheap and trending stocks.',
    },
    rules: [
      { stepNumber: 1, title: 'Momentum Score', description: '12-month return (skip last month).' },
      { stepNumber: 2, title: 'Value Score', description: 'Contrarian signal + low price/MA ratio.' },
      { stepNumber: 3, title: 'Blend & Select', description: '50/50 weighted composite, buy top 20%.' },
    ],
  },
  quality_momentum: {
    displayName: 'Quality + Momentum',
    family: 'Composite Strategies',
    factorTags: ['Quality', 'Momentum'],
    riskProfile: 'Medium Risk',
    horizon: 'Medium',
    rebalanceFrequency: 'Monthly',
    marketCaps: ['Large Cap', 'Mid Cap'],
    overview: {
      concept: 'Targets "compounders" — high-quality businesses with positive price momentum. Combines low volatility and risk-adjusted returns (quality) with trailing momentum.',
      worksWellWhen: 'Quality leadership and sustained bull markets.',
      strugglesWhen: 'Junk rallies and speculative rotations into low-quality stocks.',
      typicalHoldings: 100,
      universe: 'S&P 500',
      liquidityProfile: 'Stable, trending large and mid-cap stocks.',
    },
    rules: [
      { stepNumber: 1, title: 'Momentum Rank', description: '12-month return (skip recent month).' },
      { stepNumber: 2, title: 'Quality Rank', description: 'Low vol + high risk-adjusted return.' },
      { stepNumber: 3, title: 'Composite Select', description: '50/50 blend, go long top 20%.' },
    ],
  },
  quality_low_vol: {
    displayName: 'Quality + Low Volatility',
    family: 'Composite Strategies',
    factorTags: ['Quality', 'Low Volatility'],
    riskProfile: 'Low Risk',
    horizon: 'Long',
    rebalanceFrequency: 'Monthly',
    marketCaps: ['Large Cap'],
    overview: {
      concept: 'Defensive "sleep-at-night" portfolio combining quality and low volatility. Targets the most stable, resilient stocks for consistent, low-drawdown performance.',
      worksWellWhen: 'Uncertain markets, corrections, and risk-off environments.',
      strugglesWhen: 'Strong risk-on rallies when volatile stocks lead.',
      typicalHoldings: 100,
      universe: 'S&P 500',
      liquidityProfile: 'Ultra-stable large-caps with proven resilience.',
    },
    rules: [
      { stepNumber: 1, title: 'Low Vol Score', description: 'Trailing volatility rank (lower = better).' },
      { stepNumber: 2, title: 'Quality Score', description: 'Risk-adjusted return + low max drawdown.' },
      { stepNumber: 3, title: 'Defensive Portfolio', description: '50/50 blend, go long top 20%.' },
    ],
  },
  composite_factor_score: {
    displayName: 'Composite Factor Score',
    family: 'Multi-Factor Strategies',
    factorTags: ['Momentum', 'Value', 'Quality', 'Low Volatility'],
    riskProfile: 'Medium Risk',
    horizon: 'Medium',
    rebalanceFrequency: 'Monthly',
    marketCaps: ['Large Cap', 'Mid Cap'],
    overview: {
      concept: 'All-in-one multi-factor portfolio combining momentum (30%), quality (30%), value (20%), and low volatility (20%) into a single composite score. A systematic "smart beta" approach.',
      worksWellWhen: 'Diversified factor exposure works in most environments.',
      strugglesWhen: 'Extreme single-factor dominance (e.g., pure growth or pure value rallies).',
      typicalHoldings: 100,
      universe: 'S&P 500',
      liquidityProfile: 'Well-diversified multi-factor portfolio.',
    },
    rules: [
      { stepNumber: 1, title: 'Score Each Factor', description: 'Rank all stocks on momentum, value, quality, low vol.' },
      { stepNumber: 2, title: 'Weighted Composite', description: '30% momentum + 30% quality + 20% value + 20% low vol.' },
      { stepNumber: 3, title: 'Select Top Quintile', description: 'Go long the top 20% by composite score.' },
    ],
  },
  volatility_targeting: {
    displayName: 'Volatility Targeting',
    family: 'Risk Management Strategies',
    factorTags: ['Low Volatility'],
    riskProfile: 'Low Risk',
    horizon: 'Medium',
    rebalanceFrequency: 'Weekly',
    marketCaps: ['Large Cap', 'Mid Cap', 'Small Cap'],
    overview: {
      concept: 'Maintains constant portfolio volatility by scaling exposure inversely to realized vol. When markets are calm, increase exposure; when volatile, reduce. Used by institutional risk-parity funds.',
      worksWellWhen: 'Trending markets with gradually changing volatility regimes.',
      strugglesWhen: 'Sudden volatility spikes (vol scales down too late).',
      typicalHoldings: 500,
      universe: 'S&P 500 (full universe)',
      liquidityProfile: 'Broad market with dynamic leverage adjustment.',
    },
    rules: [
      { stepNumber: 1, title: 'Estimate Realized Vol', description: '63-day trailing annualized portfolio volatility.' },
      { stepNumber: 2, title: 'Calculate Scale Factor', description: 'Scale = target_vol (10%) / realized_vol.' },
      { stepNumber: 3, title: 'Adjust Exposure', description: 'Equal-weight portfolio scaled by factor (capped at 2x).' },
    ],
  },
  earnings_surprise_momentum: {
    displayName: 'Earnings Surprise Momentum',
    family: 'Event-Driven Strategies',
    factorTags: ['Momentum'],
    riskProfile: 'High Risk',
    horizon: 'Short',
    rebalanceFrequency: 'Daily',
    marketCaps: ['Large Cap', 'Mid Cap', 'Small Cap'],
    overview: {
      concept: 'Exploits Post-Earnings Announcement Drift (PEAD) — stocks with positive earnings surprises tend to drift higher for weeks. Detects "earnings-like" events via volume spikes + large price moves.',
      worksWellWhen: 'Earnings seasons with clear surprises and continued drift.',
      strugglesWhen: 'Markets where earnings reactions are quickly priced in.',
      typicalHoldings: 30,
      universe: 'S&P 500',
      liquidityProfile: 'Event-driven with concentrated positions.',
    },
    rules: [
      { stepNumber: 1, title: 'Detect Events', description: 'Volume spike (3x average) + large price move (>2 std devs).' },
      { stepNumber: 2, title: 'Filter Positive', description: 'Only enter on positive surprise (price up).' },
      { stepNumber: 3, title: 'Hold for Drift', description: 'Hold position for 63 days (3 months) post-event.' },
    ],
  },
};

// Default display info for unknown strategies
const DEFAULT_DISPLAY_INFO = {
  displayName: 'Unknown Strategy',
  family: 'Other',
  factorTags: [],
  riskProfile: 'Medium Risk',
  horizon: 'Medium',
  rebalanceFrequency: 'Monthly',
  marketCaps: ['Large Cap'],
  overview: {
    concept: 'Strategy description not available.',
    worksWellWhen: 'Market conditions vary.',
    strugglesWhen: 'Adverse market conditions.',
    typicalHoldings: 10,
    universe: 'S&P 500',
    liquidityProfile: 'Standard liquidity requirements.',
  },
  rules: [],
};

export interface EnrichedStrategy {
  // From API
  id: number;
  name: string;
  strategyType: string;
  description: string | null;
  symbol: string | null;
  runId: number;
  startDate: string | null;
  endDate: string | null;
  initialCapital: number;
  finalCapital: number | null;
  metrics: {
    totalReturn: number | null;
    cagr: number | null;
    volatility: number | null;
    sharpeRatio: number | null;
    sortinoRatio: number | null;
    maxDrawdown: number | null;
    calmarRatio: number | null;
    winRate: number | null;
    profitFactor: number | null;
  };
  equityCurve: Array<{ date: string; strategy: number; benchmark: number }>;
  drawdown: Array<{ date: string; drawdown: number }>;
  // From display info
  slug: string;
  displayName: string;
  family: string;
  factorTags: string[];
  riskProfile: string;
  horizon: string;
  rebalanceFrequency: string;
  marketCaps: string[];
  overview: {
    concept: string;
    worksWellWhen: string;
    strugglesWhen: string;
    typicalHoldings: number;
    universe: string;
    liquidityProfile: string;
  };
  rules: { stepNumber: number; title: string; description: string }[];
  implemented: boolean;
  // Phase 3 research data (from scorecard)
  tier: string | null;
  phase3Sharpe: number | null;
}

export interface UseDashboardDataResult {
  strategies: EnrichedStrategy[];
  benchmark: BenchmarkData | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

function enrichStrategy(
  strategy: StrategyBacktest,
  benchmarkEquity: { date: string; equity: number }[],
  scorecard: Record<string, { tier: string; sharpe: number | null }> = {}
): EnrichedStrategy {
  const displayInfo = STRATEGY_DISPLAY_INFO[strategy.name] || {
    ...DEFAULT_DISPLAY_INFO,
    displayName: strategy.name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
  };

  // Create a map of benchmark equity by date for quick lookup
  const benchmarkByDate = new Map(benchmarkEquity.map(p => [p.date, p.equity]));

  // Build combined equity curve with benchmark
  const equityCurve = strategy.equity_curve.map(point => ({
    date: point.date,
    strategy: point.equity,
    benchmark: benchmarkByDate.get(point.date) || 100000,
  }));

  // Build drawdown data
  const drawdown = strategy.equity_curve.map(point => ({
    date: point.date,
    drawdown: (point.drawdown || 0) * 100, // Convert to percentage
  }));

  return {
    // API data
    id: strategy.id,
    name: strategy.name,
    strategyType: strategy.strategy_type,
    description: strategy.description,
    symbol: strategy.symbol,
    runId: strategy.run_id,
    startDate: strategy.start_date,
    endDate: strategy.end_date,
    initialCapital: strategy.initial_capital,
    finalCapital: strategy.final_capital,
    metrics: {
      totalReturn: strategy.metrics.total_return,
      cagr: strategy.metrics.cagr,
      volatility: strategy.metrics.volatility,
      sharpeRatio: strategy.metrics.sharpe_ratio,
      sortinoRatio: strategy.metrics.sortino_ratio,
      maxDrawdown: strategy.metrics.max_drawdown,
      calmarRatio: strategy.metrics.calmar_ratio,
      winRate: strategy.metrics.win_rate,
      profitFactor: strategy.metrics.profit_factor,
    },
    equityCurve,
    drawdown,
    // Display info
    slug: strategy.name.replace(/_/g, '-'),
    displayName: displayInfo.displayName,
    family: displayInfo.family,
    factorTags: displayInfo.factorTags,
    riskProfile: displayInfo.riskProfile,
    horizon: displayInfo.horizon,
    rebalanceFrequency: displayInfo.rebalanceFrequency,
    marketCaps: displayInfo.marketCaps,
    overview: displayInfo.overview,
    rules: displayInfo.rules,
    implemented: true,
    tier: scorecard[strategy.name]?.tier ?? null,
    phase3Sharpe: scorecard[strategy.name]?.sharpe ?? null,
  };
}

export function useDashboardData(): UseDashboardDataResult {
  const [strategies, setStrategies] = useState<EnrichedStrategy[]>([]);
  const [benchmark, setBenchmark] = useState<BenchmarkData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch dashboard data and Phase 3 scorecard in parallel
      const [data, scorecardRes] = await Promise.all([
        fetchDashboardData(),
        fetch(`${API_BASE_URL}/research/scorecard`).then(r => r.ok ? r.json() : { scorecard: {} }),
      ]);

      const scorecard = scorecardRes.scorecard || {};

      // Enrich strategies with display info, benchmark data, and Phase 3 tier
      const benchmarkEquity = data.benchmark?.equity_curve || [];
      const enrichedStrategies = data.strategies.map(s => enrichStrategy(s, benchmarkEquity, scorecard));

      setStrategies(enrichedStrategies);
      setBenchmark(data.benchmark);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    strategies,
    benchmark,
    isLoading,
    error,
    refetch: fetchData,
  };
}

export function getStrategyBySlug(strategies: EnrichedStrategy[], slug: string): EnrichedStrategy | undefined {
  return strategies.find(s => s.slug === slug);
}
