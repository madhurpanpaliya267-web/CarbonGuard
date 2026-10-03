import { describe, it, expect } from 'vitest'
import {
  formatCarbonPerWorkload,
  carbonPerWorkloadReason,
  carbonBasisLabel,
  CARBON_INTENSITY_NOTE,
  formatJoules,
  formatWatts,
  formatKilograms,
  formatScalar,
  formatInteger,
  shortId,
  workloadLabel,
  modeVariant,
  controlsLabel,
  parseControls,
  distinctOptions,
} from '../utils/format'
import type { CarbonPerWorkload } from '../types/research'

const available = (
  value_kg: number | null,
  unit: string | null = null,
): CarbonPerWorkload => ({ value_kg, unit, status: 'available', reason: null })

const unavailable = (reason: string | null = null): CarbonPerWorkload => ({
  value_kg: null,
  unit: null,
  status: 'unavailable',
  reason,
})

describe('formatCarbonPerWorkload', () => {
  it('returns "Not available" for null input', () => {
    expect(formatCarbonPerWorkload(null)).toBe('Not available')
    expect(formatCarbonPerWorkload(undefined)).toBe('Not available')
  })

  it('returns "Not available" for non-available status', () => {
    expect(formatCarbonPerWorkload(unavailable())).toBe('Not available')
  })

  it('returns "Not available" when value_kg is null', () => {
    expect(formatCarbonPerWorkload(available(null, 'kg/kWh'))).toBe('Not available')
  })

  it('strips the "kg/" prefix from the workload unit', () => {
    expect(formatCarbonPerWorkload(available(0.001, 'kg/kWh'))).toBe('1.0 g/kWh')
  })

  it('appends the workload unit when present', () => {
    expect(formatCarbonPerWorkload(available(0.5, 'per_run'))).toBe('500.0 g/per_run')
  })

  it('omits the workload suffix when the unit is empty', () => {
    expect(formatCarbonPerWorkload(available(0.5))).toBe('500.0 g')
    expect(formatCarbonPerWorkload(available(0.5, null))).toBe('500.0 g')
  })

  it('formats kilogram-scale values with the shared CO2 formatter', () => {
    expect(formatCarbonPerWorkload(available(2, 'kg/kWh'))).toBe('2.00 kg/kWh')
  })
})

describe('carbonPerWorkloadReason', () => {
  it('returns null for null input and available values', () => {
    expect(carbonPerWorkloadReason(null)).toBeNull()
    expect(carbonPerWorkloadReason(available(1))).toBeNull()
  })

  it('returns the reason for unavailable values', () => {
    expect(carbonPerWorkloadReason(unavailable('No workload recorded'))).toBe(
      'No workload recorded',
    )
  })

  it('falls back to "Not available" when no reason is present', () => {
    expect(carbonPerWorkloadReason(unavailable(null))).toBe('Not available')
  })
})

describe('carbonBasisLabel', () => {
  it('labels a missing basis as unknown', () => {
    expect(carbonBasisLabel(null)).toBe('unknown energy basis')
    expect(carbonBasisLabel(undefined)).toBe('unknown energy basis')
    expect(carbonBasisLabel('')).toBe('unknown energy basis')
  })

  it('renders underscores as spaces', () => {
    expect(carbonBasisLabel('calculated_from_estimated_energy')).toBe(
      'calculated from estimated energy',
    )
  })
})

describe('CARBON_INTENSITY_NOTE', () => {
  it('documents the formula and the calculated-not-measured provenance', () => {
    expect(CARBON_INTENSITY_NOTE).toContain('475 gCO₂/kWh')
    expect(CARBON_INTENSITY_NOTE).toContain('not live grid telemetry')
    expect(CARBON_INTENSITY_NOTE).toContain('calculated — never measured')
  })
})

describe('formatJoules', () => {
  it('returns an em dash for null, undefined and NaN', () => {
    expect(formatJoules(null)).toBe('—')
    expect(formatJoules(undefined)).toBe('—')
    expect(formatJoules(Number.NaN)).toBe('—')
  })

  it('formats joules with two digits by default', () => {
    expect(formatJoules(1234.5678)).toBe('1234.57 J')
  })

  it('honors the digits parameter', () => {
    expect(formatJoules(5.678, 1)).toBe('5.7 J')
  })
})

describe('formatWatts', () => {
  it('returns an em dash for null, undefined and NaN', () => {
    expect(formatWatts(null)).toBe('—')
    expect(formatWatts(undefined)).toBe('—')
    expect(formatWatts(Number.NaN)).toBe('—')
  })

  it('formats watts with three digits by default', () => {
    expect(formatWatts(12.5)).toBe('12.500 W')
  })

  it('honors the digits parameter', () => {
    expect(formatWatts(12.3456, 1)).toBe('12.3 W')
  })
})

describe('formatKilograms', () => {
  it('returns an em dash for null, undefined and NaN', () => {
    expect(formatKilograms(null)).toBe('—')
    expect(formatKilograms(undefined)).toBe('—')
    expect(formatKilograms(Number.NaN)).toBe('—')
  })

  it('formats small masses in grams and large masses in kilograms', () => {
    expect(formatKilograms(0.5)).toBe('500.0 g')
    expect(formatKilograms(2)).toBe('2.00 kg')
  })
})

describe('formatScalar', () => {
  it('returns an em dash for null, undefined and NaN', () => {
    expect(formatScalar(null)).toBe('—')
    expect(formatScalar(undefined)).toBe('—')
    expect(formatScalar(Number.NaN)).toBe('—')
  })

  it('formats with four digits by default and no suffix', () => {
    expect(formatScalar(0.5)).toBe('0.5000')
  })

  it('honors digits and suffix parameters', () => {
    expect(formatScalar(1.23456, 4, ' W')).toBe('1.2346 W')
    expect(formatScalar(3, 0, '%')).toBe('3%')
  })
})

describe('formatInteger', () => {
  it('returns an em dash for null, undefined and NaN', () => {
    expect(formatInteger(null)).toBe('—')
    expect(formatInteger(undefined)).toBe('—')
    expect(formatInteger(Number.NaN)).toBe('—')
  })

  it('stringifies integers', () => {
    expect(formatInteger(42)).toBe('42')
    expect(formatInteger(0)).toBe('0')
  })
})

describe('shortId', () => {
  it('returns an em dash for empty input', () => {
    expect(shortId(null)).toBe('—')
    expect(shortId(undefined)).toBe('—')
    expect(shortId('')).toBe('—')
  })

  it('keeps ids up to 12 characters intact', () => {
    expect(shortId('abcdef123456')).toBe('abcdef123456')
    expect(shortId('short-id')).toBe('short-id')
  })

  it('truncates longer ids to 8 characters plus an ellipsis', () => {
    expect(shortId('abcdef1234567')).toBe('abcdef12…')
  })
})

describe('workloadLabel', () => {
  it('returns an em dash for null, undefined and NaN', () => {
    expect(workloadLabel(null, 'packets_per_second')).toBe('—')
    expect(workloadLabel(undefined, null)).toBe('—')
    expect(workloadLabel(Number.NaN, null)).toBe('—')
  })

  it('appends the unit when present', () => {
    expect(workloadLabel(500, 'packets_per_second')).toBe('500.00 packets_per_second')
  })

  it('omits the unit when missing', () => {
    expect(workloadLabel(500, null)).toBe('500.00')
    expect(workloadLabel(500, '')).toBe('500.00')
  })
})

describe('modeVariant', () => {
  it('marks ESTIMATED as warning, case-insensitively', () => {
    expect(modeVariant('ESTIMATED')).toBe('warning')
    expect(modeVariant('estimated')).toBe('warning')
  })

  it('marks MEASURED as success, case-insensitively', () => {
    expect(modeVariant('MEASURED')).toBe('success')
    expect(modeVariant('measured')).toBe('success')
  })

  it('marks SIMULATED as muted — never as measured success', () => {
    expect(modeVariant('SIMULATED')).toBe('muted')
    expect(modeVariant('simulated')).toBe('muted')
  })

  it('marks unknown, empty and missing modes as muted', () => {
    expect(modeVariant('garbage')).toBe('muted')
    expect(modeVariant('')).toBe('muted')
    expect(modeVariant(null)).toBe('muted')
    expect(modeVariant(undefined)).toBe('muted')
  })
})

describe('controlsLabel', () => {
  it('falls back to "No security controls" for empty input', () => {
    expect(controlsLabel(null)).toBe('No security controls')
    expect(controlsLabel(undefined)).toBe('No security controls')
    expect(controlsLabel('')).toBe('No security controls')
    expect(controlsLabel('   ')).toBe('No security controls')
  })

  it('trims a non-empty label', () => {
    expect(controlsLabel('  firewall, ids  ')).toBe('firewall, ids')
  })
})

describe('parseControls', () => {
  it('returns an empty array for empty input', () => {
    expect(parseControls(null)).toEqual([])
    expect(parseControls(undefined)).toEqual([])
    expect(parseControls('')).toEqual([])
    expect(parseControls('   ')).toEqual([])
  })

  it('parses JSON arrays and coerces entries to strings', () => {
    expect(parseControls('["firewall", "ids"]')).toEqual(['firewall', 'ids'])
    expect(parseControls('[1, 2]')).toEqual(['1', '2'])
  })

  it('drops blank entries from JSON arrays', () => {
    expect(parseControls('["a", "", "b"]')).toEqual(['a', 'b'])
  })

  it('wraps a bare JSON string as a single entry', () => {
    expect(parseControls('"firewall"')).toEqual(['firewall'])
    expect(parseControls('""')).toEqual([])
  })

  it('falls back to comma splitting for invalid JSON', () => {
    expect(parseControls('firewall, ids')).toEqual(['firewall', 'ids'])
    expect(parseControls(' a , b ')).toEqual(['a', 'b'])
    expect(parseControls('{broken')).toEqual(['{broken'])
  })

  it('falls back to comma splitting for non-array JSON values', () => {
    expect(parseControls('42')).toEqual(['42'])
    expect(parseControls('{"a":1}')).toEqual(['{"a":1}'])
  })
})

describe('distinctOptions', () => {
  it('drops null, undefined and empty values', () => {
    expect(distinctOptions([null, undefined, '', 'a'])).toEqual([
      { value: 'a', label: 'a' },
    ])
  })

  it('deduplicates by stringified value', () => {
    expect(distinctOptions([1, '1', 2])).toEqual([
      { value: '1', label: '1' },
      { value: '2', label: '2' },
    ])
  })

  it('sorts numerically when values are numeric', () => {
    expect(distinctOptions(['10', '2', '1']).map((option) => option.value)).toEqual([
      '1',
      '2',
      '10',
    ])
  })

  it('applies the label prefix', () => {
    expect(distinctOptions(['ESTIMATED'], 'mode-')).toEqual([
      { value: 'ESTIMATED', label: 'mode-ESTIMATED' },
    ])
  })
})
