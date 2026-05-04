from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.core.models import UserRole
from app.modules.Providers.service import ProviderService
from app.modules.Providers.schemes import ProviderCreate, ProviderUpdate, ProviderResponse

provider_router = APIRouter()
provider_service = ProviderService()

# Public — anyone can browse providers
@provider_router.get("/", response_model=list[ProviderResponse])
async def get_all_providers(session: AsyncSession = Depends(get_db)):
    return await provider_service.get_all_providers(session)

# Provider or admin — view a profile
@provider_router.get("/{user_id}", response_model=ProviderResponse)
async def get_provider(
    user_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    provider = await provider_service.get_provider_by_user_id(user_id, session)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@provider_router.post("/", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    data: ProviderCreate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        return await provider_service.create_provider(current_user, data, session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@provider_router.put("/{user_id}", response_model=ProviderResponse)
async def update_provider(
    user_id: UUID,
    data: ProviderUpdate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        return await provider_service.update_provider(current_user, user_id, data, session)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@provider_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    user_id: UUID,
    session: AsyncSession = Depends(get_db),
    _=Depends(RoleChecker([UserRole.ADMIN]))
):
    try:
        await provider_service.delete_provider(user_id, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))