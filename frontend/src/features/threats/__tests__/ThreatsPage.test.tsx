import { describe, it, expect, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import ThreatsPage from '../components/ThreatsPage'
import { mockFetchAllSuccess } from '@/test/mocks'

const mockThreats = {
  items: [
    {
      id: 1, threat_uuid: 't-uuid-1', event_id: 1, threat_type: 'ddos', severity: 'HIGH' as const,
      confidence: 0.9, risk_score: 75, status: 'active' as const, detected_at: new Date().toISOString(),
      resolved_at: null, explanation: '', recommended_action: 'Block IPs', anomaly_level: 0.85,
    },
  ],
  total: 1,
  page: 1,
  page_size: 50,
}

const mockStats = {
  total_threats: 20, active_threats: 8, resolved_threats: 7,
  avg_risk_score: 45.2, avg_confidence: 0.81,
  by_severity: { CRITICAL: 2, HIGH: 5, MEDIUM: 8, LOW: 5 },
  by_type: { ddos: 4 }, by_status: { active: 8 }, total_events: 30,
}

describe('ThreatsPage', () => {
  beforeEach(() => {
    mockFetchAllSuccess(mockThreats, mockStats)
  })

  it('shows loading spinner initially', () => {
    render(<ThreatsPage />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('renders page title after loading', async () => {
    render(<ThreatsPage />)
    await waitFor(() => {
      expect(screen.getByText('Threats')).toBeInTheDocument()
    })
  })

  it('renders stats cards after loading', async () => {
    render(<ThreatsPage />)
    await waitFor(() => {
      expect(screen.getByText('Total Threats')).toBeInTheDocument()
      expect(screen.getAllByText('Active').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('Resolved').length).toBeGreaterThanOrEqual(1)
    })
  })

  it('renders filter controls after loading', async () => {
    render(<ThreatsPage />)
    await waitFor(() => {
      expect(screen.getByText('Filters:')).toBeInTheDocument()
    })
  })

  it('renders simulated data badge', async () => {
    render(<ThreatsPage />)
    await waitFor(() => {
      expect(screen.getByText('SIMULATED DATA')).toBeInTheDocument()
    })
  })

  it('renders refresh button', async () => {
    render(<ThreatsPage />)
    await waitFor(() => {
      expect(screen.getByText('Refresh')).toBeInTheDocument()
    })
  })

  it('renders export CSV button', async () => {
    render(<ThreatsPage />)
    await waitFor(() => {
      expect(screen.getByText('Export CSV')).toBeInTheDocument()
    })
  })
})
