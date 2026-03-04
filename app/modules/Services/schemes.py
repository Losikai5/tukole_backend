from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal

class CreateService(BaseModel):
    """Schema for creating a new service."""
    name: str = Field(..., min_length=1, max_length=255, description="Service name")
    description: Optional[str] = Field(
        default=None, 
        max_length=1000,
        description="Service description"
    )
    price: Decimal = Field(..., gt=0, decimal_places=2, description="Service price (must be positive)")

    

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Web Development",
                "description": "Full-stack web development services",
                "price": 1500.00
            }
        }
    }

class UpdateService(BaseModel):
    """Schema for updating an existing service."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Service name")
    description: Optional[str] = Field(None, max_length=1000, description="Service description")
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2, description="Service price")

   

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Web Development",
                "description": "Updated full-stack web development services",
                "price": 1750.00
            }
        }
    }

class ServiceResponse(BaseModel):
    """Schema for service response."""
    uid: UUID
    name: str
    description: Optional[str]
    price: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "uid": "12345678-1234-1234-1234-123456789012",
                "name": "Web Development",
                "description": "Full-stack web development services",
                "price": 1500.00,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }
    }