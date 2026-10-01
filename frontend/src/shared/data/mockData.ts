import type { Severity } from '@/shared/types/common'

export interface DashboardMetrics {
  carbonGuardScore: number
  securityRiskScore: number
  currentThreatLevel: Severity
  activeThreats: number
  threatsDetected24h: number
  threatsBlocked24h: number
  energyConsumptionKwh: number
  estimatedCo2Kg: number
  carbonSavedKg: number
  renewablePercentage: number
  currentWorkload: number
  securityCarbonEfficiency: number
}

export interface ThreatActivityPoint {
  timestamp: string
  count: number
  critical: number
  high: number
  medium: number
  low: number
}

export interface CarbonEmissionPoint {
  timestamp: string
  co2Kg: number
  energyKwh: number
}

export interface CarbonSavingsPoint {
  timestamp: string
  baselineKg: number
  optimizedKg: number
  savedKg: number
}

export interface ThreatCategory {
  type: string
  count: number
  percentage: number
  color: string
}

export interface SecurityEvent {
  id: number
  timestamp: string
  eventType: string
  severity: Severity
  sourceIp: string
  targetIp: string
  status: string
  confidence: number
}

export interface AiRecommendation {
  id: number
  type: string
  recommendation: string
  priority: 'critical' | 'high' | 'medium' | 'low'
  reason: string
  expectedImpact: string
  confidence: number
}

export interface SystemHealthStatus {
  component: string
  status: 'online' | 'warning' | 'offline'
  lastCheck: string
}

export interface CarbonEfficiencyData {
  threatsDetected: number
  securityWorkload: string
  energyUsed: string
  estimatedCo2: string
  efficiencyScore: number
  rating: string
}

const now = new Date()

function hoursAgo(h: number): string {
  return new Date(now.getTime() - h * 3600000).toISOString()
}

function daysAgo(d: number): string {
  return new Date(now.getTime() - d * 86400000).toISOString()
}

export const mockDashboardMetrics: DashboardMetrics = {
  carbonGuardScore: 82,
  securityRiskScore: 45,
  currentThreatLevel: 'MEDIUM',
  activeThreats: 3,
  threatsDetected24h: 28,
  threatsBlocked24h: 25,
  energyConsumptionKwh: 3.42,
  estimatedCo2Kg: 1.62,
  carbonSavedKg: 14.7,
  renewablePercentage: 34.2,
  currentWorkload: 5,
  securityCarbonEfficiency: 72.5,
}

export const mockThreatActivity: ThreatActivityPoint[] = Array.from({ length: 24 }, (_, i) => ({
  timestamp: hoursAgo(23 - i),
  count: Math.floor(Math.random() * 8) + 1,
  critical: Math.floor(Math.random() * 2),
  high: Math.floor(Math.random() * 3),
  medium: Math.floor(Math.random() * 4),
  low: Math.floor(Math.random() * 5),
}))

export const mockCarbonEmissions: CarbonEmissionPoint[] = Array.from({ length: 24 }, (_, i) => ({
  timestamp: hoursAgo(23 - i),
  co2Kg: parseFloat((Math.random() * 0.12 + 0.03).toFixed(4)),
  energyKwh: parseFloat((Math.random() * 0.25 + 0.05).toFixed(4)),
}))

export const mockCarbonSavings: CarbonSavingsPoint[] = Array.from({ length: 14 }, (_, i) => {
  const baseline = Math.random() * 0.8 + 0.5
  const saved = Math.random() * 0.3 + 0.1
  return {
    timestamp: daysAgo(13 - i),
    baselineKg: parseFloat(baseline.toFixed(2)),
    optimizedKg: parseFloat((baseline - saved).toFixed(2)),
    savedKg: parseFloat(saved.toFixed(2)),
  }
})

export const mockThreatCategories: ThreatCategory[] = [
  { type: 'DDoS', count: 14, percentage: 22, color: '#ef4444' },
  { type: 'Brute Force', count: 11, percentage: 17, color: '#f97316' },
  { type: 'Port Scan', count: 18, percentage: 28, color: '#f59e0b' },
  { type: 'SQL Injection', count: 7, percentage: 11, color: '#a855f7' },
  { type: 'Malware', count: 4, percentage: 6, color: '#ec4899' },
  { type: 'Suspicious Login', count: 10, percentage: 16, color: '#06b6d4' },
]

export const mockSecurityEvents: SecurityEvent[] = [
  { id: 1, timestamp: hoursAgo(0.1), eventType: 'DDoS', severity: 'HIGH', sourceIp: '192.168.1.105', targetIp: '10.0.0.1', status: 'detected', confidence: 0.92 },
  { id: 2, timestamp: hoursAgo(0.5), eventType: 'Brute Force', severity: 'MEDIUM', sourceIp: '10.0.0.50', targetIp: '10.0.0.2', status: 'investigating', confidence: 0.87 },
  { id: 3, timestamp: hoursAgo(1.2), eventType: 'SQL Injection', severity: 'CRITICAL', sourceIp: '172.16.0.25', targetIp: '10.0.0.3', status: 'blocked', confidence: 0.95 },
  { id: 4, timestamp: hoursAgo(2.0), eventType: 'Port Scan', severity: 'LOW', sourceIp: '192.168.1.110', targetIp: '10.0.0.1', status: 'false_positive', confidence: 0.65 },
  { id: 5, timestamp: hoursAgo(3.1), eventType: 'Malware', severity: 'CRITICAL', sourceIp: '10.0.0.55', targetIp: '10.0.0.2', status: 'mitigated', confidence: 0.98 },
  { id: 6, timestamp: hoursAgo(4.5), eventType: 'Suspicious Login', severity: 'MEDIUM', sourceIp: '192.168.1.120', targetIp: '10.0.0.3', status: 'blocked', confidence: 0.78 },
  { id: 7, timestamp: hoursAgo(5.8), eventType: 'DDoS', severity: 'HIGH', sourceIp: '10.0.0.60', targetIp: '10.0.0.1', status: 'mitigated', confidence: 0.91 },
  { id: 8, timestamp: hoursAgo(7.2), eventType: 'Port Scan', severity: 'LOW', sourceIp: '172.16.0.30', targetIp: '10.0.0.2', status: 'detected', confidence: 0.58 },
  { id: 9, timestamp: hoursAgo(9.0), eventType: 'Brute Force', severity: 'HIGH', sourceIp: '192.168.1.130', targetIp: '10.0.0.1', status: 'blocked', confidence: 0.89 },
  { id: 10, timestamp: hoursAgo(11.5), eventType: 'SQL Injection', severity: 'HIGH', sourceIp: '10.0.0.65', targetIp: '10.0.0.3', status: 'mitigated', confidence: 0.93 },
]

export const mockRecommendations: AiRecommendation[] = [
  {
    id: 1,
    type: 'carbon',
    recommendation: 'Shift non-critical workloads to a lower-carbon period. Renewable energy availability is expected to increase in 2 hours.',
    priority: 'medium',
    reason: 'Current carbon intensity is above average. Low-carbon window predicted.',
    expectedImpact: 'Estimated 18% reduction in workload emissions',
    confidence: 0.82,
  },
  {
    id: 2,
    type: 'security',
    recommendation: 'Threat activity has increased 23% in the last 6 hours. Increase monitoring intensity on perimeter defenses.',
    priority: 'high',
    reason: 'Multiple DDoS and brute force attempts detected from similar source ranges.',
    expectedImpact: 'Improved detection rate and faster response time',
    confidence: 0.88,
  },
  {
    id: 3,
    type: 'energy',
    recommendation: 'Current workload has unusually high estimated energy consumption. Review resource allocation for log analysis tasks.',
    priority: 'medium',
    reason: 'Energy consumption 34% above baseline for current workload profile.',
    expectedImpact: 'Potential to save 0.4 kWh by optimizing log analysis scheduling',
    confidence: 0.76,
  },
  {
    id: 4,
    type: 'carbon',
    recommendation: 'Renewable energy availability is currently high at 45%. Schedule eligible security scans now.',
    priority: 'low',
    reason: 'Solar and wind availability optimal for next 3 hours.',
    expectedImpact: 'Carbon-efficient window for non-critical security operations',
    confidence: 0.85,
  },
]

export const mockSystemHealth: SystemHealthStatus[] = [
  { component: 'Security Engine', status: 'online', lastCheck: hoursAgo(0) },
  { component: 'Carbon Engine', status: 'online', lastCheck: hoursAgo(0) },
  { component: 'AI Engine', status: 'online', lastCheck: hoursAgo(0) },
  { component: 'Database', status: 'online', lastCheck: hoursAgo(0) },
  { component: 'API Server', status: 'online', lastCheck: hoursAgo(0) },
]

export const mockCarbonEfficiency: CarbonEfficiencyData = {
  threatsDetected: 28,
  securityWorkload: '5 active tasks',
  energyUsed: '0.82 kWh',
  estimatedCo2: '0.39 kg',
  efficiencyScore: 72.5,
  rating: 'Good',
}
