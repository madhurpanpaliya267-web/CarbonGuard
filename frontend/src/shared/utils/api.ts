import { config } from '@/config/env'
import { apiClient } from './apiClient'
import {
  mockDashboardMetrics,
  mockThreatActivity,
  mockCarbonEmissions,
  mockCarbonSavings,
  mockThreatCategories,
  mockSecurityEvents,
  mockRecommendations,
  mockSystemHealth,
  mockCarbonEfficiency,
} from '@/shared/data/mockData'
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
import type {
  SecurityStats,
  SecurityEventDetail,
  AttackTypeInfo,
  SimulationResult,
  ThreatDetail,
  ThreatStats,
  ThreatExplanation,
  CarbonOverview,
  CarbonMetric,
  CarbonEfficiency,
  EnergyOverview,
  EnergyMetric,
  Workload,
  OptimizationResult,
  OptimizationComparison,
  RenewableStatus,
  AIRecommendationItem,
  SecurityAnalytics,
  CarbonAnalytics,
  EnergyAnalytics,
  OptimizationAnalytics,
  SystemMetric,
  SystemSetting,
} from '@/shared/types/common'

async function fetchWithFallback<T>(
  path: string,
  fallback: T,
  transform?: (data: unknown) => T,
): Promise<T> {
  try {
    const response = await fetch(`${config.API_BASE_URL}${path}`, {
      signal: AbortSignal.timeout(3000),
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const data = await response.json()
    return transform ? transform(data) : data as T
  } catch {
    return fallback
  }
}

export const api = {
  getDashboardMetrics: (): Promise<DashboardMetrics> =>
    fetchWithFallback('/dashboard', mockDashboardMetrics, (data: unknown) => {
      const d = data as Record<string, unknown>
      return {
        carbonGuardScore: (d.carbon_guard_score as number) ?? mockDashboardMetrics.carbonGuardScore,
        securityRiskScore: (d.security_risk_score as number) ?? mockDashboardMetrics.securityRiskScore,
        currentThreatLevel: (d.current_threat_level as DashboardMetrics['currentThreatLevel']) ?? mockDashboardMetrics.currentThreatLevel,
        activeThreats: (d.active_threats as number) ?? mockDashboardMetrics.activeThreats,
        threatsDetected24h: (d.threats_detected_24h as number) ?? mockDashboardMetrics.threatsDetected24h,
        threatsBlocked24h: (d.threats_blocked_24h as number) ?? mockDashboardMetrics.threatsBlocked24h,
        energyConsumptionKwh: (d.energy_consumption_kwh as number) ?? mockDashboardMetrics.energyConsumptionKwh,
        estimatedCo2Kg: (d.estimated_co2_kg as number) ?? mockDashboardMetrics.estimatedCo2Kg,
        carbonSavedKg: (d.carbon_saved_kg as number) ?? mockDashboardMetrics.carbonSavedKg,
        renewablePercentage: (d.renewable_percentage as number) ?? mockDashboardMetrics.renewablePercentage,
        currentWorkload: (d.current_workload as number) ?? mockDashboardMetrics.currentWorkload,
        securityCarbonEfficiency: (d.security_carbon_efficiency as number) ?? mockDashboardMetrics.securityCarbonEfficiency,
      }
    }),

  getThreatActivity: (period: string = '24h'): Promise<{ data_points: ThreatActivityPoint[] }> =>
    fetchWithFallback(
      `/dashboard/charts/threat-activity?period=${period}`,
      { data_points: mockThreatActivity },
      (data: unknown) => {
        const d = data as Record<string, unknown>
        return {
          data_points: Array.isArray(d.data_points) ? d.data_points as ThreatActivityPoint[] : mockThreatActivity,
        }
      },
    ),

  getCarbonEmissions: (period: string = '24h'): Promise<{ data_points: CarbonEmissionPoint[] }> =>
    fetchWithFallback(
      `/dashboard/charts/carbon-emissions?period=${period}`,
      { data_points: mockCarbonEmissions },
      (data: unknown) => {
        const d = data as Record<string, unknown>
        const points = Array.isArray(d.data_points) ? d.data_points as Record<string, unknown>[] : null
        return {
          data_points: points
            ? points.map((p) => ({
                timestamp: p.timestamp as string,
                co2Kg: (p.co2_kg as number) ?? 0,
                energyKwh: (p.energy_kwh as number) ?? 0,
              }))
            : mockCarbonEmissions,
        }
      },
    ),

  getCarbonSavings: (): Promise<{ data_points: CarbonSavingsPoint[] }> =>
    fetchWithFallback(
      '/dashboard/charts/carbon-savings',
      { data_points: mockCarbonSavings },
      (data: unknown) => {
        const d = data as Record<string, unknown>
        const points = Array.isArray(d.data_points) ? d.data_points as Record<string, unknown>[] : null
        return {
          data_points: points
            ? points.map((p) => {
                const saved = (p.saved_kg as number) ?? 0
                const baseline = saved + ((p.optimized_kg as number) ?? saved * 0.8)
                return {
                  timestamp: p.timestamp as string,
                  baselineKg: parseFloat(baseline.toFixed(2)),
                  optimizedKg: parseFloat((baseline - saved).toFixed(2)),
                  savedKg: parseFloat(saved.toFixed(2)),
                }
              })
            : mockCarbonSavings,
        }
      },
    ),

  getThreatCategories: (): Promise<{ categories: ThreatCategory[] }> =>
    fetchWithFallback(
      '/dashboard/charts/threat-categories',
      { categories: mockThreatCategories },
      (data: unknown) => {
        const d = data as Record<string, unknown>
        const items = Array.isArray(d.categories) ? d.categories as Record<string, unknown>[] : null
        if (!items) return { categories: mockThreatCategories }
        const colorMap: Record<string, string> = {
          DDoS: '#ef4444', 'Brute Force': '#f97316', 'Port Scan': '#f59e0b',
          'SQL Injection': '#a855f7', Malware: '#ec4899', 'Suspicious Login': '#06b6d4',
        }
        return {
          categories: items.map((c) => ({
            type: c.type as string,
            count: c.count as number,
            percentage: c.percentage as number,
            color: colorMap[c.type as string] ?? '#6b7280',
          })),
        }
      },
    ),

  getSecurityEvents: (): Promise<SecurityEvent[]> =>
    fetchWithFallback('/security/events', mockSecurityEvents, (data: unknown) => {
      const d = data as Record<string, unknown>
      const items = d.items
      if (!Array.isArray(items)) return mockSecurityEvents
      return items.map((e: Record<string, unknown>) => ({
        id: e.id as number,
        timestamp: e.timestamp as string,
        eventType: (e.event_type as string) ?? '',
        severity: (e.severity as SecurityEvent['severity']) ?? 'LOW',
        sourceIp: (e.source_ip as string) ?? '',
        targetIp: (e.target_ip as string) ?? '',
        status: (e.status as string) ?? '',
        confidence: (e.confidence as number) ?? 0,
      }))
    }),

  getRecommendations: (): Promise<AiRecommendation[]> =>
    fetchWithFallback('/recommendations', mockRecommendations, (data: unknown) => {
      if (!Array.isArray(data)) return mockRecommendations
      return data.map((r: Record<string, unknown>) => ({
        id: r.id as number,
        type: (r.recommendation_type as string) ?? '',
        recommendation: (r.recommendation as string) ?? '',
        priority: (r.priority as AiRecommendation['priority']) ?? 'medium',
        reason: (r.reason as string) ?? '',
        expectedImpact: (r.expected_security_impact as string) ?? (r.expected_carbon_impact as string) ?? '',
        confidence: (r.confidence as number) ?? 0,
      }))
    }),

  getSystemHealth: (): Promise<SystemHealthStatus[]> =>
    fetchWithFallback('/system-health', mockSystemHealth, (data: unknown) => {
      const d = data as Record<string, unknown>
      const mapped: SystemHealthStatus[] = [
        { component: 'Security Engine', status: (d.security_engine_status as string || 'online') as SystemHealthStatus['status'], lastCheck: new Date().toISOString() },
        { component: 'Carbon Engine', status: (d.carbon_engine_status as string || 'online') as SystemHealthStatus['status'], lastCheck: new Date().toISOString() },
        { component: 'AI Engine', status: (d.ai_engine_status as string || 'online') as SystemHealthStatus['status'], lastCheck: new Date().toISOString() },
        { component: 'Database', status: (d.database_status as string || 'online') as SystemHealthStatus['status'], lastCheck: new Date().toISOString() },
        { component: 'API Server', status: (d.api_status as string || 'online') as SystemHealthStatus['status'], lastCheck: new Date().toISOString() },
      ]
      return mapped
    }),

  getCarbonEfficiency: (): Promise<CarbonEfficiencyData> =>
    fetchWithFallback('/carbon/efficiency', mockCarbonEfficiency, (data: unknown) => {
      const d = data as Record<string, unknown>
      const score = (d.efficiency_score as number) ?? mockCarbonEfficiency.efficiencyScore
      const rating = (d.rating as string) ?? mockCarbonEfficiency.rating
      const threatsPerKwh = (d.threats_per_kwh as number) ?? 0
      return {
        threatsDetected: Math.round(threatsPerKwh * 10),
        securityWorkload: mockCarbonEfficiency.securityWorkload,
        energyUsed: mockCarbonEfficiency.energyUsed,
        estimatedCo2: mockCarbonEfficiency.estimatedCo2,
        efficiencyScore: score,
        rating: rating,
      }
    }),

  getSecurityStats: (): Promise<SecurityStats> =>
    fetchWithFallback('/security/stats', {
      total_events: 30,
      by_severity: { CRITICAL: 3, HIGH: 8, MEDIUM: 10, LOW: 9 },
      by_type: { ddos: 6, brute_force: 5, port_scan: 8, sql_injection: 4, malware: 3, suspicious_login: 4 },
      by_status: { detected: 8, investigating: 5, mitigated: 7, blocked: 8, false_positive: 2 },
      avg_confidence: 0.82,
      total_energy_kwh: 0.82,
      total_co2_kg: 0.39,
      simulated: true,
    }),

  getSecurityEventsList: (params?: {
    severity?: string
    event_type?: string
    status?: string
    page?: number
    page_size?: number
  }): Promise<{ items: SecurityEventDetail[]; total: number; page: number; page_size: number }> => {
    const searchParams = new URLSearchParams()
    if (params?.severity) searchParams.set('severity', params.severity)
    if (params?.event_type) searchParams.set('event_type', params.event_type)
    if (params?.status) searchParams.set('status', params.status)
    if (params?.page) searchParams.set('page', String(params.page))
    if (params?.page_size) searchParams.set('page_size', String(params.page_size))
    const query = searchParams.toString()
    const path = `/security/events${query ? `?${query}` : ''}`
    return fetchWithFallback(path, { items: [], total: 0, page: 1, page_size: 20 })
  },

  getAttackTypes: (): Promise<{ types: AttackTypeInfo[] }> =>
    fetchWithFallback('/simulator/attack-types', {
      types: [
        { id: 'ddos', name: 'DDoS', description: 'Distributed Denial of Service', typical_severity: 'HIGH' },
        { id: 'brute_force', name: 'Brute Force', description: 'Brute force login attempt', typical_severity: 'MEDIUM' },
        { id: 'port_scan', name: 'Port Scan', description: 'Network port scanning', typical_severity: 'LOW' },
        { id: 'sql_injection', name: 'SQL Injection', description: 'SQL injection attempt', typical_severity: 'HIGH' },
        { id: 'malware', name: 'Malware', description: 'Malware detection', typical_severity: 'CRITICAL' },
        { id: 'suspicious_login', name: 'Suspicious Login', description: 'Suspicious login activity', typical_severity: 'MEDIUM' },
      ],
    }),

  simulateAttack: (attackType: string): Promise<SimulationResult> =>
    apiClient.post('/simulator/simulate', { attack_type: attackType }),

  getThreats: (params?: {
    severity?: string
    threat_type?: string
    status?: string
    page?: number
    page_size?: number
  }): Promise<{ items: ThreatDetail[]; total: number; page: number; page_size: number }> => {
    const searchParams = new URLSearchParams()
    if (params?.severity) searchParams.set('severity', params.severity)
    if (params?.threat_type) searchParams.set('threat_type', params.threat_type)
    if (params?.status) searchParams.set('status', params.status)
    if (params?.page) searchParams.set('page', String(params.page))
    if (params?.page_size) searchParams.set('page_size', String(params.page_size))
    const query = searchParams.toString()
    const path = `/threats${query ? `?${query}` : ''}`
    return fetchWithFallback(path, { items: [], total: 0, page: 1, page_size: 20 })
  },

  getThreatStats: (): Promise<ThreatStats> =>
    fetchWithFallback('/threats/stats', {
      total_threats: 20,
      active_threats: 8,
      resolved_threats: 7,
      avg_risk_score: 45.2,
      avg_confidence: 0.81,
      by_severity: { CRITICAL: 2, HIGH: 5, MEDIUM: 8, LOW: 5 },
      by_type: { ddos: 4, brute_force: 3, port_scan: 5, sql_injection: 3, malware: 2, suspicious_login: 3 },
      by_status: { active: 8, investigating: 3, resolved: 7, false_positive: 2 },
      total_events: 30,
    }),

  updateThreatStatus: (threatId: number, status: string): Promise<ThreatDetail> =>
    apiClient.patch(`/threats/${threatId}/status`, { status }),

  getThreatExplanation: (threatId: number): Promise<ThreatExplanation> =>
    fetchWithFallback(`/threats/${threatId}/explanation`, {
      prediction: 'Unknown',
      confidence: 0,
      factors: [],
      reasoning: 'No explanation available',
      recommended_action: 'Investigate',
    }),

  getCarbonOverview: (): Promise<CarbonOverview> =>
    fetchWithFallback('/carbon', {
      current: { id: 0, timestamp: '', total_energy_kwh: 0, total_co2_kg: 0, security_energy_kwh: 0, security_co2_kg: 0, carbon_saved_kg: 0, carbon_intensity: 475, renewable_percentage: 25, workload_count: 0, security_carbon_efficiency: 0 },
      history: [],
      summary: { total_energy: 0, total_co2: 0, total_saved: 0, avg_efficiency: 0 },
    }),

  getCarbonCurrent: (): Promise<CarbonMetric> =>
    fetchWithFallback('/carbon/current', { id: 0, timestamp: '', total_energy_kwh: 0, total_co2_kg: 0, security_energy_kwh: 0, security_co2_kg: 0, carbon_saved_kg: 0, carbon_intensity: 475, renewable_percentage: 25, workload_count: 0, security_carbon_efficiency: 0 }),

  getCarbonEfficiencyData: (): Promise<CarbonEfficiency> =>
    fetchWithFallback('/carbon/efficiency', { threats_per_kwh: 0, co2_per_threat: 0, efficiency_score: 0, rating: 'N/A' }),

  getEnergyOverview: (): Promise<EnergyOverview> =>
    fetchWithFallback('/energy', {
      current: { id: 0, timestamp: '', total_power_watts: 0, cpu_power_watts: 0, memory_power_watts: 0, network_power_watts: 0, energy_kwh: 0, estimated: true },
      history: [],
      summary: { total_energy: 0, avg_power: 0 },
    }),

  getEnergyCurrent: (): Promise<EnergyMetric> =>
    fetchWithFallback('/energy/current', { id: 0, timestamp: '', total_power_watts: 0, cpu_power_watts: 0, memory_power_watts: 0, network_power_watts: 0, energy_kwh: 0, estimated: true }),

  getWorkloads: (): Promise<Workload[]> =>
    fetchWithFallback('/optimizer/workloads', []),

  runOptimization: (): Promise<{ result_id: number; comparison: OptimizationResult }> =>
    apiClient.post('/optimizer/run'),

  getOptimizationComparison: (): Promise<OptimizationComparison> =>
    fetchWithFallback('/optimizer/comparison', {
      before: { energy_kwh: 0, co2_kg: 0 },
      after: { energy_kwh: 0, co2_kg: 0 },
      comparison: { energy_saved: 0, co2_saved: 0, reduction_pct: 0 },
    }),

  getRenewableStatus: (): Promise<RenewableStatus> =>
    fetchWithFallback('/renewable-energy', {
      renewable_percentage: 0,
      solar_availability: 0,
      wind_availability: 0,
      grid_carbon_intensity: 475,
      forecast: [],
    }),

  getRecommendationsList: (params?: {
    type?: string
    priority?: string
    unread_only?: boolean
  }): Promise<AIRecommendationItem[]> => {
    const searchParams = new URLSearchParams()
    if (params?.type) searchParams.set('type', params.type)
    if (params?.priority) searchParams.set('priority', params.priority)
    if (params?.unread_only) searchParams.set('unread_only', 'true')
    const query = searchParams.toString()
    const path = `/recommendations${query ? `?${query}` : ''}`
    return fetchWithFallback(path, [])
  },

  generateRecommendations: (): Promise<AIRecommendationItem[]> =>
    apiClient.post('/recommendations/generate'),

  markRecommendationRead: (id: number): Promise<{ success: boolean }> =>
    apiClient.patch(`/recommendations/${id}/read`),

  dismissRecommendation: (id: number): Promise<{ success: boolean }> =>
    apiClient.patch(`/recommendations/${id}/dismiss`),

  getSecurityAnalytics: (period: string = '7d'): Promise<SecurityAnalytics> =>
    fetchWithFallback(`/analytics/security?period=${period}`, {
      attacks_over_time: [],
      categories: [],
      severity_dist: [],
      top_sources: [],
    }),

  getCarbonAnalytics: (period: string = '7d'): Promise<CarbonAnalytics> =>
    fetchWithFallback(`/analytics/carbon?period=${period}`, {
      emissions_over_time: [],
      savings_over_time: [],
      efficiency_trend: [],
    }),

  getEnergyAnalytics: (period: string = '7d'): Promise<EnergyAnalytics> =>
    fetchWithFallback(`/analytics/energy?period=${period}`, {
      usage_over_time: [],
      by_type: [],
      peak_hours: [],
    }),

  getOptimizationAnalytics: (): Promise<OptimizationAnalytics> =>
    fetchWithFallback('/analytics/optimization', { runs: 0, avg_reduction: 0, total_saved_kg: 0, best_reduction: 0 }),

  getEventsList: (params?: {
    severity?: string
    event_type?: string
    status?: string
    page?: number
    page_size?: number
  }): Promise<{ items: SecurityEventDetail[]; total: number; page: number; page_size: number }> => {
    const searchParams = new URLSearchParams()
    if (params?.severity) searchParams.set('severity', params.severity)
    if (params?.event_type) searchParams.set('event_type', params.event_type)
    if (params?.status) searchParams.set('status', params.status)
    if (params?.page) searchParams.set('page', String(params.page))
    if (params?.page_size) searchParams.set('page_size', String(params.page_size))
    const query = searchParams.toString()
    const path = `/events${query ? `?${query}` : ''}`
    return fetchWithFallback(path, { items: [], total: 0, page: 1, page_size: 20 })
  },

  getSystemHealthData: (): Promise<SystemMetric> =>
    fetchWithFallback('/system-health', {
      id: 0, timestamp: '', cpu_utilization: 0, memory_utilization: 0, active_workloads: 0,
      security_engine_status: 'online', carbon_engine_status: 'online', ai_engine_status: 'online',
      database_status: 'online', api_status: 'online', simulated: true,
    }),

  getSystemHealthHistory: (): Promise<SystemMetric[]> =>
    fetchWithFallback('/system-health/history', []),

  getSettings: (): Promise<SystemSetting[]> =>
    fetchWithFallback('/settings', []),

  updateSetting: (key: string, value: string): Promise<SystemSetting> =>
    apiClient.put('/settings', { key, value }),

  resetSettings: (): Promise<{ success: boolean }> =>
    apiClient.post('/settings/reset'),
}
