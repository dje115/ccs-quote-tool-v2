#!/usr/bin/env python3
"""
Celery configuration for background tasks

DEPRECATED: This module is kept for backward compatibility.
All Celery configuration is now in app.core.celery_app.

This module re-exports celery_app and init_celery from celery_app.py
to maintain compatibility with existing imports.
"""

# Import from consolidated celery_app module
from app.core.celery_app import celery_app

# Re-export for backward compatibility
__all__ = ['celery_app', 'init_celery']


def init_celery():
    """
    Initialize Celery
    
    This function is kept for backward compatibility.
    The actual Celery app is initialized in celery_app.py.
    """
    # Celery app is already initialized in celery_app.py
    # Just return it for compatibility
    return celery_app


# Task decorators (for backward compatibility)
def task(*args, **kwargs):
    """Celery task decorator (re-exported from celery_app)"""
    return celery_app.task(*args, **kwargs)

