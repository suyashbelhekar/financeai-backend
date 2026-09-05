from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List, Any


class TransactionCreate(BaseModel):
    account_id: Any
    transaction_id: str
    transaction_date: date
    description: Optional[str] = None
    merchant: Optional[str] = None
    amount: float
    direction: str
    transaction_type: Optional[str] = None
    currency: str = "INR"
    category: Optional[str] = None
    reference: Optional[str] = None
    source: str = "manual"
    status: str = "pending"
    balance_after: Optional[float] = None


class TransactionUpdate(BaseModel):
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None


class TransactionOut(BaseModel):
    id: Any
    account_id: Any
    transaction_id: str
    transaction_date: date
    description: Optional[str]
    merchant: Optional[str]
    amount: float
    direction: str
    transaction_type: Optional[str]
    currency: str
    category: Optional[str]
    source: str
    status: str
    balance_after: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[TransactionOut]


class CSVImportResponse(BaseModel):
    total_rows: int
    imported: int
    duplicates: int
    rejected: int
    errors: List[str]
