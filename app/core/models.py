from sqlmodel import SQLModel, Field, Column, func, Relationship
from uuid import uuid4
from datetime import datetime
import sqlalchemy.dialects.postgresql as pg

class User(SQLModel, table=True):
    __tablename__ = "users"
    uuid:str = Field(sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4))
    username:str = Field(sa_column=Column(nullable=False, unique=True))
    first_name:str = Field(sa_column=Column(nullable=False))
    last_name:str = Field(sa_column=Column(nullable=False))
    role:str = Field(default="user")
    email:str = Field(sa_column=Column(nullable=False, unique=True))
    is_verified: bool = Field(default=False)
    password_hash: str
    created_at:datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), server_default=func.now()))
    updated_at:datetime = Field(sa_column=Column(pg.TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()))

    def __repr__(self) -> str:
        return f"User(uuid={self.uuid}, username={self.username}, email={self.email})"


