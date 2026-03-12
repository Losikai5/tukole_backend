from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime


class DisputeCreate(BaseModel):

    booking_id: UUID
    reason: str
    description: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "booking_id": "123e4567-e89b-12d3-a456-426614174000",
                "reason": "Service was not completed",
                "description": "The provider did not show up on the scheduled date."
            }
        }
    }


class UpdateDispute(BaseModel):

    status: Optional[str] = None
    admin_response: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "resolved",
                "admin_response": "Refund has been issued."
            }
        }
    }


class DisputeResponse(BaseModel):

    uid: UUID
    booking_id: UUID
    raised_by: UUID
    reason: str
    description: Optional[str] = None
    status: str
    admin_response: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "uid": "123e4567-e89b-12d3-a456-426614174000",
                "booking_id": "123e4567-e89b-12d3-a456-426614174000",
                "raised_by": "123e4567-e89b-12d3-a456-426614174000",
                "reason": "Service was not completed",
                "description": "The provider did not show up.",
                "status": "open",
                "admin_response": None,
                "created_at": "2024-01-01T00:00:00Z",
                "resolved_at": None
            }
        }
    }