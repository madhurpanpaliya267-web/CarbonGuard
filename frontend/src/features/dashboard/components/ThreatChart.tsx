import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'
import { chartConfig } from '@/shared/utils/chartConfig'

interface ThreatChartProps {
  data: Array<{
    timestamp: string
    count: number
    critical: number
    high: number
    medium: number
    low: number
  }>
}

function formatTime(ts: string) {
  const d = new Date(ts)
  return `${d.getHours().toString().padStart(2, '0')}:00`
}

export default function ThreatChart({ data }: ThreatChartProps) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        <defs>
          <linearGradient id="gradCritical" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={chartConfig.severityColors.CRITICAL} stopOpacity={0.3} />
            <stop offset="95%" stopColor={chartConfig.severityColors.CRITICAL} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gradHigh" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={chartConfig.severityColors.HIGH} stopOpacity={0.3} />
            <stop offset="95%" stopColor={chartConfig.severityColors.HIGH} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gradMedium" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={chartConfig.severityColors.MEDIUM} stopOpacity={0.3} />
            <stop offset="95%" stopColor={chartConfig.severityColors.MEDIUM} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gradLow" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={chartConfig.severityColors.LOW} stopOpacity={0.3} />
            <stop offset="95%" stopColor={chartConfig.severityColors.LOW} stopOpacity={0} />
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
          labelFormatter={(label: string) => `Time: ${formatTime(label)}`}
        />
        <Legend wrapperStyle={{ fontSize: '11px' }} />
        <Area type="monotone" dataKey="critical" stackId="1" stroke={chartConfig.severityColors.CRITICAL} fill="url(#gradCritical)" name="Critical" />
        <Area type="monotone" dataKey="high" stackId="1" stroke={chartConfig.severityColors.HIGH} fill="url(#gradHigh)" name="High" />
        <Area type="monotone" dataKey="medium" stackId="1" stroke={chartConfig.severityColors.MEDIUM} fill="url(#gradMedium)" name="Medium" />
        <Area type="monotone" dataKey="low" stackId="1" stroke={chartConfig.severityColors.LOW} fill="url(#gradLow)" name="Low" />
      </AreaChart>
    </ResponsiveContainer>
  )
}
