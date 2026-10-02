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
  FormulaNote,
  SectionEmpty,
  SectionError,
  StatTile,
} from './ResearchBits'
import {
  formatInteger,
  formatJoules,
  formatKilograms,
  formatScalar,
  formatWatts,
  modeVariant,
} from '../utils/format'
import type { AmplificationResult } from '../types/research'

const tooltipStyle = {
  backgroundColor: chartConfig.tooltipBg,
  border: `1px solid ${chartConfig.tooltipBorder}`,
  borderRadius: '8px',
  fontSize: '12px',
}

function meanAdeByControl(items: AmplificationResult[]) {
  const buckets = new Map<string, number[]>()
  items.forEach((item) => {
    const values = buckets.get(item.control_name) ?? []
    values.push(item.additional_defense_energy)
    buckets.set(item.control_name, values)
  })
  return [...buckets.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([control, values]) => ({
      control,
      meanAde: values.reduce((a, b) => a + b, 0) / values.length,
    }))
}

interface Props {
  items: AmplificationResult[]
  error: string | null
}

export default function AmplificationSection({ items, error }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const selected = useMemo(() => {
    if (items.length === 0) return null
    return items.find((item) => item.id === selectedId) ?? items[items.length - 1]
  }, [items, selectedId])

  const controlData = useMemo(() => meanAdeByControl(items), [items])

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
          title="No defense amplification results recorded"
          message="Run a DEFENSE_AMPLIFICATION experiment and compute amplification to populate Phase 7 results."
        />
      </Card>
    )
  }

  const stats = selected.statistics

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
              value={selected.id}
              onChange={(event) => setSelectedId(Number(event.target.value))}
              className="bg-card border border-border rounded-md px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:border-accent/50"
            >
              {items.map((item) => (
                <option key={item.id} value={item.id}>
                  #{item.id} · {item.control_name} · ADE {formatNumber(item.additional_defense_energy, 2)} J
                </option>
              ))}
            </select>
          </div>
        </div>

        <CardContent className="mt-4 space-y-5">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-background/60 border border-border rounded-md p-4">
              <p className="text-xs font-semibold text-text-primary mb-3">Amplification</p>
              <FieldGrid>
                <Field label="Attack Workload" value={`${formatNumber(selected.attack_workload, 2)} ${selected.workload_unit}`} />
                <Field label="Baseline Attack Energy" value={formatJoules(selected.energy_attack_only)} />
                <Field label="Attack + Defense Energy" value={formatJoules(selected.energy_attack_defense)} />
                <Field label="Additional Defense Energy (ADE)" value={formatJoules(selected.additional_defense_energy)} />
                <Field label="Defense Energy Amplification (DEA)" value={formatScalar(selected.defense_energy_amplification, 6, ' J/unit')} />
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
              </FieldGrid>
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
                    <StatTile label="Min / Max" value={`${formatNumber(stats.amplification_energy.min, 2)} / ${formatNumber(stats.amplification_energy.max, 2)}`} />
                  </div>
                  <div className="grid grid-cols-2 gap-2 mt-3">
                    <StatTile label="Mean DEA" value={formatNumber(stats.amplification_ratio.mean, 6)} />
                    <StatTile label="Formula" value={stats.formula_version} />
                  </div>
                </>
              ) : (
                <p className="text-xs text-warning">
                  No stored trial statistics for this result. Statistics are attached when the
                  amplification is computed through the API.
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
                  label="Measurement Mode"
                  value={<Badge variant={modeVariant(selected.measurement_mode)}>{selected.measurement_mode ?? '—'}</Badge>}
                />
                <Field label="Carbon Intensity" value={formatScalar(selected.carbon_intensity, 1, ' gCO₂/kWh')} />
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
        </CardContent>
      </Card>

      <Card>
        <CardTitle>Defense Energy Amplification by Control</CardTitle>
        <CardContent className="mt-3">
          {controlData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={controlData}>
                <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                <XAxis dataKey="control" tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={tooltipStyle}
                  formatter={(value: number) => [`${formatNumber(value, 3)} J`, 'Mean ADE']}
                />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
                <Bar
                  dataKey="meanAde"
                  fill={chartConfig.colors.warning}
                  radius={[4, 4, 0, 0]}
                  name="Mean additional defense energy (J)"
                />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64 text-sm text-muted">No data</div>
          )}
          <p className="text-[11px] text-muted mt-2">
            Mean ADE per control across persisted Phase 7 results. Estimated energy — not a hardware
            measurement and not a claim that any control is preferable.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
