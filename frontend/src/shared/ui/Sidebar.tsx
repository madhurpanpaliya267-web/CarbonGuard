import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Shield,
  Zap,
  Target,
  Leaf,
  Battery,
  Settings,
  Activity,
  Brain,
  BarChart3,
  FlaskConical,
  ScrollText,
  HeartPulse,
  Sliders,
  Sun,
  ChevronLeft,
  ChevronRight,
  Menu,
  GitBranch,
  Waves,
  Radio,
  PlayCircle,
  Table2,
  type LucideIcon,
} from 'lucide-react'

interface NavItem {
  to: string
  icon: LucideIcon
  label: string
}

interface NavSection {
  title?: string
  items: NavItem[]
}

const navSections: NavSection[] = [
  {
    items: [
      { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
      { to: '/security', icon: Shield, label: 'Security Monitor' },
      { to: '/attack-simulator', icon: Zap, label: 'Attack Simulator' },
      { to: '/threats', icon: Target, label: 'Threats' },
      { to: '/carbon', icon: Leaf, label: 'Carbon Monitor' },
      { to: '/energy', icon: Battery, label: 'Energy Monitor' },
      { to: '/optimizer', icon: Sliders, label: 'Carbon Optimizer' },
      { to: '/renewable-energy', icon: Sun, label: 'Renewable Energy' },
      { to: '/ai-recommendations', icon: Brain, label: 'AI Recommendations' },
      { to: '/analytics', icon: BarChart3, label: 'Analytics' },
    ],
  },
  {
    title: 'Research',
    items: [
      { to: '/research-lab', icon: FlaskConical, label: 'Research Lab' },
      { to: '/research-lab/marginal-energy', icon: Waves, label: 'Marginal Energy' },
      { to: '/research-lab/interaction-analysis', icon: GitBranch, label: 'Interaction Analysis' },
      { to: '/research-lab/defense-amplification', icon: Radio, label: 'Defense Amplification' },
      { to: '/research-lab/experiments', icon: PlayCircle, label: 'Experiments' },
      { to: '/research-lab/dataset', icon: Table2, label: 'Research Dataset' },
    ],
  },
  {
    items: [
      { to: '/events', icon: ScrollText, label: 'Event Logs' },
      { to: '/system-health', icon: HeartPulse, label: 'System Health' },
      { to: '/settings', icon: Settings, label: 'Settings' },
    ],
  },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <>
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="lg:hidden fixed top-3 left-3 z-50 p-2 bg-surface border border-border rounded-md text-muted hover:text-text-primary"
      >
        <Menu className="w-5 h-5" />
      </button>

      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/60 z-40 backdrop-blur-sm"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside className={`
        fixed lg:sticky top-0 left-0 z-40 h-screen
        bg-surface border-r border-border flex flex-col
        transition-all duration-300 ease-in-out
        ${collapsed ? 'w-[68px]' : 'w-64'}
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="p-4 border-b border-border flex items-center justify-between">
          {!collapsed && (
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-md bg-accent/15 border border-accent/25 flex items-center justify-center flex-shrink-0">
                <Activity className="w-4.5 h-4.5 text-accent" />
              </div>
              <div className="min-w-0">
                <h1 className="text-sm font-bold text-text-primary truncate tracking-tight">CarbonGuard</h1>
                <p className="text-[10px] text-muted truncate">Green SOC Operations</p>
              </div>
            </div>
          )}
          {collapsed && (
            <div className="w-8 h-8 rounded-md bg-accent/15 border border-accent/25 flex items-center justify-center mx-auto">
              <Activity className="w-4.5 h-4.5 text-accent" />
            </div>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden lg:flex p-1 text-muted hover:text-text-primary transition-colors flex-shrink-0"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto py-2 px-2">
          {navSections.map((section, sectionIndex) => (
            <div key={section.title ?? `nav-${sectionIndex}`}>
              {section.title && !collapsed && (
                <p className="px-3 pt-3 pb-1 text-[10px] font-semibold uppercase tracking-widest text-muted/80">
                  {section.title}
                </p>
              )}
              {section.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/' || item.to === '/research-lab'}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 text-sm rounded-md transition-all duration-150 mb-0.5 relative ${
                      isActive
                        ? 'bg-accent/10 text-accent-light border-l-2 border-accent ml-0'
                        : 'text-muted hover:text-text-primary hover:bg-card border-l-2 border-transparent ml-0'
                    } ${collapsed ? 'justify-center' : ''}`
                  }
                  title={collapsed ? item.label : undefined}
                >
                  <item.icon className="w-4 h-4 flex-shrink-0" />
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        <div className="p-3 border-t border-border">
          {!collapsed && (
            <div className="text-[10px] text-muted text-center">
              v1.0.0 — Simulation Mode
            </div>
          )}
          {collapsed && (
            <div className="text-[10px] text-muted text-center">v1.0</div>
          )}
        </div>
      </aside>
    </>
  )
}
