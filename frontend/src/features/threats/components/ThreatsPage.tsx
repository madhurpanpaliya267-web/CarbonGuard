import { useEffect, useState, useCallback } from 'react'
import {
  Target,
  AlertTriangle,
  Activity,
  TrendingUp,
  Eye,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Download,
} from 'lucide-react'
import PageHeader from '@/shared/ui/PageHeader'
import { Card } from '@/shared/ui/Card'
import Badge, { SeverityBadge, StatusBadge } from '@/shared/ui/Badge'
import MetricCard from '@/shared/ui/MetricCard'
import { api } from '@/shared/utils/api'
import { formatDateTime } from '@/shared/utils/formatters'
import { exportThreatsToCSV } from '@/shared/utils/exportData'
import type { ThreatDetail, ThreatStats, ThreatExplanation } from '@/shared/types/common'

export default function ThreatsPage() {
  const [threats, setThreats] = useState<ThreatDetail[]>([])
  const [stats, setStats] = useState<ThreatStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)

  // Filters
  const [severityFilter, setSeverityFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  // Detail view
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [explanation, setExplanation] = useState<ThreatExplanation | null>(null)
  const [loadingExplanation, setLoadingExplanation] = useState(false)

  const loadThreats = useCallback(async () => {
    try {
      const [t, s] = await Promise.all([
        api.getThreats({
          severity: severityFilter || undefined,
          threat_type: typeFilter || undefined,
          status: statusFilter || undefined,
          page_size: 50,
        }),
        api.getThreatStats(),
      ])
      setThreats(t.items)
      setTotal(t.total)
      setStats(s)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [severityFilter, typeFilter, statusFilter])

  useEffect(() => {
    loadThreats()
  }, [loadThreats])

  async function handleStatusUpdate(threatId: number, newStatus: string) {
    try {
      await api.updateThreatStatus(threatId, newStatus)
      setThreats((prev) =>
        prev.map((t) => (t.id === threatId ? { ...t, status: newStatus as ThreatDetail['status'] } : t))
      )
      if (stats) {
        setStats({
          ...stats,
          active_threats: newStatus === 'active' ? stats.active_threats + 1 : stats.active_threats - 1,
          resolved_threats: newStatus === 'resolved' ? stats.resolved_threats + 1 : stats.resolved_threats,
        })
      }
    } catch {
      // silently fail
    }
  }

  async function handleExpand(threatId: number) {
    if (expandedId === threatId) {
      setExpandedId(null)
      setExplanation(null)
      return
    }
    setExpandedId(threatId)
    setLoadingExplanation(true)
    try {
      const exp = await api.getThreatExplanation(threatId)
      setExplanation(exp)
    } catch {
      setExplanation(null)
    } finally {
      setLoadingExplanation(false)
    }
  }

  async function handleExport() {
    try {
      const result = await api.getThreats({
        severity: severityFilter || undefined,
        threat_type: typeFilter || undefined,
        status: statusFilter || undefined,
        page_size: 500,
      })
      exportThreatsToCSV(result.items)
    } catch {
      // silently fail
    }
  }

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
        <PageHeader title="Threats" subtitle="Threat analysis and management" />
        <Card>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <AlertTriangle className="w-10 h-10 text-danger mb-3" />
            <p className="text-sm text-danger mb-2">Failed to load threats</p>
            <p className="text-xs text-muted">{error}</p>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Threats"
        subtitle="Active and resolved threat analysis with AI-powered explanations"
        badge={
          <Badge variant="warning" size="sm">
            <span className="inline-block w-1.5 h-1.5 bg-warning rounded-full animate-pulse mr-1" />
            SIMULATED DATA
          </Badge>
        }
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={handleExport}
              className="flex items-center gap-2 px-3 py-1.5 bg-card border border-border rounded-md text-xs text-muted hover:text-text-primary transition-colors"
            >
              <Download className="w-3 h-3" />
              Export CSV
            </button>
            <button
              onClick={() => { setLoading(true); loadThreats() }}
              className="flex items-center gap-2 px-3 py-1.5 bg-card border border-border rounded-md text-xs text-muted hover:text-text-primary transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              Refresh
            </button>
          </div>
        }
      />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard title="Total Threats" value={stats?.total_threats ?? 0} icon={Target} color="primary" subtitle="All detected" compact />
        <MetricCard title="Active" value={stats?.active_threats ?? 0} icon={AlertTriangle} color="danger" subtitle="Requires action" compact />
        <MetricCard title="Resolved" value={stats?.resolved_threats ?? 0} icon={Activity} color="success" subtitle="Handled" compact />
        <MetricCard title="Avg Risk" value={`${(stats?.avg_risk_score ?? 0).toFixed(0)}`} icon={TrendingUp} color="warning" subtitle="Risk score" compact />
        <MetricCard title="Avg Confidence" value={`${((stats?.avg_confidence ?? 0) * 100).toFixed(0)}%`} icon={Eye} color="purple" subtitle="Detection" compact />
      </div>

      {/* Filters */}
      <Card>
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-xs text-muted font-medium">Filters:</span>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-1.5 bg-background border border-border rounded-md text-xs text-text-primary"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-1.5 bg-background border border-border rounded-md text-xs text-text-primary"
          >
            <option value="">All Types</option>
            <option value="ddos">DDoS</option>
            <option value="brute_force">Brute Force</option>
            <option value="port_scan">Port Scan</option>
            <option value="sql_injection">SQL Injection</option>
            <option value="malware">Malware</option>
            <option value="suspicious_login">Suspicious Login</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 bg-background border border-border rounded-md text-xs text-text-primary"
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
          </select>
          <span className="text-xs text-muted">{total} threats found</span>
        </div>
      </Card>

      {/* Threats Table */}
      <Card>
        {threats.length === 0 ? (
          <div className="text-center py-12">
            <Target className="w-8 h-8 text-muted mx-auto mb-2" />
            <p className="text-sm text-muted">No threats match your filters</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">ID</th>
                  <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Type</th>
                  <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Severity</th>
                  <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider hidden md:table-cell">Risk</th>
                  <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider hidden md:table-cell">Confidence</th>
                  <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider hidden lg:table-cell">Detected</th>
                  <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody>
                {threats.map((threat) => (
                  <>
                    <tr key={threat.id} className="border-b border-border/30 hover:bg-card-hover transition-colors">
                      <td className="px-4 py-3 text-xs text-muted font-mono">#{threat.id}</td>
                      <td className="px-4 py-3 text-sm text-text-primary font-medium capitalize">{threat.threat_type.replace('_', ' ')}</td>
                      <td className="px-4 py-3"><SeverityBadge severity={threat.severity} /></td>
                      <td className="px-4 py-3 hidden md:table-cell">
                        <div className="flex items-center gap-2">
                              <div className="w-16 bg-border rounded-full h-1.5">
                            <div
                              className={`h-1.5 rounded-full ${
                                threat.risk_score > 70 ? 'bg-danger' : threat.risk_score > 40 ? 'bg-warning' : 'bg-accent-light'
                              }`}
                              style={{ width: `${Math.min(threat.risk_score, 100)}%` }}
                            />
                          </div>
                          <span className="text-xs text-muted">{threat.risk_score.toFixed(0)}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-xs text-muted hidden md:table-cell">{(threat.confidence * 100).toFixed(0)}%</td>
                      <td className="px-4 py-3 text-xs text-muted whitespace-nowrap hidden lg:table-cell">{formatDateTime(threat.detected_at)}</td>
                      <td className="px-4 py-3"><StatusBadge status={threat.status} /></td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleExpand(threat.id)}
                            className="p-1 rounded hover:bg-card text-muted hover:text-text-primary transition-colors"
                            title="View details"
                          >
                            {expandedId === threat.id ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                          </button>
                        </div>
                      </td>
                    </tr>
                    {expandedId === threat.id && (
                      <tr key={`${threat.id}-detail`}>
                        <td colSpan={8} className="px-4 py-4 bg-background/50">
                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                            {/* Threat Details */}
                            <div className="space-y-3">
                              <h4 className="text-xs font-semibold text-muted uppercase tracking-wider">Threat Details</h4>
                              <div className="bg-background rounded-md p-3 space-y-2">
                                <div className="flex justify-between">
                                  <span className="text-xs text-muted">UUID</span>
                                  <span className="text-xs text-text-primary font-mono">{threat.threat_uuid}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-xs text-muted">Anomaly Level</span>
                                  <span className="text-xs text-text-primary">{(threat.anomaly_level * 100).toFixed(0)}%</span>
                                </div>
                                {threat.recommended_action && (
                                  <div className="pt-2 border-t border-border">
                                    <p className="text-[10px] text-muted uppercase tracking-wider mb-1">Recommended Action</p>
                                    <p className="text-xs text-text-primary">{threat.recommended_action}</p>
                                  </div>
                                )}
                              </div>
                              <div className="flex gap-2">
                                {threat.status !== 'investigating' && (
                                  <button
                                    onClick={() => handleStatusUpdate(threat.id, 'investigating')}
                                    className="px-3 py-1.5 bg-accent/10 text-accent text-xs rounded-md hover:bg-accent/15 transition-colors"
                                  >
                                    Investigate
                                  </button>
                                )}
                                {threat.status !== 'resolved' && (
                                  <button
                                    onClick={() => handleStatusUpdate(threat.id, 'resolved')}
                                    className="px-3 py-1.5 bg-accent/10 text-accent-light text-xs rounded-lg hover:bg-accent/15 transition-colors"
                                  >
                                    Resolve
                                  </button>
                                )}
                              </div>
                            </div>

                            {/* AI Explanation */}
                            <div className="space-y-3">
                              <h4 className="text-xs font-semibold text-muted uppercase tracking-wider">AI Explanation</h4>
                              {loadingExplanation ? (
                                <div className="flex items-center justify-center py-4">
                                  <div className="w-5 h-5 border-2 border-border border-t-accent rounded-full animate-spin" />
                                </div>
                              ) : explanation ? (
                                <div className="bg-background rounded-md p-3 space-y-2">
                                  <p className="text-xs text-text-primary font-medium">{explanation.prediction}</p>
                                  <p className="text-xs text-muted">{explanation.reasoning}</p>
                                  {explanation.factors.length > 0 && (
                                    <div className="pt-2 border-t border-border space-y-1">
                                      {explanation.factors.map((f, i) => (
                                        <div key={i} className="flex justify-between text-xs">
                                          <span className="text-muted">{f.factor}</span>
                                          <span className="text-text-primary">
                                            {typeof f.value === 'number' ? (f.value as number).toFixed(2) : String(f.value)}
                                            <span className="text-muted ml-1">({(f.weight * 100).toFixed(0)}%)</span>
                                          </span>
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              ) : (
                                <p className="text-xs text-muted">No explanation available</p>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
