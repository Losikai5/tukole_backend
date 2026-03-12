from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from .schemes import CreateService, UpdateService, ServiceResponse
from .service import ServiceService
from app.core.database import get_db
from app.core.dependencies import Bearer, get_current_user
from app.core.models import  Provider

service_router = APIRouter()
service_service = ServiceService()
token_auth = Bearer()  # Initialize the Bearer token authentication dependency

@service_router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(service_data: CreateService, session: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    """Create a new service."""
    try:
        return await service_service.create_service(service_data, current_user.uid, session)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@service_router.get("/", response_model=List[ServiceResponse])
async def get_all_services(session: AsyncSession = Depends(get_db)):
    """Get all services."""
    services = await service_service.get_all_services(session)
    return services

@service_router.get("/{service_id}", response_model=ServiceResponse)
async def get_service_by_id(service_id: UUID, session: AsyncSession = Depends(get_db)):
    """Get a service by ID."""
    service = await service_service.get_service_by_id(service_id, session)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return service

@service_router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(service_id: UUID, service_data: UpdateService, session: AsyncSession = Depends(get_db)):
    """Update a service."""
    try:
        return await service_service.update_service(service_id, service_data, session)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@service_router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(service_id: UUID, session: AsyncSession = Depends(get_db)):
    """Delete a service."""
    try:
        await service_service.delete_service(service_id, session)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
