from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.utils.security import get_current_user
from app.schemas.transaction import (
    TransactionCreate, TransactionUpdate, TransactionOut,
    TransactionListResponse, CSVImportResponse,
)
from app.services.transaction_service import (
    list_transactions, get_transaction, create_transaction,
    update_transaction, delete_transaction, import_csv,
)

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.get("", response_model=TransactionListResponse)
def get_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    account_id: Optional[str] = None,
    direction: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort_by: str = "transaction_date",
    sort_dir: str = "desc",
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    return list_transactions(db, page, page_size, search, status,
                             account_id, direction, date_from, date_to, sort_by, sort_dir)


@router.get("/{tx_id}", response_model=TransactionOut)
def get_tx(tx_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return get_transaction(db, tx_id)


@router.post("", response_model=TransactionOut, status_code=201)
def create_tx(data: TransactionCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return create_transaction(db, data)


@router.put("/{tx_id}", response_model=TransactionOut)
def update_tx(tx_id: str, data: TransactionUpdate, db: Session = Depends(get_db),
              _=Depends(get_current_user)):
    return update_transaction(db, tx_id, data)


@router.delete("/{tx_id}", status_code=204)
def delete_tx(tx_id: str, db: Session = Depends(get_db), _=Depends(get_current_user)):
    delete_transaction(db, tx_id)


@router.post("/import", response_model=CSVImportResponse)
async def import_transactions(
    account_id: str = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    content = await file.read()
    return import_csv(db, content, account_id)
