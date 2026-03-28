import logging
from sqlmodel import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from uuid import UUID
from datetime import timezone, datetime, timedelta
from typing import Any, Optional

from app.core.models import Booking, Provider, Service
from app.modules.Notifications.service import NotificationService
from .schemes import BookingCreate


class BookingService:
    VALID_BOOKING_STATUSES = {"pending", "accepted", "completed", "cancelled"}
    PROVIDER_ALLOWED_STATUSES = {"completed", "cancelled"}

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
                user_id=user_id,
                title=title,
                message=message,
                session=session,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                payload=payload,
            )
        except Exception:
            logging.exception("Failed to create notification")


    async def _get_booking_or_404(self, booking_id: str, session: AsyncSession):

        booking = await session.get(Booking, booking_id)

        if not booking or booking.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Booking not found")

        return booking


    async def _get_provider_for_booking(self, booking: Booking, session: AsyncSession):

        service = await session.get(Service, booking.service_id)
        if not service:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

        provider = await session.get(Provider, service.provider_id)
        if not provider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")

        return provider


    async def create_booking(self,booking_data: BookingCreate,user_id: UUID,session: AsyncSession):

        # Check if service exists
        service = await session.get(Service, booking_data.service_id)

        if not service:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Service not found")

        booking_date = booking_data.booking_date
        if booking_date.tzinfo is not None:
            booking_date = booking_date.astimezone(timezone.utc).replace(tzinfo=None)

        booking = Booking(
            service_id=booking_data.service_id,
            customer_id=user_id,
            booking_date=booking_date
        )

        session.add(booking)

        await session.commit()
        await session.refresh(booking)

        provider = await session.get(Provider, service.provider_id)

        if provider:
            await self._safe_create_notification(
                user_id=provider.user_id,
                title="New Booking Request",
                message=(
                    f"You have a new booking request for service '{service.name}' "
                    f"(booking ID: {booking.uid})."
                ),
                session=session,
                event_type="booking.created",
                entity_type="booking",
                entity_id=booking.uid,
                payload={"service_id": str(service.uid), "status": booking.status},
            )

        await self._safe_create_notification(
            user_id=user_id,
            title="Booking Created",
            message=(
                f"Your booking has been created successfully with status '{booking.status}' "
                f"(booking ID: {booking.uid})."
            ),
            session=session,
            event_type="booking.created",
            entity_type="booking",
            entity_id=booking.uid,
            payload={"service_id": str(service.uid), "status": booking.status},
        )

        return booking


    async def get_user_bookings(self,user_id:str,session: AsyncSession):

        statement = select(Booking).where(
            Booking.customer_id == user_id,
            Booking.deleted_at == None,
        )

        result = await session.exec(statement)

        return result.all()


    async def get_provider_bookings(self, user_id: str, session: AsyncSession):

        provider_stmt = select(Provider).where(Provider.user_id == user_id)
        provider_result = await session.exec(provider_stmt)
        provider = provider_result.first()

        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider profile not found"
            )

        service_stmt = select(Service.uid).where(Service.provider_id == provider.uid)
        service_result = await session.exec(service_stmt)
        service_ids = service_result.all()

        if not service_ids:
            return []

        booking_stmt = (
            select(Booking)
            .where(
                Booking.service_id.in_(service_ids),
                Booking.deleted_at == None,
            )
            .order_by(desc(Booking.created_at))
        )
        booking_result = await session.exec(booking_stmt)
        return booking_result.all()


    async def update_booking_status(self,booking_id:str,status_value: str,current_user,session: AsyncSession):

        if status_value not in self.VALID_BOOKING_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid booking status. Allowed values: {', '.join(sorted(self.VALID_BOOKING_STATUSES))}"
            )

        booking = await self._get_booking_or_404(booking_id, session)

        if current_user.role != "admin":
            provider = await self._get_provider_for_booking(booking, session)
            if provider.user_id != current_user.uid:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update bookings for your own services"
                )

            if status_value not in self.PROVIDER_ALLOWED_STATUSES:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Providers can only set booking status to completed or cancelled"
                )

        booking.status = status_value

        await session.commit()
        await session.refresh(booking)

        provider = await self._get_provider_for_booking(booking, session)

        await self._safe_create_notification(
            user_id=booking.customer_id,
            title="Booking Status Updated",
            message=(
                f"Your booking {booking.uid} status has been updated to '{booking.status}'."
            ),
            session=session,
            event_type="booking.status_updated",
            entity_type="booking",
            entity_id=booking.uid,
            payload={"status": booking.status},
        )

        if provider.user_id != current_user.uid:
            await self._safe_create_notification(
                user_id=provider.user_id,
                title="Booking Status Updated",
                message=(
                    f"Booking {booking.uid} status is now '{booking.status}'."
                ),
                session=session,
                event_type="booking.status_updated",
                entity_type="booking",
                entity_id=booking.uid,
                payload={"status": booking.status},
            )

        return booking
    
    async def delete_booking(
        self,
        booking_id: str,
        current_user,
        session: AsyncSession,
        delete_reason: Optional[str] = None,
    ):

        booking = await self._get_booking_or_404(booking_id, session)

        if current_user.role != "admin" and booking.customer_id != current_user.uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own bookings"
            )

        service = await session.get(Service, booking.service_id)
        provider = await session.get(Provider, service.provider_id) if service else None

        # Persist cancelled status before soft-delete for consistent state transitions.
        booking.status = "cancelled"
        booking.deleted_at = datetime.utcnow()
        booking.deleted_by = current_user.uid
        booking.delete_reason = delete_reason
        await session.commit()
        await session.refresh(booking)

        if provider and provider.user_id != current_user.uid:
            await self._safe_create_notification(
                user_id=provider.user_id,
                title="Booking Cancelled",
                message=(
                    f"Booking {booking.uid} was cancelled by the customer/admin."
                ),
                session=session,
                event_type="booking.cancelled",
                entity_type="booking",
                entity_id=booking.uid,
                payload={
                    "status": "cancelled",
                    "deleted_by": str(current_user.uid),
                    "delete_reason": delete_reason,
                },
            )

        return {"detail": "Booking deleted successfully"}


    async def expire_pending_bookings(self, timeout_minutes: int, session: AsyncSession):

        if timeout_minutes <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="timeout_minutes must be greater than 0"
            )

        cutoff = datetime.utcnow() - timedelta(minutes=timeout_minutes)

        statement = select(Booking).where(
            Booking.status == "pending",
            Booking.created_at <= cutoff,
            Booking.deleted_at == None,
        )
        result = await session.exec(statement)
        expired_bookings = result.all()

        if not expired_bookings:
            return {"expired_count": 0}

        for booking in expired_bookings:
            booking.status = "cancelled"

        await session.commit()

        for booking in expired_bookings:
            await self._safe_create_notification(
                user_id=booking.customer_id,
                title="Booking Expired",
                message=(
                    f"Your booking {booking.uid} expired because the provider did not respond in time."
                ),
                session=session,
                event_type="booking.expired",
                entity_type="booking",
                entity_id=booking.uid,
                payload={"status": "cancelled", "reason": "provider_timeout"},
            )

        return {"expired_count": len(expired_bookings)}
