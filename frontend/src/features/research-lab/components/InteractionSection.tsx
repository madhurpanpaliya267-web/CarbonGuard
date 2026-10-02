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
  FormulaNote,
  SectionEmpty,
  SectionError,
  SectionLoading,
  StatTile,
} from './ResearchBits'
import {
  formatInteger,
  formatJoules,
  formatKilograms,
  formatScalar,
  formatWatts,
  modeVariant,
  workloadLabel,
} from '../utils/format'
import type { InteractionResult, ResearchAnalyticsResult } from '../types/research'

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

function meanEffectByPair(items: InteractionResult[]) {
  const buckets = new Map<string, number[]>()
  items.forEach((item) => {
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
}

interface Props {
  items: InteractionResult[]
  error: string | null
}

export default function InteractionSection({ items, error }: Props) {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [stats, setStats] = useState<ResearchAnalyticsResult | null>(null)
  const [statsError, setStatsError] = useState<string | null>(null)
  const [statsLoading, setStatsLoading] = useState(false)

  const selected = useMemo(() => {
    if (items.length === 0) return null
    return items.find((item) => item.id === selectedId) ?? items[items.length - 1]
  }, [items, selectedId])

  const pairData = useMemo(() => meanEffectByPair(items), [items])

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

  if (items.length === 0 || !selected) {
    return (
      <Card>
        <SectionEmpty
          title="No interaction effects recorded"
          message="Run an INTERACTION experiment and compute interaction effects to populate Phase 6 results."
        />
      </Card>
    )
  }

  const interpretation = selected.interpretation ?? 'not classified'

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle>Security-Control Interaction (Phase 6)</CardTitle>
            <p className="text-xs text-muted mt-1">
              I(A,B) = E_AB − E_A − E_B + E_0, as persisted by the backend.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted" htmlFor="interaction-select">
              Result
            </label>
            <select
              id="interaction-select"
              value={selected.id}
              onChange={(event) => setSelectedId(Number(event.target.value))}
              className="bg-card border border-border rounded-md px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:border-accent/50"
            >
              {items.map((item) => (
                <option key={item.id} value={item.id}>
                  #{item.id} · {pairKey(item)} · I {formatNumber(item.interaction_effect, 2)} J
                </option>
              ))}
            </select>
          </div>
        </div>

        <CardContent className="mt-4 space-y-5">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-background/60 border border-border rounded-md p-4">
              <p className="text-xs font-semibold text-text-primary mb-3">Configuration</p>
              <FieldGrid>
                <Field label="Control A" value={selected.control_a} />
                <Field label="Control B" value={selected.control_b} />
                <Field label="Attack Type" value={selected.attack_type ?? '—'} />
                <Field label="Attack Intensity" value={selected.attack_intensity ?? '—'} />
                <Field label="Workload" value={workloadLabel(selected.workload_value, selected.workload_unit)} />
                <Field label="Duration" value={formatScalar(selected.duration_seconds, 1, ' s')} />
              </FieldGrid>
            </div>

            <div className="bg-background/60 border border-border rounded-md p-4">
              <p className="text-xs font-semibold text-text-primary mb-3">Interaction</p>
              <FieldGrid>
                <Field label="Baseline Energy E₀" value={formatJoules(selected.energy_baseline)} />
                <Field label="Energy A" value={formatJoules(selected.energy_a)} />
                <Field label="Energy B" value={formatJoules(selected.energy_b)} />
                <Field label="Combined Energy E_AB" value={formatJoules(selected.energy_ab)} />
                <Field label="Interaction Effect I(A,B)" value={formatJoules(selected.interaction_effect)} />
                <Field label="Interaction Index" value={formatScalar(selected.interaction_index, 4)} />
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
                Super-additive: combined cost exceeds the sum of individual costs. Approximately
                additive: combined cost matches the sum within tolerance. Sub-additive: combined
                cost is below the sum. These are neutral descriptive labels, not rankings.
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
                    <StatTile label="Std Dev (pop.)" value={formatNumber(stats.statistics.std_dev, 3)} />
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
              <Field label="Interaction Carbon ΔC" value={formatKilograms(selected.interaction_carbon_kg)} />
              <Field label="Recorded" value={formatDateTime(selected.created_at)} />
              <Field label="Result ID" value={`#${selected.id} (experiment #${selected.experiment_id})`} />
              <Field label="Carbon Intensity" value={formatScalar(selected.carbon_intensity, 1, ' gCO₂/kWh')} />
            </FieldGrid>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardTitle>Interaction Effect by Control Pair</CardTitle>
        <CardContent className="mt-3">
          {pairData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={pairData}>
                <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                <XAxis dataKey="pair" tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
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
            <div className="flex items-center justify-center h-64 text-sm text-muted">No data</div>
          )}
          <p className="text-[11px] text-muted mt-2">
            Mean interaction effect per persisted control pair. Positive values indicate
            super-additive cost, negative values sub-additive cost.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
