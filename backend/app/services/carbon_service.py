from sqlalchemy.orm import Session
from datetime import datetime
from app.repositories.carbon_repo import CarbonMetricRepository, EnergyMetricRepository
from app.engines.carbon.carbon_calculator import (
    calculate_carbon,
    calculate_security_carbon_efficiency,
)
from app.repositories.security_repo import ThreatRepository


class CarbonService:
    def __init__(self, db: Session):
        self.db = db
        self.carbon_repo = CarbonMetricRepository(db)
        self.energy_repo = EnergyMetricRepository(db)
        self.threat_repo = ThreatRepository(db)

    def get_overview(self) -> dict:
        current = self.carbon_repo.get_latest()
        history = self.carbon_repo.get_history(30)

        if not current:
            current = self.carbon_repo.create({
                "total_energy_kwh": 3.2,
                "total_co2_kg": 1.52,
                "security_energy_kwh": 0.8,
                "security_co2_kg": 0.38,
                "carbon_saved_kg": 2.1,
                "carbon_intensity": 475.0,
                "renewable_percentage": 34.0,
                "workload_count": 5,
                "security_carbon_efficiency": 72.5,
            })

        return {
            "current": current,
            "history": history,
            "summary": {
                "total_energy": round(sum(m.total_energy_kwh for m in history), 2),
                "total_co2": round(sum(m.total_co2_kg for m in history), 2),
                "total_saved": round(sum(m.carbon_saved_kg for m in history), 2),
                "avg_efficiency": round(
                    sum(m.security_carbon_efficiency or 0 for m in history) / max(len(history), 1), 1
                ),
            },
        }

    def get_current(self):
        current = self.carbon_repo.get_latest()
        if not current:
            current = self.carbon_repo.create({
                "total_energy_kwh": 3.2,
                "total_co2_kg": 1.52,
                "security_energy_kwh": 0.8,
                "security_co2_kg": 0.38,
                "carbon_saved_kg": 2.1,
                "carbon_intensity": 475.0,
                "renewable_percentage": 34.0,
                "workload_count": 5,
                "security_carbon_efficiency": 72.5,
            })
        return current

    def get_history(self, limit: int = 30):
        return self.carbon_repo.get_history(limit)

    def calculate(self, energy_kwh: float, carbon_intensity: float, renewable_percentage: float):
        return calculate_carbon(energy_kwh, carbon_intensity, renewable_percentage)

    def get_efficiency(self):
        total_threats = self.threat_repo.count_active()
        current = self.carbon_repo.get_latest()
        energy = current.security_energy_kwh if current else 0.8
        co2 = current.security_co2_kg if current else 0.38

        return calculate_security_carbon_efficiency(total_threats, energy, co2)
