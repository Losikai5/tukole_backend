# modules/Admin/router.py
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import RoleChecker
from app.core.models import UserRole  # ← fixed import

from .schemes import (
    AdminActionResponse,
    AdminDeletedBookingResponse,
    AdminDeletedReviewResponse,
    AdminDashboardResponse,
    AdminDisputeResolve,
    AdminDisputeResponse,
    AdminProviderResponse,
    AdminProviderServiceResponse,
    AdminUserResponse,
    UserRoleUpdate,
    UserStatusUpdate,
)
from .service import AdminService

# Fixed — RoleChecker now uses UserRole enum not plain string
admin_router = APIRouter(
    dependencies=[Depends(RoleChecker([UserRole.ADMIN]))]
)
admin_service = AdminService()


@admin_router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard(session: AsyncSession = Depends(get_db)):
    return await admin_service.get_dashboard_metrics(session)


@admin_router.get("/users", response_model=List[AdminUserResponse])
async def get_all_users(session: AsyncSession = Depends(get_db)):
    return await admin_service.list_users(session)


@admin_router.delete("/users/{user_id}", response_model=AdminActionResponse)
async def delete_user(user_id: UUID, session: AsyncSession = Depends(get_db)):
    return await admin_service.delete_user(user_id, session)


@admin_router.patch("/users/{user_id}/status", response_model=AdminUserResponse)
async def set_user_status(
    user_id: UUID,
    payload: UserStatusUpdate,
    session: AsyncSession = Depends(get_db),
):
    return await admin_service.update_user_status(user_id, payload.is_active, session)


@admin_router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
async def set_user_role(
    user_id: UUID,
    payload: UserRoleUpdate,
    session: AsyncSession = Depends(get_db),
):
    return await admin_service.update_user_role(user_id, payload.role, session)


@admin_router.get("/disputes", response_model=List[AdminDisputeResponse])
async def get_all_disputes(session: AsyncSession = Depends(get_db)):
    return await admin_service.list_disputes(session)


# Fixed — now accepts resolution field and triggers payment + notifications
@admin_router.patch("/disputes/{dispute_id}/resolve", response_model=AdminDisputeResponse)
async def resolve_dispute(
    dispute_id: UUID,
    payload: AdminDisputeResolve,
    session: AsyncSession = Depends(get_db),
):
    return await admin_service.resolve_dispute(
        dispute_id,
        payload.status,
        payload.admin_response,
        payload.resolution,  # ← new field passed through
        session,
    )


@admin_router.get("/audits/deleted-bookings", response_model=List[AdminDeletedBookingResponse])
async def get_deleted_bookings(session: AsyncSession = Depends(get_db)):
    return await admin_service.list_deleted_bookings(session)


@admin_router.get("/audits/deleted-reviews", response_model=List[AdminDeletedReviewResponse])
async def get_deleted_reviews(session: AsyncSession = Depends(get_db)):
    return await admin_service.list_deleted_reviews(session)


@admin_router.get("/providers", response_model=List[AdminProviderResponse])
async def get_all_providers(session: AsyncSession = Depends(get_db)):
    return await admin_service.list_providers(session)


@admin_router.get("/providers/{provider_id}/services", response_model=List[AdminProviderServiceResponse])
async def get_provider_services(
    provider_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    return await admin_service.list_provider_services(provider_id, session)


@admin_router.delete("/providers/{provider_id}", response_model=AdminActionResponse)
async def delete_provider(
    provider_id: UUID,
    session: AsyncSession = Depends(get_db),
):
    return await admin_service.delete_provider(provider_id, session)