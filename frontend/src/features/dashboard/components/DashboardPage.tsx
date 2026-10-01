import { useEffect, useState } from 'react'
import {
  Shield,
  Leaf,
  Zap,
  Target,
  AlertTriangle,
  Activity,
  TrendingUp,
  Sun,
  RefreshCw,
} from 'lucide-react'
import MetricCard from '@/shared/ui/MetricCard'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import ThreatLevel from '@/shared/ui/ThreatLevel'
import PageHeader from '@/shared/ui/PageHeader'
import Badge from '@/shared/ui/Badge'
import ThreatChart from './ThreatChart'
import CarbonChart from './CarbonChart'
import SavingsChart from './SavingsChart'
import ThreatDistribution from './ThreatDistribution'
import RecommendationCard from './RecommendationCard'
import SecurityEventTable from './SecurityEventTable'
import SystemHealth from './SystemHealth'
import SecurityCarbonEfficiency from './SecurityCarbonEfficiency'
import { api } from '@/shared/utils/api'
import type {
  DashboardMetrics,
  ThreatActivityPoint,
  CarbonEmissionPoint,
  CarbonSavingsPoint,
  ThreatCategory,
  SecurityEvent,
  AiRecommendation,
  SystemHealthStatus,
  CarbonEfficiencyData,
} from '@/shared/data/mockData'

const POLL_INTERVAL = 30000

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [threatActivity, setThreatActivity] = useState<ThreatActivityPoint[]>([])
  const [carbonEmissions, setCarbonEmissions] = useState<CarbonEmissionPoint[]>([])
  const [carbonSavings, setCarbonSavings] = useState<CarbonSavingsPoint[]>([])
  const [threatCategories, setThreatCategories] = useState<ThreatCategory[]>([])
  const [events, setEvents] = useState<SecurityEvent[]>([])
  const [recommendations, setRecommendations] = useState<AiRecommendation[]>([])
  const [systemHealth, setSystemHealth] = useState<SystemHealthStatus[]>([])
  const [carbonEfficiency, setCarbonEfficiency] = useState<CarbonEfficiencyData | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  async function loadData() {
    try {
      const [m, ta, ce, cs, tc, ev, rec, sh, ceff] = await Promise.all([
        api.getDashboardMetrics(),
        api.getThreatActivity(),
        api.getCarbonEmissions(),
        api.getCarbonSavings(),
        api.getThreatCategories(),
        api.getSecurityEvents(),
        api.getRecommendations(),
        api.getSystemHealth(),
        api.getCarbonEfficiency(),
      ])
      setMetrics(m)
      setThreatActivity(ta.data_points)
      setCarbonEmissions(ce.data_points)
      setCarbonSavings(cs.data_points)
      setThreatCategories(tc.categories)
      setEvents(ev)
      setRecommendations(rec)
      setSystemHealth(sh)
      setCarbonEfficiency(ceff)
      setLastUpdated(new Date())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, POLL_INTERVAL)
    return () => clearInterval(interval)
  }, [])

  if (loading || !metrics || !carbonEfficiency) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-10 h-10 border-2 border-border border-t-accent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Dashboard"
        subtitle="CarbonGuard — Cybersecurity & Green Infrastructure Operations Center"
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
              className="flex items-center gap-2 px-3 py-1.5 bg-card border border-border rounded-md text-xs text-muted hover:text-accent hover:border-accent/30 transition-all"
            >
              <RefreshCw className="w-3 h-3" />
              Refresh
            </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="Carbon Guard Score" value={`${metrics.carbonGuardScore}`} icon={Leaf} color="success" trend={2.5} subtitle="Overall environmental rating" />
        <MetricCard title="Security Risk Score" value={`${metrics.securityRiskScore}`} icon={Shield} color="warning" trend={-1.2} subtitle="Current threat risk" />
        <MetricCard title="Active Threats" value={metrics.activeThreats} icon={Target} color="danger" trend={15} subtitle="Requires attention" />
        <MetricCard title="Threats Blocked" value={`${metrics.threatsBlocked24h}/${metrics.threatsDetected24h}`} icon={AlertTriangle} color="primary" trend={8} subtitle="Last 24 hours" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="Energy Consumption" value={`${metrics.energyConsumptionKwh} kWh`} icon={Zap} color="primary" subtitle="Current estimate" compact />
        <MetricCard title="Est. CO2 Emissions" value={`${metrics.estimatedCo2Kg} kg`} icon={Activity} color="danger" subtitle="Environmental impact" compact />
        <MetricCard title="Carbon Saved" value={`${metrics.carbonSavedKg} kg`} icon={TrendingUp} color="success" trend={12} subtitle="This month" compact />
        <MetricCard title="Renewable Energy" value={`${metrics.renewablePercentage}%`} icon={Sun} color="success" subtitle="Current mix" compact />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <CardTitle>Threat Activity (24h)</CardTitle>
              <ThreatLevel level={metrics.currentThreatLevel} size="sm" />
            </div>
            <CardContent>
              <ThreatChart data={threatActivity} />
            </CardContent>
          </Card>
        </div>
        <div>
          <Card className="h-full">
            <CardTitle>Threat Distribution</CardTitle>
            <CardContent>
              <ThreatDistribution data={threatCategories} />
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <Card>
          <div className="flex items-center justify-between mb-4">
            <CardTitle>Carbon Emissions & Energy (24h)</CardTitle>
            <Badge variant="muted" size="sm">ESTIMATED</Badge>
          </div>
          <CardContent>
            <CarbonChart data={carbonEmissions} />
          </CardContent>
        </Card>
        <Card>
          <div className="flex items-center justify-between mb-4">
            <CardTitle>Carbon Savings Comparison</CardTitle>
            <Badge variant="success" size="sm">14-DAY TREND</Badge>
          </div>
          <CardContent>
            <SavingsChart data={carbonSavings} />
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div>
          <Card className="h-full">
            <div className="flex items-center justify-between mb-4">
              <CardTitle>AI Recommendations</CardTitle>
              <Badge variant="primary" size="sm">{recommendations.length} active</Badge>
            </div>
            <CardContent>
              <RecommendationCard recommendations={recommendations} />
            </CardContent>
          </Card>
        </div>
        <div>
          <Card className="h-full">
            <div className="flex items-center justify-between mb-4">
              <CardTitle>System Health</CardTitle>
              <Badge variant="success" size="sm">ALL ONLINE</Badge>
            </div>
            <CardContent>
              <SystemHealth health={systemHealth} />
            </CardContent>
          </Card>
        </div>
        <div>
          <Card className="h-full border-accent/20">
            <div className="flex items-center justify-between mb-4">
              <CardTitle>Efficiency Score</CardTitle>
              <Badge variant="success" size="sm">LIVE</Badge>
            </div>
            <CardContent>
              <SecurityCarbonEfficiency data={carbonEfficiency} />
            </CardContent>
          </Card>
        </div>
      </div>

      <Card>
        <div className="flex items-center justify-between mb-4">
          <CardTitle>Recent Security Events</CardTitle>
          <Badge variant="muted" size="sm">DEMO DATA</Badge>
        </div>
        <CardContent>
          <SecurityEventTable events={events} />
        </CardContent>
      </Card>
    </div>
  )
}
