"""
Campaign Signal Handlers

This module handles Celery signals to automatically clean up stuck campaigns
when workers restart or tasks fail.
"""

import logging
from celery import Celery
from celery.signals import worker_ready, worker_shutdown, task_failure

from app.services.campaign_monitor_service import get_campaign_monitor

logger = logging.getLogger(__name__)


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """
    Called when a Celery worker is ready to start processing tasks.
    This is the perfect time to clean up any campaigns that were stuck
    when the worker was restarted.
    """
    logger.info("🚀 Celery worker is ready - starting campaign cleanup...")
    
    try:
        # Get the campaign monitor service
        monitor = get_campaign_monitor(sender)
        
        if monitor:
            # Clean up stuck campaigns from previous worker session
            cleanup_results = monitor.cleanup_stuck_campaigns_on_startup()
            
            logger.info(f"✅ Worker startup cleanup completed: "
                       f"{cleanup_results['cleaned_up']}/{cleanup_results['total_found']} "
                       f"campaigns cleaned up")
            
            if cleanup_results['errors']:
                logger.warning(f"⚠️ Cleanup errors: {cleanup_results['errors']}")
        else:
            logger.warning("⚠️ Campaign monitor not available during worker startup")
            
    except Exception as e:
        logger.error(f"💥 Error during worker startup cleanup: {str(e)}")


@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """
    Called when a Celery worker is shutting down.
    This gives us a chance to clean up any running campaigns.
    """
    logger.info("🛑 Celery worker is shutting down - cleaning up running campaigns...")
    
    try:
        monitor = get_campaign_monitor(sender)
        
        if monitor:
            # Force fail any campaigns that are still running
            # (they will be restarted when the worker comes back up)
            cleanup_results = monitor.force_fail_stuck_campaigns(max_duration_hours=0)
            
            logger.info(f"✅ Worker shutdown cleanup completed: "
                       f"{cleanup_results['force_failed']} campaigns force-failed")
            
            if cleanup_results['errors']:
                logger.warning(f"⚠️ Shutdown cleanup errors: {cleanup_results['errors']}")
        else:
            logger.warning("⚠️ Campaign monitor not available during worker shutdown")
            
    except Exception as e:
        logger.error(f"💥 Error during worker shutdown cleanup: {str(e)}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwargs):
    """
    Called when a Celery task fails.
    We can use this to detect and handle campaign task failures.
    """
    # Only handle lead generation campaign task failures
    if sender and 'run_lead_generation_campaign' in str(sender):
        logger.error(f"💥 Lead generation campaign task failed: {task_id}")
        logger.error(f"Exception: {exception}")
        
        try:
            # Try to mark the campaign as failed in the database
            from app.core.database import SessionLocal
            from app.models.leads import LeadGenerationCampaign, LeadGenerationStatus
            
            db = SessionLocal()
            
            # Find campaign by task_id (we'd need to store this in the campaign model)
            # For now, we'll log the failure for manual investigation
            logger.warning(f"🔍 Manual investigation needed for failed campaign task: {task_id}")
            
        except Exception as e:
            logger.error(f"❌ Error handling campaign task failure: {str(e)}")


def setup_campaign_monitoring(celery_app: Celery):
    """
    Set up campaign monitoring for the given Celery app.
    This should be called when initializing the Celery app.
    """
    logger.info("🔧 Setting up campaign monitoring...")
    
    try:
        # Initialize the campaign monitor
        monitor = get_campaign_monitor(celery_app)
        
        if monitor:
            logger.info("✅ Campaign monitoring initialized successfully")
        else:
            logger.warning("⚠️ Failed to initialize campaign monitoring")
            
    except Exception as e:
        logger.error(f"💥 Error setting up campaign monitoring: {str(e)}")
