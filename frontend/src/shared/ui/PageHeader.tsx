import { ReactNode } from 'react'

interface PageHeaderProps {
  title: string
  subtitle?: string
  actions?: ReactNode
  badge?: ReactNode
}

export default function PageHeader({ title, subtitle, actions, badge }: PageHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div className="flex items-center gap-3">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-text-primary tracking-tight">{title}</h1>
            {badge}
          </div>
          {subtitle && <p className="text-xs text-muted mt-1">{subtitle}</p>}
        </div>
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  )
}
