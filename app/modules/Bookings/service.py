# modules/Booking/service.py
from sqlmodel import select, desc
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from datetime import datetime, timezone
from app.core.models import Booking, Service, Provider, BookingStatus, UserRole, NotificationType
from app.modules.Bookings.schemes import BookingCreate, BookingStatusUpdate, BookingCancel
from app.modules.Notifications.service import NotificationService
from app.modules.Payments.service import PaymentService
from app.celery_task import send_booking_cancelled_email


VALID_TRANSITIONS = {
    BookingStatus.PENDING:   [BookingStatus.ACCEPTED, BookingStatus.CANCELLED],
    BookingStatus.ACCEPTED:  [BookingStatus.COMPLETED, BookingStatus.CANCELLED],
    BookingStatus.COMPLETED: [],
    BookingStatus.CANCELLED: []
}


notification_service = NotificationService()


class BookingService:

    async def get_booking_by_id(self, booking_id: UUID, session: AsyncSession):
        statement = select(Booking).where(Booking.uid == booking_id)
        result = await session.exec(statement)
        return result.first()

    async def get_all_bookings(self, session: AsyncSession):
        statement = select(Booking).order_by(desc(Booking.created_at))
        result = await session.exec(statement)
        return result.all()

    async def get_customer_bookings(self, customer_id: UUID, session: AsyncSession):
        statement = select(Booking).where(Booking.customer_id == customer_id).order_by(desc(Booking.created_at))
        result = await session.exec(statement)
        return result.all()

    async def get_provider_bookings(self, current_user, session: AsyncSession):
        result = await session.exec(select(Provider).where(Provider.user_id == current_user.uid))
        provider = result.first()
        if not provider:
            raise ValueError("Provider profile not found")

        statement = select(Booking).where(
            Booking.service_id.in_(
                select(Service.uid).where(Service.provider_id == provider.uid)
            )
        ).order_by(desc(Booking.created_at))
        result = await session.exec(statement)
        return result.all()

    async def create_booking(self, data: BookingCreate, current_user, session: AsyncSession):
        service = await session.get(Service, data.service_id)
        if not service:
            raise ValueError("Service not found")

        result = await session.exec(select(Provider).where(Provider.user_id == current_user.uid))
        provider = result.first()
        if provider and provider.uid == service.provider_id:
            raise PermissionError("You cannot book your own service")

        booking_date = data.booking_date
        if booking_date.tzinfo is not None:
            booking_date = booking_date.astimezone(timezone.utc).replace(tzinfo=None)

        booking = Booking(
            **data.model_dump(exclude={"booking_date"}),
            booking_date=booking_date,
            customer_id=current_user.uid,
            status=BookingStatus.PENDING,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add(booking)
        await session.commit()
        await session.refresh(booking)
        return booking

    async def update_booking_status(self, booking_id: UUID, data: BookingStatusUpdate, current_user, session: AsyncSession):
        booking = await self.get_booking_by_id(booking_id, session)
        if not booking:
            raise ValueError("Booking not found")

        allowed = VALID_TRANSITIONS.get(booking.status, [])
        if data.status not in allowed:
            raise ValueError(f"Cannot move booking from {booking.status} to {data.status}")

        result = await session.exec(select(Provider).where(Provider.user_id == current_user.uid))
        provider = result.first()

        if current_user.role != UserRole.ADMIN and (not provider or provider.uid != booking.service.provider_id):
            raise PermissionError("You are not authorised to update this booking")

        booking.status = data.status
        await session.commit()
        await session.refresh(booking)
        return booking

    async def cancel_booking(self, booking_id: UUID, data: BookingCancel, current_user, session: AsyncSession):
        booking = await self.get_booking_by_id(booking_id, session)
        if not booking:
            raise ValueError("Booking not found")

        is_provider = booking.service.provider.user_id == current_user.uid
        is_customer = booking.customer_id == current_user.uid
        is_admin = current_user.role == UserRole.ADMIN

        # only parties involved or admin can cancel
        if not is_provider and not is_customer and not is_admin:
            raise PermissionError("You are not authorised to cancel this booking")

        if is_customer:
            # customer can only cancel PENDING bookings
            if booking.status != BookingStatus.PENDING:
                raise ValueError("You can only cancel a pending booking")

        elif is_provider:
            # provider can cancel PENDING or ACCEPTED
            if booking.status not in [BookingStatus.PENDING, BookingStatus.ACCEPTED]:
                raise ValueError(f"Cannot cancel a booking that is already {booking.status}")

            # auto refund if provider cancels ACCEPTED booking
            if booking.status == BookingStatus.ACCEPTED:
                payment_service = PaymentService()
                payment = await payment_service.get_payment_by_booking_id(booking.uid, session)
                if payment:
                    await payment_service.refund_to_customer(booking.uid, session)

        booking.status = BookingStatus.CANCELLED
        booking.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
        booking.deleted_by = current_user.uid
        booking.delete_reason = data.delete_reason

        # notify customer
        await notification_service.create_notification(
            user_uid=booking.customer_id,
            message="Your booking has been cancelled.",
            notification_type=NotificationType.BOOKING_CANCELLED,
            session=session
        )
        send_booking_cancelled_email.delay(
            recipient_email=booking.customer.email,
            service_name=booking.service.name
        )

        await session.commit()
        await session.refresh(booking)
        return booking
