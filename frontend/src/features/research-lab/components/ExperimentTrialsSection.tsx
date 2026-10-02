import { useEffect, useMemo, useState } from 'react'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import Badge from '@/shared/ui/Badge'
import { formatDateTime, formatNumber } from '@/shared/utils/formatters'
import { researchApi } from '../api/researchApi'
import { Field, SectionEmpty, SectionError, SectionLoading } from './ResearchBits'
import {
  formatInteger,
  formatJoules,
  formatKilograms,
  formatScalar,
  formatWatts,
  modeVariant,
  shortId,
} from '../utils/format'
import type {
  AmplificationResult,
  Experiment,
  ExperimentSummary,
  InteractionResult,
  MarginalEnergyResult,
} from '../types/research'

type SortKey = 'trial' | 'energy' | 'power' | 'carbon' | 'duration'
type SortDir = 'asc' | 'desc'

function buildCarbonByRun(
  marginal: MarginalEnergyResult[],
  interaction: InteractionResult[],
  amplification: AmplificationResult[],
): Map<number, number | null> {
  const map = new Map<number, number | null>()
  const put = (runId: number | null, carbon: number | null) => {
    if (runId !== null && !map.has(runId)) map.set(runId, carbon)
  }

  marginal.forEach((item) => {
    put(item.baseline_run_id, item.baseline_carbon_kg)
    put(item.security_run_id, item.security_carbon_kg)
  })
  interaction.forEach((item) => {
    put(item.baseline_run_id, item.carbon_baseline_kg)
    put(item.control_a_run_id, item.carbon_a_kg)
    put(item.control_b_run_id, item.carbon_b_kg)
    put(item.combined_run_id, item.carbon_ab_kg)
  })
  amplification.forEach((item) => {
    put(item.baseline_run_id, item.carbon_baseline_kg)
    put(item.defense_run_id, item.carbon_defense_kg)
  })

  return map
}

function statusVariant(status: string): 'success' | 'danger' | 'warning' | 'muted' {
  if (status === 'COMPLETED' || status === 'SUCCEEDED') return 'success'
  if (status === 'FAILED') return 'danger'
  if (status === 'RUNNING') return 'warning'
  return 'muted'
}

interface Props {
  experiments: Experiment[]
  marginal: MarginalEnergyResult[]
  interaction: InteractionResult[]
  amplification: AmplificationResult[]
}

export default function ExperimentTrialsSection({
  experiments,
  marginal,
  interaction,
  amplification,
}: Props) {
  const [selectedUuid, setSelectedUuid] = useState<string>('')
  const [summary, setSummary] = useState<ExperimentSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [sort, setSort] = useState<{ key: SortKey; dir: SortDir }>({ key: 'trial', dir: 'asc' })

  const carbonByRun = useMemo(
    () => buildCarbonByRun(marginal, interaction, amplification),
    [marginal, interaction, amplification],
  )

  useEffect(() => {
    if (!selectedUuid) {
      setSummary(null)
      setError(null)
      return
    }

    let cancelled = false
    setLoading(true)
    setError(null)
    researchApi
      .getExperimentSummary(selectedUuid)
      .then((data) => {
        if (!cancelled) setSummary(data)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setSummary(null)
          setError(err instanceof Error ? err.message : 'Unable to load experiment summary')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [selectedUuid])

  const rows = useMemo(() => {
    if (!summary) return []

    const measurementByRun = new Map<number, (typeof summary.measurements)[number]>()
    summary.measurements.forEach((measurement) => {
      if (!measurementByRun.has(measurement.run_id)) measurementByRun.set(measurement.run_id, measurement)
    })

    const effectByRun = new Map<number, (typeof summary.security_effects)[number]>()
    summary.security_effects.forEach((effect) => effectByRun.set(effect.run_id, effect))

    const query = search.trim().toLowerCase()

    const mapped = summary.runs.map((run) => {
      const measurement = measurementByRun.get(run.id)
      const effect = effectByRun.get(run.id)
      return {
        run,
        measurement,
        effect,
        energy: measurement?.energy_joules ?? null,
        power: measurement?.power_watts ?? null,
        carbon: carbonByRun.get(run.id) ?? null,
      }
    })

    const filtered = mapped.filter((row) => {
      if (statusFilter !== 'ALL' && row.run.status !== statusFilter) return false
      if (!query) return true
      const haystack = [
        row.run.run_uuid,
        row.run.attack_type,
        row.run.attack_intensity,
        row.run.security_controls ?? '',
        row.run.measurement_mode,
        row.run.workload_profile ?? '',
      ]
        .join(' ')
        .toLowerCase()
      return haystack.includes(query)
    })

    const direction = sort.dir === 'asc' ? 1 : -1
    const value = (row: (typeof filtered)[number]): number => {
      switch (sort.key) {
        case 'trial':
          return row.run.trial_number
        case 'energy':
          return row.energy ?? Number.NEGATIVE_INFINITY
        case 'power':
          return row.power ?? Number.NEGATIVE_INFINITY
        case 'carbon':
          return row.carbon ?? Number.NEGATIVE_INFINITY
        case 'duration':
          return row.run.duration_seconds ?? Number.NEGATIVE_INFINITY
      }
    }

    return [...filtered].sort((a, b) => (value(a) - value(b)) * direction)
  }, [summary, carbonByRun, search, statusFilter, sort])

  function toggleSort(key: SortKey) {
    setSort((current) =>
      current.key === key
        ? { key, dir: current.dir === 'asc' ? 'desc' : 'asc' }
        : { key, dir: 'asc' },
    )
  }

  const sortIndicator = (key: SortKey) =>
    sort.key === key ? (sort.dir === 'asc' ? ' ↑' : ' ↓') : ''

  const selectClass =
    'bg-card border border-border rounded-md px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:border-accent/50'

  if (experiments.length === 0) {
    return (
      <Card>
        <SectionEmpty
          title="No experiments recorded"
          message="Completed experiments expose per-trial runs, measurements, and security effectiveness here."
        />
      </Card>
    )
  }

  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <CardTitle>Experiment Trials</CardTitle>
          <p className="text-xs text-muted mt-1">
            Per-trial runs joined with measurements and security effectiveness. Carbon columns are
            sourced from Phase 5–7 result records where present; otherwise shown as “—”.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-muted" htmlFor="trial-experiment">
            Experiment
          </label>
          <select
            id="trial-experiment"
            className={selectClass}
            value={selectedUuid}
            onChange={(event) => setSelectedUuid(event.target.value)}
          >
            <option value="">Select an experiment…</option>
            {experiments.map((experiment) => (
              <option key={experiment.experiment_uuid} value={experiment.experiment_uuid}>
                #{experiment.id} · {experiment.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <CardContent className="mt-4 space-y-4">
        {!selectedUuid && (
          <SectionEmpty
            title="Select an experiment"
            message="Choose an experiment above to load its trial-level detail."
          />
        )}

        {loading && <SectionLoading label="Loading experiment summary…" />}

        {error && <SectionError title="Unable to load experiment summary" message={error} />}

        {summary && !loading && (
          <>
            <div className="bg-background/60 border border-border rounded-md p-4">
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <span className="text-sm font-semibold text-text-primary">
                  {summary.experiment.name}
                </span>
                <Badge variant={statusVariant(summary.experiment.status)} size="sm">
                  {summary.experiment.status}
                </Badge>
                <Badge variant={modeVariant(summary.experiment.measurement_mode)} size="sm">
                  {summary.experiment.measurement_mode}
                </Badge>
                <Badge variant="muted" size="sm">
                  {summary.experiment.experiment_type}
                </Badge>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-3">
                <Field label="Attack" value={`${summary.experiment.attack_type} / ${summary.experiment.attack_intensity}`} />
                <Field label="Trials" value={`${formatInteger(summary.runs.length)} runs`} />
                <Field
                  label="Duration"
                  value={formatScalar(summary.experiment.duration_seconds, 0, ' s')}
                />
                <Field label="Created" value={formatDateTime(summary.experiment.created_at)} />
                <Field label="Carbon Intensity" value={formatScalar(summary.experiment.carbon_intensity, 1, ' gCO₂/kWh')} />
                <Field label="Renewable" value={formatScalar(summary.experiment.renewable_pct, 1, ' %')} />
                <Field label="Software Version" value={summary.experiment.software_version ?? '—'} />
                <Field label="Random Seed" value={formatInteger(summary.experiment.random_seed)} />
              </div>
              {summary.experiment.description && (
                <p className="text-xs text-muted mt-3">{summary.experiment.description}</p>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Filter by uuid, attack, controls…"
                className={`${selectClass} min-w-64`}
                aria-label="Filter trials"
              />
              <select
                className={selectClass}
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                aria-label="Filter by status"
              >
                <option value="ALL">All statuses</option>
                <option value="COMPLETED">Completed</option>
                <option value="RUNNING">Running</option>
                <option value="FAILED">Failed</option>
                <option value="PENDING">Pending</option>
              </select>
              <span className="text-[11px] text-muted">
                {formatInteger(rows.length)} of {formatInteger(summary.runs.length)} runs shown
              </span>
            </div>

            {rows.length === 0 ? (
              <SectionEmpty
                title="No runs match the current filters"
                message="Adjust the search text or status filter to see trial runs."
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border text-muted uppercase tracking-wider">
                      <th
                        className="text-left px-2 py-1.5 cursor-pointer hover:text-text-primary"
                        onClick={() => toggleSort('trial')}
                      >
                        Trial{sortIndicator('trial')}
                      </th>
                      <th className="text-left px-2 py-1.5">Run</th>
                      <th className="text-left px-2 py-1.5">Attack</th>
                      <th className="text-left px-2 py-1.5">Controls</th>
                      <th className="text-right px-2 py-1.5">Workload</th>
                      <th
                        className="text-right px-2 py-1.5 cursor-pointer hover:text-text-primary"
                        onClick={() => toggleSort('duration')}
                      >
                        Duration{sortIndicator('duration')}
                      </th>
                      <th
                        className="text-right px-2 py-1.5 cursor-pointer hover:text-text-primary"
                        onClick={() => toggleSort('energy')}
                      >
                        Energy{sortIndicator('energy')}
                      </th>
                      <th
                        className="text-right px-2 py-1.5 cursor-pointer hover:text-text-primary"
                        onClick={() => toggleSort('power')}
                      >
                        Power{sortIndicator('power')}
                      </th>
                      <th
                        className="text-right px-2 py-1.5 cursor-pointer hover:text-text-primary"
                        onClick={() => toggleSort('carbon')}
                      >
                        Carbon{sortIndicator('carbon')}
                      </th>
                      <th className="text-right px-2 py-1.5">Detection</th>
                      <th className="text-left px-2 py-1.5">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => (
                      <tr key={row.run.id} className="border-b border-border/50">
                        <td className="px-2 py-1.5 text-text-primary">
                          {formatInteger(row.run.trial_number)}
                        </td>
                        <td className="px-2 py-1.5 font-mono text-muted" title={row.run.run_uuid}>
                          {shortId(row.run.run_uuid)}
                        </td>
                        <td className="px-2 py-1.5">
                          {row.run.attack_type} / {row.run.attack_intensity}
                        </td>
                        <td className="px-2 py-1.5 text-muted">
                          {row.run.security_controls ?? '—'}
                        </td>
                        <td className="px-2 py-1.5 text-right">
                          {row.run.workload_value !== null
                            ? `${formatNumber(row.run.workload_value, 2)} ${row.run.workload_unit ?? ''}`
                            : '—'}
                        </td>
                        <td className="px-2 py-1.5 text-right">
                          {formatScalar(row.run.duration_seconds, 1, ' s')}
                        </td>
                        <td className="px-2 py-1.5 text-right">
                          {row.energy !== null ? formatJoules(row.energy) : '—'}
                        </td>
                        <td className="px-2 py-1.5 text-right">
                          {row.power !== null ? formatWatts(row.power) : '—'}
                        </td>
                        <td className="px-2 py-1.5 text-right">
                          {row.carbon !== null ? formatKilograms(row.carbon) : '—'}
                        </td>
                        <td className="px-2 py-1.5 text-right">
                          {row.effect?.detection_rate !== null && row.effect?.detection_rate !== undefined
                            ? formatNumber(row.effect.detection_rate * 100, 1)
                            : '—'}
                        </td>
                        <td className="px-2 py-1.5">
                          <Badge variant={statusVariant(row.run.status)} size="sm">
                            {row.run.status}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <p className="text-[11px] text-muted leading-relaxed">
              Energy values are ESTIMATED unless the experiment measurement mode is MEASURED.
              Missing values are shown as “—” rather than estimated in the UI.
            </p>
          </>
        )}
      </CardContent>
    </Card>
  )
}
