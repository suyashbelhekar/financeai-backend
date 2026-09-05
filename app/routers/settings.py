from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import get_current_user
from app.schemas.ai import SettingsOut, SettingsUpdate
from app.models.settings import UserSettings

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("", response_model=SettingsOut, summary="Get user settings")
def get_settings(db: Session = Depends(get_db), user=Depends(get_current_user)):
    s = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if not s:
        s = UserSettings(user_id=user.id)
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


@router.put("", response_model=SettingsOut, summary="Update user settings")
def update_settings(data: SettingsUpdate, db: Session = Depends(get_db),
                    user=Depends(get_current_user)):
    s = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if not s:
        s = UserSettings(user_id=user.id)
        db.add(s)
        db.flush()
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s
