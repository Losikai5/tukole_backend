# modules/Service/service.py
from sqlmodel import select, desc
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from fastapi import HTTPException, status
from app.core.models import Service, Provider, UserRole
from app.modules.Services.schemes import ServiceCreate, ServiceUpdate


class ServiceService:

    async def _ensure_service_access(self, service: Service, current_user, session: AsyncSession):
        if current_user.role == UserRole.ADMIN:
            return service

        provider = await session.get(Provider, service.provider_id)
        if not provider or provider.user_id != current_user.uid:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only modify your own services")

        return service

    async def get_service_by_id(self, service_id: UUID, session: AsyncSession):
        statement = select(Service).where(Service.uid == service_id)
        result = await session.exec(statement)
        return result.first()

    async def get_all_services(self, session: AsyncSession):
        statement = select(Service).order_by(desc(Service.created_at))
        result = await session.exec(statement)
        return result.all()

    async def get_provider_services(self, provider_id: UUID, session: AsyncSession):
        statement = select(Service).where(Service.provider_id == provider_id)
        result = await session.exec(statement)
        return result.all()

    async def create_service(self, service_data: ServiceCreate, current_user, session: AsyncSession):
        result = await session.exec(select(Provider).where(Provider.user_id == current_user.uid))
        provider = result.first()
        if not provider:
            raise ValueError("Provider profile not found. Create a provider profile first")

        # prevent duplicate service names — return a friendly 400 via router
        existing_stmt = select(Service).where(Service.name == service_data.name)
        existing = (await session.exec(existing_stmt)).first()
        if existing:
            raise ValueError("A service with this name already exists")

        new_service = Service(**service_data.model_dump(), provider_id=provider.uid)
        session.add(new_service)
        await session.commit()
        await session.refresh(new_service)
        return new_service

    async def update_service(self, service_id: UUID, service_data: ServiceUpdate, current_user, session: AsyncSession):
        service = await self.get_service_by_id(service_id, session)
        if not service:
            raise ValueError("Service not found")

        await self._ensure_service_access(service, current_user, session)

        update_data = service_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(service, key, value)

        await session.commit()
        await session.refresh(service)
        return service

    async def delete_service(self, service_id: UUID, current_user, session: AsyncSession):
        service = await self.get_service_by_id(service_id, session)
        if not service:
            raise ValueError("Service not found")

        await self._ensure_service_access(service, current_user, session)

        await session.delete(service)
        await session.commit()
        return True