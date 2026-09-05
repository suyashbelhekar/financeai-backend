from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import get_current_user
from app.schemas.tax_match import TaxMatchOut, TaxMatchOverride
from app.services.tax_matching_service import match_all, match_transaction
from app.models.tax_match import TaxMatch

router = APIRouter(prefix="/api/tax", tags=["Tax Matching"])


@router.post("/match")
def run_matching(db: Session = Depends(get_db), _=Depends(get_current_user)):
    results = match_all(db)
    return {"matched": len(results), "results": results}


@router.get("/results", response_model=list[TaxMatchOut])
def get_matches(
    status: str = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(TaxMatch)
    if status:
        q = q.filter(TaxMatch.status == status)
    return q.order_by(TaxMatch.created_at.desc()).all()


@router.put("/{match_id}", response_model=TaxMatchOut)
def override(match_id: str, data: TaxMatchOverride, db: Session = Depends(get_db),
             _=Depends(get_current_user)):
    tm = db.query(TaxMatch).filter(TaxMatch.id == match_id).first()
    if not tm:
        raise HTTPException(404, detail={"success": False, "message": "Tax match not found",
                                         "error_code": "NOT_FOUND"})
    tm.tax_category = data.tax_category
    tm.tax_code     = data.tax_code
    tm.reasoning    = data.reasoning or tm.reasoning
    tm.status       = "matched"
    tm.method       = "manual"
    db.commit()
    db.refresh(tm)
    return tm
