import { describe, it, expect, beforeEach, vi } from 'vitest'
import { screen, waitFor, fireEvent } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import ResearchLabPage from '../components/ResearchLabPage'
import type {
  AmplificationResult,
  AttackProfile,
  EnergyMeasurement,
  Experiment,
  ExperimentRun,
  ExperimentSummary,
  InteractionResult,
  MarginalEnergyResult,
  ResearchAnalyticsResult,
  SecurityControl,
  SecurityEffectiveness,
} from '../types/research'

const experiment: Experiment = {
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

const run: ExperimentRun = {
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

const measurement: EnergyMeasurement = {
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

const securityEffect: SecurityEffectiveness = {
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

const summary: ExperimentSummary = {
  experiment,
  runs: [run],
  measurements: [measurement],
  security_effects: [securityEffect],
}

const attackProfile: AttackProfile = {
  attack_type: 'ddos',
  display_name: 'DDoS Flood',
  description: 'Synthetic flood profile',
  workload_unit: 'req/s',
  intensity_levels: ['LOW', 'MEDIUM', 'HIGH'],
  supported_controls: ['waf'],
  config_version: 'cfg-1',
}

const securityControl: SecurityControl = {
  control_id: 'waf',
  display_name: 'Web Application Firewall',
  category: 'network',
  description: 'Filters synthetic traffic',
  supported_attack_types: ['ddos'],
  config_parameters: {},
  enabled_by_default: true,
}

const marginal: MarginalEnergyResult = {
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
  measurement_mode: 'ESTIMATED',
  formula_version: 'marginal-energy-v1',
  created_at: '2026-01-01T10:06:00Z',
}

const interaction: InteractionResult = {
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
  formula_version: 'interaction-v1',
  created_at: '2026-01-01T10:10:00Z',
  security_effectiveness: null,
}

const amplification: AmplificationResult = {
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
  statistics: {
    amplification_energy: { mean: 350, median: 348, std_dev: 12, min: 330, max: 372, count: 5 },
    amplification_ratio: { mean: 3.5, median: 3.48, std_dev: 0.1, min: 3.3, max: 3.72, count: 5 },
    power_amplification: { mean: 5.8, median: 5.7, std_dev: 0.2, min: 5.5, max: 6.1, count: 5 },
    carbon_amplification: { mean: 0.00004, median: 0.00004, std_dev: 0, min: 0.00004, max: 0.00004, count: 5 },
    formula_version: 'amplification-v1',
  },
  formula_version: 'amplification-v1',
  created_at: '2026-01-01T10:15:00Z',
}

const analyticsResult: ResearchAnalyticsResult = {
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

function jsonResponse(data: unknown) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(data) })
}

function mockResearchFetch() {
  globalThis.fetch = vi.fn().mockImplementation((input: string, init?: RequestInit) => {
    const url = String(input)
    const method = init?.method ?? 'GET'

    if (url.includes('/summary')) return jsonResponse(summary)
    if (url.includes('/experiments')) return jsonResponse({ total: 1, items: [experiment] })
    if (url.includes('/attacks')) return jsonResponse({ attacks: [attackProfile] })
    if (url.includes('/controls')) return jsonResponse({ controls: [securityControl] })
    if (url.includes('/marginal-energy')) return jsonResponse({ total: 1, items: [marginal] })
    if (url.includes('/interaction-effects'))
      return jsonResponse({ total: 1, items: [interaction] })
    if (url.includes('/defense-energy-amplification'))
      return jsonResponse({ total: 1, items: [amplification] })
    if (url.includes('/analytics') && method === 'POST') return jsonResponse(analyticsResult)
    if (url.includes('/analytics')) return jsonResponse({ total: 1, items: [analyticsResult] })
    return jsonResponse({})
  })
}

describe('ResearchLabPage', () => {
  beforeEach(() => {
    mockResearchFetch()
  })

  it('shows loading indicator while research data loads', () => {
    render(<ResearchLabPage />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('renders page header and simulation badges', async () => {
    render(<ResearchLabPage />)
    await waitFor(() => {
      expect(screen.getByText('Research Lab')).toBeInTheDocument()
      expect(screen.getByText('SIMULATED DATA')).toBeInTheDocument()
      expect(screen.getByText('RULE-BASED ANALYTICS')).toBeInTheDocument()
    })
  })

  it('renders overview metrics after loading', async () => {
    render(<ResearchLabPage />)
    await waitFor(() => {
      expect(screen.getByText('Research Overview')).toBeInTheDocument()
      expect(screen.getByText('Total Experiments')).toBeInTheDocument()
      expect(screen.getByText('ESTIMATED ENERGY')).toBeInTheDocument()
    })
  })

  it('renders the Phase 5 marginal energy section', async () => {
    render(<ResearchLabPage />)
    await waitFor(() => {
      expect(screen.getByText('Marginal Energy Attribution (Phase 5)')).toBeInTheDocument()
      expect(screen.getByText('Marginal Energy by Attack Intensity')).toBeInTheDocument()
    })
  })

  it('renders the Phase 6 interaction section with interpretation', async () => {
    render(<ResearchLabPage />)
    await waitFor(() => {
      expect(screen.getByText('Security-Control Interaction (Phase 6)')).toBeInTheDocument()
      expect(screen.getByText('super-additive')).toBeInTheDocument()
      expect(screen.getByText('Interaction Effect by Control Pair')).toBeInTheDocument()
    })
  })

  it('renders the Phase 7 amplification section with stored statistics', async () => {
    render(<ResearchLabPage />)
    await waitFor(() => {
      expect(screen.getByText('Defense Energy Amplification (Phase 7)')).toBeInTheDocument()
      expect(screen.getByText('Defense Energy Amplification by Control')).toBeInTheDocument()
      expect(screen.getByText('Trials (paired)')).toBeInTheDocument()
    })
  })

  it('renders the Phase 8 statistics form and stored analyses', async () => {
    render(<ResearchLabPage />)
    await waitFor(() => {
      expect(screen.getByText('Statistical Analysis (Phase 8)')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /run analysis/i })).toBeInTheDocument()
      expect(screen.getByText('Stored Analyses')).toBeInTheDocument()
    })
  })

  it('runs an analysis and renders confidence interval and test results', async () => {
    render(<ResearchLabPage />)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /run analysis/i })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /run analysis/i }))

    await waitFor(() => {
      expect(screen.getByText('Analysis Result')).toBeInTheDocument()
      expect(screen.getByText('Confidence Interval')).toBeInTheDocument()
      expect(screen.getByText('Hypothesis Test')).toBeInTheDocument()
      expect(screen.getByText('reject null')).toBeInTheDocument()
    })
  })

  it('loads experiment trial detail after selecting an experiment', async () => {
    render(<ResearchLabPage />)
    await waitFor(() => {
      expect(screen.getByLabelText('Experiment')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText('Experiment'), {
      target: { value: 'exp-uuid-1' },
    })

    await waitFor(() => {
      expect(screen.getByText('DDoS Baseline vs WAF')).toBeInTheDocument()
      expect(screen.getByText('1 of 1 runs shown')).toBeInTheDocument()
    })
  })

  it('renders reference catalogues for attacks and controls', async () => {
    render(<ResearchLabPage />)
    await waitFor(() => {
      expect(screen.getByText('Synthetic Attack Profiles')).toBeInTheDocument()
      expect(screen.getByText('DDoS Flood')).toBeInTheDocument()
      expect(screen.getByText('Web Application Firewall')).toBeInTheDocument()
    })
  })

  it('shows a failed-source error when research requests fail', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error('Network error'))
    render(<ResearchLabPage />)

    await waitFor(() => {
      expect(
        screen.getByText('Some research sources could not be loaded'),
      ).toBeInTheDocument()
    })
  })
})
