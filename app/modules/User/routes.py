from fastapi import APIRouter, Depends, HTTPException, status
from app.modules.User.service import UserService
from app.modules.User.schemes import UserUpdate, UserResponse
from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List


user_router = APIRouter()
user_service = UserService()

@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
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
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != "admin" and str(current_user.uid) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own account"
        )

    update_payload = user_data.model_dump(exclude_unset=True)

    if current_user.role != "admin":
        restricted_fields = {"role", "is_active"}
        attempted_restricted_fields = restricted_fields.intersection(update_payload)
        if attempted_restricted_fields:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can update role or activation status"
            )

    try:
        return await user_service.update_user(user_id, UserUpdate(**update_payload), session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@user_router.delete("/{user_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _: bool = Depends(RoleChecker(["admin"]))
):
       try:
            await user_service.delete_user(user_id, session)
       except ValueError as e:
              raise HTTPException(status_code=404, detail=str(e))
    

@user_router.get("/", response_model=List[UserResponse])
async def get_all_users(
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _: bool = Depends(RoleChecker(["admin"]))
):
    users = await user_service.get_all_users(session)
    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users found")
    return users
