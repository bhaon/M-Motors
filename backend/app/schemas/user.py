from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.user import RoleEnum


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    role: RoleEnum
    email_verified: bool


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginIn(BaseModel):
    email: EmailStr
    password: str
