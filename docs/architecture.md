# Architecture

This document describes the actual architecture of the CarbonGuard platform as implemented.

> **Note**: All data in this system is **simulated/synthetic**. No real cyber attacks are performed, no real infrastructure is scanned, and all energy/carbon values are estimated using calculation models.

## High-Level Overview

```mermaid
graph TB
    subgraph Frontend["Frontend (React + TypeScript)"]
        UI[React UI Components]
        API_CLIENT[API Client Layer]
    end

    subgraph Backend["Backend (Python + FastAPI)"]
        ROUTES[API Routes - Thin]
        SERVICES[Service Layer]
        ENGINES[Engine Layer]
        REPOS[Repository Layer]
    end

    subgraph Database["Database"]
        SQLITE[(SQLite)]
    end

    UI --> API_CLIENT
    API_CLIENT -->|"HTTP/REST"| ROUTES
    ROUTES --> SERVICES
    SERVICES --> ENGINES
    SERVICES --> REPOS
    REPOS --> SQLITE
```

## Backend Architecture

The backend follows a strict layered architecture with no circular dependencies:

```
main.py → api/ → services/ → repositories/ → models/
                     ↓
                  engines/
```

### Layer Responsibilities

| Layer | Location | Responsibility |
|-------|----------|---------------|
| **API Routes** | `app/api/` | Parse HTTP requests, validate input, call services, return responses. No business logic. |
| **Services** | `app/services/` | Business logic, validation, orchestration. Coordinates between repos and engines. |
| **Engines** | `app/engines/` | Domain-specific computation. Pure functions/classes with no DB dependency. |
| **Repositories** | `app/repositories/` | Database CRUD operations. Wraps SQLAlchemy queries. |
| **Models** | `app/models/` | SQLAlchemy ORM model definitions. |
| **Schemas** | `app/schemas/` | Pydantic models for API request/response validation. |

### Backend Module Map

```mermaid
graph LR
    subgraph API["API Routes (15 modules)"]
        A1[dashboard]
        A2[security]
        A3[attack_simulator]
        A4[threats]
        A5[carbon]
        A6[energy]
        A7[optimizer]
        A8[renewable_energy]
        A9[recommendations]
        A10[analytics]
        A11[events]
        A12[system_health]
        A13[settings]
        A14[research]
        A15[orchestration]
    end

    subgraph Services["Services (17 classes)"]
        S1[DashboardService]
        S2[SecurityService]
        S3[CarbonService]
        S4[EnergyService]
        S5[OptimizerService]
        S6[AIService]
        S7[SystemService]
        S8[AnalyticsService]
        S9[renewable_service]
        S10[ResearchExperimentService]
        S11[orchestration_service]
        S12[marginal_energy_service]
        S13[interaction_effect_service]
        S14[defense_energy_amplification_service]
        S15[research_analytics_service]
        S16[research_summary_service]
        S17[research_export_service]
    end

    subgraph Engines["Engines (6 modules)"]
        E1[threat_detector]
        E2[risk_analyzer]
        E3[attack_simulator]
        E4[carbon_calculator]
        E5[energy_estimator]
        E6[workload_optimizer]
        E7[recommendation_engine]
        E8[explainability]
        E9[energy_providers]
        E10[statistics]
    end

    A1 --> S1
    A2 --> S2
    A3 --> S2
    A4 --> S2
    A5 --> S3
    A6 --> S4
    A7 --> S5
    A8 --> S9
    A9 --> S6
    A10 --> S8
    A12 --> S7
    A13 --> S7
    A14 --> S10
    A14 --> S12
    A14 --> S13
    A14 --> S14
    A14 --> S15
    A14 --> S16
    A14 --> S17
    A15 --> S11
    S11 --> S10

    S2 --> E1
    S2 --> E2
    S2 --> E3
    S3 --> E4
    S4 --> E5
    S5 --> E6
    S6 --> E7
    S10 --> E9
    S15 --> E10
```

### Key Engine Functions

| Engine | Functions | Purpose |
|--------|-----------|---------|
| `threat_detector` | `detect_event()`, `classify_severity()`, `generate_event_uuid()` | Detects and classifies simulated threats |
| `risk_analyzer` | `analyze_risk()` | Calculates weighted risk scores from 5 factors |
| `attack_simulator` | `simulate_attack()` | Full pipeline: detect → risk → carbon → recommendation |
| `carbon_calculator` | `calculate_carbon()`, `calculate_security_carbon_efficiency()`, `estimate_workload_energy()` | Core carbon formulas |
| `energy_estimator` | `estimate_energy_consumption()`, `estimate_security_workload_energy()` | Power/energy estimation models |
| `workload_optimizer` | `optimize_workloads()`, `generate_sample_workloads()` | Carbon-aware scheduling |
| `recommendation_engine` | `generate_recommendations()` | Rule-based multi-factor recommendations |
| `explainability` | `explain_prediction()`, `explain_recommendation()` | Human-readable explanation generation |
| `energy providers` | `get_provider()`, `get_measurement()` | ESTIMATED/MEASURED energy provider abstraction used by Phases 5-7 |
| `statistics` | `descriptive_statistics()`, `confidence_interval_t()`, `paired_t_test()`, `wilcoxon_signed_rank()`, `cohens_dz()` | Deterministic research statistics (Phase 8) |

## Frontend Architecture

The frontend uses a feature-based organization with shared components:

```mermaid
graph TB
    subgraph Features["Feature Modules (14)"]
        F1[dashboard]
        F2[security]
        F3[attack-simulator]
        F4[threats]
        F5[carbon]
        F6[energy]
        F7[optimizer]
        F8[renewable-energy]
        F9[ai-recommendations]
        F10[analytics]
        F11[research-lab]
        F12[events]
        F13[system-health]
        F14[settings]
    end

    subgraph Shared["Shared Layer"]
        UI[UI Components]
        HOOKS[Custom Hooks]
        UTILS[Utilities]
        TYPES[TypeScript Types]
    end

    subgraph Entry["Entry Points"]
        APP[App.tsx - Router]
        MAIN[main.tsx]
    end

    MAIN --> APP
    APP --> Features
    Features --> Shared
```

The `research-lab` module hosts the seven Research Lab routes (overview,
marginal energy, interaction analysis, defense amplification, experiments,
experiment detail, dataset) — Phases 9-12. See
[RESEARCH_ARCHITECTURE.md](RESEARCH_ARCHITECTURE.md).

### Shared UI Components (14)

| Component | Purpose |
|-----------|---------|
| `Button` | Configurable button with variants (primary, secondary, danger, ghost) |
| `Card`, `CardHeader`, `CardContent`, `CardTitle` | Card layout primitives |
| `Badge`, `SeverityBadge`, `StatusBadge` | Status and severity indicators |
| `StatusIndicator` | Online/offline/degraded status display |
| `MetricCard` | Metric display with title, value, trend |
| `StatCard` | Statistics card with trend direction |
| `PageHeader` | Page title with subtitle, badge, and actions |
| `LoadingSpinner` | Loading state indicator |
| `ChartContainer` | Chart wrapper with title |
| `DataTable` | Generic table with columns and empty state |
| `ThreatLevel` | Threat level indicator with animated dot |
| `Header` | Top navigation bar |
| `Sidebar` | Side navigation with collapsible menu |

### Frontend Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant C as React Component
    participant AC as apiClient
    participant API as FastAPI Backend
    participant DB as SQLite

    U->>C: Interacts with UI
    C->>AC: Calls API function
    AC->>API: HTTP request (fetch)
    API->>API: Route → Service → Engine/Repo
    Repo->>DB: Query
    DB-->>Repo: Result
    Repo-->>Service: Model
    Service-->>API: Response dict
    API-->>AC: JSON response
    AC-->>C: Typed data
    C-->>U: Renders updated UI
```

## Data Flow: Security Event Simulation

The attack simulation demonstrates the full pipeline:

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant API as /simulator/simulate
    participant SIM as attack_simulator engine
    participant DET as threat_detector
    participant RISK as risk_analyzer
    participant CARB as carbon_calculator
    participant DB as Database

    U->>FE: Click "Simulate" on attack type
    FE->>API: POST /api/v1/simulator/simulate
    API->>SIM: simulate_attack(attack_type)
    SIM->>DET: detect_event({attack_type})
    DET-->>SIM: detection result
    SIM->>RISK: analyze_risk(severity, confidence, ...)
    RISK-->>SIM: risk assessment
    SIM->>CARB: calculate_carbon(energy_kwh)
    CARB-->>SIM: carbon impact
    SIM-->>API: Full simulation result
    API->>DB: Store event + threat
    API-->>FE: JSON response
    FE-->>U: Display pipeline + results
```

## Data Flow: End-to-End CarbonGuard Pipeline (Phase 13)

`POST /api/v1/orchestration/run` extends the simulation flow above into the
complete lifecycle: attack → threat → risk → rule-based defense controls →
energy measurement (provider abstraction) → carbon calculation → optional
research observation → analytics feeds. It orchestrates the existing engines
and services without adding duplicate formulas or storage.

See [PIPELINE.md](PIPELINE.md) for the component mapping, provenance rules
(energy measurement mode, carbon basis), failure handling and the response
schema.

## Carbon Calculation Formula

```
Energy (kWh) × Carbon Intensity (gCO2/kWh) = Gross CO2 (gCO2)
Gross CO2 × (Renewable % / 100) = Renewable Offset (gCO2)
Gross CO2 - Renewable Offset = Net CO2 (gCO2)
```

Default values: `carbon_intensity = 475 gCO2/kWh`, `renewable_percentage = 25%`

## Workload Optimization Rules

1. Critical security tasks are **NEVER** delayed for carbon savings
2. Non-critical tasks may be shifted to lower-carbon periods
3. Shift window is limited to `MAX_DELAY_HOURS` (default: 4 hours)
4. Minimum savings threshold must be met to justify shifting
5. Non-critical tasks are sorted by priority (high → medium → low) before shifting

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend Framework | React | 18.3.1 |
| Frontend Language | TypeScript | 5.4.5 |
| Build Tool | Vite | 5.4.2 |
| CSS Framework | Tailwind CSS | 3.4.4 |
| Charting | Recharts | 2.12.7 |
| Routing | React Router | 6.23.1 |
| Backend Framework | FastAPI | 0.115+ |
| Backend Language | Python | 3.12 |
| ORM | SQLAlchemy | 2.0+ |
| Validation | Pydantic | 2.10+ |
| Database | SQLite | — |
| Backend Testing | pytest | 9.1.1 |
| Frontend Testing | Vitest | 4.1.11 |
| Containerization | Docker | — |
| CI/CD | GitHub Actions | — |
