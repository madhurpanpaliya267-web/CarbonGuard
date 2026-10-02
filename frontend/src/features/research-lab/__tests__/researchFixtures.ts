import { vi } from 'vitest'
import type {
  AmplificationResult,
  AttackProfile,
  EnergyMeasurement,
  Experiment,
  ExperimentRun,
  ExperimentStatus,
  ExperimentSummary,
  InteractionResult,
  MarginalEnergyResult,
  ResearchAnalyticsResult,
  ResearchExportPayload,
  ResearchMetrics,
  ResearchSummary,
  SecurityControl,
  SecurityEffectiveness,
} from '../types/research'

export const experiment: Experiment = {
  id: 1,
  experiment_uuid: 'exp-uuid-1',
  name: 'DDoS Baseline vs WAF',
  description: 'Phase 5 marginal energy trial',
  experiment_type: 'MARGINAL_ENERGY',
  attack_type: 'ddos',
  attack_intensity: 'MEDIUM',
  workload_profile: 'steady',
  security_controls: 'waf',
  measurement_mode: 'ESTIMATED',
  duration_seconds: 60,
  num_trials: 5,
  carbon_intensity: 420,
  renewable_pct: 30,
  software_version: 'v0.8',
  configuration_version: 'cfg-1',
  random_seed: 42,
  status: 'COMPLETED',
  created_at: '2026-01-01T10:00:00Z',
  completed_at: '2026-01-01T10:05:00Z',
  notes: null,
}

export const run: ExperimentRun = {
  id: 11,
  run_uuid: 'run-uuid-0011',
  experiment_id: 1,
  trial_number: 1,
  attack_type: 'ddos',
  attack_intensity: 'MEDIUM',
  attack_parameters: null,
  workload_profile: 'steady',
  workload_value: 100,
  workload_unit: 'req/s',
  security_controls: 'waf',
  control_count: 1,
  measurement_mode: 'ESTIMATED',
  start_time: '2026-01-01T10:01:00Z',
  end_time: '2026-01-01T10:02:00Z',
  duration_seconds: 60,
  status: 'COMPLETED',
  error_message: null,
}

export const measurement: EnergyMeasurement = {
  id: 101,
  run_id: 11,
  energy_joules: 1200.5,
  power_watts: 20.008,
  duration_seconds: 60,
  cpu_usage_pct: 45,
  memory_usage_pct: 60,
  network_usage_mbps: 12,
  source: 'estimator',
  measurement_mode: 'ESTIMATED',
  timestamp: '2026-01-01T10:02:00Z',
}

export const securityEffect: SecurityEffectiveness = {
  id: 201,
  run_id: 11,
  detection_rate: 0.92,
  detection_latency_ms: 120,
  false_positive_rate: 0.03,
  mitigation_time_ms: 450,
  threat_severity: 'MEDIUM',
  security_response: 'blocked',
  security_score: 88,
  controls_active: 'waf',
  controls_config: null,
}

export const summary: ExperimentSummary = {
  experiment,
  runs: [run],
  measurements: [measurement],
  security_effects: [securityEffect],
}

export const attackProfile: AttackProfile = {
  attack_type: 'ddos',
  display_name: 'DDoS Flood',
  description: 'Synthetic flood profile',
  workload_unit: 'req/s',
  intensity_levels: ['LOW', 'MEDIUM', 'HIGH'],
  supported_controls: ['waf'],
  config_version: 'cfg-1',
}

export const securityControl: SecurityControl = {
  control_id: 'waf',
  display_name: 'Web Application Firewall',
  category: 'network',
  description: 'Filters synthetic traffic',
  supported_attack_types: ['ddos'],
  config_parameters: {},
  enabled_by_default: true,
}

export const marginal: MarginalEnergyResult = {
  id: 1,
  experiment_id: 1,
  baseline_run_id: 11,
  security_run_id: 12,
  attack_type: 'ddos',
  attack_intensity: 'MEDIUM',
  workload_value: 100,
  workload_unit: 'req/s',
  duration_seconds: 60,
  baseline_energy_joules: 1000,
  security_energy_joules: 1350,
  marginal_energy_joules: 350,
  baseline_power_watts: 16.667,
  security_power_watts: 22.5,
  marginal_power_watts: 5.833,
  baseline_energy_kwh: 0.000278,
  security_energy_kwh: 0.000375,
  marginal_energy_kwh: 0.000097,
  baseline_carbon_kg: 0.000117,
  security_carbon_kg: 0.000158,
  marginal_carbon_kg: 0.000041,
  carbon_intensity: 420,
  marginal_carbon_per_workload: {
    value_kg: 0.00000041,
    unit: 'kg/req/s',
    status: 'available',
    reason: null,
  },
  carbon_basis: 'calculated_from_estimated_energy',
  measurement_mode: 'ESTIMATED',
  formula_version: 'marginal-energy-v1',
  created_at: '2026-01-01T10:06:00Z',
}

export const interaction: InteractionResult = {
  id: 5,
  experiment_id: 1,
  trial_number: 2,
  baseline_run_id: 11,
  control_a_run_id: 13,
  control_b_run_id: 14,
  combined_run_id: 15,
  control_a: 'waf',
  control_b: 'ids',
  attack_type: 'ddos',
  attack_intensity: 'MEDIUM',
  workload_value: 100,
  workload_unit: 'req/s',
  duration_seconds: 60,
  energy_baseline: 1000,
  energy_a: 1200,
  energy_b: 1150,
  energy_ab: 2500,
  interaction_effect: 150,
  interaction_index: 0.065,
  interpretation: 'super-additive',
  power_baseline: 16.667,
  power_a: 20,
  power_b: 19.167,
  power_ab: 41.667,
  interaction_power: 2.5,
  carbon_baseline_kg: 0.000117,
  carbon_a_kg: 0.00014,
  carbon_b_kg: 0.000134,
  carbon_ab_kg: 0.000291,
  interaction_carbon_kg: 0.000017,
  carbon_intensity: 420,
  energy_provider: 'simulated-grid',
  measurement_mode: 'ESTIMATED',
  interaction_carbon_per_workload: {
    value_kg: 0.00000017,
    unit: 'kg/req/s',
    status: 'available',
    reason: null,
  },
  carbon_basis: 'calculated_from_estimated_energy',
  formula_version: 'interaction-v1',
  created_at: '2026-01-01T10:10:00Z',
  security_effectiveness: null,
}

export const amplification: AmplificationResult = {
  id: 3,
  experiment_id: 1,
  trial_number: 3,
  baseline_run_id: 11,
  defense_run_id: 16,
  control_name: 'waf',
  attack_type: 'ddos',
  attack_intensity: 'MEDIUM',
  attack_workload: 100,
  workload_unit: 'req/s',
  duration_seconds: 60,
  energy_attack_only: 1400,
  energy_attack_defense: 1750,
  additional_defense_energy: 350,
  defense_energy_amplification: 3.5,
  power_baseline: 23.333,
  power_defense: 29.167,
  power_amplification: 5.833,
  carbon_baseline_kg: 0.000164,
  carbon_defense_kg: 0.000205,
  amplification_carbon_kg: 0.000041,
  carbon_intensity: 420,
  energy_provider: 'simulated-grid',
  measurement_mode: 'ESTIMATED',
  environment_info: null,
  software_version: 'v0.8',
  configuration_version: 'cfg-1',
  num_paired_trials: 5,
  defense_carbon_per_workload: {
    value_kg: 0.00000041,
    unit: 'kg/req/s',
    status: 'available',
    reason: null,
  },
  carbon_basis: 'calculated_from_estimated_energy',
  statistics: {
    amplification_energy: { mean: 350, median: 348, std_dev: 12, min: 330, max: 372, count: 5 },
    amplification_ratio: { mean: 3.5, median: 3.48, std_dev: 0.1, min: 3.3, max: 3.72, count: 5 },
    power_amplification: { mean: 5.8, median: 5.7, std_dev: 0.2, min: 5.5, max: 6.1, count: 5 },
    carbon_amplification: {
      mean: 0.00004,
      median: 0.00004,
      std_dev: 0,
      min: 0.00004,
      max: 0.00004,
      count: 5,
    },
    formula_version: 'amplification-v1',
  },
  formula_version: 'amplification-v1',
  created_at: '2026-01-01T10:15:00Z',
}

export const analyticsResult: ResearchAnalyticsResult = {
  analysis_id: 'analysis-1',
  analysis_version: 'research-analytics-v1',
  source: 'marginal',
  metric: 'marginal_energy_joules',
  metric_category: 'difference',
  filters: {},
  group_by: [],
  n: 8,
  statistics: { mean: 340.5, median: 338, std_dev: 12.4, min: 320, max: 365, count: 8 },
  std_dev_convention: 'population',
  groups: [],
  confidence_interval: {
    level: 0.95,
    n: 8,
    status: 'ok',
    reason: null,
    lower: 330.1,
    upper: 350.9,
    mean: 340.5,
    standard_error: 4.38,
    degrees_of_freedom: 7,
    critical_value: 2.365,
    method: 't_interval',
    std_dev_convention: 'population',
  },
  hypothesis_test: {
    test_id: 'paired_t',
    test_name: 'Paired t-test',
    null_hypothesis: 'mean difference = 0',
    alternative_hypothesis: 'mean difference != 0',
    status: 'ok',
    reason: null,
    statistic: 4.12,
    p_value: 0.004,
    sample_count: 8,
    excluded_zero_differences: 0,
    degrees_of_freedom: 7,
    significance_level: 0.05,
    alternative: 'two-sided',
    reject_null: true,
    interpretation: 'reject_null',
    method: 'paired_t',
    method_notes: 'Requires approximately normal paired differences.',
    effect_size: {
      name: 'cohens_dz',
      value: 1.46,
      status: 'ok',
      reason: null,
      sample_count: 8,
      convention: 'small 0.2 / medium 0.5 / large 0.8',
    },
  },
  paired_differences: [350, 340],
  measurement_mode: 'ESTIMATED',
  energy_provider: 'simulated-grid',
  warnings: [],
  limitations: ['Synthetic simulation data.'],
  created_at: '2026-01-01T10:20:00Z',
}

export const researchSummary: ResearchSummary = {
  total_experiments: 1,
  total_trials: 1,
  attack_types: ['ddos'],
  security_controls: ['waf'],
  measurement_modes: ['ESTIMATED'],
  estimated_trials: 1,
  measured_trials: 0,
  marginal_energy_observations: 1,
  interaction_observations: 1,
  amplification_observations: 1,
  carbon_observations: 1,
}

function block(status: 'available' | 'unavailable' = 'available', reason: string | null = null) {
  return {
    status,
    reason,
    unit: 'J',
    observation_count: 1,
    statistics: status === 'available'
      ? { mean: 350, median: 350, std_dev: 12, min: 330, max: 372, count: 1 }
      : null,
  }
}

export const researchMetrics: ResearchMetrics = {
  marginal_energy: block(),
  marginal_power: block(),
  marginal_carbon: { ...block(), unit: 'kg' },
  interaction_effect: block(),
  amplification_energy: block(),
  amplification_ratio: { ...block(), unit: 'ratio' },
  std_dev_convention: 'population',
}

export const experimentStatus: ExperimentStatus = {
  experiment_uuid: experiment.experiment_uuid,
  status: 'COMPLETED',
  total_runs: 1,
  completed_runs: 1,
  failed_runs: 0,
}

export const exportPayload: ResearchExportPayload = {
  exported_at: '2026-01-01T11:00:00Z',
  record_counts: {
    experiments: 1,
    marginal_energy: 1,
    interaction_effects: 1,
    defense_amplification: 1,
  },
  experiments: [experiment],
  marginal_energy: [marginal],
  interaction_effects: [interaction],
  defense_amplification: [amplification],
}

export const optimizerComparison = {
  before: { energy_kwh: 10, co2_kg: 4.75 },
  after: { energy_kwh: 9, co2_kg: 4.275 },
  comparison: { energy_saved: 1, co2_saved: 0.475, reduction_pct: 10 },
}

export function ok(data: unknown) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(data) })
}

export function text(body: string) {
  return Promise.resolve({ ok: true, text: () => Promise.resolve(body) })
}

export interface FetchMockOptions {
  csvBody?: string
  exportCounts?: ResearchExportPayload['record_counts']
  fail?: string[]
}

/**
 * Routes every research endpoint used by the Phase 12 pages to fixture data.
 * `fail` lists URL substrings that should reject, for error-state tests.
 */
export function installFetchMock(options: FetchMockOptions = {}) {
  const failures = options.fail ?? []

  globalThis.fetch = vi.fn().mockImplementation((input: string, init?: RequestInit) => {
    const raw = String(input)
    const path = raw.split('?')[0]
    const method = init?.method ?? 'GET'

    if (failures.some((needle) => raw.includes(needle))) {
      return Promise.reject(new Error('Network error'))
    }

    if (path.endsWith('/optimizer/comparison')) return ok(optimizerComparison)
    if (path.endsWith('/research/summary')) return ok(researchSummary)
    if (path.endsWith('/research/metrics')) return ok(researchMetrics)

    if (path.endsWith('/export/csv')) {
      return text(options.csvBody ?? 'attack_type,marginal_energy_joules\nddos,350')
    }
    if (path.endsWith('/export/json')) {
      return ok({
        ...exportPayload,
        record_counts: options.exportCounts ?? exportPayload.record_counts,
      })
    }

    if (path.endsWith('/experiments')) {
      return method === 'POST' ? ok(experiment) : ok({ total: 1, items: [experiment] })
    }
    if (path.endsWith('/execute')) return ok(experiment)
    if (path.endsWith('/status')) return ok(experimentStatus)
    if (path.endsWith('/runs')) return ok({ total: 1, items: [run] })
    if (path.endsWith('/summary')) return ok(summary)
    if (path.includes('/experiments/')) return ok(experiment)

    if (path.endsWith('/attacks')) return ok({ attacks: [attackProfile] })
    if (path.endsWith('/controls')) return ok({ controls: [securityControl] })
    if (path.endsWith('/marginal-energy')) return ok({ total: 1, items: [marginal] })
    if (path.endsWith('/interaction-effects')) return ok({ total: 1, items: [interaction] })
    if (path.endsWith('/defense-energy-amplification')) return ok({ total: 1, items: [amplification] })
    if (path.endsWith('/analytics') && method === 'POST') return ok(analyticsResult)
    if (path.endsWith('/analytics')) return ok({ total: 1, items: [analyticsResult] })

    return ok({})
  })

  return globalThis.fetch as ReturnType<typeof vi.fn>
}
