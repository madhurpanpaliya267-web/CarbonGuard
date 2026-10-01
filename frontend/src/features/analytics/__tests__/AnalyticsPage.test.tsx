import { describe, it, expect, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import AnalyticsPage from '../components/AnalyticsPage'
import { mockFetchAllSuccess } from '@/test/mocks'

const mockSecurity = {
  attacks_over_time: [{ date: '2025-01-01', count: 5 }],
  categories: [{ type: 'ddos', count: 10 }],
  severity_dist: [{ level: 'HIGH', count: 5 }],
  top_sources: [{ ip: '1.2.3.4', count: 10 }],
}

const mockCarbon = {
  emissions_over_time: [{ date: '2025-01-01', co2_kg: 0.5 }],
  savings_over_time: [{ date: '2025-01-01', saved_kg: 0.2, cumulative_kg: 1.0 }],
  efficiency_trend: [{ date: '2025-01-01', efficiency: 72 }],
}

const mockEnergy = {
  usage_over_time: [{ date: '2025-01-01', energy_kwh: 3.5 }],
  by_type: [{ type: 'cpu', energy_kwh: 2.0 }],
  peak_hours: [{ hour: 14, energy_kwh: 4.0 }],
}

const mockOptimization = {
  runs: 5, avg_reduction: 18.5, total_saved_kg: 2.5, best_reduction: 25.0,
}

describe('AnalyticsPage', () => {
  beforeEach(() => {
    mockFetchAllSuccess(mockSecurity, mockCarbon, mockEnergy, mockOptimization)
  })

  it('shows loading spinner initially', () => {
    render(<AnalyticsPage />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('renders page title after loading', async () => {
    render(<AnalyticsPage />)
    await waitFor(() => {
      expect(screen.getByText('Analytics')).toBeInTheDocument()
    })
  })

  it('renders period selector', async () => {
    render(<AnalyticsPage />)
    await waitFor(() => {
      expect(screen.getByText('24h')).toBeInTheDocument()
      expect(screen.getByText('7d')).toBeInTheDocument()
      expect(screen.getByText('30d')).toBeInTheDocument()
    })
  })

  it('renders tab buttons', async () => {
    render(<AnalyticsPage />)
    await waitFor(() => {
      expect(screen.getByText('Security')).toBeInTheDocument()
      expect(screen.getByText('Carbon')).toBeInTheDocument()
      expect(screen.getByText('Energy')).toBeInTheDocument()
      expect(screen.getByText('Optimization')).toBeInTheDocument()
    })
  })

  it('renders security analytics by default', async () => {
    render(<AnalyticsPage />)
    await waitFor(() => {
      expect(screen.getByText('Attacks Over Time')).toBeInTheDocument()
    })
  })

  it('renders simulated data badge', async () => {
    render(<AnalyticsPage />)
    await waitFor(() => {
      expect(screen.getByText('SIMULATED DATA')).toBeInTheDocument()
    })
  })
})
