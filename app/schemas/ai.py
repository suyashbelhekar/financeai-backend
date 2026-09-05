from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any


class AIInsightOut(BaseModel):
    id: Any
    insight_type: Optional[str]
    title: str
    description: str
    severity: str
    generated_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    data_used: Optional[Any] = None


class SettlementQueryRequest(BaseModel):
    question: str


class SettlementQueryResponse(BaseModel):
    answer: str
    supporting_transactions: List[Any] = []
    confidence: float = 0.0


class SettingsOut(BaseModel):
    currency: str
    forecast_period: int
    reconciliation_threshold: int
    notify_critical: bool
    notify_warnings: bool
    notify_digest: bool

    model_config = {"from_attributes": True}


class SettingsUpdate(BaseModel):
    currency: Optional[str] = None
    forecast_period: Optional[int] = None
    reconciliation_threshold: Optional[int] = None
    notify_critical: Optional[bool] = None
    notify_warnings: Optional[bool] = None
    notify_digest: Optional[bool] = None
