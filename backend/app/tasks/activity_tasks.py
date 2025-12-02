#!/usr/bin/env python3
"""
Celery tasks for activity-related background operations

These tasks run asynchronously in Celery workers to avoid blocking the API.
"""

from datetime import datetime, timezone
from typing import Dict, Any
import json
import httpx

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.crm import Customer
from app.models.sales import SalesActivity
from app.core.api_keys import get_api_keys
from sqlalchemy import desc


@celery_app.task(name='refresh_customer_suggestions', bind=True)
def refresh_customer_suggestions(self, customer_id: str, tenant_id: str) -> Dict[str, Any]:
    """
    Background task to refresh AI action suggestions for a customer
    
    This task runs asynchronously to avoid blocking the user interface
    while AI generates new suggestions.
    
    Uses ActivityService.generate_action_suggestions() to ensure quote/ticket
    context is properly included in the prompt.
    
    Args:
        customer_id: Customer ID
        tenant_id: Tenant ID
    
    Returns:
        Dict with task results
    """
    db = SessionLocal()
    
    try:
        print(f"\n{'='*80}")
        print(f"🔄 REFRESHING AI SUGGESTIONS (Background Task)")
        print(f"Task ID: {self.request.id}")
        print(f"Customer ID: {customer_id}")
        print(f"Tenant ID: {tenant_id}")
        print(f"{'='*80}\n")
        
        # Get customer
        customer = db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.tenant_id == tenant_id
        ).first()
        
        if not customer:
            print(f"❌ Customer not found: {customer_id}")
            return {'success': False, 'error': 'Customer not found'}
        
        print(f"📊 Analyzing: {customer.company_name}")
        
        # Use ActivityService to generate suggestions (ensures quote/ticket context is included)
        from app.services.activity_service import ActivityService
        
        activity_service = ActivityService(db, tenant_id=tenant_id)
        
        # Run async method in sync context
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        print(f"🤖 Calling ActivityService.generate_action_suggestions()...")
        print(f"[ACTION PROMPT] Using ActivityService to ensure quote_summary and ticket_summary are included")
        
        result = loop.run_until_complete(
            activity_service.generate_action_suggestions(customer_id, force_refresh=True)
        )
        
        if result.get('success'):
            print(f"✅ Successfully generated and cached suggestions for {customer.company_name}")
            print(f"   Generated at: {result.get('generated_at')}")
            print(f"{'='*80}\n")
            
            # Publish suggestions updated event (sync wrapper for Celery)
            from app.core.events import get_event_publisher
            event_publisher = get_event_publisher()
            event_publisher.publish_activity_suggestions_updated_sync(
                tenant_id=tenant_id,
                customer_id=customer_id
            )
            
            return {
                'success': True,
                'customer_id': customer_id,
                'customer_name': customer.company_name,
                'generated_at': result.get('generated_at')
            }
        else:
            error_msg = result.get('error', 'Unknown error generating suggestions')
            print(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
            
    except Exception as e:
        print(f"❌ Error in refresh_customer_suggestions task: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}
    finally:
        db.close()


@celery_app.task(name='run_ai_analysis', bind=True)
def run_ai_analysis_task(self, customer_id: str, tenant_id: str, update_financial_data: bool = True, update_addresses: bool = True) -> Dict[str, Any]:
    """
    Background task to run comprehensive AI analysis for a customer
    
    This task runs asynchronously to avoid blocking the user interface
    while AI performs comprehensive analysis including:
    - Website discovery (using web search)
    - Companies House data retrieval (if update_financial_data=True)
    - Google Maps location data (if update_addresses=True)
    - Website scraping and LinkedIn data
    - Comprehensive AI business intelligence
    
    Args:
        customer_id: Customer ID
        tenant_id: Tenant ID
        update_financial_data: Whether to fetch/update Companies House data
        update_addresses: Whether to fetch/update Google Maps address data
    
    Returns:
        Dict with task results
    """
    db = SessionLocal()
    
    try:
        print(f"\n{'='*80}")
        print(f"🤖 RUNNING AI ANALYSIS (Background Task)")
        print(f"Task ID: {self.request.id}")
        print(f"Customer ID: {customer_id}")
        print(f"Tenant ID: {tenant_id}")
        print(f"{'='*80}\n")
        
        # Get customer
        customer = db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.tenant_id == tenant_id
        ).first()
        
        if not customer:
            print(f"❌ Customer not found: {customer_id}")
            return {'success': False, 'error': 'Customer not found'}
        
        print(f"📊 Analyzing: {customer.company_name}")
        
        # Update status to 'running' (like campaigns)
        customer.ai_analysis_status = 'running'
        db.commit()
        
        # Publish started event (sync wrapper for Celery)
        from app.core.events import get_event_publisher
        event_publisher = get_event_publisher()
        event_publisher.publish_ai_analysis_started_sync(
            tenant_id=tenant_id,
            customer_id=customer_id,
            task_id=self.request.id,
            customer_name=customer.company_name
        )
        
        # Get API keys for this tenant
        from app.models.tenant import Tenant
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        
        if not tenant:
            print(f"❌ Tenant not found: {tenant_id}")
            return {'success': False, 'error': 'Tenant not found'}
        
        # Get API keys with fallback (tenant first, then system-wide)
        api_keys = get_api_keys(db, tenant)
        
        print(f"[AI ANALYSIS] Using API keys from: {api_keys.source}")
        print(f"[AI ANALYSIS] OpenAI configured: {bool(api_keys.openai)}")
        print(f"[AI ANALYSIS] Companies House configured: {bool(api_keys.companies_house)}")
        print(f"[AI ANALYSIS] Google Maps configured: {bool(api_keys.google_maps)}")
        print(f"[AI ANALYSIS] Options: update_financial_data={update_financial_data}, update_addresses={update_addresses}")
        
        if not api_keys.openai:
            print(f"❌ No OpenAI API key configured")
            return {'success': False, 'error': 'No OpenAI API key configured'}
        
        # Import AI service
        from app.services.ai_analysis_service import AIAnalysisService
        
        # Create AI service instance with actual API keys
        ai_service = AIAnalysisService(
            openai_api_key=api_keys.openai,
            companies_house_api_key=api_keys.companies_house,
            google_maps_api_key=api_keys.google_maps,
            tenant_id=tenant_id,
            db=db
        )
        
        # Publish progress event - starting analysis
        event_publisher.publish_ai_analysis_progress(
            tenant_id=tenant_id,
            customer_id=customer_id,
            task_id=self.request.id,
            progress={"step": "starting", "message": "Beginning AI analysis"}
        )
        
        # Run async analysis in sync context
        # Use asyncio.run() which properly creates and manages a new event loop
        # This is safer than get_event_loop() which can fail in Celery workers
        import asyncio
        
        # Run the analysis using asyncio.run() which creates a fresh event loop
        analysis_result = asyncio.run(
            ai_service.analyze_company(
                company_name=customer.company_name,
                company_number=customer.company_registration,
                website=customer.website,
                known_facts=customer.known_facts,
                excluded_addresses=customer.excluded_addresses or [],
                update_financial_data=update_financial_data,
                update_addresses=update_addresses,
                customer_id=customer_id  # Pass customer_id for MinIO storage
            )
        )
        
        print(f"[AI ANALYSIS] Analysis result: success={analysis_result.get('success')}, keys={list(analysis_result.keys())}")
        
        if analysis_result.get('success'):
            # Store the results in customer record
            customer.ai_analysis_raw = analysis_result.get('analysis')
            customer.lead_score = analysis_result.get('analysis', {}).get('lead_score')
            
            # Only update Companies House data if it was fetched
            if update_financial_data:
                companies_house_data = analysis_result.get('source_data', {}).get('companies_house')
                if companies_house_data:
                    # Ensure accounts_documents are included in the stored data
                    if isinstance(customer.companies_house_data, dict):
                        # Merge with existing data, preserving accounts_documents
                        existing_docs = customer.companies_house_data.get('accounts_documents', [])
                        if 'accounts_documents' in companies_house_data:
                            # Merge documents, avoiding duplicates
                            new_docs = companies_house_data.get('accounts_documents', [])
                            existing_paths = {doc.get('minio_path') for doc in existing_docs if doc.get('minio_path')}
                            for doc in new_docs:
                                if doc.get('minio_path') not in existing_paths:
                                    existing_docs.append(doc)
                            companies_house_data['accounts_documents'] = existing_docs
                        else:
                            # Preserve existing documents if new data doesn't have them
                            companies_house_data['accounts_documents'] = existing_docs
                    
                    customer.companies_house_data = companies_house_data
            
            # Only update Google Maps data if it was fetched
            if update_addresses:
                google_maps_data = analysis_result.get('source_data', {}).get('google_maps')
                if google_maps_data:
                    customer.google_maps_data = google_maps_data
            
            # Store web scraping data (website and LinkedIn)
            web_scraping_data = analysis_result.get('source_data', {}).get('web_scraping', {})
            if web_scraping_data:
                # Store LinkedIn data
                linkedin_data = web_scraping_data.get('linkedin', {})
                if linkedin_data.get('linkedin_url'):
                    customer.linkedin_url = linkedin_data.get('linkedin_url')
                customer.linkedin_data = linkedin_data if linkedin_data else None
                
                # Store website analysis data
                website_data = web_scraping_data.get('website', {})
                customer.website_data = website_data if website_data else None
                
                # Extract and populate phone numbers from website scraping if not already set
                if not customer.main_phone and website_data.get('contact_info'):
                    contact_info = website_data['contact_info']
                    # Look for phone numbers in contact info
                    for info in contact_info:
                        # Phone number patterns
                        import re
                        phone_match = re.search(r'(\+?\d[\d\s\-\(\)]{8,})', str(info))
                        if phone_match:
                            customer.main_phone = phone_match.group(1).strip()
                            print(f"[AI ANALYSIS] Extracted phone from website: {customer.main_phone}")
                            break
            
            # Extract phone from Google Maps if not already set
            if not customer.main_phone:
                google_maps_data = analysis_result.get('source_data', {}).get('google_maps', {})
                if google_maps_data.get('locations'):
                    for location in google_maps_data['locations']:
                        if location.get('formatted_phone_number'):
                            customer.main_phone = location['formatted_phone_number']
                            print(f"[AI ANALYSIS] Extracted phone from Google Maps: {customer.main_phone}")
                            break
            
            # Update company registration if found and not already set
            if not customer.company_registration:
                ch_data = analysis_result.get('source_data', {}).get('companies_house', {})
                if ch_data.get('company_number'):
                    customer.company_registration = ch_data.get('company_number')
            
            # Update website if discovered
            if not customer.website and analysis_result.get('source_data', {}).get('web_scraping', {}).get('website_url'):
                customer.website = analysis_result['source_data']['web_scraping']['website_url']
                print(f"[AI ANALYSIS] Discovered and saved website: {customer.website}")
            
            # Update status to 'completed' (like campaigns)
            from datetime import datetime, timezone
            print(f"[AI ANALYSIS] Setting status to 'completed' for {customer.company_name}")
            customer.ai_analysis_status = 'completed'
            customer.ai_analysis_completed_at = datetime.now(timezone.utc)
            
            print(f"[AI ANALYSIS] Committing changes to database...")
            db.commit()
            print(f"[AI ANALYSIS] Database commit successful")
            
            print(f"✅ Successfully completed AI analysis for {customer.company_name}")
            print(f"[AI ANALYSIS] Final status: {customer.ai_analysis_status}")
            print(f"{'='*80}\n")
            
            # Publish completed event (sync wrapper for Celery)
            result_data = {
                'lead_score': customer.lead_score,
                'has_phone': bool(customer.main_phone),
                'has_website': bool(customer.website),
                'has_financial_data': bool(customer.companies_house_data),
                'has_location_data': bool(customer.google_maps_data)
            }
            event_publisher.publish_ai_analysis_completed_sync(
                tenant_id=tenant_id,
                customer_id=customer_id,
                task_id=self.request.id,
                customer_name=customer.company_name,
                result=result_data
            )
            
            return {
                'success': True,
                'customer_id': customer_id,
                'customer_name': customer.company_name,
                'analysis_summary': result_data
            }
        else:
            error_msg = analysis_result.get('error', 'AI analysis failed')
            print(f"❌ AI Analysis failed: {error_msg}")
            print(f"❌ Full analysis_result: {analysis_result}")
            
            # Update status to 'failed'
            from datetime import datetime, timezone
            customer.ai_analysis_status = 'failed'
            customer.ai_analysis_completed_at = datetime.now(timezone.utc)
            db.commit()
            
            # Publish failed event with detailed error
            detailed_error = f"{error_msg}"
            if isinstance(analysis_result.get('error'), dict):
                detailed_error = f"{error_msg} - Details: {json.dumps(analysis_result.get('error'))}"
            
            event_publisher.publish_ai_analysis_failed_sync(
                tenant_id=tenant_id,
                customer_id=customer_id,
                task_id=self.request.id,
                customer_name=customer.company_name,
                error=detailed_error
            )
            
            return {'success': False, 'error': error_msg}
            
    except Exception as e:
        print(f"❌ Exception in run_ai_analysis task: {e}")
        print(f"❌ Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
        # Update status to 'failed' on exception
        try:
            from datetime import datetime, timezone
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                customer.ai_analysis_status = 'failed'
                customer.ai_analysis_completed_at = datetime.now(timezone.utc)
                db.commit()
                
                # Publish failed event with detailed error
                from app.core.events import get_event_publisher
                event_publisher = get_event_publisher()
                error_details = f"{type(e).__name__}: {str(e)}"
                event_publisher.publish_ai_analysis_failed(
                    tenant_id=tenant_id,
                    customer_id=customer_id,
                    task_id=self.request.id,
                    customer_name=customer.company_name,
                    error=error_details
                )
        except Exception as inner_e:
            print(f"❌ Error updating failed status: {inner_e}")
        
        return {'success': False, 'error': str(e)}
    finally:
        db.close()
