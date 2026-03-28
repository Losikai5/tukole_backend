from redis.asyncio import Redis as aioredis
from app.core.config import settings

JTI_EXPIRATION_SECONDS = 3600 
token_blocklist_redis = aioredis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}")

async def add_token_to_blocklist(jti: str):
    await token_blocklist_redis.setex(jti, JTI_EXPIRATION_SECONDS, "true")
    
async def is_token_revoked(jti: str) -> bool:
    entry = await token_blocklist_redis.get(jti)
    return entry is not None


async def acquire_verification_resend_slot(email: str, cooldown_seconds: int = 60) -> bool:
    key = f"verify_resend:{email.lower()}"
    # NX ensures we only set the key if it does not already exist.
    created = await token_blocklist_redis.set(key, "1", ex=cooldown_seconds, nx=True)
    return bool(created)