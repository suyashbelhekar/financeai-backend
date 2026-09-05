from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import get_current_user
from app.schemas.account import AccountCreate, AccountUpdate, AccountOut
from app.services.account_service import (
    list_accounts, get_account, create_account, update_account, delete_account
)

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


@router.get("", response_model=list[AccountOut])
def get_accounts(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return list_accounts(db, str(user.id))


@router.get("/{account_id}", response_model=AccountOut)
def get_account_by_id(account_id: str, db: Session = Depends(get_db),
                      user=Depends(get_current_user)):
    return get_account(db, account_id, str(user.id))


@router.post("", response_model=AccountOut, status_code=201)
def create(data: AccountCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return create_account(db, data, str(user.id))


@router.put("/{account_id}", response_model=AccountOut)
def update(account_id: str, data: AccountUpdate, db: Session = Depends(get_db),
           user=Depends(get_current_user)):
    return update_account(db, account_id, data, str(user.id))


@router.delete("/{account_id}", status_code=204)
def delete(account_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    delete_account(db, account_id, str(user.id))
