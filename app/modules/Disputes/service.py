# modules/Dispute/service.py
from sqlmodel import select, desc
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.core.models import Dispute, Booking, BookingStatus, DisputeStatus, UserRole
from app.modules.Disputes.schemes import DisputeCreate, DisputeAdminUpdate


class DisputeService:

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
            return dispute

        booking = await session.get(Booking, dispute.booking_id)
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

        provider_user_id = await self._get_booking_provider_user_id(booking, session)
        is_owner = current_user.uid == dispute.raised_by
        is_provider = provider_user_id is not None and current_user.uid == provider_user_id
        is_admin = getattr(current_user, "role", None) == UserRole.ADMIN

        if not (is_owner or is_provider or is_admin):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorised to view this dispute")

        return dispute

    async def get_all_disputes(self, session: AsyncSession):
        statement = select(Dispute).order_by(desc(Dispute.created_at))
        result = await session.exec(statement)
        return result.all()

    async def get_booking_disputes(self, booking_id: UUID, session: AsyncSession):
        statement = select(Dispute).where(Dispute.booking_id == booking_id)
        result = await session.exec(statement)
        return result.all()

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
        return dispute

    async def update_dispute(self, dispute_id: UUID, data: DisputeAdminUpdate, session: AsyncSession):
        dispute = await self.get_dispute_by_id(dispute_id, session)
        if not dispute:
            raise ValueError("Dispute not found")

        if dispute.status == DisputeStatus.RESOLVED:
            raise ValueError("Cannot update an already resolved dispute")

        dispute.status = data.status
        dispute.admin_response = data.admin_response
        dispute.resolution = data.resolution

        if data.status == DisputeStatus.RESOLVED:
            dispute.resolved_at = datetime.now(timezone.utc)

        await session.commit()
        await session.refresh(dispute)
        return dispute
