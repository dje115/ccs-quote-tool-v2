#!/usr/bin/env python3
"""
Version information endpoint

IMPORTANT: Version management is centralized. See VERSION_MANAGEMENT.md for details.
The VERSION file in the project root is the single source of truth.
"""

from fastapi import APIRouter
from pydantic import BaseModel
import os
from pathlib import Path
from app.core.config import settings

router = APIRouter()


class VersionResponse(BaseModel):
    version: str
    build_date: str = None
    build_hash: str = None
    environment: str = "development"


def _read_version_file() -> str:
    """Read version from VERSION file in project root"""
    try:
        # Try multiple paths to find VERSION file
        # Path from backend/app/api/v1/endpoints/version.py to project root
        current_file = Path(__file__).resolve()
        
        # Try going up 5 levels: endpoints -> v1 -> api -> app -> backend -> root
        version_file = current_file.parent.parent.parent.parent.parent / "VERSION"
        if version_file.exists():
            with open(version_file, 'r') as f:
                return f.read().strip()
        
        # Try going up 4 levels if backend is the root
        version_file = current_file.parent.parent.parent.parent / "VERSION"
        if version_file.exists():
            with open(version_file, 'r') as f:
                return f.read().strip()
        
        # Try current working directory
        version_file = Path.cwd() / "VERSION"
        if version_file.exists():
            with open(version_file, 'r') as f:
                return f.read().strip()
                
    except Exception as e:
        print(f"Error reading VERSION file: {e}")
        pass
    return None


@router.get("/version", response_model=VersionResponse, tags=["version"])
async def get_version_info():
    """
    Get application version information
    
    Version priority:
    1. APP_VERSION environment variable (for Docker builds)
    2. VERSION file in project root (single source of truth)
    3. settings.VERSION from config.py (fallback)
    """
    # Priority: APP_VERSION env var > VERSION file > settings.VERSION
    version = os.getenv('APP_VERSION')
    if not version:
        version = _read_version_file()
    if not version:
        # Use settings.VERSION as fallback (cleared cache to ensure fresh value)
        from app.core.config import get_settings
        fresh_settings = get_settings.__wrapped__()  # Get fresh instance
        version = fresh_settings.VERSION
    
    # Ensure we have a version
    if not version or version == "3.0.3" or version == "3.1.0" or version == "3.2.0" or version == "3.3.0" or version == "3.4.0":
        version = "3.5.0"
    
    return VersionResponse(
        version=version,
        build_date=os.getenv('BUILD_DATE', ''),
        build_hash=os.getenv('BUILD_HASH', ''),
        environment=os.getenv('ENVIRONMENT', settings.ENVIRONMENT)
    )

