from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.core.models import PaymentStatus


class PaymentCreate(BaseModel):
    booking_id: UUID
    amount: float
    transaction_ref: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "booking_id": "123e4567-e89b-12d3-a456-426614174000",
                "amount": 50.00,
                "transaction_ref": "TXN123456"
            }
        }
    }


class PaymentResponse(BaseModel):
    uid: UUID
    booking_id: UUID
    amount: float
    status: PaymentStatus
    transaction_ref: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}