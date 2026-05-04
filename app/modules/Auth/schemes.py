from typing import Literal
from sqlmodel import SQLModel, Field
from pydantic import BaseModel, EmailStr, field_validator
import uuid
from app.core.models import UserRole
from datetime import datetime




class SignUpScheme(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.CONSUMER

    @field_validator("role", mode="before")
    @classmethod
    def role_must_not_be_admin(cls, v):
        if v == "user":
            return UserRole.CONSUMER
        if v == UserRole.ADMIN:
            raise ValueError("Cannot register as admin")
        return v
    

   
class SignInScheme(BaseModel):
    email: EmailStr
    password: str
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "johndoe@example.com",
                "password": "strongpassword123"
            }
        }   
    }
    
class UserResponseScheme(BaseModel):
    uid: uuid.UUID
    username: str
    first_name: str
    last_name: str
    role: str
    email: EmailStr
    is_active: bool
    created_at: datetime 
    updated_at: datetime
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "uid": "123e4567-e89b-12d3-a456-426614174000",
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "role": "user",
                "email": "johndoe@example.com",
                "is_active": False,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            }
        }
    }


class ResendVerificationRequest(BaseModel):
    email: EmailStr



