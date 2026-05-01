'use client'

export const dynamic = 'force-dynamic'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import {
  ArrowLeft, Loader2, AlertCircle, TrendingUp, ArrowUpDown,
  Globe, BarChart3, Info, Radio, ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  fetchNSESignals,
  type NSESignalsData, type NSEConsensusEntry,
} from '@/lib/api'

// ── Constants ─────────────────────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1'

const STRATEGY_SHORT: Record<string, string> = {
  large_cap_momentum: 'LCM', '52_week_high_breakout': '52W',
  deep_value_all_cap: 'DV', high_quality_roic: 'HQ',
  low_volatility_shield: 'LV', dividend_aristocrats: 'DIV',
  moving_average_trend: 'MAT', rsi_mean_reversion: 'RSI',
  value_momentum_blend: 'V+M', quality_momentum: 'Q+M',
  quality_low_vol: 'QLV', composite_factor_score: 'CFS',
  volatility_targeting: 'VT', earnings_surprise_momentum: 'ES',
}

const DISPLAY: Record<string, string> = {
  large_cap_momentum: 'Large Cap Momentum', '52_week_high_breakout': '52-Week High Breakout',
  deep_value_all_cap: 'Deep Value All-Cap', high_quality_roic: 'High Quality ROIC',
  low_volatility_shield: 'Low Volatility Shield', dividend_aristocrats: 'Dividend Aristocrats',
  moving_average_trend: 'MA Trend', rsi_mean_reversion: 'RSI Mean Reversion',
  value_momentum_blend: 'Value+Momentum', quality_momentum: 'Quality+Momentum',
  quality_low_vol: 'Quality+Low Vol', composite_factor_score: 'Composite Factor',
  volatility_targeting: 'Volatility Targeting', earnings_surprise_momentum: 'Earnings Surprise',
}

// ── Backtest types ─────────────────────────────────────────────────────────────

interface NSEStrategyBacktest {
  name: string; display_name: string; status: string
  nse_sharpe: number | null; us_sharpe: number | null; delta_sharpe: number | null
  nse_cagr: number | null; nse_max_dd: number | null
  nse_volatility: number | null; nse_win_rate: number | null; nse_total_return: number | null
}
interface NSEBacktestData {
  market: string; n_symbols: number; date_range: string[]; generated_at: string
  summary: { avg_nse_sharpe: number; avg_us_sharpe: number; avg_delta: number; n_beat_us: number; n_strategies: number }
  strategies: NSEStrategyBacktest[]
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
        <div className={cn('h-1.5 rounded-full', delta >= 0 ? 'bg-emerald-500' : 'bg-red-400')} style={{ width: `${pct}%` }} />
      </div>
      <span className={cn('text-xs font-semibold tabular-nums w-12', delta >= 0 ? 'text-emerald-700' : 'text-red-600')}>
        {fmt(delta, false, 3, true)}
      </span>
    </div>
  )
}

// ── Backtest tab ───────────────────────────────────────────────────────────────

function BacktestTab() {
  const [data, setData] = useState<NSEBacktestData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sortKey, setSortKey] = useState<SortKey>('nse_sharpe')
  const [sortAsc, setSortAsc] = useState(false)

  useEffect(() => {
    fetch(`${API_BASE}/research/nse`)
      .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json() })
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex items-center gap-2 py-12 justify-center"><Loader2 className="w-5 h-5 animate-spin text-blue-600" /><span className="text-gray-500">Loading NSE results…</span></div>
  if (error || !data) return <div className="text-center py-12 text-red-500">{error ?? 'Failed to load'}</div>

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortAsc(p => !p)
    else { setSortKey(key); setSortAsc(false) }
  }
  const sorted = [...data.strategies].sort((a, b) => {
    const av = (a[sortKey] as number | null) ?? -999
    const bv = (b[sortKey] as number | null) ?? -999
    return sortAsc ? av - bv : bv - av
  })
  const maxDelta = Math.max(...data.strategies.map(s => Math.abs(s.delta_sharpe ?? 0)))
  const s = data.summary
  const dateStart = data.date_range?.[0]?.slice(0, 4) ?? '2005'
  const dateEnd   = data.date_range?.[1]?.slice(0, 4) ?? '2026'

  return (
    <div className="space-y-6">
      {/* KPI tiles */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Avg NSE Sharpe', value: s.avg_nse_sharpe.toFixed(2), sub: `vs ${s.avg_us_sharpe.toFixed(2)} on S&P 500`, pos: true },
          { label: 'Avg Edge over US', value: `+${s.avg_delta.toFixed(2)}`, sub: 'higher Sharpe on NSE', pos: true },
          { label: 'Beat US', value: `${s.n_beat_us} / ${s.n_strategies}`, sub: 'strategies outperform', pos: true },
          { label: 'Universe', value: `${data.n_symbols}`, sub: `NSE 500 · ${dateStart}–${dateEnd}`, pos: null },
        ].map(t => (
          <div key={t.label} className="bg-white rounded-lg border p-4">
            <p className="text-xs text-gray-500 mb-1">{t.label}</p>
            <p className={cn('text-2xl font-bold', t.pos === true ? 'text-emerald-700' : 'text-gray-900')}>{t.value}</p>
            <p className="text-xs text-gray-400 mt-0.5">{t.sub}</p>
          </div>
        ))}
      </div>

      {/* Insight */}
      <div className="bg-orange-50 border border-orange-200 rounded-xl p-5">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-orange-600 mt-0.5 shrink-0" />
          <div className="space-y-1.5 text-sm text-orange-800">
            <p className="font-semibold text-orange-900">Why NSE strategies outperform S&P 500 by ~0.43 Sharpe</p>
            <p><strong>Less efficient market:</strong> Indian mid/small-caps are under-researched. Factor signals take longer to arbitrage away.</p>
            <p><strong>Higher structural vol:</strong> NSE 18–22% vs S&P 500 15–17% ann. vol. Factor strategies capture the upside asymmetry in high-vol environments.</p>
            <p><strong>Exception — Earnings Surprise:</strong> Failed on NSE (Sharpe = 0). No IBES/Compustat earnings revision data for NSE.</p>
            <p className="text-xs text-orange-700">No survivorship bias correction · No transaction costs in NSE · Point-in-time universe not used</p>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <div className="px-5 py-4 border-b flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">NSE vs S&P 500 — All 14 Strategies</h2>
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
                  { key: 'delta_sharpe' as SortKey, label: 'Δ vs US' },
                  { key: 'nse_cagr' as SortKey, label: 'NSE CAGR' },
                  { key: 'nse_max_dd' as SortKey, label: 'Max DD' },
                ] as const).map(col => (
                  <th key={col.key} className="px-4 py-2.5 text-right font-medium text-gray-600 cursor-pointer hover:text-gray-900 whitespace-nowrap" onClick={() => toggleSort(col.key)}>
                    <span className="inline-flex items-center gap-1 justify-end">
                      {col.label}
                      <ArrowUpDown className={cn('w-3 h-3', sortKey === col.key ? 'text-blue-600' : 'text-gray-300')} />
                    </span>
                  </th>
                ))}
                <th className="text-right px-4 py-2.5 font-medium text-gray-600">US SR</th>
                <th className="px-4 py-2.5 font-medium text-gray-600">Delta bar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {sorted.map((s, i) => {
                const skip = s.status !== 'success' || (s.nse_sharpe ?? 0) === 0
                return (
                  <tr key={s.name} className={cn('hover:bg-gray-50/50', i % 2 === 0 ? 'bg-white' : 'bg-gray-50/30', skip ? 'opacity-50' : '')}>
                    <td className="px-4 py-3 font-medium text-gray-900 whitespace-nowrap">
                      {s.display_name}{skip && <span className="ml-2 text-xs text-gray-400">(no data)</span>}
                    </td>
                    <td className={cn('px-4 py-3 text-right font-bold tabular-nums text-xl', (s.nse_sharpe ?? 0) >= 1.0 ? 'text-emerald-600' : (s.nse_sharpe ?? 0) >= 0.7 ? 'text-yellow-600' : 'text-gray-500')}>
                      {fmt(s.nse_sharpe)}
                    </td>
                    <td className={cn('px-4 py-3 text-right font-semibold tabular-nums', (s.delta_sharpe ?? 0) > 0 ? 'text-emerald-600' : 'text-red-500')}>
                      {fmt(s.delta_sharpe, false, 3, true)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-600 tabular-nums">{fmt(s.nse_cagr, true, 1)}</td>
                    <td className="px-4 py-3 text-right text-red-500 tabular-nums">{fmt(s.nse_max_dd, true, 1)}</td>
                    <td className="px-4 py-3 text-right text-gray-400 tabular-nums text-xs">{fmt(s.us_sharpe)}</td>
                    <td className="px-4 py-3"><DeltaBar delta={s.delta_sharpe ?? 0} max={maxDelta} /></td>
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

      <div className="bg-gray-50 border rounded-xl p-5 text-sm text-gray-600 space-y-2">
        <p className="font-semibold text-gray-800">Data & Methodology</p>
        <p>NSE data from Yahoo Finance (<code className="bg-gray-200 px-1 rounded text-xs">.NS</code> suffix). Universe: NIFTY 500 current constituents — survivorship bias present. US results use point-in-time S&P 500 including delisted stocks. No transaction costs applied to NSE (add ~1–3%/yr for live trading).</p>
      </div>
    </div>
  )
}

// ── Live Signals tab ───────────────────────────────────────────────────────────

function AllocationBar({ pct, max }: { pct: number; max: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 bg-gray-100 rounded-full h-1.5">
        <div className="bg-orange-500 h-1.5 rounded-full" style={{ width: `${Math.min((pct / max) * 100, 100)}%` }} />
      </div>
      <span className="text-xs font-medium text-gray-700 tabular-nums w-8">{pct.toFixed(1)}%</span>
    </div>
  )
}

function LiveSignalsTab() {
  const [data, setData] = useState<NSESignalsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<string | null>(null)

  useEffect(() => {
    fetchNSESignals()
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex items-center gap-2 py-12 justify-center"><Loader2 className="w-5 h-5 animate-spin text-blue-600" /><span className="text-gray-500">Loading live NSE signals…</span></div>
  if (error || !data) return <div className="text-center py-12"><AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" /><p className="text-red-500 text-sm">{error ?? 'Failed to load'}</p></div>

  const consensus = data.consensus_trade_list
  const maxAlloc = Math.max(...consensus.map(t => t.allocation_pct))
  const signalDate = new Date(data.signal_date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })

  // Per-strategy table: sort strategies by n_holdings desc
  const stratEntries = Object.entries(data.strategies)
    .filter(([, v]) => !v.error && v.holdings && v.holdings.length > 0)
    .sort((a, b) => (b[1].n_holdings ?? 0) - (a[1].n_holdings ?? 0))

  return (
    <div className="space-y-6">
      {/* Header strip */}
      <div className="flex items-center gap-6 bg-orange-50 border border-orange-200 rounded-lg px-4 py-3">
        <div>
          <p className="text-xs text-gray-500 font-medium">Signal Date</p>
          <p className="font-bold text-gray-900">{signalDate}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 font-medium">Symbols</p>
          <p className="font-bold text-gray-900">{data.n_symbols}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 font-medium">Strategies</p>
          <p className="font-bold text-gray-900">{data.n_strategies_ok} / 14</p>
        </div>
        <div className="ml-auto text-xs text-gray-400">Market: NSE 500 · Yahoo Finance</div>
      </div>

      {/* Consensus trade list */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <div className="px-5 py-4 border-b">
          <h2 className="font-semibold text-gray-900">Consensus NSE Trade List — {consensus.length} positions</h2>
          <p className="text-xs text-gray-500 mt-0.5">Ranked by combined weight across {data.n_strategies_ok} strategies · click row for per-strategy breakdown</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-2.5 font-medium text-gray-600 w-8">#</th>
                <th className="text-left px-4 py-2.5 font-medium text-gray-600">Symbol</th>
                <th className="text-right px-4 py-2.5 font-medium text-gray-600">Score</th>
                <th className="text-right px-4 py-2.5 font-medium text-gray-600">Strategies</th>
                <th className="text-right px-4 py-2.5 font-medium text-gray-600 w-52">Allocation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {consensus.map((t: NSEConsensusEntry) => {
                const isExpanded = expanded === t.symbol
                // Collect which strategies hold this symbol
                const holdingStrats = Object.entries(data.strategies)
                  .filter(([, v]) => !v.error && v.holdings?.some(h => h.symbol === t.symbol))
                  .map(([k]) => k)

                return (
                  <>
                    <tr
                      key={t.symbol}
                      className={cn('cursor-pointer transition-colors', isExpanded ? 'bg-orange-50' : 'hover:bg-gray-50')}
                      onClick={() => setExpanded(isExpanded ? null : t.symbol)}
                    >
                      <td className="px-4 py-3 text-gray-400 text-xs">{t.rank}</td>
                      <td className="px-4 py-3 font-bold text-gray-900">{t.symbol}</td>
                      <td className="px-4 py-3 text-right font-semibold text-orange-700 tabular-nums">{t.consensus_score.toFixed(3)}</td>
                      <td className="px-4 py-3 text-right">
                        <span className="text-gray-700 font-medium">{t.n_strategies}</span>
                        <span className="text-gray-400">/{data.n_strategies_ok}</span>
                      </td>
                      <td className="px-4 py-3"><AllocationBar pct={t.allocation_pct} max={maxAlloc} /></td>
                    </tr>
                    {isExpanded && (
                      <tr key={`${t.symbol}-expanded`} className="bg-orange-50">
                        <td colSpan={5} className="px-4 pb-3 pt-1">
                          <p className="text-xs text-gray-500 mb-1.5">Held by:</p>
                          <div className="flex flex-wrap gap-1">
                            {holdingStrats.map(s => (
                              <span key={s} className="inline-block px-1.5 py-0.5 bg-orange-100 text-orange-800 rounded text-xs font-medium">
                                {STRATEGY_SHORT[s] ?? s.slice(0, 3).toUpperCase()}
                              </span>
                            ))}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                )
              })}
            </tbody>
          </table>
        </div>
        <div className="px-4 py-3 bg-gray-50 border-t text-xs text-gray-500">
          80% deployed · 20% cash buffer · weights proportional to consensus score
        </div>
      </div>

      {/* Per-strategy breakdown */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <div className="px-5 py-4 border-b">
          <h2 className="font-semibold text-gray-900">Per-Strategy Top Holdings</h2>
          <p className="text-xs text-gray-500 mt-0.5">Top 5 positions from each active strategy</p>
        </div>
        <div className="divide-y">
          {stratEntries.map(([name, result]) => (
            <div key={name} className="px-5 py-3">
              <div
                className="flex items-center gap-3 cursor-pointer hover:text-blue-600"
                onClick={() => setExpanded(expanded === `strat-${name}` ? null : `strat-${name}`)}
              >
                <span className="inline-block px-2 py-0.5 bg-orange-50 text-orange-700 rounded text-xs font-semibold w-12 text-center">{STRATEGY_SHORT[name] ?? name.slice(0, 3).toUpperCase()}</span>
                <span className="text-sm font-medium text-gray-900">{DISPLAY[name] ?? name}</span>
                <span className="text-xs text-gray-400 ml-1">{result.n_holdings} holdings</span>
                <ChevronRight className={cn('w-4 h-4 text-gray-400 ml-auto transition-transform', expanded === `strat-${name}` ? 'rotate-90' : '')} />
              </div>
              {expanded === `strat-${name}` && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {(result.holdings ?? []).slice(0, 10).map(h => (
                    <div key={h.symbol} className="flex items-center gap-1.5 bg-gray-50 rounded px-2 py-1 text-xs">
                      <span className="font-bold text-gray-900">{h.symbol}</span>
                      <span className="text-gray-400">{(h.weight * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                  {(result.holdings?.length ?? 0) > 10 && (
                    <span className="text-xs text-gray-400 self-center">+{(result.holdings?.length ?? 0) - 10} more</span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

type Tab = 'backtest' | 'signals'

export default function IndianMarketsPage() {
  const [tab, setTab] = useState<Tab>('backtest')

  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
      {/* Header */}
      <div>
        <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-4">
          <ArrowLeft className="w-4 h-4" /> Dashboard
        </Link>
        <div className="flex items-center gap-3">
          <Globe className="w-6 h-6 text-orange-500" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Indian Markets — NSE</h1>
            <p className="text-gray-500 text-sm">14 factor strategies on NSE 500 · backtests 2005–2026 + live signals today</p>
          </div>
        </div>
      </div>

      {/* Tab switcher */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-lg w-fit">
        {([
          { id: 'backtest' as Tab, label: 'Backtest Results', icon: BarChart3 },
          { id: 'signals'  as Tab, label: 'Live Signals',     icon: Radio    },
        ]).map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors',
              tab === id ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            )}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {tab === 'backtest' ? <BacktestTab /> : <LiveSignalsTab />}
    </div>
  )
}
