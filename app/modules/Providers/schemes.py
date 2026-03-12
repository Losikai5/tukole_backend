from pydantic import BaseModel
from typing import Optional, List

class ProviderBase(BaseModel):
    business_name: Optional[str] = None
    bio: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "business_name": "John's Plumbing",
                "bio": "Experienced plumber with 10 years in the industry."
            }
        }
    }

class ProviderResponse(ProviderBase):
    uid: str
    user_id: str
    business_name: Optional[str] = None
    bio: Optional[str] = None
    rating: float = 0.0
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "uid": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "business_name": "John's Plumbing",
                "bio": "Experienced plumber with 10 years in the industry.",
                "rating": 4.5
            }
        }
    }
