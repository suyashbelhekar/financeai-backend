from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import get_current_user
from app.schemas.forecast import ForecastGenerateRequest
from app.services.forecasting_service import generate_forecast
from app.models.forecast import Forecast

router = APIRouter(prefix="/api/forecast", tags=["Forecasting"])


@router.get("", summary="Get latest stored forecasts")
def get_forecasts(
    scenario: str = Query("base"),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = (
        db.query(Forecast)
        .filter(Forecast.scenario == scenario)
        .order_by(Forecast.forecast_date.asc())
        .all()
    )
    if not rows:
        # Auto-generate if none exist
        return generate_forecast(db, 6, scenario)
    return [
        {
            "month": f"{r.forecast_date.strftime('%b')} {str(r.forecast_date.year)[2:]}",
            "forecast_date": str(r.forecast_date),
            "forecast": r.predicted_inflow,
            "low": round(r.predicted_inflow * 0.88, 2),
            "high": round(r.predicted_inflow * 1.12, 2),
            "predicted_inflow": r.predicted_inflow,
            "predicted_outflow": r.predicted_outflow,
            "predicted_balance": r.predicted_balance,
            "confidence": r.confidence,
            "scenario": r.scenario,
        }
        for r in rows
    ]


@router.post("/generate", summary="Generate new forecast")
def generate(
    data: ForecastGenerateRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return generate_forecast(db, data.periods, data.scenario)
