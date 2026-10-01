from sqlalchemy.orm import Session
from app.repositories.carbon_repo import EnergyMetricRepository
from app.engines.carbon.energy_estimator import estimate_energy_consumption


class EnergyService:
    def __init__(self, db: Session):
        self.db = db
        self.energy_repo = EnergyMetricRepository(db)

    def get_overview(self) -> dict:
        current = self.energy_repo.get_latest()
        history = self.energy_repo.get_history(30)

        if not current:
            current_data = estimate_energy_consumption()
            current_data.pop("measurement_mode", None)
            current = self.energy_repo.create(current_data)

        return {
            "current": current,
            "history": history,
            "summary": {
                "total_energy": round(sum(m.energy_kwh for m in history), 4),
                "avg_power": round(
                    sum(m.total_power_watts for m in history) / max(len(history), 1), 1
                ),
            },
        }

    def get_current(self):
        current = self.energy_repo.get_latest()
        if not current:
            current_data = estimate_energy_consumption()
            current_data.pop("measurement_mode", None)
            current = self.energy_repo.create(current_data)
        return current

    def get_history(self, limit: int = 30):
        return self.energy_repo.get_history(limit)
