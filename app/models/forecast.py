from sqlalchemy import Column, String, DateTime, Float, Date
from datetime import datetime, timezone
from app.database import Base
from app.models.base_types import GUID, new_uuid


class Forecast(Base):
    __tablename__ = "forecasts"

    id                = Column(GUID(), primary_key=True, default=new_uuid)
    forecast_date     = Column(Date, nullable=False)
    predicted_inflow  = Column(Float, default=0.0)
    predicted_outflow = Column(Float, default=0.0)
    predicted_balance = Column(Float, default=0.0)
    confidence        = Column(Float, default=0.0)
    model_version     = Column(String(50), default="linear_v1")
    scenario          = Column(String(20), default="base")
    created_at        = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
