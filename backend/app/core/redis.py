#!/usr/bin/env python3
"""
Redis configuration and initialization
"""

import redis.asyncio as redis
from typing import Optional
from app.core.config import settings

# Global Redis client
redis_client: Optional[redis.Redis] = None


async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    
    try:
        redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Test connection
        await redis_client.ping()
        print("✅ Redis connected successfully")
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        redis_client = None


async def get_redis() -> redis.Redis:
    """Get Redis client"""
    if redis_client is None:
        await init_redis()
    return redis_client


async def close_redis():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        print("Redis connection closed")

