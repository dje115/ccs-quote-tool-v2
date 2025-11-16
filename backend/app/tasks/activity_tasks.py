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
        
        # Get recent activities
        activities = db.query(SalesActivity).filter(
            SalesActivity.customer_id == customer_id,
            SalesActivity.tenant_id == tenant_id
        ).order_by(desc(SalesActivity.activity_date)).limit(10).all()
        
        # Get tenant for API keys and context
        from app.models.tenant import Tenant
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        
        if not tenant:
            print(f"❌ Tenant not found: {tenant_id}")
            return {'success': False, 'error': 'Tenant not found'}
        
        # Get API keys
        api_keys = get_api_keys(db, tenant_id)
        if not api_keys.openai:
            print("❌ No OpenAI API key configured")
            return {'success': False, 'error': 'No OpenAI API key configured'}
        
        # Build activity summary
        activity_summary = ""
        if activities:
            activity_summary = f"Recent activity history ({len(activities)} interactions):\n"
            for act in activities[:5]:
                activity_summary += f" - {act.activity_date.strftime('%Y-%m-%d')}: {act.activity_type.value}"
                if act.subject:
                    activity_summary += f" - {act.subject}\n"
                else:
                    activity_summary += f" - {act.notes[:100]}...\n"
        
        days_since_contact = None
        if activities:
            days_since_contact = (datetime.now(timezone.utc) - activities[0].activity_date).days
        
        # Extract AI analysis data
        needs_assessment = ""
        business_opportunities = ""
        how_we_can_help = ""
        
        if customer.ai_analysis_raw:
            needs_assessment = customer.ai_analysis_raw.get('needs_assessment', '')
            business_opportunities = customer.ai_analysis_raw.get('business_opportunities', '')
            how_we_can_help = customer.ai_analysis_raw.get('how_we_can_help', '')
            
            # Fallback to older field names
            if not needs_assessment:
                tech_needs = customer.ai_analysis_raw.get('technology_needs', [])
                if isinstance(tech_needs, list):
                    needs_assessment = '\n'.join(f"- {need}" for need in tech_needs)
            
            if not business_opportunities:
                opportunities = customer.ai_analysis_raw.get('opportunities', [])
                if isinstance(opportunities, list):
                    business_opportunities = '\n'.join(f"- {opp}" for opp in opportunities)
        
        # Build tenant context
        tenant_context = f"""
Your Company Information:
- Company: {tenant.company_name or tenant.name}
- Description: {tenant.company_description or 'Not provided'}

Products & Services:
{tenant.products_services or 'Not provided'}

Unique Selling Points:
{tenant.unique_selling_points or 'Not provided'}

Target Markets:
{tenant.target_markets or 'Not provided'}

Partnership Opportunities (B2B):
{tenant.partnership_opportunities or 'Not provided'}
"""
        
        # Build comprehensive prompt
        prompt = f"""You are a sales strategy AI helping {tenant.company_name or tenant.name} engage with their customer: {customer.company_name}.

{tenant_context}

Customer Information:
- Company: {customer.company_name}
- Status: {customer.status.value if customer.status else 'Unknown'}
- Sector: {customer.business_sector.value if customer.business_sector else 'Unknown'}
- Size: {customer.business_size.value if customer.business_size else 'Unknown'}
- Website: {customer.website or 'Not provided'}
- Days since last contact: {days_since_contact if days_since_contact else 'Never contacted'}

Customer's Needs Assessment:
{needs_assessment or 'Not yet analyzed'}

Business Opportunities Identified:
{business_opportunities or 'Not yet analyzed'}

How We Can Help:
{how_we_can_help or 'Not yet analyzed'}

{activity_summary or 'No activity history yet'}

Based on this information, generate THREE specific, actionable suggestions:

1. **Call Suggestion**: When to call, what to discuss, and key talking points
2. **Email Suggestion**: When to email, subject line, and key topics to cover
3. **Visit Suggestion**: When to visit (if appropriate), objectives, and what to bring/demo

For each suggestion:
- Be specific and actionable
- Reference the customer's actual needs and your company's solutions
- Consider their stage in the sales cycle
- Include timing recommendations
- Make it relevant to their business sector and size

Respond in this exact JSON format:
{{
    "call": {{
        "priority": "high|medium|low",
        "timing": "specific timing recommendation",
        "objective": "what you want to achieve",
        "talking_points": ["point 1", "point 2", "point 3"]
    }},
    "email": {{
        "priority": "high|medium|low",
        "timing": "specific timing recommendation",
        "subject": "suggested email subject line",
        "key_topics": ["topic 1", "topic 2", "topic 3"]
    }},
    "visit": {{
        "priority": "high|medium|low",
        "recommended": true/false,
        "timing": "specific timing recommendation",
        "objectives": ["objective 1", "objective 2"],
        "what_to_bring": ["item 1", "item 2"]
    }}
}}"""
        
        print(f"🤖 Calling OpenAI API (gpt-5-mini)...")
        
        # Call OpenAI API
        async def generate_suggestions():
            async with httpx.AsyncClient(timeout=240.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_keys.openai}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-5-mini",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a sales strategy AI that provides actionable customer engagement suggestions. Always respond with valid JSON."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_completion_tokens": 20000,
                        "response_format": {"type": "json_object"}
                    }
                )
                return response
        
        # Run async function in sync context
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(generate_suggestions())
        
        if response.status_code == 200:
            result = response.json()
            suggestions = json.loads(result['choices'][0]['message']['content'])
            generated_at = datetime.now(timezone.utc)
            
            # Cache the suggestions in the database
            customer.ai_suggestions = suggestions
            customer.ai_suggestions_date = generated_at
            db.commit()
            
            print(f"✅ Successfully generated and cached suggestions for {customer.company_name}")
            print(f"{'='*80}\n")
            
            # Publish suggestions updated event
            from app.core.events import get_event_publisher
            event_publisher = get_event_publisher()
            event_publisher.publish_activity_suggestions_updated(
                tenant_id=tenant_id,
                customer_id=customer_id
            )
            
            return {
                'success': True,
                'customer_id': customer_id,
                'customer_name': customer.company_name,
                'generated_at': generated_at.isoformat()
            }
        else:
            error_msg = f"OpenAI API error: {response.status_code}"
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
def run_ai_analysis_task(self, customer_id: str, tenant_id: str) -> Dict[str, Any]:
    """
    Background task to run comprehensive AI analysis for a customer
    
    This task runs asynchronously to avoid blocking the user interface
    while AI performs comprehensive analysis including:
    - Website discovery (using web search)
    - Companies House data retrieval
    - Google Maps location data
    - Website scraping and LinkedIn data
    - Comprehensive AI business intelligence
    
    Args:
        customer_id: Customer ID
        tenant_id: Tenant ID
    
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
        
        # Publish started event
        from app.core.events import get_event_publisher
        event_publisher = get_event_publisher()
        event_publisher.publish_ai_analysis_started(
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
                excluded_addresses=customer.excluded_addresses or []
            )
        )
        
        print(f"[AI ANALYSIS] Analysis result: success={analysis_result.get('success')}, keys={list(analysis_result.keys())}")
        
        if analysis_result.get('success'):
            # Store the results in customer record
            customer.ai_analysis_raw = analysis_result.get('analysis')
            customer.lead_score = analysis_result.get('analysis', {}).get('lead_score')
            customer.companies_house_data = analysis_result.get('source_data', {}).get('companies_house')
            customer.google_maps_data = analysis_result.get('source_data', {}).get('google_maps')
            
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
            
            # Publish completed event
            result_data = {
                'lead_score': customer.lead_score,
                'has_phone': bool(customer.main_phone),
                'has_website': bool(customer.website),
                'has_financial_data': bool(customer.companies_house_data),
                'has_location_data': bool(customer.google_maps_data)
            }
            event_publisher.publish_ai_analysis_completed(
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
            
            event_publisher.publish_ai_analysis_failed(
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

