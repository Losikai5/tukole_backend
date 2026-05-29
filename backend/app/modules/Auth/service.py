from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.models import User
from app.modules.Auth.utils import verify_password

class Auth_service:

    async def get_user_by_email(self, email: str, session: AsyncSession):
        statement = select(User).where(User.email == email)
        result = await session.exec(statement)
        return result.first()

    async def user_exists(self, email: str, session: AsyncSession):
        user = await self.get_user_by_email(email, session)
        return True if user else False

    async def verify_user(self, email: str, session: AsyncSession):
        user = await self.get_user_by_email(email, session)
        if not user:
            raise ValueError("User not found")
        if user.is_active:
            raise ValueError("Account already verified")
        
        user.is_active = True
        user.is_verified = True   
        await session.commit()
        await session.refresh(user)
        return user  
    
    async def authenticate_user(self, email: str, password: str, session: AsyncSession):
        user = await self.get_user_by_email(email, session)
        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")
        if not user.is_active:
            raise ValueError("Account not verified. Please verify your email first")
        return user