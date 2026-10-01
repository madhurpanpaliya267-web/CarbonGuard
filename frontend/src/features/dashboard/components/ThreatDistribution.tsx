import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts'
import { chartConfig } from '@/shared/utils/chartConfig'

interface ThreatDistributionProps {
  data: Array<{
    type: string
    count: number
    percentage: number
    color: string
  }>
}

export default function ThreatDistribution({ data }: ThreatDistributionProps) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={95}
          paddingAngle={3}
          dataKey="count"
          nameKey="type"
          strokeWidth={0}
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: chartConfig.tooltipBg,
            border: `1px solid ${chartConfig.tooltipBorder}`,
            borderRadius: '8px',
            fontSize: '12px',
          }}
          formatter={(value: number, name: string) => [`${value} events`, name]}
        />
        <Legend
          wrapperStyle={{ fontSize: '11px' }}
          formatter={(value) => <span style={{ color: chartConfig.tickFill }}>{value}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}
