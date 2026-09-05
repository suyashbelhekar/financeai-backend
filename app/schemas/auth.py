from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Any


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: Any
    name: str
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}
