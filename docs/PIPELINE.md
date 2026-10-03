# CarbonGuard End-to-End Pipeline (Phase 13)

Phase 13 connects the existing CarbonGuard subsystems into ONE coherent
cybersecurity + energy + carbon workflow. It adds no duplicate engines,
formulas, storage or endpoints — only orchestration.

All attack data flowing through this pipeline is **SYNTHETIC / SIMULATED**.
No real systems are scanned or attacked.

## Pipeline

```
AttackSimulation      engines/security/attack_simulator.simulate_attack
      ↓
ThreatDetection       engines/security/threat_detector.detect_event
      ↓
ThreatClassification  engines/security/threat_detector.classify_severity
      ↓
RiskAssessment        engines/security/risk_analyzer.analyze_risk
      ↓
AdaptiveDefense       engines/security/security_controls.select_controls_for_threat
      ↓
EnergyImpact          engines/energy/factory provider (Phase 5/6/7 abstraction)
      ↓
CarbonImpact          engines/carbon/carbon_calculator.calculate_carbon
      ↓
ResearchObservation   services/research_service.record_pipeline_observation
      ↓
Analytics             persisted feeds -> /security/stats, /dashboard,
                      /research/summary, /research/metrics
```

Orchestration entry point: `app/services/orchestration_service.py`
(`CarbonGuardOrchestrationService.run`).

## Component Mapping

| Stage | Existing implementation | Endpoint | Reused by Phase 13 |
|---|---|---|---|
| Attack simulation | `engines/security/attack_simulator.simulate_attack` | `POST /api/v1/simulator/simulate` | yes (unchanged) |
| Threat detection | `engines/security/threat_detector.detect_event` | internal | yes (via simulate) |
| Threat classification | `threat_detector.classify_severity` | internal | yes (via simulate) |
| Risk assessment | `engines/security/risk_analyzer.analyze_risk` | internal | yes (via simulate) |
| Control selection | `engines/security/security_controls` | `GET /api/v1/research/controls` | extended with `select_controls_for_threat` |
| Workload optimizer | `engines/optimizer/workload_optimizer` | `/api/v1/optimizer/*` | not part of the per-attack pipeline (workload scheduling only) |
| Energy measurement | `engines/energy/*` providers | `/api/v1/energy` | yes (`security_controls_active`) |
| Carbon calculation | `engines/carbon/carbon_calculator.calculate_carbon` | `/api/v1/carbon` | yes (single formula) |
| Event/threat persistence | `services/security_service.SecurityService` | `/api/v1/security/events` | yes (`persist_simulation`) |
| Experiment storage | `services/research_service.ResearchExperimentService` | `/api/v1/research/*` | yes (`record_pipeline_observation`) |
| Research analytics | `services/research_analytics_service`, `research_summary_service` | `/api/v1/research/analytics`, `/summary` | fed by recorded runs |
| Dashboard | `services/dashboard_service` | `/api/v1/dashboard` | fed by persisted events/threats |
| Research Lab | `app/api/research.py` (Phase 11) | `/api/v1/research/*` | unchanged |

## API

`POST /api/v1/orchestration/run` (the only new route)

```json
{
  "attack_type": "ddos",
  "intensity": "medium",
  "duration_seconds": 60,
  "measurement_provider": "estimated",
  "record_research": true,
  "experiment_uuid": "<existing experiment uuid>",
  "carbon_intensity": 475,
  "renewable_percentage": 25
}
```

Only `attack_type` is required. Response schema:
`app/schemas/orchestration.py::OrchestrationRunResponse`:

```json
{
  "status": "completed | partial",
  "event": {...}, "attack": {...}, "threat": {...}, "risk": {...},
  "defense": {...}, "security_controls": ["..."],
  "energy": {...}, "carbon": {...}, "comparison": {...},
  "research": {...}, "analytics": {...}, "provenance": {...},
  "stages": [...], "warnings": [...]
}
```

`GET /api/v1/simulator/simulate` and all Phase 1-12 endpoints are unchanged.

## Defense Selection (threat → controls)

`select_controls_for_threat` is a deterministic, registry-ordered rule:

| Threat severity | Controls selected |
|---|---|
| LOW | 1 (minimum necessary) |
| MEDIUM | 2 (moderate) |
| HIGH | 4 (stronger) |
| CRITICAL | every control registered for the attack type |

Candidates come from the existing `get_controls_for_attack` registry. The
result is always described as `basis: "rule_based"` / "selected" — never as
optimal or optimizer-generated.

## Energy Provenance (defense → energy)

- Uses the existing `EnergyMeasurementProvider` abstraction
  (`estimated`, `rapl`, `kepler`, `external`).
- Passes `security_controls_active = len(selected controls)` and the attack
  intensity, so activated controls are priced by the same coefficients the
  Phase 5/6/7 research experiments use.
- Marginal Energy, Interaction Effect and Defense Energy Amplification
  formulas are NOT modified. Persisted pipeline runs can be paired through
  those existing research endpoints afterwards.
- Every energy value carries `measurement_mode`:
  `ESTIMATED` | `MEASURED` | `SIMULATED`, plus `measurement_source`.
  Measured energy is only reported when a hardware provider is actually
  available; estimated values are never presented as measured.

## Carbon Provenance (energy → carbon)

- Single formula: `calculate_carbon(energy_kwh, carbon_intensity,
  renewable_percentage)` — gross = energy × intensity; net = gross −
  renewable offset. No second carbon formula exists.
- `carbon_basis` is derived with `carbon_basis_label(measurement_mode)`, e.g.
  `calculated_from_estimated_energy`. Carbon is never hardware-measured and
  is never presented as such.

## Comparison (baseline vs defense)

When both sides are available, the pipeline reports a paired same-provider
comparison: baseline (`security_controls_active = 0`) vs defense
(`security_controls_active = N`), same duration, same coefficients.

- `direction` is `additional_energy`, `energy_saved` or `neutral`.
- "saved" is only reported when the computed difference is actually negative.
- The basis string (e.g. `paired_estimated_same_provider`) is always shown;
  it is a model comparison, not a hardware measurement.

## Research Integration (pipeline → experiments)

`ResearchExperimentService.record_pipeline_observation` appends the pipeline
run as the next trial of an existing experiment, reusing the existing
tables (no new storage):

- `experiment_runs`: attack type/intensity/profile, security controls,
  measurement mode, trial number, timestamps
- `energy_measurements`: joules, watts, duration, source, mode
- `security_effectiveness`: threat severity, security response, risk score,
  controls active
- `research_metrics`: net carbon (`pipeline_net_carbon_kg`) with the carbon
  basis in notes

Recording is optional (`record_research: true` + `experiment_uuid`).
Failures never fail the pipeline — they return `research.status = "failed"`
with a `reason` and a pipeline warning.

## Analytics / Dashboard Feed

- Persisted events/threats increment `/api/v1/security/stats`,
  `/api/v1/threats/stats` and `/api/v1/dashboard` counters (labelled
  `simulated: true`).
- Recorded research observations appear in `/api/v1/research/summary` and
  `/api/v1/research/metrics`, and are analysable through
  `/api/v1/research/analytics`.
- The response's `analytics.feeds` lists exactly which feeds this run
  reached. No synthetic dashboard activity is created.

## Failure Handling

| Failure | Behaviour |
|---|---|
| Invalid attack profile / intensity / provider / duration | HTTP 400/422 before the run starts |
| Event/threat persistence failure | pipeline continues with raw dicts; `analytics.status = "partial"`, warning |
| Energy provider unavailable | `energy.status = "unavailable"` + reason; carbon and comparison degrade; run = `partial` |
| Carbon calculation unavailable | `carbon.status = "unavailable"` + reason; energy kept; comparison unavailable |
| Invalid experiment ID | `research.status = "failed"` + reason; run continues |
| Research persistence failure | `research.status = "failed"` + warning; run continues |
| Optional analytics/persistence problems | explicit `status`/`reason`/`warnings` fields, never an exception to the client |

## Synthetic vs Measured

| Data | Label |
|---|---|
| Attack, event, threat, risk | SYNTHETIC (simulated) |
| Energy | `measurement_mode` = ESTIMATED / MEASURED / SIMULATED + source |
| Carbon | `carbon_basis` = calculated_from_*_energy |
| Control selection | `basis` = rule_based |
| Comparison | `basis` = paired_*_same_provider |

## Frontend

`AttackSimulatorPage` runs the integrated pipeline via
`api.runPipeline` (`POST /api/v1/orchestration/run`) and renders:

1. Pipeline flow strip: ATTACK → THREAT → DEFENSE → ENERGY → CARBON → RESULT
2. Result summary (attack type, threat level, risk, security response,
   controls activated, energy, carbon, measurement mode, carbon basis,
   research run ID)
3. Warnings (when degraded), event details, risk assessment
4. Adaptive security response (rule-based controls, tier, reason)
5. Energy and carbon cards with measurement/basis badges
6. Baseline vs defense comparison (or "Not available" with a reason)
7. Rule-based recommendation and the full stage list

Missing metrics render as **Not available** with the API's reason; nothing is
fabricated client-side.

## Integration Audit (Phase 17)

Phase 17 verified the complete integration across the whole system. No
integration defects were found; no source code was changed.

### Verified end-to-end path

```
frontend api.runPipeline / researchApi
  → fetch(`${VITE_API_BASE_URL}` = http://localhost:8000/api/v1)
  → app.main → api/router.py (15 route modules + research + orchestration)
  → thin route → service → engine (security → controls → energy provider → carbon)
  → research persistence (experiment_runs / energy_measurements /
    security_effectiveness / research_metrics)
  → typed response (response_model DTOs)
  → frontend section rendering with provenance badges
```

Verified specifically:

- **Router registration**: all 15 feature routers + `research` + `orchestration`
  mounted under `/api/v1`; no duplicate or stale routes; route ordering
  (`/threats/stats` before `/{threat_id}`) is correct.
- **Endpoint → consumer map**: every path, HTTP method, query parameter and
  request payload used by `shared/utils/api.ts` and `research-lab/api/researchApi.ts`
  matches a backend route signature (filtered lists: `page`/`page_size`,
  `severity`, `threat_type`, `event_type`, `type`/`priority`/`unread_only`,
  `period`, research `experiment_id`/`measurement_mode`/`control_name`).
- **DTO contracts**: `ExperimentCreateRequest`, `ExperimentSummaryResponse`,
  `ExperimentStatusResponse`, `ResearchAnalyticsRequest`,
  `ResearchSummaryResponse` and `OrchestrationRunResponse` (all 15 top-level
  keys) match their frontend TypeScript counterparts field-for-field.
- **Orchestration chain**: attack → threat → risk → rule-based defense →
  energy provider → carbon → research recording → persistence feeds →
  response → `AttackSimulatorPage` rendering (stages, warnings, provenance,
  measurement badges).
- **Persistence/DTO boundary**: research and orchestration routes return
  typed `response_model` schemas (25 typed responses); ORM rows never leak
  through those DTOs. Remaining feature routes return plain dicts by design
  (see §2.9 problem 5 in RESEARCH_ARCHITECTURE.md).
- **E2E smoke test**: `backend/tests/test_api/test_e2e_smoke.py` exercises the
  whole chain (create experiment → pipeline run with `record_research` →
  summary/security/research aggregates → CSV export) in under a second.

### Known integration limitations (unchanged, pre-existing)

| # | Limitation | Reference |
|---|-----------|-----------|
| 1 | Dashboard metric values and chart series still include synthetic randomness; only event/threat counters come from the DB | RESEARCH_ARCHITECTURE §2.9 #2/#3 |
| 2 | Duplicate event endpoints (`/security/events` and `/events`), both consumed by the frontend | §2.9 #4 |
| 3 | Two HTTP client patterns coexist: `fetchWithFallback` (GET + mock fallback) and `apiClient` (mutations) | §2.9 #8 |
| 4 | No authentication and no database migrations | §2.9 #6/#7 |
| 5 | Attack Simulator uses a local `MeasurementBadge`; Research Lab uses `modeVariant` — same literal labels, slightly different color mapping (both keep MEASURED visually distinct) | audit observation |
| 6 | Backend has no linter; `npm run lint` references eslint, which is not in devDependencies (typechecking runs via `npm run build`) | docs/testing.md |
| 7 | `api.simulateAttack` (`POST /simulator/simulate`) is retained API surface with no current frontend consumer | audit observation |
