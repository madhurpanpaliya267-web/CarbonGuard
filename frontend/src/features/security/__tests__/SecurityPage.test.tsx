import { describe, it, expect, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import SecurityPage from '../components/SecurityPage'
import { mockFetchAllSuccess } from '@/test/mocks'

const mockStats = {
  total_events: 30,
  by_severity: { CRITICAL: 3, HIGH: 8, MEDIUM: 10, LOW: 9 },
  by_type: { ddos: 6, brute_force: 5, port_scan: 8, sql_injection: 4, malware: 3, suspicious_login: 4 },
  by_status: { detected: 8, investigating: 5, mitigated: 7, blocked: 8, false_positive: 2 },
  avg_confidence: 0.82,
  total_energy_kwh: 0.82,
  total_co2_kg: 0.39,
  simulated: true,
}

const mockEvents = {
  items: [
    {
      id: 1, event_uuid: 'uuid-1', timestamp: new Date().toISOString(),
      event_type: 'ddos', severity: 'HIGH' as const, source_ip: '1.2.3.4',
      target_ip: '5.6.7.8', target_port: 443, confidence: 0.92,
      status: 'detected', detection_method: 'rule-based', description: 'DDoS detected',
      risk_score: 75, estimated_workload_cpu: 2.5, estimated_energy_kwh: 0.01, estimated_co2_kg: 0.005,
    },
  ],
  total: 1,
  page: 1,
  page_size: 15,
}

describe('SecurityPage', () => {
  beforeEach(() => {
    mockFetchAllSuccess(mockStats, mockEvents)
  })

  it('shows loading spinner initially', () => {
    render(<SecurityPage />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('renders page title after loading', async () => {
    render(<SecurityPage />)
    await waitFor(() => {
      expect(screen.getByText('Security Monitoring')).toBeInTheDocument()
    })
  })

  it('renders metrics after loading', async () => {
    render(<SecurityPage />)
    await waitFor(() => {
      expect(screen.getByText('Total Events')).toBeInTheDocument()
      expect(screen.getByText('Avg Confidence')).toBeInTheDocument()
    })
  })

  it('renders severity breakdown section', async () => {
    render(<SecurityPage />)
    await waitFor(() => {
      expect(screen.getByText('Severity Breakdown')).toBeInTheDocument()
    })
  })

  it('renders recent events table', async () => {
    render(<SecurityPage />)
    await waitFor(() => {
      expect(screen.getByText('Recent Security Events')).toBeInTheDocument()
    })
  })

  it('renders simulated data badge', async () => {
    render(<SecurityPage />)
    await waitFor(() => {
      expect(screen.getByText('SIMULATED DATA')).toBeInTheDocument()
    })
  })

  it('renders refresh button after loading', async () => {
    render(<SecurityPage />)
    await waitFor(() => {
      expect(screen.getByText('Refresh')).toBeInTheDocument()
    })
  })

  it('shows last updated time after loading', async () => {
    render(<SecurityPage />)
    await waitFor(() => {
      expect(screen.getByText(/Updated/)).toBeInTheDocument()
    })
  })
})
