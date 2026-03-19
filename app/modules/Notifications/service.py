from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import Notification
from uuid import UUID
from fastapi import HTTPException, status

class NotificationService:

    async def create_notification(self, user_id: UUID, title: str, message: str, session: AsyncSession):

        notification = Notification(
            user_id=user_id,
            title=title,
            message=message
        )

        session.add(notification)

        await session.commit()
        await session.refresh(notification)

        return notification


    async def get_user_notifications(self, user_id: UUID, session: AsyncSession):

        statement = select(Notification).where(
            Notification.user_id == user_id
        ).order_by(Notification.created_at.desc())

        result = await session.exec(statement)

        return result.all()


    async def mark_as_read(self, notification_id: str, user_id: UUID, session: AsyncSession):

        notification = await session.get(Notification, notification_id)
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )

        if notification.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only mark your own notifications as read"
            )

        notification.is_read = True

        await session.commit()
        await session.refresh(notification)

        return notification
