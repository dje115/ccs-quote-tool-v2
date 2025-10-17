#!/usr/bin/env python3
"""
Celery configuration for background task processing
Used for long-running operations like lead generation campaigns
"""
from celery import Celery
import os

# Initialize Celery
celery_app = Celery(
    "ccs_quote_tool",
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    include=[
        "app.tasks.campaign_tasks", 
        "app.tasks.activity_tasks", 
        "app.tasks.lead_generation_tasks",
        "app.tasks.campaign_monitor_tasks"
    ]  # Import task modules
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=7200,  # 2 hours max for any task
    task_soft_time_limit=6900,  # 1h 55m soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (prevent memory leaks)
    task_acks_late=True,  # Acknowledge tasks after completion
    task_reject_on_worker_lost=True,  # Retry if worker dies
    result_expires=3600,  # Keep results for 1 hour
    beat_schedule={
        'monitor-campaign-health': {
            'task': 'app.tasks.campaign_monitor_tasks.monitor_campaign_health',
            'schedule': 300.0,  # Every 5 minutes
        },
        'generate-health-report': {
            'task': 'app.tasks.campaign_monitor_tasks.get_campaign_health_report',
            'schedule': 21600.0,  # Every 6 hours
        },
        'force-cleanup-stuck-campaigns': {
            'task': 'app.tasks.campaign_monitor_tasks.force_cleanup_stuck_campaigns',
            'schedule': 86400.0,  # Daily
            'args': (4,)  # 4 hours max duration
        },
    }
)

# Optional: Configure task routes for different queues
celery_app.conf.task_routes = {
    "app.tasks.campaign_tasks.*": {"queue": "campaigns"},
    "app.tasks.email_tasks.*": {"queue": "emails"},
}

# Setup campaign monitoring signals
from app.tasks.campaign_signals import setup_campaign_monitoring
setup_campaign_monitoring(celery_app)

if __name__ == "__main__":
    celery_app.start()

