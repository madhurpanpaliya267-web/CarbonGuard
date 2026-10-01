from pydantic import BaseModel
from typing import Optional, List


class EventLogResponse(BaseModel):
    id: int
    timestamp: datetime
    event_type: str
    severity: str
    source_ip: str
    target_ip: str
    status: str
    confidence: float
    risk_score: Optional[float] = None
    estimated_co2_kg: Optional[float] = None
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class EventLogListResponse(BaseModel):
    items: List[EventLogResponse]
    total: int
    page: int
    page_size: int
