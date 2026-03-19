from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from uuid import UUID
from datetime import timezone

from app.core.models import Booking, Provider, Service
from .schemes import BookingCreate


class BookingService:
    VALID_BOOKING_STATUSES = {"pending", "accepted", "completed", "cancelled"}


    async def _get_booking_or_404(self, booking_id: str, session: AsyncSession):

        booking = await session.get(Booking, booking_id)

        if not booking:
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

        return booking


    async def get_user_bookings(self,user_id:str,session: AsyncSession):

        statement = select(Booking).where(Booking.customer_id == user_id)

        result = await session.exec(statement)

        return result.all()


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

        booking.status = status_value

        await session.commit()
        await session.refresh(booking)

        return booking
    
    async def delete_booking(self,booking_id:str,current_user,session: AsyncSession):

        booking = await self._get_booking_or_404(booking_id, session)

        if current_user.role != "admin" and booking.customer_id != current_user.uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own bookings"
            )

        await session.delete(booking)
        await session.commit()

        return {"detail": "Booking deleted successfully"}
