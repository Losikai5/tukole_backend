from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.core.models import Provider ,User
from .schemes import ProviderBase

class ProviderService:
    async def create_provider(self, provider_data: ProviderBase, user_id: str, session: AsyncSession):
        """Create a new provider profile."""
        # Check if the user already has a provider profile
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        #check role 
        if user.role != "provider":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have provider role")
        #check if provider profile already exists
        statement = select(Provider).where(Provider.user_id == user_id)
        result = await session.exec(statement)
        existing_provider = result.first()
        if existing_provider:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already has a provider profile")

        new_provider = Provider(**provider_data.model_dump(), user_id=user_id)
        session.add(new_provider)
        await session.commit()
        await session.refresh(new_provider)
        return new_provider
    
    async def get_provider_by_user_id(self, user_id: str, session: AsyncSession):
        """Get a provider profile by user ID."""
        statement = select(Provider).where(Provider.user_id == user_id)
        result = await session.exec(statement)
        provider = result.first()
        if not provider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider profile not found")
        return provider
    
    async def update_provider(self, provider_id: str, provider_data: ProviderBase, session: AsyncSession):
        """Update an existing provider profile."""
        statement = select(Provider).where(Provider.uid == provider_id)
        result = await session.exec(statement)
        provider = result.first()
        if not provider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider profile not found")

        update_data = provider_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(provider, key, value)

        await session.commit()
        await session.refresh(provider)
        return provider
    
    async def delete_provider(self, provider_id: str, session: AsyncSession):
        """Delete a provider profile."""
        statement = select(Provider).where(Provider.uid == provider_id)
        result = await session.exec(statement)
        provider = result.first()
        if not provider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider profile not found")

        await session.delete(provider)
        await session.commit()
        return True
    async def get_all_providers(self, session: AsyncSession):
        """Get all provider profiles."""
        statement = select(Provider)
        result = await session.exec(statement)
        return result.all()