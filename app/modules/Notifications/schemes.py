from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Any, Optional

from app.core.models import NotificationType


class NotificationResponse(BaseModel):
    uid: UUID
    message: str
    notification_type: NotificationType
    is_read: bool
    created_at: Optional[datetime] = None
    user_uid: UUID

    model_config = {"from_attributes": True}

class NotificationMarkRead(BaseModel):
    uids: list[UUID]

