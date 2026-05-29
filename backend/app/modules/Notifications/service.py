# modules/Notification/service.py
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.models import Notification, NotificationType


class NotificationService:

    async def create_notification(
        self,
        user_uid: UUID,
        message: str,
        notification_type: NotificationType,
        session: AsyncSession
    ) -> Notification:
        notification = Notification(
            user_uid=user_uid,
            message=message,
            notification_type=notification_type,
        )
        session.add(notification)
        await session.commit()
        await session.refresh(notification)
        return notification

    async def get_user_notifications(
        self,
        user_uid: UUID,
        session: AsyncSession
    ) -> list[Notification]:
        statement = (
            select(Notification)
            .where(Notification.user_uid == user_uid)
            .order_by(Notification.created_at.desc())
        )
        result = await session.exec(statement)
        return result.all()

    async def get_unread_notifications(
        self,
        user_uid: UUID,
        session: AsyncSession
    ) -> list[Notification]:
        statement = (
            select(Notification)
            .where(Notification.user_uid == user_uid)
            .where(Notification.is_read == False)
        )
        result = await session.exec(statement)
        return result.all()

    async def mark_as_read(
        self,
        notification_uid: UUID,
        user_uid: UUID,
        session: AsyncSession
    ) -> Notification:
        statement = (
            select(Notification)
            .where(Notification.uid == notification_uid)
            .where(Notification.user_uid == user_uid)
        )
        result = await session.exec(statement)
        notification = result.first()
        if not notification:
            raise ValueError("Notification not found")  # ← ValueError not HTTPException
        notification.is_read = True
        session.add(notification)
        await session.commit()
        await session.refresh(notification)
        return notification

    async def mark_batch_as_read(
        self,
        uids: list[UUID],        # ← specific batch from client
        user_uid: UUID,
        session: AsyncSession
    ) -> dict:
        statement = (
            select(Notification)
            .where(Notification.uid.in_(uids))
            .where(Notification.user_uid == user_uid)
        )
        result = await session.exec(statement)
        notifications = result.all()

        for notification in notifications:
            notification.is_read = True
            session.add(notification)

        await session.commit()
        return {"message": f"{len(notifications)} notifications marked as read"}

    async def mark_all_as_read(
        self,
        user_uid: UUID,
        session: AsyncSession
    ) -> dict:
        statement = (
            select(Notification)
            .where(Notification.user_uid == user_uid)
            .where(Notification.is_read == False)
        )
        result = await session.exec(statement)
        unread = result.all()

        for notification in unread:
            notification.is_read = True
            session.add(notification)

        await session.commit()
        return {"message": f"{len(unread)} notifications marked as read"}