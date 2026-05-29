# modules/Review/service.py
from sqlmodel import select, desc
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID
from app.core.models import Review, Booking, BookingStatus, UserRole
from app.modules.Reviews.schemes import ReviewCreate, ReviewUpdate


class ReviewService:

    async def get_review_by_id(self, review_id: UUID, session: AsyncSession):
        statement = select(Review).where(Review.uid == review_id)
        result = await session.exec(statement)
        return result.first()

    async def get_all_reviews(self, session: AsyncSession):
        statement = select(Review).order_by(desc(Review.created_at))
        result = await session.exec(statement)
        return result.all()

    async def get_provider_reviews(self, provider_id: UUID, session: AsyncSession):
        statement = (
            select(Review)
            .join(Booking, Review.booking_id == Booking.uid)
            .where(Booking.service.has(provider_id=provider_id))
            .order_by(desc(Review.created_at))
        )
        result = await session.exec(statement)
        return result.all()

    async def create_review(self, data: ReviewCreate, current_user, session: AsyncSession):
        # validate booking exists
        booking = await session.get(Booking, data.booking_id)
        if not booking:
            raise ValueError("Booking not found")

        # only the customer of that booking can review
        if booking.customer_id != current_user.uid:
            raise PermissionError("You can only review your own bookings")

        # booking must be completed
        if booking.status != BookingStatus.COMPLETED:
            raise ValueError("Can only review a completed booking")

        # one review per booking
        existing = await session.exec(
            select(Review).where(Review.booking_id == data.booking_id)
        )
        if existing.first():
            raise ValueError("You have already reviewed this booking")

        review = Review(**data.model_dump(), reviewer_id=current_user.uid)
        session.add(review)
        await session.commit()
        await session.refresh(review)
        return review

    async def update_review(self, review_id: UUID, data: ReviewUpdate, current_user, session: AsyncSession):
        review = await self.get_review_by_id(review_id, session)
        if not review:
            raise ValueError("Review not found")

        # only the reviewer or admin can update
        if current_user.role != UserRole.ADMIN and current_user.uid != review.reviewer_id:
            raise PermissionError("You can only update your own reviews")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(review, key, value)

        await session.commit()
        await session.refresh(review)
        return review

    async def delete_review(self, review_id: UUID, current_user, session: AsyncSession):
        review = await self.get_review_by_id(review_id, session)
        if not review:
            raise ValueError("Review not found")

        # only the reviewer or admin can delete
        if current_user.role != UserRole.ADMIN and current_user.uid != review.reviewer_id:
            raise PermissionError("You can only delete your own reviews")

        await session.delete(review)
        await session.commit()
        return True