#!/usr/bin/env python3
"""
Custom middleware for CCS Quote Tool v2
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and validate tenant information from requests
    Sets tenant context for row-level security
    """
    
    async def dispatch(self, request: Request, call_next):
        # Extract tenant from subdomain, header, or JWT token
        tenant_id = None
        
        # Try to get tenant from header
        tenant_id = request.headers.get("X-Tenant-ID")
        
        # Try to get tenant from subdomain
        if not tenant_id:
            host = request.headers.get("host", "")
            if "." in host:
                subdomain = host.split(".")[0]
                if subdomain and subdomain not in ["www", "api", "localhost"]:
                    tenant_id = subdomain
        
        # Default to CCS tenant for development
        if not tenant_id:
            tenant_id = "ccs"
        
        # Store tenant in request state
        request.state.tenant_id = tenant_id
        
        # Set PostgreSQL session variable for row-level security
        # This will be used by the database layer
        request.state.db_tenant_id = tenant_id
        
        response = await call_next(request)
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all requests and responses
    """
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add custom header
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log response
            logger.info(
                f"Response: {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Time: {process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware
    """
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Simple rate limiting (in production, use Redis)
        current_time = int(time.time() / 60)  # Current minute
        key = f"{client_ip}:{current_time}"
        
        if key not in self.request_counts:
            self.request_counts[key] = 0
        
        self.request_counts[key] += 1
        
        if self.request_counts[key] > self.requests_per_minute:
            raise HTTPException(status_code=429, detail="Too many requests")
        
        # Clean up old entries
        old_keys = [k for k in self.request_counts.keys() if int(k.split(":")[1]) < current_time - 5]
        for old_key in old_keys:
            del self.request_counts[old_key]
        
        response = await call_next(request)
        return response

