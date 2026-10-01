import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'
import { chartConfig } from '@/shared/utils/chartConfig'

interface CarbonChartProps {
  data: Array<{
    timestamp: string
    co2Kg: number
    energyKwh: number
  }>
}

function formatTime(ts: string) {
  const d = new Date(ts)
  return `${d.getHours().toString().padStart(2, '0')}:00`
}

export default function CarbonChart({ data }: CarbonChartProps) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        <defs>
          <linearGradient id="gradCo2" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={chartConfig.colors.danger} stopOpacity={0.3} />
            <stop offset="95%" stopColor={chartConfig.colors.danger} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gradEnergy" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={chartConfig.colors.primary} stopOpacity={0.3} />
            <stop offset="95%" stopColor={chartConfig.colors.primary} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
        <XAxis
          dataKey="timestamp"
          tickFormatter={formatTime}
          tick={{ fontSize: 11, fill: chartConfig.tickFill }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          yAxisId="co2"
          tick={{ fontSize: 11, fill: chartConfig.tickFill }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          yAxisId="energy"
          orientation="right"
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
          formatter={(value: number, name: string) => [
            name === 'co2Kg' ? `${value} kg` : `${value} kWh`,
            name === 'co2Kg' ? 'CO2' : 'Energy',
          ]}
          labelFormatter={(label: string) => `Time: ${formatTime(label)}`}
        />
        <Legend wrapperStyle={{ fontSize: '11px' }} />
        <Area yAxisId="co2" type="monotone" dataKey="co2Kg" stroke={chartConfig.colors.danger} fill="url(#gradCo2)" name="CO2 (kg)" strokeWidth={2} />
        <Area yAxisId="energy" type="monotone" dataKey="energyKwh" stroke={chartConfig.colors.primary} fill="url(#gradEnergy)" name="Energy (kWh)" strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  )
}
