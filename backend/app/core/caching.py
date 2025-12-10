#!/usr/bin/env python3
"""
Strategic caching utility using Redis

PERFORMANCE: Implements caching for frequently accessed data to reduce database load
and improve response times. Uses Redis for distributed caching across multiple workers.
"""

import json
import logging
from typing import Optional, Any, Callable
from datetime import timedelta
from functools import wraps
import hashlib

from app.core.redis import get_redis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Cache key prefixes
CACHE_PREFIX_TENANT = "tenant:"
CACHE_PREFIX_AI_ANALYSIS = "ai_analysis:"
CACHE_PREFIX_CUSTOMER = "customer:"
CACHE_PREFIX_USER = "user:"


def _make_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Create a cache key from prefix and arguments
    
    Args:
        prefix: Cache key prefix
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key string
    """
    # Create a hash of all arguments for consistent key generation
    key_parts = [prefix]
    if args:
        key_parts.extend(str(arg) for arg in args)
    if kwargs:
        # Sort kwargs for consistent key generation
        sorted_kwargs = sorted(kwargs.items())
        key_parts.extend(f"{k}={v}" for k, v in sorted_kwargs)
    
    key_string = ":".join(key_parts)
    # Hash if key is too long (Redis key length limit)
    if len(key_string) > 250:
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}{key_hash}"
    return key_string


async def get_cache(key: str) -> Optional[Any]:
    """
    Get value from cache
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None if not found
    """
    try:
        redis_client = await get_redis()
        value = await redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.warning(f"Cache get failed for key {key}: {e}")
        return None


async def set_cache(key: str, value: Any, ttl: int = 3600) -> bool:
    """
    Set value in cache with TTL
    
    Args:
        key: Cache key
        value: Value to cache (must be JSON serializable)
        ttl: Time to live in seconds (default: 1 hour)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        redis_client = await get_redis()
        serialized = json.dumps(value)
        await redis_client.setex(key, ttl, serialized)
        return True
    except Exception as e:
        logger.warning(f"Cache set failed for key {key}: {e}")
        return False


async def delete_cache(key: str) -> bool:
    """
    Delete value from cache
    
    Args:
        key: Cache key
        
    Returns:
        True if successful, False otherwise
    """
    try:
        redis_client = await get_redis()
        await redis_client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache delete failed for key {key}: {e}")
        return False


async def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalidate all cache keys matching a pattern
    
    Args:
        pattern: Redis key pattern (e.g., "customer:*")
        
    Returns:
        Number of keys deleted
    """
    try:
        redis_client = await get_redis()
        keys = []
        async for key in redis_client.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            await redis_client.delete(*keys)
        return len(keys)
    except Exception as e:
        logger.warning(f"Cache invalidation failed for pattern {pattern}: {e}")
        return 0


def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator to cache function results
    
    Usage:
        @cached(ttl=3600, key_prefix="customer")
        async def get_customer(customer_id: str):
            # Function implementation
            return customer_data
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _make_cache_key(key_prefix or func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_value = await get_cache(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Cache miss - execute function
            logger.debug(f"Cache miss for {cache_key}")
            result = await func(*args, **kwargs)
            
            # Store in cache
            if result is not None:
                await set_cache(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


# Convenience functions for common cache operations

async def cache_tenant_config(tenant_id: str, config: dict, ttl: int = 3600) -> bool:
    """
    Cache tenant configuration
    
    Args:
        tenant_id: Tenant ID
        config: Configuration dictionary
        ttl: Time to live in seconds (default: 1 hour)
        
    Returns:
        True if successful
    """
    key = f"{CACHE_PREFIX_TENANT}{tenant_id}:config"
    return await set_cache(key, config, ttl)


async def get_cached_tenant_config(tenant_id: str) -> Optional[dict]:
    """
    Get cached tenant configuration
    
    Args:
        tenant_id: Tenant ID
        
    Returns:
        Cached configuration or None
    """
    key = f"{CACHE_PREFIX_TENANT}{tenant_id}:config"
    return await get_cache(key)


async def cache_ai_analysis(entity_id: str, analysis_type: str, analysis: dict, ttl: int = 86400) -> bool:
    """
    Cache AI analysis results
    
    Args:
        entity_id: Entity ID (customer_id, ticket_id, etc.)
        analysis_type: Type of analysis (e.g., "customer", "ticket")
        analysis: Analysis result dictionary
        ttl: Time to live in seconds (default: 24 hours)
        
    Returns:
        True if successful
    """
    key = f"{CACHE_PREFIX_AI_ANALYSIS}{analysis_type}:{entity_id}"
    return await set_cache(key, analysis, ttl)


async def get_cached_ai_analysis(entity_id: str, analysis_type: str) -> Optional[dict]:
    """
    Get cached AI analysis
    
    Args:
        entity_id: Entity ID
        analysis_type: Type of analysis
        
    Returns:
        Cached analysis or None
    """
    key = f"{CACHE_PREFIX_AI_ANALYSIS}{analysis_type}:{entity_id}"
    return await get_cache(key)


async def cache_customer_data(customer_id: str, customer_data: dict, ttl: int = 900) -> bool:
    """
    Cache customer data
    
    Args:
        customer_id: Customer ID
        customer_data: Customer data dictionary
        ttl: Time to live in seconds (default: 15 minutes)
        
    Returns:
        True if successful
    """
    key = f"{CACHE_PREFIX_CUSTOMER}{customer_id}"
    return await set_cache(key, customer_data, ttl)


async def get_cached_customer_data(customer_id: str) -> Optional[dict]:
    """
    Get cached customer data
    
    Args:
        customer_id: Customer ID
        
    Returns:
        Cached customer data or None
    """
    key = f"{CACHE_PREFIX_CUSTOMER}{customer_id}"
    return await get_cache(key)


async def invalidate_customer_cache(customer_id: str) -> bool:
    """
    Invalidate all cache entries for a customer
    
    Args:
        customer_id: Customer ID
        
    Returns:
        True if successful
    """
    pattern = f"{CACHE_PREFIX_CUSTOMER}{customer_id}*"
    count = await invalidate_cache_pattern(pattern)
    logger.info(f"Invalidated {count} cache entries for customer {customer_id}")
    return count > 0


async def get_cache_stats() -> dict:
    """
    Get cache statistics (hit rate, etc.)
    
    Returns:
        Dictionary with cache statistics
    """
    try:
        redis_client = await get_redis()
        info = await redis_client.info("stats")
        
        # Calculate hit rate if keyspace hits/misses are available
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0
        
        return {
            "hits": hits,
            "misses": misses,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total
        }
    except Exception as e:
        logger.warning(f"Failed to get cache stats: {e}")
        return {
            "hits": 0,
            "misses": 0,
            "hit_rate": 0,
            "total_requests": 0
        }

