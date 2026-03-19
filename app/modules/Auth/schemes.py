from typing import Literal

from pydantic import BaseModel, EmailStr, Field
import uuid
from datetime import datetime

class SignUpScheme(BaseModel):
    username: str
    first_name: str
    last_name: str
    role: Literal["user", "provider"] = Field(default="user")
    email: EmailStr
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "role": "user",
                "email": "johndoe@example.com",
                "password": "strongpassword123"
            }
        }
    }
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
