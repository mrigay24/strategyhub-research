import Link from 'next/link'
import { ArrowRight, AlertTriangle, TrendingDown, BarChart2, Shuffle, Shield, FlaskConical } from 'lucide-react'

export const metadata = {
  title: 'Key Research Findings — StrategyHub',
  description: 'What 25 years of S&P 500 backtesting actually shows about systematic factor strategies.',
}

// ── Data hardcoded from Phase 3 research (2000–2024, 653 stocks) ──

const BENCHMARK_SHARPE = 0.694
const BENCHMARK_CAGR = 12.4

const TIER_1 = [
  { name: 'Low Volatility Shield', sharpe: 0.659, alpha: '+1.7%/yr', beta: 0.54 },
  { name: 'RSI Mean Reversion', sharpe: 0.641, alpha: '+0.3%/yr', beta: 0.73 },
]

const TIER_2 = [
  { name: 'Quality + Momentum', sharpe: 0.600 },
  { name: 'Quality + Low Vol', sharpe: 0.597 },
  { name: 'Composite Factor Score', sharpe: 0.595 },
  { name: 'Moving Average Trend', sharpe: 0.588 },
  { name: 'Value + Momentum Blend', sharpe: 0.581 },
  { name: 'Large Cap Momentum', sharpe: 0.576 },
]

const ALPHA_TABLE = [
  { name: 'Earnings Surprise', alpha: 2.6, beta: 1.18, significant: true },
  { name: 'Low Volatility Shield', alpha: 1.7, beta: 0.54, significant: true },
  { name: 'High Quality ROIC', alpha: 0.9, beta: 0.68, significant: false },
  { name: 'Moving Average Trend', alpha: 0.4, beta: 0.81, significant: false },
  { name: 'Large Cap Momentum', alpha: -0.2, beta: 0.91, significant: false },
  { name: 'Deep Value All-Cap', alpha: -1.1, beta: 1.03, significant: false },
]

function FindingCard({
  icon: Icon,
  color,
  title,
  stat,
  statLabel,
  children,
}: {
  icon: React.ElementType
  color: string
  title: string
  stat: string
  statLabel: string
  children: React.ReactNode
}) {
  return (
    <div className="bg-white rounded-xl border p-6">
      <div className="flex items-start gap-4 mb-4">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <h2 className="font-semibold text-gray-900 text-base">{title}</h2>
        </div>
      </div>
      <div className="mb-4">
        <p className="text-4xl font-bold text-gray-900">{stat}</p>
        <p className="text-sm text-gray-500 mt-1">{statLabel}</p>
      </div>
      <div className="text-sm text-gray-600 leading-relaxed space-y-2">{children}</div>
    </div>
  )
}

export default function FindingsPage() {
  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="mb-10">
        <p className="text-xs font-medium text-blue-600 uppercase tracking-wide mb-2">
          25-Year Study · 653 S&amp;P 500 Stocks · 2000–2024
        </p>
        <h1 className="text-3xl font-bold text-gray-900 mb-3">
          What the Data Actually Shows
        </h1>
        <p className="text-gray-500 max-w-2xl text-base leading-relaxed">
          14 factor strategies. 25 years. 8 validation layers. Most findings are uncomfortable —
          and that's the point. Honest research is more valuable than polished narratives.
        </p>
      </div>

      {/* Main grid */}
      <div className="grid md:grid-cols-2 gap-6 mb-8">

        {/* Finding 1 */}
        <FindingCard
          icon={TrendingDown}
          color="bg-orange-50 text-orange-600"
          title="All 14 strategies lag the benchmark"
          stat="0/14"
          statLabel="strategies beat equal-weighted S&P 500 on Sharpe (25yr)"
        >
          <p>
            The benchmark Sharpe is <strong>{BENCHMARK_SHARPE}</strong> (CAGR {BENCHMARK_CAGR}%).
            The best strategy — Low Volatility Shield — achieves 0.659. The gap is small but consistent across
            all 25 years.
          </p>
          <p>
            <strong>Why:</strong> All strategies have market beta β = 0.54–1.18. They earn returns primarily
            from market exposure, not from factor discrimination. A passive equal-weight index captures
            the same risk premium more cheaply.
          </p>
          <div className="mt-3 pt-3 border-t">
            <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
              <span>Best strategy (Low Vol Shield)</span><span className="font-semibold text-gray-800">0.659</span>
            </div>
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>Benchmark (equal-weight S&amp;P 500)</span><span className="font-semibold text-orange-700">{BENCHMARK_SHARPE}</span>
            </div>
          </div>
        </FindingCard>

        {/* Finding 2 */}
        <FindingCard
          icon={Shuffle}
          color="bg-red-50 text-red-600"
          title="No strategy consistently wins"
          stat="−0.123"
          statLabel="rank stability (Spearman YoY) — anything < 0.3 is unstable"
        >
          <p>
            Year-over-year rank correlation across all 14 strategies is <strong>−0.123</strong> — essentially
            random. Last year's top performer has no predictive power for next year.
          </p>
          <p>
            <strong>Implication:</strong> Strategy selection based on recent annual Sharpe is unreliable.
            The ranking reshuffles completely each year. This rules out simple momentum-of-strategies
            as a portfolio construction method.
          </p>
          <p>
            The only stable observation: <em>all strategies lose together in bear markets</em> (GFC
            2008, dot-com 2000–02, 2022).
          </p>
        </FindingCard>

        {/* Finding 3 */}
        <FindingCard
          icon={BarChart2}
          color="bg-purple-50 text-purple-600"
          title="Diversifying across strategies adds almost nothing"
          stat="0.951"
          statLabel="average pairwise correlation across all 91 strategy pairs"
        >
          <p>
            90 of 91 strategy pairs have correlation r &gt; 0.80. In bear markets (2008–09), avg
            correlation rises to <strong>0.969</strong> — exactly when diversification is most needed.
          </p>
          <p>
            <strong>Diversification ratio:</strong> 1.024 vs theoretical 1.0 for perfectly correlated assets.
            A portfolio of all 14 strategies provides almost no risk reduction vs holding one.
          </p>
          <p>
            <strong>Root cause:</strong> All strategies are long-only equity on the same universe.
            They share market beta. Factor differences (momentum vs value vs quality) are second-order
            effects swamped by equity market co-movement.
          </p>
        </FindingCard>

        {/* Finding 4 */}
        <FindingCard
          icon={AlertTriangle}
          color="bg-amber-50 text-amber-600"
          title="Every strategy fails in bear markets"
          stat="< −1.2"
          statLabel="average Sharpe across all 14 strategies in Bear regime"
        >
          <p>
            Regime analysis (Bull 40%, Bear 12%, High-Vol 17.5%, Sideways 30.5%) shows all
            strategies produce deeply negative Sharpe ratios in Bear regime.
          </p>
          <p>
            Regime overlay (exit to cash in Bear) does <strong>not</strong> help — a 63-day signal
            lag misses fast crashes. COVID (2020) crash duration: 23 trading days.
            By the time the overlay fires, the damage is done.
          </p>
          <p>
            <strong>GFC stress test:</strong> Walk-forward Fold 2 (2008–09 OOS window) —
            every single strategy posted negative Sharpe. No exceptions.
          </p>
        </FindingCard>
      </div>

      {/* Alpha table */}
      <div className="bg-white rounded-xl border p-6 mb-6">
        <div className="flex items-start gap-4 mb-5">
          <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 bg-emerald-50 text-emerald-600">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-semibold text-gray-900">Only 2 of 14 strategies show genuine alpha</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              CAPM attribution · β/α over 25-year horizon · r<sub>f</sub> = 2%/yr
            </p>
          </div>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          CAPM alpha measures return unexplained by market exposure. Most strategies have
          near-zero or negative alpha — they earn returns through beta, not skill.
          The two exceptions are meaningful but modest.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-xs text-gray-500 uppercase tracking-wide">
                <th className="text-left pb-2">Strategy</th>
                <th className="text-right pb-2">Market β</th>
                <th className="text-right pb-2">CAPM α/yr</th>
                <th className="text-right pb-2">Significance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {ALPHA_TABLE.map(row => (
                <tr key={row.name} className={row.significant ? 'bg-emerald-50/50' : ''}>
                  <td className="py-2.5 font-medium text-gray-900">{row.name}</td>
                  <td className="py-2.5 text-right text-gray-600">{row.beta.toFixed(2)}</td>
                  <td className={`py-2.5 text-right font-semibold ${row.alpha > 0 ? 'text-emerald-700' : 'text-red-600'}`}>
                    {row.alpha > 0 ? '+' : ''}{row.alpha.toFixed(1)}%
                  </td>
                  <td className="py-2.5 text-right">
                    {row.significant
                      ? <span className="px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded text-xs font-medium">Meaningful</span>
                      : <span className="text-gray-400 text-xs">—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-gray-400 mt-3">
          Showing representative sample. Full CAPM attribution available on each strategy detail page.
        </p>
      </div>

      {/* Tier rankings */}
      <div className="bg-white rounded-xl border p-6 mb-6">
        <div className="flex items-start gap-4 mb-5">
          <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 bg-blue-50 text-blue-600">
            <FlaskConical className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-semibold text-gray-900">Phase 3 Tier Rankings (25-year composite score)</h2>
            <p className="text-sm text-gray-500 mt-0.5">Sharpe · Monte Carlo significance · Walk-forward efficiency · Regime robustness</p>
          </div>
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <p className="text-xs font-medium text-emerald-700 uppercase tracking-wide mb-2">Tier 1 — Best Risk-Adjusted</p>
            {TIER_1.map(s => (
              <Link
                key={s.name}
                href={`/strategy/${s.name.toLowerCase().replace(/[\s+]/g, '-').replace(/[^a-z0-9-]/g, '')}`}
                className="flex items-center justify-between p-3 rounded-lg bg-emerald-50 hover:bg-emerald-100 transition-colors mb-2 group"
              >
                <div>
                  <p className="font-medium text-gray-900 text-sm">{s.name}</p>
                  <p className="text-xs text-emerald-700 mt-0.5">CAPM α {s.alpha} · β {s.beta.toFixed(2)}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold text-gray-900">{s.sharpe.toFixed(3)}</span>
                  <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-gray-600 transition-colors" />
                </div>
              </Link>
            ))}
          </div>
          <div>
            <p className="text-xs font-medium text-blue-700 uppercase tracking-wide mb-2">Tier 2 — Solid but Benchmark-Lagging</p>
            {TIER_2.map(s => (
              <div key={s.name} className="flex items-center justify-between p-2.5 rounded-lg hover:bg-gray-50 mb-1">
                <p className="font-medium text-gray-700 text-sm">{s.name}</p>
                <span className="text-sm font-semibold text-gray-900">{s.sharpe.toFixed(3)}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="mt-4 pt-4 border-t flex items-center justify-between text-xs text-gray-500">
          <span>All tiers lag benchmark Sharpe of <strong className="text-gray-700">{BENCHMARK_SHARPE}</strong></span>
          <Link href="/" className="text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1">
            View all 14 strategies <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
      </div>

      {/* Methodology callout */}
      <div className="bg-gray-50 rounded-xl border p-6">
        <h3 className="font-semibold text-gray-900 mb-3">Validation Methodology</h3>
        <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          {[
            { label: 'Data span', value: '25 years (2000–2024)', sub: '653 stocks, 3.4M rows' },
            { label: 'Survivorship bias', value: '~17% upward bias', sub: 'Corrected with PIT constituents' },
            { label: 'Transaction costs', value: '15 bps round-trip', sub: 'All 14 strategies bulletproof' },
            { label: 'Monte Carlo', value: '12/14 significant', sub: 'Bonferroni p < 0.0036' },
          ].map(item => (
            <div key={item.label}>
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">{item.label}</p>
              <p className="font-semibold text-gray-900">{item.value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{item.sub}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
