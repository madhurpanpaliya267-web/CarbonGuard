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

## Security-Control Interaction Effects

### Research Question

How does the combined energy cost of multiple cybersecurity controls differ from the energy cost expected from applying those controls individually?

### Experimental Design

A security-control interaction experiment records four controlled configurations:

| Configuration | Symbol | Security Controls |
|---|---|---|
| Baseline | E_0 | None |
| Control A only | E_A | Firewall (or any single control) |
| Control B only | E_B | IDS (or any single control) |
| Combined | E_AB | Control A + Control B |

All four configurations must be comparable. They must use the same:

| Dimension | Must Match |
|---|---|
| Attack type | ddos, brute_force, etc. |
| Attack intensity | low, medium, high |
| Workload value | e.g., 500 packets/sec |
| Workload unit | e.g., packets_per_second |
| Duration | e.g., 30 seconds |
| Environment | software version, configuration version |
| Energy provider | estimated, rapl, etc. |
| Measurement mode | ESTIMATED, MEASURED, SIMULATED |

Only the security-control configuration may differ. If any dimension differs, the calculation is rejected with a clear error. Incompatible experiments are never silently combined.

### Interaction Formula

```
I(A,B) = E_AB - E_A - E_B + E_0
```

Where:
- E_0 = baseline energy with no security controls (joules)
- E_A = energy with control A only (joules)
- E_B = energy with control B only (joules)
- E_AB = energy with both controls (joules)

An equivalent view: `I = (E_AB - E_0) - (E_A - E_0) - (E_B - E_0)`, i.e., the difference between the observed combined cost and the sum of the individual costs above baseline.

### Interaction Index

```
Interaction Index = I(A,B) / E_0
```

Computed only when `E_0 > 0`. Division by a zero or negative baseline is never performed; the index is omitted instead.

### Interpretation

Interpretation is reported neutrally. The system never labels an interaction as beneficial or harmful automatically.

| Value | Interpretation |
|---|---|
| I approximately 0 | approximately additive |
| I > 0 | super-additive |
| I < 0 | sub-additive |

"I approximately 0" uses an absolute tolerance of 1e-9 joules. The measured value and interpretation are both returned.

### Attack Conditioning

Every interaction result retains the full attack context:

- Attack type (7 types: DDoS, Brute Force, Port Scan, SQL Injection, Suspicious Login, Malware, Phishing)
- Attack intensity (low, medium, high)
- Workload value and workload unit
- Duration

Results are never combined across incompatible workload units (e.g., `packets_per_second` is never mixed with `login_attempts`).

### Trial Pairing

Multiple trials are paired by trial number across all four configurations:

```
Trial 1: I_1 = E_AB,1 - E_A,1 - E_B,1 + E_0,1
Trial 2: I_2 = E_AB,2 - E_A,2 - E_B,2 + E_0,2
Trial 3: I_3 = E_AB,3 - E_A,3 - E_B,3 + E_0,3
```

Run counts must match across the four lists, and trial numbers must align. Unpaired or mismatched trials are rejected.

### Descriptive Statistics

Statistics are calculated over the per-trial interaction values:

| Statistic | Description |
|---|---|
| Mean | Average interaction energy |
| Median | Middle value |
| Standard deviation | Population spread of values |
| Minimum | Smallest interaction value |
| Maximum | Largest interaction value |

Statistics are reported for interaction energy, interaction power, and interaction carbon.

**Note**: No hypothesis testing or statistical significance claims are made.

### Measurement Modes

Every result preserves its measurement mode and energy provider:

| Mode | Description | Status |
|---|---|---|
| ESTIMATED | Deterministic estimation model | **Currently active** |
| MEASURED | Hardware measurement | Requires provider |
| SIMULATED | Simulated reading | Simulated only |

If all four runs use ESTIMATED, the result records `measurement_mode = ESTIMATED`. Estimated energy is never called measured energy, and no hardware measurements are fabricated.

**Important**: Current results are ESTIMATED unless a real energy measurement provider is configured.

### Carbon Calculation

Uses the existing CarbonGuard carbon methodology (no second formula):

```
energy_kWh = energy_joules / 3,600,000
gross_CO2_kg = energy_kWh × carbon_intensity_g_per_kWh / 1000
```

Carbon is computed for all four configurations, and the interaction carbon impact follows the same interaction formula:

```
I_C = C_AB - C_A - C_B + C_0
```

Default carbon intensity: 475 gCO2/kWh (configurable per calculation).

### Security Effectiveness

Where available, each result exposes security-effectiveness for all four configurations:

- Detection rate
- Detection latency and mitigation latency (when available)
- False positive rate (when available)
- Threat severity
- Security score

Phase 6 is measurement and interaction analysis only. No control optimization or adaptive selection is performed.

### Formula Version

Current formula version: `interaction_effect_v1`

Any changes to the calculation methodology will increment this version.

### Limitations

1. **ESTIMATED data**: All current energy values are estimates, not hardware measurements
2. **Linear estimation model**: The current provider is linear in control count, so estimated runs typically produce approximately additive interactions; non-zero interactions require measured or non-linear data
3. **Two controls at a time**: The formula analyzes pairs of controls; higher-order interactions are not modeled
4. **No significance testing**: Descriptive statistics only
5. **Simulation-based effectiveness**: Security effectiveness comes from simulation, not real security systems
6. **Single host**: All measurements assume a single computing environment

---

## Defense Energy Amplification

### Research Question

How much additional energy does a security control add, and how much defense does each unit of attack workload buys per joule spent? Phase 7 quantifies the energy price of defense.

**Distinction from earlier phases:**

| Phase | Question | Formula |
|---|---|---|
| Phase 5 (Attribution) | How much energy does the attack itself consume above idle? | ΔE = E_attack − E_idle |
| Phase 6 (Interaction) | Do two controls combined cost more or less than the sum of their parts? | I(A,B) = E_AB − E_A − E_B + E_0 |
| Phase 7 (Amplification) | How much extra energy does defense cost, and what is that cost per unit of attack workload? | ADE = E_attack+defense − E_attack+baseline; DEA = ADE / workload |

### Experimental Design

A defense-amplification experiment compares two controlled configurations:

| Configuration | Symbol | Security Controls |
|---|---|---|
| Attack baseline | E_attack+baseline | None |
| Attack + defense | E_attack+defense | One security control (firewall, ids, waf, ...) |

All comparability requirements from Phase 6 apply (attack type, intensity, workload value, workload unit, duration, environment, software/config version, measurement mode, energy provider, trial alignment). Only the security-control configuration may differ; identical baseline and defense configurations are rejected because the amplification would be trivially zero.

### ADE and DEA Formulas

```
ADE = E_attack+defense − E_attack+baseline          (joules, per trial)
DEA = ADE / Attack_Workload                          (joules per workload unit)
```

Where:
- ADE = Attack Defense Energy (additional energy attributable to the defense)
- DEA = Defense Energy Amplification
- Attack_Workload = workload value of the matched attack run (e.g., 500 packets/sec)

Zero, negative, or missing workload values are rejected: DEA cannot be computed without a positive workload. Negative ADE (defense saves energy) is valid and recorded as-is.

Power and carbon forms:

```
P_ADE = ADE / duration_seconds                       (watts)
C_ADE = C_attack+defense − C_attack+baseline         (kg CO2, same carbon methodology as Phases 5–6)
```

### Trial Pairing

Multiple trials are paired by trial number across the two configurations:

```
Trial 1: ADE_1 = E_d,1 − E_b,1
Trial 2: ADE_2 = E_d,2 − E_b,2
Trial 3: ADE_3 = E_d,3 − E_b,3
```

Run counts must match across the two lists and trial numbers must align. Unpaired or mismatched trials are rejected.

### Descriptive Statistics

Statistics are calculated over the per-trial values:

| Statistic | Description |
|---|---|
| Mean | Average amplification |
| Median | Middle value |
| Standard deviation | Population spread of values |
| Minimum | Smallest amplification value |
| Maximum | Largest amplification value |

Statistics are reported for amplification energy (ADE), amplification ratio (DEA), power amplification, and amplification carbon. **No hypothesis testing or statistical significance claims are made.**

### Measurement Modes

Every result preserves its measurement mode and energy provider (Phase 6 rules apply unchanged):

| Mode | Description | Status |
|---|---|---|
| ESTIMATED | Deterministic estimation model | **Currently active** |
| MEASURED | Hardware measurement | Requires provider |
| SIMULATED | Simulated reading | Simulated only |

**Important**: Current results are ESTIMATED unless a real energy measurement provider is configured. Estimated energy is never called measured energy, and no hardware measurements are fabricated.

### Carbon Calculation

Uses the existing CarbonGuard carbon methodology (no second formula):

```
energy_kWh = energy_joules / 3,600,000
gross_CO2_kg = energy_kWh × carbon_intensity_g_per_kWh / 1000
```

Carbon is computed for both configurations with `calculate_carbon(..., renewable_percentage=0)` (gross CO2 only), and the amplification carbon is the difference. Default carbon intensity: 475 gCO2/kWh (configurable per calculation).

### Reproducibility

The calculation is a pure deterministic function of the two energy values, workload, duration, and carbon intensity. Repeated computations over identical inputs produce identical outputs. The estimation provider is deterministic and linear in control count; no randomness is used in the energy path.

### Formula Version

Current formula version: `defense_energy_amplification_v1`

Any changes to the calculation methodology will increment this version.

### Limitations

1. **ESTIMATED data**: All current energy values are estimates, not hardware measurements
2. **Linear estimation model**: Estimated runs typically produce a small positive ADE proportional to control count
3. **Single control at a time**: Phase 7 measures one defense configuration against the attack baseline; control-to-control interaction is Phase 6
4. **No significance testing**: Descriptive statistics only
5. **Simulation-based context**: Attack workload and effectiveness come from simulation, not real attacks or real security systems
6. **Single host**: All measurements assume a single computing environment
7. **Safe synthetic simulation only**: No real attacks are executed and no real systems are scanned

---

## Experiment Lifecycle

```
CREATED → VALIDATING → RUNNING → MEASURING → COMPLETED
                            ↓
                         FAILED
```

All experiments are local synthetic simulations. No real attacks are executed.
