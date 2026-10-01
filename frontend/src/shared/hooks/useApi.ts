import { useState, useEffect, useCallback } from 'react'
import { apiClient } from '../utils/apiClient'

export function useApi<T>(path: string, options?: { enabled?: boolean }) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    if (options?.enabled === false) return
    try {
      setLoading(true)
      const result = await apiClient.get<T>(path)
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }, [path, options?.enabled])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return { data, loading, error, refetch: fetchData }
}
