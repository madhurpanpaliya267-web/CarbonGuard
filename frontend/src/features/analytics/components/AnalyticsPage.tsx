import { useEffect, useState } from 'react'
import {
  BarChart3,
  AlertTriangle,
  Shield,
  Leaf,
  Zap,
  Sliders,
} from 'lucide-react'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'
import PageHeader from '@/shared/ui/PageHeader'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import Badge from '@/shared/ui/Badge'
import { api } from '@/shared/utils/api'
import { chartConfig } from '@/shared/utils/chartConfig'
import type {
  SecurityAnalytics,
  CarbonAnalytics,
  EnergyAnalytics,
  OptimizationAnalytics,
} from '@/shared/types/common'

type AnalyticsTab = 'security' | 'carbon' | 'energy' | 'optimization'

const tabs: { id: AnalyticsTab; label: string; icon: typeof Shield }[] = [
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'carbon', label: 'Carbon', icon: Leaf },
  { id: 'energy', label: 'Energy', icon: Zap },
  { id: 'optimization', label: 'Optimization', icon: Sliders },
]

const PIE_COLORS = ['#ef4444', '#f97316', '#f59e0b', '#a855f7', '#ec4899', '#06b6d4']

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<AnalyticsTab>('security')
  const [period, setPeriod] = useState('7d')
  const [security, setSecurity] = useState<SecurityAnalytics | null>(null)
  const [carbon, setCarbon] = useState<CarbonAnalytics | null>(null)
  const [energy, setEnergy] = useState<EnergyAnalytics | null>(null)
  const [optimization, setOptimization] = useState<OptimizationAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const [s, c, e, o] = await Promise.all([
          api.getSecurityAnalytics(period),
          api.getCarbonAnalytics(period),
          api.getEnergyAnalytics(period),
          api.getOptimizationAnalytics(),
        ])
        setSecurity(s)
        setCarbon(c)
        setEnergy(e)
        setOptimization(o)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [period])

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
        <PageHeader title="Analytics" subtitle="Security, carbon, energy, and optimization analytics" />
        <Card>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <AlertTriangle className="w-10 h-10 text-danger mb-3" />
            <p className="text-sm text-danger mb-2">Failed to load analytics</p>
            <p className="text-xs text-muted">{error}</p>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Analytics"
        subtitle="Security, carbon, energy, and optimization analytics with trend analysis"
        badge={
          <Badge variant="warning" size="sm">
            <span className="inline-block w-1.5 h-1.5 bg-warning rounded-full animate-pulse mr-1" />
            SIMULATED DATA
          </Badge>
        }
      />

      {/* Period + Tab Selection */}
      <Card>
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted font-medium">Period:</span>
            {['24h', '7d', '30d'].map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                  period === p
                    ? 'bg-accent/15 text-accent'
                    : 'bg-card text-muted hover:text-text-primary'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-1 bg-card border border-border rounded-md p-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-md transition-colors ${
                  activeTab === tab.id
                    ? 'bg-accent/10 text-accent'
                    : 'text-muted hover:text-text-primary'
                }`}
              >
                <tab.icon className="w-3 h-3" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Security Analytics */}
      {activeTab === 'security' && security && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardTitle>Attacks Over Time</CardTitle>
              <CardContent>
                {security.attacks_over_time.length > 0 ? (
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={security.attacks_over_time}>
                      <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                      <XAxis dataKey="date" tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                      <Tooltip
                        contentStyle={{ backgroundColor: chartConfig.tooltipBg, border: `1px solid ${chartConfig.tooltipBorder}`, borderRadius: '8px', fontSize: '12px' }}
                      />
                      <Bar dataKey="count" fill={chartConfig.colors.primary} radius={[4, 4, 0, 0]} name="Attacks" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-64 text-sm text-muted">No data</div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardTitle>Attack Categories</CardTitle>
              <CardContent>
                {security.categories.length > 0 ? (
                  <ResponsiveContainer width="100%" height={280}>
                    <PieChart>
                      <Pie
                        data={security.categories}
                        cx="50%"
                        cy="50%"
                        outerRadius={100}
                        dataKey="count"
                        nameKey="type"
                        label={({ type, percent }) => `${type} ${(percent * 100).toFixed(0)}%`}
                      >
                        {security.categories.map((_, i) => (
                          <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ backgroundColor: chartConfig.tooltipBg, border: `1px solid ${chartConfig.tooltipBorder}`, borderRadius: '8px', fontSize: '12px' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-64 text-sm text-muted">No data</div>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardTitle>Severity Distribution</CardTitle>
              <CardContent>
                <div className="space-y-3">
                  {security.severity_dist.map((s) => {
                    const total = security.severity_dist.reduce((a, b) => a + b.count, 0)
                    const pct = (s.count / Math.max(total, 1)) * 100
                    const colors: Record<string, string> = { CRITICAL: 'bg-danger', HIGH: 'bg-orange-400', MEDIUM: 'bg-warning', LOW: 'bg-success' }
                    return (
                      <div key={s.level}>
                        <div className="flex justify-between mb-1">
                          <span className="text-xs text-text-primary">{s.level}</span>
                          <span className="text-xs text-muted">{s.count}</span>
                        </div>
                        <div className="w-full bg-border rounded-full h-2">
                          <div className={`${colors[s.level] || 'bg-muted'} rounded-full h-2`} style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardTitle>Top Source IPs</CardTitle>
              <CardContent>
                <div className="space-y-2">
                  {security.top_sources.map((s) => (
                    <div key={s.ip} className="flex items-center justify-between p-2 bg-background rounded-md">
                      <span className="text-xs text-text-primary font-mono">{s.ip}</span>
                      <span className="text-xs text-muted">{s.count} events</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Carbon Analytics */}
      {activeTab === 'carbon' && carbon && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardTitle>Carbon Emissions Trend</CardTitle>
              <CardContent>
                {carbon.emissions_over_time.length > 0 ? (
                  <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={carbon.emissions_over_time}>
                      <defs>
                        <linearGradient id="gradAnalyticsCo2" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={chartConfig.colors.danger} stopOpacity={0.3} />
                          <stop offset="95%" stopColor={chartConfig.colors.danger} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                      <XAxis dataKey="date" tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                      <Tooltip
                        contentStyle={{ backgroundColor: chartConfig.tooltipBg, border: `1px solid ${chartConfig.tooltipBorder}`, borderRadius: '8px', fontSize: '12px' }}
                        formatter={(value: number) => [`${value} kg`, 'CO2']}
                      />
                      <Area type="monotone" dataKey="co2_kg" stroke={chartConfig.colors.danger} fill="url(#gradAnalyticsCo2)" name="CO2 (kg)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-64 text-sm text-muted">No data</div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardTitle>Carbon Savings</CardTitle>
              <CardContent>
                {carbon.savings_over_time.length > 0 ? (
                  <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={carbon.savings_over_time}>
                      <defs>
                        <linearGradient id="gradAnalyticsSaved" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={chartConfig.colors.success} stopOpacity={0.3} />
                          <stop offset="95%" stopColor={chartConfig.colors.success} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                      <XAxis dataKey="date" tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                      <Tooltip
                        contentStyle={{ backgroundColor: chartConfig.tooltipBg, border: `1px solid ${chartConfig.tooltipBorder}`, borderRadius: '8px', fontSize: '12px' }}
                        formatter={(value: number, name: string) => [`${value} kg`, name === 'saved_kg' ? 'Saved' : 'Cumulative']}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px' }} />
                      <Area type="monotone" dataKey="saved_kg" stroke={chartConfig.colors.success} fill="url(#gradAnalyticsSaved)" name="Saved" strokeWidth={2} />
                      <Area type="monotone" dataKey="cumulative_kg" stroke={chartConfig.colors.primary} fill="none" name="Cumulative" strokeWidth={2} strokeDasharray="5 5" />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-64 text-sm text-muted">No data</div>
                )}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardTitle>Efficiency Trend</CardTitle>
            <CardContent>
              {carbon.efficiency_trend.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={carbon.efficiency_trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: chartConfig.tooltipBg, border: `1px solid ${chartConfig.tooltipBorder}`, borderRadius: '8px', fontSize: '12px' }}
                      formatter={(value: number) => [`${value}`, 'Efficiency']}
                    />
                    <Line type="monotone" dataKey="efficiency" stroke={chartConfig.colors.success} strokeWidth={2} dot={false} name="Efficiency Score" />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-64 text-sm text-muted">No data</div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Energy Analytics */}
      {activeTab === 'energy' && energy && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardTitle>Energy Usage Trend</CardTitle>
              <CardContent>
                {energy.usage_over_time.length > 0 ? (
                  <ResponsiveContainer width="100%" height={280}>
                    <AreaChart data={energy.usage_over_time}>
                      <defs>
                        <linearGradient id="gradAnalyticsEnergy" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={chartConfig.colors.primary} stopOpacity={0.3} />
                          <stop offset="95%" stopColor={chartConfig.colors.primary} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                      <XAxis dataKey="date" tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                      <Tooltip
                        contentStyle={{ backgroundColor: chartConfig.tooltipBg, border: `1px solid ${chartConfig.tooltipBorder}`, borderRadius: '8px', fontSize: '12px' }}
                        formatter={(value: number) => [`${value} kWh`, 'Energy']}
                      />
                      <Area type="monotone" dataKey="energy_kwh" stroke={chartConfig.colors.primary} fill="url(#gradAnalyticsEnergy)" name="Energy (kWh)" strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-64 text-sm text-muted">No data</div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardTitle>Energy by Type</CardTitle>
              <CardContent>
                {energy.by_type.length > 0 ? (
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={energy.by_type} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                      <XAxis type="number" tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                      <YAxis type="category" dataKey="type" tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} width={120} />
                      <Tooltip
                        contentStyle={{ backgroundColor: chartConfig.tooltipBg, border: `1px solid ${chartConfig.tooltipBorder}`, borderRadius: '8px', fontSize: '12px' }}
                        formatter={(value: number) => [`${value} kWh`, 'Energy']}
                      />
                      <Bar dataKey="energy_kwh" fill={chartConfig.colors.primary} radius={[0, 4, 4, 0]} name="Energy (kWh)" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-64 text-sm text-muted">No data</div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Optimization Analytics */}
      {activeTab === 'optimization' && optimization && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <div className="text-center p-4">
              <Sliders className="w-8 h-8 text-accent mx-auto mb-2" />
              <p className="text-2xl font-bold text-accent">{optimization.runs}</p>
              <p className="text-xs text-muted">Total Runs</p>
            </div>
          </Card>
          <Card>
            <div className="text-center p-4">
              <Leaf className="w-8 h-8 text-accent-light mx-auto mb-2" />
              <p className="text-2xl font-bold text-accent-light">{optimization.total_saved_kg.toFixed(2)} kg</p>
              <p className="text-xs text-muted">Total CO2 Saved</p>
            </div>
          </Card>
          <Card>
            <div className="text-center p-4">
              <BarChart3 className="w-8 h-8 text-warning mx-auto mb-2" />
              <p className="text-2xl font-bold text-warning">{optimization.avg_reduction.toFixed(1)}%</p>
              <p className="text-xs text-muted">Avg Reduction</p>
            </div>
          </Card>
          <Card>
            <div className="text-center p-4">
              <Zap className="w-8 h-8 text-purple-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-purple-400">{optimization.best_reduction.toFixed(1)}%</p>
              <p className="text-xs text-muted">Best Reduction</p>
            </div>
          </Card>
        </div>
      )}

      <Card>
        <div className="flex items-center gap-3 p-2">
          <BarChart3 className="w-4 h-4 text-accent" />
          <p className="text-xs text-muted">
            All analytics data is simulated/generated for academic demonstration.
            Values do not represent real measurements.
          </p>
        </div>
      </Card>
    </div>
  )
}
