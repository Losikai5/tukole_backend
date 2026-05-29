# modules/Notification/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.modules.Notifications.service import NotificationService
from app.modules.Notifications.schemes import NotificationResponse, NotificationMarkRead

notification_router = APIRouter()
notification_service = NotificationService()

# Get all notifications for current user
@notification_router.get("/", response_model=list[NotificationResponse])
async def get_my_notifications(
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await notification_service.get_user_notifications(current_user.uid, session)

# Get only unread notifications
@notification_router.get("/unread", response_model=list[NotificationResponse])
async def get_unread_notifications(
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await notification_service.get_unread_notifications(current_user.uid, session)

# Mark a specific batch as read
@notification_router.patch("/batch/read")
async def mark_batch_as_read(
    data: NotificationMarkRead,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await notification_service.mark_batch_as_read(data.uids, current_user.uid, session)

# Mark a single notification as read
@notification_router.patch("/{notification_uid}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_uid: UUID,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        return await notification_service.mark_as_read(notification_uid, current_user.uid, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Mark all as read
@notification_router.patch("/read-all")
async def mark_all_as_read(
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await notification_service.mark_all_as_read(current_user.uid, session)