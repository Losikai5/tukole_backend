from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime

from app.core.models import DisputeStatus, DisputeResolution


class DisputeCreate(BaseModel):
    booking_id: UUID
    reason: str
    description: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "booking_id": "123e4567-e89b-12d3-a456-426614174000",
                "reason": "Service not completed",
                "description": "The provider did not show up"
            }
        }
    }

class DisputeAdminUpdate(BaseModel):
    status: DisputeStatus
    admin_response: str
    resolution: DisputeResolution  


class DisputeResponse(BaseModel):

    uid: UUID
    booking_id: UUID
    raised_by: UUID
    reason: str
    description: Optional[str] = None
    status: str
    admin_response: Optional[str] = None
    resolution: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }