import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { researchApi } from '../api/researchApi'
import { config } from '@/config/env'

const BASE = config.API_BASE_URL

function jsonResponse(data: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: async () => data,
    text: async () => JSON.stringify(data),
  } as unknown as Response
}

function textResponse(text: string, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: async () => JSON.parse(text),
    text: async () => text,
  } as unknown as Response
}

const fetchMock = vi.fn()

beforeEach(() => {
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('request wiring', () => {
  it('issues GET requests with the JSON content type header', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ items: [] }))
    await researchApi.listExperiments()
    expect(fetchMock).toHaveBeenCalledWith(`${BASE}/research/experiments?limit=100`, {
      headers: { 'Content-Type': 'application/json' },
    })
  })

  it('appends query parameters and skips empty values', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ items: [] }))
    await researchApi.listMarginalEnergy({
      measurement_mode: '',
      attack_type: 'ddos',
      offset: 0,
    })
    const [url] = fetchMock.mock.calls[0]
    expect(url).toContain('/research/marginal-energy?')
    expect(url).toContain('limit=200')
    expect(url).toContain('attack_type=ddos')
    expect(url).toContain('offset=0')
    expect(url).not.toContain('measurement_mode')
  })

  it('maps the control filter to control_name for amplification lists', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ items: [] }))
    await researchApi.listAmplification({ control: 'firewall' })
    const [url] = fetchMock.mock.calls[0]
    expect(url).toContain('control_name=firewall')
  })

  it('omits the query string when no parameters are present', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ attacks: [] }))
    await researchApi.listAttacks()
    const [url] = fetchMock.mock.calls[0]
    expect(url).toBe(`${BASE}/research/attacks`)
  })
})

describe('POST endpoints', () => {
  it('creates experiments with a JSON body', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ id: 1 }))
    const body = {
      name: 'exp',
      experiment_type: 'MARGINAL_ENERGY',
      attack_type: 'ddos',
      attack_intensity: 'low',
      security_controls: [],
      duration_seconds: 30,
      number_of_trials: 2,
    } as never
    await researchApi.createExperiment(body)
    expect(fetchMock).toHaveBeenCalledWith(`${BASE}/research/experiments`, {
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
      body: JSON.stringify(body),
    })
  })

  it('executes experiments by uuid', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ id: 1 }))
    await researchApi.executeExperiment('uuid-1')
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe(`${BASE}/research/experiments/uuid-1/execute`)
    expect((init as RequestInit).method).toBe('POST')
  })

  it('posts analytics computations with the request body', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ id: 'anl_1' }))
    const request = {
      source: 'amplification',
      metric: 'additional_defense_energy',
    } as never
    await researchApi.computeAnalytics(request)
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe(`${BASE}/research/analytics`)
    expect((init as RequestInit).method).toBe('POST')
    expect((init as RequestInit).body).toBe(JSON.stringify(request))
  })
})

describe('GET endpoints', () => {
  it('reads experiment status, runs and summary by uuid', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ status: 'completed' }))
    await researchApi.getExperimentStatus('uuid-1')
    await researchApi.getExperimentRuns('uuid-1')
    await researchApi.getExperimentSummary('uuid-1')
    const urls = fetchMock.mock.calls.map((call) => call[0])
    expect(urls).toEqual([
      `${BASE}/research/experiments/uuid-1/status`,
      `${BASE}/research/experiments/uuid-1/runs`,
      `${BASE}/research/experiments/uuid-1/summary`,
    ])
  })

  it('reads summary, metrics and optimizer comparison resources', async () => {
    fetchMock.mockResolvedValue(jsonResponse({}))
    await researchApi.getResearchSummary()
    await researchApi.getResearchMetrics()
    await researchApi.getOptimizerComparison()
    const urls = fetchMock.mock.calls.map((call) => call[0])
    expect(urls).toEqual([
      `${BASE}/research/summary`,
      `${BASE}/research/metrics`,
      `${BASE}/optimizer/comparison`,
    ])
  })
})

describe('error handling', () => {
  it('throws the API detail message for string details', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'Experiment not found' }, false, 404))
    await expect(researchApi.getExperiment('missing')).rejects.toThrow(
      'Experiment not found',
    )
  })

  it('falls back to an HTTP status message for non-string details', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ detail: { msg: 'invalid' } }, false, 400),
    )
    await expect(researchApi.getExperiment('bad')).rejects.toThrow(
      'Request failed (HTTP 400)',
    )
  })

  it('falls back to an HTTP status message when the body is not JSON', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => {
        throw new Error('not json')
      },
      text: async () => '<html>error</html>',
    } as unknown as Response)
    await expect(researchApi.getExperiment('x')).rejects.toThrow(
      'Request failed (HTTP 500)',
    )
  })
})

describe('exports', () => {
  it('requests CSV export text with the dataset parameter', async () => {
    fetchMock.mockResolvedValue(textResponse('attack_type,value\nddos,1\n'))
    const csv = await researchApi.exportCsv()
    const [url] = fetchMock.mock.calls[0]
    expect(url).toContain('/research/export/csv?')
    expect(url).toContain('dataset=marginal_energy')
    expect(csv).toContain('attack_type,value')
  })

  it('propagates export errors through the shared error path', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'Export unavailable' }, false, 400))
    await expect(researchApi.exportCsv()).rejects.toThrow('Export unavailable')
  })

  it('requests the JSON export payload', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ records: {} }))
    await researchApi.exportJson()
    const [url] = fetchMock.mock.calls[0]
    expect(url).toBe(`${BASE}/research/export/json`)
  })
})
