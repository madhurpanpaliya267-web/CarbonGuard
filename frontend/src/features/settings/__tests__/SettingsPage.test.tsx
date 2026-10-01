import { describe, it, expect, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import SettingsPage from '../components/SettingsPage'
import { mockFetchAllSuccess } from '@/test/mocks'

const mockSettings = [
  { id: 1, key: 'carbon_intensity', value: '475', category: 'carbon', description: 'Carbon intensity in gCO2/kWh' },
  { id: 2, key: 'renewable_percentage', value: '25', category: 'carbon', description: 'Renewable energy percentage' },
  { id: 3, key: 'max_delay_hours', value: '4', category: 'optimizer', description: 'Max delay for workload shifting' },
]

describe('SettingsPage', () => {
  beforeEach(() => {
    mockFetchAllSuccess(mockSettings)
  })

  it('shows loading spinner initially', () => {
    render(<SettingsPage />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('renders page title after loading', async () => {
    render(<SettingsPage />)
    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeInTheDocument()
    })
  })

  it('renders settings groups after loading', async () => {
    render(<SettingsPage />)
    await waitFor(() => {
      expect(screen.getByText('carbon')).toBeInTheDocument()
      expect(screen.getByText('optimizer')).toBeInTheDocument()
    })
  })

  it('renders setting keys', async () => {
    render(<SettingsPage />)
    await waitFor(() => {
      expect(screen.getByText('carbon_intensity')).toBeInTheDocument()
      expect(screen.getByText('renewable_percentage')).toBeInTheDocument()
    })
  })

  it('renders configuration badge', async () => {
    render(<SettingsPage />)
    await waitFor(() => {
      expect(screen.getByText('CONFIGURATION')).toBeInTheDocument()
    })
  })

  it('renders reset all button', async () => {
    render(<SettingsPage />)
    await waitFor(() => {
      expect(screen.getByText('Reset All')).toBeInTheDocument()
    })
  })

  it('renders academic notice', async () => {
    render(<SettingsPage />)
    await waitFor(() => {
      expect(screen.getByText(/academic simulation/)).toBeInTheDocument()
    })
  })
})
