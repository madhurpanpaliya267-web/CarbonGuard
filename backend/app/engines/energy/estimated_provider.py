from dataclasses import dataclass, field
from typing import Optional
from app.engines.energy.provider import EnergyMeasurementProvider, EnergyReading, MeasurementMode


@dataclass
class EstimationCoefficients:
    base_power_watts: float = 100.0
    cpu_coefficient: float = 3.0
    memory_coefficient: float = 0.5
    network_coefficient: float = 0.1
    workload_count_coefficient: float = 5.0
    control_base_overhead_watts: float = 2.0
    control_intensity_multiplier: float = 1.5
    intensity_multipliers: dict = field(default_factory=lambda: {
        "LOW": 0.5,
        "MEDIUM": 1.0,
        "HIGH": 2.0,
    })


DEFAULT_COEFFICIENTS = EstimationCoefficients()


class EstimatedEnergyProvider(EnergyMeasurementProvider):
    def __init__(self, coefficients: Optional[EstimationCoefficients] = None):
        self.coefficients = coefficients or DEFAULT_COEFFICIENTS

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
        c = self.coefficients
        cpu = cpu_usage_pct if cpu_usage_pct is not None else 20.0
        mem = memory_usage_pct if memory_usage_pct is not None else 30.0
        net = network_usage_mbps if network_usage_mbps is not None else 0.0

        base = c.base_power_watts
        cpu_power = c.cpu_coefficient * cpu
        mem_power = c.memory_coefficient * mem
        net_power = c.network_coefficient * net
        workload_power = c.workload_count_coefficient * max(0, workload_count - 1)
        control_power = security_controls_active * c.control_base_overhead_watts

        intensity_mult = 1.0
        if attack_intensity and attack_intensity in c.intensity_multipliers:
            intensity_mult = c.intensity_multipliers[attack_intensity]

        total_power = (base + cpu_power + mem_power + net_power + workload_power + control_power) * intensity_mult
        energy_joules = total_power * duration_seconds

        return EnergyReading(
            energy_joules=round(energy_joules, 6),
            power_watts=round(total_power, 6),
            duration_seconds=duration_seconds,
            source="estimated",
            mode=MeasurementMode.ESTIMATED,
            cpu_usage_pct=cpu,
            memory_usage_pct=mem,
            network_usage_mbps=net,
            metadata={
                "coefficients": {
                    "base_power_watts": c.base_power_watts,
                    "cpu_coefficient": c.cpu_coefficient,
                    "memory_coefficient": c.memory_coefficient,
                    "network_coefficient": c.network_coefficient,
                    "workload_count_coefficient": c.workload_count_coefficient,
                    "control_base_overhead_watts": c.control_base_overhead_watts,
                    "intensity_multipliers": c.intensity_multipliers,
                },
                "workload_count": workload_count,
                "security_controls_active": security_controls_active,
                "attack_intensity": attack_intensity,
                "intensity_multiplier": intensity_mult,
            },
        )

    def get_mode(self) -> MeasurementMode:
        return MeasurementMode.ESTIMATED

    def get_source_name(self) -> str:
        return "estimated"

    def is_available(self) -> bool:
        return True
