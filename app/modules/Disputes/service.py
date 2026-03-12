from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime

from app.core.models import Dispute, Booking
from .schemes import DisputeCreate, UpdateDispute


class DisputeService:

    async def create_dispute(
        self,
        dispute_data: DisputeCreate,
        user_id: UUID,
        session: AsyncSession
    ):
        """Customer raises a dispute"""

        booking = await session.get(Booking, dispute_data.booking_id)

        if not booking:
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

        return dispute


    async def get_all_disputes(self, session: AsyncSession):
        """Admin fetches all disputes"""

        statement = select(Dispute)

        result = await session.exec(statement)

        return result.all()


    async def get_dispute_by_id(self, dispute_id: UUID, session: AsyncSession):
        """Get a single dispute"""

        dispute = await session.get(Dispute, dispute_id)

        if not dispute:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dispute not found"
            )

        return dispute


    async def update_dispute(
        self,
        dispute_id: UUID,
        dispute_data: UpdateDispute,
        session: AsyncSession
    ):
        """Admin updates dispute"""

        dispute = await self.get_dispute_by_id(dispute_id, session)

        update_data = dispute_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(dispute, key, value)

        # If resolved, set resolved_at
        if dispute_data.status == "resolved":
            dispute.resolved_at = datetime.utcnow()

        await session.commit()
        await session.refresh(dispute)

        return dispute