'use client'

export const dynamic = 'force-dynamic'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { ArrowLeft, Loader2, AlertCircle, ArrowUpDown } from 'lucide-react'
import { fetchUnifiedScorecard, type ScorecardRow, type UnifiedScorecardData } from '@/lib/api'
import { cn } from '@/lib/utils'

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmt(v: number | null | undefined, pct = false, dec = 2, sign = false): string {
  if (v == null || isNaN(v)) return '—'
  const x = pct ? v * 100 : v
  const s = Math.abs(x).toFixed(dec)
  const prefix = x < 0 ? '-' : sign && x > 0 ? '+' : ''
  return `${prefix}${s}${pct ? '%' : ''}`
}

function TierBadge({ tier }: { tier: string }) {
  const t = tier.includes('Tier 1') ? 1 : tier.includes('Tier 2') ? 2 : 3
  const styles = ['', 'bg-emerald-100 text-emerald-800', 'bg-blue-100 text-blue-800', 'bg-gray-100 text-gray-600']
  return <span className={cn('px-1.5 py-0.5 rounded text-xs font-semibold', styles[t])}>T{t}</span>
}

function MCBadge({ verdict }: { verdict: string }) {
  if (verdict.includes('★★★')) return <span className="text-emerald-600 font-bold text-xs">★★★</span>
  if (verdict.includes('★★'))  return <span className="text-yellow-600 font-bold text-xs">★★</span>
  return <span className="text-gray-400 text-xs">—</span>
}

function WFBadge({ verdict }: { verdict: string | null }) {
  if (!verdict) return <span className="text-gray-300 text-xs">—</span>
  const styles: Record<string, string> = {
    STRONG:     'bg-emerald-100 text-emerald-800',
    CONSISTENT: 'bg-blue-100 text-blue-800',
    MIXED:      'bg-yellow-100 text-yellow-800',
    WEAK:       'bg-red-100 text-red-800',
  }
  return <span className={cn('px-1.5 py-0.5 rounded text-xs font-semibold', styles[verdict] ?? 'bg-gray-100 text-gray-600')}>{verdict}</span>
}

function SrCell({ v, threshold = 0.4 }: { v: number | null; threshold?: number }) {
  const color = v == null ? 'text-gray-300'
    : v >= threshold ? 'text-emerald-600'
    : v > 0 ? 'text-yellow-600'
    : 'text-red-500'
  return <span className={cn('font-semibold tabular-nums', color)}>{fmt(v)}</span>
}

type SortKey = 'lo_sharpe' | 'ls_sharpe' | 'lo_adj_sharpe' | 'capm_alpha' | 'lo_bear_sharpe' | 'lo_wfe'

const SORT_OPTIONS: { key: SortKey; label: string }[] = [
  { key: 'lo_sharpe',    label: 'L/O Sharpe' },
  { key: 'ls_sharpe',    label: 'L/S Sharpe' },
  { key: 'lo_adj_sharpe', label: 'Adj Sharpe' },
  { key: 'capm_alpha',   label: 'CAPM α' },
  { key: 'lo_bear_sharpe', label: 'Bear SR' },
  { key: 'lo_wfe',       label: 'WFE %' },
]

// ── Column groups for the header ──────────────────────────────────────────────

const COL_GROUPS = [
  { label: 'Long-Only (25yr)', cols: 5, color: 'bg-blue-50' },
  { label: 'Regime',           cols: 2, color: 'bg-amber-50' },
  { label: 'CAPM',             cols: 2, color: 'bg-purple-50' },
  { label: 'L/S Pure Factor',  cols: 3, color: 'bg-emerald-50' },
  { label: 'Validation',       cols: 2, color: 'bg-gray-50' },
]

export default function ScorecardPage() {
  const [data, setData] = useState<UnifiedScorecardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sortKey, setSortKey] = useState<SortKey>('lo_sharpe')
  const [sortAsc, setSortAsc] = useState(false)

  useEffect(() => {
    fetchUnifiedScorecard()
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-[calc(100vh-56px)]">
      <Loader2 className="w-6 h-6 animate-spin text-blue-600 mr-3" />
      <span className="text-gray-500">Loading scorecard…</span>
    </div>
  )

  if (error || !data) return (
    <div className="flex items-center justify-center h-[calc(100vh-56px)]">
      <div className="text-center max-w-md">
        <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-3" />
        <p className="text-gray-700 font-medium mb-1">Failed to load scorecard</p>
        <p className="text-gray-400 text-sm">{error}</p>
      </div>
    </div>
  )

  const rows = [...data.strategies].sort((a, b) => {
    const av = (a[sortKey] as number | null) ?? -999
    const bv = (b[sortKey] as number | null) ?? -999
    return sortAsc ? av - bv : bv - av
  })

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortAsc(p => !p)
    else { setSortKey(key); setSortAsc(false) }
  }

  function SortTh({ col, label, className }: { col: SortKey; label: string; className?: string }) {
    const active = sortKey === col
    return (
      <th
        className={cn('px-2 py-2 text-right cursor-pointer select-none whitespace-nowrap font-medium text-gray-500 hover:text-gray-800 transition-colors', className)}
        onClick={() => toggleSort(col)}
      >
        <span className="inline-flex items-center gap-1 justify-end">
          {label}
          <ArrowUpDown className={cn('w-3 h-3', active ? 'text-blue-600' : 'text-gray-300')} />
        </span>
      </th>
    )
  }

  return (
    <div className="max-w-[1400px] mx-auto px-6 py-8">
      {/* Header */}
      <div className="mb-6">
        <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-4">
          <ArrowLeft className="w-4 h-4" /> Dashboard
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Research Scorecard</h1>
            <p className="text-gray-500 mt-1 text-sm">
              All 14 strategies · 8 validation layers · 25-year backtest (2000–2024)
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Sort by:</span>
            {SORT_OPTIONS.map(opt => (
              <button
                key={opt.key}
                onClick={() => toggleSort(opt.key)}
                className={cn(
                  'px-2.5 py-1 rounded text-xs font-medium transition-colors',
                  sortKey === opt.key
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                )}
              >{opt.label}</button>
            ))}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mb-4 text-xs text-gray-500 flex-wrap">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-emerald-100 inline-block" /> Long-only validated</span>
        <span className="flex items-center gap-1"><span className="text-emerald-600 font-bold">★★★</span> MC significant</span>
        <span className="flex items-center gap-1"><span className="px-1 py-0.5 rounded bg-emerald-100 text-emerald-800 text-xs font-semibold">STRONG</span> L/S WF verdict</span>
        <span className="text-gray-400">Click column headers to sort</span>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            {/* Column group header */}
            <thead>
              <tr className="border-b">
                <th className="px-3 py-2 text-left" rowSpan={2}>
                  <span className="text-xs font-semibold text-gray-700">Strategy</span>
                </th>
                {COL_GROUPS.map(g => (
                  <th
                    key={g.label}
                    colSpan={g.cols}
                    className={cn('py-1.5 text-center text-xs font-semibold text-gray-600 border-l', g.color)}
                  >{g.label}</th>
                ))}
              </tr>
              <tr className="border-b bg-gray-50 text-xs">
                {/* Long-only */}
                <SortTh col="lo_sharpe"    label="Sharpe"   className="border-l" />
                <SortTh col="lo_adj_sharpe" label="Adj SR"  className="" />
                <th className="px-2 py-2 text-right text-gray-500 whitespace-nowrap">CAGR</th>
                <th className="px-2 py-2 text-right text-gray-500 whitespace-nowrap">Max DD</th>
                <th className="px-2 py-2 text-right text-gray-500 whitespace-nowrap">% Pos Yrs</th>
                {/* Regime */}
                <SortTh col="lo_bear_sharpe" label="Bear SR" className="border-l" />
                <th className="px-2 py-2 text-right text-gray-500 whitespace-nowrap">Bull SR</th>
                {/* CAPM */}
                <SortTh col="capm_alpha" label="α/yr" className="border-l" />
                <th className="px-2 py-2 text-right text-gray-500 whitespace-nowrap">β</th>
                {/* L/S */}
                <SortTh col="ls_sharpe" label="L/S SR" className="border-l" />
                <th className="px-2 py-2 text-right text-gray-500 whitespace-nowrap">SPY Corr</th>
                <th className="px-2 py-2 text-right text-gray-500 whitespace-nowrap">WF</th>
                {/* Validation */}
                <th className="px-2 py-2 text-center text-gray-500 whitespace-nowrap border-l">MC</th>
                <SortTh col="lo_wfe" label="WFE%" className="" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {rows.map((row, i) => {
                const slug = row.strategy.replace(/_/g, '-')
                return (
                  <tr key={row.strategy} className={cn('hover:bg-blue-50/30 transition-colors', i % 2 === 0 ? 'bg-white' : 'bg-gray-50/40')}>
                    {/* Strategy name */}
                    <td className="px-3 py-2.5 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <TierBadge tier={row.tier} />
                        <Link href={`/strategy/${slug}`} className="font-medium text-gray-900 hover:text-blue-600 transition-colors">
                          {row.display_name}
                        </Link>
                      </div>
                    </td>
                    {/* Long-only */}
                    <td className="px-2 py-2.5 text-right border-l"><SrCell v={row.lo_sharpe} threshold={0.65} /></td>
                    <td className="px-2 py-2.5 text-right"><SrCell v={row.lo_adj_sharpe} threshold={0.55} /></td>
                    <td className="px-2 py-2.5 text-right text-gray-600 tabular-nums">{fmt(row.lo_cagr, true, 1)}</td>
                    <td className="px-2 py-2.5 text-right text-red-500 tabular-nums">{fmt(row.lo_max_drawdown, true, 1)}</td>
                    <td className="px-2 py-2.5 text-right text-gray-600 tabular-nums">{fmt(row.lo_pct_pos_years, false, 0)}%</td>
                    {/* Regime */}
                    <td className="px-2 py-2.5 text-right border-l">
                      <span className="text-red-500 font-semibold tabular-nums">{fmt(row.lo_bear_sharpe)}</span>
                    </td>
                    <td className="px-2 py-2.5 text-right">
                      <span className="text-emerald-600 font-semibold tabular-nums">{fmt(row.lo_bull_sharpe)}</span>
                    </td>
                    {/* CAPM */}
                    <td className="px-2 py-2.5 text-right border-l">
                      <span className={cn('font-semibold tabular-nums', (row.capm_alpha ?? 0) > 0 ? 'text-emerald-600' : 'text-red-500')}>
                        {fmt(row.capm_alpha, true, 1, true)}
                      </span>
                    </td>
                    <td className="px-2 py-2.5 text-right text-gray-600 tabular-nums">{fmt(row.capm_beta)}</td>
                    {/* L/S */}
                    <td className="px-2 py-2.5 text-right border-l"><SrCell v={row.ls_sharpe} threshold={0.4} /></td>
                    <td className="px-2 py-2.5 text-right text-gray-600 tabular-nums">{fmt(row.ls_spy_corr)}</td>
                    <td className="px-2 py-2.5 text-right"><WFBadge verdict={row.ls_wf_verdict} /></td>
                    {/* Validation */}
                    <td className="px-2 py-2.5 text-center border-l"><MCBadge verdict={row.mc_verdict} /></td>
                    <td className="px-2 py-2.5 text-right text-gray-600 tabular-nums">
                      {row.lo_wfe != null ? `${row.lo_wfe.toFixed(0)}%` : '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {/* Footer legend */}
        <div className="px-4 py-3 bg-gray-50 border-t grid grid-cols-4 gap-4 text-xs text-gray-500">
          <div><strong className="text-gray-700">Adj SR</strong> — Pezier-White Sharpe (penalises negative skew + fat tails)</div>
          <div><strong className="text-gray-700">Bear / Bull SR</strong> — Sharpe in regime-identified bear/bull months</div>
          <div><strong className="text-gray-700">L/S SR</strong> — Dollar-neutral quintile portfolio. Positive = factor works cross-sectionally</div>
          <div><strong className="text-gray-700">WFE</strong> — Walk-forward efficiency (OOS÷IS Sharpe ×100%). &gt;100% = OOS outperforms IS</div>
        </div>
      </div>

      <p className="text-xs text-gray-400 mt-3 text-center">
        Data: 653 S&P 500 stocks · 2000–2024 · Transaction costs 15 bps · Point-in-time universe
      </p>
    </div>
  )
}
