from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any


class TaxMatchRequest(BaseModel):
    transaction_ids: Optional[List[Any]] = None


class TaxMatchOut(BaseModel):
    id: Any
    transaction_id: Any
    tax_category: Optional[str]
    tax_code: Optional[str]
    confidence: float
    reasoning: Optional[str]
    method: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TaxMatchOverride(BaseModel):
    tax_category: str
    tax_code: str
    reasoning: Optional[str] = None
