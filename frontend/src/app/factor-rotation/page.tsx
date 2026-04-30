'use client'

export const dynamic = 'force-dynamic'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import {
  ArrowLeft, Loader2, AlertCircle, TrendingUp, TrendingDown,
  Activity, Zap, Minus, Info, Trophy, ArrowDown,
} from 'lucide-react'
import { fetchFactorRotation, type FactorRotationData, type FactorRotationAnnualLeader } from '@/lib/api'
import { cn } from '@/lib/utils'

// ── Constants ─────────────────────────────────────────────────────────────────

const REGIMES = ['Bull', 'Bear', 'High-Vol', 'Sideways'] as const
type Regime = typeof REGIMES[number]

const REGIME_META: Record<Regime, { icon: React.ElementType; color: string; bg: string; border: string; text: string }> = {
  Bull:     { icon: TrendingUp,   color: 'text-emerald-600', bg: 'bg-emerald-50',  border: 'border-emerald-300', text: 'Trending Up' },
  Bear:     { icon: TrendingDown, color: 'text-red-600',     bg: 'bg-red-50',      border: 'border-red-300',     text: 'Trending Down' },
  'High-Vol': { icon: Activity,   color: 'text-orange-600',  bg: 'bg-orange-50',   border: 'border-orange-300',  text: 'Elevated Volatility' },
  Sideways: { icon: Minus,        color: 'text-gray-600',    bg: 'bg-gray-50',     border: 'border-gray-300',    text: 'No Clear Trend' },
}

// Sharpe → color for the heatmap cells
function sharpeColor(v: number | null | undefined): string {
  if (v == null) return 'bg-gray-100 text-gray-400'
  if (v >= 2.5) return 'bg-emerald-600 text-white'
  if (v >= 1.8) return 'bg-emerald-400 text-white'
  if (v >= 0.5) return 'bg-emerald-200 text-emerald-900'
  if (v >= 0)   return 'bg-yellow-100 text-yellow-800'
  if (v >= -1)  return 'bg-red-200 text-red-800'
  return 'bg-red-500 text-white'
}

const STRATEGY_SHORT: Record<string, string> = {
  large_cap_momentum:         'LCM',
  '52_week_high_breakout':    '52W',
  deep_value_all_cap:         'DV',
  high_quality_roic:          'HQ',
  low_volatility_shield:      'LV',
  dividend_aristocrats:       'DIV',
  moving_average_trend:       'MAT',
  rsi_mean_reversion:         'RSI',
  value_momentum_blend:       'V+M',
  quality_momentum:           'Q+M',
  quality_low_vol:            'QLV',
  composite_factor_score:     'CFS',
  volatility_targeting:       'VT',
  earnings_surprise_momentum: 'ES',
}

// ── Subcomponents ─────────────────────────────────────────────────────────────

function RegimeCard({
  regime, data, isCurrent, onClick, selected,
}: {
  regime: Regime
  data: FactorRotationData
  isCurrent: boolean
  selected: boolean
  onClick: () => void
}) {
  const meta = REGIME_META[regime]
  const Icon = meta.icon
  const stats = data.regime_stats[regime]
  const weights = data.all_regime_weights[regime] ?? {}
  const topStrategies = data.strategy_summaries
    .filter(s => s.regime_sharpes[regime] != null)
    .sort((a, b) => (b.regime_sharpes[regime] ?? 0) - (a.regime_sharpes[regime] ?? 0))
    .slice(0, 3)

  return (
    <button
      onClick={onClick}
      className={cn(
        'relative text-left rounded-xl border-2 p-4 transition-all',
        selected ? `${meta.bg} ${meta.border}` : 'bg-white border-gray-200 hover:border-gray-300',
        isCurrent && !selected && 'ring-2 ring-blue-400 ring-offset-1'
      )}
    >
      {isCurrent && (
        <span className="absolute top-2 right-2 px-1.5 py-0.5 bg-blue-600 text-white text-xs rounded font-medium">
          NOW
        </span>
      )}
      <div className={cn('flex items-center gap-2 mb-3', meta.color)}>
        <Icon className="w-5 h-5" />
        <span className="font-bold text-base">{regime}</span>
      </div>
      <p className="text-xs text-gray-500 mb-2">{meta.text}</p>
      {stats && (
        <div className="text-xs text-gray-600 space-y-0.5 mb-3">
          <div>{stats.pct_of_time.toFixed(0)}% of 2000–2024</div>
          <div className={stats.ann_market_return > 0 ? 'text-emerald-600' : 'text-red-500'}>
            SPY: {(stats.ann_market_return * 100).toFixed(0)}% ann. return
          </div>
        </div>
      )}
      <div className="space-y-1">
        {topStrategies.map((s, i) => (
          <div key={s.name} className="flex items-center justify-between text-xs">
            <span className="text-gray-600">{i + 1}. {s.display_name}</span>
            <span className={cn('font-semibold', meta.color)}>
              {(s.regime_sharpes[regime] ?? 0).toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    </button>
  )
}

function AllocationBar({ pct, max }: { pct: number; max: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 bg-gray-100 rounded-full h-1.5">
        <div
          className="bg-blue-500 h-1.5 rounded-full"
          style={{ width: `${Math.min((pct / max) * 100, 100)}%` }}
        />
      </div>
      <span className="text-xs font-medium text-gray-700 tabular-nums w-8">{pct.toFixed(1)}%</span>
    </div>
  )
}

function AnnualLeadershipTable({ leaders }: { leaders: FactorRotationAnnualLeader[] }) {
  const displayMap: Record<string, string> = {
    large_cap_momentum: 'LCM', '52_week_high_breakout': '52W', deep_value_all_cap: 'DV',
    high_quality_roic: 'HQ', low_volatility_shield: 'LV', dividend_aristocrats: 'DIV',
    moving_average_trend: 'MAT', rsi_mean_reversion: 'RSI', value_momentum_blend: 'V+M',
    quality_momentum: 'Q+M', quality_low_vol: 'QLV', composite_factor_score: 'CFS',
    volatility_targeting: 'VT', earnings_surprise_momentum: 'ES',
  }
  // Count wins per strategy
  const wins: Record<string, number> = {}
  leaders.forEach(l => { if (l.leader) wins[l.leader] = (wins[l.leader] ?? 0) + 1 })
  const topWinner = Object.entries(wins).sort((a, b) => b[1] - a[1])[0]

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-gray-900">Annual Factor Leadership (2000–2024)</h2>
        {topWinner && (
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <Trophy className="w-3.5 h-3.5 text-yellow-500" />
            Most wins: <strong className="text-gray-800">{displayMap[topWinner[0]] ?? topWinner[0]}</strong> ({topWinner[1]}×)
          </div>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-3 py-2 font-medium text-gray-600 w-12">Year</th>
              <th className="text-left px-3 py-2 font-medium text-gray-600">Leader</th>
              <th className="text-right px-3 py-2 font-medium text-gray-600 w-14">SR</th>
              <th className="text-left px-3 py-2 font-medium text-gray-600">2nd</th>
              <th className="text-right px-3 py-2 font-medium text-gray-600 w-14">SR</th>
              <th className="text-left px-3 py-2 font-medium text-gray-600">Laggard</th>
              <th className="text-right px-3 py-2 font-medium text-gray-600 w-14">SR</th>
              <th className="text-right px-3 py-2 font-medium text-gray-600 w-16">SPY SR</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {[...leaders].reverse().map((l) => {
              const isBad = (l.benchmark_sr ?? 0) < 0
              return (
                <tr key={l.year} className={cn('hover:bg-gray-50', isBad ? 'bg-red-50/30' : '')}>
                  <td className="px-3 py-2 font-semibold text-gray-700">{l.year}</td>
                  <td className="px-3 py-2">
                    {l.leader ? (
                      <span className="inline-flex items-center gap-1">
                        <Trophy className="w-3 h-3 text-yellow-500" />
                        <span className="font-medium text-gray-900">{displayMap[l.leader] ?? l.leader}</span>
                      </span>
                    ) : '—'}
                  </td>
                  <td className={cn('px-3 py-2 text-right font-semibold tabular-nums',
                    (l.leader_sr ?? 0) > 0 ? 'text-emerald-600' : 'text-red-500'
                  )}>
                    {l.leader_sr != null ? l.leader_sr.toFixed(2) : '—'}
                  </td>
                  <td className="px-3 py-2 text-gray-600">{l.second ? (displayMap[l.second] ?? l.second) : '—'}</td>
                  <td className={cn('px-3 py-2 text-right tabular-nums',
                    (l.second_sr ?? 0) > 0 ? 'text-emerald-600' : 'text-red-500'
                  )}>
                    {l.second_sr != null ? l.second_sr.toFixed(2) : '—'}
                  </td>
                  <td className="px-3 py-2">
                    {l.laggard ? (
                      <span className="flex items-center gap-1 text-red-500">
                        <ArrowDown className="w-3 h-3" />
                        {displayMap[l.laggard] ?? l.laggard}
                      </span>
                    ) : '—'}
                  </td>
                  <td className={cn('px-3 py-2 text-right tabular-nums',
                    (l.laggard_sr ?? 0) > 0 ? 'text-gray-500' : 'text-red-500'
                  )}>
                    {l.laggard_sr != null ? l.laggard_sr.toFixed(2) : '—'}
                  </td>
                  <td className={cn('px-3 py-2 text-right font-semibold tabular-nums',
                    (l.benchmark_sr ?? 0) > 0 ? 'text-blue-600' : 'text-red-500'
                  )}>
                    {l.benchmark_sr != null ? l.benchmark_sr.toFixed(2) : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function FactorRotationPage() {
  const [data, setData] = useState<FactorRotationData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedRegime, setSelectedRegime] = useState<Regime | null>(null)

  useEffect(() => {
    fetchFactorRotation()
      .then(d => {
        setData(d)
        if (d.current_regime && REGIMES.includes(d.current_regime as Regime)) {
          setSelectedRegime(d.current_regime as Regime)
        }
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-[calc(100vh-56px)]">
      <Loader2 className="w-6 h-6 animate-spin text-blue-600 mr-3" />
      <span className="text-gray-500">Detecting market regime…</span>
    </div>
  )

  if (error || !data) return (
    <div className="flex items-center justify-center h-[calc(100vh-56px)]">
      <div className="text-center max-w-md">
        <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-3" />
        <p className="text-gray-700 font-medium mb-1">Failed to load factor rotation</p>
        <p className="text-gray-400 text-sm">{error}</p>
      </div>
    </div>
  )

  const activeRegime = selectedRegime ?? (data.current_regime as Regime)
  const activeMeta   = REGIME_META[activeRegime] ?? REGIME_META['Sideways']
  const ActiveIcon   = activeMeta.icon
  const weights      = data.all_regime_weights[activeRegime] ?? data.recommended_weights
  const maxWeight    = Math.max(...Object.values(weights))

  // Sort strategies by weight for the active regime
  const sortedByWeight = [...data.strategy_summaries].sort(
    (a, b) => (weights[b.name] ?? 0) - (weights[a.name] ?? 0)
  )

  const rm = data.current_regime_metrics

  return (
    <div className="max-w-6xl mx-auto px-6 py-8 space-y-8">
      {/* Header */}
      <div>
        <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-4">
          <ArrowLeft className="w-4 h-4" /> Dashboard
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Factor Rotation Model</h1>
            <p className="text-gray-500 mt-1 text-sm">
              Which factors lead in each regime · 25-year historical analysis · Click a regime to explore
            </p>
          </div>
          {/* Current regime badge */}
          <div className={cn('flex items-center gap-2 px-4 py-2 rounded-xl border-2', activeMeta.bg, activeMeta.border)}>
            <Zap className="w-4 h-4 text-blue-600" />
            <div>
              <p className="text-xs text-gray-500 font-medium">Live Regime</p>
              <p className={cn('font-bold text-lg leading-tight', activeMeta.color)}>{data.current_regime}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Live metrics strip */}
      {rm && rm.as_of && (
        <div className="flex items-center gap-6 bg-gray-50 border rounded-lg px-4 py-3 text-sm">
          <div className="flex items-center gap-1.5">
            <span className="text-gray-500">SPY 63-day trend:</span>
            <span className={cn('font-semibold', (rm.trend_63d ?? 0) > 0 ? 'text-emerald-600' : 'text-red-500')}>
              {rm.trend_63d != null ? `${(rm.trend_63d * 100).toFixed(1)}%` : '—'}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-gray-500">63-day vol (ann.):</span>
            <span className={cn('font-semibold', (rm.vol_63d_ann ?? 0) >= 0.2 ? 'text-orange-600' : 'text-gray-700')}>
              {rm.vol_63d_ann != null ? `${(rm.vol_63d_ann * 100).toFixed(1)}%` : '—'}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-gray-500">SPY:</span>
            <span className="font-semibold text-gray-800">${rm.spy_price}</span>
          </div>
          <div className="ml-auto text-xs text-gray-400">As of {rm.as_of}</div>
        </div>
      )}

      {/* Regime cards */}
      <div>
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Select a regime to see recommended strategy weights</p>
        <div className="grid grid-cols-4 gap-4">
          {REGIMES.map(r => (
            <RegimeCard
              key={r}
              regime={r}
              data={data}
              isCurrent={r === data.current_regime}
              selected={r === activeRegime}
              onClick={() => setSelectedRegime(r)}
            />
          ))}
        </div>
      </div>

      {/* Active regime: insight + weights */}
      <div className="grid grid-cols-5 gap-6">
        {/* Insight */}
        <div className={cn('col-span-2 rounded-xl border p-5', activeMeta.bg, activeMeta.border)}>
          <div className="flex items-center gap-2 mb-3">
            <ActiveIcon className={cn('w-5 h-5', activeMeta.color)} />
            <span className={cn('font-bold', activeMeta.color)}>{activeRegime} Regime Playbook</span>
          </div>
          <p className="text-sm text-gray-700 leading-relaxed mb-4">
            {data.insights[activeRegime]}
          </p>
          {data.regime_stats[activeRegime] && (
            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-500">Frequency (2000–2024)</span>
                <span className="font-semibold">{data.regime_stats[activeRegime].pct_of_time.toFixed(0)}% of time</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Avg SPY annual return</span>
                <span className={cn('font-semibold', data.regime_stats[activeRegime].ann_market_return > 0 ? 'text-emerald-600' : 'text-red-500')}>
                  {(data.regime_stats[activeRegime].ann_market_return * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Avg SPY volatility</span>
                <span className="font-semibold">{(data.regime_stats[activeRegime].ann_market_vol * 100).toFixed(0)}%</span>
              </div>
              <div className="mt-3 pt-3 border-t border-gray-200">
                <p className="text-gray-500">{data.regime_descriptions[activeRegime]}</p>
              </div>
            </div>
          )}
        </div>

        {/* Recommended weights */}
        <div className="col-span-3 bg-white rounded-xl border p-5">
          <div className="flex items-center gap-2 mb-4">
            <h2 className="font-semibold text-gray-900">Recommended Strategy Weights</h2>
            <span className={cn('px-2 py-0.5 rounded text-xs font-medium', activeMeta.bg, activeMeta.color, activeMeta.border, 'border')}>
              {activeRegime}
            </span>
          </div>
          <div className="space-y-2">
            {sortedByWeight.map(s => (
              <div key={s.name} className="flex items-center gap-3">
                <span className="text-xs text-gray-500 w-6 font-mono">{STRATEGY_SHORT[s.name]}</span>
                <span className="text-xs text-gray-700 w-36 truncate">{s.display_name}</span>
                <AllocationBar pct={weights[s.name] ?? 0} max={maxWeight} />
                {s.wf_verdict && (
                  <span className={cn('text-xs px-1.5 py-0.5 rounded font-medium',
                    s.wf_verdict === 'STRONG' ? 'bg-emerald-100 text-emerald-800' :
                    s.wf_verdict === 'CONSISTENT' ? 'bg-blue-100 text-blue-800' :
                    s.wf_verdict === 'MIXED' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-500'
                  )}>{s.wf_verdict}</span>
                )}
              </div>
            ))}
          </div>
          <p className="mt-3 text-xs text-gray-400 flex items-center gap-1">
            <Info className="w-3 h-3" />
            Weights proportional to historical Sharpe in this regime (2000–2024). L/S walk-forward verdict shown for context.
          </p>
        </div>
      </div>

      {/* Heatmap */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <div className="px-5 py-4 border-b">
          <h2 className="font-semibold text-gray-900">Strategy × Regime Sharpe Heatmap</h2>
          <p className="text-xs text-gray-500 mt-0.5">Historical Sharpe ratio per strategy in each regime. All strategies fail in Bear markets.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-2.5 font-medium text-gray-600">Strategy</th>
                {REGIMES.map(r => (
                  <th key={r} className={cn('text-center px-4 py-2.5 font-medium',
                    r === activeRegime ? activeMeta.color : 'text-gray-600'
                  )}>
                    {r} {r === data.current_regime ? '★' : ''}
                  </th>
                ))}
                <th className="text-center px-4 py-2.5 font-medium text-gray-600">Best Regime</th>
                <th className="text-center px-4 py-2.5 font-medium text-gray-600">Rank in {activeRegime}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {data.strategy_summaries.map((s) => (
                <tr key={s.name} className="hover:bg-gray-50/50">
                  <td className="px-4 py-2.5 font-medium text-gray-900 whitespace-nowrap">{s.display_name}</td>
                  {REGIMES.map(r => {
                    const v = s.regime_sharpes[r]
                    return (
                      <td key={r} className={cn('px-4 py-2.5 text-center tabular-nums font-semibold rounded-sm',
                        sharpeColor(v),
                        r === activeRegime ? 'ring-1 ring-inset ring-blue-300' : ''
                      )}>
                        {v != null ? v.toFixed(2) : '—'}
                      </td>
                    )
                  })}
                  <td className="px-4 py-2.5 text-center">
                    <span className={cn('px-1.5 py-0.5 rounded text-xs font-medium',
                      REGIME_META[s.best_regime as Regime]?.bg ?? 'bg-gray-50',
                      REGIME_META[s.best_regime as Regime]?.color ?? 'text-gray-500',
                    )}>{s.best_regime}</span>
                  </td>
                  <td className="px-4 py-2.5 text-center">
                    <span className={cn('font-semibold text-sm',
                      (s.regime_ranks[activeRegime] ?? 99) <= 3 ? 'text-emerald-600' :
                      (s.regime_ranks[activeRegime] ?? 99) <= 7 ? 'text-gray-600' :
                      'text-gray-400'
                    )}>
                      #{s.regime_ranks[activeRegime] ?? '—'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="px-4 py-3 bg-gray-50 border-t flex items-center gap-6 text-xs text-gray-500 flex-wrap">
          <span>Color scale:</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-emerald-600 inline-block" /> ≥ 2.5</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-emerald-400 inline-block" /> ≥ 1.8</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-emerald-200 inline-block" /> ≥ 0.5</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-yellow-100 inline-block" /> ≥ 0</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-200 inline-block" /> ≥ −1</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-500 inline-block" /> &lt; −1</span>
          <span className="ml-auto">★ = current live regime</span>
        </div>
      </div>

      {/* Annual leadership table */}
      <div className="bg-white rounded-xl border overflow-hidden p-5">
        <AnnualLeadershipTable leaders={data.annual_leaders} />
      </div>

      {/* Key takeaway */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-600 mt-0.5 shrink-0" />
          <div>
            <p className="font-semibold text-blue-900 mb-2">Key Insight: Factor leadership rotates — no single winner</p>
            <div className="space-y-1.5 text-sm text-blue-800">
              <p>Over 25 years, leadership changed every 1–3 years. Dividend Aristocrats and Low Volatility Shield dominated <strong>defensive</strong> periods (2000–2002, 2007–2009, 2014–2016). RSI Mean Reversion and Earnings Surprise led <strong>recovery</strong> rallies (2003, 2009, 2013).</p>
              <p>All strategies share the same bear-market weakness (Sharpe −1.3 to −1.7 in Bear regime). The regime detector flags high-vol environments early, which is when defensive tilt (Low Vol, Dividend) historically cushioned drawdowns.</p>
              <p className="text-blue-700 text-xs">Regime detected using: SPY 63-day total return + 63-day annualised vol. Thresholds: Bull ≥ +5%, Bear ≤ −5%, High-Vol ≥ 20% ann. vol, Sideways otherwise.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
