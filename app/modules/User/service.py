
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_db
from fastapi import Depends
from sqlmodel import select,desc
from.schemes import UserCreate, UserUpdate
from app.modules.User.model import User as UserModel
from fastapi import HTTPException


class UserService:
    async def get_all_users(self, session: AsyncSession ):
        statement = select(UserModel).order_by(desc(UserModel.created_at))
        results = await session.exec(statement)
        return results.all()
    
    async def get_user_by_id(self,uid: str, session: AsyncSession ):
        statement = select(UserModel).where(UserModel.uid == uid)
        results = await session.exec(statement)
        return results.first()
    
    async def create_user(self, user_data: UserCreate, session: AsyncSession ):
         user = user_data.model_dump()
         new_user = UserModel(**user)
         session.add(new_user)
         await session.commit()
         await session.refresh(new_user)
         return new_user
    async def update_user(self,user_id: str,user_data: UserUpdate,session: AsyncSession):
       user = await self.get_user_by_id(user_id, session)
       if not user:
          raise HTTPException(status_code=404, detail="User not found")
       update_data = user_data.model_dump(exclude_unset=True)
       for key, value in update_data.items():
          setattr(user, key, value)
       session.add(user)
       await session.commit()
       await session.refresh(user)

       return user
    
    async def delete_user(self,user_id: str, session: AsyncSession ):
        user = await self.get_user_by_id(user_id, session)
        if user:
            await session.delete(user)
            await session.commit()
            return True
        return HTTPException(status_code=404, detail="User not found")

   