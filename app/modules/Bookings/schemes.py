from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


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


class BookingResponse(BaseModel):

    uid: UUID
    service_id: UUID
    customer_id: UUID
    booking_date: datetime
    status: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "uid": "123e4567-e89b-12d3-a456-426614174000",
                "service_id": "123e4567-e89b-12d3-a456-426614174000",
                "customer_id": "123e4567-e89b-12d3-a456-426614174000",
                "booking_date": "2024-07-01T10:00:00Z",
                "status": "pending",
                "created_at": "2024-07-01T10:00:00Z"
            }
        }
    }