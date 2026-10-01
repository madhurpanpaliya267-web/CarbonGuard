import { useEffect, useState } from 'react'
import {
  Battery,
  AlertTriangle,
  Zap,
  Cpu,
  MemoryStick,
  Wifi,
  TrendingUp,
} from 'lucide-react'
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'
import PageHeader from '@/shared/ui/PageHeader'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import Badge from '@/shared/ui/Badge'
import MetricCard from '@/shared/ui/MetricCard'
import { api } from '@/shared/utils/api'
import { chartConfig } from '@/shared/utils/chartConfig'
import type { EnergyOverview } from '@/shared/types/common'

function formatTime(ts: string) {
  const d = new Date(ts)
  return `${d.getHours().toString().padStart(2, '0')}:00`
}

export default function EnergyPage() {
  const [overview, setOverview] = useState<EnergyOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const o = await api.getEnergyOverview()
        setOverview(o)
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
        <PageHeader title="Energy Monitoring" subtitle="Track estimated energy consumption" />
        <Card>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <AlertTriangle className="w-10 h-10 text-danger mb-3" />
            <p className="text-sm text-danger mb-2">Failed to load energy data</p>
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
    power: m.total_power_watts,
    cpu: m.cpu_power_watts,
    memory: m.memory_power_watts,
    energy: m.energy_kwh,
  }))

  return (
    <div className="space-y-6">
      <PageHeader
        title="Energy Monitoring"
        subtitle="Track estimated energy consumption from computational workloads"
        badge={
          <Badge variant="warning" size="sm">
            <span className="inline-block w-1.5 h-1.5 bg-warning rounded-full animate-pulse mr-1" />
            ESTIMATED DATA
          </Badge>
        }
      />

      {/* Current Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="Total Power" value={`${(current?.total_power_watts ?? 0).toFixed(0)} W`} icon={Zap} color="primary" subtitle="Current draw" />
        <MetricCard title="Energy" value={`${(current?.energy_kwh ?? 0).toFixed(4)} kWh`} icon={Battery} color="success" subtitle="Consumption" />
        <MetricCard title="Avg Power" value={`${(summary?.avg_power ?? 0).toFixed(0)} W`} icon={TrendingUp} color="warning" subtitle="Historical average" compact />
        <MetricCard title="Total Energy" value={`${(summary?.total_energy ?? 0).toFixed(4)} kWh`} icon={Battery} color="primary" subtitle="All records" compact />
      </div>

      {/* Power Breakdown */}
      <Card>
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-5 h-5 text-warning" />
          <CardTitle>Power Breakdown</CardTitle>
          <Badge variant="muted" size="sm">ESTIMATED</Badge>
        </div>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 bg-background rounded-md">
              <div className="flex items-center gap-2 mb-2">
                <Cpu className="w-4 h-4 text-accent" />
                <span className="text-xs text-muted">CPU Power</span>
              </div>
              <p className="text-2xl font-bold text-accent">{(current?.cpu_power_watts ?? 0).toFixed(1)} W</p>
              <div className="w-full bg-border rounded-full h-1.5 mt-2">
                <div
                  className="bg-accent rounded-full h-1.5 transition-all"
                  style={{ width: `${current ? (current.cpu_power_watts / Math.max(current.total_power_watts, 1)) * 100 : 0}%` }}
                />
              </div>
            </div>
            <div className="p-4 bg-background rounded-md">
              <div className="flex items-center gap-2 mb-2">
                <MemoryStick className="w-4 h-4 text-warning" />
                <span className="text-xs text-muted">Memory Power</span>
              </div>
              <p className="text-2xl font-bold text-warning">{(current?.memory_power_watts ?? 0).toFixed(1)} W</p>
              <div className="w-full bg-border rounded-full h-1.5 mt-2">
                <div
                  className="bg-warning rounded-full h-1.5 transition-all"
                  style={{ width: `${current ? (current.memory_power_watts / Math.max(current.total_power_watts, 1)) * 100 : 0}%` }}
                />
              </div>
            </div>
            <div className="p-4 bg-background rounded-md">
              <div className="flex items-center gap-2 mb-2">
                <Wifi className="w-4 h-4 text-accent-light" />
                <span className="text-xs text-muted">Network Power</span>
              </div>
              <p className="text-2xl font-bold text-accent-light">{(current?.network_power_watts ?? 0).toFixed(1)} W</p>
              <div className="w-full bg-border rounded-full h-1.5 mt-2">
                <div
                  className="bg-accent-light rounded-full h-1.5 transition-all"
                  style={{ width: `${current ? (current.network_power_watts / Math.max(current.total_power_watts, 1)) * 100 : 0}%` }}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Energy History Chart */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <CardTitle>Energy Consumption History</CardTitle>
          <Badge variant="muted" size="sm">ESTIMATED</Badge>
        </div>
        <CardContent>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <defs>
                  <linearGradient id="gradPower" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={chartConfig.colors.primary} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={chartConfig.colors.primary} stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gradCpu" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={chartConfig.colors.warning} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={chartConfig.colors.warning} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                <XAxis dataKey="timestamp" tickFormatter={formatTime} tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: chartConfig.tooltipBg, border: `1px solid ${chartConfig.tooltipBorder}`, borderRadius: '8px', fontSize: '12px' }}
                  formatter={(value: number, name: string) => [`${value.toFixed(1)} ${name === 'energy' ? 'kWh' : 'W'}`, name === 'power' ? 'Total Power' : name === 'cpu' ? 'CPU' : name === 'memory' ? 'Memory' : 'Energy']}
                  labelFormatter={(label: string) => `Time: ${formatTime(label)}`}
                />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
                <Area type="monotone" dataKey="power" stroke={chartConfig.colors.primary} fill="url(#gradPower)" name="Total Power (W)" strokeWidth={2} />
                <Area type="monotone" dataKey="cpu" stroke={chartConfig.colors.warning} fill="url(#gradCpu)" name="CPU (W)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64 text-sm text-muted">No history data available</div>
          )}
        </CardContent>
      </Card>

      <Card>
        <div className="flex items-center gap-3 p-2">
          <Battery className="w-4 h-4 text-accent" />
          <p className="text-xs text-muted">
            Energy values are estimated from CPU utilization, memory usage, and network activity.
            No physical power meters are used. All data is simulated for academic demonstration.
          </p>
        </div>
      </Card>
    </div>
  )
}
