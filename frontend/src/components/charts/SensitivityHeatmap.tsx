'use client'

import { cn } from '@/lib/utils'

interface HeatmapCell {
  v1: number
  v2: number
  sharpe: number | null
}

interface Heatmap {
  param_1: string | null
  param_2: string | null
  values_1: number[]
  values_2: number[]
  default_1: number | null
  default_2: number | null
  grid: HeatmapCell[]
}

interface Sweep {
  param: string
  values: { param_value: number; sharpe_ratio: number | null; is_default: boolean }[]
}

interface Props {
  heatmap: Heatmap
  sweeps: Sweep[]
  defaults: Record<string, number>
}

function sharpeColor(value: number, min: number, max: number): string {
  // Green (high) to red (low) scale
  const range = max - min || 1
  const t = Math.max(0, Math.min(1, (value - min) / range))
  // t=0 → red(239,68,68), t=1 → green(34,197,94)
  const r = Math.round(239 - t * (239 - 34))
  const g = Math.round(68 + t * (197 - 68))
  const b = Math.round(68 + t * (94 - 68))
  return `rgb(${r},${g},${b})`
}

function textOnColor(value: number, min: number, max: number): string {
  const range = max - min || 1
  const t = (value - min) / range
  return t > 0.35 && t < 0.75 ? '#1f2937' : '#ffffff'
}

function formatParam(name: string): string {
  return name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export function SensitivityHeatmap({ heatmap, sweeps, defaults }: Props) {
  const validSharpes = heatmap.grid.map(c => c.sharpe).filter((v): v is number => v !== null)
  const minS = Math.min(...validSharpes)
  const maxS = Math.max(...validSharpes)

  // Build lookup: "v1_v2" → sharpe
  const lookup = new Map<string, number>()
  heatmap.grid.forEach(c => {
    if (c.sharpe !== null) lookup.set(`${c.v1}_${c.v2}`, c.sharpe)
  })

  const cellSize = 52

  return (
    <div className="space-y-6">
      {/* 2D Sharpe Heatmap */}
      {heatmap.param_1 && heatmap.param_2 && heatmap.values_1.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <h4 className="text-sm font-semibold text-gray-800">
              2D Parameter Heatmap — Sharpe Ratio
            </h4>
            <span className="text-xs text-gray-400">
              ({formatParam(heatmap.param_1)} × {formatParam(heatmap.param_2)})
            </span>
          </div>
          <p className="text-xs text-gray-500 mb-3">
            A broad ridge of green (robust) means the strategy works across many parameter combinations — not just the default.
            A single bright spot surrounded by red (fragile) means it's overfit to specific parameters.
          </p>

          <div className="overflow-x-auto">
            <div className="inline-block">
              {/* Y-axis label */}
              <div className="flex">
                <div
                  className="flex items-center justify-center text-xs text-gray-500 font-medium"
                  style={{ width: 64, writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}
                >
                  {formatParam(heatmap.param_2)}
                </div>
                <div>
                  {/* X-axis header */}
                  <div className="flex mb-1" style={{ paddingLeft: 28 }}>
                    {heatmap.values_1.map(v1 => (
                      <div
                        key={v1}
                        className={cn(
                          'text-center text-xs font-medium',
                          v1 === heatmap.default_1 ? 'text-blue-600' : 'text-gray-500'
                        )}
                        style={{ width: cellSize }}
                      >
                        {v1}
                        {v1 === heatmap.default_1 && <span className="ml-0.5 text-blue-500">★</span>}
                      </div>
                    ))}
                  </div>

                  {/* Grid rows */}
                  {heatmap.values_2.map(v2 => (
                    <div key={v2} className="flex items-center mb-0.5">
                      <div
                        className={cn(
                          'text-right pr-2 text-xs font-medium',
                          v2 === heatmap.default_2 ? 'text-blue-600' : 'text-gray-500'
                        )}
                        style={{ width: 28 }}
                      >
                        {v2}
                        {v2 === heatmap.default_2 && <span className="text-blue-500">★</span>}
                      </div>
                      {heatmap.values_1.map(v1 => {
                        const sharpe = lookup.get(`${v1}_${v2}`) ?? null
                        const isDefault = v1 === heatmap.default_1 && v2 === heatmap.default_2
                        return (
                          <div
                            key={v1}
                            title={`${formatParam(heatmap.param_1!)}=${v1}, ${formatParam(heatmap.param_2!)}=${v2}: Sharpe=${sharpe?.toFixed(3) ?? 'N/A'}`}
                            className={cn(
                              'flex items-center justify-center text-xs font-semibold rounded',
                              isDefault ? 'ring-2 ring-blue-500 ring-offset-1' : ''
                            )}
                            style={{
                              width: cellSize,
                              height: 36,
                              backgroundColor: sharpe !== null ? sharpeColor(sharpe, minS, maxS) : '#f3f4f6',
                              color: sharpe !== null ? textOnColor(sharpe, minS, maxS) : '#9ca3af',
                            }}
                          >
                            {sharpe?.toFixed(2) ?? '—'}
                          </div>
                        )
                      })}
                    </div>
                  ))}

                  {/* X-axis label */}
                  <div
                    className="text-center text-xs text-gray-500 font-medium mt-2"
                    style={{ paddingLeft: 28 }}
                  >
                    {formatParam(heatmap.param_1)}
                  </div>
                </div>
              </div>

              {/* Color legend */}
              <div className="flex items-center gap-2 mt-3 ml-20">
                <span className="text-xs text-gray-400">Low Sharpe</span>
                <div className="flex">
                  {[0, 0.2, 0.4, 0.6, 0.8, 1.0].map(t => (
                    <div
                      key={t}
                      className="w-6 h-3"
                      style={{ backgroundColor: sharpeColor(minS + t * (maxS - minS), minS, maxS) }}
                    />
                  ))}
                </div>
                <span className="text-xs text-gray-400">High Sharpe</span>
                <span className="text-xs text-gray-400 ml-3">★ = default</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 1D Sweeps */}
      {sweeps.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-800 mb-3">1D Parameter Sweeps</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {sweeps.map(sweep => {
              const sharpes = sweep.values.map(v => v.sharpe_ratio).filter((v): v is number => v !== null)
              const lo = Math.min(...sharpes)
              const hi = Math.max(...sharpes)
              return (
                <div key={sweep.param} className="bg-gray-50 rounded-lg p-3">
                  <div className="text-xs font-semibold text-gray-700 mb-2">{formatParam(sweep.param)}</div>
                  <div className="flex items-end gap-1">
                    {sweep.values.map(pt => {
                      const s = pt.sharpe_ratio ?? 0
                      const heightPct = hi > lo ? ((s - lo) / (hi - lo)) * 60 + 20 : 40
                      return (
                        <div
                          key={pt.param_value}
                          className="flex flex-col items-center flex-1"
                          title={`${sweep.param}=${pt.param_value}: Sharpe=${s.toFixed(3)}`}
                        >
                          <div
                            className={cn(
                              'w-full rounded-t',
                              pt.is_default ? 'bg-blue-500' : 'bg-gray-400'
                            )}
                            style={{ height: heightPct }}
                          />
                          <div className={cn(
                            'text-xs mt-1',
                            pt.is_default ? 'text-blue-600 font-semibold' : 'text-gray-400'
                          )}>
                            {pt.param_value}
                          </div>
                          <div className="text-xs text-gray-500">{s.toFixed(2)}</div>
                        </div>
                      )
                    })}
                  </div>
                  <div className="flex justify-between text-xs text-gray-400 mt-1">
                    <span>min {lo.toFixed(2)}</span>
                    <span>max {hi.toFixed(2)}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
