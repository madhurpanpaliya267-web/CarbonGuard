from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel
from app.database import get_db
from app.repositories.security_repo import ThreatRepository, SecurityEventRepository

router = APIRouter()


class ThreatStatusUpdate(BaseModel):
    status: str


@router.get("")
def get_threats(
    severity: Optional[str] = Query(None),
    threat_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    db: Session = Depends(get_db),
):
    repo = ThreatRepository(db)
    threats = repo.get_all()
    if severity:
        threats = [t for t in threats if t.severity == severity]
    if threat_type:
        threats = [t for t in threats if t.threat_type == threat_type]
    if status:
        threats = [t for t in threats if t.status == status]

    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": threats[start:end],
        "total": len(threats),
        "page": page,
        "page_size": page_size,
    }


@router.get("/stats")
def get_threat_stats(db: Session = Depends(get_db)):
    repo = ThreatRepository(db)
    event_repo = SecurityEventRepository(db)
    all_threats = repo.get_all()

    severity_counts = {}
    type_counts = {}
    status_counts = {}
    for t in all_threats:
        severity_counts[t.severity] = severity_counts.get(t.severity, 0) + 1
        type_counts[t.threat_type] = type_counts.get(t.threat_type, 0) + 1
        status_counts[t.status] = status_counts.get(t.status, 0) + 1

    active = [t for t in all_threats if t.status == "active"]
    avg_risk = sum(t.risk_score for t in all_threats) / max(len(all_threats), 1)
    avg_confidence = sum(t.confidence for t in all_threats) / max(len(all_threats), 1)

    return {
        "total_threats": len(all_threats),
        "active_threats": len(active),
        "resolved_threats": status_counts.get("resolved", 0),
        "avg_risk_score": round(avg_risk, 1),
        "avg_confidence": round(avg_confidence, 2),
        "by_severity": severity_counts,
        "by_type": type_counts,
        "by_status": status_counts,
        "total_events": event_repo.count(),
    }


@router.get("/{threat_id}")
def get_threat(threat_id: int, db: Session = Depends(get_db)):
    repo = ThreatRepository(db)
    threat = repo.get_by_id(threat_id)
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")
    return threat


@router.patch("/{threat_id}/status")
def update_threat_status(threat_id: int, body: ThreatStatusUpdate, db: Session = Depends(get_db)):
    repo = ThreatRepository(db)
    threat = repo.get_by_id(threat_id)
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")

    valid_statuses = ["active", "investigating", "resolved"]
    if body.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    threat.status = body.status
    if body.status == "resolved":
        threat.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(threat)
    return threat


@router.get("/{threat_id}/explanation")
def get_threat_explanation(threat_id: int, db: Session = Depends(get_db)):
    repo = ThreatRepository(db)
    threat = repo.get_by_id(threat_id)
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")

    return {
        "prediction": f"{threat.threat_type.upper()} attack",
        "confidence": threat.confidence,
        "factors": [
            {"factor": "Severity", "weight": 0.3, "value": threat.severity},
            {"factor": "Confidence", "weight": 0.25, "value": threat.confidence},
            {"factor": "Anomaly Level", "weight": 0.2, "value": threat.anomaly_level or 0.5},
            {"factor": "Risk Score", "weight": 0.25, "value": threat.risk_score},
        ],
        "reasoning": threat.explanation or f"Threat detected with {threat.confidence * 100:.0f}% confidence.",
        "recommended_action": threat.recommended_action or "Investigate and assess impact.",
    }
