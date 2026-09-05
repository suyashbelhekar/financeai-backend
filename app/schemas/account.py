from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any


class AccountCreate(BaseModel):
    account_name: str
    account_type: str
    institution: str
    currency: str = "INR"
    current_balance: float = 0.0
    status: str = "active"


class AccountUpdate(BaseModel):
    account_name: Optional[str] = None
    account_type: Optional[str] = None
    institution: Optional[str] = None
    currency: Optional[str] = None
    current_balance: Optional[float] = None
    status: Optional[str] = None


class AccountOut(BaseModel):
    id: Any
    account_name: str
    account_type: str
    institution: str
    currency: str
    current_balance: float
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
