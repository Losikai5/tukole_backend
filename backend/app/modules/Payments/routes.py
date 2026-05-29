from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.core.models import UserRole
from app.modules.Payments.service import PaymentService
from app.modules.Payments.schema import PaymentCreate, PaymentResponse

payment_router = APIRouter()
payment_service = PaymentService()


# Consumer — make a payment
@payment_router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    data: PaymentCreate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(RoleChecker([UserRole.CONSUMER]))
):
    try:
        return await payment_service.create_payment(data, current_user, session)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Consumer or admin — release payment to provider
@payment_router.patch("/{booking_id}/release", response_model=PaymentResponse)
async def release_payment(
    booking_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        return await payment_service.release_to_provider(booking_id, current_user, session)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Admin only — refund payment to customer
@payment_router.patch("/{booking_id}/refund", response_model=PaymentResponse)
async def refund_payment(
    booking_id: UUID,
    session: AsyncSession = Depends(get_db),
    _=Depends(RoleChecker([UserRole.ADMIN]))
):
    try:
        return await payment_service.refund_to_customer(booking_id, session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Admin only — get payment by booking
@payment_router.get("/{booking_id}", response_model=PaymentResponse)
async def get_payment(
    booking_id: UUID,
    session: AsyncSession = Depends(get_db),
    _=Depends(RoleChecker([UserRole.ADMIN]))
):
    payment = await payment_service.get_payment_by_booking_id(booking_id, session)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment