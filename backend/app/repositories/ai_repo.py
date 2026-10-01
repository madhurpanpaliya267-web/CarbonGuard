from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.ai import AIRecommendation
from app.repositories.base import BaseRepository


class AIRecommendationRepository(BaseRepository[AIRecommendation]):
    def __init__(self, db: Session):
        super().__init__(AIRecommendation, db)

    def get_unread(self) -> List[AIRecommendation]:
        query = select(AIRecommendation).where(AIRecommendation.is_read == False)
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_by_type(self, recommendation_type: str) -> List[AIRecommendation]:
        query = select(AIRecommendation).where(
            AIRecommendation.recommendation_type == recommendation_type
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def get_by_priority(self, priority: str) -> List[AIRecommendation]:
        query = select(AIRecommendation).where(AIRecommendation.priority == priority)
        result = self.db.execute(query)
        return list(result.scalars().all())

    def mark_read(self, rec_id: int) -> Optional[AIRecommendation]:
        rec = self.get_by_id(rec_id)
        if rec:
            rec.is_read = True
            self.db.commit()
            self.db.refresh(rec)
        return rec

    def dismiss(self, rec_id: int) -> Optional[AIRecommendation]:
        rec = self.get_by_id(rec_id)
        if rec:
            rec.is_dismissed = True
            self.db.commit()
            self.db.refresh(rec)
        return rec
