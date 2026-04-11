'use client'

import { cn } from '@/lib/utils'

// Short display names for heatmap labels (space is tight)
const SHORT_NAMES: Record<string, string> = {
  large_cap_momentum: 'LCM',
  '52_week_high_breakout': '52WH',
  deep_value_all_cap: 'Val',
  high_quality_roic: 'Qual',
  low_volatility_shield: 'LowV',
  dividend_aristocrats: 'Div',
  moving_average_trend: 'MA',
  rsi_mean_reversion: 'RSI',
  value_momentum_blend: 'V+M',
  quality_momentum: 'Q+M',
  quality_low_vol: 'Q+V',
  composite_factor_score: 'CFS',
  volatility_targeting: 'VT',
  earnings_surprise_momentum: 'ESM',
}

function corrColor(value: number): string {
  // Red scale: 0.70 → white, 1.0 → deep red
  const t = Math.max(0, Math.min(1, (value - 0.70) / 0.30))
  const r = Math.round(255)
  const g = Math.round(255 - t * 200)
  const b = Math.round(255 - t * 200)
  return `rgb(${r},${g},${b})`
}

function textColor(value: number): string {
  return value > 0.90 ? '#7f1d1d' : '#374151'
}

interface Props {
  strategies: string[];
  cells: { row: string; col: string; value: number | null }[];
}

export function CorrelationHeatmap({ strategies, cells }: Props) {
  // Build lookup map
  const lookup = new Map<string, number>()
  cells.forEach(c => {
    if (c.value !== null) lookup.set(`${c.row}__${c.col}`, c.value)
  })

  const cellSize = 38

  return (
    <div className="overflow-x-auto">
      <table className="text-xs border-collapse" style={{ minWidth: strategies.length * cellSize + 80 }}>
        <thead>
          <tr>
            <th className="w-20" />
            {strategies.map(s => (
              <th
                key={s}
                className="text-gray-500 font-medium pb-1"
                style={{ width: cellSize, fontSize: 10, writingMode: 'vertical-rl', textAlign: 'left', paddingBottom: 4 }}
              >
                {SHORT_NAMES[s] ?? s.slice(0, 4)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {strategies.map(row => (
            <tr key={row}>
              <td
                className="text-gray-600 font-medium pr-2 text-right whitespace-nowrap"
                style={{ fontSize: 10 }}
              >
                {SHORT_NAMES[row] ?? row.slice(0, 6)}
              </td>
              {strategies.map(col => {
                const val = lookup.get(`${row}__${col}`) ?? null
                const isdiag = row === col
                return (
                  <td
                    key={col}
                    title={`${SHORT_NAMES[row]} vs ${SHORT_NAMES[col]}: ${val?.toFixed(3) ?? 'N/A'}`}
                    style={{
                      width: cellSize,
                      height: cellSize,
                      backgroundColor: isdiag ? '#f3f4f6' : val !== null ? corrColor(val) : '#f3f4f6',
                      color: val !== null ? textColor(val) : '#9ca3af',
                      textAlign: 'center',
                      fontWeight: isdiag ? 600 : 400,
                      border: '1px solid #e5e7eb',
                      fontSize: 9,
                    }}
                  >
                    {isdiag ? '—' : val !== null ? val.toFixed(2) : ''}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      {/* Legend */}
      <div className="flex items-center gap-3 mt-3">
        <span className="text-xs text-gray-500">Correlation:</span>
        {[0.70, 0.80, 0.90, 0.95, 1.00].map(v => (
          <div key={v} className="flex items-center gap-1">
            <div className="w-4 h-4 rounded border border-gray-200" style={{ backgroundColor: corrColor(v) }} />
            <span className="text-xs text-gray-500">{v.toFixed(2)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
