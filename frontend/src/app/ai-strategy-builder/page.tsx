'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import Link from 'next/link'
import {
  Sparkles, Send, BookOpen, CheckCircle2, XCircle, AlertCircle,
  ChevronDown, ChevronUp, Loader2, FlaskConical, TrendingUp,
  ShieldCheck, BarChart3, Zap, RefreshCw, ArrowRight,
} from 'lucide-react'
import {
  fetchAiBuilderGenerateAndBacktest, fetchFactorLibrary,
  AiBuilderGenerateAndBacktestResponse, AiBuilderGate, AiBuilderStrategySpec,
  FactorInfo, CustomBacktest,
} from '@/lib/api'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

// ─── Types ────────────────────────────────────────────────────────────────────

interface Message {
  role: 'user' | 'assistant'
  content: string
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const GATE_ICONS = [FlaskConical, TrendingUp, BarChart3, ShieldCheck, Zap, BookOpen, ShieldCheck]

function gateColor(result: AiBuilderGate['result']) {
  return result === 'PASS'
    ? { bg: 'bg-emerald-50', border: 'border-emerald-200', badge: 'bg-emerald-100 text-emerald-700', icon: 'text-emerald-500' }
    : result === 'FAIL'
    ? { bg: 'bg-red-50', border: 'border-red-200', badge: 'bg-red-100 text-red-700', icon: 'text-red-500' }
    : { bg: 'bg-amber-50', border: 'border-amber-200', badge: 'bg-amber-100 text-amber-700', icon: 'text-amber-500' }
}

function GateIcon({ result }: { result: AiBuilderGate['result'] }) {
  if (result === 'PASS') return <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
  if (result === 'FAIL') return <XCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
  return <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0" />
}

function verdictStyle(verdict: string) {
  if (verdict.includes('ALL')) return 'bg-emerald-600 text-white'
  if (verdict.includes('CAVEAT')) return 'bg-amber-500 text-white'
  if (verdict.includes('PARTIAL')) return 'bg-orange-500 text-white'
  return 'bg-red-600 text-white'
}

function categoryColor(cat: string) {
  const map: Record<string, string> = {
    Momentum: 'bg-blue-100 text-blue-700',
    Value: 'bg-emerald-100 text-emerald-700',
    Quality: 'bg-purple-100 text-purple-700',
    'Quality / Risk': 'bg-indigo-100 text-indigo-700',
    'Mean Reversion': 'bg-orange-100 text-orange-700',
    'Risk Management': 'bg-red-100 text-red-700',
    'Event-Driven': 'bg-pink-100 text-pink-700',
  }
  return map[cat] || 'bg-gray-100 text-gray-700'
}

const EXAMPLE_PROMPTS = [
  'I want to buy stocks that are trending upward and have strong recent price momentum',
  'Build a low-risk strategy that avoids volatile stocks and protects capital in downturns',
  'I want to exploit the quality premium — high ROIC, stable earnings, wide moat companies',
  'Mean reversion strategy: buy oversold stocks and sell when they recover',
  'A multi-factor approach blending value, momentum, and quality signals equally',
]

// ── Demo result (pre-computed, no API key required) ───────────────────────────

const DEMO_RESULT: AiBuilderGenerateAndBacktestResponse = {
  factor_code: `vol = returns.rolling(63).std() * np.sqrt(252)
return -vol`,
  custom_backtest: {
    sharpe_ratio: 0.659,
    cagr: 0.0921,
    max_drawdown: -0.513,
    volatility: 0.157,
    total_return: 8.34,
    win_rate: 0.587,
    equity_curve: [
      { date: '2000-01-03', value: 100000 },
      { date: '2001-01-02', value: 108000 },
      { date: '2002-01-02', value: 96000 },
      { date: '2003-01-02', value: 112000 },
      { date: '2004-01-02', value: 135000 },
      { date: '2005-01-03', value: 160000 },
      { date: '2006-01-03', value: 193000 },
      { date: '2007-01-03', value: 228000 },
      { date: '2008-01-02', value: 207000 },
      { date: '2009-01-02', value: 158000 },
      { date: '2010-01-04', value: 200000 },
      { date: '2011-01-03', value: 228000 },
      { date: '2012-01-03', value: 263000 },
      { date: '2013-01-02', value: 318000 },
      { date: '2014-01-02', value: 374000 },
      { date: '2015-01-02', value: 398000 },
      { date: '2016-01-04', value: 426000 },
      { date: '2017-01-03', value: 517000 },
      { date: '2018-01-02', value: 553000 },
      { date: '2019-01-02', value: 597000 },
      { date: '2020-01-02', value: 656000 },
      { date: '2020-04-01', value: 487000 },
      { date: '2021-01-04', value: 692000 },
      { date: '2022-01-03', value: 738000 },
      { date: '2023-01-03', value: 768000 },
      { date: '2024-01-02', value: 835000 },
      { date: '2024-12-31', value: 934000 },
    ],
  },
  backtest_error: null,
  raw_response: '{"matched_strategy":"low_volatility_shield","strategy_display_name":"Low Volatility Shield","confidence":0.91,"factors":[{"id":"low_volatility","name":"Low Volatility","weight":0.7,"role":"Primary signal — inverse-vol weighting favors stable, low-beta stocks"},{"id":"quality_profitability","name":"Quality / Profitability","weight":0.3,"role":"Quality overlay — tilts toward stable earnings which correlate with low vol"}],"hypothesis":"Stocks with consistently low realized volatility earn a risk-adjusted premium. The CAPM predicts high-risk stocks should outperform, but empirically the low-volatility anomaly reverses this — low-vol stocks outperform on a risk-adjusted basis across 50+ years of data.","rebalancing":"Monthly","universe":"S&P 500 (large cap)","key_risk":"Long bull markets favor high-beta stocks; this strategy underperforms significantly during momentum-driven rallies (tech 1999, growth 2020).","analyst_note":"The only strategy in the 14-strategy library to generate meaningful positive alpha (+1.7%/yr, β=0.64) while significantly reducing market exposure. Best performer in dot-com crash (Sharpe +0.63 vs benchmark +0.11)."}',
  strategy_spec: {
    matched_strategy: 'low_volatility_shield',
    strategy_display_name: 'Low Volatility Shield',
    confidence: 0.91,
    factors: [
      { id: 'low_volatility', name: 'Low Volatility', weight: 0.7, role: 'Primary signal — inverse-vol weighting favors stable, low-beta stocks' },
      { id: 'quality_profitability', name: 'Quality / Profitability', weight: 0.3, role: 'Quality overlay — tilts toward stable earnings which correlate with low vol' },
    ],
    hypothesis: 'Stocks with consistently low realized volatility earn a risk-adjusted premium. The CAPM predicts high-risk stocks should outperform, but empirically the low-volatility anomaly reverses this — low-vol stocks outperform on a risk-adjusted basis across 50+ years of data.',
    rebalancing: 'Monthly',
    universe: 'S&P 500 (large cap)',
    key_risk: 'Long bull markets favor high-beta stocks; this strategy underperforms significantly during momentum-driven rallies (tech 1999, growth 2020).',
    analyst_note: 'The only strategy in the 14-strategy library to generate meaningful positive alpha (+1.7%/yr, β=0.64) while significantly reducing market exposure. Best performer in dot-com crash (Sharpe +0.63 vs benchmark +0.11).',
  },
  validation_gates: [
    { gate: 1, name: 'In-Sample Performance', criterion: 'IS Sharpe > 0.5', value: 'Sharpe = 0.659', result: 'PASS', detail: 'The strategy achieves a Sharpe ratio of 0.659 over the 2000–2024 in-sample period, above the minimum threshold of 0.5. Top-tier result among our 14-strategy library.' },
    { gate: 2, name: 'Walk-Forward Efficiency', criterion: 'WFE ≥ 100%', value: 'WFE = 147.3%', result: 'PASS', detail: 'Out-of-sample Sharpe exceeded in-sample Sharpe across rolling 4-year folds. WFE > 100% means parameters generalize to unseen data. Note: this is partially regime-driven (IS folds included bear markets).' },
    { gate: 3, name: 'Monte Carlo Significance', criterion: 'p < 0.05 (permutation test)', value: 'p = 0.0001 ★★★ SIGNIFICANT', result: 'PASS', detail: 'Bootstrap permutation test (10,000 iterations) confirms the Sharpe is statistically significant. Probability that a random strategy achieves this result: 0.01%. IID p-value: 0.003.' },
    { gate: 4, name: 'Bear Market Resilience', criterion: 'Bear regime Sharpe > −0.5', value: 'Bear Sharpe = −1.41', result: 'FAIL', detail: 'HONEST RESULT: All 14 long-only strategies fail in bear markets. This is the academic truth of long-only equity factor strategies — they are all correlated to market direction. The Low Volatility Shield is relatively the best in bear markets (−1.41 vs avg −1.8), but still significantly negative.' },
    { gate: 5, name: 'Transaction Cost Sensitivity', criterion: 'Survives 50 bps costs', value: 'BULLETPROOF — monthly turnover 0.4×/yr', result: 'PASS', detail: 'With 15 bps round-trip transaction costs, the strategy is fully BULLETPROOF. Very low turnover (0.4× per year) means transaction costs are minimal. Still profitable at 5× the realistic cost.' },
    { gate: 6, name: 'OOS Holdout Performance', criterion: 'OOS Sharpe > 0', value: 'Avg OOS Sharpe = 0.71', result: 'PASS', detail: 'Average out-of-sample Sharpe across walk-forward folds is 0.71, well above zero. Strategy generalizes reliably to unseen periods.' },
    { gate: 7, name: 'Bonferroni Bias Audit', criterion: 'p < 0.0036 (14-strategy correction)', value: 'p = 0.0001 < 0.0036', result: 'PASS', detail: 'Testing 14 strategies simultaneously creates multiple-comparison risk. Bonferroni threshold: 0.05/14 = 0.0036. This strategy passes even this strict threshold (p = 0.0001). Survivorship bias: ~17% of historical S&P 500 stocks are missing (delisted, bankrupt) — partially survivorship-biased. CRSP database would eliminate this.' },
  ],
  n_passed: 5,
  n_failed: 1,
  n_caveat: 1,
  overall_verdict: 'VALIDATED WITH CAVEAT',
  matched_strategy_info: { display: 'Low Volatility Shield', family: 'Factor', desc: 'Inverse-volatility weighted portfolio of stable, low-beta S&P 500 stocks.' },
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function GateCard({ gate, visible }: { gate: AiBuilderGate; visible: boolean }) {
  const [expanded, setExpanded] = useState(false)
  const colors = gateColor(gate.result)

  return (
    <div
      className={`rounded-lg border transition-all duration-500 ${colors.bg} ${colors.border} ${
        visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
      }`}
    >
      <div
        className="flex items-center gap-3 p-3 cursor-pointer select-none"
        onClick={() => setExpanded(e => !e)}
      >
        <GateIcon result={gate.result} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-bold text-gray-400">GATE {gate.gate}</span>
            <span className="text-sm font-semibold text-gray-800">{gate.name}</span>
            <span className={`ml-auto text-xs font-bold px-2 py-0.5 rounded-full ${colors.badge}`}>
              {gate.result}
            </span>
          </div>
          <div className="text-xs text-gray-500 mt-0.5 truncate">{gate.value}</div>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-gray-400 flex-shrink-0" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />
        )}
      </div>
      {expanded && (
        <div className="px-4 pb-3 border-t border-gray-100 pt-2">
          <p className="text-xs text-gray-500 mb-1">
            <span className="font-semibold">Criterion:</span> {gate.criterion}
          </p>
          <p className="text-xs text-gray-700 leading-relaxed">{gate.detail}</p>
        </div>
      )}
    </div>
  )
}

function StrategySpecCard({ spec }: { spec: AiBuilderStrategySpec }) {
  const confidencePct = Math.round(spec.confidence * 100)
  const confColor =
    spec.confidence >= 0.8
      ? 'text-emerald-600'
      : spec.confidence >= 0.6
      ? 'text-amber-600'
      : 'text-red-500'

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl p-4 border border-purple-100">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs text-purple-500 font-semibold uppercase tracking-wide mb-1">
              Matched Strategy
            </p>
            <h3 className="text-lg font-bold text-gray-900">{spec.strategy_display_name}</h3>
            <p className="text-xs text-gray-500 mt-0.5 font-mono">{spec.matched_strategy}</p>
          </div>
          <div className="text-right flex-shrink-0">
            <p className={`text-2xl font-bold ${confColor}`}>{confidencePct}%</p>
            <p className="text-xs text-gray-400">match confidence</p>
          </div>
        </div>
        <div className="mt-3 w-full bg-gray-200 rounded-full h-1.5">
          <div
            className="h-1.5 rounded-full bg-gradient-to-r from-purple-500 to-indigo-500"
            style={{ width: `${confidencePct}%` }}
          />
        </div>
      </div>

      {/* Factors */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
          Factor Decomposition
        </p>
        <div className="space-y-2">
          {spec.factors.map(f => (
            <div key={f.id} className="flex items-center gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-0.5">
                  <span className="text-xs font-semibold text-gray-700 truncate">{f.name}</span>
                  <span className="text-xs font-bold text-gray-500 flex-shrink-0 ml-2">
                    {Math.round(f.weight * 100)}%
                  </span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-1.5">
                  <div
                    className="h-1.5 rounded-full bg-gradient-to-r from-purple-400 to-indigo-400"
                    style={{ width: `${Math.round(f.weight * 100)}%` }}
                  />
                </div>
                <p className="text-xs text-gray-400 mt-0.5 truncate">{f.role}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Hypothesis */}
      <div className="bg-blue-50 rounded-lg p-3 border border-blue-100">
        <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-1">
          Economic Hypothesis
        </p>
        <p className="text-xs text-gray-700 leading-relaxed">{spec.hypothesis}</p>
      </div>

      {/* Meta */}
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-gray-50 rounded-lg p-2.5">
          <p className="text-xs text-gray-400 font-medium">Rebalancing</p>
          <p className="text-sm font-semibold text-gray-800 mt-0.5">{spec.rebalancing}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-2.5">
          <p className="text-xs text-gray-400 font-medium">Universe</p>
          <p className="text-sm font-semibold text-gray-800 mt-0.5 leading-tight">{spec.universe}</p>
        </div>
      </div>

      {/* Risk */}
      <div className="bg-red-50 rounded-lg p-3 border border-red-100">
        <p className="text-xs font-semibold text-red-600 uppercase tracking-wide mb-1">Key Risk</p>
        <p className="text-xs text-gray-700">{spec.key_risk}</p>
      </div>

      {/* Analyst Note */}
      <div className="bg-amber-50 rounded-lg p-3 border border-amber-100">
        <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-1">
          Analyst Note
        </p>
        <p className="text-xs text-gray-700 italic">{spec.analyst_note}</p>
      </div>

      {/* View Full Analysis link */}
      <Link
        href={`/strategy/${spec.matched_strategy.replace(/_/g, '-')}`}
        className="flex items-center justify-center gap-2 w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold transition-colors"
      >
        View Full 25-Year Analysis
        <ArrowRight className="w-4 h-4" />
      </Link>
    </div>
  )
}

function FactorLibraryPanel({ factors }: { factors: FactorInfo[] }) {
  const categories = Array.from(new Set(factors.map(f => f.category)))

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <BookOpen className="w-4 h-4 text-purple-500" />
        <h3 className="text-sm font-semibold text-gray-700">Factor Library</h3>
        <span className="text-xs bg-purple-100 text-purple-600 px-2 py-0.5 rounded-full font-medium">
          {factors.length} signals
        </span>
      </div>
      <p className="text-xs text-gray-500 mb-4 leading-relaxed">
        Every strategy is built exclusively from these academically-documented factor signals.
        No black boxes — each signal has a published source and economic rationale.
      </p>
      <div className="space-y-3">
        {categories.map(cat => (
          <div key={cat}>
            <p className={`text-xs font-bold px-2 py-0.5 rounded-md inline-block mb-2 ${categoryColor(cat)}`}>
              {cat}
            </p>
            <div className="space-y-2">
              {factors
                .filter(f => f.category === cat)
                .map(f => (
                  <div key={f.id} className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <p className="text-xs font-semibold text-gray-800">{f.name}</p>
                    </div>
                    <p className="text-xs text-gray-600 leading-relaxed mb-1.5">{f.description}</p>
                    <p className="text-xs text-indigo-600 font-medium">{f.academic_source}</p>
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      <span className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">
                        Signal: {f.signal}
                      </span>
                      <span className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">
                        Hold: {f.typical_holding}
                      </span>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function CustomBacktestPanel({
  factorCode,
  backtest,
  backtestError,
}: {
  factorCode: string
  backtest: CustomBacktest | null
  backtestError: string | null
}) {
  const fmt = (v: number | null, pct = false, digits = 2) => {
    if (v === null) return 'N/A'
    const n = pct ? v * 100 : v
    return pct ? `${n.toFixed(digits)}%` : n.toFixed(digits)
  }

  const sharpe = backtest?.sharpe_ratio ?? null
  const cagr = backtest?.cagr ?? null
  const mdd = backtest?.max_drawdown ?? null
  const BENCHMARK_SHARPE = 0.694

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-violet-500" />
        <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
          Your Generated Strategy — Live 25-Year Backtest
        </p>
        {backtest && !backtestError && (
          <span className="ml-auto text-xs bg-violet-100 text-violet-700 px-2 py-0.5 rounded-full font-semibold">
            BACKTESTED
          </span>
        )}
      </div>

      {backtestError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-xs text-red-700">
          <span className="font-semibold">Backtest error:</span> {backtestError}
        </div>
      )}

      {backtest && (
        <>
          {/* KPI tiles */}
          <div className="grid grid-cols-3 gap-2">
            <div className="bg-gray-50 rounded-lg p-2.5 text-center">
              <p className="text-xs text-gray-400 font-medium">Sharpe (25yr)</p>
              <p className={`text-lg font-bold mt-0.5 ${sharpe !== null && sharpe > BENCHMARK_SHARPE ? 'text-emerald-600' : 'text-gray-800'}`}>
                {fmt(sharpe)}
              </p>
              <p className="text-xs text-gray-400">vs bmk {BENCHMARK_SHARPE}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-2.5 text-center">
              <p className="text-xs text-gray-400 font-medium">CAGR (25yr)</p>
              <p className="text-lg font-bold text-gray-800 mt-0.5">{fmt(cagr, true, 1)}</p>
              <p className="text-xs text-gray-400">annualized</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-2.5 text-center">
              <p className="text-xs text-gray-400 font-medium">Max Drawdown</p>
              <p className="text-lg font-bold text-red-600 mt-0.5">{fmt(mdd, true, 1)}</p>
              <p className="text-xs text-gray-400">peak-to-trough</p>
            </div>
          </div>

          {/* Equity curve */}
          {backtest.equity_curve.length > 5 && (
            <div className="h-40">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={backtest.equity_curve} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(d) => new Date(d).getFullYear().toString()}
                    tick={{ fontSize: 10, fill: '#9ca3af' }}
                    tickLine={false}
                    axisLine={{ stroke: '#e5e7eb' }}
                    interval={Math.floor(backtest.equity_curve.length / 6)}
                  />
                  <YAxis
                    tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`}
                    tick={{ fontSize: 10, fill: '#9ca3af' }}
                    tickLine={false}
                    axisLine={{ stroke: '#e5e7eb' }}
                    width={48}
                  />
                  <Tooltip
                    formatter={(v: number) => [`$${v.toLocaleString()}`, 'Portfolio']}
                    labelFormatter={(l) => new Date(l).toLocaleDateString()}
                    contentStyle={{ fontSize: '11px', border: '1px solid #e5e7eb', borderRadius: '6px' }}
                  />
                  <Line type="monotone" dataKey="value" stroke="#7c3aed" strokeWidth={2} dot={false} name="Portfolio" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}

      {/* Factor code */}
      {factorCode && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
            Generated Factor Code
          </p>
          <pre className="bg-gray-900 text-gray-100 rounded-lg p-3 text-xs font-mono overflow-x-auto leading-relaxed whitespace-pre-wrap">
            <code>{factorCode}</code>
          </pre>
          <p className="text-xs text-gray-400 mt-1">
            Receives <code className="bg-gray-100 px-1 rounded">prices</code>,{' '}
            <code className="bg-gray-100 px-1 rounded">returns</code>,{' '}
            <code className="bg-gray-100 px-1 rounded">pd</code>,{' '}
            <code className="bg-gray-100 px-1 rounded">np</code> · returns score DataFrame (higher = more attractive)
          </p>
        </div>
      )}
    </div>
  )
}


function ValidationPanel({
  result,
  visibleGates,
}: {
  result: AiBuilderGenerateAndBacktestResponse
  visibleGates: number
}) {
  const { strategy_spec, validation_gates, n_passed, n_failed, n_caveat, overall_verdict,
          factor_code, custom_backtest, backtest_error } = result

  return (
    <div className="space-y-5">
      {/* Strategy Spec */}
      {strategy_spec && <StrategySpecCard spec={strategy_spec} />}

      {/* Custom backtest results */}
      {(factor_code || custom_backtest || backtest_error) && (
        <CustomBacktestPanel
          factorCode={factor_code ?? ''}
          backtest={custom_backtest ?? null}
          backtestError={backtest_error ?? null}
        />
      )}

      {/* 7-Gate Verdict Banner */}
      {validation_gates.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              7-Gate Validation Pipeline
            </p>
            <span
              className={`text-xs font-bold px-3 py-1 rounded-full ${verdictStyle(overall_verdict)}`}
            >
              {overall_verdict}
            </span>
          </div>

          {/* Score pills */}
          <div className="flex gap-2 mb-3">
            <span className="flex items-center gap-1 text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full font-semibold">
              <CheckCircle2 className="w-3 h-3" /> {n_passed} PASS
            </span>
            {n_caveat > 0 && (
              <span className="flex items-center gap-1 text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded-full font-semibold">
                <AlertCircle className="w-3 h-3" /> {n_caveat} CAVEAT
              </span>
            )}
            {n_failed > 0 && (
              <span className="flex items-center gap-1 text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full font-semibold">
                <XCircle className="w-3 h-3" /> {n_failed} FAIL
              </span>
            )}
          </div>

          {/* Gate cards */}
          <div className="space-y-2">
            {validation_gates.map((gate, i) => (
              <GateCard key={gate.gate} gate={gate} visible={i < visibleGates} />
            ))}
          </div>

          {/* Footer note */}
          <p className="text-xs text-gray-400 mt-3 leading-relaxed">
            7-gate validation uses 25-year pre-computed research (2000–2024, S&P 500).
            Custom backtest runs your generated factor code live on the same dataset.
            Past performance does not guarantee future results.
          </p>
        </div>
      )}
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function AIStrategyBuilderPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingStage, setLoadingStage] = useState(0)
  const [result, setResult] = useState<AiBuilderGenerateAndBacktestResponse | null>(null)
  const [visibleGates, setVisibleGates] = useState(0)
  const [factors, setFactors] = useState<FactorInfo[]>([])
  const [rightPanel, setRightPanel] = useState<'factors' | 'results'>('factors')
  const [error, setError] = useState<string | null>(null)

  const chatEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Load factor library on mount
  useEffect(() => {
    fetchFactorLibrary()
      .then(d => setFactors(d.factors))
      .catch(() => {})
  }, [])

  // Scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Animate gate reveals after result arrives
  useEffect(() => {
    if (!result) return
    setVisibleGates(0)
    const n = result.validation_gates.length
    let i = 0
    const tick = () => {
      i++
      setVisibleGates(i)
      if (i < n) setTimeout(tick, 280)
    }
    setTimeout(tick, 400)
  }, [result])

  const sendMessage = useCallback(async () => {
    const text = input.trim()
    if (!text || loading) return

    const newMessages: Message[] = [...messages, { role: 'user', content: text }]
    setMessages(newMessages)
    setInput('')
    setLoading(true)
    setLoadingStage(0)
    setError(null)

    // Progress through loading stages: Claude → Factor code → Backtest
    const t1 = setTimeout(() => setLoadingStage(1), 3500)
    const t2 = setTimeout(() => setLoadingStage(2), 9000)

    try {
      const data = await fetchAiBuilderGenerateAndBacktest(
        newMessages.map(m => ({ role: m.role, content: m.content }))
      )
      clearTimeout(t1)
      clearTimeout(t2)

      // Add assistant reply to chat
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: data.raw_response },
      ])

      if (data.strategy_spec) {
        setResult(data)
        setRightPanel('results')
      }
    } catch (e) {
      clearTimeout(t1)
      clearTimeout(t2)
      const msg = e instanceof Error ? e.message : 'Unknown error'
      setError(msg)
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `Sorry, I ran into an error: ${msg}. Please check that the ANTHROPIC_API_KEY is set on the backend.`,
        },
      ])
    } finally {
      setLoading(false)
    }
  }, [input, messages, loading])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const reset = () => {
    setMessages([])
    setResult(null)
    setVisibleGates(0)
    setLoadingStage(0)
    setRightPanel('factors')
    setError(null)
    setInput('')
    setTimeout(() => textareaRef.current?.focus(), 50)
  }

  const useExamplePrompt = (p: string) => {
    setInput(p)
    setTimeout(() => textareaRef.current?.focus(), 50)
  }

  const loadDemo = () => {
    setMessages([
      { role: 'user', content: 'Build a low-risk strategy that avoids volatile stocks and protects capital in downturns' },
      { role: 'assistant', content: '✓ Strategy analyzed. See results panel →' },
    ])
    setResult(DEMO_RESULT)
    setRightPanel('results')
    setError(null)
  }

  const showEmptyState = messages.length === 0

  return (
    <div className="min-h-[calc(100vh-56px)] bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-purple-100 rounded-xl flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">AI Strategy Builder</h1>
              <p className="text-xs text-gray-500">
                Powered by Claude Opus 4.6 · Generates &amp; backtests custom factor code · 7-gate pipeline
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {result && (
              <button
                onClick={() => setRightPanel(p => p === 'results' ? 'factors' : 'results')}
                className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
              >
                <BookOpen className="w-3.5 h-3.5" />
                {rightPanel === 'results' ? 'Factor Library' : 'Results'}
              </button>
            )}
            {messages.length > 0 && (
              <button
                onClick={reset}
                className="text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                New Strategy
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 max-w-7xl mx-auto w-full px-4 py-6 flex gap-6">
        {/* Left — Chat */}
        <div className="flex flex-col w-full max-w-xl flex-shrink-0">
          {/* Chat messages */}
          <div className="flex-1 bg-white rounded-xl border border-gray-200 flex flex-col min-h-[480px] max-h-[calc(100vh-260px)]">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {showEmptyState ? (
                <div className="h-full flex flex-col items-center justify-center text-center py-8">
                  <div className="w-14 h-14 bg-purple-50 rounded-2xl flex items-center justify-center mb-4">
                    <Sparkles className="w-7 h-7 text-purple-500" />
                  </div>
                  <h3 className="text-base font-semibold text-gray-800 mb-2">
                    Describe your strategy idea
                  </h3>
                  <p className="text-sm text-gray-500 max-w-xs mb-6">
                    Tell me what kind of trading strategy you have in mind. I&apos;ll map it to an
                    academically-validated factor strategy and run a rigorous 7-gate validation.
                  </p>
                  <div className="space-y-2 w-full">
                    <p className="text-xs text-gray-400 font-medium mb-1">Try an example:</p>
                    {EXAMPLE_PROMPTS.map(p => (
                      <button
                        key={p}
                        onClick={() => useExamplePrompt(p)}
                        className="w-full text-left text-xs text-gray-600 bg-gray-50 hover:bg-purple-50 hover:text-purple-700 px-3 py-2 rounded-lg border border-gray-100 hover:border-purple-200 transition-colors"
                      >
                        {p}
                      </button>
                    ))}
                    <div className="pt-2 border-t border-gray-100">
                      <button
                        onClick={loadDemo}
                        className="w-full text-xs font-semibold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 px-3 py-2.5 rounded-lg border border-indigo-200 transition-colors flex items-center justify-center gap-2"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        Load pre-computed demo (no API key required)
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <>
                  {messages.map((m, i) => (
                    <div
                      key={i}
                      className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      {m.role === 'assistant' && (
                        <div className="w-7 h-7 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0 mr-2 mt-1">
                          <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                        </div>
                      )}
                      <div
                        className={`max-w-[85%] px-3 py-2 rounded-xl text-sm leading-relaxed ${
                          m.role === 'user'
                            ? 'bg-purple-600 text-white rounded-tr-sm'
                            : 'bg-gray-100 text-gray-800 rounded-tl-sm'
                        }`}
                      >
                        {m.role === 'assistant' ? (
                          // Show only the first line of assistant response in chat (it's mostly JSON)
                          <p className="whitespace-pre-wrap">
                            {m.content.includes('{')
                              ? '✓ Strategy analyzed. See results panel →'
                              : m.content}
                          </p>
                        ) : (
                          <p>{m.content}</p>
                        )}
                      </div>
                    </div>
                  ))}
                  {loading && (
                    <div className="flex justify-start">
                      <div className="w-7 h-7 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0 mr-2 mt-1">
                        <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                      </div>
                      <div className="bg-gray-100 px-3 py-2 rounded-xl rounded-tl-sm">
                        <div className="flex items-center gap-2 text-gray-500 text-sm">
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>
                            {loadingStage === 0 && 'Analyzing with Claude Opus 4.6…'}
                            {loadingStage === 1 && 'Generating factor code…'}
                            {loadingStage === 2 && 'Running 25-year backtest…'}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </>
              )}
            </div>

            {/* Input */}
            <div className="border-t border-gray-100 p-3">
              {error && (
                <div className="mb-2 text-xs text-red-600 bg-red-50 px-3 py-2 rounded-lg">
                  {error}
                </div>
              )}
              <div className="flex gap-2">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Describe your strategy idea… (Enter to send)"
                  rows={2}
                  disabled={loading}
                  className="flex-1 text-sm resize-none border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-300 focus:border-transparent disabled:opacity-50 placeholder-gray-400"
                />
                <button
                  onClick={sendMessage}
                  disabled={!input.trim() || loading}
                  className="self-end px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex-shrink-0"
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </button>
              </div>
              <p className="text-xs text-gray-400 mt-1.5 text-center">
                Claude Opus 4.6 · Adaptive thinking · 25-year research database
              </p>
            </div>
          </div>

          {/* How it works */}
          <div className="mt-4 bg-white rounded-xl border border-gray-200 p-4">
            <p className="text-xs font-semibold text-gray-600 mb-2">How it works</p>
            <div className="space-y-1.5">
              {[
                ['1', 'Describe your strategy in plain English'],
                ['2', 'Claude maps it to a factor and generates Python scoring code'],
                ['3', 'The code runs a live backtest on 25 years of S&P 500 data'],
                ['4', 'The 7-gate pipeline validates statistical robustness'],
              ].map(([n, t]) => (
                <div key={n} className="flex items-start gap-2">
                  <span className="w-4 h-4 bg-purple-100 text-purple-600 rounded-full text-xs flex items-center justify-center font-bold flex-shrink-0 mt-0.5">
                    {n}
                  </span>
                  <p className="text-xs text-gray-600">{t}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right — Factor Library / Validation Results */}
        <div className="flex-1 bg-white rounded-xl border border-gray-200 overflow-y-auto max-h-[calc(100vh-180px)] p-5">
          {rightPanel === 'factors' || !result ? (
            factors.length > 0 ? (
              <FactorLibraryPanel factors={factors} />
            ) : (
              <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
                Loading factor library…
              </div>
            )
          ) : result && (
            <ValidationPanel result={result} visibleGates={visibleGates} />
          )}
        </div>
      </div>
    </div>
  )
}
