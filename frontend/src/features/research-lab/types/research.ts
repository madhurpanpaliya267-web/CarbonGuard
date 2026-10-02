export interface Experiment {
  id: number
  experiment_uuid: string
  name: string
  description: string | null
  experiment_type: string
  attack_type: string
  attack_intensity: string
  workload_profile: string | null
  security_controls: string | null
  measurement_mode: string
  duration_seconds: number
  num_trials: number
  carbon_intensity: number | null
  renewable_pct: number | null
  software_version: string | null
  configuration_version: string | null
  random_seed: number | null
  status: string
  created_at: string
  completed_at: string | null
  notes: string | null
}

export interface ExperimentListResponse {
  total: number
  items: Experiment[]
}

export interface ExperimentRun {
  id: number
  run_uuid: string
  experiment_id: number
  trial_number: number
  attack_type: string
  attack_intensity: string
  attack_parameters: string | null
  workload_profile: string | null
  workload_value: number | null
  workload_unit: string | null
  security_controls: string | null
  control_count: number
  measurement_mode: string
  start_time: string
  end_time: string | null
  duration_seconds: number | null
  status: string
  error_message: string | null
}

export interface EnergyMeasurement {
  id: number
  run_id: number
  energy_joules: number
  power_watts: number | null
  duration_seconds: number
  cpu_usage_pct: number | null
  memory_usage_pct: number | null
  network_usage_mbps: number | null
  source: string
  measurement_mode: string
  timestamp: string
}

export interface SecurityEffectiveness {
  id: number
  run_id: number
  detection_rate: number | null
  detection_latency_ms: number | null
  false_positive_rate: number | null
  mitigation_time_ms: number | null
  threat_severity: string | null
  security_response: string | null
  security_score: number | null
  controls_active: string | null
  controls_config: string | null
}

export interface ExperimentSummary {
  experiment: Experiment
  runs: ExperimentRun[]
  measurements: EnergyMeasurement[]
  security_effects: SecurityEffectiveness[]
}

export interface AttackProfile {
  attack_type: string
  display_name: string
  description: string
  workload_unit: string
  intensity_levels: string[]
  supported_controls: string[]
  config_version: string
}

export interface AttackProfileListResponse {
  attacks: AttackProfile[]
}

export interface SecurityControl {
  control_id: string
  display_name: string
  category: string
  description: string
  supported_attack_types: string[]
  config_parameters: Record<string, unknown>
  enabled_by_default: boolean
}

export interface SecurityControlListResponse {
  controls: SecurityControl[]
}

export interface MarginalEnergyResult {
  id: number
  experiment_id: number
  baseline_run_id: number
  security_run_id: number
  attack_type: string
  attack_intensity: string
  workload_value: number | null
  workload_unit: string | null
  duration_seconds: number | null
  baseline_energy_joules: number
  security_energy_joules: number
  marginal_energy_joules: number
  baseline_power_watts: number | null
  security_power_watts: number | null
  marginal_power_watts: number | null
  baseline_energy_kwh: number | null
  security_energy_kwh: number | null
  marginal_energy_kwh: number | null
  baseline_carbon_kg: number | null
  security_carbon_kg: number | null
  marginal_carbon_kg: number | null
  carbon_intensity: number | null
  measurement_mode: string
  formula_version: string
  created_at: string
}

export interface MarginalEnergyListResponse {
  total: number
  items: MarginalEnergyResult[]
}

export interface StatisticsSummary {
  mean: number
  median: number
  std_dev: number
  min: number
  max: number
  count: number
}

export interface SecurityEffectivenessBundle {
  baseline: SecurityEffectiveness | null
  control_a: SecurityEffectiveness | null
  control_b: SecurityEffectiveness | null
  combined: SecurityEffectiveness | null
}

export interface InteractionResult {
  id: number
  experiment_id: number
  trial_number: number
  baseline_run_id: number | null
  control_a_run_id: number | null
  control_b_run_id: number | null
  combined_run_id: number | null
  control_a: string
  control_b: string
  attack_type: string | null
  attack_intensity: string | null
  workload_value: number | null
  workload_unit: string | null
  duration_seconds: number | null
  energy_baseline: number
  energy_a: number
  energy_b: number
  energy_ab: number
  interaction_effect: number
  interaction_index: number | null
  interpretation: string | null
  power_baseline: number | null
  power_a: number | null
  power_b: number | null
  power_ab: number | null
  interaction_power: number | null
  carbon_baseline_kg: number | null
  carbon_a_kg: number | null
  carbon_b_kg: number | null
  carbon_ab_kg: number | null
  interaction_carbon_kg: number | null
  carbon_intensity: number | null
  energy_provider: string | null
  measurement_mode: string | null
  formula_version: string
  created_at: string
  security_effectiveness: SecurityEffectivenessBundle | null
}

export interface InteractionEffectListResponse {
  total: number
  items: InteractionResult[]
}

export interface AmplificationStatistics {
  amplification_energy: StatisticsSummary
  amplification_ratio: StatisticsSummary
  power_amplification: StatisticsSummary
  carbon_amplification: StatisticsSummary
  formula_version: string
}

export interface AmplificationResult {
  id: number
  experiment_id: number
  trial_number: number
  baseline_run_id: number | null
  defense_run_id: number | null
  control_name: string
  attack_type: string
  attack_intensity: string
  attack_workload: number
  workload_unit: string
  duration_seconds: number | null
  energy_attack_only: number
  energy_attack_defense: number
  additional_defense_energy: number
  defense_energy_amplification: number
  power_baseline: number | null
  power_defense: number | null
  power_amplification: number | null
  carbon_baseline_kg: number | null
  carbon_defense_kg: number | null
  amplification_carbon_kg: number | null
  carbon_intensity: number | null
  energy_provider: string | null
  measurement_mode: string | null
  environment_info: string | null
  software_version: string | null
  configuration_version: string | null
  num_paired_trials: number
  statistics: AmplificationStatistics | null
  formula_version: string
  created_at: string
}

export interface AmplificationListResponse {
  total: number
  items: AmplificationResult[]
}

export interface AnalyticsConfidenceInterval {
  level: number
  n: number
  status: string
  reason: string | null
  lower: number | null
  upper: number | null
  mean: number | null
  standard_error: number | null
  degrees_of_freedom: number | null
  critical_value: number | null
  method: string | null
  std_dev_convention: string | null
}

export interface AnalyticsEffectSize {
  name: string
  value: number | null
  status: string
  reason: string | null
  sample_count: number
  convention: string
}

export interface AnalyticsHypothesisTest {
  test_id: string
  test_name: string
  null_hypothesis: string
  alternative_hypothesis: string
  status: string
  reason: string | null
  statistic: number | null
  p_value: number | null
  sample_count: number
  excluded_zero_differences: number
  degrees_of_freedom: number | null
  significance_level: number
  alternative: string
  reject_null: boolean | null
  interpretation: string
  method: string
  method_notes: string
  effect_size: AnalyticsEffectSize | null
}

export interface AnalyticsGroup {
  group: Record<string, string>
  n: number
  statistics: StatisticsSummary
  confidence_interval: AnalyticsConfidenceInterval | null
  hypothesis_test: AnalyticsHypothesisTest | null
  warnings: string[]
}

export interface ResearchAnalyticsResult {
  analysis_id: string
  analysis_version: string
  source: string
  metric: string
  metric_category: string
  filters: Record<string, unknown>
  group_by: string[]
  n: number
  statistics: StatisticsSummary
  std_dev_convention: string
  groups: AnalyticsGroup[]
  confidence_interval: AnalyticsConfidenceInterval | null
  hypothesis_test: AnalyticsHypothesisTest | null
  paired_differences: number[] | null
  measurement_mode: string | null
  energy_provider: string | null
  warnings: string[]
  limitations: string[]
  created_at: string
}

export interface ResearchAnalyticsListResponse {
  total: number
  items: ResearchAnalyticsResult[]
}

export interface ResearchAnalyticsRequest {
  source: string
  metric: string
  filters?: Record<string, unknown>
  group_by?: string[]
  include_confidence_interval?: boolean
  confidence_level?: number
  hypothesis_test?: string | null
  alternative?: string
  significance_level?: number
}
