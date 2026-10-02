import { useMemo, useState } from 'react'
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
import {
  Field,
  FieldGrid,
  FilterBar,
  FilterSelect,
  FormulaNote,
  SectionEmpty,
  SectionError,
} from './ResearchBits'
import {
  CARBON_INTENSITY_NOTE,
  carbonBasisLabel,
  carbonPerWorkloadReason,
  controlsLabel,
  distinctOptions,
  formatCarbonPerWorkload,
  formatInteger,
  formatJoules,
  formatKilograms,
  formatScalar,
  formatWatts,
  modeVariant,
  parseControls,
  workloadLabel,
} from '../utils/format'
import { meanBy } from '../utils/researchMetrics'
import type { Experiment, MarginalEnergyResult, SecurityControl } from '../types/research'

const tooltipStyle = {
  backgroundColor: chartConfig.tooltipBg,
  border: `1px solid ${chartConfig.tooltipBorder}`,
  borderRadius: '8px',
  fontSize: '12px',
}

interface Props {
  items: MarginalEnergyResult[]
  experiments: Experiment[]
  error: string | null
  controls?: SecurityControl[]
}

interface Filters {
  attack_type: string
  attack_intensity: string
  workload: string
  control: string
  duration: string
  trials: string
  measurement_mode: string
}

const emptyFilters: Filters = {
  attack_type: '',
  attack_intensity: '',
  workload: '',
  control: '',
  duration: '',
  trials: '',
  measurement_mode: '',
}

export default function MarginalEnergySection({ items, experiments, error, controls = [] }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [filters, setFilters] = useState<Filters>(emptyFilters)

  const experimentById = useMemo(
    () => new Map(experiments.map((experiment) => [experiment.id, experiment])),
    [experiments],
  )

  const filtered = useMemo(() => {
    return items.filter((item) => {
      const experiment = experimentById.get(item.experiment_id)
      if (filters.attack_type && item.attack_type !== filters.attack_type) return false
      if (filters.attack_intensity && item.attack_intensity !== filters.attack_intensity)
        return false
      if (filters.measurement_mode && item.measurement_mode !== filters.measurement_mode)
        return false
      if (filters.workload && String(item.workload_value ?? '') !== filters.workload) return false
      if (filters.duration && String(item.duration_seconds ?? '') !== filters.duration)
        return false
      if (filters.trials && String(experiment?.num_trials ?? '') !== filters.trials) return false
      if (filters.control) {
        const experimentControls = parseControls(experiment?.security_controls)
        if (!experimentControls.includes(filters.control)) return false
      }
      return true
    })
  }, [items, experimentById, filters])

  const options = useMemo(() => {
    const usedControls = new Set<string>()
    items.forEach((item) => {
      parseControls(experimentById.get(item.experiment_id)?.security_controls).forEach((control) =>
        usedControls.add(control),
      )
    })
    return {
      attack_type: distinctOptions(
        items.map((item) => item.attack_type),
        '',
      ),
      attack_intensity: distinctOptions(
        items.map((item) => item.attack_intensity),
        '',
      ),
      workload: distinctOptions(
        items.map((item) => item.workload_value),
        '',
      ),
      duration: distinctOptions(
        items.map((item) => item.duration_seconds),
        '',
      ),
      trials: distinctOptions(
        items.map((item) => experimentById.get(item.experiment_id)?.num_trials),
        '',
      ),
      measurement_mode: distinctOptions(
        items.map((item) => item.measurement_mode),
        '',
      ),
      control: controls
        .filter((control) => usedControls.has(control.control_id))
        .map((control) => ({ value: control.control_id, label: control.display_name })),
    }
  }, [items, experimentById, controls])

  const selected = useMemo(() => {
    if (filtered.length === 0) return null
    return filtered.find((item) => item.id === selectedId) ?? filtered[filtered.length - 1]
  }, [filtered, selectedId])

  const energyChartData = useMemo(() => {
    if (!selected) return []
    return [
      { name: 'Baseline', energyJoules: selected.baseline_energy_joules },
      { name: 'Security', energyJoules: selected.security_energy_joules },
      { name: 'Marginal ΔE', energyJoules: selected.marginal_energy_joules },
    ]
  }, [selected])

  const carbonChartData = useMemo(() => {
    if (!selected) return []
    return [
      { name: 'Baseline', carbonKg: selected.baseline_carbon_kg ?? 0 },
      { name: 'Security', carbonKg: selected.security_carbon_kg ?? 0 },
      { name: 'Marginal ΔC', carbonKg: selected.marginal_carbon_kg ?? 0 },
    ]
  }, [selected])

  const intensityData = useMemo(
    () =>
      meanBy(
        filtered,
        (item) => item.attack_intensity || 'unknown',
        (item) => item.marginal_energy_joules,
      ).map((row) => ({ intensity: row.bucket, meanMarginalJoules: row.mean })),
    [filtered],
  )

  const workloadData = useMemo(
    () =>
      meanBy(
        filtered,
        (item) => workloadLabel(item.workload_value, item.workload_unit),
        (item) => item.marginal_energy_joules,
      ).map((row) => ({ workload: row.bucket, meanMarginalJoules: row.mean })),
    [filtered],
  )

  const resetFilters = () => setFilters(emptyFilters)

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
          title="No marginal energy attributions yet"
          message="Run a MARGINAL_ENERGY experiment and compute attribution to populate Phase 5 results. Nothing is generated for display."
        />
      </Card>
    )
  }

  const experiment = selected ? experimentById.get(selected.experiment_id) : undefined

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle>Marginal Energy Attribution (Phase 5)</CardTitle>
            <p className="text-xs text-muted mt-1">
              ΔE = E_security − E_baseline, as persisted by the backend.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted" htmlFor="marginal-select">
              Attribution
            </label>
            <select
              id="marginal-select"
              value={selected?.id ?? ''}
              onChange={(event) => setSelectedId(Number(event.target.value))}
              className="bg-card border border-border rounded-md px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:border-accent/50"
            >
              {filtered.map((item) => (
                <option key={item.id} value={item.id}>
                  #{item.id} · {item.attack_type}/{item.attack_intensity} · ΔE{' '}
                  {formatNumber(item.marginal_energy_joules, 1)} J
                </option>
              ))}
            </select>
          </div>
        </div>

        <CardContent className="mt-4 space-y-5">
          <FilterBar
            title="Filters"
            onReset={resetFilters}
            summary={`${formatInteger(filtered.length)} of ${formatInteger(items.length)} attributions`}
          >
            <FilterSelect
              id="marginal-filter-attack"
              label="Attack Type"
              value={filters.attack_type}
              onChange={(value) => setFilters((f) => ({ ...f, attack_type: value }))}
              options={options.attack_type}
            />
            <FilterSelect
              id="marginal-filter-intensity"
              label="Attack Intensity"
              value={filters.attack_intensity}
              onChange={(value) => setFilters((f) => ({ ...f, attack_intensity: value }))}
              options={options.attack_intensity}
            />
            <FilterSelect
              id="marginal-filter-workload"
              label="Workload"
              value={filters.workload}
              onChange={(value) => setFilters((f) => ({ ...f, workload: value }))}
              options={options.workload}
              allLabel="Any workload"
            />
            <FilterSelect
              id="marginal-filter-control"
              label="Security Control"
              value={filters.control}
              onChange={(value) => setFilters((f) => ({ ...f, control: value }))}
              options={options.control}
              allLabel="Any control"
            />
            <FilterSelect
              id="marginal-filter-duration"
              label="Duration (s)"
              value={filters.duration}
              onChange={(value) => setFilters((f) => ({ ...f, duration: value }))}
              options={options.duration}
              allLabel="Any duration"
            />
            <FilterSelect
              id="marginal-filter-trials"
              label="Number of Trials"
              value={filters.trials}
              onChange={(value) => setFilters((f) => ({ ...f, trials: value }))}
              options={options.trials}
              allLabel="Any trial count"
            />
            <FilterSelect
              id="marginal-filter-mode"
              label="Measurement Mode"
              value={filters.measurement_mode}
              onChange={(value) => setFilters((f) => ({ ...f, measurement_mode: value }))}
              options={options.measurement_mode}
              allLabel="Any mode"
            />
          </FilterBar>

          {!selected ? (
            <SectionEmpty
              title="No attributions match the current filters"
              message="Adjust or reset the filters above to inspect persisted marginal energy results."
            />
          ) : (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-background/60 border border-border rounded-md p-4">
                  <p className="text-xs font-semibold text-text-primary mb-3">Energy</p>
                  <FieldGrid>
                    <Field
                      label="Baseline Energy"
                      value={formatJoules(selected.baseline_energy_joules)}
                    />
                    <Field
                      label="Security Energy"
                      value={formatJoules(selected.security_energy_joules)}
                    />
                    <Field
                      label="Marginal Energy ΔE"
                      value={formatJoules(selected.marginal_energy_joules)}
                    />
                    <Field
                      label="Baseline Energy (kWh)"
                      value={formatScalar(selected.baseline_energy_kwh, 6)}
                    />
                    <Field
                      label="Security Energy (kWh)"
                      value={formatScalar(selected.security_energy_kwh, 6)}
                    />
                    <Field
                      label="Marginal Energy (kWh)"
                      value={formatScalar(selected.marginal_energy_kwh, 6)}
                    />
                  </FieldGrid>
                </div>

                <div className="bg-background/60 border border-border rounded-md p-4">
                  <p className="text-xs font-semibold text-text-primary mb-3">
                    Power &amp; Carbon
                  </p>
                  <FieldGrid>
                    <Field label="Baseline Power" value={formatWatts(selected.baseline_power_watts)} />
                    <Field label="Security Power" value={formatWatts(selected.security_power_watts)} />
                    <Field label="Marginal Power ΔP" value={formatWatts(selected.marginal_power_watts)} />
                    <Field label="Baseline Carbon" value={formatKilograms(selected.baseline_carbon_kg)} />
                    <Field label="Security Carbon" value={formatKilograms(selected.security_carbon_kg)} />
                    <Field label="Carbon Difference ΔC" value={formatKilograms(selected.marginal_carbon_kg)} />
                    <Field
                      label="Marginal Carbon per Workload"
                      value={formatCarbonPerWorkload(selected.marginal_carbon_per_workload)}
                    />
                    <Field
                      label="Carbon Basis"
                      value={<span className="text-xs">{carbonBasisLabel(selected.carbon_basis)}</span>}
                    />
                  </FieldGrid>
                  {carbonPerWorkloadReason(selected.marginal_carbon_per_workload) && (
                    <p className="text-[11px] text-warning mt-2">
                      Carbon per workload unavailable:{' '}
                      {carbonPerWorkloadReason(selected.marginal_carbon_per_workload)}
                    </p>
                  )}
                  <p className="text-[11px] text-muted mt-2">{CARBON_INTENSITY_NOTE}</p>
                </div>
              </div>

              <div className="bg-background/60 border border-border rounded-md p-4">
                <p className="text-xs font-semibold text-text-primary mb-3">Context</p>
                <FieldGrid>
                  <Field label="Attack Type" value={selected.attack_type} />
                  <Field label="Attack Intensity" value={selected.attack_intensity} />
                  <Field
                    label="Workload"
                    value={workloadLabel(selected.workload_value, selected.workload_unit)}
                  />
                  <Field label="Duration" value={formatScalar(selected.duration_seconds, 1, ' s')} />
                  <Field label="Trials" value={formatInteger(experiment?.num_trials)} />
                  <Field
                    label="Security Configuration"
                    value={<span className="text-xs">{controlsLabel(experiment?.security_controls)}</span>}
                  />
                  <Field
                    label="Measurement Mode"
                    value={
                      <Badge variant={modeVariant(selected.measurement_mode)}>
                        {selected.measurement_mode}
                      </Badge>
                    }
                  />
                  <Field
                    label="Carbon Intensity"
                    value={formatScalar(selected.carbon_intensity, 1, ' gCO₂/kWh')}
                  />
                  <Field
                    label="Attribution ID"
                    value={`#${selected.id} (experiment #${selected.experiment_id})`}
                  />
                  <Field label="Recorded" value={formatDateTime(selected.created_at)} />
                </FieldGrid>
                <FormulaNote>
                  {selected.formula_version}: ΔE = E_security − E_baseline ={' '}
                  {formatNumber(selected.security_energy_joules, 2)} −{' '}
                  {formatNumber(selected.baseline_energy_joules, 2)} ={' '}
                  {formatNumber(selected.marginal_energy_joules, 2)} J
                </FormulaNote>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardTitle>Baseline vs Security Energy</CardTitle>
          <CardContent className="mt-3">
            {selected ? (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={energyChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={tooltipStyle} formatter={(value: number) => [`${formatNumber(value, 2)} J`, 'Energy']} />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                  <Bar dataKey="energyJoules" fill={chartConfig.colors.primary} radius={[4, 4, 0, 0]} name="Energy (J)" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-56 text-sm text-muted">No data</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardTitle>Marginal Energy by Attack Intensity</CardTitle>
          <CardContent className="mt-3">
            {intensityData.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={intensityData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                  <XAxis dataKey="intensity" tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(value: number) => [`${formatNumber(value, 2)} J`, 'Mean ΔE']}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                  <Bar
                    dataKey="meanMarginalJoules"
                    fill={chartConfig.colors.warning}
                    radius={[4, 4, 0, 0]}
                    name="Mean marginal ΔE (J)"
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-56 text-sm text-muted">No data</div>
            )}
            <p className="text-[11px] text-muted mt-2">
              Mean over the current filter selection, grouped by attack intensity.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardTitle>Marginal Energy vs Workload</CardTitle>
          <CardContent className="mt-3">
            {workloadData.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={workloadData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                  <XAxis
                    dataKey="workload"
                    tick={{ fontSize: 10, fill: chartConfig.tickFill }}
                    axisLine={false}
                    tickLine={false}
                    angle={-20}
                    textAnchor="end"
                    height={50}
                  />
                  <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(value: number) => [`${formatNumber(value, 2)} J`, 'Mean ΔE']}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                  <Bar
                    dataKey="meanMarginalJoules"
                    fill={chartConfig.colors.accent}
                    radius={[4, 4, 0, 0]}
                    name="Mean marginal ΔE (J)"
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-56 text-sm text-muted">No data</div>
            )}
            <p className="text-[11px] text-muted mt-2">
              Mean marginal ΔE per recorded workload value and unit.
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardTitle>Energy / Carbon Comparison</CardTitle>
        <CardContent className="mt-3">
          {selected ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={carbonChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} formatter={(value: number) => [`${formatNumber(value, 6)} kg`, 'CO₂']} />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
                <Bar dataKey="carbonKg" fill={chartConfig.colors.success} radius={[4, 4, 0, 0]} name="Carbon (kg)" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-56 text-sm text-muted">No data</div>
          )}
          <p className="text-[11px] text-muted mt-2">
            Carbon values are derived from estimated energy × grid intensity.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
