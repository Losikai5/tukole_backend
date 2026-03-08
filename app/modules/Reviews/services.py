from sqlalchemy.ext.asyncio import AsyncSession
from .schemes import CreateReview, UpdateReview, ReviewResponse
from app.core.models import Review as ReviewModel
from sqlmodel import select, desc

class ReviewService:
    async def create_review(self, review_data: CreateReview, session: AsyncSession):
        """Create a new review."""
        new_review = ReviewModel(**review_data.model_dump())
        session.add(new_review)
        await session.commit()
        await session.refresh(new_review)
        return new_review

    async def get_all_reviews(self, session: AsyncSession):
        statement = select(ReviewModel).order_by(desc(ReviewModel.created_at))
        results = await session.exec(statement)
        return results.all()

    async def get_review_by_id(self, review_id: str, session: AsyncSession):
        """Get a review by ID."""
        statement = select(ReviewModel).where(ReviewModel.uid == review_id)
        results = await session.exec(statement)
        return results.first()
    

    async def update_review(self, review_id: str, review_data: UpdateReview, session: AsyncSession):
        """Update an existing review."""
        review = await self.get_review_by_id(review_id, session)
        if not review:
            raise ValueError("Review not found")

        update_data = review_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(review, key, value)

        await session.commit()
        await session.refresh(review)
        return review
    

    async def delete_review(self, review_id: str, session: AsyncSession):
        """Delete a review."""
        review = await self.get_review_by_id(review_id, session)
        if not review:
            raise ValueError("Review not found")

        await session.delete(review)
        await session.commit()
        return True