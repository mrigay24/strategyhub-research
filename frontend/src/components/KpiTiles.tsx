'use client'

import { TrendingUp, Award, BarChart3, TrendingDown } from 'lucide-react'

interface KpiTilesProps {
  totalStrategies: number
  bestSharpe: number
  avgSharpe: number
  avgMaxDD: number
  benchmarkSharpe: number | null
}

export function KpiTiles({ totalStrategies, bestSharpe, avgSharpe, avgMaxDD, benchmarkSharpe }: KpiTilesProps) {
  const benchmarkLabel = benchmarkSharpe !== null ? benchmarkSharpe.toFixed(2) : '0.69'

  const tiles = [
    {
      label: 'Factor Strategies',
      value: totalStrategies.toString(),
      sub: '25-year S&P 500 study',
      icon: BarChart3,
      color: 'bg-blue-50 text-blue-600',
    },
    {
      label: 'Best Sharpe (25yr)',
      value: bestSharpe.toFixed(2),
      sub: 'Low Volatility Shield',
      icon: Award,
      color: 'bg-emerald-50 text-emerald-600',
    },
    {
      label: 'Avg Sharpe (25yr)',
      value: avgSharpe.toFixed(2),
      sub: `vs benchmark ${benchmarkLabel}`,
      icon: TrendingUp,
      color: avgSharpe >= (benchmarkSharpe ?? 0.69) ? 'bg-purple-50 text-purple-600' : 'bg-orange-50 text-orange-600',
    },
    {
      label: 'Avg Max Drawdown',
      value: `${avgMaxDD.toFixed(1)}%`,
      sub: 'Long-only, all strategies',
      icon: TrendingDown,
      color: 'bg-red-50 text-red-600',
    },
  ]

  return (
    <div className="grid grid-cols-4 gap-4 mb-6">
      {tiles.map((tile) => {
        const Icon = tile.icon
        return (
          <div
            key={tile.label}
            className="bg-white rounded-lg border p-4 flex items-center gap-4"
          >
            <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${tile.color}`}>
              <Icon className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs text-gray-500">{tile.label}</p>
              <p className="text-2xl font-semibold text-gray-900">{tile.value}</p>
              <p className="text-xs text-gray-400 mt-0.5">{tile.sub}</p>
            </div>
          </div>
        )
      })}
    </div>
  )
}
