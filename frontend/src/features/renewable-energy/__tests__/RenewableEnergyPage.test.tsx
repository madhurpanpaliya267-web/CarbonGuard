import { describe, it, expect, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import RenewableEnergyPage from '../components/RenewableEnergyPage'
import { mockFetchAllSuccess } from '@/test/mocks'

const mockStatus = {
  renewable_percentage: 42.5,
  solar_availability: 65,
  wind_availability: 30,
  grid_carbon_intensity: 380,
  forecast: [
    { timestamp: new Date().toISOString(), solar: 60, wind: 25, renewable_pct: 40, carbon_intensity: 380 },
  ],
}

describe('RenewableEnergyPage', () => {
  beforeEach(() => {
    mockFetchAllSuccess(mockStatus)
  })

  it('shows loading spinner initially', () => {
    render(<RenewableEnergyPage />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('renders page title after loading', async () => {
    render(<RenewableEnergyPage />)
    await waitFor(() => {
      expect(screen.getByText('Renewable Energy Monitor')).toBeInTheDocument()
    })
  })

  it('renders metric cards after loading', async () => {
    render(<RenewableEnergyPage />)
    await waitFor(() => {
      expect(screen.getByText('Renewable Energy')).toBeInTheDocument()
      expect(screen.getByText('Solar Availability')).toBeInTheDocument()
      expect(screen.getByText('Wind Availability')).toBeInTheDocument()
      expect(screen.getByText('Grid Carbon Intensity')).toBeInTheDocument()
    })
  })

  it('renders scheduling windows section', async () => {
    render(<RenewableEnergyPage />)
    await waitFor(() => {
      expect(screen.getByText('Recommended Scheduling Windows')).toBeInTheDocument()
    })
  })

  it('renders simulated data badge', async () => {
    render(<RenewableEnergyPage />)
    await waitFor(() => {
      expect(screen.getByText('SIMULATED DATA')).toBeInTheDocument()
    })
  })
})
