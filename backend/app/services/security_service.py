from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from app.repositories.security_repo import SecurityEventRepository, ThreatRepository
from app.engines.security.threat_detector import detect_event, generate_event_uuid
from app.engines.security.risk_analyzer import analyze_risk
from app.engines.security.attack_simulator import simulate_attack
from app.engines.carbon.carbon_calculator import calculate_carbon
from app.engines.ai.recommendation_engine import generate_recommendations


class SecurityService:
    def __init__(self, db: Session):
        self.db = db
        self.event_repo = SecurityEventRepository(db)
        self.threat_repo = ThreatRepository(db)

    def get_events(
        self,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        offset = (page - 1) * page_size
        events = self.event_repo.filter_events(
            severity=severity,
            event_type=event_type,
            status=status,
            offset=offset,
            limit=page_size,
        )
        total = self.event_repo.count()
        return {
            "items": events,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_event(self, event_id: int):
        return self.event_repo.get_by_id(event_id)

    def simulate(self, attack_type: str) -> dict:
        result = simulate_attack(attack_type)

        event_data = result["event"]
        if isinstance(event_data.get("timestamp"), str):
            event_data["timestamp"] = datetime.fromisoformat(event_data["timestamp"])
        event = self.event_repo.create(event_data)

        threat_data = result["threat"]
        threat_data["event_id"] = event.id
        if isinstance(threat_data.get("detected_at"), str):
            threat_data["detected_at"] = datetime.fromisoformat(threat_data["detected_at"])
        threat = self.threat_repo.create(threat_data)

        return {
            "event": event,
            "threat": threat,
            "risk_assessment": result["risk_assessment"],
            "workload_impact": result["workload_impact"],
            "energy_impact": result["energy_impact"],
            "carbon_impact": result["carbon_impact"],
            "ai_recommendation": result["ai_recommendation"],
            "pipeline": result["pipeline"],
        }
