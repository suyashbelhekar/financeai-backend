from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
from app.models.base_types import GUID, new_uuid


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (Index("ix_accounts_user_id", "user_id"),)

    id              = Column(GUID(), primary_key=True, default=new_uuid)
    user_id         = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    account_name    = Column(String(200), nullable=False)
    account_type    = Column(String(50), nullable=False)
    institution     = Column(String(200), nullable=False)
    currency        = Column(String(10), default="INR")
    current_balance = Column(Float, default=0.0)
    status          = Column(String(20), default="active")
    created_at      = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at      = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                             onupdate=lambda: datetime.now(timezone.utc))

    user         = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account",
                                cascade="all, delete-orphan")
