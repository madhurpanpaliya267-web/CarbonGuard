import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useResearchQuery } from '../hooks/useResearchQuery'
import { useResearchLabData } from '../hooks/useResearchLabData'
import { useExperimentSummaries } from '../hooks/useExperimentSummaries'
import type { Experiment } from '../types/research'

function ok(data: unknown): Response {
  return {
    ok: true,
    status: 200,
    json: async () => data,
    text: async () => JSON.stringify(data),
  } as unknown as Response
}

function fail(status: number, detail: string): Response {
  return {
    ok: false,
    status,
    json: async () => ({ detail }),
    text: async () => JSON.stringify({ detail }),
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

describe('useResearchQuery', () => {
  it('loads data and resolves to a success state', async () => {
    const loader = vi.fn().mockResolvedValue('payload')
    const { result } = renderHook(() => useResearchQuery(loader, 'key-1'))

    expect(result.current.loading).toBe(true)
    expect(result.current.data).toBeNull()

    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.data).toBe('payload')
    expect(result.current.error).toBeNull()
    expect(loader).toHaveBeenCalledTimes(1)
  })

  it('surfaces Error messages in the error state', async () => {
    const loader = vi.fn().mockRejectedValue(new Error('server down'))
    const { result } = renderHook(() => useResearchQuery(loader, 'key-1'))

    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.error).toBe('server down')
    expect(result.current.data).toBeNull()
  })

  it('falls back to a generic message for non-Error rejections', async () => {
    const loader = vi.fn().mockRejectedValue('plain string')
    const { result } = renderHook(() => useResearchQuery(loader, 'key-1'))

    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.error).toBe('Request failed')
    expect(result.current.data).toBeNull()
  })

  it('refetches when the key changes', async () => {
    const loader = vi.fn().mockResolvedValueOnce('first').mockResolvedValueOnce('second')
    const { result, rerender } = renderHook(
      ({ key }: { key: string }) => useResearchQuery(loader, key),
      { initialProps: { key: 'key-1' } },
    )

    await waitFor(() => expect(result.current.data).toBe('first'))

    rerender({ key: 'key-2' })
    expect(result.current.loading).toBe(true)

    await waitFor(() => expect(result.current.data).toBe('second'))
    expect(loader).toHaveBeenCalledTimes(2)
    expect(result.current.error).toBeNull()
  })

  it('does not refetch when only the loader closure changes', async () => {
    const firstLoader = vi.fn().mockResolvedValue('value')
    const secondLoader = vi.fn().mockResolvedValue('value')
    const { result, rerender } = renderHook(
      ({ loader, key }: { loader: () => Promise<string>; key: string }) =>
        useResearchQuery(loader, key),
      { initialProps: { loader: firstLoader, key: 'stable' } },
    )

    await waitFor(() => expect(result.current.data).toBe('value'))

    rerender({ loader: secondLoader, key: 'stable' })
    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(firstLoader).toHaveBeenCalledTimes(1)
    expect(secondLoader).not.toHaveBeenCalled()
  })
})

describe('useResearchLabData', () => {
  function routeAll(): void {
    fetchMock.mockImplementation((url: string) => {
      const target = String(url)
      if (target.includes('/research/experiments')) return Promise.resolve(ok({ items: [{ id: 1 }] }))
      if (target.includes('/research/attacks')) return Promise.resolve(ok({ attacks: [{ attack_type: 'ddos' }] }))
      if (target.includes('/research/controls')) return Promise.resolve(ok({ controls: [{ control_id: 'firewall' }] }))
      if (target.includes('/research/marginal-energy')) return Promise.resolve(ok({ items: [{ id: 1 }] }))
      if (target.includes('/research/interaction-effects')) return Promise.resolve(ok({ items: [{ id: 2 }] }))
      if (target.includes('/research/defense-energy-amplification')) return Promise.resolve(ok({ items: [{ id: 3 }] }))
      return Promise.reject(new Error(`unexpected url: ${target}`))
    })
  }

  it('loads all six research sources in parallel', async () => {
    routeAll()
    const { result } = renderHook(() => useResearchLabData())

    expect(result.current.loading).toBe(true)

    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.experiments).toHaveLength(1)
    expect(result.current.attacks).toHaveLength(1)
    expect(result.current.controls).toHaveLength(1)
    expect(result.current.marginal).toHaveLength(1)
    expect(result.current.interaction).toHaveLength(1)
    expect(result.current.amplification).toHaveLength(1)
    expect(Object.values(result.current.errors)).toEqual([
      null,
      null,
      null,
      null,
      null,
      null,
    ])
    expect(fetchMock).toHaveBeenCalledTimes(6)
  })

  it('records a per-source error without discarding the other sources', async () => {
    fetchMock.mockImplementation((url: string) => {
      const target = String(url)
      if (target.includes('/research/attacks')) {
        return Promise.resolve(fail(500, 'Server broke'))
      }
      return routeOk(target)
    })

    const { result } = renderHook(() => useResearchLabData())
    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.errors.attacks).toBe('Server broke')
    expect(result.current.errors.experiments).toBeNull()
    expect(result.current.experiments).toHaveLength(1)
    expect(result.current.attacks).toHaveLength(0)
  })

  it('refetches when the refresh key changes', async () => {
    routeAll()
    const { rerender } = renderHook(({ refreshKey }: { refreshKey: number }) =>
      useResearchLabData(refreshKey), { initialProps: { refreshKey: 0 } })

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(6))

    rerender({ refreshKey: 1 })
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(12))
  })
})

function routeOk(target: string): Promise<Response> {
  if (target.includes('/research/experiments')) return Promise.resolve(ok({ items: [{ id: 1 }] }))
  if (target.includes('/research/attacks')) return Promise.resolve(ok({ attacks: [] }))
  if (target.includes('/research/controls')) return Promise.resolve(ok({ controls: [] }))
  if (target.includes('/research/marginal-energy')) return Promise.resolve(ok({ items: [] }))
  if (target.includes('/research/interaction-effects')) return Promise.resolve(ok({ items: [] }))
  if (target.includes('/research/defense-energy-amplification')) return Promise.resolve(ok({ items: [] }))
  return Promise.reject(new Error(`unexpected url: ${target}`))
}

describe('useExperimentSummaries', () => {
  const experimentWith = (uuid: string) =>
    ({ experiment_uuid: uuid }) as unknown as Experiment

  it('does not fetch for an empty experiment list', async () => {
    const { result } = renderHook(() => useExperimentSummaries([]))
    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.byUuid.size).toBe(0)
    expect(result.current.error).toBeNull()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('loads one summary per experiment keyed by uuid', async () => {
    fetchMock.mockImplementation((url: string) => {
      const target = String(url)
      if (target.endsWith('/research/experiments/u1/summary')) {
        return Promise.resolve(ok({ runs: [{ id: 1 }] }))
      }
      if (target.endsWith('/research/experiments/u2/summary')) {
        return Promise.resolve(ok({ runs: [{ id: 2 }, { id: 3 }] }))
      }
      return Promise.reject(new Error(`unexpected url: ${target}`))
    })

    const experiments = [experimentWith('u1'), experimentWith('u2')]
    const { result } = renderHook(() => useExperimentSummaries(experiments))

    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.byUuid.size).toBe(2)
    expect(result.current.error).toBeNull()
    expect(fetchMock).toHaveBeenCalledTimes(2)

    const summary1 = result.current.byUuid.get('u1')
    const summary2 = result.current.byUuid.get('u2')
    expect(summary1?.runs).toHaveLength(1)
    expect(summary2?.runs).toHaveLength(2)
  })

  it('reports how many summaries failed while keeping the successes', async () => {
    fetchMock.mockImplementation((url: string) => {
      const target = String(url)
      if (target.endsWith('/research/experiments/u1/summary')) {
        return Promise.resolve(ok({ runs: [] }))
      }
      if (target.endsWith('/research/experiments/u2/summary')) {
        return Promise.resolve(fail(404, 'Not found'))
      }
      return Promise.reject(new Error(`unexpected url: ${target}`))
    })

    const experiments = [experimentWith('u1'), experimentWith('u2')]
    const { result } = renderHook(() => useExperimentSummaries(experiments))

    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.error).toBe('Could not load 1 experiment summary record(s)')
    expect(result.current.byUuid.size).toBe(1)
    expect(result.current.byUuid.has('u1')).toBe(true)
  })
})
