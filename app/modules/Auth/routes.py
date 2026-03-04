from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from .service import Auth_service
from app.modules.User.service import UserService
from app.modules.User.schemes import UserCreate
from app.modules.User.model import User
from .schemes import SignUpScheme, UserResponseScheme, SignInScheme
from .utils import verify_password, create_refresh_token, create_access_token, hash_password
from fastapi.responses import JSONResponse
from datetime import timedelta


auth_router = APIRouter()
auth_service = Auth_service()
user_service = UserService()


@auth_router.post("/login")
async def login(user_data: SignInScheme, session: AsyncSession = Depends(get_db)):
    user = await auth_service.get_user_by_email(user_data.email, session)

    if not user or not verify_password(user_data.password, user.hashed_password):
         raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )

    user_payload = {
    "uid": str(user.uid),
    "role": user.role
           }

    access_token = create_access_token(user_payload, refresh=False)
    refresh_token = create_refresh_token(user_payload,refresh=True,expiry=timedelta(days=7))

    return JSONResponse(content={
    "message": "Login successful",
    "access_token": access_token,
    "refresh_token": refresh_token,
     "user": {
        "uid": str(user.uid),
        "username": user.username,
        "email": user.email,
        "role": user.role
}
    })


@auth_router.post("/register", response_model=UserResponseScheme, status_code=status.HTTP_201_CREATED)
async def register(user_data: SignUpScheme, session: AsyncSession = Depends(get_db)):
    # Check if user already exists
    user_exists = await auth_service.user_exists(user_data.email, session)
    if user_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    
    # Hash the password
    hashed_pwd = hash_password(user_data.password)
    
    # Prepare user data (exclude password from SignUpScheme)
    user_create_data = UserCreate(
        username=user_data.username,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email,
        is_active=user_data.is_active,
        role=user_data.role
    )
    
    # Create user via User service
    new_user = await user_service.create_user(user_create_data, hashed_pwd, session)
    return new_user

""""
@auth_router.post("/logout")
async def logout():
    pass
@auth_router.post("/refresh-token")
async def refresh_token():
    pass
@auth_router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {
        "user": current_user
    }
"""