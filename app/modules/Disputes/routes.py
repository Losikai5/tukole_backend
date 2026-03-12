from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker

from .service import DisputeService
from .schemes import DisputeCreate, UpdateDispute, DisputeResponse


dispute_router = APIRouter()

dispute_service = DisputeService()


# Customer creates dispute
@dispute_router.post("/", response_model=DisputeResponse, status_code=status.HTTP_201_CREATED)
async def create_dispute(
    dispute_data: DisputeCreate,
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):

    dispute = await dispute_service.create_dispute(
        dispute_data,
        current_user.uid,
        session
    )

    return dispute


# Admin views all disputes
@dispute_router.get("/", response_model=List[DisputeResponse])
async def get_all_disputes(
    session: AsyncSession = Depends(get_db),
    _: bool = Depends(RoleChecker(["admin"]))
):

    return await dispute_service.get_all_disputes(session)


# Get single dispute
@dispute_router.get("/{dispute_id}", response_model=DisputeResponse)
async def get_dispute_by_id(
    dispute_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):

    return await dispute_service.get_dispute_by_id(
        dispute_id,
        session
    )


# Admin responds / updates dispute
@dispute_router.patch("/{dispute_id}", response_model=DisputeResponse)
async def update_dispute(
    dispute_id: UUID,
    dispute_data: UpdateDispute,
    session: AsyncSession = Depends(get_db),
    _: bool = Depends(RoleChecker(["admin"]))
):

    return await dispute_service.update_dispute(
        dispute_id,
        dispute_data,
        session
    )