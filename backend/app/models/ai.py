from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from datetime import datetime, timezone
from app.models.base import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=_utcnow)
    recommendation_type = Column(String(50), index=True, nullable=False)
    recommendation = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default="medium")
    reason = Column(Text, nullable=False)
    expected_security_impact = Column(Text, nullable=True)
    expected_carbon_impact = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    factors_json = Column(Text, nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    is_dismissed = Column(Boolean, nullable=False, default=False)
