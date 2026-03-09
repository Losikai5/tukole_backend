from sqlmodel import Relationship, SQLModel, Field, Column
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import func, Numeric
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
    #Relationships
    #reviews: list["Review"] = Relationship(back_populates="user")
     # Relationships
    # provider_profile: Optional["Provider"] = Relationship(back_populates="user")
    # bookings: list["Booking"] = Relationship(back_populates="customer")
    # reviews: list["Review"] = Relationship(back_populates="reviewer")

class Service(SQLModel, table=True):
    """Service model representing a service offered in the platform."""
    __tablename__ = "services"
    
    uid: UUID = Field(
        sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4),
        description="Unique identifier for the service"
    )
    name: str = Field(
        index=True, 
        unique=True, 
        nullable=False,
        max_length=255,
        description="Service name"
    )
    description: Optional[str] = Field(
        default=None,
        nullable=True,
        description="Detailed service description"
    )
    price: Decimal = Field(
        sa_column=Column(Numeric(10, 2), nullable=False),
        description="Service price in decimal format"
    )
    created_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, server_default=func.now()),
        description="Timestamp when service was created"
    )
    updated_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, server_default=func.now(), onupdate=func.now()),
        description="Timestamp when service was last updated"
    )
    # Relationships
    # provider: Optional["Provider"] = Relationship(back_populates="services")
    # bookings: list["Booking"] = Relationship(back_populates="service")

    #reviews: List["Review"] = Relationship(back_populates="services")

class Provider(SQLModel, table=True):

    __tablename__ = "providers"

    id: UUID = Field(
        sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4)
    )

    user_id: UUID = Field(
        foreign_key="users.uid"
    )

    business_name: Optional[str] = None
    bio: Optional[str] = None

    rating: float = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    # user: Optional["User"] = Relationship(back_populates="provider_profile")
    # services: list["Service"] = Relationship(back_populates="provider")

class Booking(SQLModel, table=True):

    __tablename__ = "bookings"

    id: UUID = Field(
        sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4)
    )

    service_id: UUID = Field(
        foreign_key="services.id"
    )

    customer_id: UUID = Field(
        foreign_key="users.uid"
    )

    booking_date: datetime

    status: str = "pending"  # pending | accepted | completed | cancelled

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    # service: Optional["Service"] = Relationship(back_populates="bookings")
    # customer: Optional["User"] = Relationship(back_populates="bookings")
    # payment: Optional["Payment"] = Relationship(back_populates="booking")
    # review: Optional["Review"] = Relationship(back_populates="booking")
    # disputes: list["Dispute"] = Relationship(back_populates="booking")


class Payment(SQLModel, table=True):

    __tablename__ = "payments"

    id: UUID = Field(
        sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4)
    )

    booking_id: UUID = Field(
        foreign_key="bookings.id"
    )

    amount: float

    status: str = "pending"  # pending | escrow | released | refunded

    transaction_ref: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    # booking: Optional["Booking"] = Relationship(back_populates="payment")


class Review(SQLModel, table=True):
    __tablename__ = "reviews"

    id: UUID = Field(
        sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4)
    )

    booking_id: UUID = Field(
        foreign_key="bookings.id"
    )

    reviewer_id: UUID = Field(
        foreign_key="users.uid"
    )

    rating: int

    comment: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    # booking: Optional["Booking"] = Relationship(back_populates="review")
    # reviewer: Optional["User"] = Relationship(back_populates="reviews")


class Dispute(SQLModel, table=True):

    __tablename__ = "disputes"

    id: UUID = Field(
        sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4)
    )

    booking_id: UUID = Field(
        foreign_key="bookings.id"
    )

    raised_by: UUID = Field(
        foreign_key="users.uid"
    )

    reason: str

    description: Optional[str] = None

    status: str = "open"  # open | under_review | resolved | rejected

    admin_response: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

    resolved_at: Optional[datetime] = None

    # Relationships
    # booking: Optional["Booking"] = Relationship(back_populates="disputes")
    # user: Optional["User"] = Relationship()    