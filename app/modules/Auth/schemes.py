from pydantic import BaseModel, EmailStr, Field

class SignUpScheme(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
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