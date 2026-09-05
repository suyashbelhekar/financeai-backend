from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import get_current_user
from app.schemas.alert import AlertOut
from app.services.alert_service import list_alerts, mark_read, auto_generate_alerts

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get("", response_model=list[AlertOut])
def get_alerts(db: Session = Depends(get_db), _=Depends(get_current_user)):
    auto_generate_alerts(db)
    return list_alerts(db)


@router.put("/{alert_id}/read", response_model=AlertOut)
def read_alert(alert_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    a = mark_read(db, alert_id)
    if not a:
        raise HTTPException(404, detail={"success": False, "message": "Alert not found",
                                         "error_code": "ALERT_NOT_FOUND"})
    return a
