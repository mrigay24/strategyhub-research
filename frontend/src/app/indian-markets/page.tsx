'use client'

export const dynamic = 'force-dynamic'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { ArrowLeft, Loader2, AlertCircle, TrendingUp, ArrowUpDown, Globe, BarChart3, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1'

const DISPLAY: Record<string, string> = {
  large_cap_momentum:         'Large Cap Momentum',
  '52_week_high_breakout':    '52-Week High Breakout',
  deep_value_all_cap:         'Deep Value All-Cap',
  high_quality_roic:          'High Quality ROIC',
  low_volatility_shield:      'Low Volatility Shield',
  dividend_aristocrats:       'Dividend Aristocrats',
  moving_average_trend:       'MA Trend',
  rsi_mean_reversion:         'RSI Mean Reversion',
  value_momentum_blend:       'Value+Momentum',
  quality_momentum:           'Quality+Momentum',
  quality_low_vol:            'Quality+Low Vol',
  composite_factor_score:     'Composite Factor',
  volatility_targeting:       'Volatility Targeting',
  earnings_surprise_momentum: 'Earnings Surprise',
}

interface NSEStrategy {
  name: string
  display_name: string
  status: string
  nse_sharpe: number | null
  us_sharpe: number | null
  delta_sharpe: number | null
  nse_cagr: number | null
  nse_max_dd: number | null
  nse_volatility: number | null
  nse_win_rate: number | null
  nse_total_return: number | null
}

interface NSEData {
  market: string
  n_symbols: number
  date_range: string[]
  generated_at: string
  summary: {
    avg_nse_sharpe: number
    avg_us_sharpe: number
    avg_delta: number
    n_beat_us: number
    n_strategies: number
  }
  strategies: NSEStrategy[]
}

type SortKey = 'nse_sharpe' | 'delta_sharpe' | 'nse_cagr' | 'nse_max_dd'

function fmt(v: number | null | undefined, pct = false, dec = 2, sign = false): string {
  if (v == null || isNaN(v)) return '—'
  const x = pct ? v * 100 : v
  const s = Math.abs(x).toFixed(dec)
  const prefix = x < 0 ? '-' : sign && x > 0 ? '+' : ''
  return `${prefix}${s}${pct ? '%' : ''}`
}

function DeltaBar({ delta, max }: { delta: number; max: number }) {
  const pct = Math.min(Math.abs(delta) / max * 100, 100)
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 bg-gray-100 rounded-full h-1.5">
        <div
          className={cn('h-1.5 rounded-full', delta >= 0 ? 'bg-emerald-500' : 'bg-red-400')}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={cn('text-xs font-semibold tabular-nums w-12', delta >= 0 ? 'text-emerald-700' : 'text-red-600')}>
        {fmt(delta, false, 3, true)}
      </span>
    </div>
  )
}

export default function IndianMarketsPage() {
  const [data, setData]       = useState<NSEData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)
  const [sortKey, setSortKey] = useState<SortKey>('nse_sharpe')
  const [sortAsc, setSortAsc] = useState(false)

  useEffect(() => {
    fetch(`${API_BASE}/research/nse`)
      .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json() })
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-[calc(100vh-56px)]">
      <Loader2 className="w-6 h-6 animate-spin text-blue-600 mr-3" />
      <span className="text-gray-500">Loading NSE results…</span>
    </div>
  )

  if (error || !data) return (
    <div className="flex items-center justify-center h-[calc(100vh-56px)]">
      <div className="text-center max-w-md">
        <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-3" />
        <p className="text-gray-700 font-medium mb-1">Failed to load NSE data</p>
        <p className="text-gray-400 text-sm">{error}</p>
      </div>
    </div>
  )

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortAsc(p => !p)
    else { setSortKey(key); setSortAsc(false) }
  }

  const sorted = [...data.strategies].sort((a, b) => {
    const av = (a[sortKey] as number | null) ?? -999
    const bv = (b[sortKey] as number | null) ?? -999
    return sortAsc ? av - bv : bv - av
  })

  const maxDelta  = Math.max(...data.strategies.map(s => Math.abs(s.delta_sharpe ?? 0)))
  const s         = data.summary
  const dateStart = data.date_range?.[0]?.slice(0, 4) ?? '2005'
  const dateEnd   = data.date_range?.[1]?.slice(0, 4) ?? '2026'

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
      {/* Header */}
      <div>
        <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-4">
          <ArrowLeft className="w-4 h-4" /> Dashboard
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Globe className="w-6 h-6 text-orange-500" />
              <h1 className="text-2xl font-bold text-gray-900">Indian Markets — NSE</h1>
            </div>
            <p className="text-gray-500 text-sm">
              All 14 factor strategies run on {data.n_symbols} NSE 500 stocks · {dateStart}–{dateEnd} · compared to S&P 500 25-year results
            </p>
          </div>
        </div>
      </div>

      {/* KPI tiles */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          {
            label: 'Avg NSE Sharpe',
            value: s.avg_nse_sharpe.toFixed(2),
            sub: `vs ${s.avg_us_sharpe.toFixed(2)} on S&P 500`,
            positive: true,
          },
          {
            label: 'Avg Alpha over US',
            value: `+${s.avg_delta.toFixed(2)}`,
            sub: 'higher Sharpe on NSE',
            positive: true,
          },
          {
            label: 'Strategies Beat US',
            value: `${s.n_beat_us} / ${s.n_strategies}`,
            sub: 'outperform S&P 500 SR',
            positive: true,
          },
          {
            label: 'Universe',
            value: `${data.n_symbols}`,
            sub: `NSE 500 stocks · ${dateStart}–${dateEnd}`,
            positive: null,
          },
        ].map(tile => (
          <div key={tile.label} className="bg-white rounded-lg border p-4">
            <p className="text-xs text-gray-500 mb-1">{tile.label}</p>
            <p className={cn('text-2xl font-bold',
              tile.positive === true ? 'text-emerald-700' :
              tile.positive === false ? 'text-red-600' : 'text-gray-900'
            )}>{tile.value}</p>
            <p className="text-xs text-gray-400 mt-0.5">{tile.sub}</p>
          </div>
        ))}
      </div>

      {/* Insight box */}
      <div className="bg-orange-50 border border-orange-200 rounded-xl p-5">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-orange-600 mt-0.5 shrink-0" />
          <div>
            <p className="font-semibold text-orange-900 mb-2">Why NSE strategies outperform S&P 500 by ~0.43 Sharpe</p>
            <div className="space-y-1.5 text-sm text-orange-800">
              <p><strong>Less efficient market:</strong> Indian mid/small-caps are under-researched. Factor signals (momentum, quality, value) take longer to be arbitraged away — giving systematic strategies more edge.</p>
              <p><strong>Higher structural volatility:</strong> NSE index volatility is 18–22% vs 15–17% for S&P 500. This amplifies both losses and gains, but well-structured factor strategies capture the upside asymmetry.</p>
              <p><strong>Exception — Earnings Surprise:</strong> Failed on NSE (Sharpe = 0). NSE does not have standardised earnings surprise data in the same format as IBES/Compustat used for US signals.</p>
              <p className="text-orange-700 text-xs">Backtest: {data.n_symbols} NSE stocks · {dateStart}–{dateEnd} · Yahoo Finance data · No survivorship-bias correction (NSE delistings). Transaction costs not included. US data: 653 S&P 500 stocks, 2000–2024, 15bps commission.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Comparison table */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <div className="px-5 py-4 border-b flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-gray-900">Strategy Results — NSE vs S&P 500</h2>
            <p className="text-xs text-gray-500 mt-0.5">Click column headers to sort · Delta = NSE Sharpe − US Sharpe</p>
          </div>
          <div className="flex items-center gap-3 text-xs text-gray-500">
            <span className="flex items-center gap-1"><BarChart3 className="w-3.5 h-3.5 text-orange-500" /> NSE</span>
            <span className="flex items-center gap-1"><TrendingUp className="w-3.5 h-3.5 text-blue-500" /> S&P 500</span>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-2.5 font-medium text-gray-600">Strategy</th>
                {([
                  { key: 'nse_sharpe' as SortKey, label: 'NSE Sharpe' },
                  { key: 'delta_sharpe' as SortKey, label: 'Delta vs US' },
                  { key: 'nse_cagr' as SortKey, label: 'NSE CAGR' },
                  { key: 'nse_max_dd' as SortKey, label: 'NSE Max DD' },
                ] as const).map(col => (
                  <th
                    key={col.key}
                    className="px-4 py-2.5 text-right font-medium text-gray-600 cursor-pointer hover:text-gray-900 whitespace-nowrap"
                    onClick={() => toggleSort(col.key)}
                  >
                    <span className="inline-flex items-center gap-1 justify-end">
                      {col.label}
                      <ArrowUpDown className={cn('w-3 h-3', sortKey === col.key ? 'text-blue-600' : 'text-gray-300')} />
                    </span>
                  </th>
                ))}
                <th className="text-right px-4 py-2.5 font-medium text-gray-600">US Sharpe</th>
                <th className="text-right px-4 py-2.5 font-medium text-gray-600 w-48">Delta bar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {sorted.map((s, i) => {
                const skip = s.status !== 'success' || (s.nse_sharpe ?? 0) === 0
                return (
                  <tr key={s.name} className={cn(
                    'hover:bg-gray-50/50',
                    i % 2 === 0 ? 'bg-white' : 'bg-gray-50/30',
                    skip ? 'opacity-50' : ''
                  )}>
                    <td className="px-4 py-3 font-medium text-gray-900 whitespace-nowrap">
                      {s.display_name}
                      {skip && <span className="ml-2 text-xs text-gray-400">(no data)</span>}
                    </td>
                    <td className={cn('px-4 py-3 text-right font-bold tabular-nums text-xl',
                      (s.nse_sharpe ?? 0) >= 1.0 ? 'text-emerald-600' :
                      (s.nse_sharpe ?? 0) >= 0.7 ? 'text-yellow-600' : 'text-gray-500'
                    )}>
                      {fmt(s.nse_sharpe)}
                    </td>
                    <td className={cn('px-4 py-3 text-right font-semibold tabular-nums',
                      (s.delta_sharpe ?? 0) > 0 ? 'text-emerald-600' : 'text-red-500'
                    )}>
                      {fmt(s.delta_sharpe, false, 3, true)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-600 tabular-nums">
                      {fmt(s.nse_cagr, true, 1)}
                    </td>
                    <td className="px-4 py-3 text-right text-red-500 tabular-nums">
                      {fmt(s.nse_max_dd, true, 1)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-400 tabular-nums text-xs">
                      {fmt(s.us_sharpe)}
                    </td>
                    <td className="px-4 py-3">
                      <DeltaBar delta={s.delta_sharpe ?? 0} max={maxDelta} />
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        <div className="px-4 py-3 bg-gray-50 border-t text-xs text-gray-500 flex items-center justify-between">
          <span>NSE: {data.n_symbols} symbols · {dateStart}–{dateEnd} · Yahoo Finance · S&P 500: 653 symbols · 2000–2024 · 15bps cost</span>
          <span className="text-gray-400">Generated {data.generated_at?.slice(0, 10)}</span>
        </div>
      </div>

      {/* Methodology note */}
      <div className="bg-gray-50 border rounded-xl p-5 text-sm text-gray-600 space-y-2">
        <p className="font-semibold text-gray-800">Data & Methodology</p>
        <p>NSE data downloaded from Yahoo Finance (symbols suffixed with <code className="bg-gray-200 px-1 rounded text-xs">.NS</code>). Universe: NIFTY 500 constituents as of download date — <strong>current constituents only</strong>, not point-in-time (survivorship bias present). US results use a point-in-time S&P 500 constituent list including delisted stocks.</p>
        <p>All 14 strategies run with identical parameters as the US backtest. Monthly rebalancing. Earnings Surprise strategy fails on NSE due to missing earnings-revision data from IBES/Bloomberg.</p>
        <p>No transaction costs applied to NSE results. Indian equity transaction costs (STT + brokerage) are typically 20–40bps round-trip, vs 15bps assumed for US results. Adjust NSE CAGR estimates downward by ~1–3% per year for live trading.</p>
      </div>
    </div>
  )
}
