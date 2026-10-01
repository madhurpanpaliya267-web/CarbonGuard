from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.carbon_service import CarbonService

router = APIRouter()


@router.get("")
def get_carbon_overview(db: Session = Depends(get_db)):
    service = CarbonService(db)
    return service.get_overview()


@router.get("/current")
def get_current_carbon(db: Session = Depends(get_db)):
    service = CarbonService(db)
    return service.get_current()


@router.get("/history")
def get_carbon_history(limit: int = Query(30), db: Session = Depends(get_db)):
    service = CarbonService(db)
    return service.get_history(limit)


@router.get("/efficiency")
def get_efficiency(db: Session = Depends(get_db)):
    service = CarbonService(db)
    return service.get_efficiency()
