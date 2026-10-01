import { useEffect, useState } from 'react'
import {
  Sliders,
  Shield,
  Leaf,
  Zap,
  AlertTriangle,
  Loader2,
  CheckCircle,
  Play,
} from 'lucide-react'
import PageHeader from '@/shared/ui/PageHeader'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import Badge from '@/shared/ui/Badge'
import { api } from '@/shared/utils/api'
import { formatDateTime } from '@/shared/utils/formatters'
import type { Workload, OptimizationResult, OptimizationComparison } from '@/shared/types/common'

const priorityBadge: Record<string, 'danger' | 'warning' | 'success' | 'muted'> = {
  critical: 'danger',
  high: 'warning',
  medium: 'muted',
  low: 'success',
}

export default function OptimizerPage() {
  const [workloads, setWorkloads] = useState<Workload[]>([])
  const [comparison, setComparison] = useState<OptimizationComparison | null>(null)
  const [lastResult, setLastResult] = useState<OptimizationResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [optimizing, setOptimizing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [w, c] = await Promise.all([
          api.getWorkloads(),
          api.getOptimizationComparison(),
        ])
        setWorkloads(w)
        setComparison(c)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  async function handleOptimize() {
    setOptimizing(true)
    setError(null)
    try {
      const res = await api.runOptimization()
      setLastResult(res.comparison)
      const w = await api.getWorkloads()
      setWorkloads(w)
      const c = await api.getOptimizationComparison()
      setComparison(c)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Optimization failed')
    } finally {
      setOptimizing(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-10 h-10 border-2 border-border border-t-accent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Carbon-Aware Workload Optimizer"
        subtitle="Optimize workloads for reduced carbon emissions without delaying security"
        badge={
          <Badge variant="success" size="sm">
            <span className="inline-block w-1.5 h-1.5 bg-success rounded-full animate-pulse mr-1" />
            SECURITY FIRST
          </Badge>
        }
        actions={
          <button
            onClick={handleOptimize}
            disabled={optimizing}
            className="flex items-center gap-2 px-4 py-2 bg-accent/10 text-accent-light text-sm font-medium rounded-md hover:bg-accent/15 transition-colors disabled:opacity-50"
          >
            {optimizing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Optimizing...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Run Optimization
              </>
            )}
          </button>
        }
      />

      {/* Safety Notice */}
      <Card>
        <div className="flex items-center gap-3">
          <Shield className="w-4 h-4 text-accent-light" />
          <p className="text-xs text-muted">
            Critical security tasks are NEVER delayed. Only non-critical workloads may be shifted to lower-carbon periods.
            This is an academic simulation - no external infrastructure is controlled.
          </p>
        </div>
      </Card>

      {error && (
        <Card>
          <div className="flex items-center gap-3 text-danger">
            <AlertTriangle className="w-5 h-5" />
            <p className="text-sm">{error}</p>
          </div>
        </Card>
      )}

      {/* Comparison Cards */}
      {comparison && comparison.before.energy_kwh > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card>
            <div className="flex items-center gap-2 mb-4">
              <Zap className="w-5 h-5 text-danger" />
              <CardTitle>Before Optimization</CardTitle>
            </div>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between p-2 bg-background rounded-md">
                  <span className="text-xs text-muted">Energy</span>
                  <span className="text-sm text-text-primary font-medium">{comparison.before.energy_kwh.toFixed(4)} kWh</span>
                </div>
                <div className="flex justify-between p-2 bg-background rounded-md">
                  <span className="text-xs text-muted">CO2</span>
                  <span className="text-sm text-text-primary font-medium">{comparison.before.co2_kg.toFixed(4)} kg</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <div className="flex items-center gap-2 mb-4">
              <Leaf className="w-5 h-5 text-accent-light" />
              <CardTitle>After Optimization</CardTitle>
            </div>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between p-2 bg-background rounded-md">
                  <span className="text-xs text-muted">Energy</span>
                  <span className="text-sm text-text-primary font-medium">{comparison.after.energy_kwh.toFixed(4)} kWh</span>
                </div>
                <div className="flex justify-between p-2 bg-background rounded-md">
                  <span className="text-xs text-muted">CO2</span>
                  <span className="text-sm text-text-primary font-medium">{comparison.after.co2_kg.toFixed(4)} kg</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <div className="flex items-center gap-2 mb-4">
          <CheckCircle className="w-5 h-5 text-accent-light" />
              <CardTitle>Savings</CardTitle>
            </div>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between p-2 bg-accent/15 rounded-md">
                  <span className="text-xs text-accent-light">Energy Saved</span>
                  <span className="text-sm text-accent-light font-bold">{comparison.comparison.energy_saved.toFixed(4)} kWh</span>
                </div>
                <div className="flex justify-between p-2 bg-accent/15 rounded-md">
                  <span className="text-xs text-accent-light">CO2 Saved</span>
                  <span className="text-sm text-accent-light font-bold">{comparison.comparison.co2_saved.toFixed(4)} kg</span>
                </div>
                <div className="flex justify-between p-2 bg-accent/15 rounded-md">
                  <span className="text-xs text-accent-light">Reduction</span>
                  <span className="text-sm text-accent-light font-bold">{comparison.comparison.reduction_pct.toFixed(1)}%</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Optimization Results Detail */}
      {lastResult && (
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle className="w-5 h-5 text-accent-light" />
            <CardTitle>Optimization Results</CardTitle>
            <Badge variant="success" size="sm">SIMULATION</Badge>
          </div>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-4">
              <div className="p-3 bg-background rounded-md text-center">
                <p className="text-lg font-bold text-accent">{lastResult.workloads_analyzed}</p>
                <p className="text-[10px] text-muted">Analyzed</p>
              </div>
              <div className="p-3 bg-background rounded-md text-center">
                <p className="text-lg font-bold text-accent-light">{lastResult.workloads_shifted}</p>
                <p className="text-[10px] text-muted">Shifted</p>
              </div>
              <div className="p-3 bg-background rounded-md text-center">
                <p className="text-lg font-bold text-muted">{lastResult.workloads_unchanged}</p>
                <p className="text-[10px] text-muted">Unchanged</p>
              </div>
              <div className="p-3 bg-background rounded-md text-center">
                <p className="text-lg font-bold text-accent-light">{lastResult.critical_protected}</p>
                <p className="text-[10px] text-muted">Critical Protected</p>
              </div>
              <div className="p-3 bg-background rounded-md text-center">
                <p className="text-lg font-bold text-accent-light">{lastResult.reduction_percentage.toFixed(1)}%</p>
                <p className="text-[10px] text-muted">Reduction</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Workloads Table */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <CardTitle>Workloads</CardTitle>
          <Badge variant="muted" size="sm">{workloads.length} workloads</Badge>
        </div>
        <CardContent>
          {workloads.length === 0 ? (
            <div className="text-center py-8">
              <Sliders className="w-8 h-8 text-muted mx-auto mb-2" />
              <p className="text-sm text-muted">No workloads found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Name</th>
                    <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Type</th>
                    <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Priority</th>
                    <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider hidden md:table-cell">Energy</th>
                    <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider hidden md:table-cell">CO2</th>
                    <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Critical</th>
                    <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Status</th>
                    <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider hidden lg:table-cell">Scheduled</th>
                  </tr>
                </thead>
                <tbody>
                  {workloads.map((w) => (
                    <tr key={w.id} className="border-b border-border/30 hover:bg-card-hover transition-colors">
                      <td className="px-4 py-3 text-sm text-text-primary font-medium">{w.name}</td>
                      <td className="px-4 py-3 text-xs text-muted capitalize">{w.workload_type.replace('_', ' ')}</td>
                      <td className="px-4 py-3">
                        <Badge variant={priorityBadge[w.priority]}>{w.priority}</Badge>
                      </td>
                      <td className="px-4 py-3 text-xs text-muted hidden md:table-cell">{w.estimated_energy_kwh.toFixed(4)} kWh</td>
                      <td className="px-4 py-3 text-xs text-muted hidden md:table-cell">{w.estimated_co2_kg.toFixed(4)} kg</td>
                      <td className="px-4 py-3">
                        {w.is_security_critical ? (
                          <Shield className="w-3.5 h-3.5 text-accent-light" />
                        ) : (
                          <span className="text-xs text-muted">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={w.status === 'delayed' ? 'warning' : w.status === 'completed' ? 'success' : 'muted'}>{w.status}</Badge>
                      </td>
                      <td className="px-4 py-3 text-xs text-muted hidden lg:table-cell whitespace-nowrap">
                        {w.scheduled_time ? formatDateTime(w.scheduled_time) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
