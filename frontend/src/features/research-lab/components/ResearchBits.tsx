import type { ReactNode } from 'react'
import { AlertTriangle, Inbox, Loader2 } from 'lucide-react'

export function SectionLoading({ label = 'Loading research data…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center py-12 text-muted" data-testid="section-loading">
      <Loader2 className="w-5 h-5 animate-spin mr-2" />
      <span className="text-xs">{label}</span>
    </div>
  )
}

export function SectionError({
  title = 'Unable to load research data',
  message,
}: {
  title?: string
  message: string
}) {
  return (
    <div className="flex flex-col items-center justify-center py-10 text-center">
      <AlertTriangle className="w-8 h-8 text-danger mb-3" />
      <p className="text-sm text-danger mb-1">{title}</p>
      <p className="text-xs text-muted max-w-md">{message}</p>
    </div>
  )
}

export function SectionEmpty({
  title,
  message,
}: {
  title: string
  message: string
}) {
  return (
    <div className="flex flex-col items-center justify-center py-10 text-center">
      <Inbox className="w-8 h-8 text-muted mb-3" />
      <p className="text-sm text-text-primary mb-1">{title}</p>
      <p className="text-xs text-muted max-w-md">{message}</p>
    </div>
  )
}

export function Field({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5 min-w-0">
      <span className="text-[10px] uppercase tracking-wider text-muted">{label}</span>
      <span className="text-sm text-text-primary break-words">{value}</span>
    </div>
  )
}

export function FieldGrid({ children }: { children: ReactNode }) {
  return <div className="grid grid-cols-2 md:grid-cols-3 gap-x-4 gap-y-3">{children}</div>
}

export function FormulaNote({ children }: { children: ReactNode }) {
  return (
    <div className="mt-4 px-3 py-2 bg-background/60 border border-border rounded-md">
      <p className="text-[11px] text-muted font-mono leading-relaxed">{children}</p>
    </div>
  )
}

export function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-background/60 border border-border rounded-md px-3 py-2">
      <p className="text-[10px] uppercase tracking-wider text-muted">{label}</p>
      <p className="text-sm font-semibold text-text-primary mt-0.5">{value}</p>
    </div>
  )
}
