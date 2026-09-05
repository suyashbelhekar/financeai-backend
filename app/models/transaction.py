from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Index, Date
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
from app.models.base_types import GUID, new_uuid


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_tx_account_id", "account_id"),
        Index("ix_tx_date", "transaction_date"),
        Index("ix_tx_status", "status"),
    )

    id               = Column(GUID(), primary_key=True, default=new_uuid)
    account_id       = Column(GUID(), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    transaction_id   = Column(String(100), unique=True, nullable=False)
    transaction_date = Column(Date, nullable=False, index=True)
    description      = Column(String(500))
    merchant         = Column(String(200))
    amount           = Column(Float, nullable=False)
    direction        = Column(String(10), nullable=False)
    transaction_type = Column(String(50))
    currency         = Column(String(10), default="INR")
    category         = Column(String(100))
    reference        = Column(String(200))
    source           = Column(String(50), default="manual")
    status           = Column(String(30), default="pending")
    balance_after    = Column(Float)
    created_at       = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    account        = relationship("Account", back_populates="transactions")
    reconciliation = relationship("ReconciliationRecord",
                                  foreign_keys="ReconciliationRecord.transaction_id",
                                  back_populates="transaction",
                                  cascade="all, delete-orphan")
    tax_match      = relationship("TaxMatch", back_populates="transaction",
                                  uselist=False, cascade="all, delete-orphan")
