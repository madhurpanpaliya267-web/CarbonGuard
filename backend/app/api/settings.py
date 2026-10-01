from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.repositories.system_repo import SystemSettingRepository

router = APIRouter()


class SettingUpdate(BaseModel):
    key: str
    value: str


@router.get("")
def get_settings(db: Session = Depends(get_db)):
    repo = SystemSettingRepository(db)
    return repo.get_all()


@router.put("")
def update_setting(request: SettingUpdate, db: Session = Depends(get_db)):
    repo = SystemSettingRepository(db)
    return repo.upsert(request.key, request.value)


@router.post("/reset")
def reset_settings(db: Session = Depends(get_db)):
    return {"success": True}
