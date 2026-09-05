from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Any


class ForecastOut(BaseModel):
    id: Any
    forecast_date: date
    predicted_inflow: float
    predicted_outflow: float
    predicted_balance: float
    confidence: float
    model_version: str
    scenario: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ForecastGenerateRequest(BaseModel):
    periods: int = 6
    scenario: str = "base"
