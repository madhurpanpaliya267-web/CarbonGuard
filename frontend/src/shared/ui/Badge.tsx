import { ReactNode } from 'react'

type BadgeVariant = 'danger' | 'warning' | 'success' | 'primary' | 'muted' | 'purple'

interface BadgeProps {
  children: ReactNode
  variant?: BadgeVariant
  size?: 'sm' | 'md'
}

const variantClasses: Record<BadgeVariant, string> = {
  danger: 'bg-danger/15 text-danger border-danger/20',
  warning: 'bg-warning/15 text-warning border-warning/20',
  success: 'bg-success/15 text-success border-success/20',
  primary: 'bg-accent/15 text-accent border-accent/20',
  muted: 'bg-muted/15 text-muted border-muted/20',
  purple: 'bg-violet-500/15 text-violet-400 border-violet-500/20',
}

export default function Badge({ children, variant = 'muted', size = 'sm' }: BadgeProps) {
  return (
    <span className={`inline-flex items-center gap-1 border rounded font-medium ${
      size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs'
    } ${variantClasses[variant]}`}>
      {children}
    </span>
  )
}

export function SeverityBadge({ severity }: { severity: string }) {
  const variantMap: Record<string, BadgeVariant> = {
    CRITICAL: 'danger',
    HIGH: 'danger',
    MEDIUM: 'warning',
    LOW: 'success',
  }
  return <Badge variant={variantMap[severity] || 'muted'}>{severity}</Badge>
}

export function StatusBadge({ status }: { status: string }) {
  const variantMap: Record<string, BadgeVariant> = {
    detected: 'warning',
    investigating: 'primary',
    blocked: 'success',
    mitigated: 'success',
    false_positive: 'muted',
    active: 'danger',
    resolved: 'success',
  }
  return <Badge variant={variantMap[status] || 'muted'}>{status}</Badge>
}
