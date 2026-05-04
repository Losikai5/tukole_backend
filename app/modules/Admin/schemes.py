# modules/Admin/schemas.py
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from app.core.models import UserRole, DisputeStatus


class UserStatusUpdate(BaseModel):
    is_active: bool


# Fixed — uses UserRole enum instead of Literal with "user"
class UserRoleUpdate(BaseModel):
    role: UserRole


class AdminUserResponse(BaseModel):
    uid: UUID
    username: str
    first_name: str
    last_name: str
    email: str
    is_active: bool
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


# Fixed — uses DisputeStatus enum and adds resolution field
class AdminDisputeResolve(BaseModel):
    status: DisputeStatus
    admin_response: str
    resolution: str  # "consumer" | "provider" — who admin ruled for


class AdminDisputeResponse(BaseModel):
    uid: UUID
    booking_id: UUID
    raised_by: UUID
    reason: str
    description: Optional[str] = None
    status: DisputeStatus
    admin_response: Optional[str] = None
    resolution: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AdminDashboardResponse(BaseModel):
    total_users: int
    total_providers: int
    total_services: int
    total_bookings: int
    open_disputes: int
    pending_payments: int
    released_revenue: float


class AdminProviderResponse(BaseModel):
    uid: UUID
    user_id: UUID
    business_name: Optional[str] = None
    bio: Optional[str] = None
    rating: float
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminProviderServiceResponse(BaseModel):
    uid: UUID
    provider_id: UUID
    name: str
    description: Optional[str] = None
    price: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdminActionResponse(BaseModel):
    detail: str


class AdminDeletedBookingResponse(BaseModel):
    uid: UUID
    customer_id: UUID
    service_id: UUID
    status: str
    deleted_at: datetime
    deleted_by: Optional[UUID] = None
    delete_reason: Optional[str] = None

    model_config = {"from_attributes": True}


class AdminDeletedReviewResponse(BaseModel):
    uid: UUID
    booking_id: UUID
    reviewer_id: UUID
    rating: int
    comment: Optional[str] = None
    deleted_at: datetime
    deleted_by: Optional[UUID] = None
    delete_reason: Optional[str] = None

    model_config = {"from_attributes": True}