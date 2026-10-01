from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DashboardMetrics(BaseModel):
    carbon_guard_score: float
    security_risk_score: float
    current_threat_level: str
    active_threats: int
    threats_detected_24h: int
    threats_blocked_24h: int
    energy_consumption_kwh: float
    estimated_co2_kg: float
    carbon_saved_kg: float
    renewable_percentage: float
    current_workload: int
    security_carbon_efficiency: float


class ChartDataPoint(BaseModel):
    timestamp: datetime
    value: float
    label: Optional[str] = None


class ThreatActivityChart(BaseModel):
    data_points: List[dict]


class CarbonEmissionsChart(BaseModel):
    data_points: List[dict]


class EnergyConsumptionChart(BaseModel):
    data_points: List[dict]


class CarbonSavingsChart(BaseModel):
    data_points: List[dict]


class ThreatCategoriesChart(BaseModel):
    categories: List[dict]


class ThreatSeverityChart(BaseModel):
    severities: List[dict]
