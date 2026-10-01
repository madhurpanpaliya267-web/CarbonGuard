from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.services.security_service import SecurityService

router = APIRouter()


class SimulateRequest(BaseModel):
    attack_type: str


@router.post("/simulate")
def simulate_attack(request: SimulateRequest, db: Session = Depends(get_db)):
    service = SecurityService(db)
    result = service.simulate(request.attack_type)
    return result


@router.get("/attack-types")
def get_attack_types():
    return {
        "types": [
            {"id": "ddos", "name": "DDoS", "description": "Distributed Denial of Service", "typical_severity": "HIGH"},
            {"id": "brute_force", "name": "Brute Force", "description": "Brute force login attempt", "typical_severity": "MEDIUM"},
            {"id": "port_scan", "name": "Port Scan", "description": "Network port scanning", "typical_severity": "LOW"},
            {"id": "sql_injection", "name": "SQL Injection", "description": "SQL injection attempt", "typical_severity": "HIGH"},
            {"id": "malware", "name": "Malware", "description": "Malware detection", "typical_severity": "CRITICAL"},
            {"id": "suspicious_login", "name": "Suspicious Login", "description": "Suspicious login activity", "typical_severity": "MEDIUM"},
        ]
    }
