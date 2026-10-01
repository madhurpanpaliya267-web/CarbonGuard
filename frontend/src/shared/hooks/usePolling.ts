import { useState, useEffect, useCallback, useRef } from 'react'
import { apiClient } from '../utils/apiClient'

export function usePolling<T>(path: string, intervalMs: number = 10000) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchData = useCallback(async () => {
    try {
      const result = await apiClient.get<T>(path)
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }, [path])

  useEffect(() => {
    fetchData()
    intervalRef.current = setInterval(fetchData, intervalMs)
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [fetchData, intervalMs])

  return { data, loading, error, refetch: fetchData }
}
