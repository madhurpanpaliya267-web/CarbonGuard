import { Shield, Zap, Leaf, TrendingUp } from 'lucide-react'
import type { CarbonEfficiencyData } from '@/shared/data/mockData'

interface SecurityCarbonEfficiencyProps {
  data: CarbonEfficiencyData
}

const ratingColors: Record<string, string> = {
  Excellent: 'text-accent-light',
  Good: 'text-accent',
  Fair: 'text-warning',
  Poor: 'text-danger',
}

const ratingBarColors: Record<string, string> = {
  Excellent: 'bg-accent-light',
  Good: 'bg-accent',
  Fair: 'bg-warning',
  Poor: 'bg-danger',
}

export default function SecurityCarbonEfficiency({ data }: SecurityCarbonEfficiencyProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 bg-background rounded-md border border-border/50">
          <div className="flex items-center gap-2 mb-1">
            <Shield className="w-3.5 h-3.5 text-accent" />
            <span className="text-[10px] text-muted uppercase tracking-wider">Threats Detected</span>
          </div>
          <p className="text-xl font-bold text-accent">{data.threatsDetected}</p>
        </div>
        <div className="p-3 bg-background rounded-md border border-border/50">
          <div className="flex items-center gap-2 mb-1">
            <Zap className="w-3.5 h-3.5 text-warning" />
            <span className="text-[10px] text-muted uppercase tracking-wider">Energy Used</span>
          </div>
          <p className="text-xl font-bold text-warning">{data.energyUsed}</p>
        </div>
        <div className="p-3 bg-background rounded-md border border-border/50">
          <div className="flex items-center gap-2 mb-1">
            <Leaf className="w-3.5 h-3.5 text-accent-light" />
            <span className="text-[10px] text-muted uppercase tracking-wider">Est. CO2</span>
          </div>
          <p className="text-xl font-bold text-accent-light">{data.estimatedCo2}</p>
        </div>
        <div className="p-3 bg-background rounded-md border border-border/50">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp className="w-3.5 h-3.5 text-accent" />
            <span className="text-[10px] text-muted uppercase tracking-wider">Workload</span>
          </div>
          <p className="text-sm font-bold text-accent">{data.securityWorkload}</p>
        </div>
      </div>

      <div className="p-4 bg-background rounded-md border border-accent/20">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-muted uppercase tracking-wider">Efficiency Score</span>
          <span className={`text-lg font-bold ${ratingColors[data.rating] || 'text-accent'}`}>
            {data.efficiencyScore}/100
          </span>
        </div>
        <div className="w-full bg-border rounded-full h-2.5 overflow-hidden">
          <div
            className={`${ratingBarColors[data.rating] || 'bg-accent'} rounded-full h-2.5 transition-all duration-700 ease-out`}
            style={{ width: `${data.efficiencyScore}%` }}
          />
        </div>
        <p className="text-[10px] text-muted mt-2">
          Rating: <span className={`font-medium ${ratingColors[data.rating]}`}>{data.rating}</span>
          {' '}— Security workload vs estimated environmental impact
        </p>
      </div>
    </div>
  )
}
