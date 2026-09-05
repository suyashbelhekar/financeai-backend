from sqlalchemy import Column, String, DateTime, Text
from datetime import datetime, timezone
from app.database import Base
from app.models.base_types import GUID, new_uuid


class Alert(Base):
    __tablename__ = "alerts"

    id         = Column(GUID(), primary_key=True, default=new_uuid)
    type       = Column(String(100), nullable=False)
    severity   = Column(String(20), default="info")
    title      = Column(String(300), nullable=False)
    message    = Column(Text, nullable=False)
    status     = Column(String(20), default="unread")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
