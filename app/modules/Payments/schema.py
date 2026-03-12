from pydantic import BaseModel
from uuid import UUID


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

    id: UUID
    booking_id: UUID
    amount: float
    status: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "booking_id": "123e4567-e89b-12d3-a456-426614174000",
                "amount": 100.0,
                "status": "pending" # pending | escrow | released | refunded
            }   
        }
    }