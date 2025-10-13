#!/usr/bin/env python3
"""
Celery tasks for campaign processing
All long-running campaign operations should be executed as Celery tasks
"""
import asyncio
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.leads import LeadGenerationCampaign
from app.services.lead_generation_service import LeadGenerationService


@celery_app.task(
    name="run_campaign",
    bind=True,
    max_retries=3,
    default_retry_delay=300  # 5 minutes
)
def run_campaign_task(self, campaign_id: str, tenant_id: str):
    """
    Celery task to run lead generation campaign in background
    
    Args:
        self: Celery task instance (bind=True)
        campaign_id: Campaign UUID
        tenant_id: Tenant UUID
    
    Returns:
        dict: Task result with success status and details
    """
    print(f"\n{'='*80}")
    print(f"🚀 CELERY TASK STARTED: run_campaign")
    print(f"Campaign ID: {campaign_id}")
    print(f"Tenant ID: {tenant_id}")
    print(f"Task ID: {self.request.id}")
    print(f"{'='*80}\n")
    
    # Create new database session for this task
    db = SessionLocal()
    
    try:
        # Get campaign
        campaign = db.query(LeadGenerationCampaign).filter_by(
            id=campaign_id
        ).first()
        
        if not campaign:
            error_msg = f"Campaign {campaign_id} not found"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'campaign_id': campaign_id
            }
        
        print(f"✓ Campaign found: {campaign.name}")
        print(f"   Type: {campaign.prompt_type}")
        print(f"   Location: {campaign.postcode} (±{campaign.distance_miles} miles)")
        print(f"   Target: {campaign.max_results} leads")
        
        # Initialize lead generation service
        service = LeadGenerationService(db, tenant_id)
        
        # Run lead generation (async function, so use asyncio.run)
        print(f"\n🔍 Starting lead generation process...")
        result = asyncio.run(service.generate_leads(campaign))
        
        if result['success']:
            print(f"\n{'='*80}")
            print(f"✅ CAMPAIGN COMPLETED SUCCESSFULLY!")
            print(f"{'='*80}")
            print(f"📊 Results:")
            print(f"   Total Found: {result.get('total_found', 0)}")
            print(f"   Leads Created: {result.get('leads_created', 0)}")
            print(f"   Duplicates Skipped: {result.get('duplicates_skipped', 0)}")
            print(f"{'='*80}\n")
            
            return {
                'success': True,
                'campaign_id': campaign_id,
                'campaign_name': campaign.name,
                'total_found': result.get('total_found', 0),
                'leads_created': result.get('leads_created', 0),
                'duplicates_skipped': result.get('duplicates_skipped', 0)
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"\n{'='*80}")
            print(f"❌ CAMPAIGN FAILED")
            print(f"{'='*80}")
            print(f"Error: {error_msg}")
            print(f"{'='*80}\n")
            
            # Retry if it's a transient error
            if 'timeout' in error_msg.lower() or 'connection' in error_msg.lower():
                print(f"⏰ Transient error detected, scheduling retry...")
                raise self.retry(exc=Exception(error_msg))
            
            return {
                'success': False,
                'error': error_msg,
                'campaign_id': campaign_id,
                'campaign_name': campaign.name
            }
    
    except Exception as e:
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        print(f"\n{'='*80}")
        print(f"💥 CAMPAIGN TASK CRASHED")
        print(f"{'='*80}")
        print(f"Error: {error_msg}")
        print(f"{'='*80}\n")
        
        import traceback
        traceback.print_exc()
        
        # Update campaign status to failed
        try:
            campaign = db.query(LeadGenerationCampaign).filter_by(
                id=campaign_id
            ).first()
            if campaign:
                from app.models.leads import LeadGenerationStatus
                from datetime import datetime
                campaign.status = LeadGenerationStatus.FAILED
                campaign.completed_at = datetime.utcnow()
                campaign.errors_count += 1
                db.commit()
        except Exception as db_error:
            print(f"Failed to update campaign status: {db_error}")
        
        # Retry on exception (up to max_retries)
        raise self.retry(exc=e)
    
    finally:
        db.close()


@celery_app.task(name="test_celery")
def test_celery_task(message: str = "Hello from Celery!"):
    """Simple test task to verify Celery is working"""
    print(f"✅ Celery test task executed: {message}")
    return {"success": True, "message": message}

