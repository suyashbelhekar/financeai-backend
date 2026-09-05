from sqlalchemy import Column, String, DateTime, Text
from datetime import datetime, timezone
from app.database import Base
from app.models.base_types import GUID, new_uuid


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id           = Column(GUID(), primary_key=True, default=new_uuid)
    insight_type = Column(String(100))
    title        = Column(String(300), nullable=False)
    description  = Column(Text, nullable=False)
    severity     = Column(String(20), default="info")
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
