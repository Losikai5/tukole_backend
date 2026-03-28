import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime
from typing import Any, Optional

from app.core.models import Dispute, Booking, Service, Provider, User
from app.modules.Notifications.service import NotificationService
from .schemes import DisputeCreate, UpdateDispute


class DisputeService:

    def __init__(self):
        self.notification_service = NotificationService()


    async def _safe_create_notification(
        self,
        user_id: UUID,
        title: str,
        message: str,
        session: AsyncSession,
        event_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        payload: Optional[dict[str, Any]] = None,
    ):
        try:
            await self.notification_service.create_notification(
                user_id,
                title,
                message,
                session,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                payload=payload,
            )
        except Exception:
            logging.exception("Failed to create dispute notification")


    async def _get_admin_user_ids(self, session: AsyncSession):
        statement = select(User.uid).where(User.role == "admin")
        result = await session.exec(statement)
        return result.all()


    async def _get_booking_provider_user_id(self, booking: Booking, session: AsyncSession):
        service = await session.get(Service, booking.service_id)
        if not service:
            return None

        provider = await session.get(Provider, service.provider_id)
        if not provider:
            return None

        return provider.user_id

    async def create_dispute(
        self,
        dispute_data: DisputeCreate,
        user_id: UUID,
        session: AsyncSession
    ):
        """Customer raises a dispute"""

        booking = await session.get(Booking, dispute_data.booking_id)

        if not booking or booking.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )

        # Ensure user participated in booking
        if booking.customer_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot dispute this booking"
            )

        # Prevent duplicate dispute
        statement = select(Dispute).where(
            Dispute.booking_id == dispute_data.booking_id
        )

        result = await session.exec(statement)
        existing_dispute = result.first()

        if existing_dispute:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dispute already exists for this booking"
            )

        dispute = Dispute(
            booking_id=dispute_data.booking_id,
            raised_by=user_id,
            reason=dispute_data.reason,
            description=dispute_data.description
        )

        session.add(dispute)

        await session.commit()
        await session.refresh(dispute)

        provider_user_id = await self._get_booking_provider_user_id(booking, session)
        admin_user_ids = await self._get_admin_user_ids(session)

        for admin_user_id in admin_user_ids:
            await self._safe_create_notification(
                user_id=admin_user_id,
                title="Dispute Raised",
                message=(
                    f"A new dispute ({dispute.uid}) has been raised for booking {dispute.booking_id}."
                ),
                session=session,
                event_type="dispute.raised",
                entity_type="dispute",
                entity_id=dispute.uid,
                payload={"booking_id": str(dispute.booking_id), "status": dispute.status},
            )

        if provider_user_id and provider_user_id != user_id:
            await self._safe_create_notification(
                user_id=provider_user_id,
                title="Dispute Raised",
                message=(
                    f"A dispute has been raised for booking {dispute.booking_id}."
                ),
                session=session,
                event_type="dispute.raised",
                entity_type="dispute",
                entity_id=dispute.uid,
                payload={"booking_id": str(dispute.booking_id), "status": dispute.status},
            )

        return dispute


    async def get_all_disputes(self, session: AsyncSession):
        """Admin fetches all disputes"""

        statement = select(Dispute)

        result = await session.exec(statement)

        return result.all()


    async def get_dispute_by_id(self, dispute_id: UUID, current_user, session: AsyncSession):
        """Get a single dispute"""

        dispute = await session.get(Dispute, dispute_id)

        if not dispute:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dispute not found"
            )

        if current_user.role == "admin":
            return dispute

        if dispute.raised_by == current_user.uid:
            return dispute

        booking = await session.get(Booking, dispute.booking_id)
        provider_user_id = await self._get_booking_provider_user_id(booking, session) if booking else None

        if provider_user_id != current_user.uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this dispute"
            )

        return dispute


    async def update_dispute(
        self,
        dispute_id: UUID,
        dispute_data: UpdateDispute,
        current_user,
        session: AsyncSession
    ):
        """Admin updates dispute"""

        dispute = await self.get_dispute_by_id(dispute_id, current_user, session)

        update_data = dispute_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(dispute, key, value)

        # If resolved, set resolved_at
        if dispute_data.status == "resolved":
            dispute.resolved_at = datetime.utcnow()

        await session.commit()
        await session.refresh(dispute)

        booking = await session.get(Booking, dispute.booking_id)
        provider_user_id = await self._get_booking_provider_user_id(booking, session) if booking else None

        if dispute_data.status == "under_review":
            admin_user_ids = await self._get_admin_user_ids(session)
            for admin_user_id in admin_user_ids:
                await self._safe_create_notification(
                    user_id=admin_user_id,
                    title="Dispute Escalated",
                    message=(
                        f"Dispute {dispute.uid} has been escalated and is under review."
                    ),
                    session=session,
                    event_type="dispute.under_review",
                    entity_type="dispute",
                    entity_id=dispute.uid,
                    payload={"booking_id": str(dispute.booking_id), "status": dispute.status},
                )

        if dispute_data.status == "resolved" and booking:
            await self._safe_create_notification(
                user_id=booking.customer_id,
                title="Dispute Resolved",
                message=(
                    f"Your dispute {dispute.uid} for booking {dispute.booking_id} has been resolved."
                ),
                session=session,
                event_type="dispute.resolved",
                entity_type="dispute",
                entity_id=dispute.uid,
                payload={"booking_id": str(dispute.booking_id), "status": dispute.status},
            )

            if provider_user_id:
                await self._safe_create_notification(
                    user_id=provider_user_id,
                    title="Dispute Resolved",
                    message=(
                        f"Dispute {dispute.uid} for booking {dispute.booking_id} has been resolved."
                    ),
                    session=session,
                    event_type="dispute.resolved",
                    entity_type="dispute",
                    entity_id=dispute.uid,
                    payload={"booking_id": str(dispute.booking_id), "status": dispute.status},
                )

        if dispute_data.status == "rejected" and booking:
            await self._safe_create_notification(
                user_id=booking.customer_id,
                title="Dispute Rejected",
                message=(
                    f"Your dispute {dispute.uid} for booking {dispute.booking_id} has been rejected."
                ),
                session=session,
                event_type="dispute.rejected",
                entity_type="dispute",
                entity_id=dispute.uid,
                payload={"booking_id": str(dispute.booking_id), "status": dispute.status},
            )

            if provider_user_id:
                await self._safe_create_notification(
                    user_id=provider_user_id,
                    title="Dispute Rejected",
                    message=(
                        f"Dispute {dispute.uid} for booking {dispute.booking_id} has been rejected."
                    ),
                    session=session,
                    event_type="dispute.rejected",
                    entity_type="dispute",
                    entity_id=dispute.uid,
                    payload={"booking_id": str(dispute.booking_id), "status": dispute.status},
                )

        return dispute