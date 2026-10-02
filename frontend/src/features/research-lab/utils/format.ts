import { formatCO2, formatNumber } from '@/shared/utils/formatters'

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
