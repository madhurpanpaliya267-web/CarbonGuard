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
} from '../utils/format'
import { meanBy } from '../utils/researchMetrics'
import type { AmplificationResult, Experiment, SecurityControl } from '../types/research'

const tooltipStyle = {
  backgroundColor: chartConfig.tooltipBg,
  border: `1px solid ${chartConfig.tooltipBorder}`,
  borderRadius: '8px',
  fontSize: '12px',
}

interface Props {
  items: AmplificationResult[]
  error: string | null
  experiments?: Experiment[]
  controls?: SecurityControl[]
}

interface Filters {
  control: string
  attack_type: string
  attack_intensity: string
  measurement_mode: string
}

const emptyFilters: Filters = {
  control: '',
  attack_type: '',
  attack_intensity: '',
  measurement_mode: '',
}

export default function AmplificationSection({
  items,
  error,
  experiments = [],
  controls = [],
}: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [filters, setFilters] = useState<Filters>(emptyFilters)

  const experimentById = useMemo(
    () => new Map(experiments.map((experiment) => [experiment.id, experiment])),
    [experiments],
  )

  const filtered = useMemo(() => {
    return items.filter((item) => {
      if (filters.control && item.control_name !== filters.control) return false
      if (filters.attack_type && item.attack_type !== filters.attack_type) return false
      if (filters.attack_intensity && item.attack_intensity !== filters.attack_intensity)
        return false
      if (filters.measurement_mode && item.measurement_mode !== filters.measurement_mode)
        return false
      return true
    })
  }, [items, filters])

  const controlOptions = useMemo(() => {
    const used = new Set(items.map((item) => item.control_name))
    return controls
      .filter((control) => used.has(control.control_id))
      .map((control) => ({ value: control.control_id, label: control.display_name }))
  }, [items, controls])

  const options = useMemo(
    () => ({
      control: controlOptions,
      attack_type: distinctOptions(items.map((item) => item.attack_type)),
      attack_intensity: distinctOptions(items.map((item) => item.attack_intensity)),
      measurement_mode: distinctOptions(items.map((item) => item.measurement_mode)),
    }),
    [items, controlOptions],
  )

  const selected = useMemo(() => {
    if (filtered.length === 0) return null
    return filtered.find((item) => item.id === selectedId) ?? filtered[filtered.length - 1]
  }, [filtered, selectedId])

  const intensityData = useMemo(
    () =>
      meanBy(
        filtered,
        (item) => item.attack_intensity,
        (item) => item.additional_defense_energy,
      ).map((row) => ({ intensity: row.bucket, meanAde: row.mean })),
    [filtered],
  )

  const workloadEnergyData = useMemo(
    () =>
      meanBy(
        filtered,
        (item) => `${formatNumber(item.attack_workload, 2)} ${item.workload_unit}`,
        (item) => item.energy_attack_defense,
      ).map((row) => ({ workload: row.bucket, meanEnergy: row.mean })),
    [filtered],
  )

  const workloadDeaData = useMemo(
    () =>
      meanBy(
        filtered,
        (item) => `${formatNumber(item.attack_workload, 2)} ${item.workload_unit}`,
        (item) => item.defense_energy_amplification,
      ).map((row) => ({ workload: row.bucket, meanDea: row.mean })),
    [filtered],
  )

  const controlData = useMemo(
    () =>
      meanBy(
        filtered,
        (item) => item.control_name,
        (item) => item.additional_defense_energy,
      ).map((row) => ({ control: row.bucket, meanAde: row.mean })),
    [filtered],
  )

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
          title="No defense amplification results recorded"
          message="Run a DEFENSE_AMPLIFICATION experiment and compute amplification to populate Phase 7 results."
        />
      </Card>
    )
  }

  const stats = selected?.statistics

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle>Defense Energy Amplification (Phase 7)</CardTitle>
            <p className="text-xs text-muted mt-1">
              ADE = E_attack+defense − E_attack+baseline; DEA = ADE / attack workload.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted" htmlFor="amplification-select">
              Result
            </label>
            <select
              id="amplification-select"
              value={selected?.id ?? ''}
              onChange={(event) => setSelectedId(Number(event.target.value))}
              className="bg-card border border-border rounded-md px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:border-accent/50"
            >
              {filtered.map((item) => (
                <option key={item.id} value={item.id}>
                  #{item.id} · {item.control_name} · ADE{' '}
                  {formatNumber(item.additional_defense_energy, 2)} J
                </option>
              ))}
            </select>
          </div>
        </div>

        <CardContent className="mt-4 space-y-5">
          <FilterBar
            title="Filters"
            onReset={() => setFilters(emptyFilters)}
            summary={`${formatInteger(filtered.length)} of ${formatInteger(items.length)} results`}
          >
            <FilterSelect
              id="amplification-filter-control"
              label="Security Control"
              value={filters.control}
              onChange={(value) => setFilters((f) => ({ ...f, control: value }))}
              options={options.control}
              allLabel="Any control"
            />
            <FilterSelect
              id="amplification-filter-attack"
              label="Attack Type"
              value={filters.attack_type}
              onChange={(value) => setFilters((f) => ({ ...f, attack_type: value }))}
              options={options.attack_type}
            />
            <FilterSelect
              id="amplification-filter-intensity"
              label="Attack Intensity"
              value={filters.attack_intensity}
              onChange={(value) => setFilters((f) => ({ ...f, attack_intensity: value }))}
              options={options.attack_intensity}
            />
            <FilterSelect
              id="amplification-filter-mode"
              label="Measurement Mode"
              value={filters.measurement_mode}
              onChange={(value) => setFilters((f) => ({ ...f, measurement_mode: value }))}
              options={options.measurement_mode}
              allLabel="Any mode"
            />
          </FilterBar>

          {!selected ? (
            <SectionEmpty
              title="No amplification results match the current filters"
              message="Adjust or reset the filters above to inspect persisted Phase 7 results."
            />
          ) : (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-background/60 border border-border rounded-md p-4">
                  <p className="text-xs font-semibold text-text-primary mb-3">Amplification</p>
                  <FieldGrid>
                    <Field
                      label="Attack Workload"
                      value={`${formatNumber(selected.attack_workload, 2)} ${selected.workload_unit}`}
                    />
                    <Field label="Baseline Attack Energy" value={formatJoules(selected.energy_attack_only)} />
                    <Field label="Attack + Defense Energy" value={formatJoules(selected.energy_attack_defense)} />
                    <Field label="Additional Defense Energy (ADE)" value={formatJoules(selected.additional_defense_energy)} />
                    <Field
                      label="Defense Energy Amplification (DEA)"
                      value={formatScalar(selected.defense_energy_amplification, 6, ' J/unit')}
                    />
                    <Field label="Control" value={selected.control_name} />
                  </FieldGrid>
                </div>

                <div className="bg-background/60 border border-border rounded-md p-4">
                  <p className="text-xs font-semibold text-text-primary mb-3">Power &amp; Carbon</p>
                  <FieldGrid>
                    <Field label="Baseline Power" value={formatWatts(selected.power_baseline)} />
                    <Field label="Defense Power" value={formatWatts(selected.power_defense)} />
                    <Field label="Power Difference" value={formatWatts(selected.power_amplification)} />
                    <Field label="Baseline Carbon" value={formatKilograms(selected.carbon_baseline_kg)} />
                    <Field label="Defense Carbon" value={formatKilograms(selected.carbon_defense_kg)} />
                    <Field label="Carbon Difference" value={formatKilograms(selected.amplification_carbon_kg)} />
                    <Field
                      label="Defense Carbon per Workload"
                      value={formatCarbonPerWorkload(selected.defense_carbon_per_workload)}
                    />
                    <Field
                      label="Carbon Basis"
                      value={<span className="text-xs">{carbonBasisLabel(selected.carbon_basis)}</span>}
                    />
                  </FieldGrid>
                  {carbonPerWorkloadReason(selected.defense_carbon_per_workload) && (
                    <p className="text-[11px] text-warning mt-2">
                      Carbon per workload unavailable:{' '}
                      {carbonPerWorkloadReason(selected.defense_carbon_per_workload)}
                    </p>
                  )}
                  <p className="text-[11px] text-muted mt-2">{CARBON_INTENSITY_NOTE}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-background/60 border border-border rounded-md p-4">
                  <p className="text-xs font-semibold text-text-primary mb-3">Trial Statistics</p>
                  {stats ? (
                    <>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                        <StatTile label="Trials (paired)" value={formatInteger(selected.num_paired_trials)} />
                        <StatTile label="n" value={formatInteger(stats.amplification_energy.count)} />
                        <StatTile label="Mean ADE" value={formatNumber(stats.amplification_energy.mean, 3)} />
                        <StatTile label="Median ADE" value={formatNumber(stats.amplification_energy.median, 3)} />
                        <StatTile label="Std Dev (pop.)" value={formatNumber(stats.amplification_energy.std_dev, 3)} />
                        <StatTile
                          label="Min / Max"
                          value={`${formatNumber(stats.amplification_energy.min, 2)} / ${formatNumber(stats.amplification_energy.max, 2)}`}
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-2 mt-3">
                        <StatTile label="Mean DEA" value={formatNumber(stats.amplification_ratio.mean, 6)} />
                        <StatTile label="Formula" value={stats.formula_version} />
                      </div>
                    </>
                  ) : (
                    <p className="text-xs text-warning">
                      Not available: no stored trial statistics for this result. Statistics are
                      attached when the amplification is computed through the API.
                    </p>
                  )}
                  <div className="grid grid-cols-2 gap-2 mt-3">
                    <StatTile label="Result Trial #" value={formatInteger(selected.trial_number)} />
                    <StatTile label="Energy Provider" value={selected.energy_provider ?? '—'} />
                  </div>
                </div>

                <div className="bg-background/60 border border-border rounded-md p-4">
                  <p className="text-xs font-semibold text-text-primary mb-3">Context</p>
                  <FieldGrid>
                    <Field label="Attack Type" value={selected.attack_type} />
                    <Field label="Attack Intensity" value={selected.attack_intensity} />
                    <Field label="Duration" value={formatScalar(selected.duration_seconds, 1, ' s')} />
                    <Field
                      label="Trials"
                      value={formatInteger(experimentById.get(selected.experiment_id)?.num_trials)}
                    />
                    <Field
                      label="Measurement Mode"
                      value={
                        <Badge variant={modeVariant(selected.measurement_mode)}>
                          {selected.measurement_mode ?? '—'}
                        </Badge>
                      }
                    />
                    <Field
                      label="Carbon Intensity"
                      value={formatScalar(selected.carbon_intensity, 1, ' gCO₂/kWh')}
                    />
                    <Field label="Recorded" value={formatDateTime(selected.created_at)} />
                  </FieldGrid>
                  <FormulaNote>
                    {selected.formula_version}: ADE = {formatNumber(selected.energy_attack_defense, 2)} −{' '}
                    {formatNumber(selected.energy_attack_only, 2)} ={' '}
                    {formatNumber(selected.additional_defense_energy, 2)} J
                  </FormulaNote>
                </div>
              </div>

              <div className="px-3 py-2 bg-background/60 border border-border rounded-md">
                <p className="text-[11px] text-muted leading-relaxed">
                  Three distinct quantities: Phase 5 ΔE = E_security − E_baseline (attack-conditioned
                  marginal energy), Phase 6 I(A,B) = E_AB − E_A − E_B + E_0 (control interaction), and
                  Phase 7 ADE = E_attack+defense − E_attack+baseline (additional defense energy). They
                  answer different questions and are not interchangeable.
                </p>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardTitle>Attack Intensity vs Additional Defense Energy</CardTitle>
          <CardContent className="mt-3">
            {intensityData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={intensityData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                  <XAxis dataKey="intensity" tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={tooltipStyle} formatter={(value: number) => [`${formatNumber(value, 3)} J`, 'Mean ADE']} />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                  <Bar dataKey="meanAde" fill={chartConfig.colors.warning} radius={[4, 4, 0, 0]} name="Mean ADE (J)" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-64 text-sm text-muted">No data</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardTitle>Attack Workload vs Defense Energy</CardTitle>
          <CardContent className="mt-3">
            {workloadEnergyData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={workloadEnergyData}>
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
                  <Tooltip contentStyle={tooltipStyle} formatter={(value: number) => [`${formatNumber(value, 3)} J`, 'Mean E_attack+defense']} />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                  <Bar dataKey="meanEnergy" fill={chartConfig.colors.primary} radius={[4, 4, 0, 0]} name="Mean attack + defense energy (J)" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-64 text-sm text-muted">No data</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardTitle>Attack Workload vs Defense Energy Amplification</CardTitle>
          <CardContent className="mt-3">
            {workloadDeaData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={workloadDeaData}>
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
                  <Tooltip contentStyle={tooltipStyle} formatter={(value: number) => [formatNumber(value, 6), 'Mean DEA (J/unit)']} />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                  <Bar dataKey="meanDea" fill={chartConfig.colors.purple} radius={[4, 4, 0, 0]} name="Mean DEA (J/unit)" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-64 text-sm text-muted">No data</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardTitle>Defense Energy Amplification by Control</CardTitle>
          <CardContent className="mt-3">
            {controlData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={controlData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                  <XAxis dataKey="control" tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={tooltipStyle} formatter={(value: number) => [`${formatNumber(value, 3)} J`, 'Mean ADE']} />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                  <Bar dataKey="meanAde" fill={chartConfig.colors.success} radius={[4, 4, 0, 0]} name="Mean additional defense energy (J)" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-64 text-sm text-muted">No data</div>
            )}
            <p className="text-[11px] text-muted mt-2">
              Controls are taken from the API control catalogue filtered to controls present in the
              persisted results — never a hardcoded list. Estimated energy, not a hardware
              measurement and not a claim that any control is preferable.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
