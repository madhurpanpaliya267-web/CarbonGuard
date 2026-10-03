import { describe, it, expect, beforeEach, vi } from 'vitest'
import { api } from '../api'
import { apiClient } from '../apiClient'
import type { OrchestrationResult } from '../../types/common'

vi.mock('../apiClient', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

const postMock = vi.mocked(apiClient.post)

beforeEach(() => {
  postMock.mockReset()
})

describe('api.runPipeline (Phase 13 orchestration integration)', () => {
  it('posts to the orchestration run endpoint with the attack type only by default', async () => {
    postMock.mockResolvedValue({} as never)
    await api.runPipeline('ddos')

    expect(postMock).toHaveBeenCalledWith('/orchestration/run', { attack_type: 'ddos' })
    const payload = postMock.mock.calls[0][1] as Record<string, unknown>
    expect(payload).not.toHaveProperty('intensity')
    expect(payload).not.toHaveProperty('record_research')
    expect(payload).not.toHaveProperty('experiment_uuid')
  })

  it('includes the intensity when provided', async () => {
    postMock.mockResolvedValue({} as never)
    await api.runPipeline('port_scan', { intensity: 'high' })

    expect(postMock).toHaveBeenCalledWith('/orchestration/run', {
      attack_type: 'port_scan',
      intensity: 'high',
    })
    const payload = postMock.mock.calls[0][1] as Record<string, unknown>
    expect(payload).not.toHaveProperty('record_research')
  })

  it('records the research observation with the target experiment uuid', async () => {
    postMock.mockResolvedValue({} as never)
    await api.runPipeline('ddos', {
      intensity: 'medium',
      recordResearch: true,
      experimentUuid: 'exp-uuid-1',
    })

    expect(postMock).toHaveBeenCalledWith('/orchestration/run', {
      attack_type: 'ddos',
      intensity: 'medium',
      record_research: true,
      experiment_uuid: 'exp-uuid-1',
    })
  })

  it('allows record_research without an experiment uuid', async () => {
    postMock.mockResolvedValue({} as never)
    await api.runPipeline('ddos', { recordResearch: true })

    const payload = postMock.mock.calls[0][1] as Record<string, unknown>
    expect(payload.attack_type).toBe('ddos')
    expect(payload.record_research).toBe(true)
    expect(payload.experiment_uuid).toBeUndefined()
    expect(payload).not.toHaveProperty('intensity')
  })

  it('returns the orchestration result from the API client unchanged', async () => {
    const result = {
      run_id: 7,
      attack_type: 'ddos',
      research: { status: 'recorded', run_id: 42, trial_number: 1 },
    } as unknown as OrchestrationResult
    postMock.mockResolvedValue(result)

    await expect(api.runPipeline('ddos')).resolves.toBe(result)
  })
})
