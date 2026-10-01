import { describe, it, expect, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import DashboardPage from '../components/DashboardPage'
import { mockFetchAllSuccess } from '@/test/mocks'

const mockDashboardMetrics = {
  carbonGuardScore: 82,
  securityRiskScore: 45,
  currentThreatLevel: 'MEDIUM' as const,
  activeThreats: 3,
  threatsDetected24h: 28,
  threatsBlocked24h: 25,
  energyConsumptionKwh: 3.42,
  estimatedCo2Kg: 1.62,
  carbonSavedKg: 14.7,
  renewablePercentage: 34.2,
  currentWorkload: 5,
  securityCarbonEfficiency: 72.5,
}

const mockThreatActivity = { data_points: [{ timestamp: new Date().toISOString(), count: 5, critical: 1, high: 2, medium: 1, low: 1 }] }
const mockCarbonEmissions = { data_points: [{ timestamp: new Date().toISOString(), co2Kg: 0.05, energyKwh: 0.1 }] }
const mockCarbonSavings = { data_points: [{ timestamp: new Date().toISOString(), baselineKg: 0.8, optimizedKg: 0.6, savedKg: 0.2 }] }
const mockThreatCategories = { categories: [{ type: 'DDoS', count: 5, percentage: 50, color: '#ef4444' }] }
const mockSecurityEvents = [{ id: 1, timestamp: new Date().toISOString(), eventType: 'DDoS', severity: 'HIGH' as const, sourceIp: '1.2.3.4', targetIp: '5.6.7.8', status: 'detected', confidence: 0.9 }]
const mockRecommendations = [{ id: 1, type: 'carbon', recommendation: 'Shift workload', priority: 'medium' as const, reason: 'High carbon', expectedImpact: '18%', confidence: 0.82 }]
const mockSystemHealth = [{ component: 'Security Engine', status: 'online' as const, lastCheck: new Date().toISOString() }]
const mockCarbonEfficiency = { threatsDetected: 28, securityWorkload: '5 active', energyUsed: '0.82 kWh', estimatedCo2: '0.39 kg', efficiencyScore: 72.5, rating: 'Good' }

describe('DashboardPage', () => {
  beforeEach(() => {
    mockFetchAllSuccess(
      mockDashboardMetrics,
      mockThreatActivity,
      mockCarbonEmissions,
      mockCarbonSavings,
      mockThreatCategories,
      mockSecurityEvents,
      mockRecommendations,
      mockSystemHealth,
      mockCarbonEfficiency,
    )
  })

  it('shows loading spinner initially', () => {
    render(<DashboardPage />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('renders dashboard title after loading', async () => {
    render(<DashboardPage />)
    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })
  })

  it('renders metric cards after loading', async () => {
    render(<DashboardPage />)
    await waitFor(() => {
      expect(screen.getByText('Carbon Guard Score')).toBeInTheDocument()
      expect(screen.getByText('Security Risk Score')).toBeInTheDocument()
      expect(screen.getByText('Active Threats')).toBeInTheDocument()
    })
  })

  it('renders chart sections after loading', async () => {
    render(<DashboardPage />)
    await waitFor(() => {
      expect(screen.getByText('Threat Activity (24h)')).toBeInTheDocument()
      expect(screen.getByText('Carbon Emissions & Energy (24h)')).toBeInTheDocument()
    })
  })

  it('renders simulated data badge', async () => {
    render(<DashboardPage />)
    await waitFor(() => {
      expect(screen.getByText('SIMULATED DATA')).toBeInTheDocument()
    })
  })

  it('renders refresh button after loading', async () => {
    render(<DashboardPage />)
    await waitFor(() => {
      expect(screen.getByText('Refresh')).toBeInTheDocument()
    })
  })

  it('shows last updated time after loading', async () => {
    render(<DashboardPage />)
    await waitFor(() => {
      expect(screen.getByText(/Updated/)).toBeInTheDocument()
    })
  })
})
