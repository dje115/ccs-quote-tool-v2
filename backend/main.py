#!/usr/bin/env python3
"""
CCS Quote Tool v2 - FastAPI Main Application
Multi-tenant SaaS CRM and Quoting Platform
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.core.redis import init_redis
from app.core.celery import init_celery
from app.core.middleware import TenantMiddleware, LoggingMiddleware, SecurityHeadersMiddleware
from app.core.csrf import CSRFMiddleware
from app.core.logging import setup_logging, get_logger
from app.api.v1.api import api_router
# Version endpoint is included via api_router, no need to import here

# Setup logging first
setup_logging(level="INFO" if settings.ENVIRONMENT == "production" else "DEBUG")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting CCS Quote Tool v2", extra={'version': APP_VERSION})
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Set up row-level security for tenant isolation
    from app.core.database import setup_row_level_security
    try:
        await setup_row_level_security()
        logger.info("Row-level security configured")
    except Exception as e:
        logger.warning("Could not set up row-level security", extra={'error': str(e)})
        logger.info("Tenant isolation will rely on application-level filtering")
    
    # Initialize Redis
    await init_redis()
    logger.info("Redis initialized")
    
    # Initialize Celery
    init_celery()
    logger.info("Celery initialized")
    
    # Run database seed scripts (idempotent - safe to run multiple times)
    from app.startup.seed_data import run_seed_scripts
    await run_seed_scripts()
    
    # Cleanup any stuck AI analysis tasks from previous runs
    from app.startup_cleanup import cleanup_stuck_ai_tasks
    cleanup_stuck_ai_tasks()
    
    logger.info("CCS Quote Tool v2 is ready")
    
    yield
    
    # Shutdown - cleanup resources
    logger.info("Shutting down CCS Quote Tool v2...")
    
    # Close Redis connections
    from app.core.redis import close_redis
    await close_redis()
    logger.info("Redis connections closed")
    
    # Close EventPublisher Redis connection
    from app.core.events import get_event_publisher
    event_publisher = get_event_publisher()
    await event_publisher.close()
    
    # Close WebSocketManager connections
    from app.core.websocket import get_websocket_manager
    manager = get_websocket_manager()
    await manager.close()
    
    # Close database engine connections
    from app.core.database import engine, async_engine
    engine.dispose()
    await async_engine.dispose()
    logger.info("Database connections closed")
    
    logger.info("Cleanup complete")


# Get version from settings (which reads from VERSION file or APP_VERSION env var)
APP_VERSION = settings.VERSION

# Create FastAPI application
app = FastAPI(
    title="CCS Quote Tool v2 API",
    description="Multi-tenant SaaS CRM and Quoting Platform with AI-powered features",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
)

# Add custom middleware (order matters - security headers first)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)  # Rate limiting before CSRF (fail fast)
app.add_middleware(CSRFMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(LoggingMiddleware)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CCS Quote Tool v2 API",
        "version": APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTPException handler - handles validation errors, auth errors, etc."""
    from app.core.error_handler import handle_http_exception
    
    # Get the origin from the request
    origin = request.headers.get("origin")
    
    # Check if origin is allowed
    allowed_origins = settings.CORS_ORIGINS
    if origin and origin in allowed_origins:
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    else:
        headers = {}
    
    # Use error handler utility for consistent formatting
    error_response = handle_http_exception(exc, request)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=headers
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with environment-aware error messages"""
    from fastapi import HTTPException
    from app.core.error_handler import create_error_response
    
    # Don't handle HTTPException here - it's handled above
    if isinstance(exc, HTTPException):
        raise exc
    
    # Get the origin from the request
    origin = request.headers.get("origin")
    
    # Check if origin is allowed
    allowed_origins = settings.CORS_ORIGINS
    if origin and origin in allowed_origins:
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    else:
        headers = {}
    
    # Create error response using error handler utility
    error_response = create_error_response(
        error=exc,
        status_code=500,
        default_message="An internal server error occurred",
        request=request
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response,
        headers=headers
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
