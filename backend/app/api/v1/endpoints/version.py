#!/usr/bin/env python3
"""
Version information endpoint

IMPORTANT: Version management is centralized. See VERSION_MANAGEMENT.md for details.
The VERSION file in the project root is the single source of truth.
"""

from fastapi import APIRouter
from pydantic import BaseModel
import os
from app.core.config import settings

router = APIRouter()


class VersionResponse(BaseModel):
    version: str
    build_date: str = None
    build_hash: str = None
    environment: str = "development"


@router.get("/version", response_model=VersionResponse, tags=["version"])
async def get_version_info():
    """
    Get application version information
    
    Version is injected via settings.VERSION (from config.py or APP_VERSION env var)
    """
    return VersionResponse(
        version=os.getenv('APP_VERSION', settings.VERSION),
        build_date=os.getenv('BUILD_DATE', ''),
        build_hash=os.getenv('BUILD_HASH', ''),
        environment=os.getenv('ENVIRONMENT', settings.ENVIRONMENT)
    )

