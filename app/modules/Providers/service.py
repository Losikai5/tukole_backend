from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from fastapi import HTTPException, status
from app.core.models import Provider, User, UserRole
from app.modules.Providers.schemes import ProviderCreate, ProviderUpdate


class ProviderService:

    def _ensure_provider_access(self, provider: Provider, current_user):
        if current_user.role == UserRole.ADMIN:
            return provider

        if current_user.uid != provider.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own provider profile")

        return provider

    async def get_provider_by_user_id(self, user_id: UUID, session: AsyncSession):
        statement = select(Provider).where(Provider.user_id == user_id)
        result = await session.exec(statement)
        return result.first()

    async def get_all_providers(self, session: AsyncSession):
        statement = select(Provider)
        result = await session.exec(statement)
        return result.all()

    async def create_provider(self, user: User, data: ProviderCreate, session: AsyncSession):
        # Check 1 — already a provider?
        existing = await self.get_provider_by_user_id(user.uid, session)
        if existing:
            raise ValueError("Provider profile already exists")

        # Create provider profile
        provider = Provider(**data.model_dump(), user_id=user.uid)
        session.add(provider)

        # Atomic update — upgrade role
        user.role = UserRole.PROVIDER
        session.add(user)

        await session.commit()
        await session.refresh(provider)
        return provider

    async def update_provider(self, current_user: User, user_id: UUID, data: ProviderUpdate, session: AsyncSession):
        provider = await self.get_provider_by_user_id(user_id, session)
        if not provider:
            raise ValueError("Provider profile not found")

        self._ensure_provider_access(provider, current_user)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(provider, key, value)

        await session.commit()
        await session.refresh(provider)
        return provider

    async def delete_provider(self, provider_user_id: UUID, session: AsyncSession):
        provider = await self.get_provider_by_user_id(provider_user_id, session)
        if not provider:
            raise ValueError("Provider profile not found")
        await session.delete(provider)
        await session.commit()
        return True