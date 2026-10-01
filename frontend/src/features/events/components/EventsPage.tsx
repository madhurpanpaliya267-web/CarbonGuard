import { useEffect, useState, useCallback } from 'react'
import {
  ScrollText,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Download,
} from 'lucide-react'
import PageHeader from '@/shared/ui/PageHeader'
import { Card } from '@/shared/ui/Card'
import Badge, { SeverityBadge, StatusBadge } from '@/shared/ui/Badge'
import { api } from '@/shared/utils/api'
import { formatDateTime } from '@/shared/utils/formatters'
import { exportEventsToCSV } from '@/shared/utils/exportData'
import type { SecurityEventDetail } from '@/shared/types/common'

export default function EventsPage() {
  const [events, setEvents] = useState<SecurityEventDetail[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(15)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [severityFilter, setSeverityFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const loadEvents = useCallback(async () => {
    setLoading(true)
    try {
      const result = await api.getEventsList({
        severity: severityFilter || undefined,
        event_type: typeFilter || undefined,
        status: statusFilter || undefined,
        page,
        page_size: pageSize,
      })
      setEvents(result.items)
      setTotal(result.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [severityFilter, typeFilter, statusFilter, page, pageSize])

  async function handleExport() {
    try {
      const result = await api.getEventsList({
        severity: severityFilter || undefined,
        event_type: typeFilter || undefined,
        status: statusFilter || undefined,
        page_size: 500,
      })
      exportEventsToCSV(result.items)
    } catch {
      // silently fail
    }
  }

  useEffect(() => {
    loadEvents()
  }, [loadEvents])

  const totalPages = Math.ceil(total / pageSize)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Security Event Logs"
        subtitle="Searchable event log with filtering by severity, type, and status"
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
              onClick={() => { setLoading(true); loadEvents() }}
              className="flex items-center gap-2 px-3 py-1.5 bg-card border border-border rounded-md text-xs text-muted hover:text-text-primary transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              Refresh
            </button>
          </div>
        }
      />

      {error && (
        <Card>
          <div className="flex items-center gap-3 text-danger">
            <AlertTriangle className="w-5 h-5" />
            <p className="text-sm">{error}</p>
          </div>
        </Card>
      )}

      {/* Filters */}
      <Card>
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-xs text-muted font-medium">Filters:</span>
          <select
            value={severityFilter}
            onChange={(e) => { setSeverityFilter(e.target.value); setPage(1) }}
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
            onChange={(e) => { setTypeFilter(e.target.value); setPage(1) }}
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
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
            className="px-3 py-1.5 bg-background border border-border rounded-md text-xs text-text-primary"
          >
            <option value="">All Statuses</option>
            <option value="detected">Detected</option>
            <option value="investigating">Investigating</option>
            <option value="mitigated">Mitigated</option>
            <option value="blocked">Blocked</option>
            <option value="false_positive">False Positive</option>
          </select>
          <span className="text-xs text-muted">{total} events found</span>
        </div>
      </Card>

      {/* Events Table */}
      <Card>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-2 border-border border-t-accent rounded-full animate-spin" />
          </div>
        ) : events.length === 0 ? (
          <div className="text-center py-12">
            <ScrollText className="w-8 h-8 text-muted mx-auto mb-2" />
            <p className="text-sm text-muted">No events match your filters</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">ID</th>
                    <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Type</th>
                    <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Severity</th>
                    <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Timestamp</th>
                    <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider hidden md:table-cell">Source</th>
                    <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider hidden md:table-cell">Target</th>
                    <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Status</th>
                    <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider hidden lg:table-cell">Confidence</th>
                    <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider hidden lg:table-cell">Energy</th>
                    <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider hidden lg:table-cell">CO2</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((event) => (
                    <tr key={event.id} className="border-b border-border/30 hover:bg-card-hover transition-colors">
                      <td className="px-4 py-3 text-xs text-muted font-mono">#{event.id}</td>
                      <td className="px-4 py-3 text-sm text-text-primary font-medium capitalize">{event.event_type.replace('_', ' ')}</td>
                      <td className="px-4 py-3"><SeverityBadge severity={event.severity} /></td>
                      <td className="px-4 py-3 text-xs text-muted whitespace-nowrap">{formatDateTime(event.timestamp)}</td>
                      <td className="px-4 py-3 text-xs text-muted font-mono hidden md:table-cell">{event.source_ip}</td>
                      <td className="px-4 py-3 text-xs text-muted font-mono hidden md:table-cell">{event.target_ip}</td>
                      <td className="px-4 py-3"><StatusBadge status={event.status} /></td>
                      <td className="px-4 py-3 text-xs text-muted hidden lg:table-cell">{(event.confidence * 100).toFixed(0)}%</td>
                      <td className="px-4 py-3 text-xs text-muted hidden lg:table-cell">{(event.estimated_energy_kwh ?? 0).toFixed(4)} kWh</td>
                      <td className="px-4 py-3 text-xs text-muted hidden lg:table-cell">{(event.estimated_co2_kg ?? 0).toFixed(4)} kg</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-border">
                <span className="text-xs text-muted">
                  Page {page} of {totalPages} ({total} total)
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                    className="p-1.5 rounded-md bg-card border border-border text-muted hover:text-text-primary disabled:opacity-30 transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setPage(Math.min(totalPages, page + 1))}
                    disabled={page === totalPages}
                    className="p-1.5 rounded-md bg-card border border-border text-muted hover:text-text-primary disabled:opacity-30 transition-colors"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </Card>

      <Card>
        <div className="flex items-center gap-3 p-2">
          <ScrollText className="w-4 h-4 text-accent" />
          <p className="text-xs text-muted">
            All events are simulated for academic demonstration. No real network traffic or attacks are monitored.
            Detection methods include rule-based detection, ML anomaly detection, signature matching, behavioral analysis, and heuristic analysis.
          </p>
        </div>
      </Card>
    </div>
  )
}
