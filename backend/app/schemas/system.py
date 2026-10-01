from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SystemMetricResponse(BaseModel):
    id: int
    timestamp: datetime
    cpu_utilization: float
    memory_utilization: float
    active_workloads: int
    security_engine_status: str
    carbon_engine_status: str
    ai_engine_status: str
    database_status: str
    api_status: str
    simulated: bool

    model_config = {"from_attributes": True}


class SystemHealthStatus(BaseModel):
    cpu_utilization: float
    memory_utilization: float
    active_workloads: int
    security_engine_status: str
    carbon_engine_status: str
    ai_engine_status: str
    database_status: str
    api_status: str
    simulated: bool


class SystemSettingResponse(BaseModel):
    id: int
    key: str
    value: str
    category: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class SystemSettingUpdate(BaseModel):
    key: str
    value: str
