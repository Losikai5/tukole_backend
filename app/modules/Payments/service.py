from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from uuid import UUID

from app.core.models import Payment, Booking
from .schema import PaymentCreate


class PaymentService:


    async def create_payment(self,payment_data: PaymentCreate,session: AsyncSession):

        statement = select(Payment).where(Payment.booking_id == payment_data.booking_id)
        result = await session.exec(statement)
        existing_payment = result.first()
        if existing_payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment for this booking already exists"
            )

        # Ensure booking exists
        booking = await session.get(Booking, payment_data.booking_id)

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )

        payment = Payment(booking_id=payment_data.booking_id,amount=payment_data.amount,status="pending")

        session.add(payment)

        await session.commit()
        await session.refresh(payment)

        return payment


    async def make_payment_escrow(self,payment_id: UUID,session: AsyncSession):

        payment = await session.get(Payment, payment_id)

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        payment.status = "escrow"

        await session.commit()
        await session.refresh(payment)

        return payment


    async def release_payment(self,payment_id: UUID,session: AsyncSession):

        payment = await session.get(Payment, payment_id)

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        payment.status = "released"

        await session.commit()
        await session.refresh(payment)

        return payment
    async def refund_payment(self,payment_id: UUID,session: AsyncSession):

        payment = await session.get(Payment, payment_id)

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        payment.status = "refunded"

        await session.commit()
        await session.refresh(payment)

        return payment
    
    async def get_payment_by_id(self,payment_id: UUID,session: AsyncSession):

        payment = await session.get(Payment, payment_id)

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        return payment