import PageHeader from '@/shared/ui/PageHeader'
import Badge from '@/shared/ui/Badge'
import { SectionLoading } from './ResearchBits'
import InteractionSection from './InteractionSection'
import { useResearchLabData } from '../hooks/useResearchLabData'

export default function InteractionAnalysisPage() {
  const data = useResearchLabData()

  return (
    <div className="space-y-6" data-testid="interaction-analysis-page">
      <PageHeader
        title="Interaction Analysis"
        subtitle="Phase 6 control interaction: I(A,B) = E_AB − E_A − E_B + E_0, with backend-provided classification and Phase 8 descriptive statistics."
        badge={
          <Badge variant="purple" size="sm">
            PHASE 6 RESEARCH
          </Badge>
        }
      />

      {data.loading ? (
        <SectionLoading label="Loading interaction results…" />
      ) : (
        <InteractionSection
          items={data.interaction}
          experiments={data.experiments}
          error={data.errors.interaction}
        />
      )}
    </div>
  )
}
