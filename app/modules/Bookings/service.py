from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from uuid import UUID

from app.core.models import Booking, Service
from .schemes import BookingCreate


class BookingService:


    async def create_booking(self,booking_data: BookingCreate,user_id: UUID,session: AsyncSession):

        # Check if service exists
        service = await session.get(Service, booking_data.service_id)

        if not service:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Service not found")

        booking = Booking(service_id=booking_data.service_id,customer_id=user_id,booking_date=booking_data.booking_date)

        session.add(booking)

        await session.commit()
        await session.refresh(booking)

        return booking


    async def get_user_bookings(self,user_id:str,session: AsyncSession):

        statement = select(Booking).where(Booking.customer_id == user_id)

        result = await session.exec(statement)

        return result.all()


    async def update_booking_status(self,booking_id:str,status_value: str,session: AsyncSession):

        booking = await session.get(Booking, booking_id)

        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Booking not found")

        booking.status = status_value

        await session.commit()
        await session.refresh(booking)

        return booking
    
    async def delete_booking(self,booking_id:str,session: AsyncSession):

        booking = await session.get(Booking, booking_id)

        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Booking not found")

        await session.delete(booking)
        await session.commit()

        return {"detail": "Booking deleted successfully"}