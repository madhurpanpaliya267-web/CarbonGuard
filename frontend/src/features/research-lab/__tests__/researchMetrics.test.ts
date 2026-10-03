import { describe, it, expect } from 'vitest'
import {
  CARBON_FORMULA,
  CARBON_PROVENANCE_NOTE,
  sumEnergyJoules,
  calculateCarbonKg,
  meanOf,
  maxOf,
  experimentModeCounts,
  countExperimentType,
  meanMarginalEnergy,
  meanMarginalCarbon,
  maxInteractionEffect,
  amplificationTrend,
  meanBy,
} from '../utils/researchMetrics'
import type {
  AmplificationResult,
  Experiment,
  ExperimentSummary,
  InteractionResult,
  MarginalEnergyResult,
} from '../types/research'

const summaryWith = (energies: number[]): ExperimentSummary =>
  ({
    measurements: energies.map((energy_joules) => ({ energy_joules })),
  }) as unknown as ExperimentSummary

const marginalItem = (marginal_energy_joules: number, marginal_carbon_kg: number | null) =>
  ({ marginal_energy_joules, marginal_carbon_kg }) as unknown as MarginalEnergyResult

const interactionItem = (interaction_effect: number) =>
  ({ interaction_effect }) as unknown as InteractionResult

const ampItem = (
  created_at: string,
  control_name: string,
  additional_defense_energy = 100,
  defense_energy_amplification = 0.2,
  attack_intensity = 'low',
) =>
  ({
    created_at,
    control_name,
    attack_intensity,
    additional_defense_energy,
    defense_energy_amplification,
  }) as unknown as AmplificationResult

describe('provenance constants', () => {
  it('states the carbon formula exactly', () => {
    expect(CARBON_FORMULA).toBe(
      'Carbon (kg) = energy (kWh) × carbon intensity (gCO₂/kWh) ÷ 1000',
    )
  })

  it('states that carbon is calculated, never measured', () => {
    expect(CARBON_PROVENANCE_NOTE).toContain(CARBON_FORMULA)
    expect(CARBON_PROVENANCE_NOTE).toContain('not live grid telemetry')
    expect(CARBON_PROVENANCE_NOTE).toContain('always calculated — never measured')
  })
})

describe('sumEnergyJoules', () => {
  it('returns null for missing or empty summaries', () => {
    expect(sumEnergyJoules(null)).toBeNull()
    expect(sumEnergyJoules(undefined)).toBeNull()
    expect(sumEnergyJoules(summaryWith([]))).toBeNull()
  })

  it('sums measurement energies', () => {
    expect(sumEnergyJoules(summaryWith([100, 250.5]))).toBe(350.5)
  })
})

describe('calculateCarbonKg', () => {
  it('applies the documented formula: 1 kWh at 475 gCO2/kWh = 0.475 kg', () => {
    expect(calculateCarbonKg(3_600_000, 475)).toBeCloseTo(0.475, 10)
  })

  it('returns null when energy or intensity is missing', () => {
    expect(calculateCarbonKg(null, 475)).toBeNull()
    expect(calculateCarbonKg(undefined, 475)).toBeNull()
    expect(calculateCarbonKg(3_600_000, null)).toBeNull()
    expect(calculateCarbonKg(3_600_000, undefined)).toBeNull()
  })

  it('returns zero for zero energy', () => {
    expect(calculateCarbonKg(0, 475)).toBe(0)
  })
})

describe('meanOf', () => {
  it('returns null when no usable values exist', () => {
    expect(meanOf([])).toBeNull()
    expect(meanOf([null, undefined, Number.NaN])).toBeNull()
    expect(meanOf([Number.POSITIVE_INFINITY])).toBeNull()
  })

  it('averages only finite numbers', () => {
    expect(meanOf([1, 2, 3])).toBe(2)
    expect(meanOf([null, 2, undefined, 4, Number.NaN])).toBe(3)
  })
})

describe('maxOf', () => {
  it('returns null when no usable values exist', () => {
    expect(maxOf([])).toBeNull()
    expect(maxOf([null, Number.NaN])).toBeNull()
  })

  it('returns the maximum finite value', () => {
    expect(maxOf([3, 9, 4])).toBe(9)
    expect(maxOf([Number.NaN, null, 7])).toBe(7)
  })
})

describe('experimentModeCounts', () => {
  it('counts measurement modes and labels missing modes as UNKNOWN', () => {
    const experiments = [
      { measurement_mode: 'ESTIMATED' },
      { measurement_mode: 'ESTIMATED' },
      { measurement_mode: null },
      { measurement_mode: 'MEASURED' },
    ] as unknown as Experiment[]
    expect(experimentModeCounts(experiments)).toEqual({
      ESTIMATED: 2,
      UNKNOWN: 1,
      MEASURED: 1,
    })
  })

  it('returns an empty record for no experiments', () => {
    expect(experimentModeCounts([])).toEqual({})
  })
})

describe('countExperimentType', () => {
  it('counts experiments of the requested type', () => {
    const experiments = [
      { experiment_type: 'MARGINAL_ENERGY' },
      { experiment_type: 'INTERACTION' },
      { experiment_type: 'MARGINAL_ENERGY' },
    ] as unknown as Experiment[]
    expect(countExperimentType(experiments, 'MARGINAL_ENERGY')).toBe(2)
    expect(countExperimentType(experiments, 'DEFENSE_AMPLIFICATION')).toBe(0)
  })
})

describe('meanMarginalEnergy / meanMarginalCarbon / maxInteractionEffect', () => {
  it('averages marginal energy values', () => {
    expect(meanMarginalEnergy([marginalItem(100, 0.1), marginalItem(200, 0.2)])).toBe(150)
  })

  it('returns null for an empty marginal list', () => {
    expect(meanMarginalEnergy([])).toBeNull()
  })

  it('averages marginal carbon values, ignoring nulls', () => {
    expect(
      meanMarginalCarbon([marginalItem(1, 0.2), marginalItem(2, 0.4)]),
    ).toBeCloseTo(0.3, 10)
    expect(meanMarginalCarbon([marginalItem(1, null)])).toBeNull()
  })

  it('finds the maximum interaction effect', () => {
    expect(maxInteractionEffect([interactionItem(5), interactionItem(-2)])).toBe(5)
    expect(maxInteractionEffect([])).toBeNull()
  })
})

describe('amplificationTrend', () => {
  it('sorts points ascending by creation time without mutating the input', () => {
    const later = ampItem('2026-01-02T00:00:00Z', 'firewall', 140)
    const earlier = ampItem('2026-01-01T00:00:00Z', 'ids', 60)
    const input = [later, earlier]

    const trend = amplificationTrend(input)

    expect(trend.map((point) => point.created_at)).toEqual([
      '2026-01-01T00:00:00Z',
      '2026-01-02T00:00:00Z',
    ])
    expect(trend[0].control_name).toBe('ids')
    expect(trend[0].additional_defense_energy).toBe(60)
    expect(trend[1].control_name).toBe('firewall')
    expect(trend[1].defense_energy_amplification).toBe(0.2)
    expect(trend[0].attack_intensity).toBe('low')
    expect(input[0]).toBe(later)
  })

  it('returns an empty array for no results', () => {
    expect(amplificationTrend([])).toEqual([])
  })
})

describe('meanBy', () => {
  it('groups, averages and sorts buckets, skipping unusable values', () => {
    const rows = [
      { control: 'firewall', value: 10 },
      { control: 'firewall', value: 20 },
      { control: 'ids', value: null },
      { control: 'ids', value: 6 },
      { control: 'waf', value: Number.NaN },
    ]
    expect(meanBy(rows, (row) => row.control, (row) => row.value)).toEqual([
      { bucket: 'firewall', mean: 15, observations: 2 },
      { bucket: 'ids', mean: 6, observations: 1 },
    ])
  })

  it('returns an empty array for no rows', () => {
    expect(meanBy([], (row: { control: string }) => row.control, () => 0)).toEqual([])
  })
})
