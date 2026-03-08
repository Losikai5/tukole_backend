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

    def __repr__(self):
        return f"User(uid={self.uid}, username='{self.username}', email='{self.email}', role='{self.role}')"
    





class Review(SQLModel, table=True):
    __tablename__ = "reviews"
    
    uid: UUID = Field(
        sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4),
        description="Unique identifier for the review"
    )
    service_id: str = Field(
        sa_column=Column(pg.UUID(as_uuid=True), nullable=False),
        description="ID of the reviewed service"
    )
    user_id: str = Field(
        sa_column=Column(pg.UUID(as_uuid=True), nullable=False),
        description="ID of the user who wrote the review"
    )
    rating: int = Field(..., ge=1, le=5, description="Rating between 1 and 5")
    comment: str = Field(..., max_length=1000, description="Review comment")
    created_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, server_default=func.now()),
        description="Timestamp when review was created"
    )
    updated_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP, server_default=func.now(), onupdate=func.now()),
        description="Timestamp when review was last updated"
    )
    #Relationships
    #services: List["Service"] = Relationship(back_populates="reviews")
    #user: "User" = Relationship(back_populates="reviews")

    def __repr__(self) -> str:
        return f"Review(uid={self.uid}, service_id={self.service_id}, user_id={self.user_id}, rating={self.rating})" 






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
    #reviews: List["Review"] = Relationship(back_populates="services")

    def __repr__(self) -> str:
        return f"Service(uid={self.uid}, name='{self.name}', price={self.price})"       