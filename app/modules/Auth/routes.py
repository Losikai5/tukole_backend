from fastapi import APIRouter, Depends
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from .service import Auth_service
from app.modules.User.model import User
from .schemes import SignUpScheme,UserResponseScheme,SignInScheme
from fastapi import HTTPException, status
from .utils import verify_password,create_refresh_token,create_access_token
from fastapi.responses import JSONResponse
from datetime import timedelta

auth_router = APIRouter()
auth_service = Auth_service()


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


@auth_router.post("/register",response_model=UserResponseScheme, status_code=status.HTTP_201_CREATED)
async def register(user_data:SignUpScheme,session:AsyncSession = Depends(get_db)):
    user_exists = await auth_service.user_exists(user_data.email,session)
    if user_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    new_user = await auth_service.create_user(user_data,session)
    return new_user


@auth_router.post("/logout")
async def logout():
    pass
@auth_router.post("/refresh-token")
async def refresh_token():
    pass
@auth_router.get("/me")
async def get_current_user_info():
    pass
