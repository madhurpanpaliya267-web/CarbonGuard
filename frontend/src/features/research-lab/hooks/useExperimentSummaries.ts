import { useEffect, useRef, useState } from 'react'
import { researchApi } from '../api/researchApi'
import type { Experiment, ExperimentSummary } from '../types/research'

export interface ExperimentSummariesState {
  loading: boolean
  error: string | null
  byUuid: Map<string, ExperimentSummary>
}

/**
 * Loads per-experiment summaries (runs + measurements) so trial-level energy
 * can be shown in research tables. Values come from the API only.
 */
export function useExperimentSummaries(experiments: Experiment[]): ExperimentSummariesState {
  const [state, setState] = useState<ExperimentSummariesState>({
    loading: false,
    error: null,
    byUuid: new Map(),
  })
  const key = experiments.map((experiment) => experiment.experiment_uuid).join('|')
  const experimentsRef = useRef(experiments)
  experimentsRef.current = experiments

  useEffect(() => {
    if (!key) {
      setState({ loading: false, error: null, byUuid: new Map() })
      return
    }

    let cancelled = false
    setState((current) => ({ ...current, loading: true, error: null }))

    const targets = experimentsRef.current
    Promise.all(
      targets.map((experiment) =>
        researchApi
          .getExperimentSummary(experiment.experiment_uuid)
          .then((summary) => ({ uuid: experiment.experiment_uuid, summary, error: null }))
          .catch((error: unknown) => ({
            uuid: experiment.experiment_uuid,
            summary: null,
            error: error instanceof Error ? error.message : 'Request failed',
          })),
      ),
    ).then((results) => {
      if (cancelled) return
      const byUuid = new Map<string, ExperimentSummary>()
      let failed = 0
      results.forEach((result) => {
        if (result.summary) byUuid.set(result.uuid, result.summary)
        else failed += 1
      })
      setState({
        loading: false,
        error: failed > 0 ? `Could not load ${failed} experiment summary record(s)` : null,
        byUuid,
      })
    })

    return () => {
      cancelled = true
    }
  }, [key])

  return state
}
