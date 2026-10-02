import { LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  color?: 'primary' | 'danger' | 'warning' | 'success' | 'purple'
  trend?: number
  subtitle?: string
  compact?: boolean
}

const colorMap = {
  primary: { bg: 'bg-accent/10', text: 'text-accent', border: 'border-accent/20', icon: 'text-accent' },
  danger: { bg: 'bg-danger/10', text: 'text-danger', border: 'border-danger/20', icon: 'text-danger' },
  warning: { bg: 'bg-warning/10', text: 'text-warning', border: 'border-warning/20', icon: 'text-warning' },
  success: { bg: 'bg-success/10', text: 'text-success', border: 'border-success/20', icon: 'text-success' },
  purple: { bg: 'bg-violet-500/10', text: 'text-violet-400', border: 'border-violet-500/20', icon: 'text-violet-400' },
}

export default function MetricCard({ title, value, icon: Icon, color = 'primary', trend, subtitle, compact }: MetricCardProps) {
  const c = colorMap[color]
  return (
    <div className={`card ${compact ? 'p-4' : 'p-5'} hover:border-border-hover transition-all duration-200 group`}>
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-[10px] font-medium text-muted uppercase tracking-wider">{title}</p>
          <p className={`${compact ? 'text-xl' : 'text-2xl'} font-bold ${c.text} mt-1 tracking-tight`}>{value}</p>
          {subtitle && <p className="text-xs text-muted mt-1 truncate">{subtitle}</p>}
          {trend !== undefined && (
            <div className="flex items-center gap-1 mt-2">
              {trend > 0 ? (
                <TrendingUp className="w-3 h-3 text-accent" />
              ) : trend < 0 ? (
                <TrendingDown className="w-3 h-3 text-danger" />
              ) : (
                <Minus className="w-3 h-3 text-muted" />
              )}
              <span className={`text-xs font-medium ${trend > 0 ? 'text-accent' : trend < 0 ? 'text-danger' : 'text-muted'}`}>
                {trend > 0 ? '+' : ''}{trend}%
              </span>
              <span className="text-xs text-muted">vs yesterday</span>
            </div>
          )}
        </div>
        <div className={`${c.bg} ${c.border} border rounded-md p-2.5 flex-shrink-0 group-hover:scale-105 transition-transform`}>
          <Icon className={`w-5 h-5 ${c.icon}`} />
        </div>
      </div>
    </div>
  )
}
