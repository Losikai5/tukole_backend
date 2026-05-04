from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal

class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "House Cleaning",
                "description": "Full house cleaning service",
                "price": 50.00
            }
        }
    }

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None

    
class ServiceResponse(BaseModel):
    uid: UUID
    provider_id: UUID
    name: str
    description: Optional[str]
    price: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }