from sqlalchemy import Column, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
from app.models.base_types import GUID, new_uuid


class ReconciliationRecord(Base):
    __tablename__ = "reconciliation_records"

    id                     = Column(GUID(), primary_key=True, default=new_uuid)
    transaction_id         = Column(GUID(), ForeignKey("transactions.id", ondelete="CASCADE"),
                                    nullable=False)
    matched_transaction_id = Column(GUID(), ForeignKey("transactions.id", ondelete="SET NULL"),
                                    nullable=True)
    matching_score         = Column(Float, default=0.0)
    matching_method        = Column(String(50))
    status                 = Column(String(30), default="unmatched")
    difference             = Column(Float, default=0.0)
    notes                  = Column(String(500))
    created_at             = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    transaction         = relationship("Transaction", foreign_keys=[transaction_id],
                                       back_populates="reconciliation")
    matched_transaction = relationship("Transaction", foreign_keys=[matched_transaction_id])
