from sqlalchemy import Column, Integer, String, Text
from app.models.base import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="general")
    description = Column(Text, nullable=True)
