import { useState } from 'react'
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
} from 'lucide-react'
import PageHeader from '@/shared/ui/PageHeader'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import Badge, { SeverityBadge } from '@/shared/ui/Badge'
import { api } from '@/shared/utils/api'
import type { SimulationResult } from '@/shared/types/common'

const attackTypes = [
  { id: 'ddos', name: 'DDoS', description: 'Distributed Denial of Service', severity: 'HIGH' as const, icon: Activity, color: 'danger' },
  { id: 'brute_force', name: 'Brute Force', description: 'Brute force login attempt', severity: 'MEDIUM' as const, icon: Lock, color: 'warning' },
  { id: 'port_scan', name: 'Port Scan', description: 'Network port scanning', severity: 'LOW' as const, icon: Eye, color: 'success' },
  { id: 'sql_injection', name: 'SQL Injection', description: 'SQL injection attempt', severity: 'HIGH' as const, icon: Bug, color: 'purple' },
  { id: 'malware', name: 'Malware', description: 'Malware detection', severity: 'CRITICAL' as const, icon: Shield, color: 'danger' },
  { id: 'suspicious_login', name: 'Suspicious Login', description: 'Suspicious login activity', severity: 'MEDIUM' as const, icon: AlertTriangle, color: 'warning' },
]

export default function AttackSimulatorPage() {
  const [simulating, setSimulating] = useState<string | null>(null)
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleSimulate(attackType: string) {
    setSimulating(attackType)
    setResult(null)
    setError(null)
    try {
      const res = await api.simulateAttack(attackType)
      setResult(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Simulation failed')
    } finally {
      setSimulating(null)
    }
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Attack Simulator"
        subtitle="Educational demonstration of cyber threat simulation"
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
          Simulate cyber attacks on synthetic data to observe the detection, classification,
          and response pipeline. All simulations operate on internal synthetic data only.
          No real systems are scanned or attacked.
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
                  Simulating...
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
              <p className="text-sm font-medium">Simulation Failed</p>
              <p className="text-xs text-muted">{error}</p>
            </div>
          </div>
        </Card>
      )}

      {result && (
        <div className="space-y-5">
          <Card>
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle className="w-5 h-5 text-accent" />
              <CardTitle>Simulation Result</CardTitle>
              <Badge variant="warning" size="sm">SIMULATED</Badge>
            </div>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="text-sm font-semibold text-text-primary flex items-center gap-2">
                    <Shield className="w-4 h-4 text-accent" />
                    Event Details
                  </h4>
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
                </div>

                <div className="space-y-4">
                  <h4 className="text-sm font-semibold text-text-primary flex items-center gap-2">
                    <Target className="w-4 h-4 text-warning" />
                    Risk Assessment
                  </h4>
                  <div className="bg-background rounded-md p-4 space-y-3 border border-border/50">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-muted">Risk Score</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-border rounded-full h-2 overflow-hidden">
                          <div
                            className="bg-accent rounded-full h-2 transition-all"
                            style={{ width: `${result.risk_assessment.risk_score}%` }}
                          />
                        </div>
                        <span className="text-xs text-text-primary font-medium">{result.risk_assessment.risk_score}/100</span>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-muted">Overall Severity</span>
                      <SeverityBadge severity={result.risk_assessment.severity} />
                    </div>
                    {result.risk_assessment.factors.map((f, i) => (
                      <div key={i} className="flex justify-between">
                        <span className="text-xs text-muted">{f.factor}</span>
                        <span className="text-xs text-text-primary">
                          {typeof f.value === 'number' ? (f.value as number).toFixed(2) : String(f.value)}
                          <span className="text-muted ml-1">({(f.weight * 100).toFixed(0)}%)</span>
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <Card>
              <div className="flex items-center gap-2 mb-4">
                <Zap className="w-5 h-5 text-warning" />
                <CardTitle>Energy Impact</CardTitle>
                <Badge variant="muted" size="sm">ESTIMATED</Badge>
              </div>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between p-2 bg-background rounded-md border border-border/50">
                    <span className="text-xs text-muted">Energy Consumed</span>
                    <span className="text-sm text-text-primary font-medium">{result.energy_impact.energy_kwh.toFixed(6)} kWh</span>
                  </div>
                  <div className="flex justify-between p-2 bg-background rounded-md border border-border/50">
                    <span className="text-xs text-muted">Power Draw</span>
                    <span className="text-sm text-text-primary font-medium">{result.energy_impact.power_watts.toFixed(1)} W</span>
                  </div>
                  <div className="flex justify-between p-2 bg-background rounded-md border border-border/50">
                    <span className="text-xs text-muted">CPU Workload</span>
                    <span className="text-sm text-text-primary font-medium">{result.workload_impact.cpu_seconds}s</span>
                  </div>
                  <div className="flex justify-between p-2 bg-background rounded-md border border-border/50">
                    <span className="text-xs text-muted">Memory</span>
                    <span className="text-sm text-text-primary font-medium">{result.workload_impact.memory_mb.toFixed(0)} MB</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <div className="flex items-center gap-2 mb-4">
                <Leaf className="w-5 h-5 text-accent-light" />
                <CardTitle>Carbon Impact</CardTitle>
                <Badge variant="muted" size="sm">ESTIMATED</Badge>
              </div>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between p-2 bg-background rounded-md border border-border/50">
                    <span className="text-xs text-muted">Gross CO2</span>
                    <span className="text-sm text-text-primary font-medium">{result.carbon_impact.co2_kg.toFixed(6)} kg</span>
                  </div>
                  <div className="flex justify-between p-2 bg-background rounded-md border border-border/50">
                    <span className="text-xs text-muted">Carbon Intensity</span>
                    <span className="text-sm text-text-primary font-medium">{result.carbon_impact.carbon_intensity} gCO2/kWh</span>
                  </div>
                  <div className="flex justify-between p-2 bg-background rounded-md border border-border/50">
                    <span className="text-xs text-muted">Renewable Offset</span>
                    <span className="text-sm text-accent font-medium">-{result.carbon_impact.renewable_offset_kg.toFixed(6)} kg</span>
                  </div>
                  <div className="flex justify-between p-2 bg-background rounded-md border border-accent/30">
                    <span className="text-xs text-muted font-medium">Net CO2</span>
                    <span className="text-sm text-accent font-bold">{result.carbon_impact.net_co2_kg.toFixed(6)} kg</span>
                  </div>
                  <p className="text-[10px] text-muted mt-2">{result.carbon_impact.calculation_breakdown}</p>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <div className="flex items-center gap-2 mb-4">
              <Activity className="w-5 h-5 text-accent" />
              <CardTitle>Rule-Based Recommendation</CardTitle>
              <Badge variant="primary" size="sm">{result.ai_recommendation.priority.toUpperCase()}</Badge>
            </div>
            <CardContent>
              <p className="text-sm text-text-primary mb-2">{result.ai_recommendation.recommendation}</p>
              <p className="text-xs text-muted mb-3">{result.ai_recommendation.reason}</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-2 bg-background rounded-md border border-border/50">
                  <p className="text-[10px] text-muted uppercase tracking-wider mb-1">Security Impact</p>
                  <p className="text-xs text-text-primary">{result.ai_recommendation.expected_security_impact}</p>
                </div>
                <div className="p-2 bg-background rounded-md border border-border/50">
                  <p className="text-[10px] text-muted uppercase tracking-wider mb-1">Carbon Impact</p>
                  <p className="text-xs text-text-primary">{result.ai_recommendation.expected_carbon_impact}</p>
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
                {result.pipeline.map((step, i) => (
                  <div key={i} className="flex items-center gap-3 p-2 bg-background rounded-md border border-border/50">
                    <div className="w-6 h-6 rounded-full bg-accent/15 border border-accent/25 flex items-center justify-center flex-shrink-0">
                      <span className="text-[10px] text-accent font-bold">{i + 1}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-text-primary">{step.step}</span>
                        <Badge variant="success" size="sm">{step.status}</Badge>
                      </div>
                      <p className="text-[10px] text-muted truncate">{step.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
