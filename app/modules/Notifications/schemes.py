from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class NotificationResponse(BaseModel):

    uid: UUID
    user_id: UUID
    title: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "uid": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "New Booking",
                "message": "You have a new booking request",
                "is_read": False,
                "created_at": "2026-03-12T10:30:00"
            }
        }
    }