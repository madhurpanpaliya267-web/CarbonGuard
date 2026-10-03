# Testing Strategy

This document describes the testing approach for both backend and frontend.

## Overview

| Layer | Framework | Tests | Coverage |
|-------|-----------|-------|----------|
| Backend API | pytest | 169 | All 19 route modules |
| Backend Engines | pytest | 264 | 13 engine modules |
| Backend Services | pytest | 381 | 16 service modules |
| Backend Models/Repos | pytest | 35 | Research repository layer |
| Frontend Pages | Vitest | 127 | All 18 feature test files |
| Frontend Components | Vitest | 89 | 13 shared UI components |
| Frontend Utilities | Vitest | 28 | Formatters, export helpers |
| Frontend Routing/Layout | Vitest | 6 | App routes, main layout |
| **Total** | | **1099** | 849 backend + 250 frontend |

## Backend Testing

### Test Structure

```
backend/tests/
├── conftest.py                    # Shared fixtures (client, db, setup_database)
├── test_api/                      # 19 files, 169 tests
│   ├── test_analytics.py          # 4 tests
│   ├── test_carbon.py             # 4 tests
│   ├── test_dashboard.py          # 9 tests
│   ├── test_defense_energy_amplification.py # 16 tests
│   ├── test_energy.py             # 3 tests
│   ├── test_interaction_effect.py # 15 tests
│   ├── test_marginal_energy.py    # 14 tests
│   ├── test_optimizer.py          # 4 tests
│   ├── test_orchestration.py      # 13 tests
│   ├── test_phase8_regression.py  # 9 tests
│   ├── test_recommendations.py    # 5 tests
│   ├── test_renewable.py          # 5 tests
│   ├── test_research.py           # 22 tests
│   ├── test_research_analytics.py # 21 tests
│   ├── test_research_export.py    # 8 tests
│   ├── test_research_summary.py   # 6 tests
│   ├── test_security.py           # 4 tests
│   ├── test_system_health.py      # 2 tests
│   └── test_threats.py            # 5 tests
├── test_engines/                  # 13 files, 264 tests
│   ├── test_attack_profiles.py    # 40 tests
│   ├── test_attack_simulator_integration.py # 23 tests
│   ├── test_carbon_calculator.py  # 17 tests
│   ├── test_control_selection.py  # 12 tests
│   ├── test_energy_estimator.py   # 12 tests
│   ├── test_energy_provider.py    # 37 tests
│   ├── test_explainability.py     # 12 tests
│   ├── test_recommendation_engine.py # 11 tests
│   ├── test_risk_analyzer.py      # 4 tests
│   ├── test_security_controls.py  # 30 tests
│   ├── test_statistics.py         # 44 tests
│   ├── test_threat_detector.py    # 4 tests
│   └── test_workload_optimizer.py # 18 tests
├── test_models/
│   └── test_research.py           # 35 tests
└── test_services/                 # 16 files, 381 tests
    ├── test_ai_service.py         # 12 tests
    ├── test_analytics_service.py  # 15 tests
    ├── test_carbon_service.py     # 9 tests
    ├── test_dashboard_service.py  # 9 tests
    ├── test_defense_energy_amplification.py # 68 tests
    ├── test_energy_service.py     # 7 tests
    ├── test_interaction_effect.py # 63 tests
    ├── test_marginal_energy.py    # 31 tests
    ├── test_orchestration_service.py # 28 tests
    ├── test_renewable_service.py  # 7 tests
    ├── test_research_analytics.py # 74 tests
    ├── test_research_service.py   # 36 tests
    ├── test_research_summary_service.py # 4 tests
    ├── test_security_service.py   # 6 tests
    ├── test_system_service.py     # 5 tests
    └── test_workload_service.py   # 7 tests
```

### Test Configuration

**`conftest.py`** provides:
- `client` fixture: FastAPI TestClient with dependency override
- `db` fixture: SQLAlchemy session for direct DB testing
- `setup_database` fixture: autouse, creates/drops tables per test

**Database**: SQLite in-memory (test_carbon_guard.db) with fresh tables per test.
Service test files additionally use module-scoped in-memory StaticPool engines
with per-test rollback for isolation.

### Running Backend Tests

```bash
cd backend
python -m pytest tests/ -v
```

### Test Patterns

**API Tests** — Integration tests using TestClient:
```python
class TestDashboard:
    def test_get_dashboard(self, client):
        r = client.get("/api/v1/dashboard")
        assert r.status_code == 200
        data = r.json()
        assert "carbon_guard_score" in data
```

**Engine Tests** — Pure unit tests, no fixtures:
```python
class TestCarbonCalculator:
    def test_calculate_carbon_basic(self):
        result = calculate_carbon(1.0, 475.0, 25.0)
        assert result["gross_co2_kg"] > 0
```

**Service Tests** — Unit tests with mocked repositories or seeded in-memory
sessions:
```python
class TestAIService:
    def test_get_recommendations_no_filters(self):
        mock_recs = [MagicMock(recommendation_type="security", ...)]
        self.service.rec_repo.get_all = MagicMock(return_value=mock_recs)
        result = self.service.get_recommendations()
        assert len(result) == 2
```

## Frontend Testing

### Test Structure

```
frontend/src/
├── __tests__/
│   └── App.test.tsx               # Routing test (3 tests)
├── shared/
│   ├── ui/__tests__/              # Component tests (89 tests, 13 files)
│   │   ├── Badge.test.tsx         # 14 tests
│   │   ├── Button.test.tsx        # 7 tests
│   │   ├── Card.test.tsx          # 9 tests
│   │   ├── ChartContainer.test.tsx # 4 tests
│   │   ├── DataTable.test.tsx     # 6 tests
│   │   ├── Header.test.tsx        # 6 tests
│   │   ├── LoadingSpinner.test.tsx # 4 tests
│   │   ├── MetricCard.test.tsx    # 8 tests
│   │   ├── PageHeader.test.tsx    # 6 tests
│   │   ├── Sidebar.test.tsx       # 5 tests
│   │   ├── StatCard.test.tsx      # 6 tests
│   │   ├── StatusIndicator.test.tsx # 6 tests
│   │   └── ThreatLevel.test.tsx   # 8 tests
│   ├── layouts/__tests__/
│   │   └── MainLayout.test.tsx    # 3 tests
│   └── utils/__tests__/
│       ├── exportData.test.ts     # 8 tests
│       └── formatters.test.ts     # 20 tests
└── features/                      # 18 files, 127 tests
    ├── ai-recommendations/__tests__/AiRecommendationsPage.test.tsx # 8
    ├── analytics/__tests__/AnalyticsPage.test.tsx # 6
    ├── attack-simulator/__tests__/AttackSimulatorPage.test.tsx # 6
    ├── attack-simulator/__tests__/AttackSimulatorPipeline.test.tsx # 8
    ├── carbon/__tests__/CarbonPage.test.tsx # 5
    ├── dashboard/__tests__/DashboardPage.test.tsx # 7
    ├── energy/__tests__/EnergyPage.test.tsx # 5
    ├── events/__tests__/EventsPage.test.tsx # 7
    ├── optimizer/__tests__/OptimizerPage.test.tsx # 6
    ├── renewable-energy/__tests__/RenewableEnergyPage.test.tsx # 5
    ├── research-lab/__tests__/ExperimentPages.test.tsx # 9
    ├── research-lab/__tests__/ResearchDatasetPage.test.tsx # 7
    ├── research-lab/__tests__/ResearchLabPage.test.tsx # 11
    ├── research-lab/__tests__/ResearchSectionPages.test.tsx # 10
    ├── security/__tests__/SecurityPage.test.tsx # 8
    ├── settings/__tests__/SettingsPage.test.tsx # 7
    ├── system-health/__tests__/SystemHealthPage.test.tsx # 5
    └── threats/__tests__/ThreatsPage.test.tsx # 7
```

### Test Configuration

**Vitest config** (`vite.config.ts`):
- Environment: jsdom
- Globals: enabled
- Setup: `src/test/setup.ts` (imports @testing-library/jest-dom)

**Test utilities** (`src/test/`):
- `page-test-utils.tsx`: Wraps components in BrowserRouter, mocks recharts
- `mocks.ts`: Fetch mocking helpers (mockFetchSuccess, mockFetchFailure)

### Running Frontend Tests

```bash
cd frontend
npm test
```

### Test Patterns

**Page Tests** — Render with mocked fetch, assert on loaded content:
```typescript
describe("DashboardPage", () => {
  it("renders dashboard title after loading", async () => {
    render(<DashboardPage />);
    expect(await screen.findByText(/dashboard/i)).toBeInTheDocument();
  });
});
```

**Component Tests** — Render in isolation, assert on props:
```typescript
describe("Button", () => {
  it("applies primary variant by default", () => {
    render(<Button>Click</Button>);
    expect(screen.getByRole("button")).toHaveClass("bg-blue-600");
  });
});
```

## Test Coverage Summary

### Backend Coverage by Area

| Area | Tests | What's Covered |
|------|-------|----------------|
| API Routes | 169 | All 19 modules, happy path + error cases |
| Threat Detection | 4 | Known/unknown attacks, severity bounds, UUID format |
| Risk Analysis | 4 | Weighted scoring, all severity levels |
| Carbon Calculation | 17 | Formula correctness, edge cases, efficiency |
| Workload Optimizer | 18 | Critical protection, priority sorting, edge cases |
| Recommendation Engine | 11 | All condition branches, required fields |
| Energy Estimation | 12 | Formula correctness, scaling, component breakdown |
| Explainability | 12 | Factor sorting, reasoning generation |
| Service Layer | 381 | All services, mocking, edge cases |
| Research (Phases 1-9) | 503 | Research API, services, repositories, statistics |
| Models/Repositories | 35 | Research repository filters, attribution queries |

### Research Coverage (Phase 14)

Phase 14 closed coverage gaps for research Phases 1-9. The research subset
(503 tests) reaches 100% line coverage on:

- `app/api/research.py`
- `app/engines/energy/hardware_providers.py`
- `app/repositories/research_repo.py`
- `app/services/defense_energy_amplification_service.py`
- `app/services/interaction_effect_service.py`
- `app/services/marginal_energy_service.py`
- `app/services/research_summary_service.py`
- `app/services/research_export_service.py`

And near-100% on `research_analytics_service.py` (99%; remaining lines are
cap/defensive branches) and `statistics.py` (96%; remaining lines are
defensive/numerical edge cases). `research_service.py` pipeline-observation
lines are covered by `test_orchestration_service.py` in the full suite.

### Frontend Coverage by Area

| Area | Tests | What's Covered |
|------|-------|----------------|
| Pages | 127 | Loading states, content rendering, user interactions |
| Shared Components | 89 | Props, variants, states, accessibility |
| Routing | 3 | Route rendering, sidebar, header |
| Utilities | 28 | Date/number formatting, CO2 units, export helpers |
| Layout | 3 | Sidebar, header, outlet rendering |

## What's NOT Tested

- **Database migrations**: Not applicable (SQLite, schema created per test)
- **Authentication/Authorization**: No auth system implemented
- **End-to-end browser tests**: Not implemented (would need Playwright/Cypress)
- **Performance/load tests**: Not implemented
- **Visual regression tests**: Not implemented
- **Backend linter**: No linter configured in the project (no ruff/flake8)
- **Frontend eslint**: `npm run lint` references eslint, but it is not present
  in `devDependencies` (pre-existing; typechecking runs via `npm run build`)
