import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { FlaskConical, Loader2, PlayCircle, Save, TriangleAlert } from 'lucide-react'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import Button from '@/shared/ui/Button'
import Badge from '@/shared/ui/Badge'
import { formatDateTime, formatNumber } from '@/shared/utils/formatters'
import { researchApi } from '../api/researchApi'
import {
  Field,
  FieldGrid,
  SectionError,
  SectionLoading,
  controlClass,
} from './ResearchBits'
import {
  controlsLabel,
  formatInteger,
  formatJoules,
  formatKilograms,
  formatWatts,
  modeVariant,
} from '../utils/format'
import { calculateCarbonKg, sumEnergyJoules } from '../utils/researchMetrics'
import type {
  AttackProfile,
  Experiment,
  ExperimentSummary,
  SecurityControl,
} from '../types/research'

export const MEASUREMENT_PROVIDERS = [
  { id: 'estimated', label: 'Estimated — deterministic model', available: true },
  { id: 'rapl', label: 'RAPL — CPU hardware counter', available: false },
  { id: 'kepler', label: 'Kepler — GPU hardware counter', available: false },
  { id: 'external', label: 'External power meter', available: false },
]

const EXPERIMENT_TYPES = [
  { id: 'MARGINAL_ENERGY', label: 'Marginal energy (Phase 5)' },
  { id: 'INTERACTION', label: 'Control interaction (Phase 6)' },
  { id: 'DEFENSE_AMPLIFICATION', label: 'Defense amplification (Phase 7)' },
]

const STEPS = [
  'Select attack',
  'Select intensity',
  'Select workload',
  'Select security controls',
  'Select measurement mode',
  'Set duration',
  'Set trials',
  'Run experiment',
  'Show results',
  'Save experiment',
]

type Phase = 'idle' | 'creating' | 'running' | 'loading' | 'done' | 'error'

interface Props {
  attacks: AttackProfile[]
  controls: SecurityControl[]
  referenceError: string | null
  onExperimentCreated?: () => void
}

function statusVariant(status: string): 'success' | 'danger' | 'warning' | 'muted' {
  if (status === 'COMPLETED' || status === 'completed') return 'success'
  if (status === 'FAILED' || status === 'failed') return 'danger'
  if (status === 'RUNNING' || status === 'running') return 'warning'
  return 'muted'
}

export default function ExperimentRunner({
  attacks,
  controls,
  referenceError,
  onExperimentCreated,
}: Props) {
  const [form, setForm] = useState({
    experiment_type: 'MARGINAL_ENERGY',
    attack_type: '',
    attack_intensity: '',
    attack_workload: '',
    workload_unit: '',
    security_controls: [] as string[],
    measurement_provider: 'estimated',
    duration_seconds: '60',
    number_of_trials: '3',
    carbon_intensity: '',
    name: '',
  })
  const [phase, setPhase] = useState<Phase>('idle')
  const [error, setError] = useState<string | null>(null)
  const [created, setCreated] = useState<Experiment | null>(null)
  const [summary, setSummary] = useState<ExperimentSummary | null>(null)

  const attack = useMemo(
    () => attacks.find((item) => item.attack_type === form.attack_type) ?? null,
    [attacks, form.attack_type],
  )
  const selectedProvider = MEASUREMENT_PROVIDERS.find(
    (provider) => provider.id === form.measurement_provider,
  )

  const busy = phase === 'creating' || phase === 'running' || phase === 'loading'

  function update(patch: Partial<typeof form>) {
    setForm((current) => ({ ...current, ...patch }))
  }

  function toggleControl(controlId: string) {
    setForm((current) => {
      const exists = current.security_controls.includes(controlId)
      return {
        ...current,
        security_controls: exists
          ? current.security_controls.filter((id) => id !== controlId)
          : [...current.security_controls, controlId],
      }
    })
  }

  function validate(): string | null {
    if (!form.attack_type) return 'Select an attack type.'
    if (!form.attack_intensity) return 'Select an attack intensity.'
    const duration = Number(form.duration_seconds)
    if (!Number.isInteger(duration) || duration < 1 || duration > 3600) {
      return 'Duration must be a whole number of seconds between 1 and 3600.'
    }
    const trials = Number(form.number_of_trials)
    if (!Number.isInteger(trials) || trials < 1 || trials > 20) {
      return 'Number of trials must be a whole number between 1 and 20.'
    }
    if (form.attack_workload.trim()) {
      const workload = Number(form.attack_workload)
      if (Number.isNaN(workload) || workload < 0) {
        return 'Workload must be a number greater than or equal to 0.'
      }
    }
    if (form.carbon_intensity.trim()) {
      const intensity = Number(form.carbon_intensity)
      if (Number.isNaN(intensity) || intensity < 0) {
        return 'Carbon intensity must be a number greater than or equal to 0.'
      }
    }
    return null
  }

  async function runExperiment() {
    const validationError = validate()
    if (validationError) {
      setError(validationError)
      setPhase('error')
      return
    }

    setError(null)
    setCreated(null)
    setSummary(null)

    try {
      setPhase('creating')
      const experiment = await researchApi.createExperiment({
        name:
          form.name.trim() ||
          `${form.attack_type} ${form.attack_intensity} ${form.experiment_type.toLowerCase()}`,
        experiment_type: form.experiment_type as
          | 'MARGINAL_ENERGY'
          | 'INTERACTION'
          | 'DEFENSE_AMPLIFICATION',
        attack_type: form.attack_type,
        attack_intensity: form.attack_intensity,
        attack_workload: form.attack_workload.trim() ? Number(form.attack_workload) : null,
        workload_unit: form.workload_unit.trim() || null,
        duration_seconds: Number(form.duration_seconds),
        security_controls: form.security_controls,
        measurement_provider: form.measurement_provider,
        number_of_trials: Number(form.number_of_trials),
        carbon_intensity: form.carbon_intensity.trim() ? Number(form.carbon_intensity) : null,
      })
      setCreated(experiment)

      setPhase('running')
      await researchApi.executeExperiment(experiment.experiment_uuid)

      setPhase('loading')
      const result = await researchApi.getExperimentSummary(experiment.experiment_uuid)
      setSummary(result)
      setPhase('done')
      onExperimentCreated?.()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'The experiment could not be executed.'
      const suffix = selectedProvider?.available
        ? ''
        : ' The selected measurement provider is not configured on this host, so execution cannot produce an energy reading.'
      setError(`${message}${suffix}`)
      setPhase('error')
      onExperimentCreated?.()
    }
  }

  const stepIndex =
    phase === 'idle' || phase === 'error'
      ? 7
      : phase === 'creating'
        ? 7
        : phase === 'running'
          ? 7
          : phase === 'loading'
            ? 8
            : 9

  const totalEnergy = sumEnergyJoules(summary)
  const carbonKg = calculateCarbonKg(totalEnergy, created?.carbon_intensity ?? null)

  return (
    <Card data-testid="experiment-runner">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <CardTitle>Experiment Runner</CardTitle>
          <p className="text-xs text-muted mt-1">
            Creates and executes an experiment through the Phase 11 research API. The frontend never
            simulates attacks or energy itself — safe synthetic execution happens on the backend.
          </p>
        </div>
        <Badge variant="warning" size="md">
          SAFE SYNTHETIC SIMULATION
        </Badge>
      </div>

      <CardContent className="mt-4 space-y-5">
        <ol className="flex flex-wrap gap-2" aria-label="Experiment wizard steps">
          {STEPS.map((step, index) => {
            const done = phase === 'done' && index <= 9
            const active = index === stepIndex && phase !== 'done'
            return (
              <li
                key={step}
                className={`px-2 py-1 rounded border text-[10px] uppercase tracking-wider ${
                  done
                    ? 'border-success/30 bg-success/10 text-success'
                    : active
                      ? 'border-accent/40 bg-accent/10 text-accent'
                      : 'border-border bg-card text-muted'
                }`}
              >
                {index + 1}. {step}
              </li>
            )
          })}
        </ol>

        {referenceError && <SectionError title="Reference data unavailable" message={referenceError} />}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="space-y-3">
            <label htmlFor="runner-type" className="block text-[10px] uppercase tracking-wider text-muted">
              Experiment type
            </label>
            <select
              id="runner-type"
              className={`${controlClass} w-full`}
              value={form.experiment_type}
              onChange={(event) => update({ experiment_type: event.target.value })}
            >
              {EXPERIMENT_TYPES.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.label}
                </option>
              ))}
            </select>

            <label htmlFor="runner-attack" className="block text-[10px] uppercase tracking-wider text-muted">
              1. Attack
            </label>
            <select
              id="runner-attack"
              className={`${controlClass} w-full`}
              value={form.attack_type}
              onChange={(event) => {
                const next = attacks.find((item) => item.attack_type === event.target.value)
                update({
                  attack_type: event.target.value,
                  attack_intensity: '',
                  workload_unit: next?.workload_unit ?? '',
                })
              }}
            >
              <option value="">Select an attack…</option>
              {attacks.map((item) => (
                <option key={item.attack_type} value={item.attack_type}>
                  {item.display_name}
                </option>
              ))}
            </select>

            <label htmlFor="runner-intensity" className="block text-[10px] uppercase tracking-wider text-muted">
              2. Intensity
            </label>
            <select
              id="runner-intensity"
              className={`${controlClass} w-full`}
              value={form.attack_intensity}
              onChange={(event) => update({ attack_intensity: event.target.value })}
            >
              <option value="">Select an intensity…</option>
              {(attack?.intensity_levels ?? []).map((level) => (
                <option key={level} value={level}>
                  {level}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-3">
            <label htmlFor="runner-workload" className="block text-[10px] uppercase tracking-wider text-muted">
              3. Workload value
            </label>
            <div className="flex gap-2">
              <input
                id="runner-workload"
                type="number"
                min={0}
                className={`${controlClass} w-full`}
                placeholder={attack ? `default ${attack.workload_unit}` : 'optional'}
                value={form.attack_workload}
                onChange={(event) => update({ attack_workload: event.target.value })}
              />
              <input
                aria-label="Workload unit"
                className={`${controlClass} w-28`}
                placeholder={attack?.workload_unit ?? 'unit'}
                value={form.workload_unit}
                onChange={(event) => update({ workload_unit: event.target.value })}
              />
            </div>

            <span className="block text-[10px] uppercase tracking-wider text-muted">
              4. Security controls
            </span>
            <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto border border-border rounded-md p-2 bg-card">
              {controls.length === 0 && (
                <span className="text-xs text-muted">No controls returned by the API.</span>
              )}
              {controls.map((control) => {
                const active = form.security_controls.includes(control.control_id)
                return (
                  <button
                    key={control.control_id}
                    type="button"
                    onClick={() => toggleControl(control.control_id)}
                    className={`px-2 py-1 rounded border text-xs transition-colors ${
                      active
                        ? 'border-accent/50 bg-accent/10 text-accent'
                        : 'border-border bg-card text-muted hover:text-text-primary'
                    }`}
                    aria-pressed={active}
                  >
                    {control.display_name}
                  </button>
                )
              })}
            </div>
          </div>

          <div className="space-y-3">
            <label htmlFor="runner-provider" className="block text-[10px] uppercase tracking-wider text-muted">
              5. Measurement mode
            </label>
            <select
              id="runner-provider"
              className={`${controlClass} w-full`}
              value={form.measurement_provider}
              onChange={(event) => update({ measurement_provider: event.target.value })}
            >
              {MEASUREMENT_PROVIDERS.map((provider) => (
                <option key={provider.id} value={provider.id}>
                  {provider.label}
                  {provider.available ? '' : ' — not configured'}
                </option>
              ))}
            </select>

            {!selectedProvider?.available && (
              <div className="flex items-start gap-2 px-2 py-2 bg-warning/10 border border-warning/20 rounded-md">
                <TriangleAlert className="w-4 h-4 text-warning mt-0.5 flex-shrink-0" />
                <p className="text-[11px] text-warning leading-relaxed">
                  Unavailable measurement mode: no {form.measurement_provider} provider is configured
                  on this host, so execution is expected to fail. Choose Estimated to run.
                </p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label htmlFor="runner-duration" className="block text-[10px] uppercase tracking-wider text-muted">
                  6. Duration (s)
                </label>
                <input
                  id="runner-duration"
                  type="number"
                  min={1}
                  max={3600}
                  className={`${controlClass} w-full mt-1`}
                  value={form.duration_seconds}
                  onChange={(event) => update({ duration_seconds: event.target.value })}
                />
              </div>
              <div>
                <label htmlFor="runner-trials" className="block text-[10px] uppercase tracking-wider text-muted">
                  7. Trials
                </label>
                <input
                  id="runner-trials"
                  type="number"
                  min={1}
                  max={20}
                  className={`${controlClass} w-full mt-1`}
                  value={form.number_of_trials}
                  onChange={(event) => update({ number_of_trials: event.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label htmlFor="runner-carbon" className="block text-[10px] uppercase tracking-wider text-muted">
                  Carbon intensity (gCO₂/kWh)
                </label>
                <input
                  id="runner-carbon"
                  type="number"
                  min={0}
                  className={`${controlClass} w-full mt-1`}
                  placeholder="backend default"
                  value={form.carbon_intensity}
                  onChange={(event) => update({ carbon_intensity: event.target.value })}
                />
              </div>
              <div>
                <label htmlFor="runner-name" className="block text-[10px] uppercase tracking-wider text-muted">
                  Experiment name
                </label>
                <input
                  id="runner-name"
                  type="text"
                  className={`${controlClass} w-full mt-1`}
                  placeholder="auto-generated"
                  value={form.name}
                  onChange={(event) => update({ name: event.target.value })}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={runExperiment} disabled={busy}>
            {busy ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <PlayCircle className="w-4 h-4" />
            )}
            {busy ? 'Running experiment…' : 'Run experiment'}
          </Button>
          <span className="text-[11px] text-muted">
            Step 8 — runs on the backend; results and persistence follow automatically.
          </span>
        </div>

        {busy && (
          <div className="bg-card border border-border rounded-md p-4">
            <SectionLoading
              label={
                phase === 'creating'
                  ? 'Creating experiment record…'
                  : phase === 'running'
                    ? 'Executing synthetic attack trials…'
                    : 'Loading results…'
              }
            />
          </div>
        )}

        {phase === 'error' && error && (
          <div className="bg-danger/10 border border-danger/20 rounded-md p-3">
            <p className="text-xs text-danger font-medium mb-1">Experiment did not complete</p>
            <p className="text-[11px] text-muted leading-relaxed">{error}</p>
          </div>
        )}

        {phase === 'done' && created && summary && (
          <div className="space-y-4" data-testid="runner-results">
            <div className="flex flex-wrap items-center gap-2">
              <Save className="w-4 h-4 text-success" />
              <span className="text-sm font-semibold text-text-primary">
                Step 10 — experiment saved
              </span>
              <Badge variant={statusVariant(created.status)} size="sm">
                {created.status}
              </Badge>
              <Badge variant={modeVariant(created.measurement_mode)} size="sm">
                {created.measurement_mode}
              </Badge>
            </div>

            <div className="bg-background/60 border border-border rounded-md p-4">
              <p className="text-xs font-semibold text-text-primary mb-3">Results</p>
              <FieldGrid>
                <Field label="Experiment ID" value={`#${created.id}`} />
                <Field label="Experiment UUID" value={created.experiment_uuid} />
                <Field label="Attack" value={`${created.attack_type} / ${created.attack_intensity}`} />
                <Field
                  label="Workload"
                  value={
                    summary.runs[0]?.workload_value !== null &&
                    summary.runs[0]?.workload_value !== undefined
                      ? `${formatNumber(summary.runs[0].workload_value, 2)} ${summary.runs[0].workload_unit ?? ''}`
                      : 'Not recorded'
                  }
                />
                <Field label="Security Controls" value={controlsLabel(created.security_controls)} />
                <Field label="Measurement Mode" value={created.measurement_mode} />
                <Field label="Trial Count" value={`${formatInteger(summary.runs.length)} runs`} />
                <Field
                  label="Total Energy"
                  value={totalEnergy !== null ? formatJoules(totalEnergy) : 'Not available'}
                />
                <Field
                  label="Carbon (calculated)"
                  value={carbonKg !== null ? formatKilograms(carbonKg) : 'Not available'}
                />
                <Field
                  label="Carbon Basis"
                  value={
                    created.carbon_intensity !== null
                      ? `energy × ${formatNumber(created.carbon_intensity, 1)} gCO₂/kWh ÷ 1000`
                      : 'No carbon intensity configured'
                  }
                />
                <Field label="Recorded" value={formatDateTime(created.created_at)} />
                <Field
                  label="Status"
                  value={<Badge variant={statusVariant(created.status)}>{created.status}</Badge>}
                />
              </FieldGrid>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border text-muted uppercase tracking-wider">
                    <th className="text-left px-2 py-1.5">Trial</th>
                    <th className="text-left px-2 py-1.5">Run</th>
                    <th className="text-right px-2 py-1.5">Energy</th>
                    <th className="text-right px-2 py-1.5">Power</th>
                    <th className="text-right px-2 py-1.5">Detection</th>
                    <th className="text-left px-2 py-1.5">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.runs.map((run) => {
                    const measurement = summary.measurements.find(
                      (item) => item.run_id === run.id,
                    )
                    const effect = summary.security_effects.find((item) => item.run_id === run.id)
                    return (
                      <tr key={run.id} className="border-b border-border/50">
                        <td className="px-2 py-1.5 text-text-primary">{run.trial_number}</td>
                        <td className="px-2 py-1.5 font-mono text-muted">{run.run_uuid}</td>
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

            <div className="flex flex-wrap items-center gap-3">
              <Link
                to={`/research-lab/experiments/${created.experiment_uuid}`}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-background bg-accent rounded-md hover:bg-accent-light transition-colors"
              >
                <FlaskConical className="w-4 h-4" />
                Open experiment details
              </Link>
              <p className="text-[11px] text-muted">
                Energy is {created.measurement_mode}; carbon is calculated from the configured
                intensity and is never a measurement.
              </p>
            </div>
          </div>
        )}

        {phase === 'idle' && created === null && (
          <p className="text-[11px] text-muted leading-relaxed">
            Configure steps 1–7 above, then run. Validation errors, API errors and unavailable
            measurement modes are reported here rather than silently ignored.
          </p>
        )}
      </CardContent>
    </Card>
  )
}
