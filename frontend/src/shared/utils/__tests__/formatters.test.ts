import { describe, it, expect } from 'vitest'
import { formatDate, formatDateTime, formatNumber, formatEnergy, formatCO2, formatPercentage, cn } from '../formatters'

describe('formatDate', () => {
  it('formats a date string', () => {
    const result = formatDate('2025-01-15T10:30:00Z')
    expect(result).toContain('Jan')
    expect(result).toContain('15')
    expect(result).toContain('2025')
  })

  it('formats a Date object', () => {
    const result = formatDate(new Date('2025-06-20T00:00:00Z'))
    expect(result).toContain('Jun')
    expect(result).toContain('20')
  })
})

describe('formatDateTime', () => {
  it('formats a date with time', () => {
    const result = formatDateTime('2025-01-15T10:30:00Z')
    expect(result).toContain('Jan')
    expect(result).toContain('15')
  })
})

describe('formatNumber', () => {
  it('formats number with default 2 decimals', () => {
    expect(formatNumber(3.14159)).toBe('3.14')
  })

  it('formats number with custom decimals', () => {
    expect(formatNumber(3.14159, 4)).toBe('3.1416')
  })
})

describe('formatEnergy', () => {
  it('formats large energy values in kWh', () => {
    expect(formatEnergy(5.5)).toBe('5.50 kWh')
  })

  it('formats medium energy values in Wh', () => {
    expect(formatEnergy(0.5)).toBe('500.0 Wh')
  })

  it('formats small energy values in mWh', () => {
    expect(formatEnergy(0.0005)).toBe('500.0 mWh')
  })

  it('formats tiny energy values in µWh', () => {
    expect(formatEnergy(0.0000005)).toBe('500.0 µWh')
  })
})

describe('formatCO2', () => {
  it('formats large CO2 values in kg', () => {
    expect(formatCO2(2.5)).toBe('2.50 kg')
  })

  it('formats medium CO2 values in g', () => {
    expect(formatCO2(0.5)).toBe('500.0 g')
  })

  it('formats small CO2 values in mg', () => {
    expect(formatCO2(0.0005)).toBe('500.0 mg')
  })

  it('formats tiny CO2 values in µg', () => {
    expect(formatCO2(0.0000005)).toBe('500.0 µg')
  })

  it('formats zero as zero kilograms', () => {
    expect(formatCO2(0)).toBe('0.00 kg')
  })

  it('keeps the sign of negative carbon differences', () => {
    expect(formatCO2(-0.5)).toBe('-500.0 g')
  })
})

describe('formatPercentage', () => {
  it('formats percentage with 1 decimal', () => {
    expect(formatPercentage(45.678)).toBe('45.7%')
  })

  it('formats zero percentage', () => {
    expect(formatPercentage(0)).toBe('0.0%')
  })
})

describe('cn', () => {
  it('joins class names', () => {
    expect(cn('a', 'b', 'c')).toBe('a b c')
  })

  it('filters out falsy values', () => {
    expect(cn('a', false, undefined, null, 'b')).toBe('a b')
  })

  it('returns empty string for no truthy values', () => {
    expect(cn(false, undefined, null)).toBe('')
  })
})
