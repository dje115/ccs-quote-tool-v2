#!/usr/bin/env python3
"""
Celery configuration for background task processing
Used for long-running operations like lead generation campaigns, quote analysis, etc.

CONSOLIDATED: This is the single source of truth for Celery configuration.
All Celery workers and beat schedulers should import from this module.
"""
from celery import Celery
from app.core.config import settings

# Initialize Celery with settings from config
# Use properties that fall back to REDIS_URL if CELERY_BROKER_URL is not set
celery_app = Celery(
    "ccs_quote_tool",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.campaign_tasks", 
        "app.tasks.activity_tasks", 
        "app.tasks.lead_generation_tasks",
        "app.tasks.campaign_monitor_tasks",
        "app.tasks.planning_tasks",
        "app.tasks.contract_renewal_tasks",
        "app.tasks.sla_tasks",
        "app.tasks.quote_tasks",
        "app.tasks.lead_analysis_tasks",
        "app.tasks.lifecycle_automation_tasks"
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
        'check-dormant-customers': {
            'task': 'check_dormant_customers',
            'schedule': 86400.0,  # Every 24 hours (daily)
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
        'check-expiring-contracts': {
            'task': 'contract_renewal.check_expiring_contracts',
            'schedule': 86400.0,  # Daily at midnight
        },
        'process-auto-renewals': {
            'task': 'contract_renewal.process_auto_renewals',
            'schedule': 86400.0,  # Daily at midnight
        },
        'check-sla-violations': {
            'task': 'check_sla_violations',
            'schedule': 3600.0,  # Every hour
        },
        'generate-daily-sla-report': {
            'task': 'generate_sla_compliance_report',
            'schedule': 86400.0,  # Daily at midnight
            'args': (None, 'daily'),  # All tenants, daily report
        },
        'generate-weekly-sla-report': {
            'task': 'generate_sla_compliance_report',
            'schedule': 604800.0,  # Weekly (7 days)
            'args': (None, 'weekly'),  # All tenants, weekly report
        },
        'generate-monthly-sla-report': {
            'task': 'generate_sla_compliance_report',
            'schedule': 2592000.0,  # Monthly (30 days)
            'args': (None, 'monthly'),  # All tenants, monthly report
        },
        'auto-escalate-sla-violations': {
            'task': 'auto_escalate_sla_violations',
            'schedule': 900.0,  # Every 15 minutes
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

