# Experiment Protocol — Phase 4

## Overview

The Research Experiment Engine executes controlled, reproducible experiments that record attack simulations, energy measurements, and security effectiveness data. All experiments are **LOCAL SYNTHETIC SIMULATIONS** — no real attacks, no external systems.

## Experiment Lifecycle

```
CREATED → VALIDATING → RUNNING → MEASURING → COMPLETED
                            ↓
                         FAILED
                            ↓
                        CANCELLED
```

- **CREATED** — Experiment configured, not yet executed
- **VALIDATING** — Configuration validated, attack profiles resolved
- **RUNNING** — Trials executing, attack simulations running
- **MEASURING** — All trials complete, energy measurements collected
- **COMPLETED** — Experiment finished successfully
- **FAILED** — An error occurred during execution
- **CANCELLED** — Experiment was cancelled by user

## Experiment Configuration

| Field | Description | Required |
|---|---|---|
| `name` | Human-readable experiment name | Yes |
| `description` | Optional description | No |
| `experiment_type` | MARGINAL_ENERGY, INTERACTION, or DEFENSE_AMPLIFICATION | Yes |
| `attack_type` | ddos, brute_force, port_scan, sql_injection, suspicious_login, malware, phishing | Yes |
| `attack_intensity` | low, medium, high | Yes |
| `attack_workload` | Override workload value (optional) | No |
| `workload_unit` | Unit of workload (auto-detected from attack type) | No |
| `duration_seconds` | Experiment duration (1-3600, default 60) | No |
| `security_controls` | List of control IDs (empty = baseline) | No |
| `measurement_provider` | estimated, rapl, kepler, external | No |
| `number_of_trials` | Number of repeated trials (1-20, default 1) | No |
| `random_seed` | Seed for reproducibility (optional) | No |
| `carbon_intensity` | Grid carbon intensity gCO2/kWh (optional) | No |
| `renewable_pct` | Renewable energy percentage (optional) | No |
| `notes` | Free-form notes | No |

## Baseline Concept

A **baseline** experiment uses NO security controls:

```json
{
  "security_controls": []
}
```

This captures the attack's energy and security impact without any defense. Controlled experiments (the same attack WITH security controls) are compared against this baseline to calculate marginal energy attribution — see `RESEARCH_METHODOLOGY.md`.

## Trial Concept

Each experiment can run multiple trials. Each trial:

1. Creates an `ExperimentRun` record
2. Executes the attack simulation
3. Requests an energy measurement from the configured provider
4. Records security effectiveness data
5. Stores all results as database records

Trials are independent — each produces its own measurement and effectiveness data.

## Attack Workload

The experiment engine uses the Phase 3 attack profile system:

- Attack type determines workload unit (packets/sec, login_attempts, etc.)
- Intensity determines workload magnitude
- Duration determines how long the simulation runs
- Workload value is stored on each ExperimentRun

## Security Configuration

Security controls are stored as a sorted JSON array:

```json
["firewall", "ids"]
```

Controls are normalized (sorted, deduplicated, lowercased) so the same configuration always produces the same representation.

## Measurement Provider

Energy measurements come from the Phase 2 provider system:

- `estimated` — deterministic estimation (default, always available)
- `rapl` — Intel RAPL (requires hardware support)
- `kepler` — Kubernetes-based (requires Kepler)
- `external` — External power meter (requires hardware)

The measurement mode is preserved in every `EnergyMeasurement` record.

## Energy Measurements

Every trial produces exactly one `EnergyMeasurement` with:

- `energy_joules` — Total energy consumed
- `power_watts` — Average power draw
- `duration_seconds` — Measurement duration
- `source` — Provider source identifier
- `measurement_mode` — ESTIMATED, RAPL, KEPLER, or EXTERNAL
- `timestamp` — When the measurement was taken

## Security Effectiveness

Every trial produces one `SecurityEffectiveness` record with:

- `detection_rate` — Confidence of threat detection (0.0-1.0)
- `detection_latency_ms` — Time to detect (if available)
- `mitigation_time_ms` — Time to mitigate (if available)
- `false_positive_rate` — False positive rate (if available)
- `threat_severity` — Severity of detected threat
- `security_response` — Recommended security action
- `security_score` — Risk assessment score (0-100)
- `controls_active` — JSON array of active controls
- `controls_config` — Control configuration details

## Reproducibility

Every experiment records enough metadata to reproduce:

- Attack type, intensity, workload, duration
- Security controls (sorted, normalized)
- Measurement provider and mode
- Configuration version
- Software version
- Random seed (if provided)

Same inputs → same attack profile → same workload metadata.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/research/experiments` | Create experiment |
| POST | `/api/v1/research/experiments/{uuid}/execute` | Execute experiment |
| GET | `/api/v1/research/experiments` | List experiments |
| GET | `/api/v1/research/experiments/{uuid}` | Get experiment |
| GET | `/api/v1/research/experiments/{uuid}/status` | Get execution status |
| GET | `/api/v1/research/experiments/{uuid}/runs` | Get experiment runs |
| GET | `/api/v1/research/experiments/{uuid}/summary` | Get full summary |
| GET | `/api/v1/research/attacks` | List supported attacks |
| GET | `/api/v1/research/controls` | List security controls |

## Safety Boundaries

- All attacks are synthetic simulations
- No real network traffic generated
- No external systems contacted
- No real credentials used
- No real SQL injection performed
- No real malware executed

## Failure Handling

If a trial fails:

1. The run is marked as `failed` with an error message
2. Other trials continue executing
3. The experiment is marked as `failed` if any trial fails
4. Partial results (completed trials) are preserved

## Limitations

- Energy values are estimates (ESTIMATED mode) unless hardware providers are available
- Security effectiveness metrics come from the simulation, not real security systems
- No distributed execution — all experiments run locally
- No statistical analysis engine yet (Phase 7)
- No interaction effect calculation yet
