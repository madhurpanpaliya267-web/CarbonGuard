import { useState, type ReactNode } from 'react'
import {
  Shield,
  Play,
  AlertTriangle,
  Activity,
  Zap,
  Leaf,
  Target,
  CheckCircle,
  Loader2,
  Lock,
  Eye,
  Bug,
  ArrowRight,
  Sliders,
  FlaskConical,
} from 'lucide-react'
import PageHeader from '@/shared/ui/PageHeader'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import Badge, { SeverityBadge } from '@/shared/ui/Badge'
import { api } from '@/shared/utils/api'
import type { OrchestrationResult } from '@/shared/types/common'

const attackTypes = [
  { id: 'ddos', name: 'DDoS', description: 'Distributed Denial of Service', severity: 'HIGH' as const, icon: Activity, color: 'danger' },
  { id: 'brute_force', name: 'Brute Force', description: 'Brute force login attempt', severity: 'MEDIUM' as const, icon: Lock, color: 'warning' },
  { id: 'port_scan', name: 'Port Scan', description: 'Network port scanning', severity: 'LOW' as const, icon: Eye, color: 'success' },
  { id: 'sql_injection', name: 'SQL Injection', description: 'SQL injection attempt', severity: 'HIGH' as const, icon: Bug, color: 'purple' },
  { id: 'malware', name: 'Malware', description: 'Malware detection', severity: 'CRITICAL' as const, icon: Shield, color: 'danger' },
  { id: 'suspicious_login', name: 'Suspicious Login', description: 'Suspicious login activity', severity: 'MEDIUM' as const, icon: AlertTriangle, color: 'warning' },
]

function MeasurementBadge({ mode }: { mode: string | null }) {
  if (mode === 'MEASURED') return <Badge variant="success" size="sm">MEASURED</Badge>
  if (mode === 'SIMULATED') return <Badge variant="warning" size="sm">SIMULATED</Badge>
  if (mode === 'ESTIMATED') return <Badge variant="muted" size="sm">ESTIMATED</Badge>
  return <Badge variant="warning" size="sm">UNAVAILABLE</Badge>
}

function MetricRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex justify-between items-start gap-3 p-2 bg-background rounded-md border border-border/50">
      <span className="text-xs text-muted">{label}</span>
      <span className="text-xs text-text-primary font-medium text-right">{value}</span>
    </div>
  )
}

const unavailable = (reason?: string | null) => (
  <span className="text-warning">Not available{reason ? ` — ${reason}` : ''}</span>
)

export default function AttackSimulatorPage() {
  const [simulating, setSimulating] = useState<string | null>(null)
  const [result, setResult] = useState<OrchestrationResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleSimulate(attackType: string) {
    setSimulating(attackType)
    setResult(null)
    setError(null)
    try {
      const res = await api.runPipeline(attackType)
      setResult(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Pipeline run failed')
    } finally {
      setSimulating(null)
    }
  }

  const flowNodes = result
    ? [
        { label: 'ATTACK', value: result.attack.attack_type.replace('_', ' ') },
        { label: 'THREAT', value: result.threat.severity },
        {
          label: 'DEFENSE',
          value:
            result.security_controls.length > 0
              ? `${result.security_controls.length} controls`
              : 'none',
        },
        {
          label: 'ENERGY',
          value:
            result.energy.status === 'completed' && result.energy.energy_kwh !== null
              ? `${result.energy.energy_kwh.toFixed(6)} kWh`
              : 'Not available',
        },
        {
          label: 'CARBON',
          value:
            result.carbon.status === 'completed' && result.carbon.net_co2_kg !== null
              ? `${result.carbon.net_co2_kg.toFixed(6)} kg`
              : 'Not available',
        },
        { label: 'RESULT', value: result.status },
      ]
    : []

  return (
    <div className="space-y-5">
      <PageHeader
        title="Attack Simulator"
        subtitle="End-to-end CarbonGuard pipeline: attack, threat, defense, energy, carbon"
        badge={
          <Badge variant="warning" size="sm">
            <span className="inline-block w-1.5 h-1.5 bg-warning rounded-full animate-pulse mr-1" />
            SIMULATION ONLY
          </Badge>
        }
      />

      <Card>
        <div className="flex items-center gap-3">
          <Badge variant="warning" size="sm">
            <span className="inline-block w-1.5 h-1.5 bg-warning rounded-full animate-pulse mr-1" />
            EDUCATIONAL PURPOSE ONLY
          </Badge>
        </div>
        <p className="text-sm text-muted mt-2">
          Simulate cyber attacks on synthetic data to observe the full CarbonGuard
          pipeline: detection, classification, rule-based defense response, energy
          measurement and carbon calculation. All simulations operate on internal
          synthetic data only. No real systems are scanned or attacked.
        </p>
      </Card>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {attackTypes.map((attack) => (
          <div
            key={attack.id}
            className={`p-4 bg-card border border-border rounded-md hover:border-accent/40 transition-all cursor-pointer group ${
              simulating === attack.id ? 'ring-2 ring-accent/40 border-accent/40' : ''
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <attack.icon className={`w-4 h-4 text-muted group-hover:text-accent transition-colors`} />
                <span className="text-sm font-medium text-text-primary">{attack.name}</span>
              </div>
              <SeverityBadge severity={attack.severity} />
            </div>
            <p className="text-xs text-muted mb-3">{attack.description}</p>
            <button
              onClick={() => handleSimulate(attack.id)}
              disabled={simulating !== null}
              className="w-full flex items-center justify-center gap-2 py-2 bg-accent/10 text-accent text-xs font-medium rounded-md hover:bg-accent/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed border border-accent/20"
            >
              {simulating === attack.id ? (
                <>
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Running Pipeline...
                </>
              ) : (
                <>
                  <Play className="w-3 h-3" />
                  Simulate
                </>
              )}
            </button>
          </div>
        ))}
      </div>

      {error && (
        <Card>
          <div className="flex items-center gap-3 text-danger">
            <AlertTriangle className="w-5 h-5" />
            <div>
              <p className="text-sm font-medium">Pipeline Run Failed</p>
              <p className="text-xs text-muted">{error}</p>
            </div>
          </div>
        </Card>
      )}

      {result && (
        <div className="space-y-5">
          <Card>
            <div className="flex items-center gap-2 mb-4">
              <Activity className="w-5 h-5 text-accent" />
              <CardTitle>Pipeline Flow</CardTitle>
              <Badge variant="warning" size="sm">SYNTHETIC</Badge>
              <Badge variant="muted" size="sm">{result.provenance.pipeline_version}</Badge>
            </div>
            <CardContent>
              <div className="flex flex-wrap items-center gap-2">
                {flowNodes.map((node, i) => (
                  <div key={node.label} className="flex items-center gap-2">
                    <div className="px-3 py-2 bg-background border border-border/60 rounded-md min-w-[96px]">
                      <p className="text-[10px] text-muted uppercase tracking-wider">{node.label}</p>
                      <p className="text-xs text-text-primary font-medium capitalize">{node.value}</p>
                    </div>
                    {i < flowNodes.length - 1 && <ArrowRight className="w-3.5 h-3.5 text-accent" />}
                  </div>
                ))}
              </div>
              <p className="text-[10px] text-muted mt-3">
                {result.provenance.notes}
              </p>
            </CardContent>
          </Card>

          <Card>
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle className="w-5 h-5 text-accent" />
              <CardTitle>Result Summary</CardTitle>
              <Badge variant={result.status === 'completed' ? 'success' : 'warning'} size="sm">
                {result.status.toUpperCase()}
              </Badge>
            </div>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <MetricRow
                  label="Attack Type"
                  value={<span className="capitalize">{result.attack.attack_type.replace('_', ' ')}</span>}
                />
                <MetricRow label="Threat Level" value={<SeverityBadge severity={result.threat.severity} />} />
                <MetricRow
                  label="Risk"
                  value={`${result.risk.risk_score}/100 (${result.risk.severity})`}
                />
                <MetricRow
                  label="Security Response"
                  value={result.defense.response}
                />
                <MetricRow
                  label="Controls Activated"
                  value={
                    result.security_controls.length > 0 ? (
                      <span className="flex flex-wrap justify-end gap-1">
                        {result.security_controls.map((c) => (
                          <Badge key={c} variant="primary" size="sm">{c}</Badge>
                        ))}
                      </span>
                    ) : (
                      <span className="text-warning">None</span>
                    )
                  }
                />
                <MetricRow
                  label="Energy Impact"
                  value={
                    result.energy.status === 'completed' && result.energy.energy_kwh !== null
                      ? `${result.energy.energy_kwh.toFixed(6)} kWh`
                      : unavailable(result.energy.reason)
                  }
                />
                <MetricRow
                  label="Carbon Impact"
                  value={
                    result.carbon.status === 'completed' && result.carbon.net_co2_kg !== null
                      ? `${result.carbon.net_co2_kg.toFixed(6)} kg CO2 (net)`
                      : unavailable(result.carbon.reason)
                  }
                />
                <MetricRow
                  label="Measurement Mode"
                  value={
                    <span className="flex items-center justify-end gap-2">
                      <MeasurementBadge mode={result.energy.measurement_mode} />
                      <span>{result.energy.measurement_mode ?? 'unavailable'}</span>
                    </span>
                  }
                />
                <MetricRow
                  label="Carbon Basis"
                  value={
                    result.carbon.carbon_basis ?? (
                      <span className="text-warning">Not available</span>
                    )
                  }
                />
                <MetricRow
                  label="Research Experiment / Run"
                  value={
                    result.research.status === 'recorded' ? (
                      <span className="font-mono">
                        run #{result.research.run_id} (trial {result.research.trial_number})
                      </span>
                    ) : (
                      <span className="text-warning">
                        Not available
                        {result.research.reason ? ` — ${result.research.reason}` : ''}
                      </span>
                    )
                  }
                />
              </div>
            </CardContent>
          </Card>

          {result.warnings.length > 0 && (
            <Card>
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="w-5 h-5 text-warning" />
                <CardTitle>Pipeline Warnings</CardTitle>
              </div>
              <CardContent>
                <div className="space-y-2">
                  {result.warnings.map((w, i) => (
                    <div key={i} className="flex items-start gap-3 p-2 bg-background rounded-md border border-border/50">
                      <Badge variant="warning" size="sm">{w.stage}</Badge>
                      <p className="text-xs text-muted flex-1">{w.reason}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <Card>
              <div className="flex items-center gap-2 mb-4">
                <Shield className="w-5 h-5 text-accent" />
                <CardTitle>Event Details</CardTitle>
              </div>
              <CardContent>
                <div className="bg-background rounded-md p-4 space-y-3 border border-border/50">
                  <div className="flex justify-between">
                    <span className="text-xs text-muted">Event UUID</span>
                    <span className="text-xs text-text-primary font-mono">{result.event.event_uuid}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-muted">Attack Type</span>
                    <span className="text-xs text-text-primary capitalize">{result.event.event_type.replace('_', ' ')}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-muted">Severity</span>
                    <SeverityBadge severity={result.event.severity} />
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-muted">Confidence</span>
                    <span className="text-xs text-text-primary">{(result.event.confidence * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-muted">Source IP</span>
                    <span className="text-xs text-text-primary font-mono">{result.event.source_ip}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-muted">Target IP</span>
                    <span className="text-xs text-text-primary font-mono">{result.event.target_ip}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-muted">Detection Method</span>
                    <span className="text-xs text-text-primary">{result.event.detection_method}</span>
                  </div>
                  <div className="pt-2 border-t border-border">
                    <p className="text-xs text-muted">{result.event.description}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <div className="flex items-center gap-2 mb-4">
                <Target className="w-5 h-5 text-warning" />
                <CardTitle>Risk Assessment</CardTitle>
              </div>
              <CardContent>
                <div className="bg-background rounded-md p-4 space-y-3 border border-border/50">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-muted">Risk Score</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-border rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-accent rounded-full h-2 transition-all"
                          style={{ width: `${result.risk.risk_score}%` }}
                        />
                      </div>
                      <span className="text-xs text-text-primary font-medium">{result.risk.risk_score}/100</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-muted">Overall Severity</span>
                    <SeverityBadge severity={result.risk.severity} />
                  </div>
                  {result.risk.factors.map((f, i) => (
                    <div key={i} className="flex justify-between">
                      <span className="text-xs text-muted">{f.factor}</span>
                      <span className="text-xs text-text-primary">
                        {typeof f.value === 'number' ? (f.value as number).toFixed(2) : String(f.value)}
                        <span className="text-muted ml-1">({(f.weight * 100).toFixed(0)}%)</span>
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <div className="flex items-center gap-2 mb-4">
              <Sliders className="w-5 h-5 text-accent" />
              <CardTitle>Adaptive Security Response</CardTitle>
              <Badge variant="primary" size="sm">{result.defense.tier}</Badge>
              <Badge variant="muted" size="sm">{result.defense.basis.replace('_', ' ').toUpperCase()}</Badge>
            </div>
            <CardContent>
              <p className="text-sm text-text-primary mb-1">{result.defense.response}</p>
              <p className="text-xs text-muted mb-3">{result.defense.reason}</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {result.defense.control_details.length > 0 ? (
                  result.defense.control_details.map((ctrl) => (
                    <div key={ctrl.control_id} className="p-2 bg-background rounded-md border border-border/50">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-text-primary">{ctrl.display_name}</span>
                        <Badge variant="muted" size="sm">{ctrl.category}</Badge>
                      </div>
                      <p className="text-[10px] text-muted mt-1">{ctrl.description}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-warning">No registered control matches this attack type.</p>
                )}
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <Card>
              <div className="flex items-center gap-2 mb-4">
                <Zap className="w-5 h-5 text-warning" />
                <CardTitle>Energy Impact</CardTitle>
                <MeasurementBadge mode={result.energy.measurement_mode} />
              </div>
              <CardContent>
                {result.energy.status === 'completed' ? (
                  <div className="space-y-3">
                    <MetricRow
                      label="Defense Energy"
                      value={`${result.energy.energy_kwh?.toFixed(6)} kWh`}
                    />
                    <MetricRow label="Power Draw" value={`${result.energy.power_watts?.toFixed(1)} W`} />
                    <MetricRow label="Duration" value={`${result.energy.duration_seconds}s`} />
                    <MetricRow label="Controls Active" value={String(result.energy.security_controls_active)} />
                    <MetricRow label="CPU Workload" value={`${result.attack.workload.cpu_seconds}s`} />
                    <MetricRow label="Memory" value={`${result.attack.workload.memory_mb.toFixed(0)} MB`} />
                    <p className="text-[10px] text-muted">
                      Source: {result.energy.measurement_source} · mode: {result.energy.measurement_mode}
                    </p>
                  </div>
                ) : (
                  <p className="text-xs text-warning">{unavailable(result.energy.reason)}</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <div className="flex items-center gap-2 mb-4">
                <Leaf className="w-5 h-5 text-accent-light" />
                <CardTitle>Carbon Impact</CardTitle>
                {result.carbon.carbon_basis && (
                  <Badge variant="muted" size="sm">{result.carbon.carbon_basis}</Badge>
                )}
              </div>
              <CardContent>
                {result.carbon.status === 'completed' ? (
                  <div className="space-y-3">
                    <MetricRow label="Gross CO2" value={`${result.carbon.gross_co2_kg?.toFixed(6)} kg`} />
                    <MetricRow
                      label="Carbon Intensity"
                      value={`${result.carbon.carbon_intensity} gCO2/kWh`}
                    />
                    <MetricRow
                      label="Renewable Offset"
                      value={`-${result.carbon.renewable_offset_kg?.toFixed(6)} kg`}
                    />
                    <MetricRow
                      label="Net CO2"
                      value={<span className="text-accent font-bold">{result.carbon.net_co2_kg?.toFixed(6)} kg</span>}
                    />
                    <p className="text-[10px] text-muted">{result.carbon.calculation_breakdown}</p>
                  </div>
                ) : (
                  <p className="text-xs text-warning">{unavailable(result.carbon.reason)}</p>
                )}
              </CardContent>
            </Card>
          </div>

          <Card>
            <div className="flex items-center gap-2 mb-4">
              <Leaf className="w-5 h-5 text-accent" />
              <CardTitle>Baseline vs Defense Comparison</CardTitle>
              {result.comparison.status === 'available' && (
                <Badge variant="muted" size="sm">
                  {(result.comparison.measurement_mode ?? 'UNKNOWN').toUpperCase()} PAIR
                </Badge>
              )}
            </div>
            <CardContent>
              {result.comparison.status === 'available' ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <MetricRow
                    label="Baseline Energy (no controls)"
                    value={`${result.comparison.baseline_energy_kwh?.toFixed(6)} kWh`}
                  />
                  <MetricRow
                    label="Defense Energy"
                    value={`${result.comparison.defense_energy_kwh?.toFixed(6)} kWh`}
                  />
                  <MetricRow
                    label={
                      result.comparison.direction === 'energy_saved'
                        ? 'Energy Saved'
                        : 'Energy Difference'
                    }
                    value={`${result.comparison.energy_difference_kwh?.toFixed(6)} kWh`}
                  />
                  <MetricRow
                    label="Baseline Carbon"
                    value={`${result.comparison.baseline_carbon_kg?.toFixed(6)} kg`}
                  />
                  <MetricRow
                    label="Defense Carbon"
                    value={`${result.comparison.defense_carbon_kg?.toFixed(6)} kg`}
                  />
                  <MetricRow
                    label={
                      result.comparison.direction === 'energy_saved'
                        ? 'Carbon Saved'
                        : 'Carbon Difference'
                    }
                    value={`${result.comparison.carbon_difference_kg?.toFixed(6)} kg`}
                  />
                  <div className="md:col-span-2">
                    <p className="text-[10px] text-muted">
                      {result.comparison.interpretation} · paired same-provider
                      comparison ({result.comparison.basis}), not a hardware measurement.
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-warning">{unavailable(result.comparison.reason)}</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <div className="flex items-center gap-2 mb-4">
              <Activity className="w-5 h-5 text-accent" />
              <CardTitle>Rule-Based Recommendation</CardTitle>
              <Badge variant="primary" size="sm">{result.defense.recommendation.priority.toUpperCase()}</Badge>
            </div>
            <CardContent>
              <p className="text-sm text-text-primary mb-2">{result.defense.recommendation.recommendation}</p>
              <p className="text-xs text-muted mb-3">{result.defense.recommendation.reason}</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-2 bg-background rounded-md border border-border/50">
                  <p className="text-[10px] text-muted uppercase tracking-wider mb-1">Security Impact</p>
                  <p className="text-xs text-text-primary">{result.defense.recommendation.expected_security_impact}</p>
                </div>
                <div className="p-2 bg-background rounded-md border border-border/50">
                  <p className="text-[10px] text-muted uppercase tracking-wider mb-1">Carbon Impact</p>
                  <p className="text-xs text-text-primary">{result.defense.recommendation.expected_carbon_impact}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle className="w-5 h-5 text-accent" />
              <CardTitle>Detection Pipeline</CardTitle>
            </div>
            <CardContent>
              <div className="space-y-2">
                {result.stages.map((step, i) => (
                  <div key={i} className="flex items-center gap-3 p-2 bg-background rounded-md border border-border/50">
                    <div className="w-6 h-6 rounded-full bg-accent/15 border border-accent/25 flex items-center justify-center flex-shrink-0">
                      <span className="text-[10px] text-accent font-bold">{i + 1}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-text-primary">{step.step}</span>
                        <Badge
                          variant={
                            step.status === 'completed'
                              ? 'success'
                              : step.status === 'failed'
                                ? 'warning'
                                : 'muted'
                          }
                          size="sm"
                        >
                          {step.status}
                        </Badge>
                      </div>
                      <p className="text-[10px] text-muted truncate">{step.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <div className="flex items-center gap-2 mb-2">
              <FlaskConical className="w-4 h-4 text-muted" />
              <span className="text-xs font-medium text-text-primary">Research &amp; Analytics</span>
            </div>
            <p className="text-[10px] text-muted">
              {result.analytics.detail}
            </p>
          </Card>
        </div>
      )}
    </div>
  )
}
