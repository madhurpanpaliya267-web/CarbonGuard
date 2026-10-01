export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export type EventStatus = 'detected' | 'investigating' | 'mitigated' | 'blocked' | 'false_positive'

export type ThreatStatus = 'active' | 'investigating' | 'resolved' | 'false_positive'

export type WorkloadPriority = 'critical' | 'high' | 'medium' | 'low'

export type WorkloadStatus = 'pending' | 'scheduled' | 'running' | 'completed' | 'delayed'

export type EngineStatus = 'online' | 'offline' | 'degraded'

export type AttackType =
  | 'ddos'
  | 'brute_force'
  | 'port_scan'
  | 'sql_injection'
  | 'malware'
  | 'suspicious_login'
  | 'abnormal_traffic'
  | 'unauthorized_access'

export type WorkloadType =
  | 'security_scan'
  | 'log_analysis'
  | 'traffic_monitor'
  | 'patch_deployment'
  | 'backup'
  | 'report_generation'

export interface SecurityStats {
  total_events: number
  by_severity: Record<string, number>
  by_type: Record<string, number>
  by_status: Record<string, number>
  avg_confidence: number
  total_energy_kwh: number
  total_co2_kg: number
  simulated: boolean
}

export interface SecurityEventDetail {
  id: number
  event_uuid: string
  timestamp: string
  event_type: string
  severity: Severity
  source_ip: string
  target_ip: string
  target_port: number
  confidence: number
  status: string
  detection_method: string
  description: string
  risk_score: number
  estimated_workload_cpu: number
  estimated_energy_kwh: number
  estimated_co2_kg: number
}

export interface AttackTypeInfo {
  id: string
  name: string
  description: string
  typical_severity: Severity
}

export interface SimulationResult {
  event: SecurityEventDetail
  threat: ThreatDetail
  risk_assessment: RiskAssessment
  workload_impact: WorkloadImpact
  energy_impact: EnergyImpact
  carbon_impact: CarbonImpact
  ai_recommendation: SimulationRecommendation
  pipeline: PipelineStep[]
}

export interface ThreatDetail {
  id: number
  threat_uuid: string
  event_id: number
  threat_type: string
  severity: Severity
  confidence: number
  risk_score: number
  status: ThreatStatus
  detected_at: string
  resolved_at: string | null
  explanation: string
  recommended_action: string
  anomaly_level: number
}

export interface RiskAssessment {
  risk_score: number
  severity: Severity
  confidence: number
  factors: RiskFactor[]
}

export interface RiskFactor {
  factor: string
  weight: number
  value: number | string
  contribution: number
}

export interface WorkloadImpact {
  cpu_seconds: number
  memory_mb: number
  estimated_duration_seconds: number
}

export interface EnergyImpact {
  energy_kwh: number
  power_watts: number
  estimated: boolean
}

export interface CarbonImpact {
  co2_kg: number
  carbon_intensity: number
  renewable_offset_kg: number
  net_co2_kg: number
  estimated: boolean
  simulated: boolean
  calculation_breakdown: string
}

export interface SimulationRecommendation {
  recommendation: string
  priority: string
  reason: string
  expected_security_impact: string
  expected_carbon_impact: string
  confidence: number
  factors: RiskFactor[]
}

export interface PipelineStep {
  step: string
  status: string
  detail: string
}

export interface ThreatStats {
  total_threats: number
  active_threats: number
  resolved_threats: number
  avg_risk_score: number
  avg_confidence: number
  by_severity: Record<string, number>
  by_type: Record<string, number>
  by_status: Record<string, number>
  total_events: number
}

export interface ThreatExplanation {
  prediction: string
  confidence: number
  factors: RiskFactor[]
  reasoning: string
  recommended_action: string
}

export interface CarbonMetric {
  id: number
  timestamp: string
  total_energy_kwh: number
  total_co2_kg: number
  security_energy_kwh: number
  security_co2_kg: number
  carbon_saved_kg: number
  carbon_intensity: number
  renewable_percentage: number
  workload_count: number
  security_carbon_efficiency: number
}

export interface CarbonOverview {
  current: CarbonMetric
  history: CarbonMetric[]
  summary: {
    total_energy: number
    total_co2: number
    total_saved: number
    avg_efficiency: number
  }
}

export interface CarbonEfficiency {
  threats_per_kwh: number
  co2_per_threat: number
  efficiency_score: number
  rating: string
}

export interface EnergyMetric {
  id: number
  timestamp: string
  total_power_watts: number
  cpu_power_watts: number
  memory_power_watts: number
  network_power_watts: number
  energy_kwh: number
  estimated: boolean
}

export interface EnergyOverview {
  current: EnergyMetric
  history: EnergyMetric[]
  summary: {
    total_energy: number
    avg_power: number
  }
}

export interface Workload {
  id: number
  workload_uuid: string
  name: string
  workload_type: string
  priority: WorkloadPriority
  is_security_critical: boolean
  estimated_cpu_seconds: number
  estimated_memory_mb: number
  estimated_energy_kwh: number
  estimated_co2_kg: number
  status: WorkloadStatus
  scheduled_time: string
  optimized_time: string | null
  carbon_intensity_at_exec: number | null
  created_at: string
  completed_at: string | null
}

export interface OptimizationComparison {
  before: { energy_kwh: number; co2_kg: number }
  after: { energy_kwh: number; co2_kg: number }
  comparison: { energy_saved: number; co2_saved: number; reduction_pct: number }
}

export interface OptimizationResult {
  workloads_analyzed: number
  workloads_shifted: number
  workloads_unchanged: number
  critical_protected: number
  energy_before_kwh: number
  energy_after_kwh: number
  co2_before_kg: number
  co2_after_kg: number
  energy_saved_kwh: number
  co2_saved_kg: number
  reduction_percentage: number
  details: OptimizationDetail[]
}

export interface OptimizationDetail {
  workload_uuid: string
  name: string
  action: 'shifted' | 'unchanged'
  original_time?: string
  optimized_time?: string
  delay_hours?: number
  co2_saved_kg?: number
  reason?: string
}

export interface RenewableStatus {
  renewable_percentage: number
  solar_availability: number
  wind_availability: number
  grid_carbon_intensity: number
  forecast: RenewableForecastPoint[]
}

export interface RenewableForecastPoint {
  timestamp: string
  solar: number
  wind: number
  renewable_pct: number
  carbon_intensity: number
}

export interface AIRecommendationItem {
  id: number
  timestamp: string
  recommendation_type: string
  recommendation: string
  priority: 'critical' | 'high' | 'medium' | 'low'
  reason: string
  expected_security_impact: string | null
  expected_carbon_impact: string | null
  confidence: number
  factors_json: string
  is_read: boolean
  is_dismissed: boolean
}

export interface SecurityAnalytics {
  attacks_over_time: { date: string; count: number }[]
  categories: { type: string; count: number }[]
  severity_dist: { level: string; count: number }[]
  top_sources: { ip: string; count: number }[]
}

export interface CarbonAnalytics {
  emissions_over_time: { date: string; co2_kg: number }[]
  savings_over_time: { date: string; saved_kg: number; cumulative_kg: number }[]
  efficiency_trend: { date: string; efficiency: number }[]
}

export interface EnergyAnalytics {
  usage_over_time: { date: string; energy_kwh: number }[]
  by_type: { type: string; energy_kwh: number }[]
  peak_hours: { hour: number; energy_kwh: number }[]
}

export interface OptimizationAnalytics {
  runs: number
  avg_reduction: number
  total_saved_kg: number
  best_reduction: number
}

export interface SystemMetric {
  id: number
  timestamp: string
  cpu_utilization: number
  memory_utilization: number
  active_workloads: number
  security_engine_status: string
  carbon_engine_status: string
  ai_engine_status: string
  database_status: string
  api_status: string
  simulated: boolean
}

export interface SystemSetting {
  id: number
  key: string
  value: string
  category: string
  description: string
}
