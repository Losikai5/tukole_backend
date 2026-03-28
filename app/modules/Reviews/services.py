import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc
from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime
from typing import Any, Optional

from .schemes import ReviewCreate, UpdateReview
from app.core.models import Review, Booking, Service, Provider
from app.modules.Notifications.service import NotificationService


class ReviewService:

    def __init__(self):
        self.notification_service = NotificationService()


    async def _safe_create_notification(
        self,
        user_id: UUID,
        title: str,
        message: str,
        session: AsyncSession,
        event_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        payload: Optional[dict[str, Any]] = None,
    ):
        try:
            await self.notification_service.create_notification(
                user_id,
                title,
                message,
                session,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                payload=payload,
            )
        except Exception:
            logging.exception("Failed to create review notification")


    async def create_review(self,review_data: ReviewCreate,user_id: UUID,session: AsyncSession):
        """Create a new review."""

        booking = await session.get(Booking, review_data.booking_id)

        if not booking or booking.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )

        # Ensure booking belongs to user
        if booking.customer_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User did not book this service"
            )

        # Ensure booking completed
        if booking.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot review an incomplete booking"
            )

        # Ensure review does not already exist
        statement = select(Review).where(
            Review.booking_id == review_data.booking_id,
            Review.deleted_at == None,
        )
        result = await session.exec(statement)

        existing_review = result.first()

        if existing_review:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Review already exists for this booking"
            )

        review = Review(**review_data.model_dump(),reviewer_id=user_id)

        session.add(review)

        await session.commit()
        await session.refresh(review)

        service = await session.get(Service, booking.service_id)
        provider = await session.get(Provider, service.provider_id) if service else None

        if provider:
            await self._safe_create_notification(
                user_id=provider.user_id,
                title="New Review Received",
                message=(
                    f"You received a new review (rating: {review.rating}) for booking {review.booking_id}."
                ),
                session=session,
                event_type="review.received",
                entity_type="review",
                entity_id=review.uid,
                payload={"booking_id": str(review.booking_id), "rating": review.rating},
            )

        return review


    async def get_all_reviews(self, session: AsyncSession):

        statement = select(Review).where(Review.deleted_at == None).order_by(desc(Review.created_at))

        results = await session.exec(statement)

        return results.all()


    async def get_review_by_id(self, review_id: UUID, session: AsyncSession):

        review = await session.get(Review, review_id)

        if not review or review.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )

        return review


    async def update_review(self,review_id: UUID,review_data: UpdateReview,current_user,session: AsyncSession):

        review = await self.get_review_by_id(review_id, session)

        if current_user.role != "admin" and review.reviewer_id != current_user.uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own review"
            )

        update_data = review_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(review, key, value)

        await session.commit()
        await session.refresh(review)

        booking = await session.get(Booking, review.booking_id)
        service = await session.get(Service, booking.service_id) if booking else None
        provider = await session.get(Provider, service.provider_id) if service else None

        if provider:
            await self._safe_create_notification(
                user_id=provider.user_id,
                title="Review Updated",
                message=(
                    f"A review for booking {review.booking_id} has been updated (rating: {review.rating})."
                ),
                session=session,
                event_type="review.updated",
                entity_type="review",
                entity_id=review.uid,
                payload={"booking_id": str(review.booking_id), "rating": review.rating},
            )

        return review


    async def delete_review(
        self,
        review_id: UUID,
        current_user,
        session: AsyncSession,
        delete_reason: Optional[str] = None,
    ):

        review = await self.get_review_by_id(review_id, session)

        if current_user.role != "admin" and review.reviewer_id != current_user.uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own review"
            )

        booking = await session.get(Booking, review.booking_id)
        service = await session.get(Service, booking.service_id) if booking else None
        provider = await session.get(Provider, service.provider_id) if service else None

        review.deleted_at = datetime.utcnow()
        review.deleted_by = current_user.uid
        review.delete_reason = delete_reason
        await session.commit()
        await session.refresh(review)

        if provider:
            await self._safe_create_notification(
                user_id=provider.user_id,
                title="Review Deleted",
                message=(
                    f"A review for booking {review.booking_id} has been deleted."
                ),
                session=session,
                event_type="review.deleted",
                entity_type="review",
                entity_id=review.uid,
                payload={
                    "booking_id": str(review.booking_id),
                    "rating": review.rating,
                    "deleted_by": str(current_user.uid),
                    "delete_reason": delete_reason,
                },
            )

        return True
