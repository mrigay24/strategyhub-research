'use client'

import Link from 'next/link'
import { ArrowRight, Clock, RefreshCw } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { EnrichedStrategy } from '@/hooks/useDashboardData'

interface StrategyCardProps {
  strategy: EnrichedStrategy
}

// Helper to format percentage
function formatPercent(value: number | null | undefined, decimals: number = 1): string {
  if (value === null || value === undefined || isNaN(value)) return 'N/A'
  return `${(value * 100).toFixed(decimals)}%`
}

// Helper to format number
function formatNumber(value: number | null | undefined, decimals: number = 2): string {
  if (value === null || value === undefined || isNaN(value)) return 'N/A'
  return value.toFixed(decimals)
}

export function StrategyCard({ strategy }: StrategyCardProps) {
  const riskColors: Record<string, string> = {
    'Low Risk': 'bg-green-100 text-green-700',
    'Medium Risk': 'bg-yellow-100 text-yellow-700',
    'High Risk': 'bg-red-100 text-red-700',
  }

  const familyColors: Record<string, string> = {
    'Factor Strategies': 'text-blue-600',
    'Technical Strategies': 'text-purple-600',
    'Multi-Factor Strategies': 'text-emerald-600',
    'Advanced / Quant Extensions': 'text-orange-600',
    'Other': 'text-gray-600',
  }

  return (
    <div className="bg-white rounded-lg border hover:shadow-md transition-shadow p-5 flex flex-col">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className={cn('text-xs font-medium mb-1', familyColors[strategy.family] || 'text-gray-600')}>
            {strategy.family}
          </p>
          <h3 className="text-lg font-semibold text-gray-900">{strategy.displayName}</h3>
        </div>
        <div className="flex flex-col items-end gap-1">
          {strategy.tier && (
            <span className={cn(
              'px-2 py-0.5 text-xs font-medium rounded',
              strategy.tier.includes('Tier 1') ? 'bg-emerald-100 text-emerald-700' :
              strategy.tier.includes('Tier 2') ? 'bg-blue-100 text-blue-700' :
              'bg-gray-100 text-gray-600'
            )}>
              {strategy.tier.split(' — ')[0]}
            </span>
          )}
          {strategy.implemented && (
            <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded">
              Live
            </span>
          )}
        </div>
      </div>

      {/* Symbol if single-asset */}
      {strategy.symbol && strategy.symbol !== 'UNIVERSE' && (
        <p className="text-xs text-gray-500 mb-2">
          Tested on: <span className="font-medium text-gray-700">{strategy.symbol}</span>
        </p>
      )}

      {/* Factor Tags */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {strategy.factorTags.map(tag => (
          <span
            key={tag}
            className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
          >
            {tag}
          </span>
        ))}
      </div>

      {/* Meta Row */}
      <div className="flex items-center gap-4 text-xs text-gray-500 mb-3">
        <div className="flex items-center gap-1">
          <Clock className="w-3.5 h-3.5" />
          <span>{strategy.horizon}</span>
        </div>
        <div className="flex items-center gap-1">
          <RefreshCw className="w-3.5 h-3.5" />
          <span>{strategy.rebalanceFrequency}</span>
        </div>
        <span className={cn('px-2 py-0.5 rounded text-xs font-medium', riskColors[strategy.riskProfile] || 'bg-gray-100 text-gray-700')}>
          {strategy.riskProfile}
        </span>
      </div>

      {/* Performance Preview — all metrics from 25-year dataset (2000–2024) */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-2 py-3 border-t border-b mb-4">
        <div>
          <p className="text-xs text-gray-500">CAGR (25yr)</p>
          <p className="text-sm font-semibold text-gray-900">
            {formatPercent(strategy.metrics.cagr)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Sharpe (25yr)</p>
          <p className="text-sm font-semibold text-gray-900">
            {strategy.phase3Sharpe !== null ? formatNumber(strategy.phase3Sharpe) : formatNumber(strategy.metrics.sharpeRatio)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Max Drawdown</p>
          <p className="text-sm font-semibold text-red-600">
            {formatPercent(strategy.metrics.maxDrawdown)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Win Rate</p>
          <p className="text-sm font-semibold text-gray-900">
            {formatPercent(strategy.metrics.winRate)}
          </p>
        </div>
      </div>

      {/* CTA */}
      <Link
        href={`/strategy/${strategy.slug}`}
        className="mt-auto flex items-center justify-center gap-2 w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md transition-colors"
      >
        View Strategy
        <ArrowRight className="w-4 h-4" />
      </Link>
    </div>
  )
}
