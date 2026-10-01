import { describe, it, expect, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import OptimizerPage from '../components/OptimizerPage'
import { mockFetchAllSuccess } from '@/test/mocks'

const mockWorkloads = [
  {
    id: 1, workload_uuid: 'w-1', name: 'Security Scan', workload_type: 'security_scan',
    priority: 'critical' as const, is_security_critical: true,
    estimated_cpu_seconds: 30, estimated_memory_mb: 256, estimated_energy_kwh: 0.05,
    estimated_co2_kg: 0.02, status: 'running' as const, scheduled_time: new Date().toISOString(),
    optimized_time: null, carbon_intensity_at_exec: 475, created_at: new Date().toISOString(),
    completed_at: null,
  },
]

const mockComparison = {
  before: { energy_kwh: 1.5, co2_kg: 0.7 },
  after: { energy_kwh: 1.2, co2_kg: 0.56 },
  comparison: { energy_saved: 0.3, co2_saved: 0.14, reduction_pct: 20 },
}

describe('OptimizerPage', () => {
  beforeEach(() => {
    mockFetchAllSuccess(mockWorkloads, mockComparison)
  })

  it('shows loading spinner initially', () => {
    render(<OptimizerPage />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('renders page title after loading', async () => {
    render(<OptimizerPage />)
    await waitFor(() => {
      expect(screen.getByText('Carbon-Aware Workload Optimizer')).toBeInTheDocument()
    })
  })

  it('renders security first badge', async () => {
    render(<OptimizerPage />)
    await waitFor(() => {
      expect(screen.getByText('SECURITY FIRST')).toBeInTheDocument()
    })
  })

  it('renders workloads table', async () => {
    render(<OptimizerPage />)
    await waitFor(() => {
      expect(screen.getByText('Workloads')).toBeInTheDocument()
      expect(screen.getByText('Security Scan')).toBeInTheDocument()
    })
  })

  it('renders run optimization button', async () => {
    render(<OptimizerPage />)
    await waitFor(() => {
      expect(screen.getByText('Run Optimization')).toBeInTheDocument()
    })
  })

  it('renders comparison before/after cards', async () => {
    render(<OptimizerPage />)
    await waitFor(() => {
      expect(screen.getByText('Before Optimization')).toBeInTheDocument()
      expect(screen.getByText('After Optimization')).toBeInTheDocument()
      expect(screen.getByText('Savings')).toBeInTheDocument()
    })
  })
})
