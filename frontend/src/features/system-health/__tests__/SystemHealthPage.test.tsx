import { describe, it, expect, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import SystemHealthPage from '../components/SystemHealthPage'
import { mockFetchAllSuccess } from '@/test/mocks'

const mockCurrent = {
  id: 0, timestamp: new Date().toISOString(), cpu_utilization: 45.2,
  memory_utilization: 62.1, active_workloads: 5,
  security_engine_status: 'online', carbon_engine_status: 'online',
  ai_engine_status: 'online', database_status: 'online', api_status: 'online',
  simulated: true,
}

const mockHistory = [
  {
    id: 1, timestamp: new Date().toISOString(), cpu_utilization: 40,
    memory_utilization: 55, active_workloads: 4,
    security_engine_status: 'online', carbon_engine_status: 'online',
    ai_engine_status: 'online', database_status: 'online', api_status: 'online',
    simulated: true,
  },
]

describe('SystemHealthPage', () => {
  beforeEach(() => {
    mockFetchAllSuccess(mockCurrent, mockHistory)
  })

  it('shows loading spinner initially', () => {
    render(<SystemHealthPage />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('renders page title after loading', async () => {
    render(<SystemHealthPage />)
    await waitFor(() => {
      expect(screen.getByText('System Health')).toBeInTheDocument()
    })
  })

  it('renders service status grid', async () => {
    render(<SystemHealthPage />)
    await waitFor(() => {
      expect(screen.getByText('Service Status')).toBeInTheDocument()
      expect(screen.getByText('Security Engine')).toBeInTheDocument()
      expect(screen.getByText('Carbon Engine')).toBeInTheDocument()
      expect(screen.getByText('AI Engine')).toBeInTheDocument()
      expect(screen.getByText('Database')).toBeInTheDocument()
      expect(screen.getByText('API Server')).toBeInTheDocument()
    })
  })

  it('renders metric cards', async () => {
    render(<SystemHealthPage />)
    await waitFor(() => {
      expect(screen.getByText('CPU Utilization')).toBeInTheDocument()
      expect(screen.getByText('Memory Utilization')).toBeInTheDocument()
    })
  })

  it('renders all systems operational badge', async () => {
    render(<SystemHealthPage />)
    await waitFor(() => {
      expect(screen.getByText('ALL SYSTEMS OPERATIONAL')).toBeInTheDocument()
    })
  })
})
