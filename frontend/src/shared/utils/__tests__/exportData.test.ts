import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { arrayToCSV, exportEventsToCSV, exportThreatsToCSV } from '../exportData'

describe('exportData', () => {
  let anchorClickSpy: ReturnType<typeof vi.spyOn>
  let appendChildSpy: ReturnType<typeof vi.spyOn>
  let removeChildSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    anchorClickSpy = vi.fn()
    appendChildSpy = vi.fn()
    removeChildSpy = vi.fn()
    vi.spyOn(document, 'createElement').mockReturnValue({
      href: '',
      download: '',
      click: anchorClickSpy,
    } as unknown as HTMLAnchorElement)
    vi.spyOn(document.body, 'appendChild').mockImplementation(appendChildSpy)
    vi.spyOn(document.body, 'removeChild').mockImplementation(removeChildSpy)
    vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:test')
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('arrayToCSV', () => {
    it('returns empty string for empty array', () => {
      expect(arrayToCSV([])).toBe('')
    })

    it('creates CSV with headers from keys', () => {
      const data = [{ name: 'Alice', age: 30 }]
      const result = arrayToCSV(data)
      expect(result).toBe('name,age\nAlice,30')
    })

    it('uses provided headers', () => {
      const data = [{ name: 'Alice', age: 30 }]
      const result = arrayToCSV(data, ['name'])
      expect(result).toBe('name\nAlice')
    })

    it('escapes fields containing commas', () => {
      const data = [{ val: 'a,b' }]
      const result = arrayToCSV(data)
      expect(result).toBe('val\n"a,b"')
    })

    it('escapes fields containing double quotes', () => {
      const data = [{ val: 'say "hello"' }]
      const result = arrayToCSV(data)
      expect(result).toBe('val\n"say ""hello"""')
    })

    it('handles null and undefined values', () => {
      const data = [{ a: null, b: undefined }]
      const result = arrayToCSV(data)
      expect(result).toBe('a,b\n,')
    })
  })

  describe('exportEventsToCSV', () => {
    it('creates CSV and triggers download', () => {
      const events = [{
        id: 1,
        event_type: 'ddos',
        severity: 'HIGH',
        timestamp: '2026-01-01T00:00:00Z',
        source_ip: '1.2.3.4',
        target_ip: '5.6.7.8',
        target_port: 443,
        confidence: 0.92,
        status: 'detected',
        estimated_energy_kwh: 0.01,
        estimated_co2_kg: 0.005,
        detection_method: 'rule-based',
        description: 'DDoS attack',
        risk_score: 75,
      }]
      exportEventsToCSV(events)
      expect(document.createElement).toHaveBeenCalledWith('a')
      expect(anchorClickSpy).toHaveBeenCalled()
      expect(appendChildSpy).toHaveBeenCalled()
      expect(removeChildSpy).toHaveBeenCalled()
    })
  })

  describe('exportThreatsToCSV', () => {
    it('creates CSV and triggers download', () => {
      const threats = [{
        id: 1,
        threat_type: 'ddos',
        severity: 'HIGH',
        confidence: 0.9,
        risk_score: 75,
        status: 'active',
        detected_at: '2026-01-01T00:00:00Z',
        threat_uuid: 'uuid-1',
        anomaly_level: 0.85,
        recommended_action: 'Block IPs',
      }]
      exportThreatsToCSV(threats)
      expect(document.createElement).toHaveBeenCalledWith('a')
      expect(anchorClickSpy).toHaveBeenCalled()
    })
  })
})
