import { useMemo } from 'react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'
import { Link } from 'react-router-dom'
import { Battery, FlaskConical, Layers, Radio, ShieldCheck, Sparkles } from 'lucide-react'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import Badge from '@/shared/ui/Badge'
import MetricCard from '@/shared/ui/MetricCard'
import { chartConfig } from '@/shared/utils/chartConfig'
import { formatDateTime, formatNumber } from '@/shared/utils/formatters'
import { researchApi } from '../api/researchApi'
import { useResearchQuery } from '../hooks/useResearchQuery'
import { SectionEmpty, SectionError, SectionLoading } from './ResearchBits'
import { formatInteger, formatJoules, formatKilograms } from '../utils/format'
import {
  amplificationTrend,
  countExperimentType,
  experimentModeCounts,
  CARBON_PROVENANCE_NOTE,
} from '../utils/researchMetrics'
import type { ResearchLabData } from '../hooks/useResearchLabData'

const tooltipStyle = {
  backgroundColor: chartConfig.tooltipBg,
  border: `1px solid ${chartConfig.tooltipBorder}`,
  borderRadius: '8px',
  fontSize: '12px',
}

export default function ResearchOverview({ data }: { data: ResearchLabData }) {
  const summary = useResearchQuery(() => researchApi.getResearchSummary(), 'summary')
  const metrics = useResearchQuery(() => researchApi.getResearchMetrics(), 'metrics')

  const trend = useMemo(() => amplificationTrend(data.amplification), [data.amplification])
  const modes = useMemo(() => experimentModeCounts(data.experiments), [data.experiments])

  const loading = data.loading || summary.loading || metrics.loading
  const totalExperiments = summary.data?.total_experiments ?? data.experiments.length
  const empty = !data.loading && !summary.error && totalExperiments === 0

  if (loading) return <SectionLoading label="Loading research overview…" />

  if (summary.error) {
    return (
      <Card>
        <SectionError title="Research overview unavailable" message={summary.error} />
      </Card>
    )
  }

  if (empty) {
    return (
      <Card>
        <CardTitle>Research Overview</CardTitle>
        <CardContent className="mt-3">
          <SectionEmpty
            title="No research experiments recorded yet"
            message="Open the Experiment Runner to configure an attack, security controls, duration and trial count, then run your first synthetic experiment. Results appear here once the backend persists them — nothing on this page is generated on the client."
          />
          <div className="flex justify-center">
            <Link
              to="/research-lab/experiments"
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-background bg-accent rounded-md hover:bg-accent-light transition-colors"
            >
              <FlaskConical className="w-4 h-4" />
              Open Experiment Runner
            </Link>
          </div>
        </CardContent>
      </Card>
    )
  }

  const attackTypes = summary.data?.attack_types ?? []
  const controlTypes = summary.data?.security_controls ?? []
  const measurementModes = summary.data?.measurement_modes ?? []

  const marginalBlock = metrics.data?.marginal_energy
  const carbonBlock = metrics.data?.marginal_carbon
  const interactionBlock = metrics.data?.interaction_effect
  const failedSources = (Object.entries(data.errors) as [string, string | null][]).filter(
    ([, error]) => error,
  )

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle>Research Overview</CardTitle>
            <p className="text-xs text-muted mt-1">
              Persisted research records from Phases 5–10 of the CarbonGuard research engine.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge variant="warning" size="md">
              ESTIMATED ENERGY
            </Badge>
            <Badge variant="success" size="md">
              MEASURED WHEN CONFIGURED
            </Badge>
            <Badge variant="purple" size="md">
              SIMULATED ATTACK PROFILES
            </Badge>
          </div>
        </div>

        <CardContent className="mt-4 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
            <MetricCard
              title="Total Experiments"
              value={formatInteger(totalExperiments)}
              icon={FlaskConical}
              color="primary"
              subtitle={`${formatInteger(summary.data?.total_trials ?? 0)} recorded trial runs`}
            />
            <MetricCard
              title="Estimated Experiments"
              value={formatInteger(modes.ESTIMATED ?? 0)}
              icon={Battery}
              color="warning"
              subtitle="Measurement mode ESTIMATED"
            />
            <MetricCard
              title="Measured Experiments"
              value={formatInteger(modes.MEASURED ?? 0)}
              icon={Battery}
              color="success"
              subtitle="Measurement mode MEASURED"
            />
            <MetricCard
              title="Simulated Experiments"
              value={formatInteger(modes.SIMULATED ?? 0)}
              icon={Radio}
              color="purple"
              subtitle="Measurement mode SIMULATED"
            />
            <MetricCard
              title="Attack Types Tested"
              value={formatInteger(attackTypes.length)}
              icon={ShieldCheck}
              color="primary"
              subtitle={attackTypes.length ? attackTypes.join(', ') : 'None recorded'}
            />
            <MetricCard
              title="Security Controls Tested"
              value={formatInteger(controlTypes.length)}
              icon={Layers}
              color="primary"
              subtitle={controlTypes.length ? controlTypes.join(', ') : 'None recorded'}
            />
            <MetricCard
              title="Average Marginal Energy"
              value={formatJoules(marginalBlock?.statistics?.mean ?? null)}
              icon={Sparkles}
              color="primary"
              subtitle={
                marginalBlock?.status === 'available'
                  ? `Mean of ${formatInteger(marginalBlock.observation_count)} attributions`
                  : marginalBlock?.reason ?? 'Not available'
              }
            />
            <MetricCard
              title="Average Marginal Carbon"
              value={formatKilograms(carbonBlock?.statistics?.mean ?? null)}
              icon={Sparkles}
              color="primary"
              subtitle={
                carbonBlock?.status === 'available'
                  ? `Calculated mean of ${formatInteger(carbonBlock.observation_count)} attributions`
                  : carbonBlock?.reason ?? 'Not available'
              }
            />
            <MetricCard
              title="Interaction Experiments"
              value={formatInteger(countExperimentType(data.experiments, 'INTERACTION'))}
              icon={Layers}
              color="primary"
              subtitle={`${formatInteger(summary.data?.interaction_observations ?? 0)} persisted interaction results`}
            />
            <MetricCard
              title="Highest Interaction Effect"
              value={
                interactionBlock?.status === 'available' && interactionBlock.statistics
                  ? formatJoules(interactionBlock.statistics.max)
                  : 'Not available'
              }
              icon={Sparkles}
              color="primary"
              subtitle={
                interactionBlock?.reason ??
                `Maximum of ${formatInteger(interactionBlock?.observation_count ?? 0)} observations`
              }
            />
            <MetricCard
              title="Defense Amplification Results"
              value={formatInteger(summary.data?.amplification_observations ?? 0)}
              icon={Layers}
              color="primary"
              subtitle="Persisted Phase 7 ADE observations"
            />
            <MetricCard
              title="Measurement Modes"
              value={formatInteger(measurementModes.length)}
              icon={Battery}
              color="warning"
              subtitle={
                measurementModes.length
                  ? measurementModes.join(', ')
                  : 'No energy measurements recorded'
              }
            />
          </div>

          <div className="bg-card border border-border rounded-md p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-xs font-semibold text-text-primary">
                Defense Amplification Trend
              </p>
              <div className="flex flex-wrap gap-2">
                <Badge variant="warning" size="sm">
                  ADDITIONAL DEFENSE ENERGY
                </Badge>
              </div>
            </div>
            {trend.length > 0 ? (
              <div className="mt-3">
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={trend}>
                    <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                    <XAxis
                      dataKey="created_at"
                      tick={{ fontSize: 10, fill: chartConfig.tickFill }}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(value: string) => formatDateTime(value)}
                    />
                    <YAxis
                      tick={{ fontSize: 10, fill: chartConfig.tickFill }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip
                      contentStyle={tooltipStyle}
                      formatter={(value: number, name: string) => [
                        name === 'ADE (J)'
                          ? `${formatNumber(value, 3)} J`
                          : formatNumber(value, 6),
                        name,
                      ]}
                      labelFormatter={(label: string) => formatDateTime(label)}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px' }} />
                    <Line
                      type="monotone"
                      dataKey="additional_defense_energy"
                      stroke={chartConfig.colors.warning}
                      strokeWidth={2}
                      dot={{ r: 3 }}
                      name="ADE (J)"
                    />
                    <Line
                      type="monotone"
                      dataKey="defense_energy_amplification"
                      stroke={chartConfig.colors.purple}
                      strokeWidth={2}
                      strokeDasharray="4 4"
                      dot={{ r: 3 }}
                      name="DEA (J/unit)"
                    />
                  </LineChart>
                </ResponsiveContainer>
                <p className="text-[11px] text-muted mt-2">
                  {formatInteger(trend.length)} persisted result
                  {trend.length === 1 ? '' : 's'}, ordered by recording time. Estimated energy —
                  no claim that any control is preferable.
                </p>
              </div>
            ) : (
              <SectionEmpty
                title="No defense amplification results yet"
                message="Compute Phase 7 amplification for a stored experiment to plot this trend."
              />
            )}
          </div>

          <div className="px-3 py-2 bg-warning/10 border border-warning/20 rounded-md">
            <p className="text-xs text-warning leading-relaxed">
              Energy values shown in this lab are <strong>ESTIMATED</strong> unless a hardware
              measurement provider reports <strong>MEASURED</strong> mode. Attack workloads come
              from safe synthetic simulation — no real systems are scanned or attacked.
            </p>
            <p className="text-xs text-warning leading-relaxed mt-2">
              {CARBON_PROVENANCE_NOTE}
            </p>
          </div>

          {failedSources.length > 0 && (
            <SectionError
              title="Some research sources could not be loaded"
              message={failedSources.map(([source, error]) => `${source}: ${error}`).join(' · ')}
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
