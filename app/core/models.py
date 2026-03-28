from sqlmodel import Relationship, SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import func, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal
from typing import Optional, List

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    uid: UUID = Field(sa_column=Column(pg.UUID, primary_key=True, default=uuid4))
    username: str = Field(nullable=False, unique=True)  
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    email: str = Field(nullable=False, unique=True)
    hashed_password: str = Field(exclude=True, nullable=False)
    is_active: bool = Field(default=False, nullable=False)
    role: str = Field(default="user", nullable=False)  
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, server_default=func.now()))
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


class Service(SQLModel, table=True):
    """Service model representing a service offered in the platform."""
    __tablename__ = "services"
    
    uid: UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4),description="Unique identifier for the service")
    provider_id: UUID = Field(foreign_key="providers.uid", nullable=False)
    name: str = Field(index=True, unique=True, nullable=False,max_length=255,description="Service name")
    description: Optional[str] = Field(default=None,nullable=True,description="Detailed service description")
    price: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False),description="Service price in decimal format")
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, server_default=func.now()),description="Timestamp when service was created")
    updated_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, server_default=func.now(), onupdate=func.now()),description="Timestamp when service was last updated")
    # Relationships
    provider: Optional["Provider"] = Relationship(back_populates="services")
    bookings: list["Booking"] = Relationship(back_populates="service")


class Provider(SQLModel, table=True):

    __tablename__ = "providers"

    uid: UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4))

    user_id: UUID = Field(foreign_key="users.uid",unique=True)

    business_name: Optional[str] = None
    bio: Optional[str] = None

    rating: float = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: Optional["User"] = Relationship(back_populates="provider_profile")
    services: list["Service"] = Relationship(back_populates="provider")

class Booking(SQLModel, table=True):

    __tablename__ = "bookings"

    uid: UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4))

    service_id: UUID = Field(foreign_key="services.uid")

    customer_id: UUID = Field(foreign_key="users.uid")

    booking_date: datetime

    status: str = "pending"  # pending | accepted | completed | cancelled

    deleted_at: Optional[datetime] = Field(default=None)

    deleted_by: Optional[UUID] = Field(default=None, foreign_key="users.uid")

    delete_reason: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    service: Optional["Service"] = Relationship(back_populates="bookings")
    customer: Optional["User"] = Relationship(
        back_populates="bookings",
        sa_relationship_kwargs={"foreign_keys": "[Booking.customer_id]"},
    )
    payment: Optional["Payment"] = Relationship(back_populates="booking")
    review: Optional["Review"] = Relationship(back_populates="booking")
    disputes: list["Dispute"] = Relationship(back_populates="booking")


class Payment(SQLModel, table=True):

    __tablename__ = "payments"

    uid: UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4))

    booking_id: UUID = Field(foreign_key="bookings.uid", unique=True,nullable=False)

    amount: float

    status: str = "pending"  # pending | escrow | released | refunded

    transaction_ref: Optional[str] = Field(default=None,unique=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    booking: Optional["Booking"] = Relationship(back_populates="payment")


class Review(SQLModel, table=True):
    __tablename__ = "reviews"

    uid: UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4))

    booking_id: UUID = Field(foreign_key="bookings.uid")

    reviewer_id: UUID = Field(foreign_key="users.uid")

    rating: int

    comment: Optional[str] = None

    deleted_at: Optional[datetime] = Field(default=None)
    deleted_by: Optional[UUID] = Field(default=None, foreign_key="users.uid")
    delete_reason: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    booking: Optional["Booking"] = Relationship(back_populates="review")
    reviewer: Optional["User"] = Relationship(
        back_populates="reviews",
        sa_relationship_kwargs={"foreign_keys": "[Review.reviewer_id]"},
    )


class Dispute(SQLModel, table=True):

    __tablename__ = "disputes"

    uid: UUID = Field(sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4))

    booking_id: UUID = Field(foreign_key="bookings.uid")

    raised_by: UUID = Field(foreign_key="users.uid")

    reason: str

    description: Optional[str] = None

    status: str = "open"  # open | under_review | resolved | rejected

    admin_response: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

    resolved_at: Optional[datetime] = None

    # Relationships
    booking: Optional["Booking"] = Relationship(back_populates="disputes")

class Notification(SQLModel, table=True):

    __tablename__ = "notifications"

    uid: UUID = Field(
        sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4)
    )

    user_id: UUID = Field(
        foreign_key="users.uid",
        nullable=False
    )

    title: str

    message: str

    event_type: Optional[str] = Field(default=None, max_length=100)

    entity_type: Optional[str] = Field(default=None, max_length=100)

    entity_id: Optional[UUID] = Field(default=None, sa_column=Column(pg.UUID(as_uuid=True), nullable=True))

    payload: Optional[dict] = Field(default=None, sa_column=Column(JSONB, nullable=True))

    is_read: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)     