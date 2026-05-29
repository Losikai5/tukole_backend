from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from sqlalchemy.orm import sessionmaker

DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
)
local_session = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession)

async def get_db():
    async with local_session() as session:
        yield session
