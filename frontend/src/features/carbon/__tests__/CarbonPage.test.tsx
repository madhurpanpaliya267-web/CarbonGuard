import { describe, it, expect, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import CarbonPage from '../components/CarbonPage'
import { mockFetchAllSuccess } from '@/test/mocks'

const mockOverview = {
  current: {
    id: 0, timestamp: '', total_energy_kwh: 3.42, total_co2_kg: 1.62,
    security_energy_kwh: 0.82, security_co2_kg: 0.39, carbon_saved_kg: 14.7,
    carbon_intensity: 475, renewable_percentage: 34.2, workload_count: 5,
    security_carbon_efficiency: 72.5,
  },
  history: [],
  summary: { total_energy: 100, total_co2: 47.5, total_saved: 15, avg_efficiency: 72 },
}

const mockEfficiency = {
  threats_per_kwh: 34.1, co2_per_threat: 0.0139,
  efficiency_score: 72, rating: 'Good',
}

describe('CarbonPage', () => {
  beforeEach(() => {
    mockFetchAllSuccess(mockOverview, mockEfficiency)
  })

  it('shows loading spinner initially', () => {
    render(<CarbonPage />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('renders page title after loading', async () => {
    render(<CarbonPage />)
    await waitFor(() => {
      expect(screen.getByText('Carbon Monitoring')).toBeInTheDocument()
    })
  })

  it('renders metric cards after loading', async () => {
    render(<CarbonPage />)
    await waitFor(() => {
      expect(screen.getByText('Current CO2')).toBeInTheDocument()
      expect(screen.getByText('Total Energy')).toBeInTheDocument()
      expect(screen.getByText('Carbon Saved')).toBeInTheDocument()
    })
  })

  it('renders efficiency section', async () => {
    render(<CarbonPage />)
    await waitFor(() => {
      expect(screen.getByText('Security-Carbon Efficiency')).toBeInTheDocument()
    })
  })

  it('renders estimated data badge', async () => {
    render(<CarbonPage />)
    await waitFor(() => {
      expect(screen.getByText('ESTIMATED DATA')).toBeInTheDocument()
    })
  })
})
