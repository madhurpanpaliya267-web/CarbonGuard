import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Database } from 'lucide-react'
import PageHeader from '@/shared/ui/PageHeader'
import Badge from '@/shared/ui/Badge'
import ExperimentRunner from './ExperimentRunner'
import ExperimentHistory from './ExperimentHistory'
import { SectionLoading } from './ResearchBits'
import { useResearchLabData } from '../hooks/useResearchLabData'

export default function ExperimentsPage() {
  const [refreshKey, setRefreshKey] = useState(0)
  const data = useResearchLabData(refreshKey)

  return (
    <div className="space-y-6" data-testid="experiments-page">
      <PageHeader
        title="Experiments"
        subtitle="Run controlled synthetic attack experiments, then browse every stored experiment with its measured or estimated trial energy."
        badge={
          <Badge variant="warning" size="sm">
            SAFE SYNTHETIC SIMULATION
          </Badge>
        }
        actions={
          <Link
            to="/research-lab"
            className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-muted border border-border rounded-md hover:text-text-primary hover:border-accent/40 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Research overview
          </Link>
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        <Link
          to="/research-lab/dataset"
          className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-muted border border-border rounded-md hover:text-text-primary hover:border-accent/40 transition-colors"
        >
          <Database className="w-3.5 h-3.5" />
          Research dataset & export
        </Link>
      </div>

      {data.loading ? (
        <SectionLoading label="Loading research references…" />
      ) : (
        <>
          <ExperimentRunner
            attacks={data.attacks}
            controls={data.controls}
            referenceError={data.errors.attacks ?? data.errors.controls}
            onExperimentCreated={() => setRefreshKey((key) => key + 1)}
          />
          <ExperimentHistory
            experiments={data.experiments}
            loading={false}
            error={data.errors.experiments}
          />
        </>
      )}
    </div>
  )
}
