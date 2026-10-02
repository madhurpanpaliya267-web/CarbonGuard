from typing import Any, Dict, TypeVar, Generic, Type, List, Optional
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

    def list_all(self) -> List[ModelType]:
        query = select(self.model)
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

    def column_values(
        self, column: Any, exclude_null: bool = False
    ) -> List[Any]:
        query = select(column)
        if exclude_null:
            query = query.where(column.isnot(None))
        result = self.db.execute(query)
        return list(result.scalars().all())

    def distinct_values(self, column: Any) -> List[str]:
        result = self.db.execute(select(column).distinct())
        values = [str(value) for value in result.scalars().all() if value is not None]
        return sorted(values)

    def count_by(self, column: Any) -> Dict[str, int]:
        query = select(column, func.count()).group_by(column)
        result = self.db.execute(query)
        return {str(key): int(count) for key, count in result.all() if key is not None}

    def count_where_not_null(self, column: Any) -> int:
        query = (
            select(func.count())
            .select_from(self.model)
            .where(column.isnot(None))
        )
        result = self.db.execute(query)
        return int(result.scalar() or 0)
