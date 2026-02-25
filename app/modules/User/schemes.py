from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid


class UserCreate(BaseModel):
    
    username: str 
    first_name: str 
    last_name: str 
    email: EmailStr
    #password: str 
    is_active: bool = Field(default=False, nullable=False)
    role: str 
    model_config = {"from_attributes": True,
                    "json_schema_extra": {
                        "example": {
                            "username": "johndoe",
                            "first_name": "John",
                            "last_name": "Doe",
                            "email": "johndoe@example.com",
                            #"hashed_password": "securepassword123",
                            "is_active": False,
                            "role": "user"
                        }
                    }
                }
    
class UserUpdate(BaseModel):  
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    #password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    model_config = {"from_attributes": True,
                    "json_schema_extra": {
                        "example": {
                            "first_name": "John",
                            "last_name": "Doe",
                            "email": "johndoe@example.com",
                           # "hashed_password": "newsecurepassword456",
                            "is_active": False,
                            "role": "admin"
                        }
                    }
                }
    
class UserResponse(BaseModel):
    uid: uuid.UUID
    username: str 
    first_name: str 
    last_name: str 
    email: EmailStr
    is_active: bool
    role: str 
    model_config = {"from_attributes": True,
                    "json_schema_extra": {
                        "example": {
                            "uid": "123e4567-e89b-12d3-a456-426614174000",
                            "username": "johndoe",
                            "first_name": "John",
                            "last_name": "Doe",
                            "email": "johndoe@example.com",
                            "is_active": True,
                            "role": "user"
                        }
                    }
                }