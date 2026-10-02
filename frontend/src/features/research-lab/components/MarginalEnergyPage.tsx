import PageHeader from '@/shared/ui/PageHeader'
import Badge from '@/shared/ui/Badge'
import { SectionLoading } from './ResearchBits'
import MarginalEnergySection from './MarginalEnergySection'
import { useResearchLabData } from '../hooks/useResearchLabData'

export default function MarginalEnergyPage() {
  const data = useResearchLabData()

  return (
    <div className="space-y-6" data-testid="marginal-energy-page">
      <PageHeader
        title="Marginal Energy"
        subtitle="Phase 5 attribution: ΔE = E_security − E_baseline for stored run pairs, with attack, workload, control, duration, trial and measurement-mode filters."
        badge={
          <Badge variant="warning" size="sm">
            ESTIMATED UNLESS MEASURED
          </Badge>
        }
      />

      {data.loading ? (
        <SectionLoading label="Loading marginal energy attributions…" />
      ) : (
        <MarginalEnergySection
          items={data.marginal}
          experiments={data.experiments}
          controls={data.controls}
          error={data.errors.marginal}
        />
      )}
    </div>
  )
}
