from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.models import User

class Auth_service:
    async def get_user_by_email(self, email: str, session: AsyncSession):
        statement = select(User).where(User.email == email)
        result = await session.exec(statement)
        return result.first()

    async def user_exists(self, email: str, session: AsyncSession):
        user = await self.get_user_by_email(email, session)
        return True if user else False     