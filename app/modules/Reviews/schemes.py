from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

class ReviewCreate(BaseModel):
    booking_id: UUID = Field(..., description="ID of the reviewed booking")
    rating: int = Field(..., ge=1, le=5, description="Rating between 1 and 5")
    comment: Optional[str] = Field(None, max_length=1000, description="Review comment")

    model_config = {
        "json_schema_extra": {
            "example": {
                "booking_id": "12345678-1234-1234-1234-123456789012",
                "rating": 5,
                "comment": "Excellent service!"
            }
        }
    }

class UpdateReview(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating between 1 and 5")
    comment: Optional[str] = Field(None, max_length=1000, description="Review comment")

    model_config = {
        "json_schema_extra": {
            "example": {
                "rating": 4,
                "comment": "Good service, but room for improvement."
            }
        }
    }

class ReviewResponse(BaseModel):
    uid: UUID
    booking_id: UUID
    reviewer_id: UUID
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "uid": "123e4567-e89b-12d3-a456-426614174000",
                "booking_id": "12345678-1234-1234-1234-123456789012",
                "reviewer_id": "87654321-4321-4321-4321-210987654321",
                "rating": 5,
                "comment": "Excellent service!",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            }
        }
    }
