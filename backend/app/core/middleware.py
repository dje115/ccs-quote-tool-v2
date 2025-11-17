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
    Middleware to extract tenant information from requests for PUBLIC routes only.
    
    SECURITY: For authenticated routes, tenant MUST come from JWT token (via get_current_user).
    This middleware only handles public routes (like /auth/login) where we need to identify
    the tenant from subdomain or header, but we validate the tenant exists in the database.
    
    For authenticated routes, use get_tenant_from_user() dependency which enforces
    tenant comes from JWT and rejects any header/subdomain mismatch.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Only set tenant for public routes (auth endpoints)
        # For authenticated routes, tenant will be validated from JWT in dependencies
        is_public_route = request.url.path.startswith("/api/v1/auth/")
        
        tenant_id = None
        
        if is_public_route:
            # For public routes, allow subdomain or header-based tenant detection
            # but we'll validate it exists in the database
            
            # Try to get tenant from header
            tenant_id = request.headers.get("X-Tenant-ID")
            
            # Try to get tenant from subdomain
            if not tenant_id:
                host = request.headers.get("host", "")
                if "." in host:
                    subdomain = host.split(".")[0]
                    if subdomain and subdomain not in ["www", "api", "localhost"]:
                        tenant_id = subdomain
            
            # Default to CCS tenant for development (only for public routes)
            if not tenant_id:
                tenant_id = "ccs"
            
            # Validate tenant exists (for public routes)
            # This prevents tenant impersonation even on public routes
            from app.core.database import SessionLocal
            from app.models.tenant import Tenant
            
            db = SessionLocal()
            try:
                tenant = db.query(Tenant).filter(
                    (Tenant.slug == tenant_id) | (Tenant.id == tenant_id)
                ).first()
                
                if tenant:
                    tenant_id = tenant.id  # Use actual tenant ID, not slug
                else:
                    # Tenant doesn't exist, log warning but allow default for development
                    logger.warning(f"Tenant '{tenant_id}' not found in database, using default")
                    tenant_id = "ccs"  # Fallback to default
            except Exception as e:
                logger.error(f"Error validating tenant: {e}")
                tenant_id = "ccs"  # Fallback to default
            finally:
                db.close()
        
        # Store tenant in request state (will be None for authenticated routes until JWT is validated)
        request.state.tenant_id = tenant_id
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

