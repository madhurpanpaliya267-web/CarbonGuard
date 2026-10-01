from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AIRecommendationResponse(BaseModel):
    id: int
    timestamp: datetime
    recommendation_type: str
    recommendation: str
    priority: str
    reason: str
    expected_security_impact: Optional[str] = None
    expected_carbon_impact: Optional[str] = None
    confidence: float
    factors_json: Optional[str] = None
    is_read: bool
    is_dismissed: bool

    model_config = {"from_attributes": True}
