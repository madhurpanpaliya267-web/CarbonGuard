export function formatDate(date: string | Date): string {
  const d = new Date(date)
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function formatDateTime(date: string | Date): string {
  const d = new Date(date)
  return d.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatNumber(value: number, decimals = 2): string {
  return value.toFixed(decimals)
}

export function formatEnergy(kwh: number): string {
  const abs = Math.abs(kwh)
  if (abs === 0) return '0.00 kWh'
  if (abs >= 1) return `${kwh.toFixed(2)} kWh`
  if (abs >= 0.001) return `${(kwh * 1000).toFixed(1)} Wh`
  if (abs >= 0.000001) return `${(kwh * 1000000).toFixed(1)} mWh`
  return `${(kwh * 1000000000).toFixed(1)} µWh`
}

export function formatCO2(kg: number): string {
  const abs = Math.abs(kg)
  if (abs === 0) return '0.00 kg'
  if (abs >= 1) return `${kg.toFixed(2)} kg`
  if (abs >= 0.001) return `${(kg * 1000).toFixed(1)} g`
  if (abs >= 0.000001) return `${(kg * 1000000).toFixed(1)} mg`
  return `${(kg * 1000000000).toFixed(1)} µg`
}

export function formatPercentage(value: number): string {
  return `${value.toFixed(1)}%`
}

export function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ')
}
