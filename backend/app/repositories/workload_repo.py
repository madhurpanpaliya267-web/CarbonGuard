from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.workload import Workload, OptimizationResult
from app.repositories.base import BaseRepository


class WorkloadRepository(BaseRepository[Workload]):
    def __init__(self, db: Session):
        super().__init__(Workload, db)

    def get_pending(self) -> List[Workload]:
        query = select(Workload).where(Workload.status.in_(["pending", "scheduled"]))
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_by_status(self, status: str) -> List[Workload]:
        query = select(Workload).where(Workload.status == status)
        result = self.db.execute(query)
        return list(result.scalars().all())


class OptimizationResultRepository(BaseRepository[OptimizationResult]):
    def __init__(self, db: Session):
        super().__init__(OptimizationResult, db)

    def get_latest(self) -> Optional[OptimizationResult]:
        query = select(OptimizationResult).order_by(OptimizationResult.run_timestamp.desc()).limit(1)
        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_history(self, limit: int = 10) -> List[OptimizationResult]:
        query = select(OptimizationResult).order_by(OptimizationResult.run_timestamp.desc()).limit(limit)
        result = self.db.execute(query)
        return list(result.scalars().all())
