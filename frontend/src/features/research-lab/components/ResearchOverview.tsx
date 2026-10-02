import { Battery, FlaskConical, Layers, Leaf, ShieldCheck, Clock } from 'lucide-react'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import Badge from '@/shared/ui/Badge'
import MetricCard from '@/shared/ui/MetricCard'
import { formatDateTime } from '@/shared/utils/formatters'
import { SectionError, SectionLoading } from './ResearchBits'
import type { ResearchLabData } from '../hooks/useResearchLabData'

function latestTimestamp(data: ResearchLabData): string | null {
  const stamps = [
    ...data.experiments.map((e) => e.created_at),
    ...data.marginal.map((m) => m.created_at),
    ...data.interaction.map((i) => i.created_at),
    ...data.amplification.map((a) => a.created_at),
  ].filter(Boolean)

  if (stamps.length === 0) return null
  return stamps.reduce((a, b) => (new Date(a).getTime() >= new Date(b).getTime() ? a : b))
}

function currentMeasurementMode(data: ResearchLabData): string {
  if (data.experiments.length === 0) return '—'
  const sorted = [...data.experiments].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  )
  return sorted[0].measurement_mode
}

export default function ResearchOverview({ data }: { data: ResearchLabData }) {
  if (data.loading) return <SectionLoading label="Loading research overview…" />

  const totalTrials = data.experiments.reduce((sum, e) => sum + (e.num_trials || 0), 0)
  const lastUpdated = latestTimestamp(data)
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
              Persisted experiment results from Phases 5–8 of the CarbonGuard research engine.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge variant="warning" size="md">
              ESTIMATED ENERGY
            </Badge>
            <Badge variant="purple" size="md">
              SYNTHETIC ATTACK PROFILES
            </Badge>
          </div>
        </div>

        <CardContent className="mt-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
            <MetricCard
              title="Total Experiments"
              value={data.experiments.length}
              icon={FlaskConical}
              color="primary"
              subtitle="Persisted research experiments"
            />
            <MetricCard
              title="Total Trials"
              value={totalTrials}
              icon={Layers}
              color="primary"
              subtitle="Configured trials across experiments"
            />
            <MetricCard
              title="Measurement Mode"
              value={currentMeasurementMode(data)}
              icon={Battery}
              color="warning"
              subtitle="Mode recorded on the latest experiment"
            />
            <MetricCard
              title="Attack Profiles"
              value={data.attacks.length}
              icon={ShieldCheck}
              color="purple"
              subtitle="Safe synthetic profiles"
            />
            <MetricCard
              title="Security Controls"
              value={data.controls.length}
              icon={Leaf}
              color="success"
              subtitle="Configurable defense controls"
            />
            <MetricCard
              title="Last Updated"
              value={lastUpdated ? formatDateTime(lastUpdated) : '—'}
              icon={Clock}
              color="primary"
              subtitle="Most recent persisted research record"
            />
          </div>

          <div className="mt-4 px-3 py-2 bg-warning/10 border border-warning/20 rounded-md">
            <p className="text-xs text-warning leading-relaxed">
              Energy values shown in this lab are <strong>ESTIMATED</strong> by a deterministic
              estimation model unless a hardware measurement provider is configured. They are not
              hardware measurements. Attack workloads come from safe synthetic simulation; no real
              attacks are executed.
            </p>
          </div>

          {failedSources.length > 0 && (
            <div className="mt-3">
              <SectionError
                title="Some research sources could not be loaded"
                message={failedSources
                  .map(([source, error]) => `${source}: ${error}`)
                  .join(' · ')}
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
