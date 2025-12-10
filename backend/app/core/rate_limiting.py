#!/usr/bin/env python3
"""
Rate limiting middleware for FastAPI

SECURITY: Implements per-endpoint rate limiting to prevent abuse and DDoS attacks.
Uses Redis for distributed rate limiting across multiple backend instances.
"""

import time
import logging
from typing import Optional, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.redis import get_redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with different limits per endpoint type
    
    SECURITY: Protects against:
    - Brute force attacks (login endpoints)
    - API abuse (general endpoints)
    - DDoS attacks (all endpoints)
    
    Rate Limits:
    - Admin endpoints: 1000 req/min
    - Login endpoints: 5 req/min (with progressive delays)
    - Public endpoints: 60 req/min
    - Authenticated endpoints: 300 req/min
    """
    
    # Rate limit configurations (requests per minute)
    RATE_LIMITS = {
        "admin": 1000,      # Admin endpoints (high limit for admin operations)
        "login": 5,         # Login endpoints (low limit to prevent brute force)
        "public": 60,       # Public endpoints (moderate limit)
        "authenticated": 300,  # Authenticated endpoints (standard limit)
    }
    
    # Endpoint patterns for classification
    ADMIN_PATTERNS = ["/api/v1/admin/"]
    LOGIN_PATTERNS = ["/api/v1/auth/login", "/api/v1/auth/register"]
    PUBLIC_PATTERNS = [
        "/api/v1/auth/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]
    
    async def dispatch(self, request: Request, call_next):
        """
        Check rate limit before processing request
        """
        # Skip rate limiting for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Classify endpoint type
        endpoint_type = self._classify_endpoint(request.url.path)
        limit = self.RATE_LIMITS.get(endpoint_type, self.RATE_LIMITS["authenticated"])
        
        # Get client identifier (IP address or user ID if authenticated)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        allowed, remaining, reset_time = await self._check_rate_limit(
            client_id=client_id,
            endpoint_type=endpoint_type,
            limit=limit,
            window_seconds=60  # 1 minute window
        )
        
        if not allowed:
            # Rate limit exceeded
            logger.warning(
                f"Rate limit exceeded for {client_id} on {request.url.path}",
                extra={
                    "client_id": client_id,
                    "path": request.url.path,
                    "endpoint_type": endpoint_type,
                    "limit": limit
                }
            )
            
            # For login endpoints, add progressive delay
            if endpoint_type == "login":
                delay = await self._get_progressive_delay(client_id)
                if delay > 0:
                    import asyncio
                    await asyncio.sleep(delay)
            
            # Return 429 Too Many Requests
            response = Response(
                content=f"Rate limit exceeded. Limit: {limit} requests per minute. Try again after {reset_time} seconds.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="text/plain"
            )
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(int(reset_time))
            response.headers["Retry-After"] = str(int(reset_time))
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time))
        
        return response
    
    def _classify_endpoint(self, path: str) -> str:
        """
        Classify endpoint type based on path
        
        Returns: "admin", "login", "public", or "authenticated"
        """
        # Check admin endpoints first
        if any(path.startswith(pattern) for pattern in self.ADMIN_PATTERNS):
            return "admin"
        
        # Check login endpoints
        if any(path.startswith(pattern) for pattern in self.LOGIN_PATTERNS):
            return "login"
        
        # Check public endpoints
        if any(path.startswith(pattern) for pattern in self.PUBLIC_PATTERNS):
            return "public"
        
        # Default to authenticated
        return "authenticated"
    
    def _get_client_id(self, request: Request) -> str:
        """
        Get unique client identifier for rate limiting
        
        Priority:
        1. User ID from JWT token (if authenticated)
        2. IP address (for unauthenticated requests)
        """
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    async def _check_rate_limit(
        self,
        client_id: str,
        endpoint_type: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, int, float]:
        """
        Check if request is within rate limit
        
        Uses Redis sliding window algorithm:
        - Key format: "rate_limit:{endpoint_type}:{client_id}"
        - Value: Current request count
        - TTL: window_seconds
        
        Returns:
            (allowed: bool, remaining: int, reset_time: float)
        """
        redis = await get_redis()
        if not redis:
            # If Redis is unavailable, allow request (fail open)
            logger.warning("Redis unavailable, skipping rate limit check")
            return True, limit, window_seconds
        
        try:
            # Create rate limit key
            key = f"rate_limit:{endpoint_type}:{client_id}"
            
            # Get current count
            current_count = await redis.get(key)
            if current_count is None:
                # First request in window
                await redis.setex(key, window_seconds, "1")
                return True, limit - 1, window_seconds
            
            current_count = int(current_count)
            
            if current_count >= limit:
                # Rate limit exceeded
                ttl = await redis.ttl(key)
                return False, 0, max(ttl, 1)
            
            # Increment counter
            new_count = await redis.incr(key)
            
            # Get remaining requests
            remaining = max(0, limit - new_count)
            
            # Get reset time
            ttl = await redis.ttl(key)
            reset_time = max(ttl, 1)
            
            return True, remaining, reset_time
            
        except Exception as e:
            # On error, allow request (fail open)
            logger.error(f"Rate limit check failed: {e}", exc_info=True)
            return True, limit, window_seconds
    
    async def _get_progressive_delay(self, client_id: str) -> float:
        """
        Get progressive delay for login attempts
        
        Progressive delays:
        - 1st failure: 0 seconds
        - 2nd failure: 1 second
        - 3rd failure: 2 seconds
        - 4th failure: 4 seconds
        - 5th+ failure: 8 seconds
        
        Returns: Delay in seconds
        """
        redis = await get_redis()
        if not redis:
            return 0.0
        
        try:
            key = f"login_failures:{client_id}"
            failures = await redis.get(key)
            
            if failures is None:
                return 0.0
            
            failures = int(failures)
            
            # Progressive delay: 2^(failures-1) seconds, max 8 seconds
            delay = min(2 ** (failures - 1), 8.0)
            
            return delay
            
        except Exception as e:
            logger.error(f"Progressive delay check failed: {e}", exc_info=True)
            return 0.0

