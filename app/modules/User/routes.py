from fastapi import APIRouter, Depends
from app.modules.User.service import UserService
from app.modules.User.schemes import UserCreate, UserUpdate,UserResponse
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List


user_router = APIRouter()
user_service = UserService()

@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, session: AsyncSession = Depends(get_db)):
    user = await user_service.get_user_by_id(user_id, session)
    return user

@user_router.post("/", response_model=UserResponse)
async def create_user(user_data: UserCreate, session: AsyncSession = Depends(get_db)):
      create_user = await user_service.create_user(user_data, session)
      return create_user

@user_router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdate, session: AsyncSession = Depends(get_db)):
    updated_user = await user_service.update_user(user_id, user_data, session)
    return updated_user

@user_router.delete("/{user_id}")
async def delete_user(user_id: str, session: AsyncSession = Depends(get_db)):
    result = await user_service.delete_user(user_id, session)
    return {"deleted": result}

@user_router.get("/", response_model=List[UserResponse])
async def get_all_users(session: AsyncSession = Depends(get_db)):
    users = await user_service.get_all_users(session)
    return users