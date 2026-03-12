from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc
from fastapi import HTTPException, status
from uuid import UUID

from .schemes import ReviewCreate, UpdateReview
from app.core.models import Review, Booking


class ReviewService:


    async def create_review(
        self,
        review_data: ReviewCreate,
        user_id: UUID,
        session: AsyncSession
    ):
        """Create a new review."""

        booking = await session.get(Booking, review_data.booking_id)

        if not booking:
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
        statement = select(Review).where(Review.booking_id == review_data.booking_id)
        result = await session.exec(statement)

        existing_review = result.first()

        if existing_review:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Review already exists for this booking"
            )

        review = Review(
            **review_data.model_dump(),
            reviewer_id=user_id
        )

        session.add(review)

        await session.commit()
        await session.refresh(review)

        return review


    async def get_all_reviews(self, session: AsyncSession):

        statement = select(Review).order_by(desc(Review.created_at))

        results = await session.exec(statement)

        return results.all()


    async def get_review_by_id(self, review_id: UUID, session: AsyncSession):

        review = await session.get(Review, review_id)

        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )

        return review


    async def update_review(
        self,
        review_id: UUID,
        review_data: UpdateReview,
        session: AsyncSession
    ):

        review = await self.get_review_by_id(review_id, session)

        update_data = review_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(review, key, value)

        await session.commit()
        await session.refresh(review)

        return review


    async def delete_review(self, review_id: UUID, session: AsyncSession):

        review = await self.get_review_by_id(review_id, session)

        await session.delete(review)

        await session.commit()

        return True