from app.config import settings


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
