from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime, timezone
from app.models.base import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SystemMetric(Base):
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True, nullable=False, default=_utcnow)
    cpu_utilization = Column(Float, nullable=False, default=0.0)
    memory_utilization = Column(Float, nullable=False, default=0.0)
    active_workloads = Column(Integer, nullable=False, default=0)
    security_engine_status = Column(String(20), nullable=False, default="online")
    carbon_engine_status = Column(String(20), nullable=False, default="online")
    ai_engine_status = Column(String(20), nullable=False, default="online")
    database_status = Column(String(20), nullable=False, default="online")
    api_status = Column(String(20), nullable=False, default="online")
    simulated = Column(Boolean, nullable=False, default=True)
