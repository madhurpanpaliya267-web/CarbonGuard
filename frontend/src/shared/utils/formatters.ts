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
  if (kwh < 0.001) return `${(kwh * 1000000).toFixed(1)} Wh`
  if (kwh < 1) return `${(kwh * 1000).toFixed(1)} mWh`
  return `${kwh.toFixed(2)} kWh`
}

export function formatCO2(kg: number): string {
  if (kg < 0.001) return `${(kg * 1000000).toFixed(1)} g`
  if (kg < 1) return `${(kg * 1000).toFixed(1)} mg`
  return `${kg.toFixed(2)} kg`
}

export function formatPercentage(value: number): string {
  return `${value.toFixed(1)}%`
}

export function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ')
}
