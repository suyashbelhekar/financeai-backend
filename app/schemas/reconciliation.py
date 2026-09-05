from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any


class ReconciliationRunRequest(BaseModel):
    account_id: Optional[Any] = None


class ReconciliationOut(BaseModel):
    id: Any
    transaction_id: Any
    matched_transaction_id: Optional[Any]
    matching_score: float
    matching_method: Optional[str]
    status: str
    difference: float
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ReconciliationRunResponse(BaseModel):
    total_processed: int
    matched: int
    probable: int
    unmatched: int
    disputed: int
    duration_seconds: float
