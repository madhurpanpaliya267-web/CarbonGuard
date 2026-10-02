import { describe, it, expect, beforeEach } from 'vitest'
import { screen, waitFor, fireEvent } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import { Routes, Route } from 'react-router-dom'
import ExperimentsPage from '../components/ExperimentsPage'
import ExperimentDetailPage from '../components/ExperimentDetailPage'
import { installFetchMock } from './researchFixtures'

describe('ExperimentsPage', () => {
  beforeEach(() => {
    window.history.pushState({}, '', '/')
    installFetchMock()
  })

  it('renders the experiment runner wizard and history table', async () => {
    render(<ExperimentsPage />)

    await waitFor(() => {
      expect(screen.getByTestId('experiments-page')).toBeInTheDocument()
      expect(screen.getByText('Experiment Runner')).toBeInTheDocument()
      expect(screen.getByText('Experiment History')).toBeInTheDocument()
      expect(screen.getByText(/select attack/i)).toBeInTheDocument()
      expect(screen.getAllByText(/safe synthetic simulation/i).length).toBeGreaterThan(0)
    })
  })

  it('lists stored experiments with API-provided energy', async () => {
    render(<ExperimentsPage />)

    await waitFor(() => {
      expect(screen.getByText('DDoS Baseline vs WAF')).toBeInTheDocument()
    })
    await waitFor(() => {
      expect(screen.getByText('1200.50 J')).toBeInTheDocument()
    })
  })

  it('reports a validation error when no attack is selected', async () => {
    render(<ExperimentsPage />)

    const runButton = await screen.findByRole('button', { name: /run experiment/i })
    fireEvent.click(runButton)

    await waitFor(() => {
      expect(screen.getByText('Select an attack type.')).toBeInTheDocument()
    })
  })

  it('creates, executes and shows results for a configured experiment', async () => {
    render(<ExperimentsPage />)

    const attackSelect = await screen.findByLabelText(/1\. attack/i)
    fireEvent.change(attackSelect, { target: { value: 'ddos' } })
    fireEvent.change(screen.getByLabelText(/2\. intensity/i), { target: { value: 'MEDIUM' } })

    fireEvent.click(screen.getByRole('button', { name: /run experiment/i }))

    await waitFor(
      () => {
        expect(screen.getByTestId('runner-results')).toBeInTheDocument()
        expect(screen.getByText(/experiment saved/i)).toBeInTheDocument()
        expect(screen.getByText('Trial Count')).toBeInTheDocument()
        expect(screen.getByText('Carbon Basis')).toBeInTheDocument()
      },
      { timeout: 5000 },
    )
  })

  it('shows a failed source error when the experiment list fails', async () => {
    installFetchMock({ fail: ['/research/experiments?'] })
    render(<ExperimentsPage />)

    await waitFor(() => {
      expect(screen.getByText('Unable to load experiments')).toBeInTheDocument()
    })
  })
})

describe('ExperimentDetailPage', () => {
  beforeEach(() => {
    window.history.pushState({}, '', '/research-lab/experiments/exp-uuid-1')
    installFetchMock()
  })

  it('renders configuration, trials and statistics for a stored experiment', async () => {
    render(
      <Routes>
        <Route path="/research-lab/experiments/:id" element={<ExperimentDetailPage />} />
      </Routes>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('experiment-detail-page')).toBeInTheDocument()
      expect(screen.getByText('Configuration & provenance')).toBeInTheDocument()
      expect(screen.getByText('Trials & energy')).toBeInTheDocument()
      expect(screen.getByText('Descriptive statistics')).toBeInTheDocument()
      expect(screen.getByText('Marginal energy')).toBeInTheDocument()
      expect(screen.getByText('Interaction analysis')).toBeInTheDocument()
      expect(screen.getByText('Defense amplification')).toBeInTheDocument()
    })
  })

  it('shows measured values, provenance and per-trial rows', async () => {
    render(
      <Routes>
        <Route path="/research-lab/experiments/:id" element={<ExperimentDetailPage />} />
      </Routes>,
    )

    await waitFor(() => {
      expect(screen.getAllByText('1200.50 J').length).toBeGreaterThan(0)
      expect(screen.getByText('140.1 mg')).toBeInTheDocument()
      expect(screen.getByText(/run-uuid/)).toBeInTheDocument()
      expect(screen.getAllByText('ESTIMATED').length).toBeGreaterThan(0)
      expect(screen.getAllByText(/not live grid telemetry/).length).toBeGreaterThan(0)
    })
  })

  it('renders backend statistics without inventing missing values', async () => {
    render(
      <Routes>
        <Route path="/research-lab/experiments/:id" element={<ExperimentDetailPage />} />
      </Routes>,
    )

    await waitFor(() => {
      expect(screen.getByText('Marginal energy (J)')).toBeInTheDocument()
      expect(screen.getByText('Interaction effect (J)')).toBeInTheDocument()
      expect(screen.getByText('Additional defense energy (J)')).toBeInTheDocument()
      expect(screen.getAllByText(/95% CI \[/).length).toBeGreaterThan(0)
      expect(
        screen.getAllByText(/Paired t-test: p = 0\.0040/).length,
      ).toBeGreaterThan(0)
    })
  })

  it('shows an error state when the experiment cannot be loaded', async () => {
    installFetchMock({ fail: ['/experiments/exp-uuid-1'] })
    render(
      <Routes>
        <Route path="/research-lab/experiments/:id" element={<ExperimentDetailPage />} />
      </Routes>,
    )

    await waitFor(() => {
      expect(screen.getByText('Unable to load this experiment')).toBeInTheDocument()
      expect(screen.getByText('Network error')).toBeInTheDocument()
    })
  })
})
