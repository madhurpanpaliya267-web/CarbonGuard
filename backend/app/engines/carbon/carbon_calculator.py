from typing import Optional

from app.config import settings

# Single conversion constant for the whole project: 1 kWh = 3,600,000 J.
JOULES_PER_KWH = 3_600_000

CARBON_PER_WORKLOAD_AVAILABLE = "available"
CARBON_PER_WORKLOAD_UNAVAILABLE = "unavailable"


def joules_to_kwh(energy_joules: float) -> float:
    """Convert joules to kilowatt-hours (1 kWh = 3,600,000 J)."""
    return energy_joules / JOULES_PER_KWH


def carbon_basis_label(measurement_mode: Optional[str]) -> str:
    """Describe what the carbon figure was calculated from.

    Carbon is never a direct measurement: it is energy multiplied by carbon
    intensity. The label therefore always says "calculated from ..." and names
    the energy basis recorded on the result.
    """
    mode = (measurement_mode or "").strip().upper()
    if mode == "MEASURED":
        return "calculated_from_measured_energy"
    if mode == "ESTIMATED":
        return "calculated_from_estimated_energy"
    if mode == "SIMULATED":
        return "calculated_from_simulated_energy"
    return "calculated_from_unknown_energy_basis"


def calculate_carbon_per_workload(
    carbon_kg: Optional[float],
    workload_value: Optional[float],
    workload_unit: Optional[str],
) -> dict:
    """Carbon per unit of attack workload.

        carbon_per_workload = carbon_kg / workload_value

    The workload unit is preserved verbatim (e.g. ``kg/requests_per_second``).
    Incompatible, missing, zero, or negative workloads are never divided into;
    they return an explicit unavailable state with a human-readable reason
    instead of a fabricated number.
    """
    if carbon_kg is None or not isinstance(carbon_kg, (int, float)) or not (
        carbon_kg == carbon_kg
    ):
        return {
            "value_kg": None,
            "unit": None,
            "status": CARBON_PER_WORKLOAD_UNAVAILABLE,
            "reason": "Carbon value is not available for this result",
        }

    if workload_value is None:
        return {
            "value_kg": None,
            "unit": None,
            "status": CARBON_PER_WORKLOAD_UNAVAILABLE,
            "reason": "Workload value is missing; carbon per workload cannot be computed",
        }

    if not isinstance(workload_value, (int, float)) or workload_value != workload_value:
        return {
            "value_kg": None,
            "unit": None,
            "status": CARBON_PER_WORKLOAD_UNAVAILABLE,
            "reason": f"Workload value is not a finite number: {workload_value!r}",
        }

    if workload_value < 0:
        return {
            "value_kg": None,
            "unit": None,
            "status": CARBON_PER_WORKLOAD_UNAVAILABLE,
            "reason": f"Workload value is negative ({workload_value}); ratio undefined",
        }

    if workload_value == 0:
        return {
            "value_kg": None,
            "unit": None,
            "status": CARBON_PER_WORKLOAD_UNAVAILABLE,
            "reason": "Workload value is zero; division by zero is not permitted",
        }

    unit = (workload_unit or "").strip()
    if not unit:
        return {
            "value_kg": None,
            "unit": None,
            "status": CARBON_PER_WORKLOAD_UNAVAILABLE,
            "reason": "Workload unit is missing; the per-workload unit cannot be preserved",
        }

    return {
        "value_kg": carbon_kg / workload_value,
        "unit": f"kg/{unit}",
        "status": CARBON_PER_WORKLOAD_AVAILABLE,
        "reason": None,
    }


def calculate_carbon(
    energy_kwh: float,
    carbon_intensity: float = None,
    renewable_percentage: float = None,
) -> dict:
    if carbon_intensity is None:
        carbon_intensity = settings.DEFAULT_CARBON_INTENSITY
    if renewable_percentage is None:
        renewable_percentage = settings.DEFAULT_RENEWABLE_PERCENTAGE

    gross_co2_g = energy_kwh * carbon_intensity
    gross_co2_kg = gross_co2_g / 1000

    renewable_offset_kg = gross_co2_kg * (renewable_percentage / 100)
    net_co2_kg = gross_co2_kg - renewable_offset_kg

    breakdown = (
        f"Energy: {energy_kwh} kWh x Carbon Intensity: {carbon_intensity} gCO2/kWh = "
        f"Gross CO2: {gross_co2_g:.2f}g ({gross_co2_kg:.4f}kg). "
        f"Renewable offset ({renewable_percentage}%): -{renewable_offset_kg:.4f}kg. "
        f"Net CO2: {net_co2_kg:.4f}kg."
    )

    return {
        "energy_kwh": energy_kwh,
        "carbon_intensity": carbon_intensity,
        "renewable_pct": renewable_percentage,
        "gross_co2_kg": round(gross_co2_kg, 6),
        "renewable_offset_kg": round(renewable_offset_kg, 6),
        "net_co2_kg": round(net_co2_kg, 6),
        "calculation_breakdown": breakdown,
    }


def estimate_workload_energy(
    cpu_seconds: float,
    memory_mb: float = 256,
    base_power_watts: float = 50,
) -> float:
    memory_power = memory_mb * 0.001
    total_power = base_power_watts + memory_power
    energy_wh = total_power * (cpu_seconds / 3600)
    return round(energy_wh / 1000, 6)


def calculate_security_carbon_efficiency(
    total_threats: int,
    total_security_energy_kwh: float,
    total_security_co2_kg: float,
) -> dict:
    threats_per_kwh = total_threats / max(total_security_energy_kwh, 0.001)
    co2_per_threat = total_security_co2_kg / max(total_threats, 1)
    efficiency_score = min(100, threats_per_kwh * 10)

    if efficiency_score > 80:
        rating = "Excellent"
    elif efficiency_score > 60:
        rating = "Good"
    elif efficiency_score > 40:
        rating = "Fair"
    else:
        rating = "Poor"

    return {
        "threats_per_kwh": round(threats_per_kwh, 2),
        "co2_per_threat": round(co2_per_threat, 6),
        "efficiency_score": round(efficiency_score, 1),
        "rating": rating,
    }
