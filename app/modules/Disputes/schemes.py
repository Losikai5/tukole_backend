from pydantic import BaseModel
from uuid import UUID


class DisputeCreate(BaseModel):

    booking_id: UUID
    reason: str


class DisputeUpdate(BaseModel):

    status: str


class DisputeResponse(BaseModel):

    id: UUID
    booking_id: UUID
    raised_by: UUID
    reason: str
    status: str

    class Config:
        from_attributes = True