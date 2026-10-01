from fastapi import APIRouter, Query
from app.services.renewable_service import get_renewable_status

router = APIRouter()


@router.get("")
def get_renewable_energy():
    return get_renewable_status()


@router.get("/forecast")
def get_renewable_forecast(hours: int = Query(24)):
    status = get_renewable_status()
    return {"forecast": status["forecast"][:hours]}
