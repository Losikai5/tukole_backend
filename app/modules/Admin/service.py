# modules/Admin/service.py
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.models import (
    Booking, Dispute, DisputeStatus, Notification, Payment, Provider,
    Review, Service, User, NotificationType
)
from app.modules.Notifications.service import NotificationService
from app.modules.Payments.service import PaymentService
from app.celery_task import send_dispute_resolved_email, send_payment_released_email, send_payment_refunded_email

notification_service = NotificationService()
payment_service = PaymentService()


class AdminService:

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _get_user_or_404(self, user_id: UUID, session: AsyncSession):
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    async def _get_dispute_or_404(self, dispute_id: UUID, session: AsyncSession):
        dispute = await session.get(Dispute, dispute_id)
        if not dispute:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found")
        return dispute

    async def _get_provider_or_404(self, provider_id: UUID, session: AsyncSession):
        provider = await session.get(Provider, provider_id)
        if not provider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
        return provider

    # ── Dashboard ─────────────────────────────────────────────────────────────

    async def get_dashboard_metrics(self, session: AsyncSession):
        total_users_result = await session.exec(select(func.count(User.uid)))
        total_providers_result = await session.exec(select(func.count(Provider.uid)))
        total_services_result = await session.exec(select(func.count(Service.uid)))
        total_bookings_result = await session.exec(
            select(func.count(Booking.uid)).where(Booking.deleted_at == None)
        )
        open_disputes_result = await session.exec(
            select(func.count(Dispute.uid)).where(Dispute.status == "open")
        )
        pending_payments_result = await session.exec(
            select(func.count(Payment.uid)).where(Payment.status == "pending")
        )
        released_revenue_result = await session.exec(
            select(func.sum(Payment.amount)).where(Payment.status == "released")
        )
        released_revenue = released_revenue_result.one() or Decimal("0")

        return {
            "total_users": int(total_users_result.one() or 0),
            "total_providers": int(total_providers_result.one() or 0),
            "total_services": int(total_services_result.one() or 0),
            "total_bookings": int(total_bookings_result.one() or 0),
            "open_disputes": int(open_disputes_result.one() or 0),
            "pending_payments": int(pending_payments_result.one() or 0),
            "released_revenue": float(released_revenue),
        }

    # ── Users ─────────────────────────────────────────────────────────────────

    async def list_users(self, session: AsyncSession):
        statement = select(User).order_by(User.created_at.desc())
        result = await session.exec(statement)
        return result.all()

    async def update_user_status(self, user_id: UUID, is_active: bool, session: AsyncSession):
        user = await self._get_user_or_404(user_id, session)
        user.is_active = is_active
        await session.commit()
        await session.refresh(user)
        return user

    async def update_user_role(self, user_id: UUID, role: str, session: AsyncSession):
        user = await self._get_user_or_404(user_id, session)
        user.role = role
        await session.commit()
        await session.refresh(user)
        return user

    async def delete_user(self, user_id: UUID, session: AsyncSession):
        user = await self._get_user_or_404(user_id, session)
        notifications = await session.exec(select(Notification).where(Notification.user_uid == user_id))
        for notification in notifications.all():
            await session.delete(notification)

        try:
            await session.delete(user)
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete user because related records exist",
            ) from exc
        return {"detail": "User deleted successfully"}

    # ── Providers ─────────────────────────────────────────────────────────────

    async def list_providers(self, session: AsyncSession):
        statement = select(Provider).order_by(Provider.created_at.desc())
        result = await session.exec(statement)
        return result.all()

    async def list_provider_services(self, provider_id: UUID, session: AsyncSession):
        await self._get_provider_or_404(provider_id, session)
        statement = (
            select(Service)
            .where(Service.provider_id == provider_id)
            .order_by(Service.created_at.desc())
        )
        result = await session.exec(statement)
        return result.all()

    async def delete_provider(self, provider_id: UUID, session: AsyncSession):
        provider = await self._get_provider_or_404(provider_id, session)
        statement = select(Service).where(Service.provider_id == provider_id)
        result = await session.exec(statement)
        services = result.all()
        try:
            for service in services:
                await session.delete(service)
            await session.delete(provider)
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete provider because related records exist",
            ) from exc
        return {"detail": "Provider deleted successfully"}

    # ── Disputes ──────────────────────────────────────────────────────────────

    async def list_disputes(self, session: AsyncSession):
        statement = select(Dispute).order_by(Dispute.created_at.desc())
        result = await session.exec(statement)
        return result.all()

    async def resolve_dispute(
        self,
        dispute_id: UUID,
        status_value: str,
        admin_response: str,
        resolution: str,  # "consumer" | "provider"
        current_user: User,
        session: AsyncSession,
    ):
        dispute = await self._get_dispute_or_404(dispute_id, session)

        # prevent updating an already resolved dispute
        if dispute.status == DisputeStatus.RESOLVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update an already resolved dispute"
            )

        dispute.status = status_value
        dispute.admin_response = admin_response
        dispute.resolution = resolution

        if status_value in {"resolved", "rejected"}:
            dispute.resolved_at = datetime.now(timezone.utc)
        else:
            dispute.resolved_at = None

        # get the booking linked to this dispute
        booking = await session.get(Booking, dispute.booking_id)

        # ── Under review — notify both parties ───────────────────────────────
        if status_value == DisputeStatus.UNDER_REVIEW:
            await notification_service.create_notification(
                user_uid=booking.customer_id,
                message="Your dispute is now under review. The admin will contact both parties.",
                notification_type=NotificationType.DISPUTE_UNDER_REVIEW,
                session=session
            )
            await notification_service.create_notification(
                user_uid=booking.service.provider.user_id,
                message="The dispute on your booking is now under investigation.",
                notification_type=NotificationType.DISPUTE_UNDER_REVIEW,
                session=session
            )

        # ── Resolved — trigger payment and notify both parties ────────────────
        elif status_value == DisputeStatus.RESOLVED:

            if resolution == "consumer":
                # refund the customer
                await payment_service.refund_to_customer(booking.uid, session)

                # notify customer — they won
                await notification_service.create_notification(
                    user_uid=booking.customer_id,
                    message="The dispute has been resolved in your favour. Your payment has been refunded.",
                    notification_type=NotificationType.PAYMENT_REFUNDED,
                    session=session
                )
                send_dispute_resolved_email.delay(
                    recipient_email=booking.customer.email,
                    admin_response=admin_response,
                    won=True
                )

                # notify provider — they lost
                await notification_service.create_notification(
                    user_uid=booking.service.provider.user_id,
                    message=f"Due to the evidence provided, the dispute was resolved in favour of the customer. {admin_response}",
                    notification_type=NotificationType.DISPUTE_RESOLVED,
                    session=session
                )
                send_dispute_resolved_email.delay(
                    recipient_email=booking.service.provider.user.email,
                    admin_response=admin_response,
                    won=False
                )

            elif resolution == "provider":
                # release payment to provider (thread admin user through)
                await payment_service.release_to_provider(booking.uid, current_user, session)

                # notify provider — they won
                await notification_service.create_notification(
                    user_uid=booking.service.provider.user_id,
                    message="The dispute has been resolved in your favour. Payment has been released to you.",
                    notification_type=NotificationType.PAYMENT_RELEASED,
                    session=session
                )
                send_dispute_resolved_email.delay(
                    recipient_email=booking.service.provider.user.email,
                    admin_response=admin_response,
                    won=True
                )

                # notify customer — they lost
                await notification_service.create_notification(
                    user_uid=booking.customer_id,
                    message=f"Due to the evidence provided, the dispute was resolved in favour of the provider. {admin_response}",
                    notification_type=NotificationType.DISPUTE_RESOLVED,
                    session=session
                )
                send_dispute_resolved_email.delay(
                    recipient_email=booking.customer.email,
                    admin_response=admin_response,
                    won=False
                )

        await session.commit()
        await session.refresh(dispute)
        return dispute

    # ── Audit trails ──────────────────────────────────────────────────────────

    async def list_deleted_bookings(self, session: AsyncSession):
        statement = (
            select(Booking)
            .where(Booking.deleted_at != None)
            .order_by(Booking.deleted_at.desc())
        )
        result = await session.exec(statement)
        return result.all()

    async def list_deleted_reviews(self, session: AsyncSession):
        statement = (
            select(Review)
            .where(Review.deleted_at != None)
            .order_by(Review.deleted_at.desc())
        )
        result = await session.exec(statement)
        return result.all()