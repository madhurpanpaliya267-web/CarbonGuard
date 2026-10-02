import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'
import { ArrowLeft, FlaskConical } from 'lucide-react'
import PageHeader from '@/shared/ui/PageHeader'
import Badge from '@/shared/ui/Badge'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
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
  CARBON_INTENSITY_NOTE,
  carbonBasisLabel,
  controlsLabel,
  formatInteger,
  formatJoules,
  formatKilograms,
  formatWatts,
  modeVariant,
  parseControls,
  shortId,
  workloadLabel,
} from '../utils/format'
import { calculateCarbonKg, sumEnergyJoules } from '../utils/researchMetrics'
import type {
  AmplificationResult,
  Experiment,
  ExperimentSummary,
  InteractionResult,
  MarginalEnergyResult,
  ResearchAnalyticsResult,
} from '../types/research'

const tooltipStyle = {
  backgroundColor: chartConfig.tooltipBg,
  border: `1px solid ${chartConfig.tooltipBorder}`,
  borderRadius: '8px',
  fontSize: '12px',
}

type AnalyticsKey = 'marginal' | 'interaction' | 'amplification'

interface AnalyticsState {
  key: AnalyticsKey
  label: string
  result: ResearchAnalyticsResult | null
  error: string | null
}

const ANALYTICS_SPECS: Array<{ key: AnalyticsKey; label: string; source: string; metric: string }> = [
  { key: 'marginal', label: 'Marginal energy (J)', source: 'marginal', metric: 'marginal_energy_joules' },
  { key: 'interaction', label: 'Interaction effect (J)', source: 'interaction', metric: 'interaction_effect' },
  { key: 'amplification', label: 'Additional defense energy (J)', source: 'amplification', metric: 'additional_defense_energy' },
]

interface DetailState {
  loading: boolean
  error: string | null
  experiment: Experiment | null
  summary: ExperimentSummary | null
  marginal: MarginalEnergyResult[]
  interaction: InteractionResult[]
  amplification: AmplificationResult[]
  analytics: AnalyticsState[]
  sourceErrors: string[]
}

function statusVariant(status: string): 'success' | 'danger' | 'warning' | 'muted' {
  if (status === 'COMPLETED' || status === 'completed') return 'success'
  if (status === 'FAILED' || status === 'failed') return 'danger'
  if (status === 'RUNNING' || status === 'running') return 'warning'
  return 'muted'
}

const initialState: DetailState = {
  loading: true,
  error: null,
  experiment: null,
  summary: null,
  marginal: [],
  interaction: [],
  amplification: [],
  analytics: [],
  sourceErrors: [],
}

async function settle<T>(run: () => Promise<T>): Promise<[T | null, string | null]> {
  try {
    return [await run(), null]
  } catch (error) {
    return [null, error instanceof Error ? error.message : 'Request failed']
  }
}

export default function ExperimentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [state, setState] = useState<DetailState>(initialState)

  useEffect(() => {
    if (!id) {
      setState({ ...initialState, loading: false, error: 'Missing experiment identifier.' })
      return
    }

    let cancelled = false

    async function load() {
      setState({ ...initialState })

      const [experiment, experimentError] = await settle(() =>
        researchApi.getExperiment(id as string),
      )

      if (!experiment) {
        if (cancelled) return
        setState({
          ...initialState,
          loading: false,
          error: experimentError ?? 'The experiment could not be loaded from the research API.',
        })
        return
      }

      const experimentId = experiment.id

      const [
        [summary, summaryError],
        [marginalList, marginalError],
        [interactionList, interactionError],
        [amplificationList, amplificationError],
        analyticsOutcomes,
      ] = await Promise.all([
        settle(() => researchApi.getExperimentSummary(id as string)),
        settle(() => researchApi.listMarginalEnergy({ experiment_id: experimentId, limit: 200 })),
        settle(() => researchApi.listInteractionEffects({ experiment_id: experimentId, limit: 200 })),
        settle(() => researchApi.listAmplification({ experiment_id: experimentId, limit: 200 })),
        Promise.all(
          ANALYTICS_SPECS.map((spec) =>
            settle(() =>
              researchApi.computeAnalytics({
                source: spec.source,
                metric: spec.metric,
                filters: { experiment_id: experimentId },
              }),
            ),
          ),
        ),
      ])

      if (cancelled) return

      const analytics: AnalyticsState[] = ANALYTICS_SPECS.map((spec, index) => {
        const [result, error] = analyticsOutcomes[index]
        return { key: spec.key, label: spec.label, result, error }
      })

      const sourceErrors = [
        summaryError ? `Runs and measurements: ${summaryError}` : null,
        marginalError ? `Marginal energy: ${marginalError}` : null,
        interactionError ? `Interaction effects: ${interactionError}` : null,
        amplificationError ? `Defense amplification: ${amplificationError}` : null,
      ].filter((value): value is string => value !== null)

      setState({
        loading: false,
        error: null,
        experiment,
        summary,
        marginal: marginalList?.items ?? [],
        interaction: interactionList?.items ?? [],
        amplification: amplificationList?.items ?? [],
        analytics,
        sourceErrors,
      })
    }

    load()

    return () => {
      cancelled = true
    }
  }, [id])

  if (state.loading) {
    return (
      <div className="space-y-6" data-testid="experiment-detail-page">
        <PageHeader title="Experiment Details" subtitle="Loading experiment record…" />
        <SectionLoading label="Loading experiment…" />
      </div>
    )
  }

  if (state.error || !state.experiment) {
    return (
      <div className="space-y-6" data-testid="experiment-detail-page">
        <PageHeader title="Experiment Details" subtitle="Record unavailable" />
        <Card>
          <CardContent>
            <SectionError
              title="Unable to load this experiment"
              message={state.error ?? 'The experiment does not exist or is not readable.'}
            />
            <div className="flex justify-center">
              <Link
                to="/research-lab/experiments"
                className="inline-flex items-center gap-2 text-xs text-accent hover:text-accent-light"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Back to experiments
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const experiment = state.experiment
  const summary = state.summary
  const totalEnergy = sumEnergyJoules(summary)
  const carbonKg = calculateCarbonKg(totalEnergy, experiment.carbon_intensity)

  const trialPoints = (summary?.runs ?? []).map((run) => {
    const measurement = summary?.measurements.find((item) => item.run_id === run.id)
    return {
      trial: `T${run.trial_number}`,
      energy: measurement ? measurement.energy_joules : null,
    }
  })

  return (
    <div className="space-y-6" data-testid="experiment-detail-page">
      <PageHeader
        title={experiment.name}
        subtitle={`Experiment #${experiment.id} · ${shortId(experiment.experiment_uuid)} · ${experiment.experiment_type}`}
        badge={
          <span className="flex items-center gap-2">
            <Badge variant={statusVariant(experiment.status)} size="md">
              {experiment.status}
            </Badge>
            <Badge variant={modeVariant(experiment.measurement_mode)} size="md">
              {experiment.measurement_mode}
            </Badge>
          </span>
        }
        actions={
          <Link
            to="/research-lab/experiments"
            className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-muted border border-border rounded-md hover:text-text-primary hover:border-accent/40 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            All experiments
          </Link>
        }
      />

      {state.sourceErrors.length > 0 && (
        <div className="bg-danger/10 border border-danger/20 rounded-md p-3 space-y-1">
          <p className="text-xs text-danger font-medium">Some experiment data could not be loaded</p>
          {state.sourceErrors.map((message) => (
            <p key={message} className="text-[11px] text-muted">
              {message}
            </p>
          ))}
        </div>
      )}

      <Card data-testid="experiment-config">
        <CardTitle>Configuration & provenance</CardTitle>
        <CardContent className="mt-4 space-y-4">
          <FieldGrid>
            <Field label="Experiment UUID" value={experiment.experiment_uuid} />
            <Field label="Experiment type" value={experiment.experiment_type} />
            <Field label="Attack" value={`${experiment.attack_type} / ${experiment.attack_intensity}`} />
            <Field label="Workload profile" value={experiment.workload_profile ?? 'Not recorded'} />
            <Field label="Security Controls" value={controlsLabel(experiment.security_controls)} />
            <Field label="Measurement Mode" value={experiment.measurement_mode} />
            <Field label="Duration" value={`${formatInteger(experiment.duration_seconds)} s`} />
            <Field label="Trials configured" value={formatInteger(experiment.num_trials)} />
            <Field
              label="Carbon intensity"
              value={
                experiment.carbon_intensity !== null
                  ? `${formatNumber(experiment.carbon_intensity, 1)} gCO₂/kWh`
                  : 'Not configured'
              }
            />
            <Field
              label="Renewable share"
              value={
                experiment.renewable_pct !== null ? `${formatNumber(experiment.renewable_pct, 1)} %` : 'Not configured'
              }
            />
            <Field label="Software version" value={experiment.software_version ?? 'Not recorded'} />
            <Field label="Configuration version" value={experiment.configuration_version ?? 'Not recorded'} />
            <Field label="Random seed" value={experiment.random_seed !== null ? String(experiment.random_seed) : 'Not recorded'} />
            <Field label="Created" value={formatDateTime(experiment.created_at)} />
            <Field label="Completed" value={experiment.completed_at ? formatDateTime(experiment.completed_at) : 'Not completed'} />
            <Field label="Notes" value={experiment.notes ?? 'None'} />
          </FieldGrid>
          <FormulaNote>{CARBON_INTENSITY_NOTE}</FormulaNote>
        </CardContent>
      </Card>

      <Card data-testid="experiment-trials">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle>Trials & energy</CardTitle>
          <span className="flex items-center gap-2">
            <Badge variant={modeVariant(experiment.measurement_mode)} size="sm">
              {experiment.measurement_mode}
            </Badge>
            <Badge variant="muted" size="sm">
              {summary ? `${summary.runs.length} runs` : 'summary unavailable'}
            </Badge>
          </span>
        </div>
        <CardContent className="mt-4 space-y-4">
          {!summary && (
            <SectionError
              title="Summary unavailable"
              message="Runs and measurements could not be loaded for this experiment."
            />
          )}

          {summary && summary.runs.length === 0 && (
            <SectionEmpty
              title="No runs recorded"
              message="This experiment has not executed any trials yet."
            />
          )}

          {summary && summary.runs.length > 0 && (
            <>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <StatTile label="Total energy" value={totalEnergy !== null ? formatJoules(totalEnergy) : 'Not available'} />
                <StatTile
                  label="Carbon (calculated)"
                  value={carbonKg !== null ? formatKilograms(carbonKg) : 'Not available'}
                />
                <StatTile label="Runs" value={formatInteger(summary.runs.length)} />
                <StatTile
                  label="Detection rate (mean)"
                  value={(() => {
                    const rates = summary.security_effects
                      .map((effect) => effect.detection_rate)
                      .filter((value): value is number => typeof value === 'number')
                    if (rates.length === 0) return 'Not available'
                    return `${formatNumber((rates.reduce((a, b) => a + b, 0) / rates.length) * 100, 1)} %`
                  })()}
                />
              </div>

              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={trialPoints}>
                    <CartesianGrid strokeDasharray="3 3" stroke={chartConfig.gridStroke} />
                    <XAxis dataKey="trial" tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: chartConfig.tickFill }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={tooltipStyle} formatter={(value: number) => [`${formatNumber(value, 2)} J`, 'Energy']} />
                    <Bar dataKey="energy" fill={chartConfig.colors.primary} radius={[4, 4, 0, 0]} name="Energy (J)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border text-muted uppercase tracking-wider">
                      <th className="text-left px-2 py-1.5">Trial</th>
                      <th className="text-left px-2 py-1.5">Run UUID</th>
                      <th className="text-left px-2 py-1.5">Workload</th>
                      <th className="text-right px-2 py-1.5">Energy</th>
                      <th className="text-right px-2 py-1.5">Power</th>
                      <th className="text-right px-2 py-1.5">Detection</th>
                      <th className="text-left px-2 py-1.5">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.runs.map((run) => {
                      const measurement = summary.measurements.find((item) => item.run_id === run.id)
                      const effect = summary.security_effects.find((item) => item.run_id === run.id)
                      return (
                        <tr key={run.id} className="border-b border-border/50">
                          <td className="px-2 py-1.5 text-text-primary">{run.trial_number}</td>
                          <td className="px-2 py-1.5 font-mono text-muted">{shortId(run.run_uuid)}</td>
                          <td className="px-2 py-1.5 text-muted">
                            {workloadLabel(run.workload_value, run.workload_unit)}
                          </td>
                          <td className="px-2 py-1.5 text-right">
                            {measurement ? formatJoules(measurement.energy_joules) : '—'}
                          </td>
                          <td className="px-2 py-1.5 text-right">
                            {measurement ? formatWatts(measurement.power_watts) : '—'}
                          </td>
                          <td className="px-2 py-1.5 text-right">
                            {effect?.detection_rate !== null && effect?.detection_rate !== undefined
                              ? `${formatNumber(effect.detection_rate * 100, 1)} %`
                              : '—'}
                          </td>
                          <td className="px-2 py-1.5">
                            <Badge variant={statusVariant(run.status)} size="sm">
                              {run.status}
                            </Badge>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Card data-testid="experiment-marginal">
          <CardTitle>Marginal energy</CardTitle>
          <CardContent className="mt-4 space-y-3">
            <StatTile label="Observations" value={formatInteger(state.marginal.length)} />
            {state.marginal.length === 0 ? (
              <SectionEmpty
                title="No marginal energy rows"
                message="Compute marginal energy for this experiment to see ΔE = E_security − E_baseline here."
              />
            ) : (
              <>
                <StatTile
                  label="Mean ΔE"
                  value={formatJoules(
                    state.marginal.reduce((sum, row) => sum + row.marginal_energy_joules, 0) /
                      state.marginal.length,
                  )}
                />
                <div className="overflow-x-auto max-h-64 overflow-y-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-border text-muted uppercase tracking-wider">
                        <th className="text-left px-2 py-1.5">Baseline</th>
                        <th className="text-left px-2 py-1.5">Security</th>
                        <th className="text-right px-2 py-1.5">ΔE</th>
                        <th className="text-right px-2 py-1.5">ΔC</th>
                      </tr>
                    </thead>
                    <tbody>
                      {state.marginal.map((row) => (
                        <tr key={row.id} className="border-b border-border/50">
                          <td className="px-2 py-1.5">{formatJoules(row.baseline_energy_joules)}</td>
                          <td className="px-2 py-1.5">{formatJoules(row.security_energy_joules)}</td>
                          <td className="px-2 py-1.5 text-right text-accent">
                            {formatJoules(row.marginal_energy_joules)}
                          </td>
                          <td className="px-2 py-1.5 text-right">
                            {row.marginal_carbon_kg !== null
                              ? formatKilograms(row.marginal_carbon_kg)
                              : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card data-testid="experiment-interaction">
          <CardTitle>Interaction analysis</CardTitle>
          <CardContent className="mt-4 space-y-3">
            <StatTile label="Observations" value={formatInteger(state.interaction.length)} />
            {state.interaction.length === 0 ? (
              <SectionEmpty
                title="No interaction rows"
                message="Compute control interaction for this experiment to see I(A,B) = E_AB − E_A − E_B + E_0 here."
              />
            ) : (
              <div className="overflow-x-auto max-h-72 overflow-y-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border text-muted uppercase tracking-wider">
                      <th className="text-left px-2 py-1.5">Pair</th>
                      <th className="text-right px-2 py-1.5">E₀</th>
                      <th className="text-right px-2 py-1.5">E_AB</th>
                      <th className="text-right px-2 py-1.5">I(A,B)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {state.interaction.map((row) => (
                      <tr key={row.id} className="border-b border-border/50">
                        <td className="px-2 py-1.5 text-muted">
                          {row.control_a} + {row.control_b}
                        </td>
                        <td className="px-2 py-1.5 text-right">{formatJoules(row.energy_baseline)}</td>
                        <td className="px-2 py-1.5 text-right">{formatJoules(row.energy_ab)}</td>
                        <td className="px-2 py-1.5 text-right text-accent">
                          {formatJoules(row.interaction_effect)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        <Card data-testid="experiment-amplification">
          <CardTitle>Defense amplification</CardTitle>
          <CardContent className="mt-4 space-y-3">
            <StatTile label="Observations" value={formatInteger(state.amplification.length)} />
            {state.amplification.length === 0 ? (
              <SectionEmpty
                title="No amplification rows"
                message="Compute defense energy amplification for this experiment to see ADE and DEA here."
              />
            ) : (
              <div className="overflow-x-auto max-h-72 overflow-y-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-border text-muted uppercase tracking-wider">
                      <th className="text-left px-2 py-1.5">Control</th>
                      <th className="text-right px-2 py-1.5">ADE</th>
                      <th className="text-right px-2 py-1.5">DEA</th>
                    </tr>
                  </thead>
                  <tbody>
                    {state.amplification.map((row) => (
                      <tr key={row.id} className="border-b border-border/50">
                        <td className="px-2 py-1.5 text-muted">{row.control_name}</td>
                        <td className="px-2 py-1.5 text-right text-warning">
                          {formatJoules(row.additional_defense_energy)}
                        </td>
                        <td className="px-2 py-1.5 text-right text-warning">
                          {formatNumber(row.defense_energy_amplification, 3)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card data-testid="experiment-statistics">
        <CardTitle>Descriptive statistics</CardTitle>
        <CardContent className="mt-4 space-y-4">
          <p className="text-[11px] text-muted leading-relaxed">
            Statistics are produced by the Phase 8 analytics endpoint for this experiment only. Values
            absent from the API are shown as “Not available” — nothing is estimated client-side.
          </p>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {state.analytics.map((entry) => (
              <div key={entry.key} className="bg-background/60 border border-border rounded-md p-3">
                <p className="text-xs font-semibold text-text-primary">{entry.label}</p>
                {entry.error && (
                  <p className="text-[11px] text-warning mt-2 leading-relaxed">
                    Not available: {entry.error}
                  </p>
                )}
                {entry.result && (
                  <div className="mt-2 space-y-2">
                    <div className="grid grid-cols-2 gap-2">
                      <StatTile label="n" value={formatInteger(entry.result.n)} />
                      <StatTile label="Mean" value={formatNumber(entry.result.statistics.mean, 3)} />
                      <StatTile label="Median" value={formatNumber(entry.result.statistics.median, 3)} />
                      <StatTile label="Std dev" value={formatNumber(entry.result.statistics.std_dev, 3)} />
                    </div>
                    {entry.result.confidence_interval &&
                      entry.result.confidence_interval.status === 'ok' &&
                      entry.result.confidence_interval.lower !== null &&
                      entry.result.confidence_interval.upper !== null && (
                        <p className="text-[11px] text-muted">
                          {formatNumber(entry.result.confidence_interval.level * 100, 0)}% CI [
                          {formatNumber(entry.result.confidence_interval.lower, 3)},{' '}
                          {formatNumber(entry.result.confidence_interval.upper, 3)}] ·{' '}
                          {entry.result.confidence_interval.method}
                        </p>
                      )}
                    {entry.result.confidence_interval &&
                      entry.result.confidence_interval.status !== 'ok' && (
                        <p className="text-[11px] text-warning">
                          Confidence interval unavailable:{' '}
                          {entry.result.confidence_interval.reason ?? 'no reason provided'} (n=
                          {entry.result.confidence_interval.n}).
                        </p>
                      )}
                    {entry.result.hypothesis_test &&
                      (entry.result.hypothesis_test.status === 'ok' ? (
                        <p className="text-[11px] text-muted leading-relaxed">
                          {entry.result.hypothesis_test.test_name}: p ={' '}
                          {entry.result.hypothesis_test.p_value !== null
                            ? formatNumber(entry.result.hypothesis_test.p_value, 4)
                            : 'Not available'}
                          {' — '}
                          {entry.result.hypothesis_test.interpretation.replace(/_/g, ' ')}
                        </p>
                      ) : (
                        <p className="text-[11px] text-warning">
                          Test not computed:{' '}
                          {entry.result.hypothesis_test.reason ?? 'insufficient or degenerate data'}
                        </p>
                      ))}
                    {entry.result.warnings.map((warning) => (
                      <p key={warning} className="text-[11px] text-warning">
                        {warning}
                      </p>
                    ))}
                    {entry.result.limitations.map((limitation) => (
                      <p key={limitation} className="text-[11px] text-muted">
                        {limitation}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="flex flex-wrap items-center gap-3 text-xs text-muted">
        <FlaskConical className="w-4 h-4 text-accent" />
        <span>
          Controls recorded: {parseControls(experiment.security_controls).join(', ') || 'none'}.
        </span>
        <span>{carbonBasisLabel(experiment.measurement_mode)} energy basis.</span>
        <span>{CARBON_INTENSITY_NOTE}</span>
      </div>
    </div>
  )
}
