"""
Campaign Monitor Service

This service provides monitoring and cleanup functionality for lead generation campaigns.
It handles stuck campaigns, timeout detection, and automatic recovery.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from celery import Celery
import logging

from app.core.database import SessionLocal
from app.models.leads import LeadGenerationCampaign, LeadGenerationStatus

logger = logging.getLogger(__name__)


class CampaignMonitorService:
    """Service for monitoring and managing campaign health"""
    
    def __init__(self, celery_app: Celery):
        self.celery_app = celery_app
    
    def _get_db_session(self):
        """Get a database session"""
        return SessionLocal()
    
    def cleanup_stuck_campaigns_on_startup(self) -> Dict[str, Any]:
        """
        Clean up campaigns that were stuck in RUNNING status when the worker restarted.
        This should be called when the Celery worker starts up.
        """
        logger.info("🧹 Starting campaign cleanup on worker startup...")
        
        db = self._get_db_session()
        try:
            # Find campaigns stuck in RUNNING status for more than 30 minutes OR with no task_id
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=30)
            
            stuck_campaigns = db.query(LeadGenerationCampaign).filter(
                LeadGenerationCampaign.status == LeadGenerationStatus.RUNNING,
                or_(
                    LeadGenerationCampaign.updated_at < cutoff_time,
                    LeadGenerationCampaign.task_id.is_(None)  # No task ID = never started properly
                )
            ).all()
            
            results = {
                'total_found': len(stuck_campaigns),
                'cleaned_up': 0,
                'errors': []
            }
            
            for campaign in stuck_campaigns:
                try:
                    logger.warning(f"🔧 Cleaning up stuck campaign: {campaign.name} (ID: {campaign.id})")
                    
                    # Mark as FAILED with reason
                    campaign.status = LeadGenerationStatus.FAILED
                    campaign.ai_analysis_summary = f"Campaign failed due to worker restart. Original status: RUNNING, Last updated: {campaign.updated_at}"
                    campaign.updated_at = datetime.now(timezone.utc)
                    
                    db.commit()
                    results['cleaned_up'] += 1
                    
                    logger.info(f"✅ Successfully cleaned up campaign: {campaign.name}")
                    
                except Exception as e:
                    error_msg = f"Failed to clean up campaign {campaign.name}: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    results['errors'].append(error_msg)
            
            logger.info(f"🎯 Campaign cleanup completed: {results['cleaned_up']}/{results['total_found']} campaigns cleaned")
            return results
            
        except Exception as e:
            logger.error(f"💥 Critical error during campaign cleanup: {str(e)}")
            return {'total_found': 0, 'cleaned_up': 0, 'errors': [str(e)]}
        finally:
            db.close()
    
    def detect_stuck_campaigns(self) -> List[Dict[str, Any]]:
        """
        Detect campaigns that appear to be stuck (running too long without updates)
        """
        db = self._get_db_session()
        try:
            # Campaigns running for more than 2 hours without updates
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=2)
            
            stuck_campaigns = db.query(LeadGenerationCampaign).filter(
                LeadGenerationCampaign.status == LeadGenerationStatus.RUNNING,
                LeadGenerationCampaign.updated_at < cutoff_time
            ).all()
            
            results = []
            for campaign in stuck_campaigns:
                duration = datetime.now(timezone.utc) - campaign.created_at
                results.append({
                    'id': str(campaign.id),
                    'name': campaign.name,
                    'status': campaign.status.value,
                    'created_at': campaign.created_at.isoformat(),
                    'updated_at': campaign.updated_at.isoformat(),
                    'duration_hours': round(duration.total_seconds() / 3600, 2),
                    'tenant_id': campaign.tenant_id
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error detecting stuck campaigns: {str(e)}")
            return []
        finally:
            db.close()
    
    def force_fail_stuck_campaigns(self, max_duration_hours: int = 4) -> Dict[str, Any]:
        """
        Force fail campaigns that have been running for too long
        """
        logger.info(f"🚨 Force failing campaigns running longer than {max_duration_hours} hours...")
        
        db = self._get_db_session()
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_duration_hours)
            
            stuck_campaigns = db.query(LeadGenerationCampaign).filter(
                LeadGenerationCampaign.status == LeadGenerationStatus.RUNNING,
                LeadGenerationCampaign.created_at < cutoff_time
            ).all()
            
            results = {
                'total_found': len(stuck_campaigns),
                'force_failed': 0,
                'errors': []
            }
            
            for campaign in stuck_campaigns:
                try:
                    logger.warning(f"⚠️ Force failing long-running campaign: {campaign.name}")
                    
                    campaign.status = LeadGenerationStatus.FAILED
                    campaign.ai_analysis_summary = f"Campaign force-failed due to timeout (running > {max_duration_hours}h). Original status: RUNNING"
                    campaign.updated_at = datetime.now(timezone.utc)
                    
                    db.commit()
                    results['force_failed'] += 1
                    
                    logger.info(f"✅ Force failed campaign: {campaign.name}")
                    
                except Exception as e:
                    error_msg = f"Failed to force fail campaign {campaign.name}: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    results['errors'].append(error_msg)
            
            return results
            
        except Exception as e:
            logger.error(f"Error force failing campaigns: {str(e)}")
            return {'total_found': 0, 'force_failed': 0, 'errors': [str(e)]}
        finally:
            db.close()
    
    def get_campaign_health_stats(self) -> Dict[str, Any]:
        """
        Get overall health statistics for campaigns
        """
        db = self._get_db_session()
        try:
            total_campaigns = db.query(LeadGenerationCampaign).count()
            
            running_campaigns = db.query(LeadGenerationCampaign).filter(
                LeadGenerationCampaign.status == LeadGenerationStatus.RUNNING
            ).count()
            
            completed_campaigns = db.query(LeadGenerationCampaign).filter(
                LeadGenerationCampaign.status == LeadGenerationStatus.COMPLETED
            ).count()
            
            failed_campaigns = db.query(LeadGenerationCampaign).filter(
                LeadGenerationCampaign.status == LeadGenerationStatus.FAILED
            ).count()
            
            # Check for stuck campaigns
            stuck_campaigns = len(self.detect_stuck_campaigns())
            
            return {
                'total_campaigns': total_campaigns,
                'running_campaigns': running_campaigns,
                'completed_campaigns': completed_campaigns,
                'failed_campaigns': failed_campaigns,
                'stuck_campaigns': stuck_campaigns,
                'health_score': self._calculate_health_score(
                    total_campaigns, completed_campaigns, failed_campaigns, stuck_campaigns
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign health stats: {str(e)}")
            return {}
        finally:
            db.close()
    
    def _calculate_health_score(self, total: int, completed: int, failed: int, stuck: int) -> float:
        """Calculate a health score for campaigns (0-100)"""
        if total == 0:
            return 100.0
        
        # Base score from completion rate
        completion_rate = (completed / total) * 70
        
        # Penalty for failures (max 20 points)
        failure_penalty = min((failed / total) * 20, 20)
        
        # Penalty for stuck campaigns (max 10 points)
        stuck_penalty = min((stuck / total) * 10, 10)
        
        health_score = max(0, completion_rate - failure_penalty - stuck_penalty)
        return round(health_score, 1)
    
    def monitor_and_cleanup(self) -> Dict[str, Any]:
        """
        Comprehensive monitoring and cleanup operation
        """
        logger.info("🔍 Starting comprehensive campaign monitoring...")
        
        results = {
            'health_stats': self.get_campaign_health_stats(),
            'stuck_campaigns_detected': self.detect_stuck_campaigns(),
            'cleanup_results': self.cleanup_stuck_campaigns_on_startup(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Log summary
        health_stats = results['health_stats']
        if health_stats:
            logger.info(f"📊 Campaign Health: {health_stats['health_score']}/100 "
                       f"(Running: {health_stats['running_campaigns']}, "
                       f"Completed: {health_stats['completed_campaigns']}, "
                       f"Failed: {health_stats['failed_campaigns']}, "
                       f"Stuck: {health_stats['stuck_campaigns']})")
        
        return results


# Global instance for use in other modules
campaign_monitor = None

def get_campaign_monitor(celery_app: Celery = None) -> CampaignMonitorService:
    """Get or create the global campaign monitor instance"""
    global campaign_monitor
    if campaign_monitor is None and celery_app is not None:
        campaign_monitor = CampaignMonitorService(celery_app)
    return campaign_monitor
