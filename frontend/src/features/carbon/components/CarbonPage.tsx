import { useEffect, useState } from 'react'
import {
  Leaf,
  AlertTriangle,
  Zap,
  TrendingUp,
  Activity,
  Shield,
  Sun,
} from 'lucide-react'
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'
import PageHeader from '@/shared/ui/PageHeader'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import Badge from '@/shared/ui/Badge'
import MetricCard from '@/shared/ui/MetricCard'
import { api } from '@/shared/utils/api'
import { chartConfig } from '@/shared/utils/chartConfig'
import type { CarbonOverview, CarbonEfficiency } from '@/shared/types/common'

function formatTime(ts: string) {
  const d = new Date(ts)
  return `${d.getHours().toString().padStart(2, '0')}:00`
}

export default function CarbonPage() {
  const [overview, setOverview] = useState<CarbonOverview | null>(null)
  const [efficiency, setEfficiency] = useState<CarbonEfficiency | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [o, e] = await Promise.all([
          api.getCarbonOverview(),
          api.getCarbonEfficiencyData(),
        ])
        setOverview(o)
        setEfficiency(e)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-10 h-10 border-2 border-border border-t-accent rounded-full animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <PageHeader title="Carbon Monitoring" subtitle="Track carbon emissions from security operations" />
        <Card>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <AlertTriangle className="w-10 h-10 text-danger mb-3" />
            <p className="text-sm text-danger mb-2">Failed to load carbon data</p>
            <p className="text-xs text-muted">{error}</p>
          </div>
        </Card>
      </div>
    )
  }

  const current = overview?.current
  const summary = overview?.summary
  const history = overview?.history ?? []

  const chartData = history.map((m) => ({
    timestamp: m.timestamp,
    co2: m.total_co2_kg,
    saved: m.carbon_saved_kg,
    energy: m.total_energy_kwh,
  }))

  return (
    <div className="space-y-6">
      <PageHeader
        title="Carbon Monitoring"
        subtitle="Track and estimate carbon emissions from security operations"
        badge={
          <Badge variant="warning" size="sm">
            <span className="inline-block w-1.5 h-1.5 bg-warning rounded-full animate-pulse mr-1" />
            ESTIMATED DATA
          </Badge>
        }
      />

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="Current CO2" value={`${(current?.total_co2_kg ?? 0).toFixed(2)} kg`} icon={Leaf} color="success" subtitle="Current estimate" />
        <MetricCard title="Total Energy" value={`${(current?.total_energy_kwh ?? 0).toFixed(2)} kWh`} icon={Zap} color="primary" subtitle="Consumption" />
        <MetricCard title="Carbon Saved" value={`${(current?.carbon_saved_kg ?? 0).toFixed(2)} kg`} icon={TrendingUp} color="success" subtitle="Renewable offset" />
        <MetricCard title="Carbon Intensity" value={`${current?.carbon_intensity ?? 475}`} icon={Activity} color="warning" subtitle="gCO2/kWh" compact />
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="Total Energy (History)" value={`${(summary?.total_energy ?? 0).toFixed(2)} kWh`} icon={Zap} color="primary" subtitle="All records" compact />
        <MetricCard title="Total CO2 (History)" value={`${(summary?.total_co2 ?? 0).toFixed(2)} kg`} icon={Leaf} color="danger" subtitle="All records" compact />
        <MetricCard title="Total Saved (History)" value={`${(summary?.total_saved ?? 0).toFixed(2)} kg`} icon={TrendingUp} color="success" subtitle="Renewable offsets" compact />
        <MetricCard title="Avg Efficiency" value={`${(summary?.avg_efficiency ?? 0).toFixed(0)}`} icon={Shield} color="purple" subtitle="Security-carbon ratio" compact />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Carbon Trend */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <CardTitle>Carbon Emissions Trend</CardTitle>
            <Badge variant="muted" size="sm">ESTIMATED</Badge>
          </div>
          <CardContent>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                  <defs>
                    <linearGradient id="gradCo2Carbon" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={chartConfig.colors.danger} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={chartConfig.colors.danger} stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="gradSavedCarbon" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={chartConfig.colors.success} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={chartConfig.colors.success} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                  <XAxis dataKey="timestamp" tickFormatter={formatTime} tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: chartConfig.tooltipBg, border: `1px solid ${chartConfig.tooltipBorder}`, borderRadius: '8px', fontSize: '12px' }}
                    formatter={(value: number, name: string) => [`${value} kg`, name === 'co2' ? 'CO2 Emitted' : 'CO2 Saved']}
                    labelFormatter={(label: string) => `Time: ${formatTime(label)}`}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                  <Area type="monotone" dataKey="co2" stroke={chartConfig.colors.danger} fill="url(#gradCo2Carbon)" name="CO2 Emitted" strokeWidth={2} />
                  <Area type="monotone" dataKey="saved" stroke={chartConfig.colors.success} fill="url(#gradSavedCarbon)" name="CO2 Saved" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-64 text-sm text-muted">No history data available</div>
            )}
          </CardContent>
        </Card>

        {/* Efficiency */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <CardTitle>Security-Carbon Efficiency</CardTitle>
          </div>
          <CardContent>
            {efficiency ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-background rounded-md">
                    <p className="text-[10px] text-muted uppercase tracking-wider mb-1">Threats/kWh</p>
                    <p className="text-xl font-bold text-accent">{efficiency.threats_per_kwh.toFixed(1)}</p>
                  </div>
                  <div className="p-3 bg-background rounded-md">
                    <p className="text-[10px] text-muted uppercase tracking-wider mb-1">CO2/Threat</p>
                    <p className="text-xl font-bold text-warning">{efficiency.co2_per_threat.toFixed(4)} kg</p>
                  </div>
                </div>
                <div className="p-4 bg-background rounded-md">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-muted">Efficiency Score</span>
                    <span className="text-lg font-bold text-accent">{efficiency.efficiency_score}/100</span>
                  </div>
                  <div className="w-full bg-border rounded-full h-2.5">
                    <div
                      className="bg-accent rounded-full h-2.5 transition-all duration-500"
                      style={{ width: `${Math.min(efficiency.efficiency_score, 100)}%` }}
                    />
                  </div>
                  <p className="text-xs text-muted mt-2">
                    Rating: <span className="font-medium text-accent">{efficiency.rating}</span>
                  </p>
                </div>
                <div className="p-3 bg-background rounded-md">
                  <p className="text-[10px] text-muted uppercase tracking-wider mb-1">Renewable Energy</p>
                  <div className="flex items-center gap-2">
                    <Sun className="w-4 h-4 text-warning" />
                    <span className="text-lg font-bold text-accent-light">{current?.renewable_percentage ?? 0}%</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-64 text-sm text-muted">No efficiency data</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Security Carbon Impact */}
      <Card>
        <div className="flex items-center gap-2 mb-4">
          <Shield className="w-5 h-5 text-accent" />
          <CardTitle>Security Workload Carbon Impact</CardTitle>
          <Badge variant="muted" size="sm">ESTIMATED</Badge>
        </div>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 bg-background rounded-md">
              <p className="text-[10px] text-muted uppercase tracking-wider mb-1">Security Energy</p>
              <p className="text-xl font-bold text-accent">{(current?.security_energy_kwh ?? 0).toFixed(2)} kWh</p>
            </div>
            <div className="p-4 bg-background rounded-md">
              <p className="text-[10px] text-muted uppercase tracking-wider mb-1">Security CO2</p>
              <p className="text-xl font-bold text-danger">{(current?.security_co2_kg ?? 0).toFixed(2)} kg</p>
            </div>
            <div className="p-4 bg-background rounded-md">
              <p className="text-[10px] text-muted uppercase tracking-wider mb-1">Active Workloads</p>
              <p className="text-xl font-bold text-purple-400">{current?.workload_count ?? 0}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <div className="flex items-center gap-3 p-2">
          <Leaf className="w-4 h-4 text-accent-light" />
          <p className="text-xs text-muted">
            Formula: Energy (kWh) x Carbon Intensity (gCO2/kWh) = Gross CO2. Gross CO2 x (Renewable% / 100) = Renewable Offset. Gross CO2 - Renewable Offset = Net CO2. All values are estimated/simulated for academic demonstration.
          </p>
        </div>
      </Card>
    </div>
  )
}
