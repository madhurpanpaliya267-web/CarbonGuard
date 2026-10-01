import random
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.repositories.security_repo import SecurityEventRepository, ThreatRepository
from app.repositories.carbon_repo import CarbonMetricRepository, EnergyMetricRepository
from app.repositories.workload_repo import WorkloadRepository
from app.repositories.ai_repo import AIRecommendationRepository
from app.repositories.system_repo import SystemMetricRepository


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_metrics(self) -> dict:
        event_repo = SecurityEventRepository(self.db)
        threat_repo = ThreatRepository(self.db)
        carbon_repo = CarbonMetricRepository(self.db)
        energy_repo = EnergyMetricRepository(self.db)
        workload_repo = WorkloadRepository(self.db)
        ai_repo = AIRecommendationRepository(self.db)
        system_repo = SystemMetricRepository(self.db)

        active_threats = threat_repo.count_active()
        total_events = event_repo.count()
        carbon = carbon_repo.get_latest()
        energy = energy_repo.get_latest()
        system = system_repo.get_latest()

        carbon_guard_score = random.uniform(75, 95)
        security_risk_score = random.uniform(20, 60)
        threat_levels = ["LOW", "MEDIUM", "HIGH"]
        current_threat_level = threat_levels[min(active_threats, 2)]

        return {
            "carbon_guard_score": round(carbon_guard_score, 1),
            "security_risk_score": round(security_risk_score, 1),
            "current_threat_level": current_threat_level,
            "active_threats": active_threats,
            "threats_detected_24h": random.randint(10, 30),
            "threats_blocked_24h": random.randint(8, 25),
            "energy_consumption_kwh": round(random.uniform(1.5, 5.0), 2),
            "estimated_co2_kg": round(random.uniform(0.5, 2.5), 2),
            "carbon_saved_kg": round(random.uniform(0.5, 5.0), 2),
            "renewable_percentage": round(random.uniform(20, 50), 1),
            "current_workload": random.randint(3, 8),
            "security_carbon_efficiency": round(random.uniform(60, 90), 1),
        }

    def get_threat_activity_chart(self, period: str = "24h") -> dict:
        now = _utcnow()
        data_points = []
        for i in range(24):
            ts = now - timedelta(hours=23 - i)
            data_points.append({
                "timestamp": ts.isoformat(),
                "count": random.randint(0, 8),
                "critical": random.randint(0, 2),
                "high": random.randint(0, 3),
                "medium": random.randint(0, 4),
                "low": random.randint(0, 5),
            })
        return {"data_points": data_points}

    def get_carbon_emissions_chart(self, period: str = "24h") -> dict:
        now = _utcnow()
        data_points = []
        for i in range(24):
            ts = now - timedelta(hours=23 - i)
            data_points.append({
                "timestamp": ts.isoformat(),
                "co2_kg": round(random.uniform(0.02, 0.15), 4),
                "energy_kwh": round(random.uniform(0.05, 0.3), 4),
            })
        return {"data_points": data_points}

    def get_energy_consumption_chart(self, period: str = "24h") -> dict:
        now = _utcnow()
        data_points = []
        for i in range(24):
            ts = now - timedelta(hours=23 - i)
            data_points.append({
                "timestamp": ts.isoformat(),
                "total": round(random.uniform(0.1, 0.5), 4),
                "security": round(random.uniform(0.02, 0.15), 4),
                "non_security": round(random.uniform(0.05, 0.3), 4),
            })
        return {"data_points": data_points}

    def get_carbon_savings_chart(self) -> dict:
        now = _utcnow()
        data_points = []
        cumulative = 0
        for i in range(30):
            ts = now - timedelta(days=29 - i)
            saved = round(random.uniform(0.1, 1.5), 2)
            cumulative += saved
            data_points.append({
                "timestamp": ts.isoformat(),
                "saved_kg": saved,
                "cumulative_saved_kg": round(cumulative, 2),
            })
        return {"data_points": data_points}

    def get_threat_categories_chart(self) -> dict:
        categories = [
            {"type": "DDoS", "count": random.randint(5, 15), "percentage": 0},
            {"type": "Brute Force", "count": random.randint(3, 10), "percentage": 0},
            {"type": "Port Scan", "count": random.randint(8, 20), "percentage": 0},
            {"type": "SQL Injection", "count": random.randint(2, 8), "percentage": 0},
            {"type": "Malware", "count": random.randint(1, 5), "percentage": 0},
            {"type": "Suspicious Login", "count": random.randint(4, 12), "percentage": 0},
        ]
        total = sum(c["count"] for c in categories)
        for c in categories:
            c["percentage"] = round(c["count"] / max(total, 1) * 100, 1)
        return {"categories": categories}

    def get_threat_severity_chart(self) -> dict:
        severities = [
            {"level": "CRITICAL", "count": random.randint(1, 5), "percentage": 0},
            {"level": "HIGH", "count": random.randint(3, 10), "percentage": 0},
            {"level": "MEDIUM", "count": random.randint(5, 15), "percentage": 0},
            {"level": "LOW", "count": random.randint(8, 20), "percentage": 0},
        ]
        total = sum(s["count"] for s in severities)
        for s in severities:
            s["percentage"] = round(s["count"] / max(total, 1) * 100, 1)
        return {"severities": severities}
