from pydantic import BaseModel
from datetime import datetime
from typing import Any


class AlertOut(BaseModel):
    id: Any
    type: str
    severity: str
    title: str
    message: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
