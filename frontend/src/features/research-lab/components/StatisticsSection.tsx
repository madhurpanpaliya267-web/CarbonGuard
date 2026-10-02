import { useEffect, useMemo, useState } from 'react'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import Badge from '@/shared/ui/Badge'
import { formatDateTime, formatNumber } from '@/shared/utils/formatters'
import { researchApi } from '../api/researchApi'
import { SectionEmpty, SectionError, SectionLoading, StatTile } from './ResearchBits'
import { formatInteger } from '../utils/format'
import type {
  AnalyticsConfidenceInterval,
  AnalyticsHypothesisTest,
  ResearchAnalyticsResult,
} from '../types/research'

export const ANALYSIS_SOURCES = [
  { id: 'marginal', label: 'Marginal Energy (Phase 5)' },
  { id: 'interaction', label: 'Interaction Effect (Phase 6)' },
  { id: 'amplification', label: 'Defense Amplification (Phase 7)' },
] as const

export const METRICS_BY_SOURCE: Record<string, string[]> = {
  marginal: [
    'marginal_energy_joules',
    'marginal_power_watts',
    'marginal_carbon_kg',
    'baseline_energy_joules',
    'security_energy_joules',
    'baseline_power_watts',
    'security_power_watts',
    'baseline_carbon_kg',
    'security_carbon_kg',
    'baseline_energy_kwh',
    'security_energy_kwh',
    'marginal_energy_kwh',
    'workload_value',
    'duration_seconds',
    'carbon_intensity',
    'marginal_carbon_per_workload',
  ],
  interaction: [
    'interaction_effect',
    'interaction_power',
    'interaction_carbon_kg',
    'interaction_index',
    'energy_baseline',
    'energy_a',
    'energy_b',
    'energy_ab',
    'power_baseline',
    'power_a',
    'power_b',
    'power_ab',
    'carbon_baseline_kg',
    'carbon_a_kg',
    'carbon_b_kg',
    'carbon_ab_kg',
    'workload_value',
    'duration_seconds',
    'carbon_intensity',
    'interaction_carbon_per_workload',
  ],
  amplification: [
    'additional_defense_energy',
    'power_amplification',
    'amplification_carbon_kg',
    'defense_energy_amplification',
    'energy_attack_only',
    'energy_attack_defense',
    'power_baseline',
    'power_defense',
    'carbon_baseline_kg',
    'carbon_defense_kg',
    'attack_workload',
    'duration_seconds',
    'carbon_intensity',
    'defense_carbon_per_workload',
  ],
}

const COMMON_GROUP_DIMS = [
  'attack_type',
  'attack_intensity',
  'workload_unit',
  'duration_seconds',
  'measurement_mode',
]

export const GROUP_DIMS_BY_SOURCE: Record<string, string[]> = {
  marginal: [...COMMON_GROUP_DIMS],
  interaction: [...COMMON_GROUP_DIMS, 'control_a', 'control_b', 'energy_provider'],
  amplification: [...COMMON_GROUP_DIMS, 'control_name', 'energy_provider'],
}

const TESTS = [
  { id: '', label: 'Descriptive only' },
  { id: 'paired_t', label: 'Paired t-test' },
  { id: 'wilcoxon_signed_rank', label: 'Wilcoxon signed-rank' },
]

const ALTERNATIVES = [
  { id: 'two-sided', label: 'Two-sided' },
  { id: 'greater', label: 'Greater' },
  { id: 'less', label: 'Less' },
]

const CONFIDENCE_LEVELS = [0.9, 0.95, 0.99]

function ConfidenceIntervalPanel({ interval }: { interval: AnalyticsConfidenceInterval }) {
  if (interval.status !== 'ok') {
    return (
      <p className="text-xs text-warning leading-relaxed">
        Confidence interval unavailable: {interval.reason ?? 'no reason provided'} (n={interval.n}).
      </p>
    )
  }
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
      <StatTile label="Level" value={`${formatNumber(interval.level * 100, 0)}%`} />
      <StatTile
        label="Interval"
        value={`[${formatNumber(interval.lower ?? 0, 4)}, ${formatNumber(interval.upper ?? 0, 4)}]`}
      />
      <StatTile label="Std Error" value={formatNumber(interval.standard_error ?? 0, 4)} />
      <StatTile label="df" value={formatInteger(interval.degrees_of_freedom)} />
    </div>
  )
}

function HypothesisPanel({ test }: { test: AnalyticsHypothesisTest }) {
  const unavailable = test.status !== 'ok'
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="primary" size="md">
          {test.test_name}
        </Badge>
        <Badge variant={test.reject_null === true ? 'warning' : 'muted'} size="md">
          {test.interpretation.replace(/_/g, ' ')}
        </Badge>
        <Badge variant="muted" size="md">
          α = {formatNumber(test.significance_level, 3)}
        </Badge>
      </div>

      <p className="text-[11px] text-muted leading-relaxed">
        {test.null_hypothesis} vs. {test.alternative_hypothesis} ({test.alternative}).
      </p>

      {unavailable ? (
        <p className="text-xs text-warning leading-relaxed">
          Test not computed: {test.reason ?? 'insufficient or degenerate data'}
        </p>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <StatTile
            label={test.test_id === 'paired_t' ? 't statistic' : 'W⁺ statistic'}
            value={formatNumber(test.statistic ?? 0, 4)}
          />
          <StatTile label="p-value" value={formatNumber(test.p_value ?? 0, 6)} />
          <StatTile label="Sample size" value={formatInteger(test.sample_count)} />
          <StatTile label="Method" value={test.method.replace(/_/g, ' ')} />
        </div>
      )}

      {test.effect_size && (
        <div className="bg-background/60 border border-border rounded-md px-3 py-2">
          <p className="text-[10px] uppercase tracking-wider text-muted">
            Effect size ({test.effect_size.name})
          </p>
          <p className="text-sm text-text-primary mt-0.5">
            {test.effect_size.status === 'ok' && test.effect_size.value !== null
              ? formatNumber(test.effect_size.value, 4)
              : `Unavailable — ${test.effect_size.reason ?? 'undefined for this sample'}`}
          </p>
          <p className="text-[11px] text-muted mt-1">{test.effect_size.convention}</p>
        </div>
      )}

      <p className="text-[11px] text-muted leading-relaxed">{test.method_notes}</p>
    </div>
  )
}

export default function StatisticsSection() {
  const [source, setSource] = useState('marginal')
  const [metric, setMetric] = useState('marginal_energy_joules')
  const [groupBy, setGroupBy] = useState('')
  const [hypothesisTest, setHypothesisTest] = useState('paired_t')
  const [alternative, setAlternative] = useState('two-sided')
  const [confidenceLevel, setConfidenceLevel] = useState(0.95)

  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ResearchAnalyticsResult | null>(null)

  const [saved, setSaved] = useState<ResearchAnalyticsResult[]>([])
  const [savedLoading, setSavedLoading] = useState(true)
  const [savedError, setSavedError] = useState<string | null>(null)

  const metrics = METRICS_BY_SOURCE[source] ?? []
  const groupDims = GROUP_DIMS_BY_SOURCE[source] ?? []

  useEffect(() => {
    let cancelled = false
    researchApi
      .listAnalytics()
      .then((response) => {
        if (!cancelled) {
          setSaved(response.items)
          setSavedError(null)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setSavedError(err instanceof Error ? err.message : 'Unable to load stored analyses')
        }
      })
      .finally(() => {
        if (!cancelled) setSavedLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const testableMetric = useMemo(() => {
    const differenceMetrics = new Set([
      ...(METRICS_BY_SOURCE.marginal ?? []).slice(0, 3),
      'marginal_carbon_per_workload',
      ...(METRICS_BY_SOURCE.interaction ?? []).slice(0, 3),
      'interaction_index',
      'interaction_carbon_per_workload',
      ...(METRICS_BY_SOURCE.amplification ?? []).slice(0, 3),
      'defense_energy_amplification',
      'defense_carbon_per_workload',
    ])
    return differenceMetrics.has(metric)
  }, [metric])

  function handleSourceChange(nextSource: string) {
    setSource(nextSource)
    const nextMetrics = METRICS_BY_SOURCE[nextSource] ?? []
    setMetric(nextMetrics[0] ?? '')
    setGroupBy('')
  }

  async function runAnalysis() {
    setRunning(true)
    setError(null)
    setResult(null)
    try {
      const response = await researchApi.computeAnalytics({
        source,
        metric,
        group_by: groupBy ? [groupBy] : [],
        include_confidence_interval: true,
        confidence_level: confidenceLevel,
        hypothesis_test: hypothesisTest || null,
        alternative,
        significance_level: 0.05,
      })
      setResult(response)
      const refreshed = await researchApi.listAnalytics().catch(() => null)
      if (refreshed) setSaved(refreshed.items)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis request failed')
    } finally {
      setRunning(false)
    }
  }

  const selectClass =
    'bg-card border border-border rounded-md px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:border-accent/50'
  const labelClass = 'text-xs text-muted'

  return (
    <div className="space-y-6">
      <Card>
        <CardTitle>Statistical Analysis (Phase 8)</CardTitle>
        <p className="text-xs text-muted mt-1">
          Descriptive and inferential statistics over persisted Phase 5–7 results. The service
          never invents observations; unavailable inference is reported with a reason.
        </p>

        <CardContent className="mt-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className={labelClass} htmlFor="analytics-source">
                Source
              </label>
              <select
                id="analytics-source"
                className={selectClass}
                value={source}
                onChange={(event) => handleSourceChange(event.target.value)}
              >
                {ANALYSIS_SOURCES.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className={labelClass} htmlFor="analytics-metric">
                Metric
              </label>
              <select
                id="analytics-metric"
                className={selectClass}
                value={metric}
                onChange={(event) => setMetric(event.target.value)}
              >
                {metrics.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className={labelClass} htmlFor="analytics-group">
                Group by
              </label>
              <select
                id="analytics-group"
                className={selectClass}
                value={groupBy}
                onChange={(event) => setGroupBy(event.target.value)}
              >
                <option value="">No grouping</option>
                {groupDims.map((dim) => (
                  <option key={dim} value={dim}>
                    {dim}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className={labelClass} htmlFor="analytics-test">
                Hypothesis test
              </label>
              <select
                id="analytics-test"
                className={selectClass}
                value={hypothesisTest}
                onChange={(event) => setHypothesisTest(event.target.value)}
              >
                {TESTS.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.label}
                  </option>
                ))}
              </select>
              {!testableMetric && hypothesisTest && (
                <p className="text-[11px] text-warning">
                  Level metrics are not paired differences; the backend rejects a test on them.
                </p>
              )}
            </div>

            <div className="flex flex-col gap-1.5">
              <label className={labelClass} htmlFor="analytics-alternative">
                Alternative
              </label>
              <select
                id="analytics-alternative"
                className={selectClass}
                value={alternative}
                disabled={!hypothesisTest}
                onChange={(event) => setAlternative(event.target.value)}
              >
                {ALTERNATIVES.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className={labelClass} htmlFor="analytics-confidence">
                Confidence level
              </label>
              <select
                id="analytics-confidence"
                className={selectClass}
                value={confidenceLevel}
                onChange={(event) => setConfidenceLevel(Number(event.target.value))}
              >
                {CONFIDENCE_LEVELS.map((level) => (
                  <option key={level} value={level}>
                    {level * 100}%
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button
              onClick={runAnalysis}
              disabled={running}
              className="px-4 py-2 text-xs font-medium rounded-md bg-accent/15 text-accent border border-accent/30 hover:bg-accent/25 transition-colors disabled:opacity-50"
            >
              {running ? 'Running analysis…' : 'Run analysis'}
            </button>
            <span className="text-[11px] text-muted">
              Deterministic: identical data and configuration return identical results.
            </span>
          </div>
        </CardContent>
      </Card>

      {running && (
        <Card>
          <SectionLoading label="Computing statistics…" />
        </Card>
      )}

      {error && (
        <Card>
          <SectionError title="Analysis could not be computed" message={error} />
        </Card>
      )}

      {result && !running && (
        <Card>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle>Analysis Result</CardTitle>
            <div className="flex flex-wrap gap-2">
              <Badge variant="muted" size="sm">
                {result.analysis_id}
              </Badge>
              <Badge variant="primary" size="sm">
                {result.metric_category}
              </Badge>
              <Badge variant={result.measurement_mode === 'MEASURED' ? 'success' : 'warning'} size="sm">
                {result.measurement_mode ?? 'UNKNOWN'} ENERGY
              </Badge>
            </div>
          </div>

          <CardContent className="mt-4 space-y-5">
            <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-2">
              <StatTile label="Sample size (n)" value={formatInteger(result.n)} />
              <StatTile label="Mean" value={formatNumber(result.statistics.mean, 4)} />
              <StatTile label="Median" value={formatNumber(result.statistics.median, 4)} />
              <StatTile label="Std deviation" value={formatNumber(result.statistics.std_dev, 4)} />
              <StatTile label="Minimum" value={formatNumber(result.statistics.min, 4)} />
              <StatTile label="Maximum" value={formatNumber(result.statistics.max, 4)} />
            </div>

            <p className="text-[11px] text-muted">
              Standard deviation convention: <code>{result.std_dev_convention}</code> · metric{' '}
              <code>{result.metric}</code> · source <code>{result.source}</code> · analysis version{' '}
              <code>{result.analysis_version}</code>
            </p>

            {result.confidence_interval && (
              <div className="bg-background/60 border border-border rounded-md p-3">
                <p className="text-xs font-semibold text-text-primary mb-2">Confidence Interval</p>
                <ConfidenceIntervalPanel interval={result.confidence_interval} />
              </div>
            )}

            {result.hypothesis_test ? (
              <div className="bg-background/60 border border-border rounded-md p-3">
                <p className="text-xs font-semibold text-text-primary mb-2">Hypothesis Test</p>
                <HypothesisPanel test={result.hypothesis_test} />
              </div>
            ) : (
              <div className="bg-background/60 border border-border rounded-md p-3">
                <p className="text-xs font-semibold text-text-primary mb-2">Hypothesis Test</p>
                <p className="text-xs text-warning leading-relaxed">
                  {result.warnings.find((warning) => warning.startsWith('Hypothesis test')) ??
                    'No hypothesis test was computed for this configuration.'}
                </p>
              </div>
            )}

            {result.groups.length > 0 && (
              <div className="bg-background/60 border border-border rounded-md p-3">
                <p className="text-xs font-semibold text-text-primary mb-2">
                  Grouped Analysis ({result.groups.length} groups)
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-border text-muted uppercase tracking-wider">
                        <th className="text-left px-2 py-1.5">Group</th>
                        <th className="text-right px-2 py-1.5">n</th>
                        <th className="text-right px-2 py-1.5">Mean</th>
                        <th className="text-right px-2 py-1.5">Median</th>
                        <th className="text-right px-2 py-1.5">Std Dev</th>
                        <th className="text-right px-2 py-1.5">Min</th>
                        <th className="text-right px-2 py-1.5">Max</th>
                        <th className="text-left px-2 py-1.5">Inference</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.groups.map((group, index) => (
                        <tr key={index} className="border-b border-border/50">
                          <td className="px-2 py-1.5 text-text-primary">
                            {Object.entries(group.group)
                              .map(([key, value]) => `${key}=${value}`)
                              .join(', ')}
                          </td>
                          <td className="px-2 py-1.5 text-right">{group.n}</td>
                          <td className="px-2 py-1.5 text-right">
                            {formatNumber(group.statistics.mean, 4)}
                          </td>
                          <td className="px-2 py-1.5 text-right">
                            {formatNumber(group.statistics.median, 4)}
                          </td>
                          <td className="px-2 py-1.5 text-right">
                            {formatNumber(group.statistics.std_dev, 4)}
                          </td>
                          <td className="px-2 py-1.5 text-right">
                            {formatNumber(group.statistics.min, 4)}
                          </td>
                          <td className="px-2 py-1.5 text-right">
                            {formatNumber(group.statistics.max, 4)}
                          </td>
                          <td className="px-2 py-1.5 text-muted">
                            {group.hypothesis_test
                              ? group.hypothesis_test.status === 'ok'
                                ? `p=${formatNumber(group.hypothesis_test.p_value ?? 0, 4)}`
                                : group.hypothesis_test.reason ?? 'unavailable'
                              : 'not requested'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {result.warnings.length > 0 && (
              <div className="px-3 py-2 bg-warning/10 border border-warning/20 rounded-md">
                <p className="text-[10px] uppercase tracking-wider text-warning mb-1">Warnings</p>
                <ul className="space-y-1">
                  {result.warnings.map((warning) => (
                    <li key={warning} className="text-[11px] text-warning leading-relaxed">
                      • {warning}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="px-3 py-2 bg-background/60 border border-border rounded-md">
              <p className="text-[10px] uppercase tracking-wider text-muted mb-1">Limitations</p>
              <ul className="space-y-1">
                {result.limitations.map((limitation) => (
                  <li key={limitation} className="text-[11px] text-muted leading-relaxed">
                    • {limitation}
                  </li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardTitle>Stored Analyses</CardTitle>
        <CardContent className="mt-3">
          {savedLoading ? (
            <SectionLoading label="Loading stored analyses…" />
          ) : savedError ? (
            <SectionError title="Unable to load stored analyses" message={savedError} />
          ) : saved.length === 0 ? (
            <SectionEmpty
              title="No stored analyses yet"
              message="Run an analysis above to persist a reproducible result."
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border text-muted uppercase tracking-wider">
                    <th className="text-left px-2 py-1.5">Analysis ID</th>
                    <th className="text-left px-2 py-1.5">Source</th>
                    <th className="text-left px-2 py-1.5">Metric</th>
                    <th className="text-right px-2 py-1.5">n</th>
                    <th className="text-right px-2 py-1.5">Mean</th>
                    <th className="text-left px-2 py-1.5">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {saved.map((item) => (
                    <tr
                      key={item.analysis_id}
                      className="border-b border-border/50 hover:bg-card-hover cursor-pointer"
                      onClick={() => setResult(item)}
                    >
                      <td className="px-2 py-1.5 font-mono text-text-primary">{item.analysis_id}</td>
                      <td className="px-2 py-1.5">{item.source}</td>
                      <td className="px-2 py-1.5">{item.metric}</td>
                      <td className="px-2 py-1.5 text-right">{item.n}</td>
                      <td className="px-2 py-1.5 text-right">
                        {formatNumber(item.statistics.mean, 4)}
                      </td>
                      <td className="px-2 py-1.5 text-muted">{formatDateTime(item.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
