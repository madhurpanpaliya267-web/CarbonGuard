from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
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
    source: str
    mode: MeasurementMode
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    cpu_usage_pct: Optional[float] = None
    memory_usage_pct: Optional[float] = None
    network_usage_mbps: Optional[float] = None
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "energy_joules": self.energy_joules,
            "power_watts": self.power_watts,
            "duration_seconds": self.duration_seconds,
            "source": self.source,
            "mode": self.mode.value,
            "timestamp": self.timestamp.isoformat(),
            "cpu_usage_pct": self.cpu_usage_pct,
            "memory_usage_pct": self.memory_usage_pct,
            "network_usage_mbps": self.network_usage_mbps,
            "metadata": self.metadata,
        }

    @property
    def energy_kwh(self) -> float:
        return self.energy_joules / 3_600_000


class EnergyMeasurementProvider(ABC):
    @abstractmethod
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
        ...

    @abstractmethod
    def get_mode(self) -> MeasurementMode:
        ...

    @abstractmethod
    def get_source_name(self) -> str:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...
