import { describe, it, expect, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import MarginalEnergyPage from '../components/MarginalEnergyPage'
import InteractionAnalysisPage from '../components/InteractionAnalysisPage'
import DefenseAmplificationPage from '../components/DefenseAmplificationPage'
import { installFetchMock } from './researchFixtures'

describe('MarginalEnergyPage', () => {
  beforeEach(() => {
    window.history.pushState({}, '', '/')
    installFetchMock()
  })

  it('renders the Phase 5 attribution section with workload and intensity charts', async () => {
    render(<MarginalEnergyPage />)

    await waitFor(() => {
      expect(screen.getByTestId('marginal-energy-page')).toBeInTheDocument()
      expect(
        screen.getByText('Marginal Energy Attribution (Phase 5)'),
      ).toBeInTheDocument()
      expect(screen.getByText('Baseline vs Security Energy')).toBeInTheDocument()
      expect(screen.getByText('Marginal Energy by Attack Intensity')).toBeInTheDocument()
      expect(screen.getByText('Marginal Energy vs Workload')).toBeInTheDocument()
    })
  })

  it('labels estimated provenance and carbon per workload', async () => {
    render(<MarginalEnergyPage />)

    await waitFor(() => {
      expect(screen.getByText('Marginal Carbon per Workload')).toBeInTheDocument()
      expect(screen.getByText('410.0 µg/req/s')).toBeInTheDocument()
      expect(screen.getAllByText('calculated from estimated energy').length).toBeGreaterThan(0)
      expect(screen.getAllByText('ESTIMATED').length).toBeGreaterThan(0)
    })
  })

  it('shows a provenance badge and filter controls', async () => {
    render(<MarginalEnergyPage />)

    await waitFor(() => {
      expect(screen.getByLabelText(/attack type/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/measurement mode/i)).toBeInTheDocument()
      expect(screen.getByText('Reset filters')).toBeInTheDocument()
    })
  })

  it('surfaces a source error when marginal energy requests fail', async () => {
    installFetchMock({ fail: ['/marginal-energy'] })
    render(<MarginalEnergyPage />)

    await waitFor(() => {
      expect(screen.getByText('Unable to load research data')).toBeInTheDocument()
    })
  })
})

describe('InteractionAnalysisPage', () => {
  beforeEach(() => {
    window.history.pushState({}, '', '/')
    installFetchMock()
  })

  it('renders the Phase 6 section with backend interpretation and pair chart', async () => {
    render(<InteractionAnalysisPage />)

    await waitFor(() => {
      expect(screen.getByTestId('interaction-analysis-page')).toBeInTheDocument()
      expect(screen.getByText('Security-Control Interaction (Phase 6)')).toBeInTheDocument()
      expect(screen.getAllByText('super-additive').length).toBeGreaterThan(0)
      expect(screen.getByText('Control Combination Energy')).toBeInTheDocument()
      expect(screen.getByText('Interaction Effect by Control Pair')).toBeInTheDocument()
      expect(
        screen.getByText('Interaction Effect across Attack Intensity'),
      ).toBeInTheDocument()
      expect(screen.getByText('Interaction Results')).toBeInTheDocument()
    })
  })

  it('renders interaction carbon per workload with its basis', async () => {
    render(<InteractionAnalysisPage />)

    await waitFor(() => {
      expect(screen.getByText('Interaction Carbon per Workload')).toBeInTheDocument()
      expect(screen.getAllByText('calculated from estimated energy').length).toBeGreaterThan(0)
    })
  })

  it('surfaces a source error when interaction requests fail', async () => {
    installFetchMock({ fail: ['/interaction-effects'] })
    render(<InteractionAnalysisPage />)

    await waitFor(() => {
      expect(screen.getByText('Unable to load research data')).toBeInTheDocument()
    })
  })
})

describe('DefenseAmplificationPage', () => {
  beforeEach(() => {
    window.history.pushState({}, '', '/')
    installFetchMock()
  })

  it('renders the Phase 7 section with stored statistics and control chart', async () => {
    render(<DefenseAmplificationPage />)

    await waitFor(() => {
      expect(screen.getByTestId('defense-amplification-page')).toBeInTheDocument()
      expect(
        screen.getByText('Defense Energy Amplification (Phase 7)'),
      ).toBeInTheDocument()
      expect(screen.getByText('Trials (paired)')).toBeInTheDocument()
      expect(screen.getByText('Attack Intensity vs Additional Defense Energy')).toBeInTheDocument()
      expect(screen.getByText('Defense Energy Amplification by Control')).toBeInTheDocument()
    })
  })

  it('renders defense carbon per workload and formula provenance', async () => {
    render(<DefenseAmplificationPage />)

    await waitFor(() => {
      expect(screen.getByText('Defense Carbon per Workload')).toBeInTheDocument()
      expect(screen.getAllByText('calculated from estimated energy').length).toBeGreaterThan(0)
    })
  })

  it('surfaces a source error when amplification requests fail', async () => {
    installFetchMock({ fail: ['/defense-energy-amplification'] })
    render(<DefenseAmplificationPage />)

    await waitFor(() => {
      expect(screen.getByText('Unable to load research data')).toBeInTheDocument()
    })
  })
})
