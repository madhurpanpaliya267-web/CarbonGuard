export const ENDPOINTS = {
  dashboard: {
    metrics: '/dashboard',
    threatActivity: '/dashboard/charts/threat-activity',
    carbonEmissions: '/dashboard/charts/carbon-emissions',
    energyConsumption: '/dashboard/charts/energy-consumption',
    carbonSavings: '/dashboard/charts/carbon-savings',
    threatCategories: '/dashboard/charts/threat-categories',
    threatSeverity: '/dashboard/charts/threat-severity',
  },
  security: {
    events: '/security/events',
    eventDetail: (id: number) => `/security/events/${id}`,
  },
  simulator: {
    simulate: '/simulator/simulate',
    attackTypes: '/simulator/attack-types',
  },
  threats: {
    list: '/threats',
    detail: (id: number) => `/threats/${id}`,
    explanation: (id: number) => `/threats/${id}/explanation`,
  },
  carbon: {
    overview: '/carbon',
    current: '/carbon/current',
    history: '/carbon/history',
    calculate: '/carbon/calculate',
    efficiency: '/carbon/efficiency',
  },
  energy: {
    overview: '/energy',
    current: '/energy/current',
    history: '/energy/history',
  },
  optimizer: {
    workloads: '/optimizer/workloads',
    run: '/optimizer/run',
    history: '/optimizer/history',
    comparison: '/optimizer/comparison',
  },
  renewable: {
    status: '/renewable-energy',
    forecast: '/renewable-energy/forecast',
  },
  recommendations: {
    list: '/recommendations',
    generate: '/recommendations/generate',
    markRead: (id: number) => `/recommendations/${id}/read`,
    dismiss: (id: number) => `/recommendations/${id}/dismiss`,
  },
  analytics: {
    security: '/analytics/security',
    carbon: '/analytics/carbon',
    energy: '/analytics/energy',
    optimization: '/analytics/optimization',
  },
  events: {
    list: '/events',
  },
  systemHealth: {
    status: '/system-health',
    history: '/system-health/history',
  },
  settings: {
    list: '/settings',
    update: '/settings',
    reset: '/settings/reset',
  },
} as const
