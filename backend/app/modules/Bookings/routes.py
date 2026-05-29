# modules/Booking/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.core.models import UserRole, BookingStatus, NotificationType, User
from app.modules.Bookings.service import BookingService
from app.modules.Bookings.schemes import BookingCreate, BookingStatusUpdate, BookingCancel, BookingResponse
from app.modules.Notifications.service import NotificationService
from app.celery_task import (
    send_booking_created_email,
    send_booking_accepted_email,
    send_booking_completed_email,
    send_booking_cancelled_email,
)

booking_router = APIRouter()
booking_service = BookingService()
notification_service = NotificationService()


# Admin only — see all bookings
@booking_router.get("/", response_model=list[BookingResponse])
async def get_all_bookings(
    session: AsyncSession = Depends(get_db),
    _=Depends(RoleChecker([UserRole.ADMIN]))
):
    return await booking_service.get_all_bookings(session)


# Customer — see their own bookings
@booking_router.get("/my-bookings", response_model=list[BookingResponse])
async def get_my_bookings(
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await booking_service.get_customer_bookings(current_user.uid, session)


# Provider — see bookings on their services
@booking_router.get("/provider-bookings", response_model=list[BookingResponse])
async def get_provider_bookings(
    session: AsyncSession = Depends(get_db),
    current_user=Depends(RoleChecker([UserRole.PROVIDER]))
):
    try:
        return await booking_service.get_provider_bookings(current_user, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Single booking — owner or admin
@booking_router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    booking = await booking_service.get_booking_by_id(booking_id, session)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if current_user.role != UserRole.ADMIN and current_user.uid != booking.customer_id:
        raise HTTPException(status_code=403, detail="Not authorised to view this booking")
    return booking


# Consumer only — create a booking
@booking_router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(RoleChecker([UserRole.CONSUMER]))
):
    try:
        booking = await booking_service.create_booking(data, current_user, session)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if booking.created_at is None:
        booking.created_at = booking.booking_date

    provider_user = await session.get(User, booking.service.provider.user_id)
    if provider_user:
        await notification_service.create_notification(
            provider_user.uid,
            f"New booking request for {booking.service.name}",
            NotificationType.BOOKING_CREATED,
            session
        )
        send_booking_created_email.delay(
            provider_user.email,
            booking.service.name,
            booking.booking_date.strftime("%Y-%m-%d %H:%M")
        )

    return booking


# Provider or admin — update booking status
@booking_router.patch("/{booking_id}/status", response_model=BookingResponse)
async def update_booking_status(
    booking_id: UUID,
    data: BookingStatusUpdate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        booking = await booking_service.update_booking_status(booking_id, data, current_user, session)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if data.status == BookingStatus.ACCEPTED:
        customer_user = await session.get(User, booking.customer_id)
        if customer_user:
            await notification_service.create_notification(
                customer_user.uid,
                f"Your booking for {booking.service.name} has been accepted",
                NotificationType.BOOKING_ACCEPTED,
                session
            )
            send_booking_accepted_email.delay(
                customer_user.email,
                booking.service.name,
                booking.booking_date.strftime("%Y-%m-%d %H:%M")
            )

    elif data.status == BookingStatus.COMPLETED:
        customer_user = await session.get(User, booking.customer_id)
        provider_user = await session.get(User, booking.service.provider.user_id)
        if customer_user:
            await notification_service.create_notification(
                customer_user.uid,
                f"Your booking for {booking.service.name} has been completed",
                NotificationType.BOOKING_COMPLETED,
                session
            )
            send_booking_completed_email.delay(customer_user.email, booking.service.name, False)
        if provider_user:
            await notification_service.create_notification(
                provider_user.uid,
                f"You have completed the service: {booking.service.name}",
                NotificationType.BOOKING_COMPLETED,
                session
            )
            send_booking_completed_email.delay(provider_user.email, booking.service.name, True)

    elif data.status == BookingStatus.CANCELLED:
        customer_user = await session.get(User, booking.customer_id)
        if customer_user:
            await notification_service.create_notification(
                customer_user.uid,
                f"Your booking for {booking.service.name} has been cancelled",
                NotificationType.BOOKING_CANCELLED,
                session
            )
            send_booking_cancelled_email.delay(customer_user.email, booking.service.name)

    return booking


# Customer or admin — cancel a booking
@booking_router.patch("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: UUID,
    data: BookingCancel,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        booking = await booking_service.cancel_booking(booking_id, data, current_user, session)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    provider_user = await session.get(User, booking.service.provider.user_id)
    if provider_user:
        await notification_service.create_notification(
            provider_user.uid,
            f"A booking for {booking.service.name} has been cancelled by the customer",
            NotificationType.BOOKING_CANCELLED,
            session
        )
        send_booking_cancelled_email.delay(provider_user.email, booking.service.name)

    return booking
