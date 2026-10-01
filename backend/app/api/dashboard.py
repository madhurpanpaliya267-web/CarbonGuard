from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("")
def get_dashboard(db: Session = Depends(get_db)):
    service = DashboardService(db)
    return service.get_metrics()


@router.get("/charts/threat-activity")
def get_threat_activity(period: str = "24h", db: Session = Depends(get_db)):
    service = DashboardService(db)
    return service.get_threat_activity_chart(period)


@router.get("/charts/carbon-emissions")
def get_carbon_emissions(period: str = "24h", db: Session = Depends(get_db)):
    service = DashboardService(db)
    return service.get_carbon_emissions_chart(period)


@router.get("/charts/energy-consumption")
def get_energy_consumption(period: str = "24h", db: Session = Depends(get_db)):
    service = DashboardService(db)
    return service.get_energy_consumption_chart(period)


@router.get("/charts/carbon-savings")
def get_carbon_savings(db: Session = Depends(get_db)):
    service = DashboardService(db)
    return service.get_carbon_savings_chart()


@router.get("/charts/threat-categories")
def get_threat_categories(db: Session = Depends(get_db)):
    service = DashboardService(db)
    return service.get_threat_categories_chart()


@router.get("/charts/threat-severity")
def get_threat_severity(db: Session = Depends(get_db)):
    service = DashboardService(db)
    return service.get_threat_severity_chart()
