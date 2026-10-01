from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import datetime
from app.models.carbon import CarbonMetric, EnergyMetric
from app.repositories.base import BaseRepository


class CarbonMetricRepository(BaseRepository[CarbonMetric]):
    def __init__(self, db: Session):
        super().__init__(CarbonMetric, db)

    def get_latest(self) -> Optional[CarbonMetric]:
        query = select(CarbonMetric).order_by(CarbonMetric.timestamp.desc()).limit(1)
        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_history(self, limit: int = 50) -> List[CarbonMetric]:
        query = select(CarbonMetric).order_by(CarbonMetric.timestamp.desc()).limit(limit)
        result = self.db.execute(query)
        return list(result.scalars().all())


class EnergyMetricRepository(BaseRepository[EnergyMetric]):
    def __init__(self, db: Session):
        super().__init__(EnergyMetric, db)

    def get_latest(self) -> Optional[EnergyMetric]:
        query = select(EnergyMetric).order_by(EnergyMetric.timestamp.desc()).limit(1)
        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_history(self, limit: int = 50) -> List[EnergyMetric]:
        query = select(EnergyMetric).order_by(EnergyMetric.timestamp.desc()).limit(limit)
        result = self.db.execute(query)
        return list(result.scalars().all())
