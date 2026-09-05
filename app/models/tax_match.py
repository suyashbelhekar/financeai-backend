from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
from app.models.base_types import GUID, new_uuid


class TaxMatch(Base):
    __tablename__ = "tax_matches"

    id             = Column(GUID(), primary_key=True, default=new_uuid)
    transaction_id = Column(GUID(), ForeignKey("transactions.id", ondelete="CASCADE"),
                            nullable=False, unique=True)
    tax_category   = Column(String(200))
    tax_code       = Column(String(50))
    confidence     = Column(Float, default=0.0)
    reasoning      = Column(Text)
    method         = Column(String(20), default="rule")
    status         = Column(String(20), default="matched")
    created_at     = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    transaction = relationship("Transaction", back_populates="tax_match")
