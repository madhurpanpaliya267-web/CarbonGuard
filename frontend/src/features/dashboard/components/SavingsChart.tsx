import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'
import { chartConfig } from '@/shared/utils/chartConfig'

interface SavingsChartProps {
  data: Array<{
    timestamp: string
    baselineKg: number
    optimizedKg: number
    savedKg: number
  }>
}

function formatDate(ts: string) {
  const d = new Date(ts)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

export default function SavingsChart({ data }: SavingsChartProps) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
        <XAxis
          dataKey="timestamp"
          tickFormatter={formatDate}
          tick={{ fontSize: 11, fill: chartConfig.tickFill }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: chartConfig.tickFill }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: chartConfig.tooltipBg,
            border: `1px solid ${chartConfig.tooltipBorder}`,
            borderRadius: '6px',
            fontSize: '12px',
          }}
          formatter={(value: number, name: string) => [`${value} kg CO2`, name === 'baselineKg' ? 'Baseline' : name === 'optimizedKg' ? 'Optimized' : 'Saved']}
          labelFormatter={(label: string) => `Date: ${formatDate(label)}`}
        />
        <Legend wrapperStyle={{ fontSize: '11px' }} />
        <Bar dataKey="baselineKg" fill={chartConfig.colors.muted} name="Baseline" radius={[2, 2, 0, 0]} opacity={0.5} />
        <Bar dataKey="optimizedKg" fill={chartConfig.colors.primary} name="Optimized" radius={[2, 2, 0, 0]} />
        <Bar dataKey="savedKg" fill={chartConfig.colors.success} name="Saved" radius={[2, 2, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
