# Carbon Guard

**AI-Driven Green Cybersecurity and Carbon Optimization Platform**

An academic demonstration project that combines cyber-threat detection with environmental sustainability monitoring. Detects and responds to simulated cyber threats while estimating the environmental cost of security operations and optimizing workloads to reduce carbon emissions.

> **DISCLAIMER**: This is an academic simulation project. All security events, attacks, and monitoring data are synthetic/simulated. No real cyber attacks are performed. No real infrastructure is scanned or controlled. All estimated values are clearly labeled.

## Features

| Feature | Description |
|---------|-------------|
| **Dashboard** | Central overview with carbon guard score, threat level, energy consumption, and AI recommendations |
| **Security Monitoring** | Real-time security event tracking with severity, type, and status filtering |
| **Attack Simulator** | Educational cyber attack simulation with full detection pipeline visualization |
| **Threat Analysis** | Threat classification with risk scoring, AI explanations, and status management |
| **Carbon Monitoring** | CO2 emission estimation from security operations with efficiency metrics |
| **Energy Monitoring** | Power consumption tracking (CPU, memory, network) with history charts |
| **Workload Optimizer** | Carbon-aware scheduling that shifts non-critical workloads to lower-carbon periods |
| **Renewable Energy** | Solar/wind availability tracking with 24-hour forecasting |
| **AI Recommendations** | Rule-based security and sustainability recommendations |
| **Analytics** | Security, carbon, energy, and optimization trend analysis |
| **Research Lab** | Experiment-driven research into the energy and carbon cost of security: marginal energy attribution (Phase 5), control interaction effects (Phase 6), defense energy amplification (Phase 7), statistical analytics (Phase 8), carbon metrics (Phase 10) — every result labeled ESTIMATED/MEASURED/SIMULATED |
| **End-to-End Pipeline** | One orchestrated flow from attack simulation through threat detection, rule-based defense, energy measurement and carbon calculation to optional research recording (Phase 13) |
| **Events Log** | Searchable event log with pagination and filtering |
| **System Health** | Service status monitoring with utilization history |
| **Settings** | Configurable parameters for carbon calculations and optimization |

## Architecture

```
CarbonGuard/
├── frontend/                    # React + TypeScript + Vite
│   ├── src/
│   │   ├── features/            # Feature-based modules
│   │   │   ├── dashboard/       # Dashboard overview
│   │   │   ├── security/        # Security monitoring
│   │   │   ├── attack-simulator/# Attack simulation
│   │   │   ├── threats/         # Threat management
│   │   │   ├── carbon/          # Carbon monitoring
│   │   │   ├── energy/          # Energy monitoring
│   │   │   ├── optimizer/       # Workload optimizer
│   │   │   ├── renewable-energy/# Renewable tracking
│   │   │   ├── ai-recommendations/ # Recommendations
│   │   │   ├── analytics/       # Analytics dashboards
│   │   │   ├── research-lab/    # Research Lab (Phases 9-12)
│   │   │   ├── events/          # Event logs
│   │   │   ├── system-health/   # System monitoring
│   │   │   └── settings/        # Configuration
│   │   ├── shared/              # Reusable components, utils, types
│   │   ├── App.tsx              # Route definitions
│   │   └── main.tsx             # Entry point
│   └── package.json
├── backend/                     # Python + FastAPI
│   ├── app/
│   │   ├── api/                 # API route handlers (thin)
│   │   ├── services/            # Business logic layer
│   │   ├── engines/             # Domain computation
│   │   │   ├── security/        # Threat detection, risk analysis
│   │   │   ├── carbon/          # Carbon calculation
│   │   │   ├── energy/          # Energy provider abstraction (ESTIMATED/MEASURED)
│   │   │   ├── analytics/       # Deterministic research statistics
│   │   │   ├── ai/              # Recommendations, explainability
│   │   │   └── optimizer/       # Workload optimization
│   │   ├── repositories/        # Database CRUD
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── config.py            # Settings
│   │   ├── database.py          # DB connection
│   │   └── main.py              # FastAPI app
│   ├── tests/                   # pytest suite (850 tests)
│   ├── seed.py                  # Database seeder
│   └── requirements.txt
├── docs/                        # Architecture, API, research documentation
├── AGENTS.md                    # Development guidelines
├── README.md
└── .gitignore
```

### Design Principles

- **Thin Routes**: API routes parse requests and call services
- **Service Layer**: Business logic, validation, orchestration
- **Engine Layer**: Domain-specific computation (security, carbon, optimizer)
- **Repository Layer**: Database CRUD operations only
- **No Circular Dependencies**: `main` → `api` → `services` → `repositories` → `models`

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript 5, Vite 5, Tailwind CSS, Recharts |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| Database | SQLite (development), easily migrable to PostgreSQL |
| Testing | pytest (850 backend tests), Vitest + Testing Library (351 frontend tests) |

## Getting Started

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Seed the database with demo data
python seed.py

# Start the server
uvicorn app.main:app --reload --port 8000
```

API available at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

Frontend available at: `http://localhost:5173`

### Running Tests

```bash
# Backend tests (850 tests)
cd backend
python -m pytest tests/ -v

# Frontend tests (351 tests)
cd frontend
npm test

# Frontend production build (type check + bundle)
cd frontend
npm run build
```

## Frontend Routes

| Route | Page | Description |
|-------|------|-------------|
| `/` | Dashboard | Central overview with key metrics |
| `/security` | Security Monitor | Security event monitoring and analysis |
| `/attack-simulator` | Attack Simulator | Educational attack simulation |
| `/threats` | Threats | Threat management with AI explanations |
| `/carbon` | Carbon Monitor | CO2 emission tracking |
| `/energy` | Energy Monitor | Power consumption monitoring |
| `/optimizer` | Workload Optimizer | Carbon-aware workload scheduling |
| `/renewable-energy` | Renewable Energy | Solar/wind availability tracking |
| `/ai-recommendations` | AI Recommendations | Security and sustainability suggestions |
| `/analytics` | Analytics | Trend analysis across all metrics |
| `/research-lab` | Research Lab | Experiment-driven energy/carbon research overview |
| `/research-lab/marginal-energy` | Marginal Energy | Phase 5 attack-conditioned energy attribution |
| `/research-lab/interaction-analysis` | Interaction Analysis | Phase 6 security-control interaction effects |
| `/research-lab/defense-amplification` | Defense Amplification | Phase 7 defense energy cost analysis |
| `/research-lab/experiments` | Experiments | Experiment list and runner |
| `/research-lab/experiments/:id` | Experiment Detail | Runs, measurements, and trial details |
| `/research-lab/dataset` | Research Dataset | Searchable dataset of persisted research results |
| `/events` | Event Logs | Searchable security event log |
| `/system-health` | System Health | Platform component status |
| `/settings` | Settings | Configuration management |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/dashboard` | GET | Dashboard metrics |
| `/api/v1/dashboard/charts/threat-activity` | GET | Threat activity chart data |
| `/api/v1/dashboard/charts/carbon-emissions` | GET | Carbon emissions chart data |
| `/api/v1/dashboard/charts/carbon-savings` | GET | Carbon savings chart data |
| `/api/v1/dashboard/charts/threat-categories` | GET | Threat categories chart data |
| `/api/v1/security/events` | GET | Security events list |
| `/api/v1/security/stats` | GET | Security statistics |
| `/api/v1/simulator/attack-types` | GET | Available attack types |
| `/api/v1/simulator/simulate` | POST | Run attack simulation |
| `/api/v1/threats` | GET | Threat list |
| `/api/v1/threats/stats` | GET | Threat statistics |
| `/api/v1/threats/{id}` | GET | Threat details |
| `/api/v1/threats/{id}/status` | PATCH | Update threat status |
| `/api/v1/threats/{id}/explanation` | GET | AI explanation |
| `/api/v1/carbon` | GET | Carbon overview |
| `/api/v1/carbon/current` | GET | Current carbon metrics |
| `/api/v1/carbon/efficiency` | GET | Carbon efficiency |
| `/api/v1/energy` | GET | Energy overview |
| `/api/v1/energy/current` | GET | Current energy metrics |
| `/api/v1/optimizer/workloads` | GET | Workload list |
| `/api/v1/optimizer/run` | POST | Run optimization |
| `/api/v1/optimizer/history` | GET | Optimization history |
| `/api/v1/optimizer/comparison` | GET | Before/after comparison |
| `/api/v1/renewable-energy` | GET | Renewable energy status |
| `/api/v1/recommendations` | GET | AI recommendations |
| `/api/v1/recommendations/generate` | POST | Generate new recommendations |
| `/api/v1/recommendations/{id}/read` | PATCH | Mark as read |
| `/api/v1/recommendations/{id}/dismiss` | PATCH | Dismiss recommendation |
| `/api/v1/analytics/security` | GET | Security analytics |
| `/api/v1/analytics/carbon` | GET | Carbon analytics |
| `/api/v1/analytics/energy` | GET | Energy analytics |
| `/api/v1/analytics/optimization` | GET | Optimization analytics |
| `/api/v1/orchestration/run` | POST | End-to-end pipeline: simulate → detect → defense → energy → carbon → optional research recording (Phase 13) |
| `/api/v1/research/*` | GET/POST | Research Lab: experiments, marginal energy, interaction effects, defense amplification, analytics, summary, metrics, export (see API Reference) |
| `/api/v1/events` | GET | Event log |
| `/api/v1/system-health` | GET | System health |
| `/api/v1/system-health/history` | GET | System health history |
| `/api/v1/settings` | GET | System settings |
| `/api/v1/settings` | PUT | Update setting |
| `/api/v1/settings/reset` | POST | Reset to defaults |

## Carbon Calculation

```
Energy Consumption (kWh) x Carbon Intensity (gCO2/kWh) = Gross CO2 (gCO2)
Gross CO2 x (Renewable % / 100) = Renewable Offset (gCO2)
Gross CO2 - Renewable Offset = Net CO2 (gCO2)
```

## Optimization Rules

1. Critical security tasks are **NEVER** delayed for carbon savings
2. Non-critical tasks may be shifted to lower-carbon periods
3. Shift window is limited (max 4 hours by default)
4. Minimum savings threshold must be met to justify shifting

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System architecture, data flow, and component diagrams |
| [API Reference](docs/api-reference.md) | Complete API endpoint documentation with examples |
| [Developer Guide](docs/developer-guide.md) | Setup instructions, environment config, development workflow |
| [Deployment](docs/deployment.md) | Docker configuration and deployment instructions |
| [Database Schema](docs/database.md) | Table definitions and entity relationships (incl. research tables) |
| [Testing](docs/testing.md) | Test strategy, structure, and coverage details |
| [Research Architecture](docs/RESEARCH_ARCHITECTURE.md) | Research system design and implementation phase roadmap |
| [Research Methodology](docs/RESEARCH_METHODOLOGY.md) | Research formulas, provenance rules, and statistical methods |
| [Experiment Protocol](docs/EXPERIMENT_PROTOCOL.md) | Experiment execution protocol, comparability, and validity rules |
| [Energy Measurement](docs/ENERGY_MEASUREMENT.md) | Energy provider abstraction and measurement modes |
| [Attack Profiles](docs/ATTACK_PROFILES.md) | Attack types, intensity levels, and workload definitions |
| [Pipeline](docs/PIPELINE.md) | End-to-end CarbonGuard orchestration flow (Phase 13) |

## License

Academic project for demonstration purposes.
