import { formatCO2, formatNumber } from '@/shared/utils/formatters'
import type { CarbonPerWorkload } from '../types/research'

export function formatCarbonPerWorkload(
  value: CarbonPerWorkload | null | undefined,
): string {
  if (!value || value.status !== 'available' || value.value_kg === null || value.value_kg === undefined) {
    return 'Not available'
  }
  const [amount, massUnit] = formatCO2(value.value_kg).split(' ')
  const workloadSuffix = value.unit?.startsWith('kg/')
    ? value.unit.slice(3)
    : value.unit
  return workloadSuffix ? `${amount} ${massUnit}/${workloadSuffix}` : `${amount} ${massUnit}`
}

export function carbonPerWorkloadReason(
  value: CarbonPerWorkload | null | undefined,
): string | null {
  if (!value || value.status === 'available') return null
  return value.reason ?? 'Not available'
}

export function carbonBasisLabel(basis: string | null | undefined): string {
  if (!basis) return 'unknown energy basis'
  return basis.replace(/_/g, ' ')
}

export const CARBON_INTENSITY_NOTE =
  'Carbon = energy (kWh) × carbon intensity (gCO₂/kWh) ÷ 1000. Carbon intensity is a configured value (default 475 gCO₂/kWh), not live grid telemetry, and carbon is calculated — never measured.'

export function formatJoules(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return `${formatNumber(value, digits)} J`
}

export function formatWatts(value: number | null | undefined, digits = 3): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return `${formatNumber(value, digits)} W`
}

export function formatKilograms(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return formatCO2(value)
}

export function formatScalar(
  value: number | null | undefined,
  digits = 4,
  suffix = '',
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return `${formatNumber(value, digits)}${suffix}`
}

export function formatInteger(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return String(value)
}

export function shortId(value: string | null | undefined): string {
  if (!value) return '—'
  return value.length > 12 ? `${value.slice(0, 8)}…` : value
}

export function workloadLabel(
  value: number | null | undefined,
  unit: string | null | undefined,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return unit ? `${formatNumber(value, 2)} ${unit}` : formatNumber(value, 2)
}

export function modeVariant(mode: string | null | undefined): 'warning' | 'success' | 'muted' {
  if (!mode) return 'muted'
  const normalized = mode.toUpperCase()
  if (normalized === 'ESTIMATED') return 'warning'
  if (normalized === 'MEASURED') return 'success'
  return 'muted'
}

export function controlsLabel(controls: string | null | undefined): string {
  if (!controls) return 'No security controls'
  const trimmed = controls.trim()
  return trimmed.length > 0 ? trimmed : 'No security controls'
}
