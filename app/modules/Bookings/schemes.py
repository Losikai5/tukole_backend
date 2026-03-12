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

    id: UUID
    service_id: UUID
    customer_id: UUID
    booking_date: datetime
    status: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "service_id": "123e4567-e89b-12d3-a456-426614174000",
                "customer_id": "123e4567-e89b-12d3-a456-426614174000",
                "booking_date": "2024-07-01T10:00:00Z",
                "status": "pending" # pending | accepted | completed | cancelled
            }
        }
    }