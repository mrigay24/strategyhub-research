'use client'

import { ChevronDown, Filter } from 'lucide-react'
import { cn } from '@/lib/utils'

// Filter options
const familyOptions = [
  'Momentum Strategies',
  'Value Strategies',
  'Quality Strategies',
  'Factor Strategies',
  'Income Strategies',
  'Trend Strategies',
  'Mean Reversion Strategies',
  'Composite Strategies',
  'Multi-Factor Strategies',
  'Risk Management Strategies',
  'Event-Driven Strategies',
]

const factorTagOptions = [
  'Momentum',
  'Value',
  'Quality',
  'Low Volatility',
]

const riskProfileOptions = [
  'Low Risk',
  'Medium Risk',
  'High Risk',
]

const marketCapOptions = [
  'Large Cap',
  'Mid Cap',
  'Small Cap',
]

const dateRangeOptions = [
  { value: '2000-2024', label: '2000–2024 (25-year study)', disabled: false },
]

interface FilterSidebarProps {
  selectedFamilies: string[]
  setSelectedFamilies: (v: string[]) => void
  selectedFactors: string[]
  setSelectedFactors: (v: string[]) => void
  selectedRisk: string[]
  setSelectedRisk: (v: string[]) => void
  selectedMarketCaps: string[]
  setSelectedMarketCaps: (v: string[]) => void
  selectedDateRange: string
  setSelectedDateRange: (v: string) => void
}

export function FilterSidebar({
  selectedFamilies,
  setSelectedFamilies,
  selectedFactors,
  setSelectedFactors,
  selectedRisk,
  setSelectedRisk,
  selectedMarketCaps,
  setSelectedMarketCaps,
  selectedDateRange,
  setSelectedDateRange,
}: FilterSidebarProps) {

  const toggleFamily = (family: string) => {
    if (selectedFamilies.includes(family)) {
      setSelectedFamilies(selectedFamilies.filter(f => f !== family))
    } else {
      setSelectedFamilies([...selectedFamilies, family])
    }
  }

  const toggleFactor = (factor: string) => {
    if (selectedFactors.includes(factor)) {
      setSelectedFactors(selectedFactors.filter(f => f !== factor))
    } else {
      setSelectedFactors([...selectedFactors, factor])
    }
  }

  const toggleRisk = (risk: string) => {
    if (selectedRisk.includes(risk)) {
      setSelectedRisk(selectedRisk.filter(r => r !== risk))
    } else {
      setSelectedRisk([...selectedRisk, risk])
    }
  }

  const toggleMarketCap = (cap: string) => {
    if (selectedMarketCaps.includes(cap)) {
      setSelectedMarketCaps(selectedMarketCaps.filter(c => c !== cap))
    } else {
      setSelectedMarketCaps([...selectedMarketCaps, cap])
    }
  }

  const clearAllFilters = () => {
    setSelectedFamilies([])
    setSelectedFactors([])
    setSelectedRisk([])
    setSelectedMarketCaps([])
    setSelectedDateRange('2000-2024')
  }

  const hasActiveFilters =
    selectedFamilies.length > 0 ||
    selectedFactors.length > 0 ||
    selectedRisk.length > 0 ||
    selectedMarketCaps.length > 0

  return (
    <aside className="w-72 bg-white border-r p-4 overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <span className="font-medium text-gray-900">Filters</span>
        </div>
        {hasActiveFilters && (
          <button
            onClick={clearAllFilters}
            className="text-xs text-blue-600 hover:text-blue-700"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Strategy Family */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Strategy Family</h3>
        <div className="space-y-2">
          {familyOptions.map(family => (
            <label key={family} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedFamilies.includes(family)}
                onChange={() => toggleFamily(family)}
                className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-600">{family}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Factor Exposure */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Factor Exposure</h3>
        <div className="flex flex-wrap gap-2">
          {factorTagOptions.map(factor => (
            <button
              key={factor}
              onClick={() => toggleFactor(factor)}
              className={cn(
                'px-3 py-1 rounded-full text-xs font-medium transition-colors',
                selectedFactors.includes(factor)
                  ? 'bg-blue-100 text-blue-700 border border-blue-300'
                  : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200'
              )}
            >
              {factor}
            </button>
          ))}
        </div>
      </div>

      {/* Risk Profile */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Risk Profile</h3>
        <div className="space-y-2">
          {riskProfileOptions.map(risk => (
            <label key={risk} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedRisk.includes(risk)}
                onChange={() => toggleRisk(risk)}
                className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-600">{risk}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Market Universe */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Market Universe</h3>
        <div className="relative">
          <select
            className="w-full px-3 py-2 text-sm border border-gray-200 rounded-md bg-white appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500"
            defaultValue="sp500"
          >
            <option value="sp500">S&P 500 (2000–2024, 653 stocks)</option>
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
        </div>
      </div>

      {/* Market Cap */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Market Cap</h3>
        <div className="space-y-2">
          {marketCapOptions.map(cap => (
            <label key={cap} className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedMarketCaps.includes(cap)}
                onChange={() => toggleMarketCap(cap)}
                className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-600">{cap}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Date Range */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Date Range</h3>
        <div className="relative">
          <select
            value={selectedDateRange}
            onChange={(e) => setSelectedDateRange(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-200 rounded-md bg-white appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {dateRangeOptions.map(opt => (
              <option key={opt.value} value={opt.value} disabled={opt.disabled}>
                {opt.label}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
        </div>
      </div>
    </aside>
  )
}
