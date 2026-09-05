from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import get_current_user
from app.schemas.ai import SettlementQueryRequest, SettlementQueryResponse
from app.services.ai_service import settlement_query

router = APIRouter(prefix="/api/settlement", tags=["Settlement Q&A"])


@router.post("/query", response_model=SettlementQueryResponse,
             summary="Ask the AI about settlements")
def query(data: SettlementQueryRequest, db: Session = Depends(get_db),
          _=Depends(get_current_user)):
    return settlement_query(db, data.question)
