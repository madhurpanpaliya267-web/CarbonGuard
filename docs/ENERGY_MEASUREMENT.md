# Energy Measurement Architecture

## Overview

CarbonGuard uses an extensible energy measurement provider architecture. The system distinguishes between three measurement modes:

| Mode | Label | Description |
|------|-------|-------------|
| MEASURED | `MEASURED` | Real hardware telemetry (Intel RAPL, Kepler, external power meter) |
| ESTIMATED | `ESTIMATED` | Computed from workload parameters using a configurable estimation model |
| SIMULATED | `SIMULATED` | Generated for demonstration, not tied to real workload |

**Current status**: All energy values in CarbonGuard are **ESTIMATED** unless a real measurement provider is configured and available.

## Architecture

```
EnergyMeasurementProvider (abstract)
    |
    +-- EstimatedEnergyProvider    (default, always available)
    |
    +-- RaplEnergyProvider         (stub, requires Linux + Intel RAPL)
    |
    +-- KeplerEnergyProvider       (stub, requires Kubernetes + Kepler)
    |
    +-- ExternalMeterProvider      (stub, requires physical power meter)
```

### Provider Interface

```python
class EnergyMeasurementProvider(ABC):
    def get_measurement(
        self,
        duration_seconds: float,
        cpu_usage_pct: Optional[float] = None,
        memory_usage_pct: Optional[float] = None,
        network_usage_mbps: Optional[float] = None,
        workload_count: int = 1,
        security_controls_active: int = 0,
        attack_intensity: Optional[str] = None,
    ) -> EnergyReading: ...

    def get_mode(self) -> MeasurementMode: ...
    def get_source_name(self) -> str: ...
    def is_available(self) -> bool: ...
```

### EnergyReading

```python
@dataclass
class EnergyReading:
    energy_joules: float
    power_watts: float
    duration_seconds: float
    source: str
    mode: MeasurementMode
    timestamp: datetime
    cpu_usage_pct: Optional[float]
    memory_usage_pct: Optional[float]
    network_usage_mbps: Optional[float]
    metadata: Optional[dict]
```

## EstimatedEnergyProvider

The default provider uses a deterministic estimation model based on configurable coefficients.

### Formula

```
total_power = (
    base_power_watts
    + cpu_coefficient * cpu_usage_pct
    + memory_coefficient * memory_usage_pct
    + network_coefficient * network_usage_mbps
    + workload_count_coefficient * (workload_count - 1)
    + security_controls_active * control_base_overhead_watts
) * intensity_multiplier

energy_joules = total_power * duration_seconds
```

### Default Coefficients

| Coefficient | Default | Description |
|------------|---------|-------------|
| `base_power_watts` | 100.0 | Base system power consumption |
| `cpu_coefficient` | 3.0 | Power per 1% CPU utilization |
| `memory_coefficient` | 0.5 | Power per 1% memory utilization |
| `network_coefficient` | 0.1 | Power per Mbps network traffic |
| `workload_count_coefficient` | 5.0 | Additional power per workload |
| `control_base_overhead_watts` | 2.0 | Base overhead per security control |
| `intensity_multipliers` | LOW=0.5, MEDIUM=1.0, HIGH=2.0 | Attack intensity scaling |

### Configuration

Coefficients can be configured via environment variables:

```
ENERGY_PROVIDER=estimated
ENERGY_BASE_POWER_WATTS=100.0
ENERGY_CPU_COEFFICIENT=3.0
ENERGY_MEMORY_COEFFICIENT=0.5
ENERGY_NETWORK_COEFFICIENT=0.1
ENERGY_WORKLOAD_COUNT_COEFFICIENT=5.0
ENERGY_CONTROL_BASE_OVERHEAD_WATTS=2.0
ENERGY_CONTROL_INTENSITY_MULTIPLIER=1.5
```

### Determinism

The EstimatedEnergyProvider is **deterministic**: given identical inputs, it always produces identical outputs. This is critical for reproducible research experiments.

## Provider Selection

```python
from app.engines.energy.factory import get_provider, get_default_provider

# Get default provider (configured via ENERGY_PROVIDER env var)
provider = get_default_provider()

# Get specific provider
provider = get_provider("estimated")
provider = get_provider("rapl")
```

## Future Provider Integration

### Intel RAPL

Requires:
- Linux OS with Intel RAPL support
- Access to `/sys/class/powercap/intel-rapl:0/energy_uj`
- Root or appropriate group membership

The RAPL provider would read energy counters before and after the measurement period and compute delta.

### Kepler

Requires:
- Kubernetes cluster
- Kepler operator deployed
- Access to Kepler Prometheus metrics

The Kepler provider would query `container_energy_joules` or `node_energy_joules` metrics.

### External Power Meter

Requires:
- Physical power meter (PDU, smart plug, dedicated analyzer)
- API or serial interface connection

The external meter provider would read instantaneous power readings and compute energy over the measurement duration.

## Limitations

1. Current energy values are ESTIMATED unless a real measurement provider is configured
2. The estimation model uses simplified linear coefficients
3. Real hardware energy consumption includes non-linear effects not captured by the model
4. Coefficients are not calibrated to specific hardware — they represent general approximations
5. The model does not account for thermal effects, power supply efficiency, or other hardware-specific factors
