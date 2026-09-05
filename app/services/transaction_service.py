from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from fastapi import HTTPException
from app.models.transaction import Transaction
from app.models.account import Account
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.utils.csv_processor import process_bank_csv


def list_transactions(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    status: Optional[str] = None,
    account_id: Optional[str] = None,
    direction: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort_by: str = "transaction_date",
    sort_dir: str = "desc",
) -> dict:
    q = db.query(Transaction)
    if search:
        term = f"%{search}%"
        q = q.filter(
            or_(
                Transaction.description.ilike(term),
                Transaction.transaction_id.ilike(term),
                Transaction.merchant.ilike(term),
            )
        )
    if status:
        q = q.filter(Transaction.status == status)
    if account_id:
        q = q.filter(Transaction.account_id == account_id)
    if direction:
        q = q.filter(Transaction.direction == direction.upper())
    if date_from:
        q = q.filter(Transaction.transaction_date >= date_from)
    if date_to:
        q = q.filter(Transaction.transaction_date <= date_to)

    total = q.count()
    col = getattr(Transaction, sort_by, Transaction.transaction_date)
    q = q.order_by(col.desc() if sort_dir == "desc" else col.asc())
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": items}


def get_transaction(db: Session, tx_id: str) -> Transaction:
    t = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not t:
        raise HTTPException(404, detail={"success": False, "message": "Transaction not found",
                                         "error_code": "TRANSACTION_NOT_FOUND"})
    return t


def create_transaction(db: Session, data: TransactionCreate) -> Transaction:
    existing = db.query(Transaction).filter(
        Transaction.transaction_id == data.transaction_id
    ).first()
    if existing:
        raise HTTPException(409, detail={"success": False,
                                         "message": "Duplicate transaction_id",
                                         "error_code": "DUPLICATE_TRANSACTION"})
    payload = data.model_dump()
    payload["account_id"] = str(payload["account_id"])
    t = Transaction(**payload)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def update_transaction(db: Session, tx_id: str, data: TransactionUpdate) -> Transaction:
    t = get_transaction(db, tx_id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t


def delete_transaction(db: Session, tx_id: str) -> None:
    t = get_transaction(db, tx_id)
    db.delete(t)
    db.commit()


def import_csv(db: Session, content: bytes, account_id: str) -> dict:
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(404, detail={"success": False, "message": "Account not found",
                                         "error_code": "ACCOUNT_NOT_FOUND"})
    records, errors, dups, rejected = process_bank_csv(content, account_id)
    imported = 0
    for rec in records:
        exists = db.query(Transaction).filter(
            Transaction.transaction_id == rec["transaction_id"]
        ).first()
        if exists:
            dups += 1
            continue
        db.add(Transaction(**rec))
        imported += 1
    db.commit()
    return {
        "total_rows": len(records) + dups + rejected,
        "imported": imported,
        "duplicates": dups,
        "rejected": rejected,
        "errors": errors,
    }
