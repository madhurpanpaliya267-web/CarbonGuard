from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.models.base import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    event_uuid = Column(String(36), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False, default=_utcnow)
    event_type = Column(String(50), index=True, nullable=False)
    severity = Column(String(20), index=True, nullable=False)
    source_ip = Column(String(45), nullable=False)
    target_ip = Column(String(45), nullable=False)
    target_port = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    status = Column(String(30), index=True, nullable=False, default="detected")
    detection_method = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    risk_score = Column(Float, nullable=True)
    estimated_workload_cpu = Column(Float, nullable=True)
    estimated_energy_kwh = Column(Float, nullable=True)
    estimated_co2_kg = Column(Float, nullable=True)
    metadata_json = Column(Text, nullable=True)

    threats = relationship("Threat", back_populates="event")


class Threat(Base):
    __tablename__ = "threats"

    id = Column(Integer, primary_key=True, index=True)
    threat_uuid = Column(String(36), unique=True, index=True, nullable=False)
    event_id = Column(Integer, ForeignKey("security_events.id"), index=True)
    threat_type = Column(String(50), index=True, nullable=False)
    severity = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    status = Column(String(30), nullable=False, default="active")
    detected_at = Column(DateTime, nullable=False, default=_utcnow)
    resolved_at = Column(DateTime, nullable=True)
    affected_resources = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)
    anomaly_level = Column(Float, nullable=True)

    event = relationship("SecurityEvent", back_populates="threats")
