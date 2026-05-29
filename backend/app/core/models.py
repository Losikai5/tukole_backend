import uuid
import enum
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship, Column
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import func, Numeric
from decimal import Decimal




class UserRole(str, enum.Enum):
    CONSUMER = "consumer"
    PROVIDER = "provider"
    ADMIN    = "admin"

class BookingStatus(str, enum.Enum):
    PENDING   = "pending"
    ACCEPTED  = "accepted"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PaymentStatus(str, enum.Enum):
    PENDING  = "pending"
    ESCROW   = "escrow"
    RELEASED = "released"
    REFUNDED = "refunded"

class DisputeStatus(str, enum.Enum):
    OPEN         = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED     = "resolved"
    REJECTED     = "rejected"


class DisputeResolution(str, enum.Enum):
    CONSUMER = "consumer"
    PROVIDER = "provider"

class NotificationType(str, enum.Enum):
    # Account
    ACCOUNT_VERIFICATION = "account_verification"
    # Booking
    BOOKING_CREATED      = "booking_created"
    BOOKING_ACCEPTED     = "booking_accepted"
    BOOKING_COMPLETED    = "booking_completed"
    BOOKING_CANCELLED    = "booking_cancelled"
    # Payment / Escrow
    PAYMENT_MADE         = "payment_made"
    PAYMENT_IN_ESCROW    = "payment_in_escrow"
    PAYMENT_RELEASED     = "payment_released"
    PAYMENT_REFUNDED     = "payment_refunded"
    # Dispute
    DISPUTE_RAISED       = "dispute_raised"
    DISPUTE_UNDER_REVIEW = "dispute_under_review"
    DISPUTE_RESOLVED     = "dispute_resolved"
    # Review
    REVIEW_MADE          = "review_made"


# ─────────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────────

class User(SQLModel, table=True):
    __tablename__ = "users"

    uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4))
    username: str = Field(nullable=False, unique=True)
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    email: str = Field(nullable=False, unique=True)
    hashed_password: str = Field(exclude=True, nullable=False)
    is_active: bool = Field(default=False, nullable=False)
    is_verified: bool = Field(default=False, nullable=False)
    role: UserRole = Field(default=UserRole.CONSUMER, sa_column=Column(pg.VARCHAR, nullable=False))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None), sa_column=Column(pg.TIMESTAMP, server_default=func.now()))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, server_default=func.now(), onupdate=func.now()))

    # Relationships
    provider_profile: Optional["Provider"] = Relationship(back_populates="user")
    bookings: list["Booking"] = Relationship(
        back_populates="customer",
        sa_relationship_kwargs={"foreign_keys": "[Booking.customer_id]"},
    )
    reviews: list["Review"] = Relationship(
        back_populates="reviewer",
        sa_relationship_kwargs={"foreign_keys": "[Review.reviewer_id]"},
    )
    notifications: list["Notification"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class Provider(SQLModel, table=True):
    __tablename__ = "providers"

    uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4))
    user_id: uuid.UUID = Field(foreign_key="users.uid", unique=True)
    business_name: Optional[str] = None
    bio: Optional[str] = None
    rating: float = 0
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, server_default=func.now()))

    # Relationships
    user: Optional["User"] = Relationship(back_populates="provider_profile")
    services: list["Service"] = Relationship(back_populates="provider")


class Service(SQLModel, table=True):
    __tablename__ = "services"

    uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4))
    provider_id: uuid.UUID = Field(foreign_key="providers.uid", nullable=False)
    name: str = Field(index=True, unique=True, nullable=False, max_length=255)
    description: Optional[str] = Field(default=None, nullable=True)
    price: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, server_default=func.now()))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, server_default=func.now(), onupdate=func.now()))

    # Relationships
    provider: Optional["Provider"] = Relationship(
        back_populates="services",
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    bookings: list["Booking"] = Relationship(back_populates="service")


class Booking(SQLModel, table=True):
    __tablename__ = "bookings"

    uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4))
    service_id: uuid.UUID = Field(foreign_key="services.uid")
    customer_id: uuid.UUID = Field(foreign_key="users.uid")
    booking_date: datetime
    status: BookingStatus = Field(default=BookingStatus.PENDING, sa_column=Column(pg.VARCHAR, nullable=False))
    deleted_at: Optional[datetime] = Field(default=None)
    deleted_by: Optional[uuid.UUID] = Field(default=None, foreign_key="users.uid")
    delete_reason: Optional[str] = Field(default=None)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, server_default=func.now()))

    # Relationships
    service: Optional["Service"] = Relationship(
        back_populates="bookings",
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    customer: Optional["User"] = Relationship(
        back_populates="bookings",
        sa_relationship_kwargs={"foreign_keys": "[Booking.customer_id]"},
    )
    payment: Optional["Payment"] = Relationship(back_populates="booking")
    review: Optional["Review"] = Relationship(back_populates="booking")
    disputes: list["Dispute"] = Relationship(back_populates="booking")


class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4))
    booking_id: uuid.UUID = Field(foreign_key="bookings.uid", unique=True, nullable=False)
    amount: float
    status: PaymentStatus = Field(default=PaymentStatus.PENDING, sa_column=Column(pg.VARCHAR, nullable=False))
    transaction_ref: Optional[str] = Field(default=None, unique=True)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, server_default=func.now()))

    # Relationships
    booking: Optional["Booking"] = Relationship(back_populates="payment")


class Review(SQLModel, table=True):
    __tablename__ = "reviews"

    uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4))
    booking_id: uuid.UUID = Field(foreign_key="bookings.uid")
    reviewer_id: uuid.UUID = Field(foreign_key="users.uid")
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    deleted_at: Optional[datetime] = Field(default=None)
    deleted_by: Optional[uuid.UUID] = Field(default=None, foreign_key="users.uid")
    delete_reason: Optional[str] = Field(default=None)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, server_default=func.now()))
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, server_default=func.now(), onupdate=func.now()))

    # Relationships
    booking: Optional["Booking"] = Relationship(back_populates="review")
    reviewer: Optional["User"] = Relationship(
        back_populates="reviews",
        sa_relationship_kwargs={"foreign_keys": "[Review.reviewer_id]"},
    )


class Dispute(SQLModel, table=True):
    __tablename__ = "disputes"

    uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4))
    booking_id: uuid.UUID = Field(foreign_key="bookings.uid")
    raised_by: uuid.UUID = Field(foreign_key="users.uid")
    reason: str
    description: Optional[str] = None
    status: DisputeStatus = Field(default=DisputeStatus.OPEN, sa_column=Column(pg.VARCHAR, nullable=False))
    admin_response: Optional[str] = None
    resolution: Optional[str] = Field(default=None)  # "consumer" | "provider" — who admin ruled for
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, server_default=func.now()))
    resolved_at: Optional[datetime] = None

    # Relationships
    booking: Optional["Booking"] = Relationship(back_populates="disputes")


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    uid: uuid.UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4))
    message: str
    notification_type: NotificationType = Field(sa_column=Column(pg.VARCHAR, nullable=False))
    is_read: bool = Field(default=False)
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, server_default=func.now()))
    user_uid: uuid.UUID = Field(foreign_key="users.uid", nullable=False)

    # Relationships
    user: Optional["User"] = Relationship(
        back_populates="notifications",
        sa_relationship_kwargs={"lazy": "selectin"},
    )