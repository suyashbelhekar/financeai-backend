from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.utils.security import get_current_user
from app.schemas.reconciliation import ReconciliationOut, ReconciliationRunResponse
from app.services.reconciliation_service import run_reconciliation
from app.models.reconciliation import ReconciliationRecord

router = APIRouter(prefix="/api/reconciliation", tags=["Reconciliation"])


@router.post("/run", response_model=ReconciliationRunResponse)
def run_recon(
    account_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return run_reconciliation(db, account_id)


@router.get("/results", response_model=list[ReconciliationOut])
def get_results(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(ReconciliationRecord)
    if status:
        q = q.filter(ReconciliationRecord.status == status)
    return q.order_by(ReconciliationRecord.created_at.desc()).limit(limit).all()


@router.get("/{record_id}", response_model=ReconciliationOut)
def get_record(record_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    r = db.query(ReconciliationRecord).filter(ReconciliationRecord.id == record_id).first()
    if not r:
        raise HTTPException(404, detail={"success": False, "message": "Record not found",
                                         "error_code": "NOT_FOUND"})
    return r
