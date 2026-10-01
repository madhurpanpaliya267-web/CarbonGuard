from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.security_service import SecurityService
from app.repositories.security_repo import SecurityEventRepository

router = APIRouter()


@router.get("/events")
def get_events(
    severity: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    db: Session = Depends(get_db),
):
    service = SecurityService(db)
    return service.get_events(
        severity=severity,
        event_type=event_type,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get("/events/{event_id}")
def get_event(event_id: int, db: Session = Depends(get_db)):
    service = SecurityService(db)
    event = service.get_event(event_id)
    if not event:
        return {"detail": "Event not found"}
    return event


@router.get("/stats")
def get_security_stats(db: Session = Depends(get_db)):
    repo = SecurityEventRepository(db)
    all_events = repo.get_all()

    severity_counts = {}
    type_counts = {}
    status_counts = {}
    for e in all_events:
        severity_counts[e.severity] = severity_counts.get(e.severity, 0) + 1
        type_counts[e.event_type] = type_counts.get(e.event_type, 0) + 1
        status_counts[e.status] = status_counts.get(e.status, 0) + 1

    avg_confidence = sum(e.confidence for e in all_events) / max(len(all_events), 1)
    total_energy = sum(e.estimated_energy_kwh or 0 for e in all_events)
    total_co2 = sum(e.estimated_co2_kg or 0 for e in all_events)

    return {
        "total_events": len(all_events),
        "by_severity": severity_counts,
        "by_type": type_counts,
        "by_status": status_counts,
        "avg_confidence": round(avg_confidence, 2),
        "total_energy_kwh": round(total_energy, 4),
        "total_co2_kg": round(total_co2, 4),
        "simulated": True,
    }
