from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CarbonMetricResponse(BaseModel):
    id: int
    timestamp: datetime
    total_energy_kwh: float
    total_co2_kg: float
    security_energy_kwh: float
    security_co2_kg: float
    carbon_saved_kg: float
    carbon_intensity: float
    renewable_percentage: float
    workload_count: int
    security_carbon_efficiency: Optional[float] = None

    model_config = {"from_attributes": True}


class CarbonOverview(BaseModel):
    current: CarbonMetricResponse
    history: List[CarbonMetricResponse]
    summary: dict


class CarbonCalculationRequest(BaseModel):
    energy_kwh: float
    carbon_intensity: float
    renewable_percentage: float


class CarbonCalculationResponse(BaseModel):
    energy_kwh: float
    carbon_intensity: float
    renewable_pct: float
    gross_co2_kg: float
    renewable_offset_kg: float
    net_co2_kg: float
    calculation_breakdown: str


class SecurityCarbonEfficiency(BaseModel):
    security_workload: float
    energy_consumed: float
    co2_produced: float
    threats_detected: int
    efficiency_score: float
    rating: str
