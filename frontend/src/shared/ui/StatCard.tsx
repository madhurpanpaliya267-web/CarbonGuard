import { LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  icon: LucideIcon
  trend?: {
    value: number
    isPositive: boolean
  }
  subtitle?: string
  color?: 'primary' | 'danger' | 'warning' | 'success'
}

const colorClasses = {
  primary: 'text-accent',
  danger: 'text-danger',
  warning: 'text-warning',
  success: 'text-accent-light',
}

export default function StatCard({
  title,
  value,
  icon: Icon,
  trend,
  subtitle,
  color = 'primary',
}: StatCardProps) {
  return (
    <div className="card p-5 hover:border-border-hover transition-all duration-200">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs text-muted mb-1 uppercase tracking-wider">{title}</p>
          <p className={`text-2xl font-bold ${colorClasses[color]} tracking-tight`}>{value}</p>
          {subtitle && (
            <p className="text-xs text-muted mt-1">{subtitle}</p>
          )}
          {trend && (
            <div className="flex items-center gap-1 mt-2">
              <span
                className={`text-xs font-medium ${
                  trend.isPositive ? 'text-accent' : 'text-danger'
                }`}
              >
                {trend.isPositive ? '+' : ''}{trend.value}%
              </span>
              <span className="text-xs text-muted">vs last period</span>
            </div>
          )}
        </div>
        <div className={`p-2 rounded-md bg-accent/10 border border-accent/20`}>
          <Icon className={`w-5 h-5 ${colorClasses[color]}`} />
        </div>
      </div>
    </div>
  )
}
