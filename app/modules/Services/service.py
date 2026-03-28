from sqlalchemy.ext.asyncio import AsyncSession
from .schemes import CreateService, UpdateService, ServiceResponse
from app.core.models import Service as ServiceModel
from app.core.models import Provider,Service
from sqlmodel import select, desc
from uuid import UUID
from fastapi import HTTPException, status

class ServiceService:
    async def _ensure_service_access(self, service: Service, current_user, session: AsyncSession):
        if current_user.role == "admin":
            return

        provider = await session.get(Provider, service.provider_id)
        if not provider or provider.user_id != current_user.uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only modify your own services"
            )

    async def create_service(self, service_data: CreateService, user_id: str, session: AsyncSession):
        """Create a new service."""

        # Provider accounts create services through their provider profile.
        statement = select(Provider).where(Provider.user_id == user_id)
        result = await session.exec(statement)
        provider = result.first()
        if not provider:
            raise ValueError("Provider not found")

        new_service = Service(**service_data.model_dump(), provider_id=provider.uid)
        session.add(new_service)
        await session.commit()
        await session.refresh(new_service)
        return new_service

    async def get_all_services(self, session: AsyncSession):
        statement = select(Service).order_by(desc(Service.created_at))
        results = await session.exec(statement)
        return results.all()

    async def get_service_by_id(self, service_id: UUID, session: AsyncSession):
        """Get a single service by its ID."""
        statement = select(Service).where(Service.uid == service_id)
        result = await session.exec(statement)
        return result.first()

    async def get_provider_services(self, provider_id: str, session: AsyncSession):
        """Get all services for a specific provider."""
        statement = select(Service).where(Service.provider_id == provider_id)
        results = await session.exec(statement)
        return results.all()

    async def update_service(self, service_id: str, service_data: UpdateService, current_user, session: AsyncSession):
        """Update an existing service."""
        service = select(Service).where(Service.uid == service_id)
        result = await session.exec(service)
        service = result.first()
        if not service:
            raise ValueError("Service not found")

        await self._ensure_service_access(service, current_user, session)

        update_data = service_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(service, key, value)

        await session.commit()
        await session.refresh(service)
        return service
    

    async def delete_service(self, service_id: str, current_user, session: AsyncSession):
        """Delete a service."""
        service = select(Service).where(Service.uid == service_id)
        result = await session.exec(service)
        service = result.first()
        if not service:
            raise ValueError("Service not found")

        await self._ensure_service_access(service, current_user, session)

        await session.delete(service)
        await session.commit()
        return True
