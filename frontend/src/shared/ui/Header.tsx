import { Bell, Search, Monitor, Wifi } from 'lucide-react'
import Badge from './Badge'

export default function Header() {
  return (
    <header className="h-14 bg-surface/80 backdrop-blur-md border-b border-border flex items-center justify-between px-6 sticky top-0 z-30">
      <div className="flex items-center gap-4">
        <div className="lg:hidden w-10" />
        <div className="hidden sm:flex items-center gap-2 text-xs text-muted">
          <div className="relative">
            <Monitor className="w-3.5 h-3.5 text-accent" />
            <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-accent rounded-full animate-pulse" />
          </div>
          <span>System Online</span>
        </div>
        <Badge variant="warning" size="sm">
          <span className="inline-block w-1.5 h-1.5 bg-warning rounded-full animate-pulse mr-1" />
          SIMULATION MODE
        </Badge>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative hidden md:block">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            type="text"
            placeholder="Search events, threats..."
            className="bg-card border border-border rounded-md pl-9 pr-4 py-1.5 text-sm text-text-primary placeholder-muted focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/20 w-64 transition-all"
          />
        </div>

        <div className="flex items-center gap-2 text-xs text-muted">
          <Wifi className="w-3.5 h-3.5 text-accent" />
          <span className="hidden sm:inline">Connected</span>
        </div>

        <button className="relative p-2 text-muted hover:text-text-primary transition-colors rounded-md hover:bg-card">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-danger rounded-full" />
        </button>

        <div className="w-px h-6 bg-border" />

        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-md bg-accent/15 border border-accent/25 flex items-center justify-center">
            <span className="text-xs font-bold text-accent">CG</span>
          </div>
          <div className="hidden sm:block">
            <p className="text-xs font-medium text-text-primary">Admin</p>
            <p className="text-[10px] text-muted">Demo User</p>
          </div>
        </div>
      </div>
    </header>
  )
}
