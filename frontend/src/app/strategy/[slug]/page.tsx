'use client'

export const dynamic = 'force-dynamic'

import { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import {
  ArrowLeft,
  Clock,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  Loader2,
  AlertCircle,
  FlaskConical,
  SlidersHorizontal,
  Play,
  BarChart2,
  Grid,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useDashboardData, getStrategyBySlug } from '@/hooks/useDashboardData'
import { EquityCurveChart } from '@/components/charts/EquityCurveChart'
import { DrawdownChart } from '@/components/charts/DrawdownChart'
import { AnnualBarChart } from '@/components/charts/AnnualBarChart'
import { CorrelationHeatmap } from '@/components/charts/CorrelationHeatmap'
import {
  fetchResearchData,
  fetchStrategyParameters,
  fetchSensitivityData,
  fetchFactorAlpha,
  fetchRollingMetrics,
  fetchCorrelationData,
  fetchLiveSignals,
  runBacktest,
  type StrategyResearch,
  type StrategyParameter,
  type SensitivityData,
  type FactorAlpha,
  type RollingMetrics,
  type CorrelationData,
  type LiveSignals,
} from '@/lib/api'
import { SensitivityHeatmap } from '@/components/charts/SensitivityHeatmap'

type TabId = 'overview' | 'rules' | 'performance' | 'research' | 'parameters' | 'rolling' | 'correlation'

function formatPercent(value: number | null | undefined, decimals: number = 1): string {
  if (value === null || value === undefined || isNaN(value)) return 'N/A'
  return `${(value * 100).toFixed(decimals)}%`
}

function formatNumber(value: number | null | undefined, decimals: number = 2): string {
  if (value === null || value === undefined || isNaN(value)) return 'N/A'
  return value.toFixed(decimals)
}

function pVal(v: number | null | undefined): string {
  if (v === null || v === undefined) return 'N/A'
  if (v < 0.001) return '<0.001'
  return v.toFixed(3)
}

// ── Verdict badge ────────────────────────────────────────────────────────────
function VerdictBadge({ verdict }: { verdict: string | null | undefined }) {
  if (!verdict) return null
  const is3star = verdict.includes('★★★')
  const is2star = verdict.includes('★★') && !is3star
  const isFragile = verdict.includes('FRAGILE') || verdict.includes('NOT')
  return (
    <span className={cn(
      'inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-semibold',
      is3star ? 'bg-green-100 text-green-800' :
      is2star ? 'bg-yellow-100 text-yellow-800' :
      isFragile ? 'bg-red-100 text-red-800' :
      'bg-blue-100 text-blue-800'
    )}>
      {verdict}
    </span>
  )
}

// ── Tier badge ───────────────────────────────────────────────────────────────
function TierBadge({ tier }: { tier: string | null | undefined }) {
  if (!tier) return null
  const isTier1 = tier.includes('Tier 1')
  const isTier2 = tier.includes('Tier 2')
  return (
    <span className={cn(
      'inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold',
      isTier1 ? 'bg-emerald-100 text-emerald-800' :
      isTier2 ? 'bg-blue-100 text-blue-800' :
      'bg-gray-100 text-gray-700'
    )}>
      {tier}
    </span>
  )
}

// ── Regime row colour ────────────────────────────────────────────────────────
function regimeColor(sharpe: number | null): string {
  if (sharpe === null) return 'text-gray-400'
  if (sharpe > 1) return 'text-green-700 font-semibold'
  if (sharpe > 0) return 'text-yellow-700'
  return 'text-red-700 font-semibold'
}

export default function StrategyDetailPage() {
  const params = useParams()
  const slug = params.slug as string
  const { strategies, benchmark, isLoading, error, refetch } = useDashboardData()
  const strategy = getStrategyBySlug(strategies, slug)

  const [activeTab, setActiveTab] = useState<TabId>('overview')

  // Research tab state
  const [research, setResearch] = useState<StrategyResearch | null>(null)
  const [researchLoading, setResearchLoading] = useState(false)
  const [researchError, setResearchError] = useState<string | null>(null)
  const [factorAlpha, setFactorAlpha] = useState<FactorAlpha | null>(null)

  // Parameters tab state
  const [paramDefs, setParamDefs] = useState<StrategyParameter[]>([])
  const [paramValues, setParamValues] = useState<Record<string, number>>({})
  const [paramLoading, setParamLoading] = useState(false)
  const [backtestRunning, setBacktestRunning] = useState(false)
  const [backtestResult, setBacktestResult] = useState<{
    metrics: Record<string, number | null>
    equityCurve: { date: string; equity: number }[]
  } | null>(null)
  const [backtestError, setBacktestError] = useState<string | null>(null)

  // Rolling metrics tab state
  const [rolling, setRolling] = useState<RollingMetrics | null>(null)
  const [rollingLoading, setRollingLoading] = useState(false)
  const [rollingMetric, setRollingMetric] = useState<'sharpe' | 'cagr' | 'mdd'>('sharpe')

  // 25yr benchmark averages for the rolling chart reference lines
  const rollingBenchmarkAvg = useMemo(() => {
    if (!rolling) return { sharpe: null, cagr: null, mdd: null }
    const avg = (arr: { benchmark: number | null }[]) => {
      const vals = arr.map(d => d.benchmark).filter((v): v is number => v !== null)
      return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null
    }
    return {
      sharpe: avg(rolling.annual_sharpe),
      cagr: avg(rolling.annual_cagr),
      mdd: avg(rolling.annual_mdd),
    }
  }, [rolling])

  // Sensitivity tab state
  const [sensitivity, setSensitivity] = useState<SensitivityData | null>(null)
  const [sensitivityLoading, setSensitivityLoading] = useState(false)

  // Correlation tab state
  const [correlation, setCorrelation] = useState<CorrelationData | null>(null)
  const [correlationLoading, setCorrelationLoading] = useState(false)

  // Derive strategy name from slug (hyphens → underscores)
  const strategyName = slug.replace(/-/g, '_')

  // Live signals state (loaded when Overview tab opens)
  const [liveSignals, setLiveSignals] = useState<LiveSignals | null>(null)
  const [liveSignalsLoading, setLiveSignalsLoading] = useState(false)
  const [liveSignalsUnavailable, setLiveSignalsUnavailable] = useState(false)

  useEffect(() => {
    if (activeTab !== 'overview' || liveSignals || liveSignalsLoading || liveSignalsUnavailable) return
    setLiveSignalsLoading(true)
    fetchLiveSignals(strategyName)
      .then(data => setLiveSignals(data))
      .catch(() => setLiveSignalsUnavailable(true))
      .finally(() => setLiveSignalsLoading(false))
  }, [activeTab, strategyName, liveSignals, liveSignalsLoading, liveSignalsUnavailable])

  // Fetch research data + factor alpha when tab is first opened
  useEffect(() => {
    if (activeTab !== 'research' || research || researchLoading) return
    setResearchLoading(true)
    setResearchError(null)
    Promise.all([
      fetchResearchData(strategyName),
      fetchFactorAlpha(strategyName).catch(() => null),
    ])
      .then(([researchData, alphaData]) => {
        setResearch(researchData)
        if (alphaData) setFactorAlpha(alphaData)
      })
      .catch(e => setResearchError(e.message))
      .finally(() => setResearchLoading(false))
  }, [activeTab, strategyName, research, researchLoading])

  // Fetch rolling metrics when tab is first opened
  useEffect(() => {
    if (activeTab !== 'rolling' || rolling || rollingLoading) return
    setRollingLoading(true)
    fetchRollingMetrics(strategyName)
      .then(data => setRolling(data))
      .catch(() => setRolling(null))
      .finally(() => setRollingLoading(false))
  }, [activeTab, strategyName, rolling, rollingLoading])

  // Fetch correlation data when tab is first opened
  useEffect(() => {
    if (activeTab !== 'correlation' || correlation || correlationLoading) return
    setCorrelationLoading(true)
    fetchCorrelationData()
      .then(data => setCorrelation(data))
      .catch(() => setCorrelation(null))
      .finally(() => setCorrelationLoading(false))
  }, [activeTab, correlation, correlationLoading])

  // Fetch parameter definitions + sensitivity data when tab is first opened
  useEffect(() => {
    if (activeTab !== 'parameters' || paramDefs.length > 0 || paramLoading) return
    setParamLoading(true)
    fetchStrategyParameters(strategyName)
      .then(({ parameters }) => {
        setParamDefs(parameters)
        const defaults: Record<string, number> = {}
        parameters.forEach(p => { defaults[p.name] = p.default })
        setParamValues(defaults)
      })
      .catch(() => setParamDefs([]))
      .finally(() => setParamLoading(false))
  }, [activeTab, strategyName, paramDefs.length, paramLoading])

  useEffect(() => {
    if (activeTab !== 'parameters' || sensitivity || sensitivityLoading) return
    setSensitivityLoading(true)
    fetchSensitivityData(strategyName)
      .then(setSensitivity)
      .catch(() => setSensitivity(null))
      .finally(() => setSensitivityLoading(false))
  }, [activeTab, strategyName, sensitivity, sensitivityLoading])

  const handleRunBacktest = async () => {
    setBacktestRunning(true)
    setBacktestError(null)
    setBacktestResult(null)
    try {
      const result = await runBacktest({
        strategy_name: strategyName,
        params: paramValues,
        initial_capital: 100000,
      })
      setBacktestResult({
        metrics: result.metrics,
        equityCurve: result.equity_curve,
      })
    } catch (e) {
      setBacktestError(e instanceof Error ? e.message : 'Backtest failed')
    } finally {
      setBacktestRunning(false)
    }
  }

  // ── Loading / error / not-found guards ──────────────────────────────────
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-500">Loading strategy data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Failed to Load Data</h2>
          <p className="text-gray-500 mb-4">{error}</p>
          <button
            onClick={refetch}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md"
          >
            <RefreshCw className="w-4 h-4" />
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!strategy) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-500">Strategy not found.</p>
        <Link href="/" className="text-blue-600 hover:text-blue-700 mt-2 inline-block">
          Back to Dashboard
        </Link>
      </div>
    )
  }

  const riskColors: Record<string, string> = {
    'Low Risk': 'bg-green-100 text-green-700',
    'Medium Risk': 'bg-yellow-100 text-yellow-700',
    'High Risk': 'bg-red-100 text-red-700',
  }

  const familyColors: Record<string, string> = {
    'Factor Strategies': 'text-blue-600 bg-blue-50',
    'Technical Strategies': 'text-purple-600 bg-purple-50',
    'Multi-Factor Strategies': 'text-emerald-600 bg-emerald-50',
    'Advanced / Quant Extensions': 'text-orange-600 bg-orange-50',
  }

  const tabs: { id: TabId; label: string; icon?: React.ReactNode }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'rules', label: 'Rules' },
    { id: 'performance', label: 'Performance' },
    { id: 'research', label: 'Research', icon: <FlaskConical className="w-3.5 h-3.5" /> },
    { id: 'rolling', label: 'Rolling', icon: <BarChart2 className="w-3.5 h-3.5" /> },
    { id: 'correlation', label: 'Correlations', icon: <Grid className="w-3.5 h-3.5" /> },
    { id: 'parameters', label: 'Parameters', icon: <SlidersHorizontal className="w-3.5 h-3.5" /> },
  ]

  // Regime display rows
  const regimeRows = research?.regime
    ? [
        { label: 'Bull Market', value: research.regime.bull_sharpe },
        { label: 'Bear Market', value: research.regime.bear_sharpe },
        { label: 'High Volatility', value: research.regime.high_vol_sharpe },
        { label: 'Sideways', value: research.regime.sideways_sharpe },
      ]
    : []

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Back Link */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-6 py-3">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
        </div>
      </div>

      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className={cn('px-2 py-1 text-xs font-medium rounded', familyColors[strategy.family] || 'bg-gray-100 text-gray-600')}>
                  {strategy.family}
                </span>
                {strategy.factorTags.map(tag => (
                  <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                    {tag}
                  </span>
                ))}
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">{strategy.displayName}</h1>
              {strategy.symbol && strategy.symbol !== 'UNIVERSE' && (
                <p className="text-sm text-gray-500 mb-2">
                  Backtested on: <span className="font-medium text-gray-700">{strategy.symbol}</span>
                </p>
              )}
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <div className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  <span>{strategy.horizon} Horizon</span>
                </div>
                <div className="flex items-center gap-1">
                  <RefreshCw className="w-4 h-4" />
                  <span>{strategy.rebalanceFrequency} Rebalancing</span>
                </div>
                <span className={cn('px-2 py-1 rounded text-xs font-medium', riskColors[strategy.riskProfile] || 'bg-gray-100 text-gray-700')}>
                  {strategy.riskProfile}
                </span>
              </div>
            </div>
            {strategy.implemented && (
              <span className="flex items-center gap-1 px-3 py-1.5 bg-green-100 text-green-700 text-sm font-medium rounded">
                <CheckCircle className="w-4 h-4" />
                Implemented
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-amber-800">Educational Use Only</p>
            <p className="text-sm text-amber-700">
              This strategy information is for research and educational purposes.
              Past performance does not guarantee future results.
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-6">
        <div className="border-b">
          <div className="flex gap-1">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  'inline-flex items-center gap-1.5 px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors',
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                )}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="max-w-7xl mx-auto px-6 py-6">

        {/* ── Overview Tab ── */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">Strategy Concept</h2>
              <p className="text-gray-600 leading-relaxed">{strategy.overview.concept}</p>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-5">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                  <h3 className="font-semibold text-green-800">Works Well When</h3>
                </div>
                <p className="text-sm text-green-700">{strategy.overview.worksWellWhen}</p>
              </div>
              <div className="bg-red-50 border border-red-200 rounded-lg p-5">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingDown className="w-5 h-5 text-red-600" />
                  <h3 className="font-semibold text-red-800">Struggles When</h3>
                </div>
                <p className="text-sm text-red-700">{strategy.overview.strugglesWhen}</p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white rounded-lg border p-4">
                <p className="text-sm text-gray-500 mb-1">Typical Holdings</p>
                <p className="text-xl font-semibold">{strategy.overview.typicalHoldings}</p>
              </div>
              <div className="bg-white rounded-lg border p-4">
                <p className="text-sm text-gray-500 mb-1">Universe</p>
                <p className="text-xl font-semibold">{strategy.overview.universe}</p>
              </div>
              <div className="bg-white rounded-lg border p-4">
                <p className="text-sm text-gray-500 mb-1">Liquidity Profile</p>
                <p className="text-sm text-gray-700">{strategy.overview.liquidityProfile}</p>
              </div>
            </div>

            {/* ── Current Holdings (live signals) ── */}
            <div className="bg-white rounded-lg border overflow-hidden">
              <div className="p-5 border-b flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">Current Holdings</h3>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Live signal run on latest S&P 500 price data via Yahoo Finance
                  </p>
                </div>
                {liveSignals && (
                  <div className="text-right">
                    <p className="text-xs text-gray-500">Signal date</p>
                    <p className="text-sm font-medium text-gray-900">{liveSignals.signal_date}</p>
                  </div>
                )}
              </div>

              {liveSignalsLoading && (
                <div className="p-8 flex items-center justify-center gap-3 text-gray-500">
                  <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
                  <span className="text-sm">Fetching live signals…</span>
                </div>
              )}

              {liveSignalsUnavailable && !liveSignalsLoading && (
                <div className="p-6 text-center">
                  <p className="text-sm text-gray-500 mb-2">Live signals not yet generated.</p>
                  <code className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-700">
                    .venv/bin/python scripts/generate_live_signals.py
                  </code>
                </div>
              )}

              {liveSignals && !liveSignalsLoading && (
                <div className="p-5">
                  <div className="flex items-center gap-4 mb-4 text-xs text-gray-500">
                    <span><strong className="text-gray-900">{liveSignals.n_holdings}</strong> stocks in portfolio</span>
                    <span>Showing top {Math.min(liveSignals.holdings.length, 20)} by weight</span>
                    <span className="ml-auto">Source: {liveSignals.data_source}</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                    {liveSignals.holdings.slice(0, 20).map(h => (
                      <div key={h.symbol} className="flex items-center justify-between bg-gray-50 rounded px-3 py-2">
                        <span className="text-sm font-semibold text-gray-900">{h.symbol}</span>
                        <span className="text-xs text-gray-500">{(h.weight * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-gray-400 mt-3 text-right">
                    Last generated: {liveSignals.generated_at ? new Date(liveSignals.generated_at).toLocaleDateString() : '—'}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Rules Tab ── */}
        {activeTab === 'rules' && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Strategy Rules</h2>
            {strategy.rules.length > 0 ? (
              strategy.rules.map(rule => (
                <div key={rule.stepNumber} className="bg-white rounded-lg border p-5">
                  <div className="flex items-start gap-4">
                    <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-semibold text-sm flex-shrink-0">
                      {rule.stepNumber}
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900 mb-1">{rule.title}</h3>
                      <p className="text-sm text-gray-600">{rule.description}</p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="bg-white rounded-lg border p-5 text-center text-gray-500">
                Detailed rules not available for this strategy.
              </div>
            )}
          </div>
        )}

        {/* ── Performance Tab ── */}
        {activeTab === 'performance' && (
          <div className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg border p-5">
                <h3 className="font-semibold text-gray-900 mb-4">Equity Curve vs Benchmark</h3>
                <EquityCurveChart data={strategy.equityCurve} />
              </div>
              <div className="bg-white rounded-lg border p-5">
                <h3 className="font-semibold text-gray-900 mb-4">Drawdown</h3>
                <DrawdownChart data={strategy.drawdown} />
              </div>
            </div>

            <div className="bg-white rounded-lg border overflow-hidden">
              <div className="p-5 border-b">
                <h3 className="font-semibold text-gray-900">Performance Metrics <span className="text-xs font-normal text-gray-400">(25-year, 2000–2024)</span></h3>
              </div>
              <div className="p-5">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Total Return</p>
                    <p className="text-xl font-semibold text-gray-900">{formatPercent(strategy.metrics.totalReturn)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 mb-1">CAGR</p>
                    <p className="text-xl font-semibold text-gray-900">{formatPercent(strategy.metrics.cagr)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Volatility</p>
                    <p className="text-xl font-semibold text-gray-900">{formatPercent(strategy.metrics.volatility)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Sharpe Ratio</p>
                    <p className="text-xl font-semibold text-gray-900">{formatNumber(strategy.metrics.sharpeRatio)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Sortino Ratio</p>
                    <p className="text-xl font-semibold text-gray-900">{formatNumber(strategy.metrics.sortinoRatio)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Max Drawdown</p>
                    <p className="text-xl font-semibold text-red-600">{formatPercent(strategy.metrics.maxDrawdown)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Calmar Ratio</p>
                    <p className="text-xl font-semibold text-gray-900">{formatNumber(strategy.metrics.calmarRatio)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Win Rate</p>
                    <p className="text-xl font-semibold text-gray-900">{formatPercent(strategy.metrics.winRate)}</p>
                  </div>
                </div>
              </div>
            </div>

            {benchmark && (
              <div className="bg-blue-50 rounded-lg border border-blue-200 p-5">
                <h3 className="font-semibold text-blue-900 mb-3">Benchmark Comparison (Equal-Weighted S&P 500)</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-blue-700">Benchmark Return</p>
                    <p className="text-lg font-semibold text-blue-900">{formatPercent(benchmark.metrics.total_return)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-blue-700">Benchmark CAGR</p>
                    <p className="text-lg font-semibold text-blue-900">{formatPercent(benchmark.metrics.cagr)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-blue-700">Benchmark Sharpe</p>
                    <p className="text-lg font-semibold text-blue-900">{formatNumber(benchmark.metrics.sharpe_ratio)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-blue-700">Alpha vs Benchmark</p>
                    <p className={cn(
                      'text-lg font-semibold',
                      (strategy.metrics.totalReturn || 0) > (benchmark.metrics.total_return || 0)
                        ? 'text-green-700' : 'text-red-700'
                    )}>
                      {formatPercent((strategy.metrics.totalReturn || 0) - (benchmark.metrics.total_return || 0))}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Research Tab ── */}
        {activeTab === 'research' && (
          <div className="space-y-6">
            {researchLoading && (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600 mr-3" />
                <span className="text-gray-500">Loading Phase 3 research data...</span>
              </div>
            )}

            {researchError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
                Failed to load research data: {researchError}
              </div>
            )}

            {research && !researchLoading && (
              <>
                {/* Tier + data period summary */}
                <div className="bg-white rounded-lg border p-6">
                  <div className="flex flex-wrap items-center gap-4">
                    <div>
                      <p className="text-xs text-gray-500 mb-1 uppercase tracking-wide">Phase 3 Tier</p>
                      <TierBadge tier={research.scorecard?.tier} />
                    </div>
                    {research.monte_carlo && (
                      <div>
                        <p className="text-xs text-gray-500 mb-1 uppercase tracking-wide">Statistical Significance</p>
                        <VerdictBadge verdict={research.monte_carlo.verdict} />
                      </div>
                    )}
                    {research.walk_forward && (
                      <div>
                        <p className="text-xs text-gray-500 mb-1 uppercase tracking-wide">Walk-Forward</p>
                        <VerdictBadge verdict={research.walk_forward.verdict} />
                      </div>
                    )}
                    {research.data_period && (
                      <div className="ml-auto text-right">
                        <p className="text-xs text-gray-500">Data period</p>
                        <p className="text-sm font-medium text-gray-700">{research.data_period}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Scorecard numbers */}
                {research.scorecard && (
                  <div className="bg-white rounded-lg border overflow-hidden">
                    <div className="p-5 border-b">
                      <h3 className="font-semibold text-gray-900">Phase 3 Scorecard (25-year backtest)</h3>
                      <p className="text-xs text-gray-500 mt-0.5">S&P 500 benchmark Sharpe: 0.69</p>
                    </div>
                    <div className="p-5 grid grid-cols-2 md:grid-cols-5 gap-6">
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Sharpe Ratio</p>
                        <p className="text-xl font-semibold">{formatNumber(research.scorecard.sharpe)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Adj. Sharpe</p>
                        <p className="text-xl font-semibold">{formatNumber(research.scorecard.adj_sharpe)}</p>
                        <p className="text-xs text-gray-400">Pezier-White</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 mb-1">CAGR</p>
                        <p className="text-xl font-semibold">{formatPercent(research.scorecard.cagr)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Max Drawdown</p>
                        <p className="text-xl font-semibold text-red-600">{formatPercent(research.scorecard.max_drawdown)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 mb-1">% Positive Years</p>
                        <p className="text-xl font-semibold">{research.scorecard.pct_positive_years?.toFixed(0)}%</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Monte Carlo */}
                {research.monte_carlo && (
                  <div className="bg-white rounded-lg border overflow-hidden">
                    <div className="p-5 border-b">
                      <h3 className="font-semibold text-gray-900">Monte Carlo Significance Tests</h3>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {research.n_bootstrap?.toLocaleString()} bootstrap iterations · IID, block (20-day), and random-sign tests
                      </p>
                    </div>
                    <div className="p-5 space-y-4">
                      <div className="grid grid-cols-3 gap-4">
                        <div className="bg-gray-50 rounded-lg p-4">
                          <p className="text-sm font-medium text-gray-700 mb-2">IID Bootstrap</p>
                          <p className="text-lg font-semibold">p = {pVal(research.monte_carlo.iid_p_value)}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            95% CI: [{formatNumber(research.monte_carlo.iid_ci_lower)}, {formatNumber(research.monte_carlo.iid_ci_upper)}]
                          </p>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <p className="text-sm font-medium text-gray-700 mb-2">Block Bootstrap</p>
                          <p className="text-lg font-semibold">p = {pVal(research.monte_carlo.block_p_value)}</p>
                          <p className="text-xs text-gray-500 mt-1">Preserves autocorrelation</p>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <p className="text-sm font-medium text-gray-700 mb-2">Random Sign Test</p>
                          <p className="text-lg font-semibold">p = {pVal(research.monte_carlo.sign_p_value)}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            Rank: {research.monte_carlo.percentile_rank?.toFixed(1)}th pct
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Walk-Forward */}
                {research.walk_forward && (
                  <div className="bg-white rounded-lg border overflow-hidden">
                    <div className="p-5 border-b">
                      <h3 className="font-semibold text-gray-900">Walk-Forward Validation</h3>
                      <p className="text-xs text-gray-500 mt-0.5">IS: 2000–2012 · OOS: 2013–2024 · {research.walk_forward.n_folds} rolling folds</p>
                    </div>
                    <div className="p-5 space-y-4">
                      <div className="grid grid-cols-3 gap-6">
                        <div>
                          <p className="text-sm text-gray-500 mb-1">IS Sharpe</p>
                          <p className="text-2xl font-semibold">{formatNumber(research.walk_forward.is_sharpe)}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-500 mb-1">OOS Sharpe</p>
                          <p className="text-2xl font-semibold text-blue-700">{formatNumber(research.walk_forward.oos_sharpe)}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-500 mb-1">WFE</p>
                          <p className="text-2xl font-semibold text-green-700">{research.walk_forward.wfe?.toFixed(1)}%</p>
                          <p className="text-xs text-gray-400">OOS ÷ IS × 100</p>
                        </div>
                      </div>
                      {research.walk_forward.fold_oos_sharpes.length > 0 && (
                        <div>
                          <p className="text-sm text-gray-600 mb-2">Rolling fold OOS Sharpes <span className="text-gray-400 font-normal">(each pill = one 2-year OOS window)</span>:</p>
                          <div className="flex gap-2 flex-wrap">
                            {research.walk_forward.fold_oos_sharpes.map((s, i) => (
                              <span
                                key={i}
                                title={research.walk_forward?.fold_labels?.[i] ? `OOS: ${research.walk_forward.fold_labels[i]}` : `Fold ${i + 1}`}
                                className={cn(
                                  'px-2.5 py-1 rounded text-sm font-medium cursor-default',
                                  s > 0.5 ? 'bg-green-100 text-green-800' :
                                  s > 0 ? 'bg-yellow-100 text-yellow-800' :
                                  'bg-red-100 text-red-800'
                                )}
                              >
                                {research.walk_forward?.fold_labels?.[i] || `F${i + 1}`}: {s.toFixed(2)}
                              </span>
                            ))}
                          </div>
                          <p className="text-xs text-gray-400 mt-2">
                            Avg OOS: {formatNumber(research.walk_forward.avg_oos_sharpe)} · Avg WFE: {research.walk_forward.avg_wfe?.toFixed(1)}%
                          </p>
                        </div>
                      )}
                      <div className="bg-amber-50 border border-amber-200 rounded p-3">
                        <p className="text-xs text-amber-800">
                          <strong>Caveat:</strong> WFE &gt;100% is partly a regime artifact — IS period (2000–2012)
                          included 3 bear markets; OOS (2013–2024) was predominantly a bull market. The genuine
                          stress test is Fold 2 (GFC 2008–09) where all strategies posted negative Sharpe.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Regime breakdown */}
                {research.regime && (
                  <div className="bg-white rounded-lg border overflow-hidden">
                    <div className="p-5 border-b">
                      <h3 className="font-semibold text-gray-900">Regime Performance Breakdown</h3>
                      <p className="text-xs text-gray-500 mt-0.5">
                        Best: <strong>{research.regime.best_regime}</strong> · Worst: <strong>{research.regime.worst_regime}</strong>
                      </p>
                    </div>
                    <div className="p-5">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="text-left text-gray-500 border-b">
                            <th className="pb-2 font-medium">Regime</th>
                            <th className="pb-2 font-medium text-right">Annualised Sharpe</th>
                            <th className="pb-2 font-medium text-right">Assessment</th>
                          </tr>
                        </thead>
                        <tbody>
                          {regimeRows.map(row => (
                            <tr key={row.label} className="border-b last:border-0">
                              <td className="py-3 text-gray-700">{row.label}</td>
                              <td className={cn('py-3 text-right', regimeColor(row.value))}>
                                {formatNumber(row.value)}
                              </td>
                              <td className="py-3 text-right text-xs text-gray-500">
                                {row.value === null ? '' :
                                  row.value > 1 ? 'Strong edge' :
                                  row.value > 0 ? 'Modest edge' :
                                  row.value > -0.5 ? 'Slight drag' :
                                  'Significant drag'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      <p className="text-xs text-gray-400 mt-3">
                        All strategies fail in Bear regime (Sharpe &lt; −1.2). Regime overlay does not reliably improve risk-adjusted returns over 25 years due to signal lag vs crash speed.
                      </p>
                    </div>
                  </div>
                )}

                {/* ── Factor Attribution (CAPM) ── */}
                {factorAlpha && (
                  <div className="bg-white rounded-lg border overflow-hidden">
                    <div className="p-5 border-b">
                      <h3 className="font-semibold text-gray-900">Factor Attribution — CAPM Decomposition</h3>
                      <p className="text-xs text-gray-500 mt-1">
                        CAPM regression: r<sub>strategy</sub> − r<sub>f</sub> = α + β × (r<sub>market</sub> − r<sub>f</sub>)
                        &nbsp;·&nbsp; 25-year dataset · r<sub>f</sub> = 2%/yr
                      </p>
                    </div>
                    <div className="p-5 space-y-4">
                      <div className="grid grid-cols-3 gap-4">
                        <div className="text-center">
                          <p className="text-xs text-gray-500 mb-1">Market Beta (β)</p>
                          <p className={cn(
                            'text-2xl font-bold',
                            (factorAlpha.capm.beta ?? 1) > 1.1 ? 'text-orange-600' :
                            (factorAlpha.capm.beta ?? 1) < 0.8 ? 'text-blue-600' : 'text-gray-800'
                          )}>
                            {factorAlpha.capm.beta?.toFixed(2) ?? 'N/A'}
                          </p>
                          <p className="text-xs text-gray-400 mt-0.5">
                            {(factorAlpha.capm.beta ?? 1) > 1.05 ? 'Levered market bet' :
                             (factorAlpha.capm.beta ?? 1) < 0.85 ? 'Defensive / low-beta' : 'Market-like exposure'}
                          </p>
                        </div>
                        <div className="text-center">
                          <p className="text-xs text-gray-500 mb-1">Annual Alpha (α)</p>
                          <p className={cn(
                            'text-2xl font-bold',
                            (factorAlpha.capm.alpha_annual ?? 0) > 0.01 ? 'text-green-600' :
                            (factorAlpha.capm.alpha_annual ?? 0) < -0.005 ? 'text-red-600' : 'text-gray-500'
                          )}>
                            {factorAlpha.capm.alpha_annual !== null
                              ? `${(factorAlpha.capm.alpha_annual * 100).toFixed(1)}%`
                              : 'N/A'}
                          </p>
                          <p className="text-xs text-gray-400 mt-0.5">Return unexplained by market</p>
                        </div>
                        <div className="text-center">
                          <p className="text-xs text-gray-500 mb-1">R² (market explains)</p>
                          <p className="text-2xl font-bold text-gray-800">
                            {factorAlpha.capm.r_squared !== null
                              ? `${(factorAlpha.capm.r_squared * 100).toFixed(0)}%`
                              : 'N/A'}
                          </p>
                          <p className="text-xs text-gray-400 mt-0.5">
                            {(factorAlpha.capm.r_squared ?? 0) > 0.85
                              ? 'Mostly market-driven'
                              : 'Meaningful independent return'}
                          </p>
                        </div>
                      </div>

                      <div className="border-t pt-4">
                        <p className="text-xs text-gray-600 leading-relaxed">
                          <strong>What this means:</strong> β = {factorAlpha.capm.beta?.toFixed(2) ?? '?'} means for every 1%
                          the market moves, this strategy moves {factorAlpha.capm.beta?.toFixed(2) ?? '?'}%.
                          R² = {((factorAlpha.capm.r_squared ?? 0) * 100).toFixed(0)}% of its return variance
                          is explained by market exposure alone.
                          The remaining {(100 - (factorAlpha.capm.r_squared ?? 0) * 100).toFixed(0)}% + the
                          α = {factorAlpha.capm.alpha_annual !== null
                            ? `${(factorAlpha.capm.alpha_annual * 100).toFixed(1)}%/yr`
                            : 'N/A'} represents the pure factor premium —
                          the return you would capture in a dollar-neutral (long strategy, short market) portfolio.
                        </p>
                      </div>

                      <div className="grid grid-cols-2 gap-4 border-t pt-4 text-sm">
                        <div>
                          <p className="text-xs text-gray-500 font-medium mb-2">Long-Only (current strategy)</p>
                          <div className="space-y-1">
                            <div className="flex justify-between">
                              <span className="text-gray-500">CAGR</span>
                              <span className="font-medium">{factorAlpha.longonly.cagr !== null ? `${(factorAlpha.longonly.cagr * 100).toFixed(1)}%` : 'N/A'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">Sharpe</span>
                              <span className="font-medium">{factorAlpha.longonly.sharpe_ratio?.toFixed(2) ?? 'N/A'}</span>
                            </div>
                          </div>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 font-medium mb-2">Benchmark (Equal-Wt S&P 500)</p>
                          <div className="space-y-1">
                            <div className="flex justify-between">
                              <span className="text-gray-500">CAGR</span>
                              <span className="font-medium">{factorAlpha.benchmark.cagr !== null ? `${(factorAlpha.benchmark.cagr * 100).toFixed(1)}%` : 'N/A'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">Sharpe</span>
                              <span className="font-medium">{factorAlpha.benchmark.sharpe_ratio?.toFixed(2) ?? 'N/A'}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* ── Long-Short Equity Curve ── */}
                {factorAlpha && factorAlpha.longshort.equity_curve?.length > 0 && (
                  <div className="bg-white rounded-lg border overflow-hidden">
                    <div className="p-5 border-b">
                      <h3 className="font-semibold text-gray-900">Dollar-Neutral Long-Short Portfolio</h3>
                      <p className="text-xs text-gray-500 mt-1">
                        Long top-quintile stocks, short bottom-quintile — market beta removed.
                        This isolates the pure factor return, stripped of systematic market exposure.
                      </p>
                    </div>
                    <div className="p-5">
                      {/* Metrics row */}
                      <div className="grid grid-cols-4 gap-4 mb-5">
                        {[
                          { label: 'CAGR', value: factorAlpha.longshort.cagr !== null ? `${(factorAlpha.longshort.cagr * 100).toFixed(1)}%` : 'N/A', positive: (factorAlpha.longshort.cagr ?? 0) > 0 },
                          { label: 'Sharpe', value: factorAlpha.longshort.sharpe_ratio?.toFixed(2) ?? 'N/A', positive: (factorAlpha.longshort.sharpe_ratio ?? 0) > 0 },
                          { label: 'Max DD', value: factorAlpha.longshort.max_drawdown !== null ? `${(factorAlpha.longshort.max_drawdown * 100).toFixed(1)}%` : 'N/A', positive: false },
                          { label: 'Market Corr', value: factorAlpha.longshort.market_correlation?.toFixed(2) ?? 'N/A', positive: Math.abs(factorAlpha.longshort.market_correlation ?? 1) < 0.3 },
                        ].map(m => (
                          <div key={m.label} className="text-center bg-gray-50 rounded-lg p-3">
                            <p className="text-xs text-gray-500 mb-1">{m.label}</p>
                            <p className={cn('text-lg font-bold', m.positive ? 'text-emerald-600' : m.label === 'Max DD' ? 'text-red-600' : 'text-gray-800')}>
                              {m.value}
                            </p>
                          </div>
                        ))}
                      </div>
                      {/* Equity curve */}
                      <EquityCurveChart
                        data={factorAlpha.longshort.equity_curve.map(p => ({
                          date: p.date,
                          strategy: p.value * 1_000_000,
                        }))}
                      />
                      <p className="text-xs text-gray-400 mt-2 text-center">
                        Normalized to $1M start. Monthly rebalancing. 2000–2025. Transaction costs included.
                      </p>
                      <div className="mt-3 p-3 bg-amber-50 rounded-lg border border-amber-100">
                        <p className="text-xs text-gray-600 leading-relaxed">
                          <strong>Why this matters:</strong> When all 14 long-only strategies "lag the benchmark," it's because
                          the benchmark itself has high beta (β≈1). The long-short portfolio strips that market component out —
                          what remains is the pure factor premium. A positive Sharpe here means the factor generates real alpha
                          independent of whether markets are rising or falling.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* ── Parameters Tab ── */}
        {activeTab === 'parameters' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg border p-5">
              <h2 className="text-lg font-semibold text-gray-900 mb-1">Parameter Tuning</h2>
              <p className="text-sm text-gray-500">
                Adjust strategy parameters and run a quick backtest on the full 25-year dataset (2000–2024) to see how performance changes.
                Robustness labels are from Phase 2 sensitivity analysis.
              </p>
            </div>

            {paramLoading && (
              <div className="flex items-center gap-3 py-8 justify-center text-gray-500">
                <Loader2 className="w-5 h-5 animate-spin" />
                Loading parameters...
              </div>
            )}

            {!paramLoading && paramDefs.length === 0 && (
              <div className="bg-white rounded-lg border p-6 text-center text-gray-500">
                No tunable parameters defined for this strategy.
              </div>
            )}

            {!paramLoading && paramDefs.length > 0 && (
              <>
                <div className="bg-white rounded-lg border divide-y">
                  {paramDefs.map(param => (
                    <div key={param.name} className="p-5">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-gray-900">{param.label}</span>
                            <span className={cn(
                              'text-xs px-2 py-0.5 rounded font-medium',
                              param.robustness === 'ROBUST'
                                ? 'bg-green-100 text-green-700'
                                : 'bg-red-100 text-red-700'
                            )}>
                              {param.robustness}
                            </span>
                          </div>
                          <p className="text-xs text-gray-500 mt-0.5">{param.description}</p>
                        </div>
                        <span className="text-lg font-semibold text-blue-700 min-w-[4rem] text-right">
                          {paramValues[param.name] ?? param.default}
                        </span>
                      </div>
                      <input
                        type="range"
                        min={param.min}
                        max={param.max}
                        step={param.step}
                        value={paramValues[param.name] ?? param.default}
                        onChange={e => setParamValues(prev => ({
                          ...prev,
                          [param.name]: parseFloat(e.target.value),
                        }))}
                        className="w-full accent-blue-600"
                      />
                      <div className="flex justify-between text-xs text-gray-400 mt-1">
                        <span>{param.min}</span>
                        <span className="text-gray-500">default: {param.default}</span>
                        <span>{param.max}</span>
                      </div>
                    </div>
                  ))}
                </div>

                <button
                  onClick={handleRunBacktest}
                  disabled={backtestRunning}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg font-medium transition-colors"
                >
                  {backtestRunning
                    ? <><Loader2 className="w-4 h-4 animate-spin" /> Running...</>
                    : <><Play className="w-4 h-4" /> Run Backtest</>}
                </button>

                {backtestError && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
                    {backtestError}
                  </div>
                )}

                {backtestResult && (
                  <div className="bg-white rounded-lg border overflow-hidden">
                    <div className="p-5 border-b flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <h3 className="font-semibold text-gray-900">Custom Backtest Results</h3>
                      <span className="text-xs text-gray-500 ml-1">(2000–2024, 25-year)</span>
                    </div>
                    <div className="p-5 grid grid-cols-2 md:grid-cols-4 gap-6">
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Total Return</p>
                        <p className="text-xl font-semibold">{formatPercent(backtestResult.metrics.total_return as number)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 mb-1">CAGR</p>
                        <p className="text-xl font-semibold">{formatPercent(backtestResult.metrics.cagr as number)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Sharpe Ratio</p>
                        <p className="text-xl font-semibold">{formatNumber(backtestResult.metrics.sharpe_ratio as number)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Max Drawdown</p>
                        <p className="text-xl font-semibold text-red-600">{formatPercent(backtestResult.metrics.max_drawdown as number)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Volatility</p>
                        <p className="text-xl font-semibold">{formatPercent(backtestResult.metrics.volatility as number)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Sortino Ratio</p>
                        <p className="text-xl font-semibold">{formatNumber(backtestResult.metrics.sortino_ratio as number)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Calmar Ratio</p>
                        <p className="text-xl font-semibold">{formatNumber(backtestResult.metrics.calmar_ratio as number)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Win Rate</p>
                        <p className="text-xl font-semibold">{formatPercent(backtestResult.metrics.win_rate as number)}</p>
                      </div>
                    </div>
                    {backtestResult.equityCurve.length > 0 && (
                      <div className="px-5 pb-5">
                        <EquityCurveChart data={backtestResult.equityCurve.map(p => ({
                          date: p.date,
                          strategy: p.equity,
                        }))} />
                      </div>
                    )}
                  </div>
                )}
              </>
            )}

            {/* ── Sensitivity Analysis ── */}
            {sensitivity && (
              <div className="bg-white rounded-lg border p-5">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold text-gray-900">Parameter Robustness Analysis</h3>
                  <span className="text-xs text-gray-400">(Phase 2 sensitivity sweep — 4-year dataset)</span>
                </div>
                <p className="text-xs text-gray-500 mb-4">
                  Each cell shows the Sharpe ratio at a different parameter combination.
                  Blue star (★) = current default. A wide green band = <strong>ROBUST</strong>.
                  A single bright spot = <strong>FRAGILE</strong> (overfit to specific parameters).
                </p>
                <SensitivityHeatmap
                  heatmap={sensitivity.heatmap}
                  sweeps={sensitivity.sweep_1d}
                  defaults={sensitivity.defaults}
                />
              </div>
            )}
          </div>
        )}

        {/* ── Rolling Metrics Tab ── */}
        {activeTab === 'rolling' && (
          <div className="space-y-6">
            {rollingLoading && (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600 mr-3" />
                <span className="text-gray-500">Loading annual performance data...</span>
              </div>
            )}

            {!rollingLoading && rolling && (
              <>
                {/* Summary */}
                <div className="bg-white rounded-lg border p-5 flex flex-wrap items-center gap-6">
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Data Period</p>
                    <p className="font-medium text-gray-900">{rolling.data_period ?? 'N/A'} · {rolling.n_years} years</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Rank Stability (YoY Spearman)</p>
                    <p className={cn('font-semibold text-lg', (rolling.rank_stability ?? 0) > 0.3 ? 'text-green-700' : 'text-red-600')}>
                      {rolling.rank_stability !== null ? rolling.rank_stability.toFixed(3) : 'N/A'}
                    </p>
                  </div>
                  <p className="text-xs text-gray-400 ml-auto max-w-xs text-right">
                    Rank stability near 0 or negative means strategy leadership changes randomly year-to-year — no consistent winner.
                  </p>
                </div>

                {/* Metric selector */}
                <div className="bg-white rounded-lg border overflow-hidden">
                  <div className="p-5 border-b flex items-center gap-4">
                    <h3 className="font-semibold text-gray-900">Annual Performance vs Benchmark</h3>
                    <div className="flex gap-1 ml-auto">
                      {(['sharpe', 'cagr', 'mdd'] as const).map(m => (
                        <button
                          key={m}
                          onClick={() => setRollingMetric(m)}
                          className={cn(
                            'px-3 py-1 text-xs rounded font-medium transition-colors',
                            rollingMetric === m
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          )}
                        >
                          {m === 'sharpe' ? 'Sharpe' : m === 'cagr' ? 'Return' : 'Max DD'}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="p-5">
                    <AnnualBarChart
                      data={rollingMetric === 'sharpe' ? rolling.annual_sharpe :
                            rollingMetric === 'cagr' ? rolling.annual_cagr : rolling.annual_mdd}
                      metric={rollingMetric}
                      strategyLabel={strategy.displayName}
                      benchmarkAvg={rollingMetric === 'sharpe' ? rollingBenchmarkAvg.sharpe :
                                    rollingMetric === 'cagr' ? rollingBenchmarkAvg.cagr :
                                    rollingBenchmarkAvg.mdd}
                    />
                  </div>
                </div>

                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-xs text-amber-800">
                  <strong>Key insight:</strong> Performance is concentrated in 2016–2017 and 2019–2021 bull markets.
                  Dot-com (2000–2002), GFC (2008–2009), and 2022 bear years show uniform losses across all strategies.
                  The rank_stability of −0.123 (UNSTABLE) confirms there is no consistent winner — selecting based on
                  recent annual performance is unreliable.
                </div>
              </>
            )}

            {!rollingLoading && !rolling && (
              <div className="bg-white rounded-lg border p-8 text-center text-gray-500">
                Rolling performance data not available.
              </div>
            )}
          </div>
        )}

        {/* ── Correlation Tab ── */}
        {activeTab === 'correlation' && (
          <div className="space-y-6">
            {correlationLoading && (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600 mr-3" />
                <span className="text-gray-500">Loading correlation matrix...</span>
              </div>
            )}

            {!correlationLoading && correlation && (
              <>
                <div className="bg-white rounded-lg border p-5 flex flex-wrap items-center gap-6">
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Avg Pairwise Correlation</p>
                    <p className="font-semibold text-2xl text-red-700">{correlation.avg_correlation?.toFixed(3)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Diversification Ratio</p>
                    <p className="font-semibold text-2xl text-gray-700">{correlation.diversification_ratio?.toFixed(3)}</p>
                    <p className="text-xs text-gray-400">≈1.0 = no diversification benefit</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Data Period</p>
                    <p className="font-medium text-gray-700">{correlation.data_period ?? '2000–2024'}</p>
                  </div>
                  <p className="text-xs text-gray-400 ml-auto max-w-xs text-right">
                    All 14 strategies have avg pairwise correlation &gt;0.90 over 25 years — they are essentially the same long-equity bet.
                  </p>
                </div>

                <div className="bg-white rounded-lg border p-5 overflow-x-auto">
                  <h3 className="font-semibold text-gray-900 mb-4">14 × 14 Pairwise Correlation Matrix (2000–2024)</h3>
                  <CorrelationHeatmap strategies={correlation.strategies} cells={correlation.cells} />
                </div>

                <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-xs text-red-800">
                  <strong>Phase 3 finding:</strong> 90/91 strategy pairs have r &gt; 0.80. In bear markets (GFC, COVID, 2022)
                  pairwise correlation spikes to 0.969. Diversification ratio ≈ 1.024 ≈ 1.0, meaning combining
                  any subset of these strategies provides almost no volatility reduction. All factor strategies
                  are essentially a leveraged long-equity position that fails simultaneously during crashes.
                </div>
              </>
            )}

            {!correlationLoading && !correlation && (
              <div className="bg-white rounded-lg border p-8 text-center text-gray-500">
                Correlation data not available.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
