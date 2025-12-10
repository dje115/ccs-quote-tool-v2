#!/usr/bin/env python3
"""
CSRF Protection utilities

SECURITY: Implements CSRF token generation and validation for state-changing operations
"""

import secrets
from typing import Optional
from fastapi import Request, HTTPException, status
from app.core.config import settings
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings


class CSRFProtection:
    """
    CSRF protection utility
    
    Generates and validates CSRF tokens for state-changing operations
    """
    
    @staticmethod
    def generate_token() -> str:
        """Generate a new CSRF token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def get_token_from_request(request: Request) -> Optional[str]:
        """
        Get CSRF token from request
        
        Checks:
        1. X-CSRF-Token header (preferred)
        2. csrf_token cookie
        3. csrf_token in form data (for form submissions)
        """
        # Try header first
        token = request.headers.get("X-CSRF-Token")
        if token:
            return token
        
        # Try cookie
        token = request.cookies.get("csrf_token")
        if token:
            return token
        
        # Try form data (for multipart/form-data)
        if hasattr(request, "_form") and request._form:
            form = request._form
            if "csrf_token" in form:
                return form["csrf_token"]
        
        return None
    
    @staticmethod
    def validate_token(request: Request, expected_token: Optional[str] = None) -> bool:
        """
        Validate CSRF token from request
        
        Args:
            request: FastAPI request object
            expected_token: Expected token value (if None, gets from session/cookie)
            
        Returns:
            True if token is valid, False otherwise
        """
        # Get token from request
        provided_token = CSRFProtection.get_token_from_request(request)
        
        if not provided_token:
            return False
        
        # If expected_token is provided, compare directly
        if expected_token:
            return secrets.compare_digest(provided_token, expected_token)
        
        # Otherwise, compare with cookie value (token should match cookie)
        cookie_token = request.cookies.get("csrf_token")
        if cookie_token:
            return secrets.compare_digest(provided_token, cookie_token)
        
        return False


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware
    
    SECURITY: Validates CSRF tokens for state-changing operations (POST, PUT, DELETE, PATCH)
    Excludes safe methods (GET, HEAD, OPTIONS) and public endpoints
    """
    
    # Safe HTTP methods that don't need CSRF protection
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
    
    # Public endpoints that don't require CSRF protection
    PUBLIC_ENDPOINTS = [
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/auth/csrf-token",
        "/api/v1/auth/me",  # Allow checking current user (used by admin portal)
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF check for safe methods
        if request.method in self.SAFE_METHODS:
            response = await call_next(request)
            return response
        
            # Skip CSRF check for public endpoints
            # Check if path starts with any public endpoint OR if it's an admin endpoint
            is_public = any(request.url.path.startswith(endpoint) for endpoint in self.PUBLIC_ENDPOINTS)
            is_admin_endpoint = request.url.path.startswith("/api/v1/admin/")
            
            if is_public or is_admin_endpoint:
            response = await call_next(request)
            return response
        
        # For state-changing operations, validate CSRF token
        provided_token = CSRFProtection.get_token_from_request(request)
        
        if not provided_token:
            # No token provided - reject request
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token required for this operation"
            )
        
        # Validate token matches cookie
        if not CSRFProtection.validate_token(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid CSRF token"
            )
        
        response = await call_next(request)
        
        # Set CSRF token in cookie if not present (for subsequent requests)
        if "csrf_token" not in request.cookies:
            csrf_token = CSRFProtection.generate_token()
            response.set_cookie(
                key="csrf_token",
                value=csrf_token,
                httponly=False,  # JavaScript needs to read this for X-CSRF-Token header
                secure=settings.ENVIRONMENT == "production",
                samesite="strict",  # Strict SameSite for CSRF protection
                max_age=3600,  # 1 hour
                path="/"
            )
        
        return response

