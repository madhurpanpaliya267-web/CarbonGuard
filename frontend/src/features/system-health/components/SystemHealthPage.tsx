import { useEffect, useState } from 'react'
import {
  HeartPulse,
  AlertTriangle,
  Cpu,
  MemoryStick,
  Database,
  Globe,
  Shield,
  Leaf,
  Brain,
  CheckCircle,
  XCircle,
  Activity,
} from 'lucide-react'
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'
import PageHeader from '@/shared/ui/PageHeader'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import Badge from '@/shared/ui/Badge'
import MetricCard from '@/shared/ui/MetricCard'
import { api } from '@/shared/utils/api'
import { chartConfig } from '@/shared/utils/chartConfig'
import { formatDateTime } from '@/shared/utils/formatters'
import type { SystemMetric } from '@/shared/types/common'

function formatTime(ts: string) {
  const d = new Date(ts)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

const statusConfig: Record<string, { icon: typeof CheckCircle; color: string; bg: string; label: string }> = {
  online: { icon: CheckCircle, color: 'text-accent-light', bg: 'bg-accent/10', label: 'Operational' },
  degraded: { icon: AlertTriangle, color: 'text-warning', bg: 'bg-warning/10', label: 'Degraded' },
  offline: { icon: XCircle, color: 'text-danger', bg: 'bg-danger/10', label: 'Offline' },
}

export default function SystemHealthPage() {
  const [current, setCurrent] = useState<SystemMetric | null>(null)
  const [history, setHistory] = useState<SystemMetric[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [c, h] = await Promise.all([
          api.getSystemHealthData(),
          api.getSystemHealthHistory(),
        ])
        setCurrent(c)
        setHistory(h)
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
        <PageHeader title="System Health" subtitle="Monitor all Carbon Guard components" />
        <Card>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <AlertTriangle className="w-10 h-10 text-danger mb-3" />
            <p className="text-sm text-danger mb-2">Failed to load system health</p>
            <p className="text-xs text-muted">{error}</p>
          </div>
        </Card>
      </div>
    )
  }

  const services = [
    { name: 'Security Engine', status: current?.security_engine_status ?? 'online', icon: Shield },
    { name: 'Carbon Engine', status: current?.carbon_engine_status ?? 'online', icon: Leaf },
    { name: 'AI Engine', status: current?.ai_engine_status ?? 'online', icon: Brain },
    { name: 'Database', status: current?.database_status ?? 'online', icon: Database },
    { name: 'API Server', status: current?.api_status ?? 'online', icon: Globe },
    { name: 'Frontend', status: 'online', icon: Activity },
  ]

  const onlineCount = services.filter((s) => s.status === 'online').length

  const historyChartData = history.map((m) => ({
    timestamp: m.timestamp,
    cpu: m.cpu_utilization,
    memory: m.memory_utilization,
  }))

  return (
    <div className="space-y-6">
      <PageHeader
        title="System Health"
        subtitle="Monitor all Carbon Guard platform components and their status"
        badge={
          <Badge variant={onlineCount === services.length ? 'success' : 'warning'} size="sm">
            {onlineCount === services.length ? 'ALL SYSTEMS OPERATIONAL' : `${onlineCount}/${services.length} ONLINE`}
          </Badge>
        }
      />

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="CPU Utilization" value={`${(current?.cpu_utilization ?? 0).toFixed(1)}%`} icon={Cpu} color="primary" subtitle="Current usage" />
        <MetricCard title="Memory Utilization" value={`${(current?.memory_utilization ?? 0).toFixed(1)}%`} icon={MemoryStick} color="warning" subtitle="Current usage" />
        <MetricCard title="Active Workloads" value={current?.active_workloads ?? 0} icon={Activity} color="success" subtitle="Running tasks" compact />
        <MetricCard title="Simulated" value={current?.simulated ? 'Yes' : 'No'} icon={HeartPulse} color="purple" subtitle="Data source" compact />
      </div>

      {/* Service Status Grid */}
      <Card>
        <div className="flex items-center gap-2 mb-4">
          <HeartPulse className="w-5 h-5 text-accent-light" />
          <CardTitle>Service Status</CardTitle>
        </div>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {services.map((service) => {
              const config = statusConfig[service.status] || statusConfig.offline
              return (
                <div key={service.name} className="flex items-center justify-between p-3 bg-background rounded-md">
                  <div className="flex items-center gap-3">
                    <div className={`${config.bg} rounded-md p-2`}>
                      <service.icon className={`w-4 h-4 ${config.color}`} />
                    </div>
                    <div>
                      <p className="text-sm text-text-primary font-medium">{service.name}</p>
                      <p className="text-[10px] text-muted">Last checked: {current?.timestamp ? formatDateTime(current.timestamp) : 'Now'}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className={`w-2 h-2 rounded-full ${service.status === 'online' ? 'bg-success' : service.status === 'degraded' ? 'bg-warning' : 'bg-danger'}`} />
                    <span className={`text-xs font-medium ${config.color}`}>{config.label}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Utilization History Chart */}
      {historyChartData.length > 0 && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <CardTitle>Utilization History</CardTitle>
            <Badge variant="muted" size="sm">{history.length} data points</Badge>
          </div>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={historyChartData}>
                <defs>
                  <linearGradient id="gradCpuHistory" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={chartConfig.colors.primary} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={chartConfig.colors.primary} stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gradMemHistory" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={chartConfig.colors.warning} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={chartConfig.colors.warning} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                <XAxis dataKey="timestamp" tickFormatter={formatTime} tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: chartConfig.tooltipBg, border: `1px solid ${chartConfig.tooltipBorder}`, borderRadius: '8px', fontSize: '12px' }}
                  formatter={(value: number, name: string) => [`${value.toFixed(1)}%`, name === 'cpu' ? 'CPU' : 'Memory']}
                  labelFormatter={(label: string) => `Time: ${formatTime(label)}`}
                />
                <Area type="monotone" dataKey="cpu" stroke={chartConfig.colors.primary} fill="url(#gradCpuHistory)" name="CPU" strokeWidth={2} />
                <Area type="monotone" dataKey="memory" stroke={chartConfig.colors.warning} fill="url(#gradMemHistory)" name="Memory" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      <Card>
        <div className="flex items-center gap-3 p-2">
          <HeartPulse className="w-4 h-4 text-success" />
          <p className="text-xs text-muted">
            System health metrics are simulated for academic demonstration.
            Service statuses reflect backend engine availability.
            Frontend status is always "online" when this page is viewable.
          </p>
        </div>
      </Card>
    </div>
  )
}
