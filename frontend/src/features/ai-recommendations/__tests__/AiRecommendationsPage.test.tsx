import { describe, it, expect, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import AiRecommendationsPage from '../components/AiRecommendationsPage'
import { mockFetchAllSuccess } from '@/test/mocks'

const mockRecommendations = [
  {
    id: 1, timestamp: new Date().toISOString(), recommendation_type: 'security',
    recommendation: 'Increase monitoring', priority: 'high' as const,
    reason: 'Threat activity increased', expected_security_impact: 'Better detection',
    expected_carbon_impact: null, confidence: 0.88, factors_json: '[]',
    is_read: false, is_dismissed: false,
  },
  {
    id: 2, timestamp: new Date().toISOString(), recommendation_type: 'carbon',
    recommendation: 'Shift workloads', priority: 'medium' as const,
    reason: 'High carbon intensity', expected_security_impact: null,
    expected_carbon_impact: '18% reduction', confidence: 0.82, factors_json: '[]',
    is_read: true, is_dismissed: false,
  },
]

describe('AiRecommendationsPage', () => {
  beforeEach(() => {
    mockFetchAllSuccess(mockRecommendations)
  })

  it('shows loading spinner initially', () => {
    render(<AiRecommendationsPage />)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('renders page title after loading', async () => {
    render(<AiRecommendationsPage />)
    await waitFor(() => {
      expect(screen.getByText('AI Recommendations')).toBeInTheDocument()
    })
  })

  it('renders recommendations after loading', async () => {
    render(<AiRecommendationsPage />)
    await waitFor(() => {
      expect(screen.getByText('Increase monitoring')).toBeInTheDocument()
      expect(screen.getByText('Shift workloads')).toBeInTheDocument()
    })
  })

  it('renders rule-based engine badge', async () => {
    render(<AiRecommendationsPage />)
    await waitFor(() => {
      expect(screen.getByText('RULE-BASED ENGINE')).toBeInTheDocument()
    })
  })

  it('renders filters section', async () => {
    render(<AiRecommendationsPage />)
    await waitFor(() => {
      expect(screen.getByText('Filters:')).toBeInTheDocument()
    })
  })

  it('renders generate button', async () => {
    render(<AiRecommendationsPage />)
    await waitFor(() => {
      expect(screen.getByText('Generate')).toBeInTheDocument()
    })
  })

  it('renders mark read buttons for unread items', async () => {
    render(<AiRecommendationsPage />)
    await waitFor(() => {
      const markReadButtons = screen.getAllByText('Mark Read')
      expect(markReadButtons.length).toBeGreaterThanOrEqual(1)
    })
  })

  it('renders dismiss buttons', async () => {
    render(<AiRecommendationsPage />)
    await waitFor(() => {
      const dismissButtons = screen.getAllByText('Dismiss')
      expect(dismissButtons.length).toBe(2)
    })
  })
})
