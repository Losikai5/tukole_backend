from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Any, Optional

class NotificationResponse(BaseModel):

    uid: UUID
    user_id: UUID
    title: str
    message: str
    event_type: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[UUID]
    payload: Optional[dict[str, Any]]
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
                "event_type": "booking.created",
                "entity_type": "booking",
                "entity_id": "123e4567-e89b-12d3-a456-426614174111",
                "payload": {
                    "booking_id": "123e4567-e89b-12d3-a456-426614174111",
                    "service_name": "House Cleaning"
                },
                "is_read": False,
                "created_at": "2026-03-12T10:30:00"
            }
        }
    }


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    limit: int
    offset: int


class NotificationMarkAllReadResponse(BaseModel):
    marked_count: int


class NotificationDeliveryMetricsResponse(BaseModel):
    attempted: int
    succeeded: int
    failed: int
    retries: int
    success_rate: float