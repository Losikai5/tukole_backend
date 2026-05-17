# modules/Dispute/service.py
from sqlmodel import select, desc
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload

from app.core.models import (
    Dispute,
    Booking,
    BookingStatus,
    DisputeStatus,
    UserRole,
    Payment,
    PaymentStatus,
    Notification,
    NotificationType,
    Service,
    Provider,
)
from app.modules.Disputes.schemes import DisputeCreate, DisputeAdminUpdate
from app.celery_task import send_payment_released_email, send_payment_refunded_email


class DisputeService:

    def _ensure_created_at(self, dispute):
        if dispute and dispute.created_at is None:
            dispute.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
        return dispute

    async def _get_booking_provider_user_id(self, booking: Booking, session: AsyncSession):
        if getattr(booking, "service", None) and getattr(booking.service, "provider", None):
            return booking.service.provider.user_id
        return None

    async def get_dispute_by_id(self, dispute_id: UUID, current_user=None, session: AsyncSession = None):
        if session is None:
            session = current_user
            current_user = None

        dispute = await session.get(Dispute, dispute_id)

        if not dispute or current_user is None:
            return self._ensure_created_at(dispute)

        booking = await session.get(Booking, dispute.booking_id)
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

        provider_user_id = await self._get_booking_provider_user_id(booking, session)
        is_owner = current_user.uid == dispute.raised_by
        is_provider = provider_user_id is not None and current_user.uid == provider_user_id
        is_admin = getattr(current_user, "role", None) == UserRole.ADMIN

        if not (is_owner or is_provider or is_admin):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorised to view this dispute")

        return self._ensure_created_at(dispute)

    async def get_all_disputes(self, session: AsyncSession):
        statement = select(Dispute).order_by(desc(Dispute.created_at))
        result = await session.exec(statement)
        return [self._ensure_created_at(dispute) for dispute in result.all()]

    async def get_booking_disputes(self, booking_id: UUID, session: AsyncSession):
        statement = select(Dispute).where(Dispute.booking_id == booking_id)
        result = await session.exec(statement)
        return [self._ensure_created_at(dispute) for dispute in result.all()]

    async def get_user_disputes(self, current_user, session: AsyncSession):
        # disputes where user is raiser OR is provider on the booking
        statement = (
            select(Dispute)
            .options(
                selectinload(Dispute.booking)
                .selectinload(Booking.service)
                .selectinload(Service.provider)
                .selectinload(Provider.user),
            )
            .where(
                (Dispute.raised_by == current_user.uid) |
                (Dispute.booking_id.in_(
                    select(Booking.uid).where(
                        Booking.service_id.in_(
                            select(Service.uid).where(Service.provider_id.in_(
                                select(Provider.uid).where(Provider.user_id == current_user.uid)
                            ))
                        )
                    )
                ))
            )
        )
        result = await session.exec(statement)
        return [self._ensure_created_at(d) for d in result.all()]

    async def create_dispute(self, data: DisputeCreate, current_user, session: AsyncSession):
        booking = await session.get(Booking, data.booking_id)
        if not booking:
            raise ValueError("Booking not found")

        if booking.status not in [BookingStatus.ACCEPTED, BookingStatus.COMPLETED]:
            raise ValueError("Can only raise a dispute on an accepted or completed booking")

        if current_user.uid != booking.customer_id and current_user.uid != booking.service.provider.user_id:
            raise PermissionError("You are not a party to this booking")

        existing = await session.exec(
            select(Dispute).where(Dispute.booking_id == data.booking_id)
        )
        if existing.first():
            raise ValueError("A dispute already exists for this booking")

        dispute = Dispute(
            **data.model_dump(),
            raised_by=current_user.uid,
            status=DisputeStatus.OPEN
        )
        session.add(dispute)
        await session.commit()
        await session.refresh(dispute)
        return self._ensure_created_at(dispute)

    VALID_TRANSITIONS = {
        DisputeStatus.OPEN: [DisputeStatus.UNDER_REVIEW, DisputeStatus.RESOLVED, DisputeStatus.REJECTED],
        DisputeStatus.UNDER_REVIEW: [DisputeStatus.RESOLVED, DisputeStatus.REJECTED],
        DisputeStatus.RESOLVED: [],
        DisputeStatus.REJECTED: [],
    }

    async def update_dispute(self, dispute_id: UUID, data: DisputeAdminUpdate, session: AsyncSession, current_user=None):
        dispute = await self.get_dispute_by_id(dispute_id, session)
        if not dispute:
            raise ValueError("Dispute not found")

        if dispute.status == DisputeStatus.RESOLVED:
            raise ValueError("Cannot update an already resolved dispute")

        # validate transitions
        allowed = self.VALID_TRANSITIONS.get(dispute.status, [])
        if data.status not in allowed:
            raise ValueError(f"Cannot move dispute from {dispute.status} to {data.status}")

        dispute.status = data.status
        dispute.admin_response = data.admin_response
        # store enum value string
        dispute.resolution = data.resolution.value if hasattr(data.resolution, 'value') else data.resolution

        if data.status == DisputeStatus.RESOLVED:
            # eager-load booking and related user/provider
            stmt = (
                select(Booking)
                .where(Booking.uid == dispute.booking_id)
                .options(
                    selectinload(Booking.service).selectinload(Service.provider).selectinload(Provider.user),
                    selectinload(Booking.customer),
                )
            )
            book_res = await session.exec(stmt)
            booking = book_res.first()

            # find payment
            pay_res = await session.exec(select(Payment).where(Payment.booking_id == dispute.booking_id))
            payment = pay_res.first()

            if payment and getattr(payment, 'status', None) == PaymentStatus.ESCROW:
                # consumer wins
                if data.resolution.value == "consumer":
                    payment.status = PaymentStatus.REFUNDED
                    # add notification for customer (no commit here)
                    n = Notification(
                        user_uid=booking.customer_id,
                        message=f"Your payment of ${payment.amount:.2f} has been refunded.",
                        notification_type=NotificationType.PAYMENT_REFUNDED,
                    )
                    session.add(n)
                    # enqueue email
                    customer_email = getattr(booking.customer, 'email', None)
                    if customer_email:
                        send_payment_refunded_email.delay(customer_email=customer_email, amount=payment.amount)

                # provider wins
                elif data.resolution.value == "provider":
                    payment.status = PaymentStatus.RELEASED
                    # add notification for provider
                    provider_user_id = None
                    provider_email = None
                    if getattr(booking, 'service', None) and getattr(booking.service, 'provider', None):
                        provider_user_id = booking.service.provider.user_id
                        provider_email = getattr(booking.service.provider.user, 'email', None)
                    if provider_user_id:
                        n = Notification(
                            user_uid=provider_user_id,
                            message=f"Payment of ${payment.amount:.2f} has been released to you.",
                            notification_type=NotificationType.PAYMENT_RELEASED,
                        )
                        session.add(n)
                    if provider_email:
                        send_payment_released_email.delay(provider_email=provider_email, amount=payment.amount)

            dispute.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)

        await session.commit()
        await session.refresh(dispute)
        return self._ensure_created_at(dispute)
