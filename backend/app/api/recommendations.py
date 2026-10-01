from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.ai_service import AIService

router = APIRouter()


@router.get("")
def get_recommendations(
    type: Optional[str] = Query(None, alias="type"),
    priority: Optional[str] = Query(None),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    service = AIService(db)
    return service.get_recommendations(
        recommendation_type=type,
        priority=priority,
        unread_only=unread_only,
    )


@router.post("/generate")
def generate_recommendations(db: Session = Depends(get_db)):
    service = AIService(db)
    return service.generate()


@router.patch("/{rec_id}/read")
def mark_read(rec_id: int, db: Session = Depends(get_db)):
    service = AIService(db)
    result = service.mark_read(rec_id)
    if not result:
        return {"detail": "Recommendation not found"}
    return {"success": True}


@router.patch("/{rec_id}/dismiss")
def dismiss(rec_id: int, db: Session = Depends(get_db)):
    service = AIService(db)
    result = service.dismiss(rec_id)
    if not result:
        return {"detail": "Recommendation not found"}
    return {"success": True}
