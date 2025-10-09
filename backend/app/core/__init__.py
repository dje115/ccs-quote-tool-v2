"""
Core functionality for CCS Quote Tool v2
"""

from .config import settings
from .database import get_db, get_async_db

__all__ = ["settings", "get_db", "get_async_db"]

