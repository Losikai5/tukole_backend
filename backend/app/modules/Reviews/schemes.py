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

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating between 1 and 5")
    comment: Optional[str] = Field(None, max_length=1000, description="Review comment")

    

class ReviewResponse(BaseModel):
    uid: UUID
    booking_id: UUID
    reviewer_id: UUID
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }
