'use client'

import { useState, useMemo } from 'react'
import { Info, Loader2, RefreshCw, AlertCircle, ArrowUpDown } from 'lucide-react'
import { FilterSidebar } from '@/components/FilterSidebar'
import { KpiTiles } from '@/components/KpiTiles'
import { StrategyCard } from '@/components/StrategyCard'
import { useDashboardData } from '@/hooks/useDashboardData'

export default function DashboardPage() {
  // Fetch real data from API
  const { strategies, benchmark, isLoading, error, refetch } = useDashboardData()

  // Filter state
  const [selectedFamilies, setSelectedFamilies] = useState<string[]>([])
  const [selectedFactors, setSelectedFactors] = useState<string[]>([])
  const [selectedRisk, setSelectedRisk] = useState<string[]>([])
  const [selectedMarketCaps, setSelectedMarketCaps] = useState<string[]>([])
  const [selectedDateRange, setSelectedDateRange] = useState('2000-2024')
  const [sortBy, setSortBy] = useState<'tier' | 'sharpe4yr' | 'sharpe25yr' | 'cagr' | 'maxdd'>('tier')
  const [selectedTier, setSelectedTier] = useState<string[]>([])

  // Filtered + sorted strategies
  const filteredStrategies = useMemo(() => {
    const tierOrder: Record<string, number> = { 'Tier 1': 1, 'Tier 2': 2, 'Tier 3': 3 }

    return strategies
      .filter(strategy => {
      // Family filter
      if (selectedFamilies.length > 0 && !selectedFamilies.includes(strategy.family)) {
        return false
      }

      // Factor filter (any match)
      if (selectedFactors.length > 0) {
        const hasMatch = selectedFactors.some(factor => strategy.factorTags.includes(factor))
        if (!hasMatch) return false
      }

      // Risk filter
      if (selectedRisk.length > 0 && !selectedRisk.includes(strategy.riskProfile)) {
        return false
      }

      // Market cap filter (any match)
      if (selectedMarketCaps.length > 0) {
        const hasMatch = selectedMarketCaps.some(cap => strategy.marketCaps.includes(cap))
        if (!hasMatch) return false
      }

        // Tier filter
        if (selectedTier.length > 0) {
          const stratTier = strategy.tier?.split(' — ')[0] ?? ''
          if (!selectedTier.includes(stratTier)) return false
        }

        return true
      })
      .sort((a, b) => {
        if (sortBy === 'tier') {
          const ta = tierOrder[a.tier?.split(' — ')[0] ?? ''] ?? 99
          const tb = tierOrder[b.tier?.split(' — ')[0] ?? ''] ?? 99
          return ta - tb
        }
        if (sortBy === 'sharpe4yr') return (b.metrics.sharpeRatio ?? 0) - (a.metrics.sharpeRatio ?? 0)
        if (sortBy === 'sharpe25yr') return (b.phase3Sharpe ?? 0) - (a.phase3Sharpe ?? 0)
        if (sortBy === 'cagr') return (b.metrics.cagr ?? 0) - (a.metrics.cagr ?? 0)
        if (sortBy === 'maxdd') return (a.metrics.maxDrawdown ?? 0) - (b.metrics.maxDrawdown ?? 0) // least negative first
        return 0
      })
  }, [strategies, selectedFamilies, selectedFactors, selectedRisk, selectedMarketCaps, selectedTier, sortBy])

  // Calculate KPIs from real data
  const kpis = useMemo(() => {
    // Use 25yr Sharpe (phase3Sharpe) for honest long-run comparison
    const validSharpes25 = strategies
      .map(s => s.phase3Sharpe)
      .filter((v): v is number => v !== null && !isNaN(v))
    const avgSharpe = validSharpes25.length > 0
      ? validSharpes25.reduce((a, b) => a + b, 0) / validSharpes25.length
      : 0

    const bestSharpe = validSharpes25.length > 0 ? Math.max(...validSharpes25) : 0

    const validDrawdowns = strategies
      .map(s => s.metrics.maxDrawdown)
      .filter((v): v is number => v !== null && !isNaN(v))
    const avgMaxDD = validDrawdowns.length > 0
      ? validDrawdowns.reduce((a, b) => a + b, 0) / validDrawdowns.length * 100
      : 0

    const benchmarkSharpe = benchmark?.metrics?.sharpe_ratio ?? null

    return { avgSharpe, bestSharpe, avgMaxDD, benchmarkSharpe }
  }, [strategies, benchmark])

  // Loading state
  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-56px)] items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-500">Loading strategy data from API...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="flex h-[calc(100vh-56px)] items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Failed to Load Data</h2>
          <p className="text-gray-500 mb-4">{error}</p>
          <p className="text-sm text-gray-400 mb-4">
            Make sure the API server is running at http://localhost:8000
          </p>
          <button
            onClick={refetch}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md"
          >
            <RefreshCw className="w-4 h-4" />
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-[calc(100vh-56px)]">
      {/* Sidebar */}
      <FilterSidebar
        selectedFamilies={selectedFamilies}
        setSelectedFamilies={setSelectedFamilies}
        selectedFactors={selectedFactors}
        setSelectedFactors={setSelectedFactors}
        selectedRisk={selectedRisk}
        setSelectedRisk={setSelectedRisk}
        selectedMarketCaps={selectedMarketCaps}
        setSelectedMarketCaps={setSelectedMarketCaps}
        selectedDateRange={selectedDateRange}
        setSelectedDateRange={setSelectedDateRange}
      />

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Strategy Dashboard</h1>
          <p className="text-gray-500 mt-1">
            Explore and compare {strategies.length} systematic trading strategies with real backtest data
          </p>
        </div>

        {/* Dataset Banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-6 flex items-center gap-2">
          <Info className="w-4 h-4 text-blue-600 flex-shrink-0" />
          <p className="text-sm text-blue-700">
            <span className="font-medium">25-year backtest:</span> 653 S&P 500 stocks, 2000–2024 (equal-weighted benchmark).
            {benchmark && (
              <span className="ml-1">
                Benchmark Sharpe: {((benchmark.metrics.sharpe_ratio || 0)).toFixed(2)} · Total return: {((benchmark.metrics.total_return || 0) * 100).toFixed(0)}%
              </span>
            )}
          </p>
        </div>

        {/* KPI Tiles */}
        <KpiTiles
          totalStrategies={strategies.length}
          bestSharpe={kpis.bestSharpe}
          avgSharpe={kpis.avgSharpe}
          avgMaxDD={kpis.avgMaxDD}
          benchmarkSharpe={kpis.benchmarkSharpe}
        />

        {/* Sort + Tier filter controls */}
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-600">Sort:</span>
            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value as typeof sortBy)}
              className="text-sm border rounded px-2 py-1 text-gray-700 bg-white"
            >
              <option value="tier">Phase 3 Tier</option>
              <option value="sharpe25yr">Sharpe (25yr)</option>
              <option value="sharpe4yr">Sharpe (4yr)</option>
              <option value="cagr">CAGR</option>
              <option value="maxdd">Min Drawdown</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Tier:</span>
            {['Tier 1', 'Tier 2', 'Tier 3'].map(t => (
              <button
                key={t}
                onClick={() => setSelectedTier(prev =>
                  prev.includes(t) ? prev.filter(x => x !== t) : [...prev, t]
                )}
                className={`text-xs px-2.5 py-1 rounded-full font-medium transition-colors ${
                  selectedTier.includes(t)
                    ? t === 'Tier 1' ? 'bg-emerald-600 text-white' :
                      t === 'Tier 2' ? 'bg-blue-600 text-white' :
                      'bg-gray-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
          <p className="text-sm text-gray-500 ml-auto">
            {filteredStrategies.length} of {strategies.length} strategies
          </p>
        </div>

        {/* Strategy Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredStrategies.map(strategy => (
            <StrategyCard key={strategy.slug + '-' + strategy.symbol} strategy={strategy} />
          ))}
        </div>

        {/* Empty State */}
        {filteredStrategies.length === 0 && strategies.length > 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No strategies match your filters.</p>
            <button
              onClick={() => {
                setSelectedFamilies([])
                setSelectedFactors([])
                setSelectedRisk([])
                setSelectedMarketCaps([])
              }}
              className="mt-2 text-blue-600 hover:text-blue-700 text-sm"
            >
              Clear all filters
            </button>
          </div>
        )}

        {/* No data state */}
        {strategies.length === 0 && !isLoading && !error && (
          <div className="text-center py-12">
            <p className="text-gray-500">No backtest data available.</p>
            <p className="text-sm text-gray-400 mt-2">
              Run the backtest script to generate strategy results.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
