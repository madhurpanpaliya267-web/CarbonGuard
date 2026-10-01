import { describe, it, expect, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import EventsPage from '../components/EventsPage'
import { mockFetchAllSuccess } from '@/test/mocks'

const mockEvents = {
  items: [
    {
      id: 1, event_uuid: 'e-1', timestamp: new Date().toISOString(),
      event_type: 'ddos', severity: 'HIGH' as const, source_ip: '1.2.3.4',
      target_ip: '5.6.7.8', target_port: 443, confidence: 0.92,
      status: 'detected', detection_method: 'rule-based', description: 'DDoS',
      risk_score: 75, estimated_workload_cpu: 2.5, estimated_energy_kwh: 0.01, estimated_co2_kg: 0.005,
    },
  ],
  total: 1,
  page: 1,
  page_size: 15,
}

describe('EventsPage', () => {
  beforeEach(() => {
    mockFetchAllSuccess(mockEvents)
  })

  it('shows loading spinner initially', () => {
    render(<EventsPage />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('renders page title after loading', async () => {
    render(<EventsPage />)
    await waitFor(() => {
      expect(screen.getByText('Security Event Logs')).toBeInTheDocument()
    })
  })

  it('renders filter controls after loading', async () => {
    render(<EventsPage />)
    await waitFor(() => {
      expect(screen.getByText('Filters:')).toBeInTheDocument()
    })
  })

  it('renders events table after loading', async () => {
    render(<EventsPage />)
    await waitFor(() => {
      expect(screen.getByText('#1')).toBeInTheDocument()
    })
  })

  it('renders refresh button', async () => {
    render(<EventsPage />)
    await waitFor(() => {
      expect(screen.getByText('Refresh')).toBeInTheDocument()
    })
  })

  it('renders export CSV button', async () => {
    render(<EventsPage />)
    await waitFor(() => {
      expect(screen.getByText('Export CSV')).toBeInTheDocument()
    })
  })

  it('renders simulated data badge', async () => {
    render(<EventsPage />)
    await waitFor(() => {
      expect(screen.getByText('SIMULATED DATA')).toBeInTheDocument()
    })
  })
})
