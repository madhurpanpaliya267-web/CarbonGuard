import { Routes, Route } from 'react-router-dom'
import MainLayout from './shared/layouts/MainLayout'
import DashboardPage from './features/dashboard/components/DashboardPage'
import SecurityPage from './features/security/components/SecurityPage'
import AttackSimulatorPage from './features/attack-simulator/components/AttackSimulatorPage'
import ThreatsPage from './features/threats/components/ThreatsPage'
import CarbonPage from './features/carbon/components/CarbonPage'
import EnergyPage from './features/energy/components/EnergyPage'
import OptimizerPage from './features/optimizer/components/OptimizerPage'
import RenewableEnergyPage from './features/renewable-energy/components/RenewableEnergyPage'
import AiRecommendationsPage from './features/ai-recommendations/components/AiRecommendationsPage'
import AnalyticsPage from './features/analytics/components/AnalyticsPage'
import ResearchLabPage from './features/research-lab/components/ResearchLabPage'
import MarginalEnergyPage from './features/research-lab/components/MarginalEnergyPage'
import InteractionAnalysisPage from './features/research-lab/components/InteractionAnalysisPage'
import DefenseAmplificationPage from './features/research-lab/components/DefenseAmplificationPage'
import ExperimentsPage from './features/research-lab/components/ExperimentsPage'
import ExperimentDetailPage from './features/research-lab/components/ExperimentDetailPage'
import ResearchDatasetPage from './features/research-lab/components/ResearchDatasetPage'
import EventsPage from './features/events/components/EventsPage'
import SystemHealthPage from './features/system-health/components/SystemHealthPage'
import SettingsPage from './features/settings/components/SettingsPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="security" element={<SecurityPage />} />
        <Route path="attack-simulator" element={<AttackSimulatorPage />} />
        <Route path="threats" element={<ThreatsPage />} />
        <Route path="carbon" element={<CarbonPage />} />
        <Route path="energy" element={<EnergyPage />} />
        <Route path="optimizer" element={<OptimizerPage />} />
        <Route path="renewable-energy" element={<RenewableEnergyPage />} />
        <Route path="ai-recommendations" element={<AiRecommendationsPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="research-lab" element={<ResearchLabPage />} />
        <Route path="research-lab/marginal-energy" element={<MarginalEnergyPage />} />
        <Route path="research-lab/interaction-analysis" element={<InteractionAnalysisPage />} />
        <Route path="research-lab/defense-amplification" element={<DefenseAmplificationPage />} />
        <Route path="research-lab/experiments" element={<ExperimentsPage />} />
        <Route path="research-lab/experiments/:id" element={<ExperimentDetailPage />} />
        <Route path="research-lab/dataset" element={<ResearchDatasetPage />} />
        <Route path="events" element={<EventsPage />} />
        <Route path="system-health" element={<SystemHealthPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}
