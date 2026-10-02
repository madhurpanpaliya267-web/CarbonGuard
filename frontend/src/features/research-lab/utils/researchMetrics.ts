import type {
  AmplificationResult,
  Experiment,
  ExperimentSummary,
  InteractionResult,
  MarginalEnergyResult,
} from '../types/research'

export const CARBON_FORMULA =
  'Carbon (kg) = energy (kWh) × carbon intensity (gCO₂/kWh) ÷ 1000'

export const CARBON_PROVENANCE_NOTE = `${CARBON_FORMULA}. Carbon intensity is a configured value, not live grid telemetry, so carbon is always calculated — never measured.`

export function sumEnergyJoules(summary: ExperimentSummary | null | undefined): number | null {
  if (!summary || summary.measurements.length === 0) return null
  let total = 0
  summary.measurements.forEach((measurement) => {
    total += measurement.energy_joules
  })
  return total
}

export function calculateCarbonKg(
  energyJoules: number | null | undefined,
  carbonIntensity: number | null | undefined,
): number | null {
  if (energyJoules === null || energyJoules === undefined) return null
  if (carbonIntensity === null || carbonIntensity === undefined) return null
  const energyKwh = energyJoules / 3_600_000
  return (energyKwh * carbonIntensity) / 1000
}

export function meanOf(values: Array<number | null | undefined>): number | null {
  const usable = values.filter(
    (value): value is number => typeof value === 'number' && Number.isFinite(value),
  )
  if (usable.length === 0) return null
  return usable.reduce((sum, value) => sum + value, 0) / usable.length
}

export function maxOf(values: Array<number | null | undefined>): number | null {
  const usable = values.filter(
    (value): value is number => typeof value === 'number' && Number.isFinite(value),
  )
  if (usable.length === 0) return null
  return Math.max(...usable)
}

export function experimentModeCounts(experiments: Experiment[]): Record<string, number> {
  return experiments.reduce<Record<string, number>>((counts, experiment) => {
    const mode = experiment.measurement_mode || 'UNKNOWN'
    counts[mode] = (counts[mode] ?? 0) + 1
    return counts
  }, {})
}

export function countExperimentType(experiments: Experiment[], type: string): number {
  return experiments.filter((experiment) => experiment.experiment_type === type).length
}

export function meanMarginalEnergy(items: MarginalEnergyResult[]): number | null {
  return meanOf(items.map((item) => item.marginal_energy_joules))
}

export function meanMarginalCarbon(items: MarginalEnergyResult[]): number | null {
  return meanOf(items.map((item) => item.marginal_carbon_kg))
}

export function maxInteractionEffect(items: InteractionResult[]): number | null {
  return maxOf(items.map((item) => item.interaction_effect))
}

export interface AmplificationTrendPoint {
  created_at: string
  control_name: string
  attack_intensity: string
  additional_defense_energy: number
  defense_energy_amplification: number
}

export function amplificationTrend(
  items: AmplificationResult[],
): AmplificationTrendPoint[] {
  return [...items]
    .sort(
      (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    )
    .map((item) => ({
      created_at: item.created_at,
      control_name: item.control_name,
      attack_intensity: item.attack_intensity,
      additional_defense_energy: item.additional_defense_energy,
      defense_energy_amplification: item.defense_energy_amplification,
    }))
}

export function meanBy<T>(
  items: T[],
  bucketOf: (item: T) => string,
  valueOf: (item: T) => number | null | undefined,
): Array<{ bucket: string; mean: number; observations: number }> {
  const buckets = new Map<string, Array<number>>()
  items.forEach((item) => {
    const value = valueOf(item)
    if (typeof value !== 'number' || !Number.isFinite(value)) return
    const key = bucketOf(item)
    const values = buckets.get(key) ?? []
    values.push(value)
    buckets.set(key, values)
  })
  return [...buckets.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([bucket, values]) => ({
      bucket,
      mean: values.reduce((sum, value) => sum + value, 0) / values.length,
      observations: values.length,
    }))
}
