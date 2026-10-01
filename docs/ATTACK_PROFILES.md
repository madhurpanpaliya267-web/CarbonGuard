# Attack Profiles — Phase 3

## Overview

Centralized, configuration-driven attack profile system for research experiments. All attacks are **SAFE**, **SYNTHETIC**, and **SIMULATED** — no real traffic, no external systems.

## Supported Attack Types

| Attack Type | Display Name | Workload Unit | Severity |
|---|---|---|---|
| `ddos` | DDoS | `packets_per_second` | HIGH |
| `brute_force` | Brute Force | `login_attempts` | MEDIUM |
| `port_scan` | Port Scan | `scan_requests` | LOW |
| `sql_injection` | SQL Injection | `requests_per_second` | HIGH |
| `suspicious_login` | Suspicious Login | `login_attempts` | MEDIUM |
| `malware` | Malware-like Endpoint Activity | `processed_events` | CRITICAL |
| `phishing` | Phishing-like Activity | `processed_events` | MEDIUM |

## Intensity Levels

Every attack supports three intensity levels:

- **LOW** — minimal workload, short duration
- **MEDIUM** — moderate workload, standard duration
- **HIGH** — heavy workload, extended duration

## Workload Definitions

### DDoS

| Intensity | Packets/sec | Duration |
|---|---|---|
| LOW | 500 | 30s |
| MEDIUM | 5,000 | 60s |
| HIGH | 50,000 | 120s |

### Brute Force

| Intensity | Login Attempts | Duration |
|---|---|---|
| LOW | 10 | 30s |
| MEDIUM | 100 | 60s |
| HIGH | 1,000 | 120s |

### Port Scan

| Intensity | Scan Requests | Duration |
|---|---|---|
| LOW | 20 | 15s |
| MEDIUM | 200 | 30s |
| HIGH | 2,000 | 60s |

### SQL Injection

| Intensity | Requests/sec | Duration |
|---|---|---|
| LOW | 5 | 30s |
| MEDIUM | 25 | 60s |
| HIGH | 100 | 120s |

### Suspicious Login

| Intensity | Login Attempts | Duration |
|---|---|---|
| LOW | 5 | 30s |
| MEDIUM | 25 | 60s |
| HIGH | 100 | 120s |

### Malware-like Endpoint Activity

| Intensity | Events/sec | Duration |
|---|---|---|
| LOW | 10 | 30s |
| MEDIUM | 50 | 60s |
| HIGH | 200 | 120s |

### Phishing-like Activity

| Intensity | Processed Events | Duration |
|---|---|---|
| LOW | 50 | 30s |
| MEDIUM | 250 | 60s |
| HIGH | 1,000 | 120s |

## Workload Units

Do not compare incompatible units. For example:
- `packets_per_second` (DDoS) is not directly comparable to `login_attempts` (Brute Force)
- `processed_events` (Malware) is not directly comparable to `scan_requests` (Port Scan)

Each attack type defines its own workload unit.

## Configuration

Attack profiles are defined in `app/engines/security/attack_profiles.py`.

Key data structures:
- `AttackProfileConfig` — attack type configuration with intensity configs
- `AttackProfile` — built profile with workload, duration, ranges
- `WorkloadSpec` — workload value and unit

### Adding a New Attack Type

1. Add entry to `ATTACK_PROFILE_CONFIGS` dict
2. Add severity mapping to `ATTACK_SEVERITY_MAP`
3. Add detection method to `_detection_method_for()`
4. Add CPU/energy ranges to `_cpu_range_for()` and `_energy_range_for()`
5. Add to `ATTACK_PROFILES` in `threat_detector.py` for legacy compatibility

## Safety Boundaries

- All attacks are simulated — no real traffic generated
- No external systems contacted
- No real credentials used
- No real SQL injection performed
- No real malware executed
- No real phishing emails sent

## Reproducibility

- Same configuration → same profile/workload
- `config_version` preserved on every profile
- No randomness in profile generation
- Deterministic workload values for given intensity

## Validation

The system validates:
- Supported attack type
- Supported intensity level
- Non-negative workload values
- Positive duration

Invalid configurations raise `AttackProfileError`.

## Integration with Attack Simulator

The existing `simulate_attack()` function now accepts optional `intensity` and `duration_seconds` parameters:

```python
from app.engines.security.attack_simulator import simulate_attack

# Legacy (no intensity)
result = simulate_attack("ddos")

# With research profile
result = simulate_attack("ddos", intensity="medium", duration_seconds=60)
# Result includes "research_profile" key with workload metadata
```

## Security Controls

Each attack type maps to supported security controls:

| Attack Type | Supported Controls |
|---|---|
| DDoS | firewall, ids, ips, waf |
| Brute Force | firewall, authentication, ids, siem |
| Port Scan | firewall, ids, endpoint_security |
| SQL Injection | waf, ids, siem |
| Suspicious Login | authentication, siem, endpoint_security |
| Malware | endpoint_security, siem, ids, runtime_monitoring |
| Phishing | waf, siem, endpoint_security, logging |

## Limitations

- Workload ranges are estimates for simulation purposes
- Energy values are derived from the energy measurement provider (ESTIMATED mode)
- Attack profiles do not model network propagation or cascading effects
- Current profiles are static — no adaptive/intelligent attack simulation
