from sqlmodel import SQLModel, Field, Column
import uuid
import datetime
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import func 

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    uid: uuid.UUID = Field(sa_column=Column(pg.UUID, primary_key=True, default=uuid.uuid4))
    username: str = Field(nullable=False)  # Added nullable=False directly
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    email: str = Field(nullable=False, unique=True)
    #hashed_password: str = Field(nullable=False)
    is_active: bool = Field(default=False, nullable=False)
    role: str = Field(default="user", nullable=False)  # Move nullable to Column
    created_at: datetime.datetime = Field(sa_column=Column(pg.TIMESTAMP, server_default=func.now()))
    updated_at: datetime.datetime = Field(sa_column=Column(pg.TIMESTAMP, server_default=func.now(), onupdate=func.now()))

    def __repr__(self):
        return f"User(uid={self.uid}, username='{self.username}', email='{self.email}', role='{self.role}')"