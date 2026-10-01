import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.repositories.system_repo import SystemMetricRepository


class SystemService:
    def __init__(self, db: Session):
        self.db = db
        self.metric_repo = SystemMetricRepository(db)

    def get_health(self):
        current = self.metric_repo.get_latest()
        if not current:
            current = self._create_current_metrics()
        return current

    def get_history(self, limit: int = 50):
        return self.metric_repo.get_history(limit)

    def _create_current_metrics(self):
        return self.metric_repo.create({
            "cpu_utilization": round(random.uniform(20, 70), 1),
            "memory_utilization": round(random.uniform(30, 75), 1),
            "active_workloads": random.randint(2, 6),
            "security_engine_status": "online",
            "carbon_engine_status": "online",
            "ai_engine_status": "online",
            "database_status": "online",
            "api_status": "online",
            "simulated": True,
        })
