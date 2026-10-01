from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.repositories.security_repo import SecurityEventRepository

router = APIRouter()


@router.get("")
def get_events(
    severity: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    db: Session = Depends(get_db),
):
    repo = SecurityEventRepository(db)
    events = repo.filter_events(
        severity=severity,
        event_type=event_type,
        status=status,
        offset=(page - 1) * page_size,
        limit=page_size,
    )
    total = repo.count()
    return {
        "items": events,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
