import { useEffect, useState } from 'react'
import {
  Sun,
  Wind,
  AlertTriangle,
  Leaf,
  Zap,
  Clock,
} from 'lucide-react'
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, LineChart, Line } from 'recharts'
import PageHeader from '@/shared/ui/PageHeader'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import Badge from '@/shared/ui/Badge'
import MetricCard from '@/shared/ui/MetricCard'
import { api } from '@/shared/utils/api'
import { chartConfig } from '@/shared/utils/chartConfig'
import type { RenewableStatus } from '@/shared/types/common'

function formatTime(ts: string) {
  const d = new Date(ts)
  return `${d.getHours().toString().padStart(2, '0')}:00`
}

export default function RenewableEnergyPage() {
  const [status, setStatus] = useState<RenewableStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const s = await api.getRenewableStatus()
        setStatus(s)
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
        <PageHeader title="Renewable Energy" subtitle="Track renewable energy availability" />
        <Card>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <AlertTriangle className="w-10 h-10 text-danger mb-3" />
            <p className="text-sm text-danger mb-2">Failed to load renewable data</p>
            <p className="text-xs text-muted">{error}</p>
          </div>
        </Card>
      </div>
    )
  }

  const forecast = status?.forecast ?? []

  // Find best hours for scheduling
  const bestHours = [...forecast]
    .sort((a, b) => b.renewable_pct - a.renewable_pct)
    .slice(0, 3)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Renewable Energy Monitor"
        subtitle="Track renewable energy availability and grid carbon intensity"
        badge={
          <Badge variant="warning" size="sm">
            <span className="inline-block w-1.5 h-1.5 bg-warning rounded-full animate-pulse mr-1" />
            SIMULATED DATA
          </Badge>
        }
      />

      {/* Current Status */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="Renewable Energy" value={`${(status?.renewable_percentage ?? 0).toFixed(1)}%`} icon={Leaf} color="success" subtitle="Current mix" />
        <MetricCard title="Solar Availability" value={`${(status?.solar_availability ?? 0).toFixed(1)}%`} icon={Sun} color="warning" subtitle="Solar input" />
        <MetricCard title="Wind Availability" value={`${(status?.wind_availability ?? 0).toFixed(1)}%`} icon={Wind} color="primary" subtitle="Wind input" />
        <MetricCard title="Grid Carbon Intensity" value={`${(status?.grid_carbon_intensity ?? 475).toFixed(0)}`} icon={Zap} color="danger" subtitle="gCO2/kWh" compact />
      </div>

      {/* Best Scheduling Windows */}
      <Card>
        <div className="flex items-center gap-2 mb-4">
          <Clock className="w-5 h-5 text-accent-light" />
          <CardTitle>Recommended Scheduling Windows</CardTitle>
          <Badge variant="success" size="sm">LOWEST CARBON</Badge>
        </div>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {bestHours.map((h, i) => (
              <div key={i} className="p-3 bg-background rounded-md border border-accent/20">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-6 h-6 rounded-full bg-accent/15 flex items-center justify-center">
                    <span className="text-[10px] text-accent-light font-bold">{i + 1}</span>
                  </div>
                  <span className="text-sm text-text-primary font-medium">{formatTime(h.timestamp)}</span>
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <span className="text-xs text-muted">Renewable</span>
                    <span className="text-xs text-accent-light font-medium">{h.renewable_pct.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-muted">Carbon Intensity</span>
                    <span className="text-xs text-text-primary">{h.carbon_intensity.toFixed(0)} gCO2/kWh</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Forecast Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Renewable % Forecast */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <CardTitle>24-Hour Renewable Forecast</CardTitle>
            <Badge variant="muted" size="sm">SIMULATED</Badge>
          </div>
          <CardContent>
            {forecast.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={forecast} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                  <defs>
                    <linearGradient id="gradRenewable" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={chartConfig.colors.success} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={chartConfig.colors.success} stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="gradSolar" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={chartConfig.colors.warning} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={chartConfig.colors.warning} stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="gradWind" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={chartConfig.colors.primary} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={chartConfig.colors.primary} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                  <XAxis dataKey="timestamp" tickFormatter={formatTime} tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: chartConfig.tooltipBg, border: `1px solid ${chartConfig.tooltipBorder}`, borderRadius: '8px', fontSize: '12px' }}
                    formatter={(value: number, name: string) => [`${value.toFixed(1)}%`, name === 'renewable_pct' ? 'Renewable' : name === 'solar' ? 'Solar' : 'Wind']}
                    labelFormatter={(label: string) => `Time: ${formatTime(label)}`}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                  <Area type="monotone" dataKey="solar" stroke={chartConfig.colors.warning} fill="url(#gradSolar)" name="Solar" strokeWidth={2} />
                  <Area type="monotone" dataKey="wind" stroke={chartConfig.colors.primary} fill="url(#gradWind)" name="Wind" strokeWidth={2} />
                  <Area type="monotone" dataKey="renewable_pct" stroke={chartConfig.colors.success} fill="url(#gradRenewable)" name="Total Renewable" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-64 text-sm text-muted">No forecast data</div>
            )}
          </CardContent>
        </Card>

        {/* Carbon Intensity Forecast */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <CardTitle>Carbon Intensity Forecast</CardTitle>
            <Badge variant="muted" size="sm">SIMULATED</Badge>
          </div>
          <CardContent>
            {forecast.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={forecast} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                  <XAxis dataKey="timestamp" tickFormatter={formatTime} tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: chartConfig.tooltipBg, border: `1px solid ${chartConfig.tooltipBorder}`, borderRadius: '8px', fontSize: '12px' }}
                    formatter={(value: number) => [`${value.toFixed(0)} gCO2/kWh`, 'Carbon Intensity']}
                    labelFormatter={(label: string) => `Time: ${formatTime(label)}`}
                  />
                  <Line type="monotone" dataKey="carbon_intensity" stroke={chartConfig.colors.danger} strokeWidth={2} dot={false} name="Carbon Intensity" />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-64 text-sm text-muted">No forecast data</div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <div className="flex items-center gap-3 p-2">
          <Sun className="w-4 h-4 text-warning" />
          <p className="text-xs text-muted">
            Renewable energy data is simulated based on typical solar and wind availability patterns.
            Solar peaks during midday (hours 10-14). Wind varies throughout the day.
            Carbon intensity decreases as renewable availability increases.
            All values are simulated for academic demonstration.
          </p>
        </div>
      </Card>
    </div>
  )
}
