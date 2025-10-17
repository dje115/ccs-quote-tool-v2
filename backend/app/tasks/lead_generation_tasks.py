"""
Celery tasks for lead generation campaigns
"""

import json
import traceback
from typing import Dict, Any
from datetime import datetime, timezone

from celery import current_task
from sqlalchemy.orm import sessionmaker

from app.core.celery_app import celery_app
from app.core.config import settings
from app.services.lead_generation_service import LeadGenerationService
from app.models import LeadGenerationCampaign, Lead, LeadGenerationStatus


# Import the existing database session
from app.core.database import SessionLocal


@celery_app.task(bind=True, name="lead_generation.run_campaign")
def run_lead_generation_campaign(self, campaign_data: Dict[str, Any], tenant_id: int):
    """
    Celery task to run a lead generation campaign
    
    Args:
        campaign_data: Dictionary containing campaign parameters
        tenant_id: ID of the tenant running the campaign
    """
    task_id = self.request.id
    db = SessionLocal()
    
    try:
        print(f"🚀 Starting lead generation campaign task: {task_id}")
        print(f"📊 Campaign: {campaign_data.get('name', 'Unknown')}")
        print(f"🏢 Tenant: {tenant_id}")
        
        # Update task progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Initializing campaign...'}
        )
        
        # Initialize lead generation service
        lead_service = LeadGenerationService(db=db, tenant_id=tenant_id)
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Generating leads with AI...'}
        )
        
        # Generate leads using the comprehensive AI system
        # Note: For now, we'll use a synchronous approach
        # In production, you might want to use asyncio.run() or make the service synchronous
        import asyncio
        # Get campaign ID from campaign data
        campaign_id = campaign_data.get('id')
        if not campaign_id:
            raise Exception("Campaign ID not found in campaign data")
        
        # Retrieve and update campaign in database
        campaign = db.query(LeadGenerationCampaign).filter(
            LeadGenerationCampaign.id == campaign_id
        ).first()
        
        if not campaign:
            raise Exception(f"Campaign not found: {campaign_id}")
        
        # Update campaign status to RUNNING and store task ID
        campaign.status = LeadGenerationStatus.RUNNING
        campaign.task_id = task_id  # Store Celery task ID for tracking
        campaign.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        leads = asyncio.run(lead_service.generate_leads(campaign_data))
        
        print(f"✅ Generated {len(leads)} leads")
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 80, 'total': 100, 'status': 'Saving leads to database...'}
        )
        
        # Save leads to database
        saved_leads = []
        for lead_data in leads:
            try:
                # Create lead record
                lead = Lead(
                    campaign_id=campaign_id,
                    company_name=lead_data.get('company_name', ''),
                    website=lead_data.get('website', ''),
                    contact_phone=lead_data.get('contact_phone', ''),
                    contact_email=lead_data.get('contact_email', ''),
                    postcode=lead_data.get('postcode', ''),
                    business_sector=lead_data.get('sector', ''),
                    lead_score=lead_data.get('lead_score', 60),
                    qualification_reason=lead_data.get('quick_telesales_summary', ''),
                    ai_analysis=lead_data.get('ai_business_intelligence', ''),
                    google_maps_data=json.dumps(lead_data.get('google_maps_data', {})),
                    companies_house_data=json.dumps(lead_data.get('companies_house_data', {})),
                    website_data=json.dumps(lead_data.get('website_data', {})),
                    linkedin_data=json.dumps(lead_data.get('linkedin_data', {})),
                    tenant_id=tenant_id,
                    created_at=datetime.now(timezone.utc),
                    status='NEW'
                )
                
                db.add(lead)
                saved_leads.append(lead)
                
            except Exception as e:
                print(f"⚠️ Error saving lead {lead_data.get('company_name', 'Unknown')}: {e}")
                continue
        
        # Commit all leads
        db.commit()
        
        print(f"💾 Saved {len(saved_leads)} leads to database")
        
        # Update campaign status and statistics
        campaign.status = LeadGenerationStatus.COMPLETED
        campaign.leads_created = len(saved_leads)
        campaign.total_found = len(leads)  # Total leads generated (including any that failed to save)
        campaign.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        # Update progress to completion
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Campaign completed successfully!'}
        )
        
        # Return success result
        result = {
            'status': 'SUCCESS',
            'message': f'Campaign completed successfully. Generated {len(saved_leads)} leads.',
            'total_leads': len(saved_leads),
            'campaign_name': campaign_data.get('name', 'Unknown'),
            'completed_at': datetime.now(timezone.utc).isoformat()
        }
        
        print(f"🎉 Campaign task completed: {task_id}")
        return result
        
    except Exception as e:
        error_msg = f"Campaign failed: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        
        # Update campaign status to FAILED
        try:
            campaign.status = LeadGenerationStatus.FAILED
            campaign.updated_at = datetime.now(timezone.utc)
            db.commit()
        except Exception as db_error:
            print(f"⚠️ Failed to update campaign status: {db_error}")
        
        # Update task state to failure
        current_task.update_state(
            state='FAILURE',
            meta={'error': error_msg, 'traceback': traceback.format_exc()}
        )
        
        return {
            'status': 'FAILURE',
            'error': error_msg,
            'traceback': traceback.format_exc()
        }
        
    finally:
        db.close()


@celery_app.task(bind=True, name="lead_generation.test_campaign")
def test_lead_generation_campaign(self, campaign_data: Dict[str, Any], tenant_id: int):
    """
    Test task for lead generation - simplified version for testing
    """
    task_id = self.request.id
    
    try:
        print(f"🧪 Starting test campaign task: {task_id}")
        
        # Simulate some work
        import time
        for i in range(5):
            current_task.update_state(
                state='PROGRESS',
                meta={'current': i * 20, 'total': 100, 'status': f'Test step {i+1}/5...'}
            )
            time.sleep(2)
        
        result = {
            'status': 'SUCCESS',
            'message': 'Test campaign completed successfully',
            'test_data': campaign_data,
            'tenant_id': tenant_id,
            'completed_at': datetime.now(timezone.utc).isoformat()
        }
        
        print(f"✅ Test campaign completed: {task_id}")
        return result
        
    except Exception as e:
        error_msg = f"Test campaign failed: {str(e)}"
        print(f"❌ {error_msg}")
        
        current_task.update_state(
            state='FAILURE',
            meta={'error': error_msg}
        )
        
        return {
            'status': 'FAILURE',
            'error': error_msg
        }
