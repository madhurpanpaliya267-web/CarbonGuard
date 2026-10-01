from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.system import SystemMetric
from app.models.settings import SystemSetting
from app.repositories.base import BaseRepository


class SystemMetricRepository(BaseRepository[SystemMetric]):
    def __init__(self, db: Session):
        super().__init__(SystemMetric, db)

    def get_latest(self) -> Optional[SystemMetric]:
        query = select(SystemMetric).order_by(SystemMetric.timestamp.desc()).limit(1)
        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_history(self, limit: int = 50) -> List[SystemMetric]:
        query = select(SystemMetric).order_by(SystemMetric.timestamp.desc()).limit(limit)
        result = self.db.execute(query)
        return list(result.scalars().all())


class SystemSettingRepository(BaseRepository[SystemSetting]):
    def __init__(self, db: Session):
        super().__init__(SystemSetting, db)

    def get_by_key(self, key: str) -> Optional[SystemSetting]:
        query = select(SystemSetting).where(SystemSetting.key == key)
        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_by_category(self, category: str) -> List[SystemSetting]:
        query = select(SystemSetting).where(SystemSetting.category == category)
        result = self.db.execute(query)
        return list(result.scalars().all())

    def upsert(self, key: str, value: str, category: str = "general", description: str = None) -> SystemSetting:
        existing = self.get_by_key(key)
        if existing:
            existing.value = value
            if description:
                existing.description = description
            self.db.commit()
            self.db.refresh(existing)
            return existing
        return self.create({"key": key, "value": value, "category": category, "description": description})
