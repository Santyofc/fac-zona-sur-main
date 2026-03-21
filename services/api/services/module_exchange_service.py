"""
Replay protection for hub module exchange using Redis SET NX + EX.
"""
from redis.asyncio import Redis
from config import settings


async def mark_jti_once(jti: str, ttl_seconds: int) -> bool:
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    key = f"{settings.MODULE_AUTH_REPLAY_PREFIX}:{jti}"
    # SET key value NX EX ttl  -> returns True only first time
    accepted = await redis.set(key, "1", ex=max(1, ttl_seconds), nx=True)
    await redis.close()
    return bool(accepted)
