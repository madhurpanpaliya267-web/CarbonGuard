from typing import Optional
from sqlalchemy.orm import Session
from app.repositories.ai_repo import AIRecommendationRepository
from app.engines.ai.recommendation_engine import generate_recommendations


class AIService:
    def __init__(self, db: Session):
        self.db = db
        self.rec_repo = AIRecommendationRepository(db)

    def get_recommendations(
        self,
        recommendation_type: Optional[str] = None,
        priority: Optional[str] = None,
        unread_only: bool = False,
    ):
        recs = self.rec_repo.get_all()
        if recommendation_type:
            recs = [r for r in recs if r.recommendation_type == recommendation_type]
        if priority:
            recs = [r for r in recs if r.priority == priority]
        if unread_only:
            recs = [r for r in recs if not r.is_read]
        return recs

    def generate(self):
        import random
        active_threats = random.randint(0, 5)
        energy_kwh = random.uniform(1.5, 5.0)
        co2_kg = energy_kwh * 475 / 1000
        renewable_pct = random.uniform(20, 60)
        carbon_intensity = 475 * (1 - renewable_pct / 200)
        workload_count = random.randint(3, 8)
        recent_events = random.randint(5, 20)

        recs = generate_recommendations(
            active_threats=active_threats,
            energy_kwh=energy_kwh,
            co2_kg=co2_kg,
            renewable_pct=renewable_pct,
            carbon_intensity=carbon_intensity,
            workload_count=workload_count,
            recent_events_count=recent_events,
        )

        created = []
        for rec in recs:
            import json
            db_rec = self.rec_repo.create({
                "recommendation_type": rec["recommendation_type"],
                "recommendation": rec["recommendation"],
                "priority": rec["priority"],
                "reason": rec["reason"],
                "expected_security_impact": rec.get("expected_security_impact"),
                "expected_carbon_impact": rec.get("expected_carbon_impact"),
                "confidence": rec["confidence"],
                "factors_json": json.dumps(rec.get("factors", [])),
            })
            created.append(db_rec)

        return created

    def mark_read(self, rec_id: int):
        return self.rec_repo.mark_read(rec_id)

    def dismiss(self, rec_id: int):
        return self.rec_repo.dismiss(rec_id)
