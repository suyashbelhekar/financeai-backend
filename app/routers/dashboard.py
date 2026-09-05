from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import get_current_user
from app.services.dashboard_service import get_dashboard_summary, get_cash_flow

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", summary="Dashboard KPIs and recent data")
def summary(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return get_dashboard_summary(db)


@router.get("/cash-flow", summary="Monthly cash flow for charts")
def cash_flow(
    period: str = Query("12m", description="e.g. 6m, 12m"),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    months = int(period.replace("m", "")) if period.endswith("m") else 12
    return get_cash_flow(db, months)
