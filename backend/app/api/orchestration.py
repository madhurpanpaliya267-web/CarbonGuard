from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.engines.security.attack_profiles import AttackProfileError
from app.schemas.orchestration import OrchestrationRunResponse
from app.services.orchestration_service import CarbonGuardOrchestrationService

router = APIRouter()


class OrchestrationRunRequest(BaseModel):
    attack_type: str = Field(..., min_length=1)
    intensity: Optional[str] = None
    duration_seconds: Optional[int] = Field(None, ge=1, le=3600)
    measurement_provider: str = "estimated"
    record_research: bool = False
    experiment_uuid: Optional[str] = None
    carbon_intensity: Optional[float] = Field(None, gt=0)
    renewable_percentage: Optional[float] = Field(None, ge=0, le=100)


@router.post("/run", response_model=OrchestrationRunResponse)
def run_pipeline(request: OrchestrationRunRequest, db: Session = Depends(get_db)):
    """Execute one end-to-end CarbonGuard pipeline run (synthetic attack).

    Attack -> threat -> risk -> rule-based defense -> energy -> carbon ->
    research observation -> analytics feeds. Optional stage failures degrade
    to status/reason fields instead of failing the run.
    """
    service = CarbonGuardOrchestrationService(db)
    try:
        return service.run(
            attack_type=request.attack_type,
            intensity=request.intensity,
            duration_seconds=request.duration_seconds,
            measurement_provider=request.measurement_provider,
            record_research=request.record_research,
            experiment_uuid=request.experiment_uuid,
            carbon_intensity=request.carbon_intensity,
            renewable_percentage=request.renewable_percentage,
        )
    except AttackProfileError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
