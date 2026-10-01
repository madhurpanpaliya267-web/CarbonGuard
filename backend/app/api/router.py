from fastapi import APIRouter
from app.api import (
    dashboard,
    security,
    attack_simulator,
    threats,
    carbon,
    energy,
    optimizer,
    renewable_energy,
    recommendations,
    analytics,
    events,
    system_health,
    settings,
    research,
)

router = APIRouter(prefix="/api/v1")

router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
router.include_router(security.router, prefix="/security", tags=["Security"])
router.include_router(attack_simulator.router, prefix="/simulator", tags=["Attack Simulator"])
router.include_router(threats.router, prefix="/threats", tags=["Threats"])
router.include_router(carbon.router, prefix="/carbon", tags=["Carbon"])
router.include_router(energy.router, prefix="/energy", tags=["Energy"])
router.include_router(optimizer.router, prefix="/optimizer", tags=["Optimizer"])
router.include_router(renewable_energy.router, prefix="/renewable-energy", tags=["Renewable Energy"])
router.include_router(recommendations.router, prefix="/recommendations", tags=["AI Recommendations"])
router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
router.include_router(events.router, prefix="/events", tags=["Events"])
router.include_router(system_health.router, prefix="/system-health", tags=["System Health"])
router.include_router(settings.router, prefix="/settings", tags=["Settings"])
router.include_router(research.router, prefix="/research", tags=["Research"])
