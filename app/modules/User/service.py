from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc
from uuid import UUID
from .schemes import UserCreate, UserUpdate
from app.core.models import User as UserModel


class UserService:

    async def get_all_users(self, session: AsyncSession):
        statement = select(UserModel).order_by(desc(UserModel.created_at))
        results = await session.exec(statement)
        return results.all()

    async def get_user_by_id(self, uid: UUID, session: AsyncSession):
        statement = select(UserModel).where(UserModel.uid == uid)
        results = await session.exec(statement)
        return results.first()

    async def create_user(self, user_data: UserCreate, hashed_password: str, session: AsyncSession):
        """Create a new user with the provided hashed password."""
        new_user = UserModel(
            **user_data.model_dump(),
            hashed_password=hashed_password
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

    async def update_user(self, user_id: UUID, user_data: UserUpdate, session: AsyncSession):
        user = await self.get_user_by_id(user_id, session)
        if not user:
            raise ValueError("User not found")

        update_data = user_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)

        await session.commit()
        await session.refresh(user)
        return user

    async def delete_user(self, user_id: UUID, session: AsyncSession):
        user = await self.get_user_by_id(user_id, session)
        if not user:
            raise ValueError("User not found")

        await session.delete(user)
        await session.commit()
        return True