from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.core.models import BookingStatus


class BookingCreate(BaseModel):
    service_id: UUID
    booking_date: datetime

    model_config = {
        "json_schema_extra": {
            "example": {
                "service_id": "123e4567-e89b-12d3-a456-426614174000",
                "booking_date": "2024-07-01T10:00:00Z"
            }
        }
    }


class BookingStatusUpdate(BaseModel):
    status: BookingStatus


class BookingCancel(BaseModel):
    delete_reason: Optional[str] = None


class BookingResponse(BaseModel):
    uid: UUID
    service_id: UUID
    customer_id: UUID
    booking_date: datetime
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
