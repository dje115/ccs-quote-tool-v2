#!/usr/bin/env python3
"""
Version information endpoint
"""

from fastapi import APIRouter
from pydantic import BaseModel
import os
from pathlib import Path

router = APIRouter()


class VersionResponse(BaseModel):
    version: str
    build_date: str = None
    build_hash: str = None
    environment: str = "development"


def get_version() -> str:
    """Read version from VERSION file or environment variable"""
    # Try environment variable first (set during Docker build)
    version = os.getenv('APP_VERSION')
    
    if not version:
        # Try reading from VERSION file (relative to backend directory)
        version_file = Path(__file__).parent.parent.parent.parent.parent / 'VERSION'
        if version_file.exists():
            version = version_file.read_text().strip()
        else:
            # Fallback to default
            version = "2.5.0"
    
    return version


@router.get("/version", response_model=VersionResponse, tags=["version"])
async def get_version_info():
    """
    Get application version information
    """
    return VersionResponse(
        version=get_version(),
        build_date=os.getenv('BUILD_DATE', ''),
        build_hash=os.getenv('BUILD_HASH', ''),
        environment=os.getenv('ENVIRONMENT', 'development')
    )

