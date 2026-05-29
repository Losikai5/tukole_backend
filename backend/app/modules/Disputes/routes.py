# modules/Dispute/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.core.models import UserRole, NotificationType, User, Booking, DisputeStatus
from app.modules.Disputes.service import DisputeService
from app.modules.Disputes.schemes import DisputeCreate, DisputeAdminUpdate, DisputeResponse
from app.modules.Notifications.service import NotificationService
from app.celery_task import (
    send_dispute_raised_email,
    send_dispute_under_review_email,
    send_dispute_resolved_email,
)


dispute_router = APIRouter()
dispute_service = DisputeService()
notification_service = NotificationService()


# Admin only — see all disputes
@dispute_router.get("/", response_model=list[DisputeResponse])
async def get_all_disputes(
    session: AsyncSession = Depends(get_db),
    _=Depends(RoleChecker([UserRole.ADMIN]))
):
    return await dispute_service.get_all_disputes(session)


@dispute_router.get("/my-disputes", response_model=list[DisputeResponse])
async def my_disputes(
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await dispute_service.get_user_disputes(current_user, session)


# Admin only — get single dispute
@dispute_router.get("/{dispute_id}", response_model=DisputeResponse)
async def get_dispute(
    dispute_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        dispute = await dispute_service.get_dispute_by_id(dispute_id, current_user, session)
    except HTTPException:
        raise
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return dispute


# Consumer or provider — raise a dispute
@dispute_router.post("/", response_model=DisputeResponse, status_code=status.HTTP_201_CREATED)
async def create_dispute(
    data: DisputeCreate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        dispute = await dispute_service.create_dispute(data, current_user, session)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    booking = await session.get(Booking, dispute.booking_id)
    if booking:
        if current_user.uid == booking.customer_id:
            other_party = await session.get(User, booking.service.provider.user_id)
        else:
            other_party = await session.get(User, booking.customer_id)
        if other_party:
            await notification_service.create_notification(
                other_party.uid,
                f"A dispute has been raised on booking {dispute.booking_id}",
                NotificationType.DISPUTE_RAISED,
                session
            )
            send_dispute_raised_email.delay(other_party.email, str(dispute.booking_id), False)

    return dispute


# Admin only — update dispute status and resolution
@dispute_router.patch("/{dispute_id}", response_model=DisputeResponse)
async def update_dispute(
    dispute_id: UUID,
    data: DisputeAdminUpdate,
    session: AsyncSession = Depends(get_db),
    _=Depends(RoleChecker([UserRole.ADMIN])),
    current_user=Depends(get_current_user)
):
    try:
        dispute = await dispute_service.update_dispute(dispute_id, data, session, current_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    raiser = await session.get(User, dispute.raised_by)
    if raiser:
        if dispute.status == DisputeStatus.UNDER_REVIEW:
            await notification_service.create_notification(
                raiser.uid,
                "Your dispute is now under review",
                NotificationType.DISPUTE_UNDER_REVIEW,
                session
            )
            send_dispute_under_review_email.delay(raiser.email, str(dispute.booking_id))

        elif dispute.status in (DisputeStatus.RESOLVED, DisputeStatus.REJECTED):
            won = False
            if dispute.status == DisputeStatus.RESOLVED:
                booking = await session.get(Booking, dispute.booking_id)
                if booking:
                    raiser_is_customer = raiser.uid == booking.customer_id
                    won = (raiser_is_customer and dispute.resolution == "consumer") or \
                          (not raiser_is_customer and dispute.resolution == "provider")
            await notification_service.create_notification(
                raiser.uid,
                "Your dispute has been resolved",
                NotificationType.DISPUTE_RESOLVED,
                session
            )
            send_dispute_resolved_email.delay(raiser.email, dispute.admin_response or "", won)

    return dispute
