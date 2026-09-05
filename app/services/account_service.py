from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.account import AccountCreate, AccountUpdate


def list_accounts(db: Session, user_id: str) -> list:
    return db.query(Account).filter(Account.user_id == user_id).all()


def get_account(db: Session, account_id: str, user_id: str) -> Account:
    a = db.query(Account).filter(
        Account.id == account_id, Account.user_id == user_id
    ).first()
    if not a:
        raise HTTPException(404, detail={"success": False, "message": "Account not found",
                                         "error_code": "ACCOUNT_NOT_FOUND"})
    return a


def create_account(db: Session, data: AccountCreate, user_id: str) -> Account:
    a = Account(**data.model_dump(), user_id=user_id)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def update_account(db: Session, account_id: str, data: AccountUpdate, user_id: str) -> Account:
    a = get_account(db, account_id, user_id)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(a, k, v)
    db.commit()
    db.refresh(a)
    return a


def delete_account(db: Session, account_id: str, user_id: str) -> None:
    a = get_account(db, account_id, user_id)
    db.delete(a)
    db.commit()


def recalculate_balance(db: Session, account_id: str) -> float:
    credits = db.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id == account_id,
        Transaction.direction == "CREDIT",
    ).scalar() or 0.0
    debits = db.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id == account_id,
        Transaction.direction == "DEBIT",
    ).scalar() or 0.0
    balance = credits - debits
    db.query(Account).filter(Account.id == account_id).update({"current_balance": balance})
    db.commit()
    return balance
