from typing import Optional
from app.engines.energy.provider import MeasurementMode
from app.engines.energy.factory import get_default_provider


def estimate_energy_consumption(workload_count: int = 1) -> dict:
    provider = get_default_provider()
    reading = provider.get_measurement(
        duration_seconds=1.0,
        workload_count=workload_count,
    )
    return {
        "total_power_watts": reading.power_watts,
        "cpu_power_watts": round(reading.cpu_usage_pct * 3.0, 1) if reading.cpu_usage_pct else 60.0,
        "memory_power_watts": round(reading.memory_usage_pct * 0.5, 1) if reading.memory_usage_pct else 15.0,
        "network_power_watts": round(reading.network_usage_mbps * 0.1, 1) if reading.network_usage_mbps else 0.0,
        "energy_kwh": reading.energy_kwh,
        "estimated": True,
        "measurement_mode": reading.mode.value,
    }


def estimate_security_workload_energy(security_events_count: int) -> dict:
    provider = get_default_provider()
    base_per_event_joules = 25.0
    total_joules = security_events_count * base_per_event_joules
    duration = max(security_events_count * 30, 1)

    reading = provider.get_measurement(
        duration_seconds=duration,
        workload_count=security_events_count,
    )

    scaled_energy_joules = total_joules * (reading.power_watts / max(reading.power_watts, 1))
    energy_kwh = scaled_energy_joules / 3_600_000
    power_watts = scaled_energy_joules / max(duration, 1)

    return {
        "energy_kwh": round(energy_kwh, 6),
        "power_watts": round(power_watts, 1),
        "events_processed": security_events_count,
        "estimated": True,
        "measurement_mode": reading.mode.value,
    }
