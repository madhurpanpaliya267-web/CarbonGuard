from fastapi import APIRouter, Query
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/security")
def get_security_analytics(period: str = Query("7d")):
    service = AnalyticsService()
    return service.get_security_analytics(period)


@router.get("/carbon")
def get_carbon_analytics(period: str = Query("7d")):
    service = AnalyticsService()
    return service.get_carbon_analytics(period)


@router.get("/energy")
def get_energy_analytics(period: str = Query("7d")):
    service = AnalyticsService()
    return service.get_energy_analytics(period)


@router.get("/optimization")
def get_optimization_analytics():
    service = AnalyticsService()
    return service.get_optimization_analytics()
