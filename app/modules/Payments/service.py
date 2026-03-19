from decimal import Decimal, ROUND_HALF_UP

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from uuid import UUID

from app.core.models import Booking, Payment, Provider, Service
from .schema import PaymentCreate


class PaymentService:
    @staticmethod
    def _normalize_amount(amount: float) -> Decimal:
        return Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


    async def _get_payment_or_404(self, payment_id: UUID, session: AsyncSession):

        payment = await session.get(Payment, payment_id)

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        return payment


    async def _get_booking_with_service(self, booking_id: UUID, session: AsyncSession):

        booking = await session.get(Booking, booking_id)

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )

        service = await session.get(Service, booking.service_id)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )

        return booking, service


    async def _ensure_payment_access(self, payment: Payment, current_user, session: AsyncSession):

        if current_user.role == "admin":
            return

        booking, service = await self._get_booking_with_service(payment.booking_id, session)

        if booking.customer_id == current_user.uid:
            return

        provider = await session.get(Provider, service.provider_id)
        if provider and provider.user_id == current_user.uid:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this payment"
        )


    async def create_payment(self,payment_data: PaymentCreate,current_user,session: AsyncSession):

        statement = select(Payment).where(Payment.booking_id == payment_data.booking_id)
        result = await session.exec(statement)
        existing_payment = result.first()
        if existing_payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment for this booking already exists"
            )

        booking, service = await self._get_booking_with_service(payment_data.booking_id, session)

        if current_user.role != "admin" and booking.customer_id != current_user.uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only pay for your own bookings"
            )

        requested_amount = self._normalize_amount(payment_data.amount)
        expected_amount = self._normalize_amount(float(service.price))
        if requested_amount != expected_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment amount must match the service price of {expected_amount}"
            )

        payment = Payment(
            booking_id=payment_data.booking_id,
            amount=float(expected_amount),
            status="pending"
        )

        session.add(payment)

        await session.commit()
        await session.refresh(payment)

        return payment


    async def make_payment_escrow(self,payment_id: UUID,session: AsyncSession):

        payment = await self._get_payment_or_404(payment_id, session)

        payment.status = "escrow"

        await session.commit()
        await session.refresh(payment)

        return payment


    async def release_payment(self,payment_id: UUID,session: AsyncSession):

        payment = await self._get_payment_or_404(payment_id, session)

        payment.status = "released"

        await session.commit()
        await session.refresh(payment)

        return payment
    async def refund_payment(self,payment_id: UUID,session: AsyncSession):

        payment = await self._get_payment_or_404(payment_id, session)

        payment.status = "refunded"

        await session.commit()
        await session.refresh(payment)

        return payment
    
    async def get_payment_by_id(self,payment_id: UUID,current_user,session: AsyncSession):

        payment = await self._get_payment_or_404(payment_id, session)
        await self._ensure_payment_access(payment, current_user, session)

        return payment
