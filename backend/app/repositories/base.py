from typing import TypeVar, Generic, Type, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: int) -> Optional[ModelType]:
        return self.db.get(self.model, id)

    def get_all(self, offset: int = 0, limit: int = 100) -> List[ModelType]:
        query = select(self.model).offset(offset).limit(limit)
        result = self.db.execute(query)
        return list(result.scalars().all())

    def count(self) -> int:
        query = select(func.count()).select_from(self.model)
        result = self.db.execute(query)
        return result.scalar() or 0

    def create(self, data: dict) -> ModelType:
        obj = self.model(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: ModelType, data: dict) -> ModelType:
        for key, value in data.items():
            setattr(obj, key, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelType) -> None:
        self.db.delete(obj)
        self.db.commit()
