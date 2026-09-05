from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.settings import UserSettings
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserOut
from app.utils.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=201,
             summary="Register a new user")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, detail={"success": False, "message": "Email already registered",
                                         "error_code": "EMAIL_EXISTS"})
    user = User(name=data.name, email=data.email, password_hash=hash_password(data.password))
    db.add(user)
    db.flush()
    # Create default settings
    db.add(UserSettings(user_id=user.id))
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse, summary="Login and get JWT token")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, detail={"success": False, "message": "Invalid credentials",
                                         "error_code": "INVALID_CREDENTIALS"})
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut, summary="Get current user")
def me(current_user: User = Depends(get_current_user)):
    return current_user
