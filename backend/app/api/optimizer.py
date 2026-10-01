from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.workload_service import OptimizerService

router = APIRouter()


@router.get("/workloads")
def get_workloads(db: Session = Depends(get_db)):
    service = OptimizerService(db)
    return service.get_workloads()


@router.post("/run")
def run_optimization(db: Session = Depends(get_db)):
    service = OptimizerService(db)
    return service.run_optimization()


@router.get("/history")
def get_optimization_history(db: Session = Depends(get_db)):
    service = OptimizerService(db)
    return service.get_history()


@router.get("/comparison")
def get_comparison(db: Session = Depends(get_db)):
    service = OptimizerService(db)
    return service.get_comparison()
