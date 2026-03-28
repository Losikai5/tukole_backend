from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker

from .service import BookingService
from .schemes import BookingCreate, BookingResponse


booking_router = APIRouter()

booking_service = BookingService()


@booking_router.post("/", response_model=BookingResponse)
async def create_booking(booking_data: BookingCreate,session: AsyncSession = Depends(get_db),current_user = Depends(get_current_user)):

    booking = await booking_service.create_booking(booking_data,current_user.uid,session)

    return booking


@booking_router.get("/me")
async def get_my_bookings(session: AsyncSession = Depends(get_db),current_user = Depends(get_current_user)):

    return await booking_service.get_user_bookings(current_user.uid,session)


@booking_router.get("/provider/me", response_model=list[BookingResponse])
async def get_my_provider_bookings(
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    _: bool = Depends(RoleChecker(["provider"]))
):

    return await booking_service.get_provider_bookings(current_user.uid, session)

@booking_router.put("/{booking_id}/status")
async def update_booking_status(
    booking_id: str,
    status_value: str,
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    _: bool = Depends(RoleChecker(["provider", "admin"]))
):

    return await booking_service.update_booking_status(booking_id,status_value,current_user,session)
@booking_router.delete("/{booking_id}")
async def delete_booking(
    booking_id: str,
    reason: str | None = None,
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):

    await booking_service.delete_booking(booking_id,current_user,session,reason)

    return {"detail": "Booking deleted successfully"}


@booking_router.post("/expire-pending")
async def expire_pending_bookings(
    timeout_minutes: int = 60,
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    _: bool = Depends(RoleChecker(["admin"]))
):

    return await booking_service.expire_pending_bookings(timeout_minutes, session)
