import { CheckCircle, AlertTriangle, XCircle } from 'lucide-react'
import type { SystemHealthStatus } from '@/shared/data/mockData'

interface SystemHealthProps {
  health: SystemHealthStatus[]
}

const statusConfig = {
  online: { icon: CheckCircle, color: 'text-accent', bg: 'bg-accent/10', border: 'border-accent/20', label: 'Operational' },
  warning: { icon: AlertTriangle, color: 'text-warning', bg: 'bg-warning/10', border: 'border-warning/20', label: 'Warning' },
  offline: { icon: XCircle, color: 'text-danger', bg: 'bg-danger/10', border: 'border-danger/20', label: 'Offline' },
}

export default function SystemHealth({ health }: SystemHealthProps) {
  return (
    <div className="space-y-2">
      {health.map((item) => {
        const config = statusConfig[item.status]
        const Icon = config.icon
        return (
          <div key={item.component} className="flex items-center justify-between p-2.5 bg-background rounded-md border border-border/50">
            <div className="flex items-center gap-3">
              <div className={`${config.bg} ${config.border} border rounded-md p-1.5`}>
                <Icon className={`w-3.5 h-3.5 ${config.color}`} />
              </div>
              <span className="text-sm text-text-primary">{item.component}</span>
            </div>
            <span className={`text-xs font-medium ${config.color}`}>{config.label}</span>
          </div>
        )
      })}
    </div>
  )
}
