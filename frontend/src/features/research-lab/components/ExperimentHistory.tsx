import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { FlaskConical, Search } from 'lucide-react'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import Badge from '@/shared/ui/Badge'
import { formatDateTime } from '@/shared/utils/formatters'
import { SectionEmpty, SectionError, SectionLoading, controlClass } from './ResearchBits'
import { formatJoules } from '../utils/format'
import { sumEnergyJoules } from '../utils/researchMetrics'
import { useExperimentSummaries } from '../hooks/useExperimentSummaries'
import type { Experiment } from '../types/research'

const PAGE_SIZE = 15

const SORT_OPTIONS = [
  { value: 'created_desc', label: 'Newest first' },
  { value: 'created_asc', label: 'Oldest first' },
  { value: 'name', label: 'Name (A–Z)' },
  { value: 'status', label: 'Status' },
]

function statusVariant(status: string): 'success' | 'danger' | 'warning' | 'muted' {
  if (status === 'COMPLETED' || status === 'completed') return 'success'
  if (status === 'FAILED' || status === 'failed') return 'danger'
  if (status === 'RUNNING' || status === 'running') return 'warning'
  return 'muted'
}

function typeLabel(type: string): string {
  if (type === 'MARGINAL_ENERGY') return 'Marginal energy'
  if (type === 'INTERACTION') return 'Interaction'
  if (type === 'DEFENSE_AMPLIFICATION') return 'Defense amplification'
  return type
}

export default function ExperimentHistory({
  experiments,
  loading,
  error,
}: {
  experiments: Experiment[]
  loading: boolean
  error: string | null
}) {
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [sort, setSort] = useState('created_desc')
  const [page, setPage] = useState(0)

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase()
    const result = experiments.filter((experiment) => {
      if (typeFilter && experiment.experiment_type !== typeFilter) return false
      if (statusFilter && experiment.status !== statusFilter) return false
      if (!needle) return true
      return [
        experiment.name,
        experiment.attack_type,
        experiment.attack_intensity,
        experiment.experiment_uuid,
        experiment.experiment_type,
      ].some((value) => value.toLowerCase().includes(needle))
    })

    const sorted = [...result]
    sorted.sort((a, b) => {
      if (sort === 'name') return a.name.localeCompare(b.name)
      if (sort === 'status') return a.status.localeCompare(b.status)
      const delta = new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      return sort === 'created_asc' ? delta : -delta
    })
    return sorted
  }, [experiments, search, typeFilter, statusFilter, sort])

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const currentPage = Math.min(page, pageCount - 1)
  const pageItems = filtered.slice(currentPage * PAGE_SIZE, currentPage * PAGE_SIZE + PAGE_SIZE)

  const summaries = useExperimentSummaries(pageItems)

  const typeOptions = useMemo(
    () => [...new Set(experiments.map((experiment) => experiment.experiment_type))].sort(),
    [experiments],
  )
  const statusOptions = useMemo(
    () => [...new Set(experiments.map((experiment) => experiment.status))].sort(),
    [experiments],
  )

  function resetFilters() {
    setSearch('')
    setTypeFilter('')
    setStatusFilter('')
    setSort('created_desc')
    setPage(0)
  }

  return (
    <Card data-testid="experiment-history">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <CardTitle>Experiment History</CardTitle>
          <p className="text-xs text-muted mt-1">
            Every experiment stored by the Phase 11 research API. Energy totals are summed from the
            API's per-trial measurements — never fabricated.
          </p>
        </div>
        <Badge variant="muted" size="md">
          {filtered.length} of {experiments.length} experiments
        </Badge>
      </div>

      <CardContent className="mt-4 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="flex flex-col gap-1">
            <label htmlFor="history-search" className="text-[10px] uppercase tracking-wider text-muted">
              Search
            </label>
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted" />
              <input
                id="history-search"
                type="search"
                className={`${controlClass} w-full pl-8`}
                placeholder="Name, attack, UUID…"
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value)
                  setPage(0)
                }}
              />
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor="history-type" className="text-[10px] uppercase tracking-wider text-muted">
              Experiment type
            </label>
            <select
              id="history-type"
              className={`${controlClass} w-full`}
              value={typeFilter}
              onChange={(event) => {
                setTypeFilter(event.target.value)
                setPage(0)
              }}
            >
              <option value="">All types</option>
              {typeOptions.map((type) => (
                <option key={type} value={type}>
                  {typeLabel(type)}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor="history-status" className="text-[10px] uppercase tracking-wider text-muted">
              Status
            </label>
            <select
              id="history-status"
              className={`${controlClass} w-full`}
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value)
                setPage(0)
              }}
            >
              <option value="">All statuses</option>
              {statusOptions.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor="history-sort" className="text-[10px] uppercase tracking-wider text-muted">
              Sort
            </label>
            <select
              id="history-sort"
              className={`${controlClass} w-full`}
              value={sort}
              onChange={(event) => setSort(event.target.value)}
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={resetFilters}
              className="mt-1 text-[11px] text-accent hover:text-accent-light text-left"
            >
              Reset filters
            </button>
          </div>
        </div>

        {loading && <SectionLoading label="Loading experiments…" />}

        {!loading && error && <SectionError title="Unable to load experiments" message={error} />}

        {!loading && !error && filtered.length === 0 && (
          <SectionEmpty
            title={experiments.length === 0 ? 'No experiments yet' : 'No experiments match these filters'}
            message={
              experiments.length === 0
                ? 'Run an experiment in the runner above and it will appear here.'
                : 'Adjust the search term or filters to see other experiments.'
            }
          />
        )}

        {!loading && !error && filtered.length > 0 && (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border text-muted uppercase tracking-wider">
                    <th className="text-left px-2 py-1.5">ID</th>
                    <th className="text-left px-2 py-1.5">Name</th>
                    <th className="text-left px-2 py-1.5">Type</th>
                    <th className="text-left px-2 py-1.5">Attack</th>
                    <th className="text-right px-2 py-1.5">Trials</th>
                    <th className="text-right px-2 py-1.5">Energy</th>
                    <th className="text-left px-2 py-1.5">Mode</th>
                    <th className="text-left px-2 py-1.5">Status</th>
                    <th className="text-left px-2 py-1.5">Created</th>
                    <th className="text-left px-2 py-1.5"> </th>
                  </tr>
                </thead>
                <tbody>
                  {pageItems.map((experiment) => {
                    const summary = summaries.byUuid.get(experiment.experiment_uuid)
                    const energy = sumEnergyJoules(summary)
                    return (
                      <tr
                        key={experiment.experiment_uuid}
                        className="border-b border-border/50 hover:bg-card-hover"
                      >
                        <td className="px-2 py-1.5 text-muted">#{experiment.id}</td>
                        <td className="px-2 py-1.5 text-text-primary max-w-[16rem] truncate">
                          {experiment.name}
                        </td>
                        <td className="px-2 py-1.5 text-muted">{typeLabel(experiment.experiment_type)}</td>
                        <td className="px-2 py-1.5 text-muted">
                          {experiment.attack_type} / {experiment.attack_intensity}
                        </td>
                        <td className="px-2 py-1.5 text-right text-text-primary">{experiment.num_trials}</td>
                        <td className="px-2 py-1.5 text-right text-text-primary">
                          {energy !== null ? (
                            formatJoules(energy)
                          ) : summaries.loading ? (
                        <span className="text-muted">…</span>
                          ) : (
                            <span className="text-muted">—</span>
                          )}
                        </td>
                        <td className="px-2 py-1.5">
                          <Badge variant={experiment.measurement_mode === 'MEASURED' ? 'success' : 'warning'} size="sm">
                            {experiment.measurement_mode}
                          </Badge>
                        </td>
                        <td className="px-2 py-1.5">
                          <Badge variant={statusVariant(experiment.status)} size="sm">
                            {experiment.status}
                          </Badge>
                        </td>
                        <td className="px-2 py-1.5 text-muted">{formatDateTime(experiment.created_at)}</td>
                        <td className="px-2 py-1.5">
                          <Link
                            to={`/research-lab/experiments/${experiment.experiment_uuid}`}
                            className="inline-flex items-center gap-1.5 text-accent hover:text-accent-light"
                          >
                            <FlaskConical className="w-3.5 h-3.5" />
                            Open
                          </Link>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            {summaries.error && (
              <p className="text-[11px] text-warning">{summaries.error}</p>
            )}

            <div className="flex items-center justify-between">
              <span className="text-[11px] text-muted">
                Page {currentPage + 1} of {pageCount}
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  className={`${controlClass} disabled:opacity-50`}
                  disabled={currentPage === 0}
                  onClick={() => setPage(currentPage - 1)}
                >
                  Previous
                </button>
                <button
                  type="button"
                  className={`${controlClass} disabled:opacity-50`}
                  disabled={currentPage >= pageCount - 1}
                  onClick={() => setPage(currentPage + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
