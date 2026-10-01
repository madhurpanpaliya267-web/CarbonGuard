from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.energy_service import EnergyService

router = APIRouter()


@router.get("")
def get_energy_overview(db: Session = Depends(get_db)):
    service = EnergyService(db)
    return service.get_overview()


@router.get("/current")
def get_current_energy(db: Session = Depends(get_db)):
    service = EnergyService(db)
    return service.get_current()


@router.get("/history")
def get_energy_history(limit: int = Query(30), db: Session = Depends(get_db)):
    service = EnergyService(db)
    return service.get_history(limit)
