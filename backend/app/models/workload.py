from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from datetime import datetime, timezone
from app.models.base import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Workload(Base):
    __tablename__ = "workloads"

    id = Column(Integer, primary_key=True, index=True)
    workload_uuid = Column(String(36), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    workload_type = Column(String(50), nullable=False)
    priority = Column(String(20), nullable=False, default="medium")
    is_security_critical = Column(Boolean, nullable=False, default=False)
    estimated_cpu_seconds = Column(Float, nullable=False, default=0.0)
    estimated_memory_mb = Column(Float, nullable=True)
    estimated_energy_kwh = Column(Float, nullable=False, default=0.0)
    estimated_co2_kg = Column(Float, nullable=False, default=0.0)
    status = Column(String(30), nullable=False, default="pending")
    scheduled_time = Column(DateTime, nullable=True)
    optimized_time = Column(DateTime, nullable=True)
    carbon_intensity_at_exec = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    completed_at = Column(DateTime, nullable=True)


class OptimizationResult(Base):
    __tablename__ = "optimization_results"

    id = Column(Integer, primary_key=True, index=True)
    run_timestamp = Column(DateTime, nullable=False, default=_utcnow)
    workloads_analyzed = Column(Integer, nullable=False, default=0)
    workloads_shifted = Column(Integer, nullable=False, default=0)
    workloads_unchanged = Column(Integer, nullable=False, default=0)
    critical_protected = Column(Integer, nullable=False, default=0)
    energy_before_kwh = Column(Float, nullable=False, default=0.0)
    energy_after_kwh = Column(Float, nullable=False, default=0.0)
    co2_before_kg = Column(Float, nullable=False, default=0.0)
    co2_after_kg = Column(Float, nullable=False, default=0.0)
    energy_saved_kwh = Column(Float, nullable=False, default=0.0)
    co2_saved_kg = Column(Float, nullable=False, default=0.0)
    reduction_percentage = Column(Float, nullable=False, default=0.0)
    details_json = Column(Text, nullable=True)
