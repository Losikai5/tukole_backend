# modules/Payment/service.py
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from fastapi import HTTPException, status
from app.core.models import Payment, Booking, PaymentStatus, BookingStatus, UserRole, NotificationType
from app.modules.Payments.schema import PaymentCreate
from app.modules.Notifications.service import NotificationService
from app.celery_task import (
    send_payment_in_escrow_email,
    send_payment_released_email,
    send_payment_refunded_email
)

notification_service = NotificationService()


class PaymentService:

    def _ensure_status_transition(self, payment, new_status: str):
        allowed = {
            PaymentStatus.PENDING.value: [],
            PaymentStatus.ESCROW.value: [PaymentStatus.RELEASED.value, PaymentStatus.REFUNDED.value],
            PaymentStatus.RELEASED.value: [],
            PaymentStatus.REFUNDED.value: [],
        }
        current_status = payment.status.value if hasattr(payment.status, "value") else payment.status
        target_status = new_status.value if hasattr(new_status, "value") else new_status
        if target_status not in allowed.get(current_status, []):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot move payment from {current_status} to {target_status}",
            )

    async def _get_payment_or_404(self, payment_id: UUID, session: AsyncSession):
        payment = await self.get_payment_by_id(payment_id, session)
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        return payment

    async def _get_booking_with_service(self, booking_id: UUID, session: AsyncSession):
        booking = await session.get(Booking, booking_id)
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
        return booking, getattr(booking, "service", None)

    async def release_payment(self, payment_id: UUID, session: AsyncSession):
        payment = await self._get_payment_or_404(payment_id, session)
        booking, _service = await self._get_booking_with_service(payment.booking_id, session)

        if booking.status != BookingStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Payment can only be released for completed bookings",
            )

        self._ensure_status_transition(payment, PaymentStatus.RELEASED)
        payment.status = PaymentStatus.RELEASED
        await session.commit()
        await session.refresh(payment)
        return payment

    async def refund_payment(self, payment_id: UUID, session: AsyncSession):
        payment = await self._get_payment_or_404(payment_id, session)
        self._ensure_status_transition(payment, PaymentStatus.REFUNDED)
        payment.status = PaymentStatus.REFUNDED
        await session.commit()
        await session.refresh(payment)
        return payment

    async def get_payment_by_booking_id(self, booking_id: UUID, session: AsyncSession):
        statement = select(Payment).where(Payment.booking_id == booking_id)
        result = await session.exec(statement)
        return result.first()

    async def get_payment_by_id(self, payment_id: UUID, session: AsyncSession):
        statement = select(Payment).where(Payment.uid == payment_id)
        result = await session.exec(statement)
        return result.first()

    async def create_payment(self, data: PaymentCreate, current_user, session: AsyncSession):
        # validate booking exists
        booking = await session.get(Booking, data.booking_id)
        if not booking:
            raise ValueError("Booking not found")

        # only the customer of that booking can pay
        if booking.customer_id != current_user.uid:
            raise PermissionError("You can only pay for your own bookings")

        # booking must be accepted before payment
        if booking.status != BookingStatus.ACCEPTED:
            raise ValueError("Can only pay for an accepted booking")

        # prevent double payment
        existing = await self.get_payment_by_booking_id(data.booking_id, session)
        if existing:
            raise ValueError("Payment already exists for this booking")

        payment = Payment(
            **data.model_dump(),
            status=PaymentStatus.ESCROW
        )
        session.add(payment)
        await session.flush()

        # notify customer — money in escrow
        await notification_service.create_notification(
            user_uid=current_user.uid,
            message=f"Your payment of ${data.amount:.2f} is safely held in escrow.",
            notification_type=NotificationType.PAYMENT_IN_ESCROW,
            session=session
        )
        send_payment_in_escrow_email.delay(
            customer_email=current_user.email,
            amount=data.amount,
            service_name=booking.service.name
        )

        # notify provider — safe to start
        await notification_service.create_notification(
            user_uid=booking.service.provider.user_id,
            message=f"Payment of ${data.amount:.2f} is in escrow. You can start the service.",
            notification_type=NotificationType.PAYMENT_IN_ESCROW,
            session=session
        )
        send_payment_in_escrow_email.delay(
            customer_email=booking.service.provider.user.email,
            amount=data.amount,
            service_name=booking.service.name
        )

        await session.commit()
        await session.refresh(payment)
        return payment

    async def release_to_provider(self, booking_id: UUID, current_user, session: AsyncSession):
        booking = await session.get(Booking, booking_id)
        if not booking:
            raise ValueError("Booking not found")

        # double lock — booking must be completed
        if booking.status != BookingStatus.COMPLETED:
            raise ValueError("Can only release payment for a completed booking")

        # only consumer or admin can release
        if current_user.role != UserRole.ADMIN and current_user.uid != booking.customer_id:
            raise PermissionError("Not authorised to release this payment")

        payment = await self.get_payment_by_booking_id(booking_id, session)
        if not payment:
            raise ValueError("Payment not found")

        if payment.status != PaymentStatus.ESCROW:
            raise ValueError(f"Payment is already {payment.status}")

        payment.status = PaymentStatus.RELEASED

        # notify provider
        await notification_service.create_notification(
            user_uid=booking.service.provider.user_id,
            message=f"Payment of ${payment.amount:.2f} has been released to you.",
            notification_type=NotificationType.PAYMENT_RELEASED,
            session=session
        )
        send_payment_released_email.delay(
            provider_email=booking.service.provider.user.email,
            amount=payment.amount
        )

        await session.commit()
        await session.refresh(payment)
        return payment

    async def refund_to_customer(self, booking_id: UUID, session: AsyncSession):
        booking = await session.get(Booking, booking_id)
        if not booking:
            raise ValueError("Booking not found")

        payment = await self.get_payment_by_booking_id(booking_id, session)
        if not payment:
            raise ValueError("Payment not found")

        if payment.status != PaymentStatus.ESCROW:
            raise ValueError(f"Cannot refund a payment that is {payment.status}")

        payment.status = PaymentStatus.REFUNDED

        # notify customer
        await notification_service.create_notification(
            user_uid=booking.customer_id,
            message=f"Your payment of ${payment.amount:.2f} has been refunded.",
            notification_type=NotificationType.PAYMENT_REFUNDED,
            session=session
        )
        send_payment_refunded_email.delay(
            customer_email=booking.customer.email,
            amount=payment.amount
        )

        await session.commit()
        await session.refresh(payment)
        return payment