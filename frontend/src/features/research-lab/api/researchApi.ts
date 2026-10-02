import { config } from '@/config/env'
import type {
  AmplificationListResponse,
  AttackProfileListResponse,
  ExperimentCreateRequest,
  ExperimentListResponse,
  Experiment,
  ExperimentRunListResponse,
  ExperimentStatus,
  ExperimentSummary,
  ExportDataset,
  InteractionEffectListResponse,
  MarginalEnergyListResponse,
  OptimizerComparison,
  ResearchAnalyticsListResponse,
  ResearchAnalyticsRequest,
  ResearchAnalyticsResult,
  ResearchExportPayload,
  ResearchMetrics,
  ResearchSummary,
  SecurityControlListResponse,
} from '../types/research'

const RESEARCH_PATH = '/research'

type QueryValue = string | number | boolean | null | undefined

function withQuery(path: string, params: Record<string, QueryValue> = {}): string {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === null || value === undefined || value === '') return
    search.set(key, String(value))
  })
  const query = search.toString()
  return query ? `${path}?${query}` : path
}

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

async function requestText(path: string): Promise<string> {
  const response = await fetch(`${config.API_BASE_URL}${path}`)

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: undefined }))
    const detail = typeof body.detail === 'string' ? body.detail : undefined
    throw new Error(detail || `Request failed (HTTP ${response.status})`)
  }

  return response.text()
}

export interface ExperimentQuery {
  experiment_type?: string
  status?: string
  offset?: number
  limit?: number
}

export interface ResultQuery {
  experiment_id?: number
  attack_type?: string
  attack_intensity?: string
  measurement_mode?: string
  control?: string
  offset?: number
  limit?: number
}

export const researchApi = {
  listExperiments: (query: ExperimentQuery = {}) =>
    request<ExperimentListResponse>(
      withQuery(`${RESEARCH_PATH}/experiments`, { limit: 100, ...query }),
    ),

  createExperiment: (body: ExperimentCreateRequest) =>
    request<Experiment>(`${RESEARCH_PATH}/experiments`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  executeExperiment: (experimentUuid: string) =>
    request<Experiment>(
      `${RESEARCH_PATH}/experiments/${experimentUuid}/execute`,
      { method: 'POST' },
    ),

  getExperiment: (experimentUuid: string) =>
    request<Experiment>(`${RESEARCH_PATH}/experiments/${experimentUuid}`),

  getExperimentStatus: (experimentUuid: string) =>
    request<ExperimentStatus>(`${RESEARCH_PATH}/experiments/${experimentUuid}/status`),

  getExperimentRuns: (experimentUuid: string) =>
    request<ExperimentRunListResponse>(
      `${RESEARCH_PATH}/experiments/${experimentUuid}/runs`,
    ),

  getExperimentSummary: (experimentUuid: string) =>
    request<ExperimentSummary>(`${RESEARCH_PATH}/experiments/${experimentUuid}/summary`),

  listAttacks: () => request<AttackProfileListResponse>(`${RESEARCH_PATH}/attacks`),

  listControls: () => request<SecurityControlListResponse>(`${RESEARCH_PATH}/controls`),

  listMarginalEnergy: (query: ResultQuery = {}) =>
    request<MarginalEnergyListResponse>(
      withQuery(`${RESEARCH_PATH}/marginal-energy`, { limit: 200, ...query }),
    ),

  listInteractionEffects: (query: ResultQuery = {}) =>
    request<InteractionEffectListResponse>(
      withQuery(`${RESEARCH_PATH}/interaction-effects`, { limit: 200, ...query }),
    ),

  listAmplification: (query: ResultQuery = {}) =>
    request<AmplificationListResponse>(
      withQuery(`${RESEARCH_PATH}/defense-energy-amplification`, {
        limit: 200,
        control_name: query.control,
        ...query,
      }),
    ),

  listAnalytics: (limit = 50) =>
    request<ResearchAnalyticsListResponse>(`${RESEARCH_PATH}/analytics?limit=${limit}`),

  computeAnalytics: (body: ResearchAnalyticsRequest) =>
    request<ResearchAnalyticsResult>(`${RESEARCH_PATH}/analytics`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  getResearchSummary: () => request<ResearchSummary>(`${RESEARCH_PATH}/summary`),

  getResearchMetrics: () => request<ResearchMetrics>(`${RESEARCH_PATH}/metrics`),

  exportCsv: (dataset: ExportDataset = 'marginal_energy') =>
    requestText(withQuery(`${RESEARCH_PATH}/export/csv`, { dataset })),

  exportJson: () => request<ResearchExportPayload>(`${RESEARCH_PATH}/export/json`),

  // Read-only view of the existing optimizer service (not experiment data).
  getOptimizerComparison: () => request<OptimizerComparison>('/optimizer/comparison'),
}
