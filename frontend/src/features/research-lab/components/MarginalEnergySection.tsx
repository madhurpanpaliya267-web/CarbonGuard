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
import { Field, FieldGrid, FormulaNote, SectionEmpty, SectionError } from './ResearchBits'
import {
  controlsLabel,
  formatInteger,
  formatJoules,
  formatKilograms,
  formatScalar,
  formatWatts,
  modeVariant,
  workloadLabel,
} from '../utils/format'
import type { Experiment, MarginalEnergyResult } from '../types/research'

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
}

function meanByIntensity(items: MarginalEnergyResult[]) {
  const buckets = new Map<string, number[]>()
  items.forEach((item) => {
    const key = item.attack_intensity || 'unknown'
    const values = buckets.get(key) ?? []
    values.push(item.marginal_energy_joules)
    buckets.set(key, values)
  })
  return [...buckets.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([intensity, values]) => ({
      intensity,
      meanMarginalJoules: values.reduce((a, b) => a + b, 0) / values.length,
      observations: values.length,
    }))
}

export default function MarginalEnergySection({ items, experiments, error }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const selected = useMemo(() => {
    if (items.length === 0) return null
    return items.find((item) => item.id === selectedId) ?? items[items.length - 1]
  }, [items, selectedId])

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

  const intensityData = useMemo(() => meanByIntensity(items), [items])

  if (error) {
    return (
      <Card>
        <SectionError message={error} />
      </Card>
    )
  }

  if (items.length === 0 || !selected) {
    return (
      <Card>
        <SectionEmpty
          title="No marginal energy attributions yet"
          message="Run a MARGINAL_ENERGY experiment and compute attribution to populate Phase 5 results. Nothing is generated for display."
        />
      </Card>
    )
  }

  const experiment = experiments.find((e) => e.id === selected.experiment_id)

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
              value={selected.id}
              onChange={(event) => setSelectedId(Number(event.target.value))}
              className="bg-card border border-border rounded-md px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:border-accent/50"
            >
              {items.map((item) => (
                <option key={item.id} value={item.id}>
                  #{item.id} · {item.attack_type}/{item.attack_intensity} · ΔE{' '}
                  {formatNumber(item.marginal_energy_joules, 1)} J
                </option>
              ))}
            </select>
          </div>
        </div>

        <CardContent className="mt-4 space-y-5">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-background/60 border border-border rounded-md p-4">
              <p className="text-xs font-semibold text-text-primary mb-3">Energy</p>
              <FieldGrid>
                <Field label="Baseline Energy" value={formatJoules(selected.baseline_energy_joules)} />
                <Field label="Security Energy" value={formatJoules(selected.security_energy_joules)} />
                <Field label="Marginal Energy ΔE" value={formatJoules(selected.marginal_energy_joules)} />
                <Field label="Baseline Energy (kWh)" value={formatScalar(selected.baseline_energy_kwh, 6)} />
                <Field label="Security Energy (kWh)" value={formatScalar(selected.security_energy_kwh, 6)} />
                <Field label="Marginal Energy (kWh)" value={formatScalar(selected.marginal_energy_kwh, 6)} />
              </FieldGrid>
            </div>

            <div className="bg-background/60 border border-border rounded-md p-4">
              <p className="text-xs font-semibold text-text-primary mb-3">Power &amp; Carbon</p>
              <FieldGrid>
                <Field label="Baseline Power" value={formatWatts(selected.baseline_power_watts)} />
                <Field label="Security Power" value={formatWatts(selected.security_power_watts)} />
                <Field label="Marginal Power ΔP" value={formatWatts(selected.marginal_power_watts)} />
                <Field label="Baseline Carbon" value={formatKilograms(selected.baseline_carbon_kg)} />
                <Field label="Security Carbon" value={formatKilograms(selected.security_carbon_kg)} />
                <Field label="Carbon Difference ΔC" value={formatKilograms(selected.marginal_carbon_kg)} />
              </FieldGrid>
            </div>
          </div>

          <div className="bg-background/60 border border-border rounded-md p-4">
            <p className="text-xs font-semibold text-text-primary mb-3">Context</p>
            <FieldGrid>
              <Field label="Attack Type" value={selected.attack_type} />
              <Field label="Attack Intensity" value={selected.attack_intensity} />
              <Field label="Workload" value={workloadLabel(selected.workload_value, selected.workload_unit)} />
              <Field label="Duration" value={formatScalar(selected.duration_seconds, 1, ' s')} />
              <Field
                label="Security Configuration"
                value={<span className="text-xs">{controlsLabel(experiment?.security_controls)}</span>}
              />
              <Field
                label="Measurement Mode"
                value={<Badge variant={modeVariant(selected.measurement_mode)}>{selected.measurement_mode}</Badge>}
              />
              <Field label="Carbon Intensity" value={formatScalar(selected.carbon_intensity, 1, ' gCO₂/kWh')} />
              <Field label="Attribution ID" value={`#${selected.id} (experiment #${selected.experiment_id})`} />
              <Field label="Recorded" value={formatDateTime(selected.created_at)} />
            </FieldGrid>
            <FormulaNote>
              {selected.formula_version}: ΔE = E_security − E_baseline ={' '}
              {formatNumber(selected.security_energy_joules, 2)} −{' '}
              {formatNumber(selected.baseline_energy_joules, 2)} ={' '}
              {formatNumber(selected.marginal_energy_joules, 2)} J
            </FormulaNote>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardTitle>Baseline vs Security Energy</CardTitle>
          <CardContent className="mt-3">
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
          </CardContent>
        </Card>

        <Card>
          <CardTitle>Energy / Carbon Comparison</CardTitle>
          <CardContent className="mt-3">
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={carbonChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={tooltipStyle} formatter={(value: number) => [`${formatNumber(value, 6)} kg`, 'CO₂']} />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
                <Bar dataKey="carbonKg" fill={chartConfig.colors.cyan} radius={[4, 4, 0, 0]} name="Carbon (kg)" />
              </BarChart>
            </ResponsiveContainer>
            <p className="text-[11px] text-muted mt-2">
              Carbon values are derived from estimated energy × grid intensity.
            </p>
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
              Mean of {formatInteger(items.length)} persisted attribution
              {items.length === 1 ? '' : 's'}, grouped by attack intensity.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
