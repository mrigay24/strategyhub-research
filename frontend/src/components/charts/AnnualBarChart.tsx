'use client'

import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts'

interface DataPoint {
  year: number;
  strategy: number | null;
  benchmark: number | null;
}

interface Props {
  data: DataPoint[];
  metric: 'sharpe' | 'cagr' | 'mdd';
  strategyLabel?: string;
  benchmarkAvg?: number | null;
}

const formatters: Record<string, (v: number) => string> = {
  sharpe: (v) => v.toFixed(2),
  cagr: (v) => `${(v * 100).toFixed(1)}%`,
  mdd: (v) => `${(v * 100).toFixed(1)}%`,
}

const yFormatters: Record<string, (v: number) => string> = {
  sharpe: (v) => v.toFixed(1),
  cagr: (v) => `${(v * 100).toFixed(0)}%`,
  mdd: (v) => `${(v * 100).toFixed(0)}%`,
}

const labels: Record<string, string> = {
  sharpe: 'Annual Sharpe Ratio',
  cagr: 'Annual Return (CAGR)',
  mdd: 'Max Drawdown',
}

export function AnnualBarChart({ data, metric, strategyLabel = 'Strategy', benchmarkAvg }: Props) {
  const fmt = formatters[metric]
  const yFmt = yFormatters[metric]

  const barColor = (value: number) => {
    if (metric === 'sharpe' || metric === 'cagr') return value >= 0 ? '#3b82f6' : '#ef4444'
    return value <= -0.2 ? '#ef4444' : value <= -0.1 ? '#f59e0b' : '#3b82f6'
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <ComposedChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis
          dataKey="year"
          tick={{ fontSize: 10, fill: '#6b7280' }}
          tickLine={false}
          interval={3}
        />
        <YAxis
          tick={{ fontSize: 10, fill: '#6b7280' }}
          tickLine={false}
          axisLine={false}
          tickFormatter={yFmt}
          width={42}
        />
        <Tooltip
          formatter={(value: number, name: string) => [fmt(value), name === 'strategy' ? strategyLabel : 'Benchmark']}
          labelFormatter={(y) => `Year: ${y}`}
        />
        <Legend
          wrapperStyle={{ fontSize: 11 }}
          formatter={(value) => value === 'strategy' ? strategyLabel : 'Benchmark'}
        />
        <ReferenceLine y={0} stroke="#9ca3af" strokeWidth={1} />
        {benchmarkAvg != null && (
          <ReferenceLine
            y={benchmarkAvg}
            stroke="#dc2626"
            strokeDasharray="5 3"
            strokeWidth={1.5}
            label={{ value: `25yr avg: ${fmt(benchmarkAvg)}`, position: 'insideTopRight', fontSize: 9, fill: '#dc2626' }}
          />
        )}
        <Bar dataKey="strategy" fill="#3b82f6" opacity={0.85} radius={[2, 2, 0, 0]} name="strategy" />
        <Line
          type="monotone"
          dataKey="benchmark"
          stroke="#f59e0b"
          strokeWidth={2}
          dot={{ r: 2, fill: '#f59e0b' }}
          name="benchmark"
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
