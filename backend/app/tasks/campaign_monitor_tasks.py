"""
Campaign Monitor Tasks

Periodic tasks for monitoring campaign health and cleaning up stuck campaigns.
"""

from celery import Celery
from celery.schedules import crontab
from datetime import datetime, timezone
import logging

from app.core.celery_app import celery_app
from app.services.campaign_monitor_service import get_campaign_monitor

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def monitor_campaign_health(self):
    """
    Periodic task to monitor campaign health and clean up stuck campaigns.
    This should run every 5 minutes.
    """
    logger.info("🔍 Starting periodic campaign health monitoring...")
    
    try:
        # Get the campaign monitor service
        monitor = get_campaign_monitor(self.app)
        
        if not monitor:
            logger.error("❌ Campaign monitor not available")
            return {'error': 'Campaign monitor not available'}
        
        # Run comprehensive monitoring
        results = monitor.monitor_and_cleanup()
        
        # Log results
        health_stats = results.get('health_stats', {})
        stuck_campaigns = results.get('stuck_campaigns_detected', [])
        cleanup_results = results.get('cleanup_results', {})
        
        logger.info(f"📊 Campaign Health Monitor Results:")
        logger.info(f"   Health Score: {health_stats.get('health_score', 'N/A')}/100")
        logger.info(f"   Running: {health_stats.get('running_campaigns', 0)}")
        logger.info(f"   Completed: {health_stats.get('completed_campaigns', 0)}")
        logger.info(f"   Failed: {health_stats.get('failed_campaigns', 0)}")
        logger.info(f"   Stuck: {health_stats.get('stuck_campaigns', 0)}")
        logger.info(f"   Cleaned up: {cleanup_results.get('cleaned_up', 0)} campaigns")
        
        if stuck_campaigns:
            logger.warning(f"⚠️ Found {len(stuck_campaigns)} stuck campaigns:")
            for campaign in stuck_campaigns:
                logger.warning(f"   - {campaign['name']} (running {campaign['duration_hours']}h)")
        
        return results
        
    except Exception as e:
        logger.error(f"💥 Error in campaign health monitoring: {str(e)}")
        return {'error': str(e)}


@celery_app.task(bind=True)
def force_cleanup_stuck_campaigns(self, max_duration_hours: int = 4):
    """
    Force cleanup of campaigns that have been running for too long.
    This can be called manually or on a schedule.
    """
    logger.info(f"🚨 Force cleaning up campaigns running longer than {max_duration_hours} hours...")
    
    try:
        monitor = get_campaign_monitor(self.app)
        
        if not monitor:
            logger.error("❌ Campaign monitor not available")
            return {'error': 'Campaign monitor not available'}
        
        results = monitor.force_fail_stuck_campaigns(max_duration_hours)
        
        logger.info(f"✅ Force cleanup completed: {results['force_failed']}/{results['total_found']} campaigns force-failed")
        
        if results['errors']:
            logger.warning(f"⚠️ Force cleanup errors: {results['errors']}")
        
        return results
        
    except Exception as e:
        logger.error(f"💥 Error in force cleanup: {str(e)}")
        return {'error': str(e)}


@celery_app.task(bind=True)
def get_campaign_health_report(self):
    """
    Generate a comprehensive campaign health report.
    """
    logger.info("📋 Generating campaign health report...")
    
    try:
        monitor = get_campaign_monitor(self.app)
        
        if not monitor:
            logger.error("❌ Campaign monitor not available")
            return {'error': 'Campaign monitor not available'}
        
        # Get health stats
        health_stats = monitor.get_campaign_health_stats()
        
        # Get stuck campaigns
        stuck_campaigns = monitor.detect_stuck_campaigns()
        
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'health_stats': health_stats,
            'stuck_campaigns': stuck_campaigns,
            'recommendations': _generate_recommendations(health_stats, stuck_campaigns)
        }
        
        logger.info(f"📊 Health Report Generated:")
        logger.info(f"   Health Score: {health_stats.get('health_score', 'N/A')}/100")
        logger.info(f"   Recommendations: {len(report['recommendations'])}")
        
        return report
        
    except Exception as e:
        logger.error(f"💥 Error generating health report: {str(e)}")
        return {'error': str(e)}


def _generate_recommendations(health_stats: dict, stuck_campaigns: list) -> list:
    """Generate recommendations based on campaign health"""
    recommendations = []
    
    health_score = health_stats.get('health_score', 0)
    stuck_count = health_stats.get('stuck_campaigns', 0)
    failed_count = health_stats.get('failed_campaigns', 0)
    
    if health_score < 70:
        recommendations.append("⚠️ Campaign health score is low - investigate failed campaigns")
    
    if stuck_count > 0:
        recommendations.append(f"🚨 {stuck_count} campaigns are stuck - consider force cleanup")
    
    if failed_count > 5:
        recommendations.append("🔍 High number of failed campaigns - check API keys and external services")
    
    if stuck_count == 0 and health_score > 90:
        recommendations.append("✅ Campaign system is healthy - no action needed")
    
    return recommendations


# Celery Beat schedule for periodic monitoring
CELERYBEAT_SCHEDULE = {
    'monitor-campaign-health': {
        'task': 'app.tasks.campaign_monitor_tasks.monitor_campaign_health',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'generate-health-report': {
        'task': 'app.tasks.campaign_monitor_tasks.get_campaign_health_report',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
    'force-cleanup-stuck-campaigns': {
        'task': 'app.tasks.campaign_monitor_tasks.force_cleanup_stuck_campaigns',
        'schedule': crontab(minute=0, hour=2),  # Daily at 2 AM
        'args': (4,)  # 4 hours max duration
    },
}
