from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user
from .service import NotificationService
from .schemes import NotificationResponse
from typing import List

notification_router = APIRouter()
notification_service = NotificationService()

@notification_router.get("/", response_model=List[NotificationResponse])
async def get_my_notifications(
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):

    return await notification_service.get_user_notifications(
        current_user.uid,
        session
    )

@notification_router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: str,
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return await notification_service.mark_as_read(notification_id, current_user.uid, session)
