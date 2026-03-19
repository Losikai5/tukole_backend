from .service import ProviderService
from .schemes import ProviderBase, ProviderResponse
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from typing import List

provider_router = APIRouter()

provider_service = ProviderService()

@provider_router.post("/provider", response_model=ProviderResponse)
async def create_provider(provider_data: ProviderBase, current_user=Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await provider_service.create_provider(provider_data, current_user.uid, session)

@provider_router.get("/me", response_model=ProviderResponse)
async def get_provider_by_user_id(current_user=Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    return await provider_service.get_provider_by_user_id(current_user.uid, session)

@provider_router.put("/provider/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: str,
    provider_data: ProviderBase,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _: bool = Depends(RoleChecker(["provider", "admin"]))
):
    return await provider_service.update_provider(provider_id, provider_data, session)
@provider_router.delete("/provider/{provider_id}")
async def delete_provider(provider_id: str,session: AsyncSession = Depends(get_db),current_user=Depends(get_current_user), _: bool = Depends(RoleChecker(["provider", "admin"]))):
    await provider_service.delete_provider(provider_id, session)
    return {"detail": "Provider profile deleted successfully"}

@provider_router.get("/providers", response_model=List[ProviderResponse])
async def get_all_providers(session: AsyncSession = Depends(get_db)):
    providers = await provider_service.get_all_providers(session)
    return providers