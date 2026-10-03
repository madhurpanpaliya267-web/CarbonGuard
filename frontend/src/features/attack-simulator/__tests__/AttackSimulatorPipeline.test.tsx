import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { render } from '@/test/page-test-utils'
import AttackSimulatorPage from '../components/AttackSimulatorPage'
import { api } from '@/shared/utils/api'
import type { OrchestrationResult } from '@/shared/types/common'

vi.mock('@/shared/utils/api', () => ({
  api: {
    runPipeline: vi.fn(),
  },
}))

const runPipeline = vi.mocked(api.runPipeline)

function makeResult(overrides: Partial<OrchestrationResult> = {}): OrchestrationResult {
  const base: OrchestrationResult = {
    status: 'completed',
    event: {
      id: 1,
      event_uuid: 'evt-uuid-1',
      timestamp: '2026-10-02T10:00:00',
      event_type: 'ddos',
      severity: 'HIGH',
      source_ip: '192.168.1.100',
      target_ip: '10.0.0.1',
      target_port: 443,
      confidence: 0.9,
      status: 'detected',
      detection_method: 'Traffic anomaly detection',
      description: 'Distributed Denial of Service attack detected',
      risk_score: 71.5,
      estimated_workload_cpu: 60,
      estimated_energy_kwh: 0.03,
      estimated_co2_kg: 0.01,
    },
    attack: {
      attack_type: 'ddos',
      intensity: null,
      duration_seconds: 60,
      description: 'Distributed Denial of Service attack detected',
      detection_method: 'Traffic anomaly detection',
      detection_confidence: 0.9,
      detection_estimate: {
        energy_kwh: 0.03,
        co2_kg: 0.01,
        source: 'threat_detector_profile',
        note: 'detection-stage estimate',
      },
      workload: { cpu_seconds: 60, memory_mb: 256, estimated_duration_seconds: 90 },
      attack_profile: null,
      synthetic: true,
    },
    threat: {
      id: 1,
      threat_uuid: 'thr-uuid-1',
      event_id: 1,
      threat_type: 'ddos',
      severity: 'HIGH',
      confidence: 0.9,
      risk_score: 71.5,
      status: 'active',
      detected_at: '2026-10-02T10:00:00',
      resolved_at: null,
      explanation: 'Synthetic explanation',
      recommended_action: 'Activate rate limiting',
      anomaly_level: 0.6,
    },
    risk: {
      risk_score: 71.5,
      severity: 'HIGH',
      confidence: 0.9,
      factors: [
        { factor: 'Attack Severity', weight: 0.3, value: 'HIGH', contribution: 22.5 },
      ],
    },
    defense: {
      status: 'selected',
      basis: 'rule_based',
      tier: 'HIGH',
      selected: ['firewall', 'ids', 'ips', 'waf'],
      available: ['firewall', 'ids', 'ips', 'waf', 'siem'],
      reason: 'Rule-based tier HIGH: selected 4 of 5 controls (registry order, not an optimality claim)',
      risk_score: 71.5,
      control_details: [
        {
          control_id: 'firewall',
          display_name: 'Firewall',
          category: 'network',
          description: 'Network traffic filtering and access control',
          supported_attack_types: ['ddos'],
          config_parameters: {},
          enabled_by_default: true,
        },
      ],
      activated: true,
      response: 'Activate rate limiting and engage upstream filtering immediately.',
      recommendation: {
        recommendation: 'Activate rate limiting and engage upstream filtering immediately.',
        priority: 'high',
        reason: 'Detected ddos with risk score 71.5/100',
        expected_security_impact: 'Mitigate DDoS traffic and protect target services',
        expected_carbon_impact: 'Increased monitoring workload may increase energy use temporarily',
        confidence: 0.9,
        factors: [],
      },
    },
    security_controls: ['firewall', 'ids', 'ips', 'waf'],
    energy: {
      status: 'completed',
      energy_joules: 7200,
      energy_kwh: 0.002,
      power_watts: 120,
      duration_seconds: 60,
      measurement_mode: 'ESTIMATED',
      measurement_source: 'estimated',
      provider: 'estimated',
      security_controls_active: 4,
      estimated: true,
      reason: null,
    },
    carbon: {
      status: 'completed',
      reason: null,
      energy_kwh: 0.002,
      carbon_intensity: 475,
      renewable_pct: 25,
      gross_co2_kg: 0.00095,
      renewable_offset_kg: 0.0002375,
      net_co2_kg: 0.0007125,
      carbon_basis: 'calculated_from_estimated_energy',
      measurement_mode: 'ESTIMATED',
      calculation_breakdown: 'Energy: 0.002 kWh x Carbon Intensity: 475 gCO2/kWh = Gross CO2: 0.95g.',
    },
    comparison: {
      status: 'available',
      reason: null,
      basis: 'paired_estimated_same_provider',
      measurement_mode: 'ESTIMATED',
      baseline_energy_kwh: 0.00168,
      defense_energy_kwh: 0.002,
      energy_difference_kwh: 0.00032,
      baseline_carbon_kg: 0.0006,
      defense_carbon_kg: 0.0007125,
      carbon_difference_kg: 0.0001125,
      direction: 'additional_energy',
      interpretation: 'Activated controls add energy/carbon overhead relative to the no-controls baseline',
    },
    research: {
      status: 'not_requested',
      reason: null,
      experiment_uuid: null,
      run_id: null,
      trial_number: null,
    },
    analytics: {
      status: 'completed',
      recorded: false,
      feeds: ['security_stats', 'threat_stats', 'dashboard'],
      detail: 'Persisted events/threats aggregate through security stats and dashboard.',
    },
    provenance: {
      data_classification: 'SYNTHETIC',
      simulated_attack: true,
      measurement_mode: 'ESTIMATED',
      measurement_source: 'estimated',
      carbon_basis: 'calculated_from_estimated_energy',
      energy_engine: 'energy_provider:estimated',
      carbon_engine: 'calculate_carbon',
      control_selection: 'rule_based',
      pipeline_version: '13.0.0',
      generated_at: '2026-10-02T10:00:00',
      notes: 'Synthetic attack data; energy is ESTIMATED unless a hardware provider reports MEASURED.',
    },
    stages: [
      { step: 'Attack Simulation', status: 'completed', detail: 'Simulated ddos attack' },
      { step: 'Threat Detection', status: 'completed', detail: 'Classified as ddos' },
      { step: 'Defense Selection', status: 'completed', detail: '4 control(s) selected (HIGH, rule-based)' },
      { step: 'Defense Energy Measurement', status: 'completed', detail: '0.002 kWh [ESTIMATED]' },
      { step: 'Defense Carbon Calculation', status: 'completed', detail: 'net 0.0007125 kg CO2 [calculated_from_estimated_energy]' },
      { step: 'Analytics', status: 'completed', detail: 'Run persisted to feeds' },
    ],
    warnings: [],
  }
  return { ...base, ...overrides }
}

async function runSimulate() {
  const buttons = screen.getAllByText('Simulate')
  await userEvent.click(buttons[0])
}

describe('AttackSimulatorPage integrated pipeline', () => {
  beforeEach(() => {
    runPipeline.mockReset()
  })

  it('renders an integrated result summary from the pipeline', async () => {
    runPipeline.mockResolvedValue(makeResult())
    render(<AttackSimulatorPage />)
    await runSimulate()

    expect(await screen.findByText('Result Summary')).toBeInTheDocument()
    expect(screen.getByText('Pipeline Flow')).toBeInTheDocument()

    expect(screen.getAllByText('ddos').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Activate rate limiting and engage upstream filtering immediately.').length).toBeGreaterThan(0)
    expect(screen.getByText('4 controls')).toBeInTheDocument()
    expect(screen.getAllByText('firewall').length).toBeGreaterThan(0)
    expect(screen.getAllByText('0.002000 kWh').length).toBeGreaterThan(0)
    expect(screen.getAllByText(/kg CO2 \(net\)/).length).toBeGreaterThan(0)
    expect(screen.getAllByText('HIGH').length).toBeGreaterThan(0)
  })

  it('shows measurement mode and carbon basis labels', async () => {
    runPipeline.mockResolvedValue(makeResult())
    render(<AttackSimulatorPage />)
    await runSimulate()

    expect(await screen.findByText('Result Summary')).toBeInTheDocument()
    expect(screen.getAllByText('ESTIMATED').length).toBeGreaterThan(0)
    expect(screen.getAllByText('calculated_from_estimated_energy').length).toBeGreaterThan(0)
    expect(screen.getAllByText('SYNTHETIC').length).toBeGreaterThan(0)
  })

  it('shows research run id when a run was recorded', async () => {
    runPipeline.mockResolvedValue(
      makeResult({
        research: {
          status: 'recorded',
          reason: null,
          experiment_uuid: 'exp-1',
          run_id: 7,
          trial_number: 2,
        },
        analytics: {
          status: 'completed',
          recorded: true,
          feeds: ['research_summary'],
          detail: 'recorded',
        },
      }),
    )
    render(<AttackSimulatorPage />)
    await runSimulate()

    expect(await screen.findByText(/run #7 \(trial 2\)/)).toBeInTheDocument()
  })

  it('shows API error without crashing', async () => {
    runPipeline.mockRejectedValue(new Error('HTTP 500'))
    render(<AttackSimulatorPage />)
    await runSimulate()

    expect(await screen.findByText('Pipeline Run Failed')).toBeInTheDocument()
    expect(screen.getByText('HTTP 500')).toBeInTheDocument()
    expect(screen.queryByText('Result Summary')).not.toBeInTheDocument()
  })

  it('handles missing energy, carbon and comparison metrics', async () => {
    runPipeline.mockResolvedValue(
      makeResult({
        status: 'partial',
        energy: {
          status: 'unavailable',
          energy_joules: null,
          energy_kwh: null,
          power_watts: null,
          duration_seconds: 60,
          measurement_mode: null,
          measurement_source: null,
          provider: 'estimated',
          security_controls_active: 4,
          estimated: null,
          reason: 'Energy measurement unavailable: provider down',
        },
        carbon: {
          status: 'unavailable',
          reason: 'Carbon unavailable because energy measurement is unavailable',
          energy_kwh: null,
          carbon_intensity: null,
          renewable_pct: null,
          gross_co2_kg: null,
          renewable_offset_kg: null,
          net_co2_kg: null,
          carbon_basis: null,
          measurement_mode: null,
          calculation_breakdown: null,
        },
        comparison: {
          status: 'unavailable',
          reason: 'Energy or carbon unavailable; no valid baseline/defense comparison',
          basis: null,
          measurement_mode: null,
          baseline_energy_kwh: null,
          defense_energy_kwh: null,
          energy_difference_kwh: null,
          baseline_carbon_kg: null,
          defense_carbon_kg: null,
          carbon_difference_kg: null,
          direction: null,
          interpretation: null,
        },
        warnings: [{ stage: 'Energy', reason: 'Energy measurement unavailable: provider down' }],
      }),
    )
    render(<AttackSimulatorPage />)
    await runSimulate()

    expect(await screen.findByText('Result Summary')).toBeInTheDocument()
    expect(screen.getAllByText(/Not available — Energy measurement unavailable: provider down/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/Carbon unavailable because energy measurement is unavailable/).length).toBeGreaterThan(0)
    expect(screen.getByText(/no valid baseline\/defense comparison/)).toBeInTheDocument()
    expect(screen.getByText('Pipeline Warnings')).toBeInTheDocument()
    expect(screen.getAllByText('UNAVAILABLE').length).toBeGreaterThan(0)
    expect(screen.queryByText('0.002000 kWh')).not.toBeInTheDocument()
  })

  it('shows comparison direction without claiming savings for added overhead', async () => {
    runPipeline.mockResolvedValue(makeResult())
    render(<AttackSimulatorPage />)
    await runSimulate()

    expect(await screen.findByText('Baseline vs Defense Comparison')).toBeInTheDocument()
    expect(screen.getByText('Energy Difference')).toBeInTheDocument()
    expect(screen.queryByText('Energy Saved')).not.toBeInTheDocument()
    expect(screen.queryByText('Carbon Saved')).not.toBeInTheDocument()
  })

  it('does not run the pipeline until simulate is clicked', () => {
    render(<AttackSimulatorPage />)
    expect(runPipeline).not.toHaveBeenCalled()
    expect(screen.queryByText('Result Summary')).not.toBeInTheDocument()
  })

  it('passes the selected attack type to the pipeline API', async () => {
    runPipeline.mockResolvedValue(makeResult())
    render(<AttackSimulatorPage />)
    const buttons = screen.getAllByText('Simulate')
    await userEvent.click(buttons[2])

    await waitFor(() => expect(runPipeline).toHaveBeenCalledWith('port_scan'))
  })
})
