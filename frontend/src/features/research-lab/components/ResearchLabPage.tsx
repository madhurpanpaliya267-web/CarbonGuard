import { FlaskConical, FlaskConicalOff, GitMerge, Layers, Shield, Table2, Zap } from 'lucide-react'
import { Link } from 'react-router-dom'
import PageHeader from '@/shared/ui/PageHeader'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import Badge from '@/shared/ui/Badge'
import { SectionEmpty, SectionError, SectionLoading } from './ResearchBits'
import ResearchOverview from './ResearchOverview'
import CarbonContextSection from './CarbonContextSection'
import StatisticsSection from './StatisticsSection'
import ExperimentTrialsSection from './ExperimentTrialsSection'
import { useResearchLabData } from '../hooks/useResearchLabData'
import type { AttackProfile, SecurityControl } from '../types/research'

interface NavItem {
  to: string
  title: string
  description: string
  icon: typeof FlaskConical
}

const RESEARCH_NAV: NavItem[] = [
  {
    to: '/research-lab/marginal-energy',
    title: 'Marginal Energy',
    description: 'ΔE attribution with workload, control and measurement filters.',
    icon: Zap,
  },
  {
    to: '/research-lab/interaction-analysis',
    title: 'Interaction Analysis',
    description: 'I(A,B) control pair effects with statistics and results table.',
    icon: GitMerge,
  },
  {
    to: '/research-lab/defense-amplification',
    title: 'Defense Amplification',
    description: 'ADE and DEA across controls, workloads and intensities.',
    icon: FlaskConicalOff,
  },
  {
    to: '/research-lab/experiments',
    title: 'Experiments',
    description: 'Run experiments, then browse history and per-trial results.',
    icon: FlaskConical,
  },
  {
    to: '/research-lab/dataset',
    title: 'Research Dataset',
    description: 'Joined result tables with CSV and JSON export.',
    icon: Table2,
  },
  {
    to: '/research-lab/statistics',
    title: 'Statistics',
    description: 'Phase 8 descriptive and inferential analysis stays below.',
    icon: Layers,
  },
]

function ResearchNav() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
      {RESEARCH_NAV.map((item) => {
        const Icon = item.icon
        const isAnchor = item.to === '/research-lab/statistics'
        const content = (
          <>
            <div className="flex items-center gap-2">
              <Icon className="w-4 h-4 text-accent" />
              <span className="text-sm font-semibold text-text-primary">{item.title}</span>
            </div>
            <p className="text-xs text-muted leading-relaxed mt-1">{item.description}</p>
          </>
        )
        return isAnchor ? (
          <a
            key={item.to}
            href="#statistical-analysis"
            className="block bg-card border border-border rounded-md p-3 hover:border-accent/40 transition-colors"
          >
            {content}
          </a>
        ) : (
          <Link
            key={item.to}
            to={item.to}
            className="block bg-card border border-border rounded-md p-3 hover:border-accent/40 transition-colors"
            data-testid={`research-nav-${item.title.toLowerCase().replace(/\s+/g, '-')}`}
          >
            {content}
          </Link>
        )
      })}
    </div>
  )
}

function ReferenceCatalog({
  attacks,
  controls,
}: {
  attacks: AttackProfile[]
  controls: SecurityControl[]
}) {
  if (attacks.length === 0 && controls.length === 0) return null

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardTitle>Synthetic Attack Profiles</CardTitle>
        <CardContent className="mt-3">
          {attacks.length === 0 ? (
            <SectionEmpty
              title="No attack profiles"
              message="The research attack catalogue could not be loaded."
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border text-muted uppercase tracking-wider">
                    <th className="text-left px-2 py-1.5">Attack</th>
                    <th className="text-left px-2 py-1.5">Unit</th>
                    <th className="text-left px-2 py-1.5">Intensities</th>
                    <th className="text-left px-2 py-1.5">Controls</th>
                  </tr>
                </thead>
                <tbody>
                  {attacks.map((attack) => (
                    <tr key={attack.attack_type} className="border-b border-border/50">
                      <td className="px-2 py-1.5 text-text-primary">{attack.display_name}</td>
                      <td className="px-2 py-1.5 text-muted">{attack.workload_unit}</td>
                      <td className="px-2 py-1.5 text-muted">
                        {attack.intensity_levels.join(', ')}
                      </td>
                      <td className="px-2 py-1.5 text-muted">
                        {attack.supported_controls.join(', ')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardTitle>Security Controls</CardTitle>
        <CardContent className="mt-3">
          {controls.length === 0 ? (
            <SectionEmpty
              title="No security controls"
              message="The research control catalogue could not be loaded."
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border text-muted uppercase tracking-wider">
                    <th className="text-left px-2 py-1.5">Control</th>
                    <th className="text-left px-2 py-1.5">Category</th>
                    <th className="text-left px-2 py-1.5">Default</th>
                    <th className="text-left px-2 py-1.5">Attacks</th>
                  </tr>
                </thead>
                <tbody>
                  {controls.map((control) => (
                    <tr key={control.control_id} className="border-b border-border/50">
                      <td className="px-2 py-1.5 text-text-primary">{control.display_name}</td>
                      <td className="px-2 py-1.5 text-muted">{control.category}</td>
                      <td className="px-2 py-1.5">
                        <Badge variant={control.enabled_by_default ? 'success' : 'muted'} size="sm">
                          {control.enabled_by_default ? 'ON' : 'OFF'}
                        </Badge>
                      </td>
                      <td className="px-2 py-1.5 text-muted">
                        {control.supported_attack_types.join(', ') || '—'}
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
  )
}

export default function ResearchLabPage() {
  const data = useResearchLabData()

  if (data.loading) {
    return (
      <div className="space-y-6" data-testid="research-lab-page">
        <PageHeader
          title="Research Lab"
          subtitle="Phase 5–8 research analytics with Phase 10 carbon metrics: marginal energy, control interaction, defense amplification, carbon per workload, and statistics"
          badge={
            <Badge variant="warning" size="sm">
              <span className="inline-block w-1.5 h-1.5 bg-warning rounded-full animate-pulse mr-1" />
              SIMULATED DATA
            </Badge>
          }
          actions={
            <Badge variant="purple" size="md">
              RULE-BASED ANALYTICS
            </Badge>
          }
        />
        <SectionLoading label="Loading research lab…" />
      </div>
    )
  }

  return (
    <div className="space-y-6" data-testid="research-lab-page">
      <PageHeader
        title="Research Lab"
        subtitle="Phase 5–8 research analytics with Phase 10 carbon metrics: marginal energy, control interaction, defense amplification, carbon per workload, and statistics"
        badge={
          <Badge variant="warning" size="sm">
            <span className="inline-block w-1.5 h-1.5 bg-warning rounded-full animate-pulse mr-1" />
            SIMULATED DATA
          </Badge>
        }
        actions={
          <Badge variant="purple" size="md">
            RULE-BASED ANALYTICS
          </Badge>
        }
      />

      <ResearchNav />

      <ResearchOverview data={data} />

      <section aria-label="Carbon context">
        <CarbonContextSection />
      </section>

      <section aria-label="Statistical analysis" id="statistical-analysis">
        <StatisticsSection />
      </section>

      <section aria-label="Experiment trials">
        <ExperimentTrialsSection
          experiments={data.experiments}
          marginal={data.marginal}
          interaction={data.interaction}
          amplification={data.amplification}
        />
      </section>

      {data.errors.experiments && (
        <Card>
          <SectionError
            title="Experiment catalogue unavailable"
            message={data.errors.experiments}
          />
        </Card>
      )}

      <section aria-label="Research reference data">
        <ReferenceCatalog attacks={data.attacks} controls={data.controls} />
      </section>

      <Card>
        <div className="flex items-start gap-3 p-2">
          <FlaskConical className="w-4 h-4 text-accent mt-0.5" />
          <div className="space-y-1">
            <p className="text-xs text-muted leading-relaxed">
              All research data shown here is persisted by the CarbonGuard research engine. Energy
              is ESTIMATED unless a measurement provider reports MEASURED mode. Attack profiles are
              safe synthetic simulations — no real systems are scanned or attacked.
            </p>
            <p className="text-xs text-muted leading-relaxed flex flex-wrap items-center gap-2">
              <Shield className="w-3 h-3 inline" />
              Security workloads are never delayed or degraded for carbon optimization.
              <Zap className="w-3 h-3 inline" />
              This page performs read-only queries plus explicit statistical analysis requests; it
              never writes experiment data.
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}
