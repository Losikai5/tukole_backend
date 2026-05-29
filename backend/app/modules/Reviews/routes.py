# modules/Review/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.core.models import UserRole, NotificationType, User, Booking
from app.modules.Reviews.services import ReviewService
from app.modules.Reviews.schemes import ReviewCreate, ReviewUpdate, ReviewResponse
from app.modules.Notifications.service import NotificationService
from app.celery_task import send_review_made_email

review_router = APIRouter()
review_service = ReviewService()
notification_service = NotificationService()


# Public — see all reviews
@review_router.get("/", response_model=list[ReviewResponse])
async def get_all_reviews(session: AsyncSession = Depends(get_db)):
    return await review_service.get_all_reviews(session)


# Public — see reviews for a specific provider
@review_router.get("/provider/{provider_id}", response_model=list[ReviewResponse])
async def get_provider_reviews(
    provider_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    return await review_service.get_provider_reviews(provider_id, session)


# Public — get single review
@review_router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    review = await review_service.get_review_by_id(review_id, session)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


# Consumer only — create a review
@review_router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    data: ReviewCreate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(RoleChecker([UserRole.CONSUMER]))
):
    try:
        review = await review_service.create_review(data, current_user, session)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    booking = await session.get(Booking, review.booking_id)
    if booking:
        provider_user = await session.get(User, booking.service.provider.user_id)
        if provider_user:
            await notification_service.create_notification(
                provider_user.uid,
                f"You received a new {review.rating}/5 star review",
                NotificationType.REVIEW_MADE,
                session
            )
            send_review_made_email.delay(provider_user.email, review.rating, review.comment or "")

    return review


# Reviewer or admin — update a review
@review_router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: UUID,
    data: ReviewUpdate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        return await review_service.update_review(review_id, data, current_user, session)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Reviewer or admin — delete a review
@review_router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        await review_service.delete_review(review_id, current_user, session)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
