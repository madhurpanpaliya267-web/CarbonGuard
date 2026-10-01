from typing import Optional
from app.engines.energy.provider import EnergyMeasurementProvider, EnergyReading, MeasurementMode


class RaplEnergyProvider(EnergyMeasurementProvider):
    """Intel RAPL energy measurement provider.

    Requires Linux with Intel RAPL support and appropriate permissions.
    On Windows or unsupported hardware, is_available() returns False.

    To enable in the future:
    - Read from /sys/class/powercap/intel-rapl:0/energy_uj on Linux
    - Convert microjoules to joules
    - Requires root or appropriate group membership
    """

    def get_measurement(
        self,
        duration_seconds: float,
        cpu_usage_pct: Optional[float] = None,
        memory_usage_pct: Optional[float] = None,
        network_usage_mbps: Optional[float] = None,
        workload_count: int = 1,
        security_controls_active: int = 0,
        attack_intensity: Optional[str] = None,
    ) -> EnergyReading:
        raise NotImplementedError(
            "RAPL provider is not yet implemented. "
            "Requires Linux with Intel RAPL support and "
            "access to /sys/class/powercap/intel-rapl:0/energy_uj."
        )

    def get_mode(self) -> MeasurementMode:
        return MeasurementMode.MEASURED

    def get_source_name(self) -> str:
        return "rapl"

    def is_available(self) -> bool:
        return False


class KeplerEnergyProvider(EnergyMeasurementProvider):
    """Kepler (Kubernetes-based Efficient Power Level Exporter) energy provider.

    Requires a Kubernetes cluster with Kepler deployed.
    Kepler provides container/pod/node-level energy measurements.

    To enable in the future:
    - Query Kepler Prometheus metrics endpoint
    - Use container_energy_joules or node_energy_joules metrics
    - Requires Kubernetes cluster with Kepler operator installed
    """

    def get_measurement(
        self,
        duration_seconds: float,
        cpu_usage_pct: Optional[float] = None,
        memory_usage_pct: Optional[float] = None,
        network_usage_mbps: Optional[float] = None,
        workload_count: int = 1,
        security_controls_active: int = 0,
        attack_intensity: Optional[str] = None,
    ) -> EnergyReading:
        raise NotImplementedError(
            "Kepler provider is not yet implemented. "
            "Requires a Kubernetes cluster with Kepler deployed."
        )

    def get_mode(self) -> MeasurementMode:
        return MeasurementMode.MEASURED

    def get_source_name(self) -> str:
        return "kepler"

    def is_available(self) -> bool:
        return False


class ExternalMeterProvider(EnergyMeasurementProvider):
    """External power meter provider.

    For integration with physical power meters (e.g., PDU, smart plug,
    dedicated power analyzer).

    To enable in the future:
    - Read from meter API or serial interface
    - Requires configured hardware connection
    """

    def get_measurement(
        self,
        duration_seconds: float,
        cpu_usage_pct: Optional[float] = None,
        memory_usage_pct: Optional[float] = None,
        network_usage_mbps: Optional[float] = None,
        workload_count: int = 1,
        security_controls_active: int = 0,
        attack_intensity: Optional[str] = None,
    ) -> EnergyReading:
        raise NotImplementedError(
            "External meter provider is not yet implemented. "
            "Requires configured physical power meter hardware."
        )

    def get_mode(self) -> MeasurementMode:
        return MeasurementMode.MEASURED

    def get_source_name(self) -> str:
        return "external_meter"

    def is_available(self) -> bool:
        return False
