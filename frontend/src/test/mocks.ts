import { vi } from 'vitest'

export function mockFetchSuccess(data: unknown) {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(data),
  })
}

export function mockFetchFailure(message = 'Network error') {
  globalThis.fetch = vi.fn().mockRejectedValue(new Error(message))
}

export function mockFetchTimeout() {
  globalThis.fetch = vi.fn().mockImplementation(() => {
    return new Promise((_, reject) => {
      setTimeout(() => reject(new Error('Timeout')), 100)
    })
  })
}

export function mockFetchSequence(responses: Array<{ ok: boolean; data?: unknown; error?: string }>) {
  let callIndex = 0
  globalThis.fetch = vi.fn().mockImplementation(() => {
    const resp = responses[callIndex] ?? responses[responses.length - 1]
    callIndex++
    if (resp.ok) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(resp.data),
      })
    }
    return Promise.reject(new Error(resp.error || 'Error'))
  })
}

export function mockFetchAllSuccess(...datas: unknown[]) {
  let callIndex = 0
  globalThis.fetch = vi.fn().mockImplementation(() => {
    const data = datas[callIndex] ?? datas[datas.length - 1]
    callIndex++
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(data),
    })
  })
}
