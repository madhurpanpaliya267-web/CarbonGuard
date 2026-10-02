import { useEffect, useMemo, useState } from 'react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import Badge from '@/shared/ui/Badge'
import { chartConfig } from '@/shared/utils/chartConfig'
import { formatDateTime, formatNumber } from '@/shared/utils/formatters'
import { researchApi } from '../api/researchApi'
import {
  Field,
  FieldGrid,
  FilterBar,
  FilterSelect,
  FormulaNote,
  SectionEmpty,
  SectionError,
  SectionLoading,
  StatTile,
} from './ResearchBits'
import {
  CARBON_INTENSITY_NOTE,
  carbonBasisLabel,
  carbonPerWorkloadReason,
  distinctOptions,
  formatCarbonPerWorkload,
  formatInteger,
  formatJoules,
  formatKilograms,
  formatScalar,
  formatWatts,
  modeVariant,
  workloadLabel,
} from '../utils/format'
import { meanBy } from '../utils/researchMetrics'
import type { Experiment, InteractionResult, ResearchAnalyticsResult } from '../types/research'

const tooltipStyle = {
  backgroundColor: chartConfig.tooltipBg,
  border: `1px solid ${chartConfig.tooltipBorder}`,
  borderRadius: '8px',
  fontSize: '12px',
}

const interpretationVariant: Record<string, 'primary' | 'muted' | 'purple'> = {
  'super-additive': 'primary',
  'approximately additive': 'muted',
  'sub-additive': 'purple',
}

function pairKey(item: InteractionResult): string {
  return `${item.control_a} + ${item.control_b}`
}

interface Props {
  items: InteractionResult[]
  error: string | null
  experiments?: Experiment[]
}

interface Filters {
  control_a: string
  control_b: string
  attack_type: string
  attack_intensity: string
  workload: string
  duration: string
  trials: string
}

const emptyFilters: Filters = {
  control_a: '',
  control_b: '',
  attack_type: '',
  attack_intensity: '',
  workload: '',
  duration: '',
  trials: '',
}

export default function InteractionSection({ items, error, experiments = [] }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [filters, setFilters] = useState<Filters>(emptyFilters)
  const [stats, setStats] = useState<ResearchAnalyticsResult | null>(null)
  const [statsError, setStatsError] = useState<string | null>(null)
  const [statsLoading, setStatsLoading] = useState(false)

  const experimentById = useMemo(
    () => new Map(experiments.map((experiment) => [experiment.id, experiment])),
    [experiments],
  )

  const filtered = useMemo(() => {
    return items.filter((item) => {
      const experiment = experimentById.get(item.experiment_id)
      if (filters.control_a && item.control_a !== filters.control_a) return false
      if (filters.control_b && item.control_b !== filters.control_b) return false
      if (filters.attack_type && item.attack_type !== filters.attack_type) return false
      if (filters.attack_intensity && item.attack_intensity !== filters.attack_intensity)
        return false
      if (filters.workload && String(item.workload_value ?? '') !== filters.workload) return false
      if (filters.duration && String(item.duration_seconds ?? '') !== filters.duration)
        return false
      if (filters.trials && String(experiment?.num_trials ?? '') !== filters.trials) return false
      return true
    })
  }, [items, experimentById, filters])

  const options = useMemo(
    () => ({
      control_a: distinctOptions(items.map((item) => item.control_a)),
      control_b: distinctOptions(items.map((item) => item.control_b)),
      attack_type: distinctOptions(items.map((item) => item.attack_type)),
      attack_intensity: distinctOptions(items.map((item) => item.attack_intensity)),
      workload: distinctOptions(items.map((item) => item.workload_value)),
      duration: distinctOptions(items.map((item) => item.duration_seconds)),
      trials: distinctOptions(
        items.map((item) => experimentById.get(item.experiment_id)?.num_trials),
      ),
    }),
    [items, experimentById],
  )

  const selected = useMemo(() => {
    if (filtered.length === 0) return null
    return filtered.find((item) => item.id === selectedId) ?? filtered[filtered.length - 1]
  }, [filtered, selectedId])

  const combinationData = useMemo(() => {
    if (!selected) return []
    return [
      { name: 'E₀ baseline', energy: selected.energy_baseline },
      { name: 'E_A control A', energy: selected.energy_a },
      { name: 'E_B control B', energy: selected.energy_b },
      { name: 'E_AB combined', energy: selected.energy_ab },
    ]
  }, [selected])

  const pairData = useMemo(() => {
    const buckets = new Map<string, number[]>()
    filtered.forEach((item) => {
      const key = pairKey(item)
      const values = buckets.get(key) ?? []
      values.push(item.interaction_effect)
      buckets.set(key, values)
    })
    return [...buckets.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([pair, values]) => ({
        pair,
        meanInteraction: values.reduce((a, b) => a + b, 0) / values.length,
      }))
  }, [filtered])

  const intensityData = useMemo(
    () =>
      meanBy(
        filtered,
        (item) => item.attack_intensity || 'unknown',
        (item) => item.interaction_effect,
      ).map((row) => ({ intensity: row.bucket, meanInteraction: row.mean })),
    [filtered],
  )

  useEffect(() => {
    if (items.length === 0) {
      setStats(null)
      setStatsError(null)
      return
    }

    let cancelled = false
    setStatsLoading(true)
    researchApi
      .computeAnalytics({ source: 'interaction', metric: 'interaction_effect' })
      .then((result) => {
        if (!cancelled) {
          setStats(result)
          setStatsError(null)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setStats(null)
          setStatsError(err instanceof Error ? err.message : 'Statistics unavailable')
        }
      })
      .finally(() => {
        if (!cancelled) setStatsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [items.length])

  if (error) {
    return (
      <Card>
        <SectionError message={error} />
      </Card>
    )
  }

  if (items.length === 0) {
    return (
      <Card>
        <SectionEmpty
          title="No interaction effects recorded"
          message="Run an INTERACTION experiment and compute interaction effects to populate Phase 6 results."
        />
      </Card>
    )
  }

  const interpretation = selected?.interpretation ?? 'not classified'

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle>Security-Control Interaction (Phase 6)</CardTitle>
            <p className="text-xs text-muted mt-1">
              I(A,B) = E_AB − E_A − E_B + E_0, as persisted by the backend. Classification is the
              backend-recorded interpretation — thresholds are never invented here.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted" htmlFor="interaction-select">
              Result
            </label>
            <select
              id="interaction-select"
              value={selected?.id ?? ''}
              onChange={(event) => setSelectedId(Number(event.target.value))}
              className="bg-card border border-border rounded-md px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:border-accent/50"
            >
              {filtered.map((item) => (
                <option key={item.id} value={item.id}>
                  #{item.id} · {pairKey(item)} · I {formatNumber(item.interaction_effect, 2)} J
                </option>
              ))}
            </select>
          </div>
        </div>

        <CardContent className="mt-4 space-y-5">
          <FilterBar
            title="Inputs"
            onReset={() => setFilters(emptyFilters)}
            summary={`${formatInteger(filtered.length)} of ${formatInteger(items.length)} results`}
          >
            <FilterSelect
              id="interaction-filter-control-a"
              label="Control A"
              value={filters.control_a}
              onChange={(value) => setFilters((f) => ({ ...f, control_a: value }))}
              options={options.control_a}
              allLabel="Any control A"
            />
            <FilterSelect
              id="interaction-filter-control-b"
              label="Control B"
              value={filters.control_b}
              onChange={(value) => setFilters((f) => ({ ...f, control_b: value }))}
              options={options.control_b}
              allLabel="Any control B"
            />
            <FilterSelect
              id="interaction-filter-attack"
              label="Attack Type"
              value={filters.attack_type}
              onChange={(value) => setFilters((f) => ({ ...f, attack_type: value }))}
              options={options.attack_type}
            />
            <FilterSelect
              id="interaction-filter-intensity"
              label="Attack Intensity"
              value={filters.attack_intensity}
              onChange={(value) => setFilters((f) => ({ ...f, attack_intensity: value }))}
              options={options.attack_intensity}
            />
            <FilterSelect
              id="interaction-filter-workload"
              label="Workload"
              value={filters.workload}
              onChange={(value) => setFilters((f) => ({ ...f, workload: value }))}
              options={options.workload}
              allLabel="Any workload"
            />
            <FilterSelect
              id="interaction-filter-duration"
              label="Duration (s)"
              value={filters.duration}
              onChange={(value) => setFilters((f) => ({ ...f, duration: value }))}
              options={options.duration}
              allLabel="Any duration"
            />
            <FilterSelect
              id="interaction-filter-trials"
              label="Number of Trials"
              value={filters.trials}
              onChange={(value) => setFilters((f) => ({ ...f, trials: value }))}
              options={options.trials}
              allLabel="Any trial count"
            />
          </FilterBar>

          {!selected ? (
            <SectionEmpty
              title="No interaction results match the current inputs"
              message="Adjust or reset the inputs above to inspect persisted Phase 6 results."
            />
          ) : (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-background/60 border border-border rounded-md p-4">
                  <p className="text-xs font-semibold text-text-primary mb-3">Configuration</p>
                  <FieldGrid>
                    <Field label="Control A" value={selected.control_a} />
                    <Field label="Control B" value={selected.control_b} />
                    <Field label="Attack Type" value={selected.attack_type ?? '—'} />
                    <Field label="Attack Intensity" value={selected.attack_intensity ?? '—'} />
                    <Field
                      label="Workload"
                      value={workloadLabel(selected.workload_value, selected.workload_unit)}
                    />
                    <Field
                      label="Duration"
                      value={formatScalar(selected.duration_seconds, 1, ' s')}
                    />
                    <Field
                      label="Trials"
                      value={formatInteger(experimentById.get(selected.experiment_id)?.num_trials)}
                    />
                  </FieldGrid>
                </div>

                <div className="bg-background/60 border border-border rounded-md p-4">
                  <p className="text-xs font-semibold text-text-primary mb-3">Interaction</p>
                  <FieldGrid>
                    <Field label="Baseline Energy E₀" value={formatJoules(selected.energy_baseline)} />
                    <Field label="Energy A" value={formatJoules(selected.energy_a)} />
                    <Field label="Energy B" value={formatJoules(selected.energy_b)} />
                    <Field label="Combined Energy E_AB" value={formatJoules(selected.energy_ab)} />
                    <Field
                      label="Interaction Effect I(A,B)"
                      value={formatJoules(selected.interaction_effect)}
                    />
                    <Field
                      label="Interaction Index"
                      value={formatScalar(selected.interaction_index, 4)}
                    />
                  </FieldGrid>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-background/60 border border-border rounded-md p-4">
                  <p className="text-xs font-semibold text-text-primary mb-3">Interpretation</p>
                  <div className="flex flex-wrap items-center gap-2 mb-3">
                    <Badge variant={interpretationVariant[interpretation] ?? 'muted'} size="md">
                      {interpretation}
                    </Badge>
                    <Badge variant={modeVariant(selected.measurement_mode)} size="md">
                      {selected.measurement_mode ?? 'UNKNOWN MODE'}
                    </Badge>
                  </div>
                  <p className="text-[11px] text-muted leading-relaxed">
                    Approximately additive: combined cost matches the sum within the backend
                    tolerance. Sub-additive: below the sum. Super-additive: above the sum. These are
                    neutral descriptive labels produced by the research engine, not rankings.
                  </p>
                  <FormulaNote>
                    {selected.formula_version}: I(A,B) = {formatNumber(selected.energy_ab, 2)} −{' '}
                    {formatNumber(selected.energy_a, 2)} − {formatNumber(selected.energy_b, 2)} +{' '}
                    {formatNumber(selected.energy_baseline, 2)} ={' '}
                    {formatNumber(selected.interaction_effect, 2)} J
                  </FormulaNote>
                </div>

                <div className="bg-background/60 border border-border rounded-md p-4">
                  <p className="text-xs font-semibold text-text-primary mb-3">
                    Descriptive Statistics (Phase 8)
                  </p>
                  {statsLoading ? (
                    <SectionLoading label="Computing descriptive statistics…" />
                  ) : stats ? (
                    <>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                        <StatTile label="Observations (n)" value={formatInteger(stats.n)} />
                        <StatTile label="Mean" value={formatNumber(stats.statistics.mean, 3)} />
                        <StatTile label="Median" value={formatNumber(stats.statistics.median, 3)} />
                        <StatTile
                          label="Std Dev (pop.)"
                          value={formatNumber(stats.statistics.std_dev, 3)}
                        />
                        <StatTile label="Min" value={formatNumber(stats.statistics.min, 3)} />
                        <StatTile label="Max" value={formatNumber(stats.statistics.max, 3)} />
                      </div>
                      <p className="text-[11px] text-muted mt-3">
                        Over {formatInteger(stats.n)} persisted interaction result
                        {stats.n === 1 ? '' : 's'} (metric <code>{stats.metric}</code>). Population
                        standard deviation, convention <code>{stats.std_dev_convention}</code>.
                      </p>
                    </>
                  ) : (
                    <p className="text-xs text-warning leading-relaxed">
                      {statsError ?? 'Descriptive statistics are unavailable for this selection.'}
                    </p>
                  )}
                  <div className="grid grid-cols-2 gap-2 mt-3">
                    <StatTile label="Result Trial #" value={formatInteger(selected.trial_number)} />
                    <StatTile label="Energy Provider" value={selected.energy_provider ?? '—'} />
                  </div>
                </div>
              </div>

              <div className="bg-background/60 border border-border rounded-md p-4">
                <p className="text-xs font-semibold text-text-primary mb-3">Power &amp; Carbon</p>
                <FieldGrid>
                  <Field label="Baseline Power" value={formatWatts(selected.power_baseline)} />
                  <Field label="Power A" value={formatWatts(selected.power_a)} />
                  <Field label="Power B" value={formatWatts(selected.power_b)} />
                  <Field label="Power AB" value={formatWatts(selected.power_ab)} />
                  <Field label="Interaction Power" value={formatWatts(selected.interaction_power)} />
                  <Field
                    label="Interaction Carbon ΔC"
                    value={formatKilograms(selected.interaction_carbon_kg)}
                  />
                  <Field
                    label="Interaction Carbon per Workload"
                    value={formatCarbonPerWorkload(selected.interaction_carbon_per_workload)}
                  />
                  <Field
                    label="Carbon Basis"
                    value={<span className="text-xs">{carbonBasisLabel(selected.carbon_basis)}</span>}
                  />
                  <Field label="Recorded" value={formatDateTime(selected.created_at)} />
                  <Field
                    label="Result ID"
                    value={`#${selected.id} (experiment #${selected.experiment_id})`}
                  />
                  <Field
                    label="Carbon Intensity"
                    value={formatScalar(selected.carbon_intensity, 1, ' gCO₂/kWh')}
                  />
                </FieldGrid>
                {carbonPerWorkloadReason(selected.interaction_carbon_per_workload) && (
                  <p className="text-[11px] text-warning mt-2">
                    Carbon per workload unavailable:{' '}
                    {carbonPerWorkloadReason(selected.interaction_carbon_per_workload)}
                  </p>
                )}
                <p className="text-[11px] text-muted mt-2">{CARBON_INTENSITY_NOTE}</p>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardTitle>Control Combination Energy</CardTitle>
          <CardContent className="mt-3">
            {selected ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={combinationData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 10, fill: chartConfig.tickFill }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(value: number) => [`${formatNumber(value, 2)} J`, 'Energy']}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                  <Bar dataKey="energy" fill={chartConfig.colors.primary} radius={[4, 4, 0, 0]} name="Energy (J)" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-56 text-sm text-muted">No data</div>
            )}
            <p className="text-[11px] text-muted mt-2">
              E₀, E_A, E_B and E_AB for the selected result — the four terms of the Phase 6 formula.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardTitle>Interaction Effect by Control Pair</CardTitle>
          <CardContent className="mt-3">
            {pairData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={pairData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                  <XAxis dataKey="pair" tick={{ fontSize: 10, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(value: number) => [`${formatNumber(value, 3)} J`, 'Mean I(A,B)']}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                  <Bar
                    dataKey="meanInteraction"
                    fill={chartConfig.colors.purple}
                    radius={[4, 4, 0, 0]}
                    name="Mean interaction effect (J)"
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-56 text-sm text-muted">No data</div>
            )}
            <p className="text-[11px] text-muted mt-2">
              Positive values indicate super-additive cost, negative values sub-additive cost.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardTitle>Interaction Effect across Attack Intensity</CardTitle>
          <CardContent className="mt-3">
            {intensityData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={intensityData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                  <XAxis dataKey="intensity" tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(value: number) => [`${formatNumber(value, 3)} J`, 'Mean I(A,B)']}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                  <Bar
                    dataKey="meanInteraction"
                    fill={chartConfig.colors.accent}
                    radius={[4, 4, 0, 0]}
                    name="Mean interaction effect (J)"
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-56 text-sm text-muted">No data</div>
            )}
            <p className="text-[11px] text-muted mt-2">
              Mean interaction effect per attack intensity over the current input selection.
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardTitle>Interaction Results</CardTitle>
        <CardContent className="mt-3">
          {filtered.length === 0 ? (
            <SectionEmpty
              title="No rows match the current inputs"
              message="Adjust or reset the inputs to see persisted interaction results."
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border text-muted uppercase tracking-wider">
                    <th className="text-left px-2 py-1.5">ID</th>
                    <th className="text-left px-2 py-1.5">Controls</th>
                    <th className="text-left px-2 py-1.5">Attack</th>
                    <th className="text-right px-2 py-1.5">Workload</th>
                    <th className="text-right px-2 py-1.5">E₀</th>
                    <th className="text-right px-2 py-1.5">E_A</th>
                    <th className="text-right px-2 py-1.5">E_B</th>
                    <th className="text-right px-2 py-1.5">E_AB</th>
                    <th className="text-right px-2 py-1.5">I(A,B)</th>
                    <th className="text-right px-2 py-1.5">Index</th>
                    <th className="text-right px-2 py-1.5">Carbon ΔC</th>
                    <th className="text-left px-2 py-1.5">Class</th>
                    <th className="text-left px-2 py-1.5">Mode</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((item) => (
                    <tr
                      key={item.id}
                      className={`border-b border-border/50 cursor-pointer hover:bg-card ${
                        selected?.id === item.id ? 'bg-accent/5' : ''
                      }`}
                      onClick={() => setSelectedId(item.id)}
                    >
                      <td className="px-2 py-1.5 text-text-primary">#{item.id}</td>
                      <td className="px-2 py-1.5 text-muted">{pairKey(item)}</td>
                      <td className="px-2 py-1.5 text-muted">
                        {item.attack_type ?? '—'} / {item.attack_intensity ?? '—'}
                      </td>
                      <td className="px-2 py-1.5 text-right">
                        {workloadLabel(item.workload_value, item.workload_unit)}
                      </td>
                      <td className="px-2 py-1.5 text-right">{formatJoules(item.energy_baseline, 1)}</td>
                      <td className="px-2 py-1.5 text-right">{formatJoules(item.energy_a, 1)}</td>
                      <td className="px-2 py-1.5 text-right">{formatJoules(item.energy_b, 1)}</td>
                      <td className="px-2 py-1.5 text-right">{formatJoules(item.energy_ab, 1)}</td>
                      <td className="px-2 py-1.5 text-right text-text-primary">
                        {formatJoules(item.interaction_effect, 1)}
                      </td>
                      <td className="px-2 py-1.5 text-right">
                        {formatScalar(item.interaction_index, 4)}
                      </td>
                      <td className="px-2 py-1.5 text-right">
                        {formatKilograms(item.interaction_carbon_kg)}
                      </td>
                      <td className="px-2 py-1.5">
                        <Badge variant={interpretationVariant[item.interpretation ?? ''] ?? 'muted'} size="sm">
                          {item.interpretation ?? 'not classified'}
                        </Badge>
                      </td>
                      <td className="px-2 py-1.5">
                        <Badge variant={modeVariant(item.measurement_mode)} size="sm">
                          {item.measurement_mode ?? '—'}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p className="text-[11px] text-muted mt-3">
            Select a row to load it into the detail panels above. Classification comes from the
            persisted backend interpretation field.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
