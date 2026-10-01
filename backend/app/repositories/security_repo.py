from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.security import SecurityEvent, Threat
from app.repositories.base import BaseRepository


class SecurityEventRepository(BaseRepository[SecurityEvent]):
    def __init__(self, db: Session):
        super().__init__(SecurityEvent, db)

    def get_by_uuid(self, event_uuid: str) -> Optional[SecurityEvent]:
        query = select(SecurityEvent).where(SecurityEvent.event_uuid == event_uuid)
        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_by_severity(self, severity: str) -> List[SecurityEvent]:
        query = select(SecurityEvent).where(SecurityEvent.severity == severity)
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_by_type(self, event_type: str) -> List[SecurityEvent]:
        query = select(SecurityEvent).where(SecurityEvent.event_type == event_type)
        result = self.db.execute(query)
        return list(result.scalars().all())

    def filter_events(
        self,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[SecurityEvent]:
        query = select(SecurityEvent)
        if severity:
            query = query.where(SecurityEvent.severity == severity)
        if event_type:
            query = query.where(SecurityEvent.event_type == event_type)
        if status:
            query = query.where(SecurityEvent.status == status)
        query = query.offset(offset).limit(limit)
        result = self.db.execute(query)
        return list(result.scalars().all())

    def count_active(self) -> int:
        query = select(func.count()).select_from(SecurityEvent).where(
            SecurityEvent.status.in_(["detected", "investigating"])
        )
        result = self.db.execute(query)
        return result.scalar() or 0


class ThreatRepository(BaseRepository[Threat]):
    def __init__(self, db: Session):
        super().__init__(Threat, db)

    def get_by_uuid(self, threat_uuid: str) -> Optional[Threat]:
        query = select(Threat).where(Threat.threat_uuid == threat_uuid)
        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_active_threats(self) -> List[Threat]:
        query = select(Threat).where(Threat.status == "active")
        result = self.db.execute(query)
        return list(result.scalars().all())

    def count_active(self) -> int:
        query = select(func.count()).select_from(Threat).where(Threat.status == "active")
        result = self.db.execute(query)
        return result.scalar() or 0
