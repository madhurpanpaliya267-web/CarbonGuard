import { describe, it, expect, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import EnergyPage from '../components/EnergyPage'
import { mockFetchAllSuccess } from '@/test/mocks'

const mockOverview = {
  current: {
    id: 0, timestamp: '', total_power_watts: 120, cpu_power_watts: 65,
    memory_power_watts: 35, network_power_watts: 20, energy_kwh: 0.12, estimated: true,
  },
  history: [],
  summary: { total_energy: 10, avg_power: 110 },
}

describe('EnergyPage', () => {
  beforeEach(() => {
    mockFetchAllSuccess(mockOverview)
  })

  it('shows loading spinner initially', () => {
    render(<EnergyPage />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('renders page title after loading', async () => {
    render(<EnergyPage />)
    await waitFor(() => {
      expect(screen.getByText('Energy Monitoring')).toBeInTheDocument()
    })
  })

  it('renders metric cards after loading', async () => {
    render(<EnergyPage />)
    await waitFor(() => {
      expect(screen.getByText('Total Power')).toBeInTheDocument()
      expect(screen.getByText('Energy')).toBeInTheDocument()
    })
  })

  it('renders power breakdown section', async () => {
    render(<EnergyPage />)
    await waitFor(() => {
      expect(screen.getByText('Power Breakdown')).toBeInTheDocument()
    })
  })

  it('renders estimated data badge', async () => {
    render(<EnergyPage />)
    await waitFor(() => {
      expect(screen.getByText('ESTIMATED DATA')).toBeInTheDocument()
    })
  })
})
