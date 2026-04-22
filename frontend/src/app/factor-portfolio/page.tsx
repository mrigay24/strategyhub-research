'use client'

export const dynamic = 'force-dynamic'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { ArrowLeft, Loader2, AlertCircle, TrendingUp, Info, CheckCircle2, XCircle } from 'lucide-react'
import {
  fetchLSPortfolio, fetchLSWalkForward,
  type LSPortfolioData, type LSWalkForwardData,
} from '@/lib/api'
import { EquityCurveChart } from '@/components/charts/EquityCurveChart'
import { cn } from '@/lib/utils'

const STRATEGY_DISPLAY: Record<string, string> = {
  large_cap_momentum:         'Large Cap Momentum',
  '52_week_high_breakout':    '52-Week High',
  deep_value_all_cap:         'Deep Value',
  high_quality_roic:          'High Quality ROIC',
  low_volatility_shield:      'Low Volatility',
  dividend_aristocrats:       'Dividend Aristocrats',
  moving_average_trend:       'MA Trend',
  rsi_mean_reversion:         'RSI Mean Reversion',
  value_momentum_blend:       'Value + Momentum',
  quality_momentum:           'Quality Momentum',
  quality_low_vol:            'Quality + Low Vol',
  composite_factor_score:     'Composite Factor',
  volatility_targeting:       'Volatility Targeting',
  earnings_surprise_momentum: 'Earnings Surprise',
  equal_weight_combo:         'Equal-Weight Combo (3)',
}

function fmt(v: number | null | undefined, pct = false, dec = 2): string {
  if (v == null || isNaN(v)) return 'N/A'
  const x = pct ? v * 100 : v
  const s = Math.abs(x).toFixed(dec)
  const sign = x < 0 ? '-' : ''
  return `${sign}${s}${pct ? '%' : ''}`
}

function MetricTile({ label, value, positive, isDD = false }: {
  label: string; value: string; positive: boolean; isDD?: boolean
}) {
  return (
    <div className="text-center bg-gray-50 rounded-lg p-3">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={cn('text-lg font-bold',
        isDD ? 'text-red-600' : positive ? 'text-emerald-600' : 'text-red-600'
      )}>{value}</p>
    </div>
  )
}

function VerdictBadge({ verdict }: { verdict: string }) {
  const colors: Record<string, string> = {
    STRONG:     'bg-emerald-100 text-emerald-800',
    CONSISTENT: 'bg-blue-100 text-blue-800',
    MIXED:      'bg-yellow-100 text-yellow-800',
    WEAK:       'bg-red-100 text-red-800',
  }
  return (
    <span className={cn('px-2 py-0.5 rounded text-xs font-semibold', colors[verdict] ?? 'bg-gray-100 text-gray-700')}>
      {verdict}
    </span>
  )
}

// ── Walk-Forward Tab ──────────────────────────────────────────────────────────

function WalkForwardTab({ wf }: { wf: LSWalkForwardData }) {
  const strategies = [...wf.focus_strategies, 'equal_weight_combo']
  const FOCUS_DISPLAY = strategies.map(s => STRATEGY_DISPLAY[s] ?? s)

  // Build rolling chart data for equal_weight_combo
  const rollingSeries = wf.rolling_12m_sharpe['equal_weight_combo'] ?? []

  const FOLD_COLORS = [
    { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700' },
    { bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-700' },
    { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700' },
    { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700' },
  ]

  return (
    <div className="space-y-8">
      {/* Insight banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-5">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-600 mt-0.5 shrink-0" />
          <div>
            <p className="font-semibold text-blue-900 mb-1">Why walk-forward matters for factor strategies</p>
            <p className="text-sm text-blue-800 leading-relaxed">
              L/S factor strategies have no fit parameters — so walk-forward validation answers a different question:{' '}
              <strong>&ldquo;Is the cross-sectional factor signal economically persistent into unseen future data?&rdquo;</strong>{' '}
              The honest answer: <em>yes in 3 of 4 regimes</em>, no during the GFC (2005–2009) when credit stress
              overwhelmed all factor signals. The equal-weight combination achieves 4/4 positive folds.
            </p>
          </div>
        </div>
      </div>

      {/* Summary table */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <div className="p-5 border-b">
          <h2 className="font-semibold text-gray-900">Walk-Forward Summary</h2>
          <p className="text-xs text-gray-500 mt-0.5">Expanding IS window · 5-year OOS folds · 4 folds (2000–2024)</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-y">
              <tr>
                <th className="text-left px-4 py-2.5 font-medium text-gray-600">Strategy</th>
                <th className="text-right px-4 py-2.5 font-medium text-gray-600">Avg OOS Sharpe</th>
                <th className="text-right px-4 py-2.5 font-medium text-gray-600">% Positive Folds</th>
                <th className="text-right px-4 py-2.5 font-medium text-gray-600">Avg WFE</th>
                <th className="text-right px-4 py-2.5 font-medium text-gray-600">Verdict</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {strategies.map(name => {
                const s = wf.summary[name]
                if (!s) return null
                return (
                  <tr key={name} className={cn('hover:bg-gray-50', name === 'equal_weight_combo' && 'bg-blue-50/40')}>
                    <td className="px-4 py-3 font-medium text-gray-900">
                      {STRATEGY_DISPLAY[name] ?? name}
                      {name === 'equal_weight_combo' && (
                        <span className="ml-2 text-xs text-blue-600 font-normal">recommended</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right font-semibold">
                      <span className={(s.avg_oos_sharpe ?? 0) > 0.4 ? 'text-emerald-600' : (s.avg_oos_sharpe ?? 0) > 0 ? 'text-yellow-600' : 'text-red-600'}>
                        {fmt(s.avg_oos_sharpe)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-gray-700">
                      {s.pct_folds_positive.toFixed(0)}%
                    </td>
                    <td className="px-4 py-3 text-right text-gray-700">
                      {s.avg_wfe_pct != null ? `${s.avg_wfe_pct.toFixed(0)}%` : 'N/A'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <VerdictBadge verdict={s.verdict} />
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Per-fold breakdown */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <div className="p-5 border-b">
          <h2 className="font-semibold text-gray-900">Fold-by-Fold Breakdown</h2>
          <p className="text-xs text-gray-500 mt-0.5">IS = In-Sample (expanding) · OOS = Out-of-Sample (5-year window) · WFE = OOS SR / IS SR × 100%</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-gray-50 border-y">
              <tr>
                <th className="text-left px-3 py-2 font-medium text-gray-600">Fold</th>
                <th className="text-left px-3 py-2 font-medium text-gray-600">OOS Period</th>
                <th className="text-left px-3 py-2 font-medium text-gray-600">Strategy</th>
                <th className="text-right px-3 py-2 font-medium text-gray-600">IS SR</th>
                <th className="text-right px-3 py-2 font-medium text-gray-600">OOS SR</th>
                <th className="text-right px-3 py-2 font-medium text-gray-600">WFE</th>
                <th className="text-right px-3 py-2 font-medium text-gray-600">OOS CAGR</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {wf.folds.map((fold, fi) => {
                const color = FOLD_COLORS[fi % FOLD_COLORS.length]
                return strategies.map((name, si) => {
                  const s = fold.strategies[name]
                  if (!s) return null
                  const oosPositive = (s.oos_sharpe ?? 0) > 0
                  return (
                    <tr key={`${fi}-${name}`} className="hover:bg-gray-50">
                      {si === 0 && (
                        <>
                          <td rowSpan={strategies.length} className={cn('px-3 py-2 font-medium align-top', color.text)}>
                            <span className={cn('px-1.5 py-0.5 rounded text-xs', color.bg, color.border, 'border')}>
                              {fold.label}
                            </span>
                          </td>
                          <td rowSpan={strategies.length} className="px-3 py-2 text-gray-500 align-top text-xs">
                            {fold.oos_period}
                          </td>
                        </>
                      )}
                      <td className="px-3 py-2 text-gray-700">{STRATEGY_DISPLAY[name] ?? name}</td>
                      <td className="px-3 py-2 text-right text-gray-600">{fmt(s.is_sharpe)}</td>
                      <td className={cn('px-3 py-2 text-right font-semibold', oosPositive ? 'text-emerald-600' : 'text-red-600')}>
                        {fmt(s.oos_sharpe)}
                      </td>
                      <td className="px-3 py-2 text-right text-gray-600">
                        {s.wfe_pct != null ? `${s.wfe_pct.toFixed(0)}%` : 'N/A'}
                      </td>
                      <td className={cn('px-3 py-2 text-right', (s.oos_stats.cagr ?? 0) >= 0 ? 'text-gray-700' : 'text-red-600')}>
                        {fmt(s.oos_stats.cagr, true, 1)}
                      </td>
                    </tr>
                  )
                })
              })}
            </tbody>
          </table>
        </div>
        <div className="px-5 pb-4 pt-2 bg-amber-50 border-t border-amber-200">
          <p className="text-xs text-amber-800">
            <strong>GFC fold (2005–2009):</strong> All factor strategies went negative OOS.
            Credit market stress overwhelmed cross-sectional factor signals — a systematic event that factor models cannot hedge.
            Outside of crisis regimes, all strategies show strong persistence (SR 0.67–1.74).
          </p>
        </div>
      </div>

      {/* Decade analysis */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <div className="p-5 border-b">
          <h2 className="font-semibold text-gray-900">Decade Analysis</h2>
          <p className="text-xs text-gray-500 mt-0.5">Is the factor premium consistent across market eras?</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-gray-50 border-y">
              <tr>
                <th className="text-left px-3 py-2 font-medium text-gray-600">Period</th>
                {strategies.map(name => (
                  <th key={name} className="text-right px-3 py-2 font-medium text-gray-600">
                    {name === 'equal_weight_combo' ? 'EqWt Combo' : STRATEGY_DISPLAY[name]?.split(' ').slice(0, 2).join(' ')}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {wf.decade_analysis.map(decade => (
                <tr key={decade.label} className="hover:bg-gray-50">
                  <td className="px-3 py-2 text-gray-700 font-medium">
                    {decade.label.split('(')[0].trim()}
                    <span className="text-gray-400 font-normal ml-1 text-xs">
                      ({decade.label.match(/\(([^)]+)\)/)?.[1]})
                    </span>
                  </td>
                  {strategies.map(name => {
                    const s = decade.strategies[name]
                    const sr = s?.sharpe ?? null
                    return (
                      <td key={name} className={cn('px-3 py-2 text-right font-semibold',
                        sr == null ? 'text-gray-300'
                        : sr > 0.5 ? 'text-emerald-600'
                        : sr > 0 ? 'text-yellow-600'
                        : 'text-red-600'
                      )}>
                        {fmt(sr)}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="px-5 pb-4 pt-3 grid grid-cols-3 gap-3 border-t bg-gray-50">
          <div className="text-center">
            <p className="text-xs text-gray-500">Best period</p>
            <p className="text-sm font-semibold text-emerald-600">2010–2014</p>
            <p className="text-xs text-gray-400">Post-crisis factor rebound (SR 1.1–1.7)</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-500">Worst period</p>
            <p className="text-sm font-semibold text-red-600">2005–2009</p>
            <p className="text-xs text-gray-400">GFC — all factors negative</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-500">Most consistent</p>
            <p className="text-sm font-semibold text-blue-600">Equal-Weight Combo</p>
            <p className="text-xs text-gray-400">4/5 decades positive</p>
          </div>
        </div>
      </div>

      {/* Rolling 12m Sharpe */}
      {rollingSeries.length > 0 && (
        <div className="bg-white rounded-lg border overflow-hidden">
          <div className="p-5 border-b">
            <h2 className="font-semibold text-gray-900">Rolling 12-Month Sharpe — Equal-Weight Combo</h2>
            <p className="text-xs text-gray-500 mt-0.5">Does the signal persist month-to-month, or is it episodic?</p>
          </div>
          <div className="p-5">
            <EquityCurveChart
              data={rollingSeries
                .filter(p => p.sharpe != null)
                .map(p => ({ date: p.date, strategy: (p.sharpe ?? 0) + 2 }))}
            />
            <p className="text-xs text-gray-400 mt-2 text-center">
              Values offset by +2 for chart scaling. Chart value of 2.0 = Sharpe 0.0 (breakeven line).
            </p>
          </div>
        </div>
      )}

      {/* Key takeaways */}
      <div className="bg-white rounded-lg border p-5">
        <h2 className="font-semibold text-gray-900 mb-3">Key Takeaways</h2>
        <div className="grid grid-cols-2 gap-3 text-sm">
          {[
            { icon: CheckCircle2, color: 'text-emerald-500', text: 'All 4 strategies earn STRONG verdict — avg OOS Sharpe 0.72–0.88 across 25 years.' },
            { icon: CheckCircle2, color: 'text-emerald-500', text: 'Equal-Weight Combo achieves 4/4 positive OOS folds — no single factor dominates.' },
            { icon: CheckCircle2, color: 'text-emerald-500', text: 'Post-GFC rebound (2010–2014) shows WFE 331–588% — factor premia were historically compressed and then released.' },
            { icon: XCircle, color: 'text-red-500', text: 'GFC fold (2005–2009) all negative OOS — systematic credit crisis overwhelms factor signals. This is not curve-fitting, it is an honest finding.' },
          ].map(({ icon: Icon, color, text }, i) => (
            <div key={i} className="flex items-start gap-2">
              <Icon className={cn('w-4 h-4 mt-0.5 shrink-0', color)} />
              <p className="text-gray-700 text-xs leading-relaxed">{text}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function FactorPortfolioPage() {
  const [portfolioData, setPortfolioData] = useState<LSPortfolioData | null>(null)
  const [wfData, setWfData] = useState<LSWalkForwardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activePortfolio, setActivePortfolio] = useState<'equal_weight_pos' | 'risk_parity_pos' | 'max_sharpe_pos'>('max_sharpe_pos')
  const [activeTab, setActiveTab] = useState<'portfolio' | 'walkforward'>('portfolio')

  useEffect(() => {
    Promise.all([fetchLSPortfolio(), fetchLSWalkForward()])
      .then(([p, wf]) => { setPortfolioData(p); setWfData(wf) })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-[calc(100vh-56px)]">
      <Loader2 className="w-6 h-6 animate-spin text-blue-600 mr-3" />
      <span className="text-gray-500">Loading portfolio analysis…</span>
    </div>
  )

  if (error || !portfolioData) return (
    <div className="flex items-center justify-center h-[calc(100vh-56px)]">
      <div className="text-center max-w-md">
        <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-3" />
        <p className="text-gray-700 font-medium mb-1">Failed to load data</p>
        <p className="text-gray-400 text-sm">{error}</p>
        <p className="text-gray-400 text-xs mt-2">Make sure the API server is running and ls_portfolio_analysis.py has been run.</p>
      </div>
    </div>
  )

  const data = portfolioData
  const port = data.portfolios[activePortfolio]
  const ms = data.portfolios.max_sharpe_pos
  const regimes = data.regime_metrics.max_sharpe_portfolio
  const crisisLabels: Record<string, string> = {
    dot_com_bust:   'Dot-com bust (2000–02)',
    gfc:            'GFC (2007–09)',
    covid_crash:    'COVID crash (2020)',
    rate_hike_2022: 'Rate hike (2022)',
  }

  const pairs = data.best_pairs.filter(p => p.n === 2).slice(0, 5)
  const trips = data.best_pairs.filter(p => p.n === 3).slice(0, 5)

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">
      {/* Nav + Header */}
      <div>
        <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-4">
          <ArrowLeft className="w-4 h-4" /> Dashboard
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Multi-Factor L/S Portfolio</h1>
            <p className="text-gray-500 mt-1 text-sm">
              Beta-neutral factor combination · 25-year backtest (2000–2024) · {data.data_period}
            </p>
          </div>
          <span className="px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-sm font-semibold">
            Max-Sharpe SR: {ms.sharpe?.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Top-level tabs */}
      <div className="flex border-b">
        {([
          ['portfolio',    'Portfolio Construction'],
          ['walkforward',  'Walk-Forward Validation'],
        ] as const).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={cn(
              'px-5 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px',
              activeTab === key
                ? 'border-blue-600 text-blue-700'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            )}
          >{label}</button>
        ))}
      </div>

      {/* Walk-Forward Tab */}
      {activeTab === 'walkforward' && wfData && <WalkForwardTab wf={wfData} />}

      {/* Portfolio Tab */}
      {activeTab === 'portfolio' && (
        <>
          {/* The Core Insight */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-5">
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-blue-600 mt-0.5 shrink-0" />
              <div>
                <p className="font-semibold text-blue-900 mb-1">Why combination works here but not for long-only</p>
                <p className="text-sm text-blue-800 leading-relaxed">
                  Long-only strategies all move with the market (avg correlation = <strong>0.951</strong>) — combining 14 of them
                  gives almost no diversification benefit (Diversification Ratio = 1.024).
                  Strip out the market beta via dollar-neutral L/S construction and the same strategies
                  have avg correlation = <strong>{data.correlation_stats.avg.toFixed(3)}</strong> — that&apos;s{' '}
                  <strong>{data.correlation_stats.improvement_factor}× more diversifiable</strong>.
                  A max-Sharpe combination reaches SR = <strong>{ms.sharpe?.toFixed(2)}</strong>, above any individual strategy.
                </p>
              </div>
            </div>
          </div>

          {/* Correlation summary tiles */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-white rounded-lg border p-5 text-center">
              <p className="text-xs text-gray-500 mb-1">Avg L/S Pairwise Corr</p>
              <p className="text-3xl font-bold text-emerald-600">{data.correlation_stats.avg.toFixed(3)}</p>
              <p className="text-xs text-gray-400 mt-1">vs 0.951 long-only</p>
            </div>
            <div className="bg-white rounded-lg border p-5 text-center">
              <p className="text-xs text-gray-500 mb-1">Diversification Factor</p>
              <p className="text-3xl font-bold text-blue-600">{data.correlation_stats.improvement_factor}×</p>
              <p className="text-xs text-gray-400 mt-1">more diversifiable than long-only</p>
            </div>
            <div className="bg-white rounded-lg border p-5 text-center">
              <p className="text-xs text-gray-500 mb-1">Best Portfolio Sharpe</p>
              <p className="text-3xl font-bold text-gray-900">{ms.sharpe?.toFixed(2)}</p>
              <p className="text-xs text-gray-400 mt-1">
                vs {Math.max(...Object.values(data.individual_strategies).map(s => s.sharpe ?? -99)).toFixed(2)} best individual
              </p>
            </div>
          </div>

          {/* Portfolio construction methods */}
          <div className="bg-white rounded-lg border overflow-hidden">
            <div className="p-5 border-b">
              <h2 className="font-semibold text-gray-900">Portfolio Construction Methods</h2>
              <p className="text-xs text-gray-500 mt-0.5">All use only the 7 positive-Sharpe L/S strategies</p>
            </div>
            <div className="flex border-b">
              {([ ['max_sharpe_pos', 'Max-Sharpe MVO'], ['equal_weight_pos', 'Equal-Weight'], ['risk_parity_pos', 'Risk-Parity'] ] as const).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setActivePortfolio(key)}
                  className={cn(
                    'flex-1 py-3 text-sm font-medium transition-colors',
                    activePortfolio === key
                      ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-600'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  )}
                >{label}</button>
              ))}
            </div>
            <div className="p-5">
              <div className="grid grid-cols-4 gap-3 mb-5">
                <MetricTile label="Sharpe" value={fmt(port.sharpe)} positive={(port.sharpe ?? 0) > 0} />
                <MetricTile label="CAGR" value={fmt(port.cagr, true, 1)} positive={(port.cagr ?? 0) > 0} />
                <MetricTile label="Max DD" value={fmt(port.max_drawdown, true, 1)} positive={false} isDD />
                <MetricTile label="Win Rate" value={fmt(port.win_rate, true, 0)} positive={(port.win_rate ?? 0) > 0.5} />
              </div>
              <div className="mb-5">
                <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Weights</p>
                <div className="space-y-1.5">
                  {Object.entries(port.weights)
                    .sort((a, b) => b[1] - a[1])
                    .map(([name, w]) => (
                      <div key={name} className="flex items-center gap-3">
                        <span className="text-xs text-gray-600 w-44 shrink-0">{STRATEGY_DISPLAY[name] ?? name}</span>
                        <div className="flex-1 bg-gray-100 rounded-full h-2">
                          <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${(w * 100).toFixed(0)}%` }} />
                        </div>
                        <span className="text-xs font-medium text-gray-700 w-12 text-right">{(w * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                </div>
              </div>
              {port.equity_curve?.length > 0 && (
                <>
                  <EquityCurveChart
                    data={port.equity_curve.map(p => ({ date: p.date, strategy: p.value * 1_000_000 }))}
                  />
                  <p className="text-xs text-gray-400 mt-2 text-center">
                    Normalized to $1M start · Monthly data · 2000–2024
                  </p>
                </>
              )}
            </div>
          </div>

          {/* Best pairs & triplets */}
          <div className="grid grid-cols-2 gap-5">
            {[{ title: 'Best 2-Strategy Pairs', rows: pairs }, { title: 'Best 3-Strategy Combinations', rows: trips }].map(({ title, rows }) => (
              <div key={title} className="bg-white rounded-lg border overflow-hidden">
                <div className="p-4 border-b">
                  <h2 className="font-semibold text-gray-900 text-sm">{title}</h2>
                  <p className="text-xs text-gray-500">Equal-weighted, by combined Sharpe</p>
                </div>
                <table className="w-full text-xs">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="text-left px-3 py-2 font-medium text-gray-500">Strategies</th>
                      <th className="text-right px-3 py-2 font-medium text-gray-500">SR</th>
                      <th className="text-right px-3 py-2 font-medium text-gray-500">Corr</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {rows.map((r, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="px-3 py-2 text-gray-700">
                          {r.strategies.map(n => STRATEGY_DISPLAY[n] ?? n).join(' + ')}
                        </td>
                        <td className="px-3 py-2 text-right font-semibold text-emerald-600">{r.sharpe.toFixed(2)}</td>
                        <td className="px-3 py-2 text-right text-gray-500">{r.avg_correlation.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </div>

          {/* Regime performance */}
          <div className="bg-white rounded-lg border overflow-hidden">
            <div className="p-5 border-b">
              <h2 className="font-semibold text-gray-900">Regime Performance — Max-Sharpe Portfolio</h2>
              <p className="text-xs text-gray-500 mt-0.5">How does the combined portfolio behave across market environments?</p>
            </div>
            <div className="p-5 grid grid-cols-2 gap-5">
              <div className="space-y-3">
                {([['bull', 'Bull markets', true], ['bear', 'Bear markets', false]] as const).map(([key, label, positive]) => {
                  const m = regimes[key]
                  return (
                    <div key={key} className={cn('rounded-lg p-4 border', positive ? 'bg-emerald-50 border-emerald-100' : 'bg-red-50 border-red-100')}>
                      <p className={cn('font-medium text-sm mb-2', positive ? 'text-emerald-800' : 'text-red-800')}>{label}</p>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div><p className="text-gray-500">Sharpe</p><p className="font-semibold">{fmt(m?.sharpe)}</p></div>
                        <div><p className="text-gray-500">CAGR</p><p className="font-semibold">{fmt(m?.cagr, true, 1)}</p></div>
                        <div><p className="text-gray-500">Max DD</p><p className="font-semibold text-red-600">{fmt(m?.max_drawdown, true, 1)}</p></div>
                      </div>
                      <p className="text-xs text-gray-400 mt-1">{m?.n_months} months</p>
                    </div>
                  )
                })}
              </div>
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Specific Crises</p>
                <table className="w-full text-xs">
                  <thead className="bg-gray-50 rounded">
                    <tr>
                      <th className="text-left px-2 py-1.5 font-medium text-gray-500">Period</th>
                      <th className="text-right px-2 py-1.5 font-medium text-gray-500">SR</th>
                      <th className="text-right px-2 py-1.5 font-medium text-gray-500">CAGR</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {Object.entries(regimes.crises || {}).map(([key, m]) => (
                      <tr key={key}>
                        <td className="px-2 py-2 text-gray-700">{crisisLabels[key] ?? key}</td>
                        <td className={cn('px-2 py-2 text-right font-semibold', (m.sharpe ?? 0) >= 0 ? 'text-emerald-600' : 'text-red-600')}>
                          {fmt(m.sharpe)}
                        </td>
                        <td className={cn('px-2 py-2 text-right', (m.cagr ?? 0) >= 0 ? 'text-gray-700' : 'text-red-600')}>
                          {fmt(m.cagr, true, 1)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="text-xs text-gray-400 mt-2 leading-relaxed">
                  SR 1.15 in dot-com bust = momentum/quality correctly shorts overvalued tech.
                  GFC hurt badly — credit crisis overwhelmed all factor signals.
                </p>
              </div>
            </div>
          </div>

          {/* Rolling 3yr Sharpe */}
          {data.rolling_sharpe_36m.length > 0 && (
            <div className="bg-white rounded-lg border overflow-hidden">
              <div className="p-5 border-b">
                <h2 className="font-semibold text-gray-900">Rolling 3-Year Sharpe — Max-Sharpe Portfolio</h2>
                <p className="text-xs text-gray-500 mt-0.5">Is the factor premium persistent over time?</p>
              </div>
              <div className="p-5">
                <EquityCurveChart
                  data={data.rolling_sharpe_36m
                    .filter(p => p.sharpe != null)
                    .map(p => ({ date: p.date, strategy: (p.sharpe ?? 0) + 2 }))}
                />
                <p className="text-xs text-gray-400 mt-2 text-center">
                  Values offset by +2 for chart scaling. A value of 2.0 on the chart = Sharpe 0.0.
                </p>
              </div>
            </div>
          )}

          {/* Individual strategy breakdown */}
          <div className="bg-white rounded-lg border overflow-hidden">
            <div className="p-5 border-b">
              <h2 className="font-semibold text-gray-900">Individual L/S Strategy Contributions</h2>
              <p className="text-xs text-gray-500 mt-0.5">Ranked by L/S Sharpe. Positive = factor premium confirmed.</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-y">
                  <tr>
                    <th className="text-left px-4 py-2.5 font-medium text-gray-600">#</th>
                    <th className="text-left px-4 py-2.5 font-medium text-gray-600">Strategy</th>
                    <th className="text-right px-4 py-2.5 font-medium text-gray-600">L/S Sharpe</th>
                    <th className="text-right px-4 py-2.5 font-medium text-gray-600">CAGR</th>
                    <th className="text-right px-4 py-2.5 font-medium text-gray-600">Max DD</th>
                    <th className="text-right px-4 py-2.5 font-medium text-gray-600">In Portfolio</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {Object.entries(data.individual_strategies)
                    .sort((a, b) => (b[1].sharpe ?? -99) - (a[1].sharpe ?? -99))
                    .map(([name, s], i) => {
                      const inPortfolio = name in ms.weights && ms.weights[name] > 0.01
                      return (
                        <tr key={name} className="hover:bg-gray-50">
                          <td className="px-4 py-2.5 text-gray-400">{i + 1}</td>
                          <td className="px-4 py-2.5">
                            <Link href={`/strategy/${name.replace(/_/g, '-')}`} className="font-medium text-gray-900 hover:text-blue-600">
                              {STRATEGY_DISPLAY[name] ?? name}
                            </Link>
                          </td>
                          <td className="px-4 py-2.5 text-right font-semibold">
                            <span className={(s.sharpe ?? 0) > 0.4 ? 'text-emerald-600' : (s.sharpe ?? 0) > 0 ? 'text-yellow-600' : 'text-red-600'}>
                              {fmt(s.sharpe)}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 text-right text-gray-600">{fmt(s.cagr, true, 1)}</td>
                          <td className="px-4 py-2.5 text-right text-red-600">{fmt(s.max_drawdown, true, 1)}</td>
                          <td className="px-4 py-2.5 text-right">
                            {inPortfolio
                              ? <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium">{(ms.weights[name] * 100).toFixed(0)}%</span>
                              : <span className="text-gray-300 text-xs">—</span>}
                          </td>
                        </tr>
                      )
                    })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
