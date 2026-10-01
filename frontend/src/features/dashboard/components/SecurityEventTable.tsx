import { SeverityBadge, StatusBadge } from '@/shared/ui/Badge'
import { formatDateTime } from '@/shared/utils/formatters'
import type { SecurityEvent } from '@/shared/data/mockData'

interface SecurityEventTableProps {
  events: SecurityEvent[]
}

export default function SecurityEventTable({ events }: SecurityEventTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-border">
            <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Time</th>
            <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Event</th>
            <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider hidden sm:table-cell">Type</th>
            <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Severity</th>
            <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider hidden md:table-cell">Source</th>
            <th className="px-4 py-3 text-left text-[10px] font-semibold text-muted uppercase tracking-wider">Status</th>
          </tr>
        </thead>
        <tbody>
          {events.map((event) => (
            <tr key={event.id} className="border-b border-border/30 hover:bg-card-hover transition-colors">
              <td className="px-4 py-3 text-xs text-muted whitespace-nowrap">{formatDateTime(event.timestamp)}</td>
              <td className="px-4 py-3 text-sm text-text-primary font-medium">{event.eventType}</td>
              <td className="px-4 py-3 text-sm text-muted hidden sm:table-cell">{event.eventType}</td>
              <td className="px-4 py-3"><SeverityBadge severity={event.severity} /></td>
              <td className="px-4 py-3 text-xs text-muted font-mono hidden md:table-cell">{event.sourceIp}</td>
              <td className="px-4 py-3"><StatusBadge status={event.status} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
