from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.system_service import SystemService

router = APIRouter()


@router.get("")
def get_system_health(db: Session = Depends(get_db)):
    service = SystemService(db)
    return service.get_health()


@router.get("/history")
def get_system_history(limit: int = Query(50), db: Session = Depends(get_db)):
    service = SystemService(db)
    return service.get_history(limit)
