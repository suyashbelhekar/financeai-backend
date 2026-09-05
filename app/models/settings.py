from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
from app.models.base_types import GUID, new_uuid


class UserSettings(Base):
    __tablename__ = "user_settings"

    id                       = Column(GUID(), primary_key=True, default=new_uuid)
    user_id                  = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"),
                                      nullable=False, unique=True)
    currency                 = Column(String(10), default="INR")
    forecast_period          = Column(Integer, default=6)
    reconciliation_threshold = Column(Integer, default=85)
    notify_critical          = Column(Boolean, default=True)
    notify_warnings          = Column(Boolean, default=True)
    notify_digest            = Column(Boolean, default=True)
    created_at               = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at               = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                                      onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="settings")
