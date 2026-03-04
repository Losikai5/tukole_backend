from fastapi import APIRouter, Depends, HTTPException, status
from app.modules.User.service import UserService
from app.modules.User.schemes import UserUpdate, UserResponse
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List


user_router = APIRouter()
user_service = UserService()

@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, session: AsyncSession = Depends(get_db)):
   try:
        user = await user_service.get_user_by_id(user_id, session)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
   except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

# User creation should only be done through /auth/register endpoint
# This ensures proper password hashing and validation

@user_router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdate, session: AsyncSession = Depends(get_db)):
    try:
        return await user_service.update_user(user_id, user_data, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@user_router.delete("/{user_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, session: AsyncSession = Depends(get_db)):
       try:
            await user_service.delete_user(user_id, session)
       except ValueError as e:
              raise HTTPException(status_code=404, detail=str(e))
    

@user_router.get("/", response_model=List[UserResponse])
async def get_all_users(session: AsyncSession = Depends(get_db)):
    users = await user_service.get_all_users(session)
    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users found")
    return users