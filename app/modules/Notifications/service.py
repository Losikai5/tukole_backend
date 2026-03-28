import asyncio
import logging
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import Notification
from app.core.database import local_session
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import func, update
from typing import Any, Optional

class NotificationService:
    MAX_RETRIES = 2
    BASE_RETRY_DELAY_SECONDS = 0.25
    _delivery_metrics = {
        "attempted": 0,
        "succeeded": 0,
        "failed": 0,
        "retries": 0,
    }

    @classmethod
    def _increment_metric(cls, key: str, value: int = 1):
        cls._delivery_metrics[key] = cls._delivery_metrics.get(key, 0) + value

    async def create_notification(
        self,
        user_id: UUID,
        title: str,
        message: str,
        session: Optional[AsyncSession] = None,
        event_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        payload: Optional[dict[str, Any]] = None,
    ):
        # Notification writes use an isolated transaction so failures do not
        # rollback business operations that already succeeded in another session.
        self._increment_metric("attempted")
        max_attempts = self.MAX_RETRIES + 1

        for attempt in range(max_attempts):
            try:
                async with local_session() as notification_session:
                    notification = Notification(
                        user_id=user_id,
                        title=title,
                        message=message,
                        event_type=event_type,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        payload=payload,
                    )

                    notification_session.add(notification)

                    await notification_session.commit()
                    await notification_session.refresh(notification)

                    self._increment_metric("succeeded")
                    return notification
            except Exception:
                is_last_attempt = attempt == (max_attempts - 1)
                if is_last_attempt:
                    self._increment_metric("failed")
                    logging.exception("Failed to persist notification after retries")
                    raise

                self._increment_metric("retries")
                delay_seconds = self.BASE_RETRY_DELAY_SECONDS * (2 ** attempt)
                await asyncio.sleep(delay_seconds)


    async def get_user_notifications(
        self,
        user_id: UUID,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False,
    ):

        filters = [Notification.user_id == user_id]
        if unread_only:
            filters.append(Notification.is_read == False)

        count_statement = select(func.count()).select_from(Notification).where(*filters)
        count_result = await session.exec(count_statement)
        total = count_result.one()

        statement = select(Notification).where(
            *filters
        ).order_by(Notification.created_at.desc()).offset(offset).limit(limit)

        result = await session.exec(statement)

        return {
            "items": result.all(),
            "total": total,
            "limit": limit,
            "offset": offset,
        }


    async def mark_as_read(self, notification_id: UUID, user_id: UUID, session: AsyncSession):

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


    async def get_unread_count(self, user_id: UUID, session: AsyncSession):

        statement = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False
        )

        result = await session.exec(statement)

        return result.one()


    async def mark_all_as_read(self, user_id: UUID, session: AsyncSession):

        statement = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
            .values(is_read=True)
        )

        result = await session.exec(statement)
        await session.commit()

        return result.rowcount or 0


    async def get_delivery_metrics(self):

        attempted = self._delivery_metrics.get("attempted", 0)
        succeeded = self._delivery_metrics.get("succeeded", 0)
        failed = self._delivery_metrics.get("failed", 0)
        retries = self._delivery_metrics.get("retries", 0)
        success_rate = (succeeded / attempted) if attempted else 0.0

        return {
            "attempted": attempted,
            "succeeded": succeeded,
            "failed": failed,
            "retries": retries,
            "success_rate": round(success_rate, 4),
        }
