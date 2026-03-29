from fastapi import APIRouter
from sqlalchemy import text
from redis import asyncio as aioredis

from app.core.config import settings
from app.infrastructure.db.session import engine

router = APIRouter(prefix='/v1', tags=['health'])


@router.get('/health')
async def health():
    return {'status': 'ok'}


@router.get('/readiness')
async def readiness():
    async with engine.connect() as conn:
        await conn.execute(text('SELECT 1'))
    redis_client = aioredis.from_url(settings.REDIS_URL)
    await redis_client.ping()
    await redis_client.aclose()
    return {'status': 'ready'}
