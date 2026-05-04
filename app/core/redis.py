from redis.asyncio import Redis as aioredis
from app.core.config import settings

JTI_EXPIRATION_SECONDS = 3600 
token_blocklist_redis = aioredis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}")

async def add_token_to_blocklist(jti: str):
    await token_blocklist_redis.setex(jti, JTI_EXPIRATION_SECONDS, "true")
    
async def is_token_revoked(jti: str) -> bool:
    entry = await token_blocklist_redis.get(jti)
    return entry is not None

