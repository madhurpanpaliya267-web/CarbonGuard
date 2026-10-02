import { config } from '@/config/env'
import type {
  AmplificationListResponse,
  AttackProfileListResponse,
  ExperimentListResponse,
  ExperimentSummary,
  InteractionEffectListResponse,
  MarginalEnergyListResponse,
  OptimizerComparison,
  ResearchAnalyticsListResponse,
  ResearchAnalyticsRequest,
  ResearchAnalyticsResult,
  SecurityControlListResponse,
} from '../types/research'

const RESEARCH_PATH = '/research'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${config.API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: undefined }))
    const detail = typeof body.detail === 'string' ? body.detail : undefined
    throw new Error(detail || `Request failed (HTTP ${response.status})`)
  }

  return response.json() as Promise<T>
}

export const researchApi = {
  listExperiments: (limit = 100) =>
    request<ExperimentListResponse>(`${RESEARCH_PATH}/experiments?limit=${limit}`),

  getExperimentSummary: (experimentUuid: string) =>
    request<ExperimentSummary>(`${RESEARCH_PATH}/experiments/${experimentUuid}/summary`),

  listAttacks: () => request<AttackProfileListResponse>(`${RESEARCH_PATH}/attacks`),

  listControls: () => request<SecurityControlListResponse>(`${RESEARCH_PATH}/controls`),

  listMarginalEnergy: (limit = 200) =>
    request<MarginalEnergyListResponse>(`${RESEARCH_PATH}/marginal-energy?limit=${limit}`),

  listInteractionEffects: (limit = 200) =>
    request<InteractionEffectListResponse>(`${RESEARCH_PATH}/interaction-effects?limit=${limit}`),

  listAmplification: (limit = 200) =>
    request<AmplificationListResponse>(
      `${RESEARCH_PATH}/defense-energy-amplification?limit=${limit}`,
    ),

  listAnalytics: (limit = 50) =>
    request<ResearchAnalyticsListResponse>(`${RESEARCH_PATH}/analytics?limit=${limit}`),

  computeAnalytics: (body: ResearchAnalyticsRequest) =>
    request<ResearchAnalyticsResult>(`${RESEARCH_PATH}/analytics`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  // Read-only view of the existing optimizer service (not experiment data).
  getOptimizerComparison: () => request<OptimizerComparison>('/optimizer/comparison'),
}
