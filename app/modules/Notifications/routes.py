from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from .service import NotificationService
from .schemes import (
    NotificationResponse,
    NotificationUnreadCountResponse,
    NotificationListResponse,
    NotificationMarkAllReadResponse,
    NotificationDeliveryMetricsResponse,
)
from uuid import UUID

notification_router = APIRouter()
notification_service = NotificationService()

@notification_router.get("/", response_model=NotificationListResponse)
async def get_my_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    unread_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):

    return await notification_service.get_user_notifications(
        current_user.uid,
        session,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
    )

@notification_router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return await notification_service.mark_as_read(notification_id, current_user.uid, session)


@notification_router.patch("/read-all", response_model=NotificationMarkAllReadResponse)
async def mark_all_notifications_read(
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    marked_count = await notification_service.mark_all_as_read(current_user.uid, session)
    return NotificationMarkAllReadResponse(marked_count=marked_count)


@notification_router.get("/unread-count", response_model=NotificationUnreadCountResponse)
async def get_unread_notifications_count(
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    unread_count = await notification_service.get_unread_count(current_user.uid, session)
    return NotificationUnreadCountResponse(unread_count=unread_count)


@notification_router.get("/delivery-metrics", response_model=NotificationDeliveryMetricsResponse)
async def get_notification_delivery_metrics(
    _: bool = Depends(RoleChecker(["admin"]))
):
    return await notification_service.get_delivery_metrics()
