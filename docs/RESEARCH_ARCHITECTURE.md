# CarbonGuard Research Architecture

## Document Status

- **Version**: 1.0
- **Date**: 2026-09-30
- **Status**: Audit Complete — Pre-Implementation

---

## 1. Research Problem

The energy cost of cybersecurity is not constant. It depends on attack intensity, workload, security-control configuration, and interactions between multiple security controls. Current cybersecurity energy accounting treats security overhead as a fixed cost, which leads to inaccurate carbon footprint estimates and suboptimal security resource allocation.

### Research Questions

| ID | Question |
|----|----------|
| RQ1 | How does the marginal energy consumption of individual cybersecurity controls change with attack intensity and legitimate workload? |
| RQ2 | Are the energy costs of combined cybersecurity controls additive, sub-additive, or super-additive under different attack conditions? |
| RQ3 | Does attack intensity produce disproportionate increases in defensive energy consumption? |
| RQ4 | Can attack-conditioned energy measurements support adaptive security configurations while maintaining a required security effectiveness threshold? |

### Hypotheses

| ID | Hypothesis |
|----|-----------|
| H1 | The marginal energy cost of cybersecurity controls varies with attack intensity and workload. |
| H2 | The energy cost of combined security controls is not always equal to the sum of their individual energy costs. |
| H3 | Some attack/control combinations produce disproportionate defensive energy consumption. |
| H4 | Attack-conditioned energy measurements can help identify security configurations that maintain required security effectiveness with lower energy overhead. |

**Status**: These hypotheses are unproven. The software provides experimental evidence for later evaluation.

---

## 2. Current Architecture Audit

### 2.1 Project Structure

```
Carbon_1/
├── backend/          Python FastAPI (SQLAlchemy + SQLite)
├── frontend/         React 18 + TypeScript 5 + Tailwind CSS
├── docs/             Documentation
├── docker-compose.yml
└── .github/workflows/ci.yml
```

### 2.2 Backend Architecture

**Layered architecture**: API → Service → Repository/Engine

| Layer | Location | Pattern |
|-------|----------|---------|
| API Routes | `app/api/*.py` | Thin handlers, parse requests, call services |
| Services | `app/services/*.py` | Business logic, orchestration |
| Repositories | `app/repositories/*.py` | Generic CRUD via SQLAlchemy |
| Engines | `app/engines/` | Stateless pure-function computation |
| Models | `app/models/*.py` | SQLAlchemy ORM |
| Schemas | `app/schemas/*.py` | Pydantic validation (largely unused in routes) |

**Database**: SQLite via SQLAlchemy 2.0, schema created via `create_all()` (no Alembic).

**Config**: pydantic-settings loading from `.env`.

### 2.3 Current Database Models

| Model | Table | Fields | Purpose |
|-------|-------|--------|---------|
| `SecurityEvent` | `security_events` | 17 columns | Security event log |
| `Threat` | `threats` | 13 columns | Active threats (FK→security_events) |
| `CarbonMetric` | `carbon_metrics` | 11 columns | Hourly carbon snapshots |
| `EnergyMetric` | `energy_metrics` | 7 columns | Hourly energy readings |
| `Workload` | `workloads` | 14 columns | Scheduled computational tasks |
| `OptimizationResult` | `optimization_results` | 13 columns | Optimizer run results |
| `AIRecommendation` | `ai_recommendations` | 11 columns | Rule-based suggestions |
| `SystemMetric` | `system_metrics` | 10 columns | System health snapshots |
| `SystemSetting` | `system_settings` | 4 columns | Key-value config |

**Only relationship**: `SecurityEvent (1) → (N) Threat` via `event_id` FK.

### 2.4 Current API Endpoints (~40)

All under `/api/v1/`:

| Domain | Endpoints | Notes |
|--------|-----------|-------|
| Dashboard | 7 | Metrics + 6 chart data |
| Security | 3 | Events list, single, stats |
| Simulator | 2 | `POST /simulate`, `GET /attack-types` |
| Threats | 5 | CRUD + explanation |
| Carbon | 4 | Overview, current, history, efficiency |
| Energy | 3 | Overview, current, history |
| Optimizer | 4 | Workloads, run, history, comparison |
| Renewable | 2 | Status, forecast |
| Recommendations | 4 | List, generate, read, dismiss |
| Analytics | 4 | Security, carbon, energy, optimization |
| Events | 1 | Filtered list |
| System Health | 2 | Current, history |
| Settings | 3 | List, update, reset (stub) |

### 2.5 Current Attack Simulation

**6 attack types**: ddos, brute_force, port_scan, sql_injection, malware, suspicious_login

**Pipeline** (9 steps):
1. Validate attack type
2. Detect event (random confidence/severity from profile ranges)
3. Analyze risk (weighted 5-factor score)
4. Calculate carbon impact (from estimated energy)
5. Generate recommendation (rule-based, per attack type)
6. Build pipeline trace
7. Return result
8. Persist event + threat to DB
9. Frontend displays breakdown

**Limitations for research**:
- All values randomized — no reproducibility
- No attack intensity parameter (LOW/MEDIUM/HIGH)
- No batch simulation
- No security control configuration
- No baseline comparison
- No energy measurement abstraction
- Energy from `ATTACK_PROFILES[attack_type]["energy_range"]` — arbitrary random range

### 2.6 Current Energy/Carbon Calculation

**Energy**: 100% simulated/random. `energy_estimator.py` generates random watt values for CPU, memory, network, base power. No real hardware measurement.

**Carbon formula** (correct):
```
gross_co2_g = energy_kwh × carbon_intensity (default 475 gCO2/kWh)
net_co2_kg = gross_co2_kg × (1 - renewable%/100)
```

**Dashboard/Analytics**: Many metrics use `random.uniform()` — not connected to stored data.

**Labels**: Energy values correctly marked `estimated: True` and `simulated: True`.

### 2.7 Current Frontend

**13 feature pages**, flat routing under `MainLayout`:

| Page | Description |
|------|-------------|
| Dashboard | 8 metric cards, charts, recommendations |
| Security Monitor | Event monitoring, severity breakdown |
| Attack Simulator | 6 attack type cards, one-click simulation |
| Threats | Threat management, AI explanations |
| Carbon Monitor | Carbon metrics, efficiency gauge |
| Energy Monitor | Power breakdown, consumption history |
| Optimizer | Workload optimization, before/after |
| Renewable Energy | Solar/wind, forecasts |
| AI Recommendations | Rule-based suggestions |
| Analytics | 4-tab analytics |
| Events | Paginated event log |
| System Health | Service status |
| Settings | Key-value editor |

**API layer**: `fetchWithFallback()` pattern — tries real API (3s timeout), falls back to mock data.

**Theme**: All-green dark cybersecurity aesthetic (`#03150F` background, `#00C878` accent).

### 2.8 Current Tests

**Backend** (26 files): 10 API, 9 service, 7 engine tests. Uses pytest + SQLite test DB.

**Frontend** (30 files): 1 App, 13 page, 13 UI component, 1 layout, 2 util tests. Uses Vitest + Testing Library.

### 2.9 Identified Problems

| # | Problem | Severity |
|---|---------|----------|
| 1 | `schemas/common.py` missing `datetime` import | Bug |
| 2 | Dashboard generates random data, not connected to DB | Architecture |
| 3 | Analytics entirely random, no DB queries | Architecture |
| 4 | Duplicate event endpoints (`/security/events` and `/events`) | Duplicate |
| 5 | Pydantic schemas defined but routes return raw dicts | Architecture |
| 6 | No authentication | Security |
| 7 | No database migrations | Architecture |
| 8 | Two HTTP client patterns (api.ts vs apiClient.ts) | Inconsistency |
| 9 | Unused shared hooks (useApi, usePolling, useLocalStorage) | Dead code |
| 10 | Unused shared UI components (DataTable, StatCard, etc.) | Dead code |
| 11 | `global_exception_handler` defined but never registered | Bug |
| 12 | `estimate_workload_energy()` defined but never called | Dead code |
| 13 | Non-deterministic optimizer (random shift decisions) | Reproducibility |
| 14 | Settings reset endpoint is a stub | Incomplete |
| 15 | Search bar and notification bell are visual-only | Incomplete |
| 16 | No 404 catch-all route | Missing |
| 17 | Empty `src/app/` directory | Dead code |
| 18 | Empty feature-level `api/`, `hooks/`, `types/` dirs | Scaffold |

---

## 3. Proposed Research Architecture

### 3.1 Design Principles

1. **Backward compatibility**: All existing functionality preserved
2. **Research extension**: New capabilities extend, not replace
3. **Measurement honesty**: MEASURED / ESTIMATED / SIMULATED always visible
4. **Reproducibility**: Every experiment recordable and repeatable
5. **Configurability**: No hardcoded research values
6. **Modularity**: Energy provider, attack profiles, controls are pluggable
7. **Clean separation**: Engines compute, services orchestrate, APIs expose

### 3.2 New Backend Modules

```
backend/app/
├── engines/
│   ├── carbon/
│   │   ├── carbon_calculator.py          (existing — extend)
│   │   └── energy_estimator.py           (existing — refactor)
│   ├── security/
│   │   ├── threat_detector.py            (existing — extend)
│   │   ├── risk_analyzer.py              (existing — keep)
│   │   └── attack_simulator.py           (existing — extend)
│   ├── optimizer/
│   │   └── workload_optimizer.py         (existing — keep)
│   ├── ai/
│   │   ├── recommendation_engine.py      (existing — keep)
│   │   └── explainability.py             (existing — keep)
│   └── research/                         (NEW)
│       ├── __init__.py
│       ├── energy_provider.py            Energy measurement abstraction
│       ├── marginal_energy.py            Marginal energy attribution engine (implemented as services/marginal_energy_service.py)
│       ├── interaction_engine.py         Security control interaction analysis
│       ├── amplification_engine.py       Defense energy amplification
│       ├── experiment_engine.py          Experiment orchestration
│       ├── statistics.py                 Statistical analysis utilities
│       └── attack_profiles.py            Extended attack profiles with intensity
├── models/
│   ├── research.py                       (NEW) Research experiment models
│   └── ... (existing models unchanged)
├── schemas/
│   ├── research.py                       (NEW) Research DTOs
│   └── ... (existing schemas unchanged)
├── services/
│   ├── research_service.py               (NEW) Research orchestration
│   └── ... (existing services unchanged)
├── repositories/
│   ├── research_repo.py                  (NEW) Research data access
│   └── ... (existing repos unchanged)
└── api/
    ├── research.py                       (NEW) Research API endpoints
    └── ... (existing routes unchanged)
```

### 3.3 New Database Models

```python
# app/models/research.py

class Experiment(Base):
    """Container for a research experiment with multiple runs."""
    __tablename__ = "experiments"
    
    id                  = Column(Integer, primary_key=True, index=True)
    experiment_uuid     = Column(String(36), unique=True, index=True, nullable=False)
    name                = Column(String(200), nullable=False)
    description         = Column(Text, nullable=True)
    experiment_type     = Column(String(50), index=True, nullable=False)
        # "marginal_energy" | "interaction" | "amplification"
    attack_type         = Column(String(50), nullable=False)
    attack_intensity    = Column(String(20), nullable=False)  # LOW | MEDIUM | HIGH | numeric
    workload_profile    = Column(String(100), nullable=True)
    security_controls   = Column(Text, nullable=True)  # JSON array of control IDs
    measurement_mode    = Column(String(20), nullable=False, default="ESTIMATED")
        # MEASURED | ESTIMATED | SIMULATED
    duration_seconds    = Column(Float, nullable=False, default=60.0)
    carbon_intensity    = Column(Float, nullable=True)
    renewable_pct       = Column(Float, nullable=True)
    environment_info    = Column(Text, nullable=True)  # JSON
    software_version    = Column(String(50), nullable=True)
    configuration_version = Column(String(50), nullable=True)
    random_seed         = Column(Integer, nullable=True)
    status              = Column(String(20), nullable=False, default="created")
        # created | running | completed | failed
    created_at          = Column(DateTime, nullable=False, default=_utcnow)
    completed_at        = Column(DateTime, nullable=True)
    notes               = Column(Text, nullable=True)


class ExperimentRun(Base):
    """A single trial/run within an experiment."""
    __tablename__ = "experiment_runs"
    
    id                  = Column(Integer, primary_key=True, index=True)
    run_uuid            = Column(String(36), unique=True, index=True, nullable=False)
    experiment_id       = Column(Integer, ForeignKey("experiments.id"), index=True, nullable=False)
    trial_number        = Column(Integer, nullable=False, default=1)
    attack_type         = Column(String(50), nullable=False)
    attack_intensity    = Column(String(20), nullable=False)
    attack_parameters   = Column(Text, nullable=True)  # JSON
    workload_profile    = Column(String(100), nullable=True)
    security_controls   = Column(Text, nullable=True)  # JSON array
    control_count       = Column(Integer, nullable=False, default=0)
    measurement_mode    = Column(String(20), nullable=False, default="ESTIMATED")
    start_time          = Column(DateTime, nullable=False, default=_utcnow)
    end_time            = Column(DateTime, nullable=True)
    duration_seconds    = Column(Float, nullable=True)
    status              = Column(String(20), nullable=False, default="running")
        # running | completed | failed
    error_message       = Column(Text, nullable=True)
    
    # Relationships
    measurements        = relationship("EnergyMeasurement", back_populates="run")
    security_effects    = relationship("SecurityEffectiveness", back_populates="run")
    research_metrics    = relationship("ResearchMetric", back_populates="run")
    
    experiment          = relationship("Experiment", backref="runs")


class EnergyMeasurement(Base):
    """Energy measurement for a single run."""
    __tablename__ = "energy_measurements"
    
    id                  = Column(Integer, primary_key=True, index=True)
    run_id              = Column(Integer, ForeignKey("experiment_runs.id"), index=True, nullable=False)
    energy_joules       = Column(Float, nullable=False)
    power_watts         = Column(Float, nullable=True)
    duration_seconds    = Column(Float, nullable=False)
    cpu_usage_pct       = Column(Float, nullable=True)
    memory_usage_pct    = Column(Float, nullable=True)
    network_usage_mbps  = Column(Float, nullable=True)
    source              = Column(String(50), nullable=False, default="estimated")
        # "estimated" | "rapl" | "kepler" | "external_meter" | "synthetic"
    measurement_mode    = Column(String(20), nullable=False, default="ESTIMATED")
    timestamp           = Column(DateTime, nullable=False, default=_utcnow)
    
    run                 = relationship("ExperimentRun", back_populates="measurements")


class SecurityEffectiveness(Base):
    """Security effectiveness measurement for a run."""
    __tablename__ = "security_effectiveness"
    
    id                  = Column(Integer, primary_key=True, index=True)
    run_id              = Column(Integer, ForeignKey("experiment_runs.id"), index=True, nullable=False)
    detection_rate      = Column(Float, nullable=True)       # 0.0 - 1.0
    detection_latency_ms = Column(Float, nullable=True)
    false_positive_rate = Column(Float, nullable=True)       # 0.0 - 1.0
    mitigation_time_ms  = Column(Float, nullable=True)
    security_score      = Column(Float, nullable=True)       # 0 - 100
    controls_active     = Column(Text, nullable=True)        # JSON array
    controls_config     = Column(Text, nullable=True)        # JSON config
    
    run                 = relationship("ExperimentRun", back_populates="security_effects")


class ResearchMetric(Base):
    """Named metric computed from an experiment run."""
    __tablename__ = "research_metrics"
    
    id                  = Column(Integer, primary_key=True, index=True)
    run_id              = Column(Integer, ForeignKey("experiment_runs.id"), index=True, nullable=False)
    metric_name         = Column(String(100), nullable=False)  # e.g. "marginal_energy_joules"
    metric_value        = Column(Float, nullable=False)
    unit                = Column(String(50), nullable=False)   # e.g. "joules", "watts", "ratio"
    formula_version     = Column(String(50), nullable=True)
    measurement_mode    = Column(String(20), nullable=True)
    confidence_interval_lower = Column(Float, nullable=True)
    confidence_interval_upper = Column(Float, nullable=True)
    notes               = Column(Text, nullable=True)
    
    run                 = relationship("ExperimentRun", back_populates="research_metrics")


class InteractionResult(Base):
    """Pre-computed interaction analysis result."""
    __tablename__ = "interaction_results"
    
    id                  = Column(Integer, primary_key=True, index=True)
    experiment_id       = Column(Integer, ForeignKey("experiments.id"), index=True, nullable=False)
    control_a           = Column(String(50), nullable=False)
    control_b           = Column(String(50), nullable=False)
    energy_baseline     = Column(Float, nullable=False)   # E(0)
    energy_a            = Column(Float, nullable=False)   # E(A)
    energy_b            = Column(Float, nullable=False)   # E(B)
    energy_ab           = Column(Float, nullable=False)   # E(A+B)
    interaction_effect  = Column(Float, nullable=False)   # I(A,B)
    interaction_index   = Column(Float, nullable=True)    # I(A,B) / E(0)
    interpretation      = Column(String(100), nullable=True)  # "additive" | "sub_additive" | "super_additive"
    attack_type         = Column(String(50), nullable=True)
    attack_intensity    = Column(String(20), nullable=True)
    created_at          = Column(DateTime, nullable=False, default=_utcnow)
    
    experiment          = relationship("Experiment", backref="interactions")


class DefenseAmplificationResult(Base):
    """Pre-computed defense amplification result."""
    __tablename__ = "defense_amplification_results"
    
    id                  = Column(Integer, primary_key=True, index=True)
    experiment_id       = Column(Integer, ForeignKey("experiments.id"), index=True, nullable=False)
    control_name        = Column(String(50), nullable=False)
    attack_type         = Column(String(50), nullable=False)
    attack_intensity    = Column(String(20), nullable=False)
    attack_workload     = Column(Float, nullable=False)
    workload_unit       = Column(String(50), nullable=False)  # "requests_per_second" etc.
    energy_attack_only  = Column(Float, nullable=False)   # E(attack)
    energy_attack_defense = Column(Float, nullable=False) # E(attack + defense)
    additional_defense_energy = Column(Float, nullable=False)  # ADE
    defense_energy_amplification = Column(Float, nullable=False)  # DEA = ADE / workload
    created_at          = Column(DateTime, nullable=False, default=_utcnow)
    
    experiment          = relationship("Experiment", backref="amplification_results")
```

### 3.4 Energy Measurement Provider Abstraction

```python
# app/engines/research/energy_provider.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MeasurementMode(str, Enum):
    MEASURED = "MEASURED"
    ESTIMATED = "ESTIMATED"
    SIMULATED = "SIMULATED"


@dataclass
class EnergyReading:
    energy_joules: float
    power_watts: float
    duration_seconds: float
    cpu_usage_pct: Optional[float]
    memory_usage_pct: Optional[float]
    network_usage_mbps: Optional[float]
    source: str
    mode: MeasurementMode


class EnergyMeasurementProvider(ABC):
    """Abstract base for energy measurement providers."""
    
    @abstractmethod
    def get_measurement(
        self,
        duration_seconds: float,
        cpu_usage_pct: Optional[float] = None,
        memory_usage_pct: Optional[float] = None,
        network_usage_mbps: Optional[float] = None,
    ) -> EnergyReading:
        ...
    
    @abstractmethod
    def get_mode(self) -> MeasurementMode:
        ...
    
    @abstractmethod
    def get_source_name(self) -> str:
        ...


class EstimatedEnergyProvider(EnergyMeasurementProvider):
    """Default provider using configurable estimation model."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.base_power_watts = self.config.get("base_power_watts", 100.0)
        self.cpu_power_per_pct = self.config.get("cpu_power_per_pct", 3.0)
        self.memory_power_per_pct = self.config.get("memory_power_per_pct", 0.5)
        self.network_power_per_mbps = self.config.get("network_power_per_mbps", 0.1)
    
    def get_measurement(self, duration_seconds, cpu_usage_pct=None,
                        memory_usage_pct=None, network_usage_mbps=None) -> EnergyReading:
        cpu = cpu_usage_pct or 20.0
        mem = memory_usage_pct or 30.0
        net = network_usage_mbps or 0.0
        
        power = (
            self.base_power_watts
            + self.cpu_power_per_pct * cpu
            + self.memory_power_per_pct * mem
            + self.network_power_per_mbps * net
        )
        energy_joules = power * duration_seconds
        
        return EnergyReading(
            energy_joules=round(energy_joules, 4),
            power_watts=round(power, 4),
            duration_seconds=duration_seconds,
            cpu_usage_pct=cpu,
            memory_usage_pct=mem,
            network_usage_mbps=net,
            source="estimated",
            mode=MeasurementMode.ESTIMATED,
        )
    
    def get_mode(self) -> MeasurementMode:
        return MeasurementMode.ESTIMATED
    
    def get_source_name(self) -> str:
        return "estimated"


# Future providers (stubs for architecture):
# class RaplEnergyProvider(EnergyMeasurementProvider): ...
# class KeplerEnergyProvider(EnergyMeasurementProvider): ...
# class ExternalMeterProvider(EnergyMeasurementProvider): ...
```

### 3.5 Attack Profile Extension

```python
# app/engines/research/attack_profiles.py

ATTACK_PROFILES_RESEARCH = {
    "ddos": {
        "base_severity": "HIGH",
        "workload_metric": "requests_per_second",
        "intensity_levels": {
            "LOW":    {"rps_range": (100, 500),    "cpu_range": (10, 30),  "energy_range": (0.005, 0.015)},
            "MEDIUM": {"rps_range": (500, 5000),   "cpu_range": (30, 80),  "energy_range": (0.015, 0.05)},
            "HIGH":   {"rps_range": (5000, 50000), "cpu_range": (80, 200), "energy_range": (0.05, 0.15)},
        },
    },
    "brute_force": {
        "base_severity": "MEDIUM",
        "workload_metric": "login_attempts",
        "intensity_levels": {
            "LOW":    {"attempts_range": (10, 50),    "cpu_range": (5, 15),   "energy_range": (0.002, 0.008)},
            "MEDIUM": {"attempts_range": (50, 500),   "cpu_range": (15, 40),  "energy_range": (0.008, 0.02)},
            "HIGH":   {"attempts_range": (500, 5000), "cpu_range": (40, 100), "energy_range": (0.02, 0.06)},
        },
    },
    "port_scan": {
        "base_severity": "LOW",
        "workload_metric": "scan_requests",
        "intensity_levels": {
            "LOW":    {"scans_range": (10, 100),     "cpu_range": (2, 8),    "energy_range": (0.001, 0.004)},
            "MEDIUM": {"scans_range": (100, 1000),   "cpu_range": (8, 20),   "energy_range": (0.004, 0.01)},
            "HIGH":   {"scans_range": (1000, 10000), "cpu_range": (20, 50),  "energy_range": (0.01, 0.03)},
        },
    },
    "sql_injection": {
        "base_severity": "HIGH",
        "workload_metric": "processed_events",
        "intensity_levels": {
            "LOW":    {"events_range": (10, 50),     "cpu_range": (5, 15),   "energy_range": (0.003, 0.008)},
            "MEDIUM": {"events_range": (50, 500),    "cpu_range": (15, 40),  "energy_range": (0.008, 0.02)},
            "HIGH":   {"events_range": (500, 5000),  "cpu_range": (40, 100), "energy_range": (0.02, 0.05)},
        },
    },
    "malware": {
        "base_severity": "CRITICAL",
        "workload_metric": "processed_events",
        "intensity_levels": {
            "LOW":    {"events_range": (5, 20),      "cpu_range": (20, 60),  "energy_range": (0.01, 0.03)},
            "MEDIUM": {"events_range": (20, 200),    "cpu_range": (60, 150), "energy_range": (0.03, 0.08)},
            "HIGH":   {"events_range": (200, 2000),  "cpu_range": (150, 400),"energy_range": (0.08, 0.25)},
        },
    },
    "suspicious_login": {
        "base_severity": "MEDIUM",
        "workload_metric": "connection_attempts",
        "intensity_levels": {
            "LOW":    {"connections_range": (5, 20),    "cpu_range": (2, 8),   "energy_range": (0.001, 0.005)},
            "MEDIUM": {"connections_range": (20, 200),  "cpu_range": (8, 25),  "energy_range": (0.005, 0.015)},
            "HIGH":   {"connections_range": (200, 2000),"cpu_range": (25, 60), "energy_range": (0.015, 0.04)},
        },
    },
    "phishing": {
        "base_severity": "MEDIUM",
        "workload_metric": "processed_events",
        "intensity_levels": {
            "LOW":    {"events_range": (5, 30),     "cpu_range": (3, 10),   "energy_range": (0.002, 0.006)},
            "MEDIUM": {"events_range": (30, 300),   "cpu_range": (10, 30),  "energy_range": (0.006, 0.018)},
            "HIGH":   {"events_range": (300, 3000), "cpu_range": (30, 80),  "energy_range": (0.018, 0.05)},
        },
    },
}

SECURITY_CONTROLS = {
    "firewall":   {"name": "Firewall",   "base_overhead_watts": 2.0,  "attack_overhead_multiplier": 1.5},
    "ids":        {"name": "IDS",        "base_overhead_watts": 5.0,  "attack_overhead_multiplier": 2.0},
    "ips":        {"name": "IPS",        "base_overhead_watts": 8.0,  "attack_overhead_multiplier": 2.5},
    "waf":        {"name": "WAF",        "base_overhead_watts": 4.0,  "attack_overhead_multiplier": 1.8},
    "endpoint":   {"name": "Endpoint Security", "base_overhead_watts": 3.0, "attack_overhead_multiplier": 1.6},
    "auth":       {"name": "Authentication",    "base_overhead_watts": 1.5, "attack_overhead_multiplier": 1.3},
    "encryption": {"name": "Encryption", "base_overhead_watts": 2.5,  "attack_overhead_multiplier": 1.2},
    "siem":       {"name": "SIEM",       "base_overhead_watts": 6.0,  "attack_overhead_multiplier": 2.2},
    "monitoring": {"name": "Runtime Monitoring", "base_overhead_watts": 4.0, "attack_overhead_multiplier": 1.7},
    "logging":    {"name": "Logging",    "base_overhead_watts": 1.0,  "attack_overhead_multiplier": 1.4},
}
```

### 3.6 Research Engine Formulas

#### Marginal Energy Attribution

```
Given:
  E_baseline = energy with no security control
  E_security = energy with security control enabled

Marginal Energy:
  ΔE = E_security - E_baseline  (joules)

Marginal Power:
  ΔP = P_security - P_baseline  (watts)

Marginal Carbon:
  ΔC = ΔE_kWh × carbon_intensity_g_per_kWh / 1000  (kg CO2)

Where:
  ΔE_kWh = ΔE_joules / 3_600_000
```

#### Security Control Interaction

```
Given:
  E(0)   = baseline energy (no controls)
  E(A)   = energy with control A only
  E(B)   = energy with control B only
  E(A+B) = energy with both controls

Interaction Effect:
  I(A,B) = E(A+B) - E(A) - E(B) + E(0)

Interaction Index:
  II(A,B) = I(A,B) / E(0)     if E(0) > 0

Interpretation:
  II ≈ 0    → approximately additive
  II > 0    → super-additive (negative interaction)
  II < 0    → sub-additive (synergistic)
```

#### Defense Energy Amplification

```
Given:
  E_attack          = energy under attack (no defense)
  E_attack_defense  = energy under attack (with defense)
  Attack_Workload   = attack-specific workload metric

Additional Defense Energy:
  ADE = E_attack_defense - E_attack

Defense Energy Amplification:
  DEA = ADE / Attack_Workload    (joules per workload unit)

Where Attack_Workload units depend on attack type:
  DDoS           → requests_per_second
  Brute Force    → login_attempts
  Port Scan      → scan_requests
  SQL Injection  → processed_events
  Malware        → processed_events
  Suspicious Login → connection_attempts
  Phishing       → processed_events
```

### 3.7 Research API Endpoints

All under `/api/v1/research/`:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/experiments` | Create experiment |
| GET | `/experiments` | List experiments (paginated, filterable) |
| GET | `/experiments/{id}` | Get experiment with runs |
| POST | `/experiments/{id}/run` | Execute a single trial |
| POST | `/experiments/{id}/run-batch` | Execute multiple trials |
| POST | `/marginal-energy` | Run marginal energy experiment |
| GET | `/marginal-energy/{experiment_id}` | Get marginal energy results |
| POST | `/interaction` | Run interaction experiment |
| GET | `/interaction/{experiment_id}` | Get interaction results |
| POST | `/amplification` | Run amplification experiment |
| GET | `/amplification/{experiment_id}` | Get amplification results |
| GET | `/summary` | Research summary statistics |
| GET | `/metrics` | All computed research metrics |
| GET | `/attack-types` | Supported attack types with intensity levels |
| GET | `/security-controls` | Supported security controls |
| GET | `/export/csv` | Export research dataset as CSV |
| GET | `/export/json` | Export research dataset as JSON |

### 3.8 Frontend: Research Lab

New feature directory: `frontend/src/features/research/`

```
features/research/
├── components/
│   ├── ResearchOverviewPage.tsx      Summary dashboard
│   ├── MarginalEnergyPage.tsx        Marginal energy attribution
│   ├── InteractionAnalysisPage.tsx   Security control interaction
│   ├── DefenseAmplificationPage.tsx  Defense energy amplification
│   ├── ExperimentRunnerPage.tsx      Experiment wizard
│   ├── ExperimentHistoryPage.tsx     Experiment list/table
│   ├── ExperimentDetailPage.tsx      Single experiment view
│   ├── ResearchDatasetPage.tsx       Data table + export
│   └── shared/
│       ├── MeasurementBadge.tsx      MEASURED/ESTIMATED/SIMULATED badge
│       ├── FormulaCard.tsx           Methodology display
│       └── ConfidenceInterval.tsx    CI visualization
├── __tests__/
├── api/
│   └── researchApi.ts               Research API methods
├── hooks/
│   └── useResearch.ts               Research data hooks
└── types/
    └── research.ts                  Research-specific types
```

### 3.9 Proposed Sidebar Navigation

```
Overview                    → /

SECURITY
  Security Dashboard        → /security
  Threats                   → /threats
  Attack Simulator          → /attack-simulator

ENERGY & CARBON
  Energy                    → /energy
  Carbon                    → /carbon
  Optimizer                 → /optimizer
  Renewable Energy          → /renewable-energy

RESEARCH
  Research Lab              → /research
  Marginal Energy           → /research/marginal-energy
  Interaction Analysis      → /research/interaction
  Defense Amplification     → /research/amplification
  Experiments               → /research/experiments
  Dataset                   → /research/dataset

ANALYTICS
  Analytics                 → /analytics
  Events                    → /events

SYSTEM
  System Health             → /system-health
  Settings                  → /settings
```

### 3.10 UI Theme Redesign

**Current**: All-green dark theme (`#03150F` bg, `#00C878` accent)

**Proposed**: Professional SOC + Research Lab aesthetic

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| Background | Charcoal/near-black | `#070B12` | Page background |
| Panels | Deep slate | `#111827` | Cards, sidebar |
| Elevated | Dark slate | `#151E2D` | Hover states, headers |
| Cybersecurity | Cyan/electric blue | `#22D3EE` | Security metrics, network |
| Cybersecurity secondary | Blue | `#38BDF8` | Links, secondary security |
| Sustainability | Emerald | `#10B981` | Carbon reduction, energy savings |
| Warning | Amber | `#F59E0B` | Medium threats |
| Critical | Red | `#EF4444` | High threats, errors |
| AI/Research | Violet (subtle) | `#8B5CF6` | Research accents, AI features |
| Text primary | White | `#F8FAFC` | Main text |
| Text secondary | Light slate | `#94A3B8` | Secondary text |

**Rules**:
- Green only for carbon/energy/sustainability
- Cyan/blue for cybersecurity and research
- Violet only as subtle accent for AI/research
- No glassmorphism, no excessive gradients
- No dominant green theme
- No dominant purple theme

---

## 4. Implementation Phases

| Phase | Scope | Dependencies | Status |
|-------|-------|-------------|--------|
| 1 | Database models (research) | None | Complete |
| 2 | Energy provider abstraction | None | Complete |
| 3 | Attack profiles (extended) | None | Complete |
| 4 | Experiment engine | Phases 1-3 | Complete |
| 5 | Marginal energy engine | Phase 4 | Complete |
| 6 | Interaction engine | Phase 4 | Complete |
| 7 | Amplification engine | Phase 4 | Complete |
| 8 | Research service + repository | Phases 1-7 | Complete |
| 9 | Research API endpoints | Phase 8 | Complete |
| 10 | Frontend: Research Lab pages | Phase 9 | Complete |
| 11 | Frontend: UI theme redesign | Phase 10 | Complete |
| 12 | Attack Simulator integration | Phases 4-9 | Complete |
| 13 | Dashboard integration | Phase 10 | Complete |
| 14 | Backend tests | Phases 1-9 | Complete |
| 15 | Frontend tests | Phases 10-13 | Complete |
| 16 | Documentation | All | Complete |
| 17 | Integration audit | All | Pending |

After each phase: run tests, check TypeScript, verify API startup, verify frontend build.

---

## 5. Reuse vs. New

### Reuse Existing

| Existing Module | Reuse As |
|----------------|----------|
| `engines/carbon/carbon_calculator.py` | Carbon calculation for research experiments |
| `engines/security/threat_detector.py` | Extended with intensity levels for research |
| `engines/security/risk_analyzer.py` | Risk assessment for research runs |
| `engines/security/attack_simulator.py` | Extended for configurable research simulation |
| `engines/ai/recommendation_engine.py` | Recommendations based on research results |
| `repositories/base.py` | Generic CRUD for research models |
| `app/config.py` | Research configuration settings |
| `app/dependencies.py` | DB session injection for research API |
| `app/database.py` | Same SQLite, same `create_all()` |
| Frontend shared UI components | Card, Badge, MetricCard, PageHeader, etc. |
| Frontend `apiClient.ts` | HTTP client for research API |
| Frontend `formatters.ts` | Number/date formatting |

### New Modules Only

| New Module | Purpose |
|-----------|---------|
| `engines/research/energy_provider.py` | Measurement abstraction |
| `services/marginal_energy_service.py` | Marginal energy attribution |
| `engines/research/interaction_engine.py` | Interaction analysis |
| `engines/research/amplification_engine.py` | Defense amplification |
| `engines/research/experiment_engine.py` | Experiment orchestration |
| `engines/research/statistics.py` | Statistical utilities |
| `engines/research/attack_profiles.py` | Extended attack profiles |
| `models/research.py` | Research database models |
| `schemas/research.py` | Research Pydantic DTOs |
| `services/research_service.py` | Research business logic |
| `repositories/research_repo.py` | Research data access |
| `api/research.py` | Research API endpoints |

### Dead Code to Clean Up

| File | Issue |
|------|-------|
| `schemas/common.py` | Missing `datetime` import — fix or remove |
| `engines/carbon/estimate_workload_energy()` | Never called — integrate or remove |
| `src/shared/hooks/useApi.ts` | Unused — integrate or remove |
| `src/shared/hooks/usePolling.ts` | Unused — integrate or remove |
| `src/shared/hooks/useLocalStorage.ts` | Unused — integrate or remove |
| `src/shared/ui/DataTable.tsx` | Unused — integrate or remove |
| `src/shared/ui/StatCard.tsx` | Unused — integrate or remove |
| `src/shared/utils/constants.ts` | Unused — integrate or remove |
| `src/app/` | Empty directory — remove |

---

## 6. Measurement Honesty

### Energy Measurement Modes

| Mode | Label | Description |
|------|-------|-------------|
| MEASURED | `MEASURED` | Real hardware telemetry (Intel RAPL, Kepler, external meter) |
| ESTIMATED | `ESTIMATED` | Computed from workload parameters using estimation model |
| SIMULATED | `SIMULATED` | Generated for demonstration, not tied to real workload |

### Current State

- **All energy data is ESTIMATED or SIMULATED**
- No real hardware telemetry is available
- The estimation model uses configurable coefficients
- Energy provider abstraction allows plugging in real telemetry later

### Display Rules

1. Every energy/carbon value must show a measurement mode badge
2. Charts must indicate measurement mode in title or legend
3. Research dataset export must include measurement_mode column
4. No claim of "measured" data unless provider is a real hardware source
5. Default provider is `EstimatedEnergyProvider`

---

## 7. Known Limitations

1. No real hardware energy telemetry — all energy is estimated or simulated
2. SQLite database — not suitable for high-concurrency production
3. No Alembic migrations — schema changes require manual intervention
4. No authentication — all endpoints publicly accessible
5. Dashboard analytics use random data — not connected to stored metrics
6. Attack simulation is synthetic — not real-world attack traffic
7. Estimation model coefficients are configurable but not calibrated to real hardware
8. Research analytics (Phase 8) covers descriptive statistics, confidence intervals, paired tests, and effect sizes; no multiple-comparison correction and no frontend analytics dashboard yet
9. No real-time streaming — experiments are batch/synchronous
10. Frontend builds may have unused code from original scaffold

---

## 8. Acceptance Criteria

### Backend
- [ ] All existing tests pass
- [ ] All new research tests pass
- [ ] FastAPI starts successfully
- [ ] All research endpoints functional
- [ ] No raw ORM serialization in responses
- [ ] Database operations correct

### Frontend
- [ ] All existing pages work
- [ ] Research Lab pages functional
- [ ] Experiment runner works
- [ ] Charts render with correct data
- [ ] Filtering and export work
- [ ] No TypeScript errors
- [ ] Production build succeeds

### Research
- [x] Marginal energy calculation correct
- [ ] Interaction formula correct
- [ ] Defense amplification correct
- [ ] Repeated experiments with statistics
- [ ] Measurement modes visible everywhere
- [ ] Formulas documented
- [ ] Dataset exportable
- [ ] No fabricated measurements

### UI
- [ ] No all-green design
- [ ] Professional SOC aesthetic
- [ ] Cyan cybersecurity identity
- [ ] Emerald sustainability identity
- [ ] Red/amber threat identity
- [ ] Violet research accent (subtle)
- [ ] Measurement badges present
- [ ] Responsive layout
- [ ] No excessive gradients or glassmorphism
