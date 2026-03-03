from sqlalchemy.ext.asyncio import AsyncSession
from .utils import  hash_password
from sqlmodel import select
from app.modules.User.model import User
from .schemes import SignUpScheme

class Auth_service:
    async def get_user_by_email(self,email:str,session:AsyncSession):
        statement = select(User).where(User.email == email)
        result = await session.exec(statement)
        return result.first()

    async def user_exists(self,email:str,session:AsyncSession):
          user = await self.get_user_by_email(email,session)
          return True if user else False
    

    async def create_user(self,user_data:SignUpScheme,session:AsyncSession):
         new_user = User(**user_data.model_dump(exclude={"password"}),
                         hashed_password = hash_password(user_data.password))
         session.add(new_user)
         await session.commit()
         await session.refresh(new_user)
         return new_user     