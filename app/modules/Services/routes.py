from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from .schemes import ServiceCreate, ServiceUpdate, ServiceResponse
from .service import ServiceService
from app.core.database import get_db

service_router = APIRouter()
service_service = ServiceService()

@service_router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(service_data: ServiceCreate, session: AsyncSession = Depends(get_db)):
    return await service_service.create_service(service_data, session)

@service_router.get("/", response_model=list[ServiceResponse])
async def get_all_services(session: AsyncSession = Depends(get_db)):
    return await service_service.get_all_services(session)

@service_router.get("/{service_id}", response_model=ServiceResponse)
async def get_service_by_id(service_id: str, session: AsyncSession = Depends(get_db)):
    return await service_service.get_service_by_id(service_id, session)

@service_router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(service_id: str, service_data: ServiceUpdate, session: AsyncSession = Depends(get_db)):
    return await service_service.update_service(service_id, service_data, session)

@service_router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(service_id: str, session: AsyncSession = Depends(get_db)):
    return await service_service.delete_service(service_id, session)
