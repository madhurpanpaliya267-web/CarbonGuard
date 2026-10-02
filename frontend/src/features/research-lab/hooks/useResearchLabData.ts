import { useEffect, useState } from 'react'
import { researchApi } from '../api/researchApi'
import type {
  AmplificationResult,
  AttackProfile,
  Experiment,
  InteractionResult,
  MarginalEnergyResult,
  SecurityControl,
} from '../types/research'

export type ResearchSource =
  | 'experiments'
  | 'attacks'
  | 'controls'
  | 'marginal'
  | 'interaction'
  | 'amplification'

export type ResearchErrors = Record<ResearchSource, string | null>

function emptyErrors(): ResearchErrors {
  return {
    experiments: null,
    attacks: null,
    controls: null,
    marginal: null,
    interaction: null,
    amplification: null,
  }
}

function message(error: unknown): string {
  return error instanceof Error ? error.message : 'Request failed'
}

async function settle<T>(run: () => Promise<T>): Promise<{ data: T | null; error: string | null }> {
  try {
    return { data: await run(), error: null }
  } catch (error) {
    return { data: null, error: message(error) }
  }
}

export interface ResearchLabData {
  loading: boolean
  errors: ResearchErrors
  experiments: Experiment[]
  attacks: AttackProfile[]
  controls: SecurityControl[]
  marginal: MarginalEnergyResult[]
  interaction: InteractionResult[]
  amplification: AmplificationResult[]
}

export function useResearchLabData(refreshKey = 0): ResearchLabData {
  const [loading, setLoading] = useState(true)
  const [errors, setErrors] = useState<ResearchErrors>(emptyErrors)
  const [experiments, setExperiments] = useState<Experiment[]>([])
  const [attacks, setAttacks] = useState<AttackProfile[]>([])
  const [controls, setControls] = useState<SecurityControl[]>([])
  const [marginal, setMarginal] = useState<MarginalEnergyResult[]>([])
  const [interaction, setInteraction] = useState<InteractionResult[]>([])
  const [amplification, setAmplification] = useState<AmplificationResult[]>([])

  useEffect(() => {
    let cancelled = false

    async function load() {
      const [exp, att, ctl, mar, inter, amp] = await Promise.all([
        settle(() => researchApi.listExperiments()),
        settle(() => researchApi.listAttacks()),
        settle(() => researchApi.listControls()),
        settle(() => researchApi.listMarginalEnergy()),
        settle(() => researchApi.listInteractionEffects()),
        settle(() => researchApi.listAmplification()),
      ])

      if (cancelled) return

      setExperiments(exp.data?.items ?? [])
      setAttacks(att.data?.attacks ?? [])
      setControls(ctl.data?.controls ?? [])
      setMarginal(mar.data?.items ?? [])
      setInteraction(inter.data?.items ?? [])
      setAmplification(amp.data?.items ?? [])
      setErrors({
        experiments: exp.error,
        attacks: att.error,
        controls: ctl.error,
        marginal: mar.error,
        interaction: inter.error,
        amplification: amp.error,
      })
      setLoading(false)
    }

    load()
    return () => {
      cancelled = true
    }
  }, [refreshKey])

  return { loading, errors, experiments, attacks, controls, marginal, interaction, amplification }
}
