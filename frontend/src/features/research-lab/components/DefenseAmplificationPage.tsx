import PageHeader from '@/shared/ui/PageHeader'
import Badge from '@/shared/ui/Badge'
import { SectionLoading } from './ResearchBits'
import AmplificationSection from './AmplificationSection'
import { useResearchLabData } from '../hooks/useResearchLabData'

export default function DefenseAmplificationPage() {
  const data = useResearchLabData()

  return (
    <div className="space-y-6" data-testid="defense-amplification-page">
      <PageHeader
        title="Defense Amplification"
        subtitle="Phase 7 defense energy amplification: ADE = E_attack+defense − E_attack+baseline and DEA = ADE / attack workload, compared across the controls the API returns."
        badge={
          <Badge variant="warning" size="sm">
            ADDITIONAL DEFENSE ENERGY
          </Badge>
        }
      />

      {data.loading ? (
        <SectionLoading label="Loading amplification results…" />
      ) : (
        <AmplificationSection
          items={data.amplification}
          experiments={data.experiments}
          controls={data.controls}
          error={data.errors.amplification}
        />
      )}
    </div>
  )
}
