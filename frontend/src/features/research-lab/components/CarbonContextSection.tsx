import { useEffect, useState } from 'react'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import { researchApi } from '../api/researchApi'
import { SectionEmpty, SectionError, SectionLoading, StatTile } from './ResearchBits'
import { formatKilograms, formatScalar } from '../utils/format'
import type { OptimizerComparison } from '../types/research'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ok'; comparison: OptimizerComparison }

function hasOptimizedCarbon(comparison: OptimizerComparison): boolean {
  return comparison.after?.co2_kg !== undefined && comparison.after?.co2_kg !== null
}

export default function CarbonContextSection() {
  const [state, setState] = useState<LoadState>({ status: 'loading' })

  useEffect(() => {
    let cancelled = false
    researchApi
      .getOptimizerComparison()
      .then((comparison) => {
        if (!cancelled) setState({ status: 'ok', comparison })
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            status: 'error',
            message: err instanceof Error ? err.message : 'Unable to load optimizer comparison',
          })
        }
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (state.status === 'loading') {
    return (
      <Card>
        <SectionLoading label="Loading optimized carbon context…" />
      </Card>
    )
  }

  if (state.status === 'error') {
    return (
      <Card>
        <SectionError
          title="Optimizer carbon context unavailable"
          message={state.message}
        />
      </Card>
    )
  }

  const comparison = state.comparison
  const optimizedCarbon = comparison.after?.co2_kg ?? null
  const baselineCarbon = comparison.before?.co2_kg ?? null
  const carbonSaved = comparison.comparison?.co2_saved ?? null
  const reductionPct = comparison.comparison?.reduction_pct ?? null

  if (!hasOptimizedCarbon(comparison)) {
    return (
      <Card>
        <CardTitle>Carbon Context (Existing Optimizer)</CardTitle>
        <CardContent className="mt-3">
          <SectionEmpty
            title="No optimizer comparison recorded"
            message="Run workload optimization to persist a before/after carbon comparison. Nothing is generated for display."
          />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <CardTitle>Carbon Context (Existing Optimizer)</CardTitle>
          <p className="text-xs text-muted mt-1">
            Optimized carbon and carbon saved, read from the existing workload optimizer
            (GET /optimizer/comparison) — simulated scheduling over estimated energy, not
            research experiment data.
          </p>
        </div>
      </div>

      <CardContent className="mt-4">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <StatTile
            label="Baseline Carbon"
            value={formatKilograms(baselineCarbon)}
          />
          <StatTile
            label="Optimized Carbon"
            value={formatKilograms(optimizedCarbon)}
          />
          <StatTile
            label="Carbon Saved"
            value={formatKilograms(carbonSaved)}
          />
          <StatTile
            label="Reduction"
            value={formatScalar(reductionPct, 1, ' %')}
          />
        </div>

        <p className="text-[11px] text-muted mt-3">
          Security-critical workloads are never delayed or degraded for carbon savings; only
          eligible non-critical workloads may be shifted, and the carbon figures above are
          calculated from estimated energy × configured carbon intensity.
        </p>
      </CardContent>
    </Card>
  )
}
