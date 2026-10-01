from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime, timezone
from app.models.base import Base


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CarbonMetric(Base):
    __tablename__ = "carbon_metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True, nullable=False, default=_utcnow)
    total_energy_kwh = Column(Float, nullable=False, default=0.0)
    total_co2_kg = Column(Float, nullable=False, default=0.0)
    security_energy_kwh = Column(Float, nullable=False, default=0.0)
    security_co2_kg = Column(Float, nullable=False, default=0.0)
    carbon_saved_kg = Column(Float, nullable=False, default=0.0)
    carbon_intensity = Column(Float, nullable=False, default=475.0)
    renewable_percentage = Column(Float, nullable=False, default=25.0)
    workload_count = Column(Integer, nullable=False, default=0)
    security_carbon_efficiency = Column(Float, nullable=True)


class EnergyMetric(Base):
    __tablename__ = "energy_metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True, nullable=False, default=_utcnow)
    total_power_watts = Column(Float, nullable=False, default=0.0)
    cpu_power_watts = Column(Float, nullable=True)
    memory_power_watts = Column(Float, nullable=True)
    network_power_watts = Column(Float, nullable=True)
    energy_kwh = Column(Float, nullable=False, default=0.0)
    estimated = Column(Boolean, nullable=False, default=True)
