#!/usr/bin/env python3
"""
Celery tasks for lead analysis background operations

These tasks run asynchronously in Celery workers to avoid blocking the API.
"""

from datetime import datetime, timezone
from typing import Dict, Any
import json

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.leads import Lead
from app.services.lead_intelligence_service import LeadIntelligenceService


@celery_app.task(name='run_lead_analysis', bind=True)
def run_lead_analysis_task(self, lead_id: str, tenant_id: str) -> Dict[str, Any]:
    """
    Background task to run AI analysis for a lead
    
    This task runs asynchronously to avoid blocking the user interface
    while AI performs lead intelligence analysis.
    
    Args:
        lead_id: Lead ID
        tenant_id: Tenant ID
    
    Returns:
        Dict with task results
    """
    db = SessionLocal()
    
    try:
        print(f"\n{'='*80}")
        print(f"🤖 RUNNING LEAD ANALYSIS (Background Task)")
        print(f"Task ID: {self.request.id}")
        print(f"Lead ID: {lead_id}")
        print(f"Tenant ID: {tenant_id}")
        print(f"{'='*80}\n")
        
        # Get lead
        lead = db.query(Lead).filter(
            Lead.id == lead_id,
            Lead.tenant_id == tenant_id,
            Lead.is_deleted == False
        ).first()
        
        if not lead:
            print(f"❌ Lead not found: {lead_id}")
            return {'success': False, 'error': 'Lead not found'}
        
        print(f"📊 Analyzing: {lead.company_name}")
        
        # Publish started event (sync wrapper for Celery)
        from app.core.events import get_event_publisher
        event_publisher = get_event_publisher()
        event_publisher.publish_lead_analysis_started_sync(
            tenant_id=tenant_id,
            lead_id=lead_id,
            task_id=self.request.id,
            lead_name=lead.company_name
        )
        
        # Create intelligence service
        intelligence_service = LeadIntelligenceService(db, tenant_id)
        
        # Run analysis (this is async, but we're in sync context)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        analysis_result = loop.run_until_complete(
            intelligence_service.analyze_lead(lead)
        )
        
        if not analysis_result.get("success", False):
            error_msg = analysis_result.get("error", "Unknown error during analysis")
            print(f"❌ Analysis failed: {error_msg}")
            
            # Publish failure event
            event_publisher.publish_lead_analysis_failed_sync(
                tenant_id=tenant_id,
                lead_id=lead_id,
                task_id=self.request.id,
                lead_name=lead.company_name,
                error=error_msg
            )
            
            return {'success': False, 'error': error_msg}
        
        print(f"✅ Analysis completed successfully")
        print(f"   Conversion Probability: {analysis_result.get('conversion_probability', 'N/A')}%")
        
        # Refresh lead to get updated data
        db.refresh(lead)
        
        # Publish completion event
        event_publisher.publish_lead_analysis_completed_sync(
            tenant_id=tenant_id,
            lead_id=lead_id,
            task_id=self.request.id,
            lead_name=lead.company_name,
            result=analysis_result
        )
        
        return {
            'success': True,
            'analysis': analysis_result,
            'lead_id': lead_id,
            'lead_name': lead.company_name
        }
        
    except Exception as e:
        import traceback
        print(f"❌ Exception in run_lead_analysis task: {e}")
        print(traceback.format_exc())
        
        # Publish failure event
        try:
            from app.core.events import get_event_publisher
            event_publisher = get_event_publisher()
            event_publisher.publish_lead_analysis_failed_sync(
                tenant_id=tenant_id,
                lead_id=lead_id,
                task_id=self.request.id,
                lead_name="Unknown",
                error=str(e)
            )
        except Exception as e2:
            print(f"⚠️  Could not publish failure event: {e2}")
        
        return {'success': False, 'error': str(e)}
    finally:
        db.close()

