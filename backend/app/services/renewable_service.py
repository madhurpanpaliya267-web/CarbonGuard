import random
from datetime import datetime, timedelta, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_renewable_status() -> dict:
    solar = random.uniform(20, 80)
    wind = random.uniform(10, 60)
    renewable_pct = (solar + wind) / 2
    carbon_intensity = 475 * (1 - renewable_pct / 200)

    forecast = []
    now = _utcnow()
    for i in range(24):
        ts = now + timedelta(hours=i)
        f_solar = max(0, 80 - abs(i - 12) * 6 + random.uniform(-10, 10))
        f_wind = random.uniform(15, 55)
        f_renewable = (f_solar + f_wind) / 2
        f_intensity = 475 * (1 - f_renewable / 200)
        forecast.append({
            "timestamp": ts.isoformat(),
            "solar": round(f_solar, 1),
            "wind": round(f_wind, 1),
            "renewable_pct": round(f_renewable, 1),
            "carbon_intensity": round(f_intensity, 1),
        })

    return {
        "renewable_percentage": round(renewable_pct, 1),
        "solar_availability": round(solar, 1),
        "wind_availability": round(wind, 1),
        "grid_carbon_intensity": round(carbon_intensity, 1),
        "forecast": forecast,
    }
