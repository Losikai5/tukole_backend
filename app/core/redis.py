from redis.asyncio import Redis as  aioredis
from app.config import Config

JTI_EXPIRATION_SECONDS = 3600 
token_blocklist_redis = aioredis.from_url(Config.REDIS_URL)

async def add_token_to_blocklist(jti: str):
    await token_blocklist_redis.setex(jti, JTI_EXPIRATION_SECONDS, "true")
    
async def is_token_revoked(jti: str) -> bool:
    entry = await token_blocklist_redis.get(jti)
    return entry is not None  