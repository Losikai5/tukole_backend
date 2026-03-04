from sqlmodel import Field, SQLModel, Column
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import func, Numeric
from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal
from typing import Optional


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

    def __repr__(self) -> str:
        return f"Service(uid={self.uid}, name='{self.name}', price={self.price})"