import { AlertTriangle, Leaf, Zap, Brain } from 'lucide-react'
import Badge from '@/shared/ui/Badge'
import type { AiRecommendation } from '@/shared/data/mockData'

interface RecommendationCardProps {
  recommendations: AiRecommendation[]
}

const typeIcons: Record<string, typeof AlertTriangle> = {
  security: AlertTriangle,
  carbon: Leaf,
  energy: Zap,
  general: Brain,
}

const typeColors: Record<string, string> = {
  security: 'text-danger',
  carbon: 'text-accent-light',
  energy: 'text-warning',
  general: 'text-accent',
}

const typeBg: Record<string, string> = {
  security: 'bg-danger/10 border-danger/20',
  carbon: 'bg-accent/10 border-accent/20',
  energy: 'bg-warning/10 border-warning/20',
  general: 'bg-accent/10 border-accent/20',
}

const priorityVariant: Record<string, 'danger' | 'warning' | 'primary' | 'muted'> = {
  critical: 'danger',
  high: 'warning',
  medium: 'primary',
  low: 'muted',
}

export default function RecommendationCard({ recommendations }: RecommendationCardProps) {
  return (
    <div className="space-y-3">
      {recommendations.map((rec) => {
        const Icon = typeIcons[rec.type] || Brain
        const color = typeColors[rec.type] || 'text-accent'
        const bg = typeBg[rec.type] || 'bg-accent/10 border-accent/20'
        return (
          <div key={rec.id} className="p-3 bg-background rounded-md border border-border/50 hover:border-border transition-colors">
            <div className="flex items-start gap-3">
              <div className={`p-1.5 rounded-md border ${bg} flex-shrink-0 mt-0.5`}>
                <Icon className={`w-4 h-4 ${color}`} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant={priorityVariant[rec.priority]}>{rec.priority}</Badge>
                  <span className="text-[10px] text-muted uppercase tracking-wider">{rec.type}</span>
                </div>
                <p className="text-sm text-text-primary leading-relaxed">{rec.recommendation}</p>
                <p className="text-xs text-muted mt-1.5">{rec.reason}</p>
                <div className="flex items-center gap-3 mt-2">
                  <span className="text-[10px] text-accent">Impact: {rec.expectedImpact}</span>
                  <span className="text-[10px] text-muted">{(rec.confidence * 100).toFixed(0)}% confidence</span>
                </div>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
