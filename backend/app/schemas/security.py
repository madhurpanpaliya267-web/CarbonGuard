from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int


class SecurityEventBase(BaseModel):
    event_type: str
    severity: str
    source_ip: str
    target_ip: str
    target_port: Optional[int] = None
    confidence: float
    status: str
    detection_method: Optional[str] = None
    description: Optional[str] = None


class SecurityEventCreate(SecurityEventBase):
    event_uuid: str
    risk_score: Optional[float] = None
    estimated_workload_cpu: Optional[float] = None
    estimated_energy_kwh: Optional[float] = None
    estimated_co2_kg: Optional[float] = None
    metadata_json: Optional[str] = None


class SecurityEventResponse(SecurityEventBase):
    id: int
    event_uuid: str
    timestamp: datetime
    risk_score: Optional[float] = None
    estimated_workload_cpu: Optional[float] = None
    estimated_energy_kwh: Optional[float] = None
    estimated_co2_kg: Optional[float] = None
    metadata_json: Optional[str] = None

    model_config = {"from_attributes": True}


class SecurityEventListResponse(PaginatedResponse):
    items: List[SecurityEventResponse]


class ThreatResponse(BaseModel):
    id: int
    threat_uuid: str
    event_id: Optional[int] = None
    threat_type: str
    severity: str
    confidence: float
    risk_score: float
    status: str
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    affected_resources: Optional[str] = None
    explanation: Optional[str] = None
    recommended_action: Optional[str] = None
    anomaly_level: Optional[float] = None

    model_config = {"from_attributes": True}


class ThreatListResponse(PaginatedResponse):
    items: List[ThreatResponse]


class ThreatExplanationResponse(BaseModel):
    prediction: str
    confidence: float
    factors: List[dict]
    reasoning: str
    recommended_action: str


class RiskAssessment(BaseModel):
    risk_score: float
    severity: str
    confidence: float
    factors: List[dict]


class SimulationRequest(BaseModel):
    attack_type: str


class SimulationResult(BaseModel):
    event: SecurityEventResponse
    threat: ThreatResponse
    risk_assessment: RiskAssessment
    workload_impact: dict
    energy_impact: dict
    carbon_impact: dict
    ai_recommendation: dict
    pipeline: List[dict]
