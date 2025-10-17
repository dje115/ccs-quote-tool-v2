#!/usr/bin/env python3
"""
CCS Quote Tool v2 - FastAPI Main Application
Multi-tenant SaaS CRM and Quoting Platform
"""

from fastapi import FastAPI, Request
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
from app.core.middleware import TenantMiddleware, LoggingMiddleware
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting CCS Quote Tool v2...")
    
    # Initialize database
    await init_db()
    print("✅ Database initialized")
    
    # Initialize Redis
    await init_redis()
    print("✅ Redis initialized")
    
    # Initialize Celery
    init_celery()
    print("✅ Celery initialized")
    
    # Cleanup any stuck AI analysis tasks from previous runs
    from app.startup_cleanup import cleanup_stuck_ai_tasks
    cleanup_stuck_ai_tasks()
    
    print("🎉 CCS Quote Tool v2 is ready!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down CCS Quote Tool v2...")


# Create FastAPI application
app = FastAPI(
    title="CCS Quote Tool v2 API",
    description="Multi-tenant SaaS CRM and Quoting Platform with AI-powered features",
    version="2.6.0",
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

# Add custom middleware
app.add_middleware(TenantMiddleware)
app.add_middleware(LoggingMiddleware)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CCS Quote Tool v2 API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": "2025-10-09T21:45:00Z"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.ENVIRONMENT == "development" else "Something went wrong",
            "path": str(request.url)
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
