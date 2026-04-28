'use client'

export const dynamic = 'force-dynamic'

import { useState, useEffect, Fragment } from 'react'
import Link from 'next/link'
import { ArrowLeft, Loader2, AlertCircle, CheckCircle2, AlertTriangle, Shield, TrendingUp, Info } from 'lucide-react'
import { fetchMorningTradeList, type MorningTradeList, type TradeListEntry } from '@/lib/api'
import { cn } from '@/lib/utils'

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

const SECTOR_COLORS: Record<string, string> = {
  'Technology':        'bg-blue-500',
  'Financial Services': 'bg-emerald-500',
  'Healthcare':        'bg-red-400',
  'Utilities':         'bg-yellow-500',
  'Industrials':       'bg-orange-400',
  'Consumer Defensive': 'bg-teal-500',
  'Basic Materials':   'bg-stone-500',
  'Energy':            'bg-amber-600',
  'Real Estate':       'bg-purple-400',
  'Consumer Cyclical': 'bg-pink-400',
  'Communication Services': 'bg-indigo-400',
}

function SafeBadge({ label, safe }: { label: string; safe: boolean }) {
  return (
    <div className={cn('flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium',
      safe ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-red-50 text-red-700 border border-red-200'
    )}>
      {safe
        ? <CheckCircle2 className="w-4 h-4" />
        : <AlertTriangle className="w-4 h-4" />}
      {label}
    </div>
  )
}

function StrategyTag({ name }: { name: string }) {
  const short = STRATEGY_SHORT[name] ?? name.slice(0, 3).toUpperCase()
  return (
    <span className="inline-block px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded text-xs font-medium mr-1 mb-0.5">
      {short}
    </span>
  )
}

function AllocationBar({ pct, max }: { pct: number; max: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 bg-gray-100 rounded-full h-1.5">
        <div
          className="bg-blue-500 h-1.5 rounded-full"
          style={{ width: `${Math.min((pct / max) * 100, 100)}%` }}
        />
      </div>
      <span className="text-xs font-medium text-gray-700 tabular-nums w-8">{pct.toFixed(1)}%</span>
    </div>
  )
}

export default function SignalsPage() {
  const [data, setData] = useState<MorningTradeList | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedRow, setExpandedRow] = useState<number | null>(null)

  useEffect(() => {
    fetchMorningTradeList()
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-[calc(100vh-56px)]">
      <Loader2 className="w-6 h-6 animate-spin text-blue-600 mr-3" />
      <span className="text-gray-500">Loading signals…</span>
    </div>
  )

  if (error || !data) return (
    <div className="flex items-center justify-center h-[calc(100vh-56px)]">
      <div className="text-center max-w-md">
        <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-3" />
        <p className="text-gray-700 font-medium mb-1">Failed to load signals</p>
        <p className="text-gray-400 text-sm">{error}</p>
      </div>
    </div>
  )

  const { risk_metrics: rm, sector_breakdown, trade_list } = data
  const maxAlloc = Math.max(...trade_list.map(t => t.allocation_pct))
  const maxSector = Math.max(...Object.values(sector_breakdown))
  const signalDate = new Date(data.signal_date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
      {/* Header */}
      <div>
        <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-4">
          <ArrowLeft className="w-4 h-4" /> Dashboard
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Morning Trade List</h1>
            <p className="text-gray-500 mt-1 text-sm">
              Consensus-ranked positions · {signalDate}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-400">Account size</p>
            <p className="text-2xl font-bold text-gray-900">${data.account_size.toLocaleString()}</p>
          </div>
        </div>
      </div>

      {/* Prop firm safety badges */}
      <div>
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Prop firm compatibility</p>
        <div className="flex gap-3 flex-wrap">
          <SafeBadge label="FTMO Safe" safe={rm.ftmo_safe} />
          <SafeBadge label="Apex Safe" safe={rm.apex_safe} />
          <SafeBadge label="TopStep Safe" safe={rm.topstep_safe} />
        </div>
      </div>

      {/* Risk summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Positions', value: rm.n_positions.toString(), sub: 'consensus holdings' },
          { label: 'Allocated', value: `${rm.total_allocated_pct.toFixed(1)}%`, sub: `${rm.cash_buffer_pct.toFixed(1)}% cash buffer` },
          { label: 'Max Position', value: `${rm.max_single_pos_pct.toFixed(1)}%`, sub: 'single name limit' },
          { label: 'Est. Max Daily Loss', value: `${rm.est_max_daily_loss.toFixed(1)}%`, sub: 'worst-case 2σ move' },
        ].map(item => (
          <div key={item.label} className="bg-white rounded-lg border p-4">
            <p className="text-xs text-gray-500 mb-1">{item.label}</p>
            <p className="text-2xl font-bold text-gray-900">{item.value}</p>
            <p className="text-xs text-gray-400 mt-0.5">{item.sub}</p>
          </div>
        ))}
      </div>

      {/* Earnings warnings */}
      {data.earnings_warning.length > 0 && (
        <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
          <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
          <p className="text-sm text-amber-800">
            <strong>Earnings this week:</strong> {data.earnings_warning.join(', ')} — consider reducing or avoiding these positions.
          </p>
        </div>
      )}

      <div className="grid grid-cols-3 gap-5">
        {/* Sector breakdown */}
        <div className="bg-white rounded-lg border p-5 col-span-1">
          <h2 className="font-semibold text-gray-900 text-sm mb-3">Sector Exposure</h2>
          <div className="space-y-2">
            {Object.entries(sector_breakdown)
              .sort((a, b) => b[1] - a[1])
              .map(([sector, pct]) => (
                <div key={sector}>
                  <div className="flex items-center justify-between text-xs mb-0.5">
                    <span className="text-gray-600 truncate">{sector}</span>
                    <span className="font-medium text-gray-800 ml-2">{pct.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-1.5">
                    <div
                      className={cn('h-1.5 rounded-full', SECTOR_COLORS[sector] ?? 'bg-gray-400')}
                      style={{ width: `${(pct / maxSector) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Methodology note */}
        <div className="col-span-2 bg-blue-50 border border-blue-200 rounded-lg p-5">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-600 mt-0.5 shrink-0" />
            <div>
              <p className="font-semibold text-blue-900 mb-2">How consensus signals work</p>
              <div className="space-y-1.5 text-sm text-blue-800">
                <p>Each of the 14 factor strategies runs independently on the current S&P 500 universe (501 stocks, Yahoo Finance data).</p>
                <p><strong>Consensus score</strong> = sum of position weights across all strategies that hold the stock. A stock scoring in 9 strategies with avg weight 3.3% gets a consensus score of ~29.7.</p>
                <p><strong>Position sizing</strong> is proportional to consensus score, capped at {rm.max_single_pos_pct}% per name, with a {rm.cash_buffer_pct.toFixed(1)}% cash reserve.</p>
                <p className="text-blue-700">Signal date: {signalDate}. Regenerate with <code className="bg-blue-100 px-1 rounded text-xs">scripts/generate_morning_signals.py</code></p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Trade list */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <div className="p-5 border-b flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-gray-900">Trade List — {trade_list.length} Positions</h2>
            <p className="text-xs text-gray-500 mt-0.5">Click any row to see which strategies are holding it</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <TrendingUp className="w-4 h-4" />
            Total deployed: <strong className="text-gray-800">${trade_list.reduce((s, t) => s + t.allocation_dollar, 0).toLocaleString()}</strong>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-2.5 font-medium text-gray-600 w-8">#</th>
                <th className="text-left px-4 py-2.5 font-medium text-gray-600">Symbol</th>
                <th className="text-left px-4 py-2.5 font-medium text-gray-600">Sector</th>
                <th className="text-right px-4 py-2.5 font-medium text-gray-600">Score</th>
                <th className="text-right px-4 py-2.5 font-medium text-gray-600">Strategies</th>
                <th className="text-right px-4 py-2.5 font-medium text-gray-600">Allocation</th>
                <th className="text-right px-4 py-2.5 font-medium text-gray-600">$ Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {trade_list.map((t: TradeListEntry) => (
                <Fragment key={t.rank}>
                  <tr
                    className={cn('cursor-pointer transition-colors', expandedRow === t.rank ? 'bg-blue-50' : 'hover:bg-gray-50')}
                    onClick={() => setExpandedRow(expandedRow === t.rank ? null : t.rank)}
                  >
                    <td className="px-4 py-3 text-gray-400 text-xs">{t.rank}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-gray-900">{t.symbol}</span>
                        {t.earnings_warning && (
                          <span className="px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded text-xs font-medium">earnings</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5">
                        <span className={cn('w-2 h-2 rounded-full', SECTOR_COLORS[t.sector] ?? 'bg-gray-400')} />
                        <span className="text-gray-600 text-xs">{t.sector}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right font-semibold text-blue-700 tabular-nums">{t.consensus_score.toFixed(1)}</td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-gray-700 font-medium">{t.n_strategies}</span>
                      <span className="text-gray-400">/14</span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <AllocationBar pct={t.allocation_pct} max={maxAlloc} />
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-gray-900 tabular-nums">${t.allocation_dollar}</td>
                  </tr>
                  {expandedRow === t.rank && (
                    <tr className="bg-blue-50">
                      <td colSpan={7} className="px-4 pb-3 pt-1">
                        <p className="text-xs text-gray-500 mb-1.5">Strategies holding {t.symbol}:</p>
                        <div className="flex flex-wrap gap-1">
                          {t.strategies.split(', ').map(s => (
                            <StrategyTag key={s} name={s} />
                          ))}
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
        <div className="px-4 py-3 bg-gray-50 border-t flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5" />
            Position caps enforced · Cash buffer maintained · Earnings flags applied
          </div>
          <span>Signal date: {signalDate}</span>
        </div>
      </div>
    </div>
  )
}
