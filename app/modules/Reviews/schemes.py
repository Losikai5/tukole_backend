from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

class CreateReview(BaseModel):
    service_id: str = Field(..., description="ID of the reviewed service")
    user_id: str = Field(..., description="ID of the user who wrote the review")
    rating: int = Field(..., ge=1, le=5, description="Rating between 1 and 5")
    comment: str = Field(..., max_length=1000, description="Review comment")

    model_config = {
        "json_schema_extra": {
            "example": {
                "service_id": "12345678-1234-1234-1234-123456789012",
                "user_id": "87654321-4321-4321-4321-210987654321",
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
    service_id: str
    user_id: str
    rating: int
    comment: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "uid": "123e4567-e89b-12d3-a456-426614174000",
                "service_id": "12345678-1234-1234-1234-123456789012",
                "user_id": "87654321-4321-4321-4321-210987654321",
                "rating": 5,
                "comment": "Excellent service!",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z"
            }
        }
    }

