from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.models import Booking, Dispute, Payment, Provider, Review, Service, User


class AdminService:
    async def _get_user_or_404(self, user_id: UUID, session: AsyncSession):
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    async def _get_dispute_or_404(self, dispute_id: UUID, session: AsyncSession):
        dispute = await session.get(Dispute, dispute_id)
        if not dispute:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dispute not found",
            )
        return dispute

    async def _get_provider_or_404(self, provider_id: UUID, session: AsyncSession):
        provider = await session.get(Provider, provider_id)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found",
            )
        return provider

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

    async def list_disputes(self, session: AsyncSession):
        statement = select(Dispute).order_by(Dispute.created_at.desc())
        result = await session.exec(statement)
        return result.all()

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

    async def list_providers(self, session: AsyncSession):
        statement = select(Provider).order_by(Provider.created_at.desc())
        result = await session.exec(statement)
        return result.all()

    async def list_provider_services(self, provider_id: UUID, session: AsyncSession):
        await self._get_provider_or_404(provider_id, session)

        statement = select(Service).where(Service.provider_id == provider_id).order_by(Service.created_at.desc())
        result = await session.exec(statement)
        return result.all()

    async def delete_user(self, user_id: UUID, session: AsyncSession):
        user = await self._get_user_or_404(user_id, session)

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

    async def resolve_dispute(
        self,
        dispute_id: UUID,
        status_value: str,
        admin_response: str | None,
        session: AsyncSession,
    ):
        dispute = await self._get_dispute_or_404(dispute_id, session)

        dispute.status = status_value
        dispute.admin_response = admin_response

        if status_value in {"resolved", "rejected"}:
            dispute.resolved_at = datetime.utcnow()
        else:
            dispute.resolved_at = None

        await session.commit()
        await session.refresh(dispute)

        return dispute
