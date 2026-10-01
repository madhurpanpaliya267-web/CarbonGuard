import type { Severity } from '@/shared/types/common'

interface ThreatLevelProps {
  level: Severity
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

const levelConfig: Record<Severity, { color: string; bg: string; label: string }> = {
  CRITICAL: { color: 'text-danger', bg: 'bg-danger', label: 'CRITICAL' },
  HIGH: { color: 'text-orange-400', bg: 'bg-orange-400', label: 'HIGH' },
  MEDIUM: { color: 'text-warning', bg: 'bg-warning', label: 'MEDIUM' },
  LOW: { color: 'text-success', bg: 'bg-success', label: 'LOW' },
}

const sizeConfig = {
  sm: { dot: 'w-1.5 h-1.5', text: 'text-[10px]', padding: 'px-1.5 py-0.5' },
  md: { dot: 'w-2 h-2', text: 'text-xs', padding: 'px-2 py-1' },
  lg: { dot: 'w-2.5 h-2.5', text: 'text-sm', padding: 'px-3 py-1.5' },
}

export default function ThreatLevel({ level, size = 'md', showLabel = true }: ThreatLevelProps) {
  const config = levelConfig[level]
  const sizeStyle = sizeConfig[size]

  return (
    <div className={`inline-flex items-center gap-1.5 ${sizeStyle.padding} rounded-full`}>
      <div className={`${sizeStyle.dot} ${config.bg} rounded-full animate-pulse`} />
      {showLabel && (
        <span className={`${sizeStyle.text} font-semibold ${config.color}`}>{config.label}</span>
      )}
    </div>
  )
}
