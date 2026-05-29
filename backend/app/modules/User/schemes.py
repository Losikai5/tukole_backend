from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

from app.core.models import UserRole


class SignUpScheme(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.CONSUMER


class UserCreate(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRole = UserRole.CONSUMER


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None


class UserResponse(BaseModel):
    uid: uuid.UUID
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    is_active: bool
    role: str

    model_config = {"from_attributes": True}
