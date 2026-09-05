from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
from app.models.base_types import GUID, new_uuid


class User(Base):
    __tablename__ = "users"

    id           = Column(GUID(), primary_key=True, default=new_uuid, index=True)
    name         = Column(String(200), nullable=False)
    email        = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role         = Column(String(50), default="user")
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at   = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))

    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False,
                            cascade="all, delete-orphan")
