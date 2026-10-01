import { useEffect, useState, useCallback } from 'react'
import {
  Shield,
  AlertTriangle,
  Target,
  Activity,
  TrendingUp,
  Eye,
  Lock,
  Bug,
  RefreshCw,
} from 'lucide-react'
import PageHeader from '@/shared/ui/PageHeader'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import Badge, { SeverityBadge, StatusBadge } from '@/shared/ui/Badge'
import MetricCard from '@/shared/ui/MetricCard'
import { api } from '@/shared/utils/api'
import { formatDateTime } from '@/shared/utils/formatters'
import type { SecurityStats, SecurityEventDetail } from '@/shared/types/common'

const POLL_INTERVAL = 15000

const severityColors: Record<string, string> = {
  CRITICAL: 'text-danger',
  HIGH: 'text-orange-400',
  MEDIUM: 'text-warning',
  LOW: 'text-success',
}

export default function SecurityPage() {
  const [stats, setStats] = useState<SecurityStats | null>(null)
  const [events, setEvents] = useState<SecurityEventDetail[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const loadData = useCallback(async () => {
    try {
      const [s, e] = await Promise.all([
        api.getSecurityStats(),
        api.getSecurityEventsList({ page_size: 15 }),
      ])
      setStats(s)
      setEvents(e.items)
      setLastUpdated(new Date())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, POLL_INTERVAL)
    return () => clearInterval(interval)
  }, [loadData])

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
        <PageHeader title="Security Monitoring" subtitle="Real-time cybersecurity event monitoring" />
        <Card>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <AlertTriangle className="w-10 h-10 text-danger mb-3" />
            <p className="text-sm text-danger mb-2">Failed to load security data</p>
            <p className="text-xs text-muted">{error}</p>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Security Monitoring"
        subtitle="Real-time cybersecurity event monitoring and analysis"
        badge={
          <Badge variant="warning" size="sm">
            <span className="inline-block w-1.5 h-1.5 bg-warning rounded-full animate-pulse mr-1" />
            SIMULATED DATA
          </Badge>
        }
        actions={
          <div className="flex items-center gap-3">
            {lastUpdated && (
              <span className="text-[10px] text-muted">
                Updated {lastUpdated.toLocaleTimeString()}
              </span>
            )}
            <button
              onClick={() => { setLoading(true); loadData() }}
              className="flex items-center gap-2 px-3 py-1.5 bg-card border border-border rounded-md text-xs text-muted hover:text-text-primary transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              Refresh
            </button>
          </div>
        }
      />

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Events"
          value={stats?.total_events ?? 0}
          icon={Shield}
          color="primary"
          subtitle="Security events detected"
        />
        <MetricCard
          title="Avg Confidence"
          value={`${((stats?.avg_confidence ?? 0) * 100).toFixed(0)}%`}
          icon={Target}
          color="success"
          subtitle="Detection accuracy"
        />
        <MetricCard
          title="Est. Energy Used"
          value={`${(stats?.total_energy_kwh ?? 0).toFixed(2)} kWh`}
          icon={Activity}
          color="warning"
          subtitle="Security workload"
          compact
        />
        <MetricCard
          title="Est. CO2 Emitted"
          value={`${(stats?.total_co2_kg ?? 0).toFixed(2)} kg`}
          icon={TrendingUp}
          color="danger"
          subtitle="Carbon footprint"
          compact
        />
      </div>

      {/* Severity Breakdown + Recent Events */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Severity Breakdown */}
        <div>
          <Card className="h-full">
            <CardTitle>Severity Breakdown</CardTitle>
            <CardContent>
              <div className="space-y-3 mt-4">
                {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => {
                  const count = stats?.by_severity[sev] ?? 0
                  const total = stats?.total_events ?? 1
                  const pct = (count / total) * 100
                  return (
                    <div key={sev}>
                      <div className="flex items-center justify-between mb-1">
                        <span className={`text-xs font-medium ${severityColors[sev]}`}>{sev}</span>
                        <span className="text-xs text-muted">{count} ({pct.toFixed(0)}%)</span>
                      </div>
                      <div className="w-full bg-border rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all duration-500 ${
                            sev === 'CRITICAL' ? 'bg-danger' :
                            sev === 'HIGH' ? 'bg-orange-400' :
                            sev === 'MEDIUM' ? 'bg-warning' : 'bg-success'
                          }`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Event Type Breakdown */}
              <div className="mt-6 pt-4 border-t border-border">
                <h4 className="text-xs font-semibold text-muted uppercase tracking-wider mb-3">By Attack Type</h4>
                <div className="space-y-2">
                  {Object.entries(stats?.by_type ?? {}).map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {type === 'ddos' && <Activity className="w-3 h-3 text-danger" />}
                        {type === 'brute_force' && <Lock className="w-3 h-3 text-orange-400" />}
                        {type === 'port_scan' && <Eye className="w-3 h-3 text-warning" />}
                        {type === 'sql_injection' && <Bug className="w-3 h-3 text-purple-400" />}
                        {type === 'malware' && <Bug className="w-3 h-3 text-pink-400" />}
                        {type === 'suspicious_login' && <Shield className="w-3 h-3 text-cyan-400" />}
                        <span className="text-xs text-text-primary capitalize">{type.replace('_', ' ')}</span>
                      </div>
                      <span className="text-xs text-muted">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Events Table */}
        <div className="lg:col-span-2">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <CardTitle>Recent Security Events</CardTitle>
              <Badge variant="muted" size="sm">{events.length} shown</Badge>
            </div>
            <CardContent>
              {events.length === 0 ? (
                <div className="text-center py-8">
                  <Shield className="w-8 h-8 text-muted mx-auto mb-2" />
                  <p className="text-sm text-muted">No security events recorded yet</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="px-3 py-2 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Time</th>
                        <th className="px-3 py-2 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Type</th>
                        <th className="px-3 py-2 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Severity</th>
                        <th className="px-3 py-2 text-left text-[10px] font-semibold text-muted uppercase tracking-wider hidden md:table-cell">Source</th>
                        <th className="px-3 py-2 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Status</th>
                        <th className="px-3 py-2 text-left text-[10px] font-semibold text-muted uppercase tracking-wider hidden lg:table-cell">Confidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      {events.map((event) => (
                        <tr key={event.id} className="border-b border-border/30 hover:bg-card-hover transition-colors">
                          <td className="px-3 py-2.5 text-xs text-muted whitespace-nowrap">{formatDateTime(event.timestamp)}</td>
                          <td className="px-3 py-2.5 text-sm text-text-primary font-medium capitalize">{event.event_type.replace('_', ' ')}</td>
                          <td className="px-3 py-2.5"><SeverityBadge severity={event.severity} /></td>
                          <td className="px-3 py-2.5 text-xs text-muted font-mono hidden md:table-cell">{event.source_ip}</td>
                          <td className="px-3 py-2.5"><StatusBadge status={event.status} /></td>
                          <td className="px-3 py-2.5 text-xs text-muted hidden lg:table-cell">{(event.confidence * 100).toFixed(0)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Detection Info Footer */}
      <Card>
        <div className="flex items-center gap-3 p-2">
          <Activity className="w-4 h-4 text-accent-light" />
          <p className="text-xs text-muted">
            Detection methods: Rule-based detection, ML anomaly detection, Signature matching, Behavioral analysis, Heuristic analysis.
            All data is simulated for academic demonstration purposes.
          </p>
        </div>
      </Card>
    </div>
  )
}
