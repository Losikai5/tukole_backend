from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from .service import PaymentService
from .schema import PaymentCreate, PaymentResponse


payment_router = APIRouter()

payment_service = PaymentService()


@payment_router.post("/", response_model=PaymentResponse)
async def create_payment(payment_data: PaymentCreate,session: AsyncSession = Depends(get_db)):

    return await payment_service.create_payment(payment_data,session)


@payment_router.patch("/{payment_id}/escrow")
async def mark_payment_escrow(payment_id,session: AsyncSession = Depends(get_db)):

    return await payment_service.mark_payment_escrow(payment_id,session)


@payment_router.patch("/{payment_id}/release")
async def release_payment(payment_id,session: AsyncSession = Depends(get_db)):

    return await payment_service.release_payment(payment_id,session)

@payment_router.patch("/{payment_id}/refund")
async def refund_payment(payment_id,session: AsyncSession = Depends(get_db)):

    return await payment_service.refund_payment(payment_id,session)


@payment_router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id,session: AsyncSession = Depends(get_db)):

    return await payment_service.get_payment(payment_id,session)