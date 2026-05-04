from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.core.models import UserRole
from app.modules.Services.service import ServiceService
from app.modules.Services.schemes import ServiceCreate, ServiceUpdate, ServiceResponse

service_router = APIRouter()
service_service = ServiceService()

# Public — anyone can browse services
@service_router.get("/", response_model=list[ServiceResponse])
async def get_all_services(session: AsyncSession = Depends(get_db)):
    return await service_service.get_all_services(session)

# Public — get single service
@service_router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    service = await service_service.get_service_by_id(service_id, session)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service

# Public — get all services for a specific provider
@service_router.get("/provider/{provider_id}", response_model=list[ServiceResponse])
async def get_provider_services(
    provider_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    return await service_service.get_provider_services(provider_id, session)

# Provider only — create a service
@service_router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    data: ServiceCreate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(RoleChecker([UserRole.PROVIDER]))  # ← role enforced here
):
    try:
        return await service_service.create_service(data, current_user, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Owner or admin — update a service
@service_router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: UUID,
    data: ServiceUpdate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        return await service_service.update_service(service_id, data, current_user, session)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Owner or admin — delete a service
@service_router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        await service_service.delete_service(service_id, current_user, session)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))