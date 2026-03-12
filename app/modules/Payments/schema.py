from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class PaymentCreate(BaseModel):

    booking_id: UUID
    amount: float
    model_config = {
        "json_schema_extra": {
            "example": {
                "booking_id": "123e4567-e89b-12d3-a456-426614174000",
                "amount": 100.0
                }
        }
    }


class PaymentResponse(BaseModel):

    uid: UUID
    booking_id: UUID
    amount: float
    status: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "uid": "123e4567-e89b-12d3-a456-426614174000",
                "booking_id": "123e4567-e89b-12d3-a456-426614174000",
                "amount": 100.0,
                "status": "pending",
                "created_at": "2024-01-01T00:00:00Z"
            }   
        }
    }