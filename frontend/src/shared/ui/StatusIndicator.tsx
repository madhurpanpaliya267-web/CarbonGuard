interface StatusIndicatorProps {
  status: 'online' | 'offline' | 'degraded'
  label: string
}

const statusConfig = {
  online: { color: 'bg-success', text: 'text-success', label: 'Online' },
  offline: { color: 'bg-danger', text: 'text-danger', label: 'Offline' },
  degraded: { color: 'bg-warning', text: 'text-warning', label: 'Degraded' },
}

export default function StatusIndicator({ status, label }: StatusIndicatorProps) {
  const config = statusConfig[status]

  return (
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${config.color}`} />
      <span className="text-sm text-muted">{label}</span>
      <span className={`text-xs font-medium ${config.text}`}>{config.label}</span>
    </div>
  )
}
