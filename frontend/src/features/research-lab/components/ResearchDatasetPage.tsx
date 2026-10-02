import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Download, FileJson, FileSpreadsheet } from 'lucide-react'
import PageHeader from '@/shared/ui/PageHeader'
import Badge from '@/shared/ui/Badge'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import { downloadFile } from '@/shared/utils/exportData'
import { formatDateTime, formatNumber } from '@/shared/utils/formatters'
import { researchApi } from '../api/researchApi'
import { SectionEmpty, SectionError, SectionLoading, controlClass } from './ResearchBits'
import {
  controlsLabel,
  formatJoules,
  formatKilograms,
  modeVariant,
} from '../utils/format'
import { useResearchLabData } from '../hooks/useResearchLabData'
import type { ExportDataset } from '../types/research'

type TabId = 'experiments' | 'marginal_energy' | 'interaction_effects' | 'defense_amplification'

const TABS: Array<{ id: TabId; label: string }> = [
  { id: 'experiments', label: 'Experiments' },
  { id: 'marginal_energy', label: 'Marginal energy' },
  { id: 'interaction_effects', label: 'Interaction effects' },
  { id: 'defense_amplification', label: 'Defense amplification' },
]

const CSV_DATASETS: Array<{ id: ExportDataset; label: string }> = [
  { id: 'experiments', label: 'Experiments' },
  { id: 'marginal_energy', label: 'Marginal energy' },
  { id: 'interaction_effects', label: 'Interaction effects' },
  { id: 'defense_amplification', label: 'Defense amplification' },
]

interface DatasetRow {
  key: string
  experiment: string
  attack: string
  intensity: string
  workload: string
  controls: string
  mode: string
  energy: string
  carbon: string
  result: string
  formula: string
  created: string
  searchable: string
}

const COLUMNS: Array<{ id: keyof Omit<DatasetRow, 'key' | 'searchable'>; label: string; align?: string }> = [
  { id: 'experiment', label: 'Experiment' },
  { id: 'attack', label: 'Attack' },
  { id: 'intensity', label: 'Intensity' },
  { id: 'workload', label: 'Workload' },
  { id: 'controls', label: 'Controls' },
  { id: 'mode', label: 'Mode' },
  { id: 'energy', label: 'Energy', align: 'text-right' },
  { id: 'carbon', label: 'Carbon', align: 'text-right' },
  { id: 'result', label: 'Result' },
  { id: 'formula', label: 'Formula version' },
  { id: 'created', label: 'Created' },
]

function buildRows(
  tab: TabId,
  data: ReturnType<typeof useResearchLabData>,
): DatasetRow[] {
  const experimentName = (id: number) => {
    const experiment = data.experiments.find((item) => item.id === id)
    return experiment ? `#${id} ${experiment.name}` : `#${id}`
  }

  if (tab === 'experiments') {
    return data.experiments.map((experiment) => ({
      key: `exp-${experiment.id}`,
      experiment: experiment.name,
      attack: experiment.attack_type,
      intensity: experiment.attack_intensity,
      workload: experiment.workload_profile ?? '—',
      controls: controlsLabel(experiment.security_controls),
      mode: experiment.measurement_mode,
      energy: '—',
      carbon: '—',
      result: experiment.status,
      formula: experiment.configuration_version ?? '—',
      created: formatDateTime(experiment.created_at),
      searchable: [
        experiment.name,
        experiment.attack_type,
        experiment.attack_intensity,
        experiment.experiment_uuid,
        experiment.status,
        experiment.measurement_mode,
      ].join(' ').toLowerCase(),
    }))
  }

  if (tab === 'marginal_energy') {
    return data.marginal.map((row) => ({
      key: `marg-${row.id}`,
      experiment: experimentName(row.experiment_id),
      attack: row.attack_type,
      intensity: row.attack_intensity,
      workload:
        row.workload_value !== null
          ? `${formatNumber(row.workload_value, 2)}${row.workload_unit ? ` ${row.workload_unit}` : ''}`
          : '—',
      controls: '—',
      mode: row.measurement_mode,
      energy: formatJoules(row.marginal_energy_joules),
      carbon: row.marginal_carbon_kg !== null ? formatKilograms(row.marginal_carbon_kg) : '—',
      result: `baseline ${formatJoules(row.baseline_energy_joules)} → security ${formatJoules(row.security_energy_joules)}`,
      formula: row.formula_version,
      created: formatDateTime(row.created_at),
      searchable: [row.attack_type, row.attack_intensity, row.measurement_mode, row.formula_version]
        .join(' ')
        .toLowerCase(),
    }))
  }

  if (tab === 'interaction_effects') {
    return data.interaction.map((row) => ({
      key: `int-${row.id}`,
      experiment: experimentName(row.experiment_id),
      attack: row.attack_type ?? '—',
      intensity: row.attack_intensity ?? '—',
      workload:
        row.workload_value !== null
          ? `${formatNumber(row.workload_value, 2)}${row.workload_unit ? ` ${row.workload_unit}` : ''}`
          : '—',
      controls: `${row.control_a} + ${row.control_b}`,
      mode: row.measurement_mode ?? '—',
      energy: formatJoules(row.interaction_effect),
      carbon: row.interaction_carbon_kg !== null ? formatKilograms(row.interaction_carbon_kg) : '—',
      result: row.interpretation ?? 'Not classified',
      formula: row.formula_version,
      created: formatDateTime(row.created_at),
      searchable: [row.control_a, row.control_b, row.attack_type ?? '', row.interpretation ?? '']
        .join(' ')
        .toLowerCase(),
    }))
  }

  return data.amplification.map((row) => ({
    key: `amp-${row.id}`,
    experiment: experimentName(row.experiment_id),
    attack: row.attack_type,
    intensity: row.attack_intensity,
    workload: `${formatNumber(row.attack_workload, 2)} ${row.workload_unit}`.trim(),
    controls: row.control_name,
    mode: row.measurement_mode ?? '—',
    energy: formatJoules(row.additional_defense_energy),
    carbon: row.amplification_carbon_kg !== null ? formatKilograms(row.amplification_carbon_kg) : '—',
    result: `DEA ${formatNumber(row.defense_energy_amplification, 3)}`,
    formula: row.formula_version,
    created: formatDateTime(row.created_at),
    searchable: [row.control_name, row.attack_type, row.attack_intensity, row.measurement_mode ?? '']
      .join(' ')
      .toLowerCase(),
  }))
}

export default function ResearchDatasetPage() {
  const data = useResearchLabData()
  const [tab, setTab] = useState<TabId>('experiments')
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<'created_desc' | 'created_asc' | 'attack'>('created_desc')
  const [pending, setPending] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [exportError, setExportError] = useState<string | null>(null)

  const rows = useMemo(() => {
    const needle = search.trim().toLowerCase()
    const filtered = needle
      ? buildRows(tab, data).filter((row) => row.searchable.includes(needle))
      : buildRows(tab, data)
    const sorted = [...filtered]
    sorted.sort((a, b) => {
      if (sort === 'attack') return a.attack.localeCompare(b.attack)
      const delta = new Date(a.created).getTime() - new Date(b.created).getTime()
      return sort === 'created_asc' ? delta : -delta
    })
    return sorted
  }, [tab, data, search, sort])

  async function handleCsv(dataset: ExportDataset) {
    setPending(`csv:${dataset}`)
    setNotice(null)
    setExportError(null)
    try {
      const csv = await researchApi.exportCsv(dataset)
      if (!csv.trim()) {
        setExportError(`The ${dataset} dataset is empty, so no CSV file was produced.`)
        return
      }
      downloadFile(csv, `carbonguard-research-${dataset}-${new Date().toISOString().slice(0, 10)}.csv`)
      setNotice(`${dataset} CSV exported.`)
    } catch (error) {
      setExportError(error instanceof Error ? error.message : 'The export request failed.')
    } finally {
      setPending(null)
    }
  }

  async function handleJson() {
    setPending('json')
    setNotice(null)
    setExportError(null)
    try {
      const payload = await researchApi.exportJson()
      const total = Object.values(payload.record_counts ?? {}).reduce(
        (sum, value) => sum + (value ?? 0),
        0,
      )
      if (total === 0) {
        setExportError('There are no research records to export yet.')
        return
      }
      downloadFile(
        JSON.stringify(payload, null, 2),
        `carbonguard-research-${new Date().toISOString().slice(0, 10)}.json`,
        'application/json',
      )
      setNotice(`JSON export completed — ${total} records.`)
    } catch (error) {
      setExportError(error instanceof Error ? error.message : 'The export request failed.')
    } finally {
      setPending(null)
    }
  }

  return (
    <div className="space-y-6" data-testid="research-dataset-page">
      <PageHeader
        title="Research Dataset"
        subtitle="Joined Phase 5–7 result tables with search, plus CSV and JSON export through the Phase 11 research API."
        badge={
          <Badge variant="warning" size="sm">
            ESTIMATED / MEASURED AS RECORDED
          </Badge>
        }
        actions={
          <Link
            to="/research-lab"
            className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-muted border border-border rounded-md hover:text-text-primary hover:border-accent/40 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Research overview
          </Link>
        }
      />

      <Card data-testid="research-export">
        <CardTitle>Export</CardTitle>
        <CardContent className="mt-4 space-y-3">
          <div className="flex flex-wrap gap-2">
            {CSV_DATASETS.map((dataset) => (
              <button
                key={dataset.id}
                type="button"
                onClick={() => handleCsv(dataset.id)}
                disabled={pending !== null}
                className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-text-primary bg-card border border-border rounded-md hover:border-accent/40 disabled:opacity-50 transition-colors"
              >
                <FileSpreadsheet className="w-3.5 h-3.5 text-accent" />
                {pending === `csv:${dataset.id}` ? 'Exporting…' : `CSV · ${dataset.label}`}
              </button>
            ))}
            <button
              type="button"
              onClick={handleJson}
              disabled={pending !== null}
              className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-text-primary bg-card border border-border rounded-md hover:border-accent/40 disabled:opacity-50 transition-colors"
            >
              <FileJson className="w-3.5 h-3.5 text-success" />
              {pending === 'json' ? 'Exporting…' : 'JSON · all datasets'}
            </button>
            <button
              type="button"
              onClick={() => window.print()}
              className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-muted border border-border rounded-md hover:text-text-primary hover:border-accent/40 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              Print view
            </button>
          </div>

          {notice && <p className="text-[11px] text-success">{notice}</p>}
          {exportError && (
            <p className="text-[11px] text-danger" data-testid="export-error">
              Export failed: {exportError}
            </p>
          )}
          <p className="text-[11px] text-muted leading-relaxed">
            Files contain only records stored by the backend. Empty datasets and API errors are
            reported instead of producing empty or fabricated files.
          </p>
        </CardContent>
      </Card>

      <Card data-testid="research-dataset-table">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle>Dataset</CardTitle>
          <Badge variant="muted" size="md">
            {rows.length} rows
          </Badge>
        </div>

        <CardContent className="mt-4 space-y-4">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div className="flex flex-wrap gap-1" role="tablist" aria-label="Research datasets">
              {TABS.map((item) => {
                const active = tab === item.id
                return (
                  <button
                    key={item.id}
                    type="button"
                    role="tab"
                    aria-selected={active}
                    onClick={() => setTab(item.id)}
                    className={`px-3 py-1.5 text-xs rounded-md border transition-colors ${
                      active
                        ? 'border-accent/50 bg-accent/10 text-accent'
                        : 'border-border bg-card text-muted hover:text-text-primary'
                    }`}
                  >
                    {item.label}
                  </button>
                )
              })}
            </div>

            <div className="flex gap-2">
              <input
                type="search"
                aria-label="Search dataset"
                className={controlClass}
                placeholder="Search rows…"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
              <select
                aria-label="Sort dataset"
                className={controlClass}
                value={sort}
                onChange={(event) => setSort(event.target.value as typeof sort)}
              >
                <option value="created_desc">Newest first</option>
                <option value="created_asc">Oldest first</option>
                <option value="attack">Attack type</option>
              </select>
            </div>
          </div>

          {data.loading && <SectionLoading label="Loading research dataset…" />}

          {!data.loading && data.errors.experiments && (
            <SectionError
              title="Unable to load the dataset"
              message={data.errors.experiments}
            />
          )}

          {!data.loading && !data.errors.experiments && rows.length === 0 && (
            <SectionEmpty
              title={search ? 'No rows match this search' : 'No records yet'}
              message={
                search
                  ? 'Clear the search box to see every stored row.'
                  : 'Run experiments and compute Phase 5–7 results to populate this dataset.'
              }
            />
          )}

          {!data.loading && rows.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border text-muted uppercase tracking-wider">
                    {COLUMNS.map((column) => (
                      <th key={column.id} className={`px-2 py-1.5 ${column.align ?? 'text-left'}`}>
                        {column.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.slice(0, 100).map((row) => (
                    <tr key={row.key} className="border-b border-border/50 hover:bg-card-hover">
                      {COLUMNS.map((column) => (
                        <td
                          key={column.id}
                          className={`px-2 py-1.5 ${
                            column.align ?? 'text-left'
                          } ${column.id === 'experiment' ? 'text-text-primary' : 'text-muted'}`}
                        >
                          {column.id === 'mode' ? (
                            <Badge variant={modeVariant(row.mode)} size="sm">
                              {row.mode}
                            </Badge>
                          ) : (
                            row[column.id]
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {rows.length > 100 && (
            <p className="text-[11px] text-muted">
              Showing the first 100 of {rows.length} rows — narrow with the search box or use the
              CSV export for the full dataset.
            </p>
          )}

          <p className="text-[11px] text-muted leading-relaxed">
            Energy is measured or estimated according to each row&apos;s mode badge; carbon is
            calculated as energy (kWh) × carbon intensity (gCO₂/kWh) ÷ 1000 and is never a
            measurement.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
