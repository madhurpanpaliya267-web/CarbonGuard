import { describe, it, expect, beforeEach, beforeAll, afterAll, vi } from 'vitest'
import { screen, waitFor, fireEvent } from '@testing-library/react'
import { render } from '@/test/page-test-utils'
import ResearchDatasetPage from '../components/ResearchDatasetPage'
import { installFetchMock } from './researchFixtures'

beforeAll(() => {
  Object.defineProperty(URL, 'createObjectURL', {
    configurable: true,
    writable: true,
    value: vi.fn(() => 'blob:mock'),
  })
  Object.defineProperty(URL, 'revokeObjectURL', {
    configurable: true,
    writable: true,
    value: vi.fn(),
  })
})

afterAll(() => {
  vi.unstubAllGlobals()
})

function clickExport(name: string | RegExp) {
  fireEvent.click(screen.getByRole('button', { name }))
}

describe('ResearchDatasetPage', () => {
  beforeEach(() => {
    window.history.pushState({}, '', '/')
    installFetchMock()
  })

  it('renders export controls and the experiments dataset table', async () => {
    render(<ResearchDatasetPage />)

    await waitFor(() => {
      expect(screen.getByTestId('research-dataset-page')).toBeInTheDocument()
      expect(screen.getByText('Export')).toBeInTheDocument()
      expect(screen.getByText('Dataset')).toBeInTheDocument()
      expect(screen.getByText('DDoS Baseline vs WAF')).toBeInTheDocument()
      expect(screen.getByText('1 rows')).toBeInTheDocument()
    })
  })

  it('switches dataset tabs to show marginal energy rows', async () => {
    render(<ResearchDatasetPage />)

    const tab = await screen.findByRole('tab', { name: 'Marginal energy' })
    fireEvent.click(tab)

    await waitFor(() => {
      expect(screen.getByText('marginal-energy-v1')).toBeInTheDocument()
      expect(screen.getByText('350.00 J')).toBeInTheDocument()
      expect(screen.getByText('41.0 mg')).toBeInTheDocument()
    })
  })

  it('filters rows with the search box and shows an empty state', async () => {
    render(<ResearchDatasetPage />)

    const search = await screen.findByLabelText('Search dataset')
    fireEvent.change(search, { target: { value: 'nomatch' } })

    await waitFor(() => {
      expect(screen.getByText('No rows match this search')).toBeInTheDocument()
    })
  })

  it('exports a CSV file from the research API', async () => {
    render(<ResearchDatasetPage />)

    await screen.findByRole('button', { name: 'CSV · Experiments' })
    clickExport('CSV · Experiments')

    await waitFor(() => {
      expect(screen.getByText('experiments CSV exported.')).toBeInTheDocument()
    })
    expect(URL.createObjectURL).toHaveBeenCalled()
  })

  it('reports an empty dataset instead of downloading an empty CSV', async () => {
    installFetchMock({ csvBody: '   ' })
    render(<ResearchDatasetPage />)

    await screen.findByRole('button', { name: 'CSV · Marginal energy' })
    clickExport('CSV · Marginal energy')

    await waitFor(() => {
      expect(screen.getByTestId('export-error')).toHaveTextContent('is empty')
    })
  })

  it('exports the combined JSON payload with record counts', async () => {
    render(<ResearchDatasetPage />)

    await screen.findByRole('button', { name: /JSON · all datasets/ })
    clickExport(/JSON · all datasets/)

    await waitFor(() => {
      expect(screen.getByText('JSON export completed — 4 records.')).toBeInTheDocument()
    })
  })

  it('reports API errors from the export endpoint', async () => {
    installFetchMock({ fail: ['/export/csv'] })
    render(<ResearchDatasetPage />)

    await screen.findByRole('button', { name: 'CSV · Experiments' })
    clickExport('CSV · Experiments')

    await waitFor(() => {
      expect(screen.getByTestId('export-error')).toHaveTextContent('Network error')
    })
  })
})
