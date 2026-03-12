from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user

from .services import ReviewService
from .schemes import ReviewCreate, UpdateReview, ReviewResponse


review_router = APIRouter()

review_service = ReviewService()


# Create Review
@review_router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    session: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):

    review = await review_service.create_review(
        review_data,
        current_user.uid,
        session
    )

    return review


# Get All Reviews
@review_router.get("/", response_model=List[ReviewResponse])
async def get_all_reviews(
    session: AsyncSession = Depends(get_db)
):

    reviews = await review_service.get_all_reviews(session)

    return reviews


# Get Single Review
@review_router.get("/{review_id}", response_model=ReviewResponse)
async def get_review_by_id(
    review_id: UUID,
    session: AsyncSession = Depends(get_db)
):

    review = await review_service.get_review_by_id(review_id, session)

    return review


# Update Review
@review_router.patch("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: UUID,
    review_data: UpdateReview,
    session: AsyncSession = Depends(get_db)
):

    review = await review_service.update_review(
        review_id,
        review_data,
        session
    )

    return review


# Delete Review
@review_router.delete("/{review_id}", status_code=status.HTTP_200_OK)
async def delete_review(
    review_id: UUID,
    session: AsyncSession = Depends(get_db)
):

    await review_service.delete_review(review_id, session)

    return {"message": "Review deleted successfully"}