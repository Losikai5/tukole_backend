from sqlalchemy.ext.asyncio import AsyncSession
from .schemes import CreateService, UpdateService, ServiceResponse
from app.core.models import Service as ServiceModel
from sqlmodel import select, desc
from uuid import UUID

class ServiceService:
    async def create_service(self, service_data: CreateService, session: AsyncSession):
        """Create a new service."""
        new_service = ServiceModel(**service_data.model_dump())
        session.add(new_service)
        await session.commit()
        await session.refresh(new_service)
        return new_service

    async def get_all_services(self, session: AsyncSession):
        statement = select(ServiceModel).order_by(desc(ServiceModel.created_at))
        results = await session.exec(statement)
        return results.all()

    async def get_service_by_id(self, service_id: str, session: AsyncSession):
        """Get a service by ID."""
        statement = select(ServiceModel).where(ServiceModel.uid == service_id)
        results = await session.exec(statement)
        return results.first()
    

    async def update_service(self, service_id: str, service_data: UpdateService, session: AsyncSession):
        """Update an existing service."""
        service = await self.get_service_by_id(service_id, session)
        if not service:
            raise ValueError("Service not found")

        update_data = service_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(service, key, value)

        await session.commit()
        await session.refresh(service)
        return service
    

    async def delete_service(self, service_id: str, session: AsyncSession):
        """Delete a service."""
        service = await self.get_service_by_id(service_id, session)
        if not service:
            raise ValueError("Service not found")

        await session.delete(service)
        await session.commit()
        return True
