#!/usr/bin/env python3
"""
Celery configuration for background tasks
"""

from celery import Celery
from app.core.config import settings

# Create Celery application
celery_app = Celery(
    "ccs_quote_tool_v2",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.services"])


def init_celery():
    """Initialize Celery"""
    print("✅ Celery initialized")
    return celery_app


# Task decorators
def task(*args, **kwargs):
    """Celery task decorator"""
    return celery_app.task(*args, **kwargs)

