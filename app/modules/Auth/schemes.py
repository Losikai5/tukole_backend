from pydantic import BaseModel, EmailStr, Field

class SignUpScheme(BaseModel):
    username: str
    first_name: str
    last_name: str
    role: str = Field(default="user")
    email: EmailStr
    is_verified: bool = Field(default=False)
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "role": "user",
                "email": "johndoe@example.com",
                "is_verified": False,
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
    uuid: str
    username: str
    first_name: str
    last_name: str
    role: str
    email: EmailStr
    is_verified: bool

    model_config = {
        "json_schema_extra": {
            "example": {
                "uuid": "123e4567-e89b-12d3-a456-426614174000",
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "role": "user",
                "email": "johndoe@example.com",
                "is_verified": False
            }
        }
    }