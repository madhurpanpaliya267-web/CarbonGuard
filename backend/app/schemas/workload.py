from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class WorkloadResponse(BaseModel):
    id: int
    workload_uuid: str
    name: str
    workload_type: str
    priority: str
    is_security_critical: bool
    estimated_cpu_seconds: float
    estimated_memory_mb: Optional[float] = None
    estimated_energy_kwh: float
    estimated_co2_kg: float
    status: str
    scheduled_time: Optional[datetime] = None
    optimized_time: Optional[datetime] = None
    carbon_intensity_at_exec: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class OptimizationResultResponse(BaseModel):
    id: int
    run_timestamp: datetime
    workloads_analyzed: int
    workloads_shifted: int
    workloads_unchanged: int
    critical_protected: int
    energy_before_kwh: float
    energy_after_kwh: float
    co2_before_kg: float
    co2_after_kg: float
    energy_saved_kwh: float
    co2_saved_kg: float
    reduction_percentage: float
    details_json: Optional[str] = None

    model_config = {"from_attributes": True}


class OptimizationComparison(BaseModel):
    before: dict
    after: dict
    comparison: dict
    details: List[dict]
