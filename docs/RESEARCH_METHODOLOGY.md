# Research Methodology

## Overview

CarbonGuard's research engine enables reproducible, controlled experiments on the energy cost of cybersecurity defenses. All data is **ESTIMATED** unless a real energy measurement provider is configured.

---

## Attack-Conditioned Marginal Energy Attribution

### Research Question

How does the marginal energy cost of a cybersecurity control change with attack intensity and workload?

### Experimental Setup

A marginal energy experiment compares:

- **Baseline**: Attack simulated with NO security controls
- **Security**: Same attack simulated WITH selected security controls

The only intended difference between the two configurations is the security controls.

### Matching Requirements

Baseline and security runs MUST match on:

| Dimension | Must Match |
|---|---|
| Attack type | ddos, brute_force, etc. |
| Attack intensity | low, medium, high |
| Workload value | e.g., 5000 packets/sec |
| Workload unit | packets_per_second, login_attempts, etc. |
| Duration | e.g., 60 seconds |
| Measurement mode | ESTIMATED, RAPL, etc. |

If any dimension differs, the system rejects the comparison with a clear error.

### Formula

```
ΔE = E_security - E_baseline
ΔP = P_security - P_baseline
ΔC = C_security - C_baseline
```

Where:
- E = Energy in joules
- P = Power in watts (E / duration)
- C = Carbon in kg CO2

### Carbon Calculation

Uses the existing CarbonGuard carbon methodology:

```
energy_kWh = energy_joules / 3,600,000
gross_CO2_kg = energy_kWh × carbon_intensity_g_per_kWh / 1000
```

Default carbon intensity: 475 gCO2/kWh (configurable per experiment).

### Measurement Modes

Every result preserves its measurement mode:

| Mode | Description | Status |
|---|---|---|
| ESTIMATED | Deterministic estimation model | **Currently active** |
| RAPL | Intel Running Average Power Limit | Requires hardware |
| KEPLER | Kubernetes-based energy measurement | Requires cluster |
| EXTERNAL | External power meter | Requires hardware |

**Important**: Current results are ESTIMATED unless a real energy measurement provider is configured.

### Trial Pairing

When an experiment has multiple trials, the system pairs them:

```
Trial 1 baseline ↔ Trial 1 security
Trial 2 baseline ↔ Trial 2 security
Trial 3 baseline ↔ Trial 3 security
```

For each pair i:

```
ΔE_i = E_security_i - E_baseline_i
```

### Descriptive Statistics

The system calculates:

| Statistic | Description |
|---|---|
| Mean | Average marginal energy |
| Median | Middle value |
| Standard deviation | Spread of values |
| Minimum | Smallest marginal energy |
| Maximum | Largest marginal energy |

**Note**: No hypothesis testing or statistical significance claims are made yet.

### Security Effectiveness

Every marginal energy comparison exposes the corresponding security effectiveness:

- Detection rate (confidence 0.0-1.0)
- Threat severity (LOW, MEDIUM, HIGH, CRITICAL)
- Security score (risk assessment 0-100)
- Recommended security response

This enables future analysis of energy cost versus security benefit.

### Attack-Conditioned Analysis

The system supports comparison across:

- **7 attack types**: DDoS, Brute Force, Port Scan, SQL Injection, Suspicious Login, Malware, Phishing
- **3 intensity levels**: LOW, MEDIUM, HIGH
- **10 security controls**: Firewall, IDS, IPS, WAF, Endpoint Security, Authentication, Encryption, SIEM, Runtime Monitoring, Logging

### Workload Analysis

Marginal energy can be compared across different workload levels:

```
DDoS + Firewall:
  LOW (500 packets/sec)    → ΔE = X joules
  MEDIUM (5000 packets/sec) → ΔE = Y joules
  HIGH (50000 packets/sec)  → ΔE = Z joules
```

**Important**: Workload units are never combined. `packets_per_second` is not plotted with `login_attempts`.

### Limitations

1. **ESTIMATED data**: All current energy values are estimates, not hardware measurements
2. **Simulation-based**: Security effectiveness comes from simulation, not real security systems
3. **Linear model**: The estimation model does not capture non-linear effects
4. **No significance testing**: Descriptive statistics only
5. **Static environment**: No modeling of time-varying conditions
6. **Single host**: All measurements assume a single computing environment

### Formula Version

Current formula version: `marginal_energy_v1`

Any changes to the calculation methodology will increment this version.

---

## Experiment Lifecycle

```
CREATED → VALIDATING → RUNNING → MEASURING → COMPLETED
                            ↓
                         FAILED
```

All experiments are local synthetic simulations. No real attacks are executed.
