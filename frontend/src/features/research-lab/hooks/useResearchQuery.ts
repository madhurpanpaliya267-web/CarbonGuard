import { useEffect, useRef, useState } from 'react'

export interface QueryState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

function message(error: unknown): string {
  return error instanceof Error ? error.message : 'Request failed'
}

/**
 * Loads a research resource once per `key` change. The loader is kept in a ref
 * so callers may pass a fresh closure without re-triggering the request.
 */
export function useResearchQuery<T>(loader: () => Promise<T>, key: string): QueryState<T> {
  const [state, setState] = useState<QueryState<T>>({ data: null, loading: true, error: null })
  const loaderRef = useRef(loader)
  loaderRef.current = loader

  useEffect(() => {
    let cancelled = false
    setState((current) => ({ data: current.data, loading: true, error: null }))

    loaderRef
      .current()
      .then((data) => {
        if (!cancelled) setState({ data, loading: false, error: null })
      })
      .catch((error: unknown) => {
        if (!cancelled) setState({ data: null, loading: false, error: message(error) })
      })

    return () => {
      cancelled = true
    }
  }, [key])

  return state
}
