# Testing Strategy

This document describes the testing approach for both backend and frontend.

## Overview

| Layer | Framework | Tests | Coverage |
|-------|-----------|-------|----------|
| Backend API | pytest | 46 | All 13 route modules |
| Backend Engines | pytest | 64 | 8 engine modules |
| Backend Services | pytest | 77 | 9 service classes |
| Frontend Pages | Vitest | 57 | All 13 feature pages |
| Frontend Components | Vitest | 116 | 14 shared UI components |
| Frontend Utilities | Vitest | 14 | Formatters, routing, layout |
| **Total** | | **374** | |

## Backend Testing

### Test Structure

```
backend/tests/
├── conftest.py                    # Shared fixtures (client, db, setup_database)
├── test_api/                      # API integration tests
│   ├── test_dashboard.py          # 9 tests
│   ├── test_security.py           # 4 tests
│   ├── test_threats.py            # 5 tests
│   ├── test_carbon.py             # 4 tests
│   ├── test_energy.py             # 3 tests
│   ├── test_optimizer.py          # 4 tests
│   ├── test_recommendations.py    # 5 tests
│   ├── test_renewable.py          # 5 tests
│   ├── test_analytics.py          # 4 tests
│   ├── test_system_health.py      # 2 tests
│   └── (10 files total)
├── test_engines/                  # Engine unit tests
│   ├── test_threat_detector.py    # 4 tests
│   ├── test_risk_analyzer.py      # 4 tests
│   ├── test_carbon_calculator.py  # 4 tests
│   ├── test_workload_optimizer.py # 18 tests
│   ├── test_recommendation_engine.py # 11 tests
│   ├── test_energy_estimator.py   # 12 tests
│   └── test_explainability.py     # 12 tests
└── test_services/                 # Service unit tests
    ├── test_ai_service.py         # 12 tests
    ├── test_analytics_service.py  # 15 tests
    ├── test_carbon_service.py     # 9 tests
    ├── test_dashboard_service.py  # 9 tests
    ├── test_energy_service.py     # 7 tests
    ├── test_renewable_service.py  # 7 tests
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

**Service Tests** — Unit tests with mocked repositories:
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
│   ├── ui/__tests__/              # Component tests (116 tests)
│   │   ├── Button.test.tsx
│   │   ├── Card.test.tsx
│   │   ├── Badge.test.tsx
│   │   ├── DataTable.test.tsx
│   │   ├── Header.test.tsx
│   │   ├── Sidebar.test.tsx
│   │   ├── MetricCard.test.tsx
│   │   ├── StatCard.test.tsx
│   │   ├── StatusIndicator.test.tsx
│   │   ├── PageHeader.test.tsx
│   │   ├── LoadingSpinner.test.tsx
│   │   ├── ChartContainer.test.tsx
│   │   └── ThreatLevel.test.tsx
│   ├── layouts/__tests__/
│   │   └── MainLayout.test.tsx    # Layout test (3 tests)
│   └── utils/__tests__/
│       └── formatters.test.ts     # Utility tests (14 tests)
└── features/
    ├── dashboard/__tests__/DashboardPage.test.tsx
    ├── security/__tests__/SecurityPage.test.tsx
    ├── attack-simulator/__tests__/AttackSimulatorPage.test.tsx
    ├── threats/__tests__/ThreatsPage.test.tsx
    ├── carbon/__tests__/CarbonPage.test.tsx
    ├── energy/__tests__/EnergyPage.test.tsx
    ├── optimizer/__tests__/OptimizerPage.test.tsx
    ├── renewable-energy/__tests__/RenewableEnergyPage.test.tsx
    ├── ai-recommendations/__tests__/AiRecommendationsPage.test.tsx
    ├── analytics/__tests__/AnalyticsPage.test.tsx
    ├── events/__tests__/EventsPage.test.tsx
    ├── system-health/__tests__/SystemHealthPage.test.tsx
    └── settings/__tests__/SettingsPage.test.tsx
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
| API Routes | 46 | All 13 modules, happy path + error cases |
| Threat Detection | 4 | Known/unknown attacks, severity bounds, UUID format |
| Risk Analysis | 4 | Weighted scoring, all severity levels |
| Carbon Calculation | 4 | Formula correctness, edge cases, efficiency |
| Workload Optimizer | 18 | Critical protection, priority sorting, edge cases |
| Recommendation Engine | 10 | All condition branches, required fields |
| Energy Estimation | 12 | Formula correctness, scaling, component breakdown |
| Explainability | 12 | Factor sorting, reasoning generation |
| Service Layer | 77 | All 9 services, mocking, edge cases |

### Frontend Coverage by Area

| Area | Tests | What's Covered |
|------|-------|----------------|
| Pages | 57 | Loading states, content rendering, user interactions |
| Shared Components | 116 | Props, variants, states, accessibility |
| Routing | 3 | Route rendering, sidebar, header |
| Utilities | 14 | Date formatting, number formatting, energy units |
| Layout | 3 | Sidebar, header, outlet rendering |

## What's NOT Tested

- **Repository layer**: Tested indirectly through API tests
- **Database migrations**: Not applicable (SQLite, schema created per test)
- **Authentication/Authorization**: No auth system implemented
- **End-to-end browser tests**: Not implemented (would need Playwright/Cypress)
- **Performance/load tests**: Not implemented
- **Visual regression tests**: Not implemented
