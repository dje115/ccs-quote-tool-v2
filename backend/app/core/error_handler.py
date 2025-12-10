#!/usr/bin/env python3
"""
Environment-based error handling utility

SECURITY: Prevents information disclosure in production by providing
generic error messages while maintaining detailed logging for debugging.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_error_message(
    error: Exception,
    default_message: str = "An error occurred",
    request: Optional[Request] = None
) -> str:
    """
    Get error message based on environment.
    
    In production: Returns generic message to prevent information disclosure
    In development: Returns detailed error message for debugging
    
    Args:
        error: The exception that occurred
        default_message: Default message to show in production
        request: Optional request object for logging context
        
    Returns:
        Error message appropriate for the environment
    """
    if settings.ENVIRONMENT == "production":
        # Production: Generic message only
        return default_message
    else:
        # Development: Detailed error for debugging
        return str(error)


def log_error(
    error: Exception,
    request: Optional[Request] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log detailed error information for debugging.
    
    This ensures we have full error details in logs even when
    returning generic messages to users.
    
    Args:
        error: The exception that occurred
        request: Optional request object for logging context
        context: Additional context to log
    """
    error_context = {
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    
    if request:
        error_context.update({
            "path": str(request.url.path),
            "method": request.method,
            "client": request.client.host if request.client else None,
        })
    
    if context:
        error_context.update(context)
    
    logger.error(
        "Error occurred",
        extra=error_context,
        exc_info=True
    )


def create_error_response(
    error: Exception,
    status_code: int = 500,
    default_message: str = "An error occurred",
    request: Optional[Request] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create standardized error response.
    
    Args:
        error: The exception that occurred
        status_code: HTTP status code
        default_message: Default message for production
        request: Optional request object
        context: Additional context
        
    Returns:
        Dictionary with error response data
    """
    # Log the error with full details
    log_error(error, request, context)
    
    # Get appropriate message for environment
    message = get_error_message(error, default_message, request)
    
    response = {
        "error": "Internal server error" if status_code >= 500 else "Request error",
        "message": message,
    }
    
    # In development, include error type for debugging
    if settings.ENVIRONMENT != "production":
        response["error_type"] = type(error).__name__
        if request:
            response["path"] = str(request.url.path)
    
    return response


def handle_http_exception(
    exc: HTTPException,
    request: Optional[Request] = None
) -> Dict[str, Any]:
    """
    Handle HTTPException with environment-aware messaging.
    
    Args:
        exc: The HTTPException
        request: Optional request object
        
    Returns:
        Dictionary with error response data (FastAPI format: {"detail": ...})
    """
    # HTTPExceptions are usually safe to show (validation errors, etc.)
    # But we still log them for monitoring
    if request:
        logger.warning(
            "HTTPException raised",
            extra={
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": str(request.url.path),
                "method": request.method,
            }
        )
    
    # Return in FastAPI's expected format (uses "detail" key)
    return {
        "detail": exc.detail
    }

