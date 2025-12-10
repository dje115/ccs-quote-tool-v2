"""
Celery tasks for planning application campaigns
"""

import asyncio
from typing import Dict, Any
from datetime import datetime, timezone

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.planning_service import PlanningApplicationService
from app.models.planning import PlanningApplicationCampaign, PlanningCampaignStatus


@celery_app.task(
    name="planning.run_campaign",
    bind=True,
    max_retries=3,
    default_retry_delay=300  # 5 minutes
)
def run_planning_campaign_task(self, campaign_id: str, tenant_id: str):
    """
    Celery task to run planning application campaign in background
    
    Args:
        self: Celery task instance (bind=True)
        campaign_id: Planning campaign UUID
        tenant_id: Tenant UUID
    
    Returns:
        dict: Task result with success status and details
    """
    print(f"\n{'='*80}")
    print(f"🚀 PLANNING CELERY TASK STARTED: run_planning_campaign")
    print(f"Campaign ID: {campaign_id}")
    print(f"Tenant ID: {tenant_id}")
    print(f"Task ID: {self.request.id}")
    print(f"{'='*80}\n")
    
    # Create new database session for this task
    db = SessionLocal()
    
    try:
        # Get planning campaign
        campaign = db.query(PlanningApplicationCampaign).filter(
            PlanningApplicationCampaign.id == campaign_id
        ).first()
        
        if not campaign:
            error_msg = f"Planning campaign {campaign_id} not found"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'campaign_id': campaign_id
            }
        
        print(f"✓ Planning campaign found: {campaign.name}")
        print(f"   County: {campaign.county}")
        print(f"   AI Analysis: {campaign.enable_ai_analysis}")
        print(f"   Max AI Analysis: {campaign.max_ai_analysis_per_run}")
        
        # Update campaign status to running
        campaign.status = PlanningCampaignStatus.ACTIVE
        campaign.task_id = self.request.id  # Store Celery task ID for tracking
        campaign.last_run_at = datetime.now(timezone.utc)
        db.commit()
        
        # Publish started event
        from app.core.events import get_event_publisher
        event_publisher = get_event_publisher()
        event_publisher.publish_campaign_started_sync(
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            campaign_name=campaign.name,
            task_id=self.request.id
        )
        
        # Initialize planning service
        service = PlanningApplicationService(db, tenant_id)
        
        # Run planning campaign using async bridge (safe for Celery tasks)
        from app.core.async_bridge import run_async_safe
        print(f"\n🔍 Starting planning campaign process...")
        result = run_async_safe(service.run_campaign(campaign_id))
        
        # The run_campaign method returns a dict with keys: total_found, new_applications, ai_analyzed
        # If it throws an exception, we catch it in the outer try/except block
        if isinstance(result, dict) and 'total_found' in result:
            print(f"\n{'='*80}")
            print(f"✅ PLANNING CAMPAIGN COMPLETED SUCCESSFULLY")
            print(f"Campaign: {campaign.name}")
            print(f"Total found: {result.get('total_found', 0)}")
            print(f"New applications: {result.get('new_applications', 0)}")
            print(f"AI analyzed: {result.get('ai_analyzed', 0)}")
            print(f"{'='*80}\n")
            
            # Update campaign status to completed
            campaign.status = PlanningCampaignStatus.COMPLETED
            campaign.last_run_at = datetime.now(timezone.utc)
            db.commit()
            
            # Publish completed event
            event_publisher.publish_campaign_completed_sync(
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                campaign_name=campaign.name,
                result=result
            )
            
            return {
                'success': True,
                'campaign_id': campaign_id,
                'result': result
            }
        else:
            error_msg = f"Planning campaign failed: Unexpected result format: {result}"
            print(f"❌ {error_msg}")
            
            # Update campaign status to failed
            campaign.status = PlanningCampaignStatus.FAILED
            campaign.last_error = error_msg
            campaign.consecutive_failures += 1
            db.commit()
            
            # Publish failed event
            event_publisher.publish_campaign_failed_sync(
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                campaign_name=campaign.name,
                error=error_msg
            )
            
            return {
                'success': False,
                'error': error_msg,
                'campaign_id': campaign_id
            }
    
    except Exception as e:
        error_msg = f"Planning campaign task failed: {str(e)}"
        print(f"❌ {error_msg}")
        
        # Update campaign status to failed if campaign exists
        if 'campaign' in locals():
            campaign.status = PlanningCampaignStatus.FAILED
            campaign.last_error = error_msg
            campaign.consecutive_failures += 1
            db.commit()
            
            # Publish failed event
            from app.core.events import get_event_publisher
            event_publisher = get_event_publisher()
            event_publisher.publish_campaign_failed_sync(
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                campaign_name=campaign.name,
                error=error_msg
            )
        
        return {
            'success': False,
            'error': error_msg,
            'campaign_id': campaign_id
        }
    
    finally:
        db.close()
