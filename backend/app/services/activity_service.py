#!/usr/bin/env python3
"""
Sales Activity Service

Handles all sales activity operations including:
- Activity logging (calls, notes, emails, meetings)
- AI-powered note enhancement and cleanup
- AI-generated action suggestions
- Activity analysis and insights
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, desc, func
import httpx
import json

from app.models.crm import Customer, Contact
from app.models.sales import SalesActivity, ActivityType, ActivityOutcome
from app.core.config import settings
from app.services.ai_provider_service import AIProviderService


class ActivityService:
    """Service for managing sales activities with AI assistance"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.provider_service = AIProviderService(db, tenant_id=tenant_id)
    
    async def create_activity(
        self,
        customer_id: str,
        user_id: str,
        activity_type: ActivityType,
        notes: str,
        subject: Optional[str] = None,
        contact_id: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        outcome: Optional[ActivityOutcome] = None,
        process_with_ai: bool = True
    ) -> SalesActivity:
        """
        Create a new sales activity
        
        Args:
            customer_id: ID of the customer
            user_id: ID of the user creating the activity
            activity_type: Type of activity (call, note, email, etc.)
            notes: Original notes from the user
            subject: Optional subject/title
            contact_id: Optional specific contact involved
            duration_minutes: Duration for calls/meetings
            outcome: Outcome of the activity
            process_with_ai: Whether to enhance notes with AI
        """
        # Create the activity
        activity = SalesActivity(
            tenant_id=self.tenant_id,
            customer_id=customer_id,
            user_id=user_id,
            contact_id=contact_id,
            activity_type=activity_type,
            activity_date=datetime.now(timezone.utc),
            duration_minutes=duration_minutes,
            subject=subject,
            notes=notes,
            outcome=outcome
        )
        
        self.db.add(activity)
        self.db.flush()  # Get the ID
        
        # Process with AI if requested
        if process_with_ai:
            await self.enhance_activity_with_ai(activity)
        
        self.db.commit()
        self.db.refresh(activity)
        
        return activity
    
    async def enhance_activity_with_ai(self, activity: SalesActivity) -> None:
        """
        Use AI to clean up notes and suggest next actions
        
        This function:
        1. Cleans up and structures the original notes
        2. Extracts key information
        3. Suggests specific next actions
        4. Identifies follow-up requirements
        """
        try:
            # Get customer context
            customer = self.db.query(Customer).filter(
                Customer.id == activity.customer_id,
                Customer.tenant_id == self.tenant_id
            ).first()
            
            if not customer:
                return
            
            # Get recent activities for context
            recent_activities = self.db.query(SalesActivity).filter(
                SalesActivity.customer_id == activity.customer_id,
                SalesActivity.tenant_id == self.tenant_id,
                SalesActivity.id != activity.id
            ).order_by(desc(SalesActivity.activity_date)).limit(5).all()
            
            # Check if tenant exists
            tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
            if not tenant:
                print("[ActivityService] Tenant not found")
                return
            
            # Build context for AI
            activity_context = ""
            if recent_activities:
                activity_context = "\n\nRecent Activity History:\n"
                for act in recent_activities:
                    activity_context += f"- {act.activity_date.strftime('%Y-%m-%d')}: {act.activity_type.value.upper()} - {act.notes[:100]}...\n"
            
            customer_context = f"""
Company: {customer.company_name}
Business Sector: {customer.business_sector.value if customer.business_sector else 'Unknown'}
Status: {customer.status.value}
Lead Score: {customer.lead_score or 'N/A'}
"""
            
            if customer.description:
                customer_context += f"Description: {customer.description}\n"
            
            # Get tenant profile for context
            from app.models.tenant import Tenant
            tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
            
            tenant_context = ""
            if tenant:
                tenant_context = f"""
Your Company: {tenant.company_name}
"""
                if tenant.products_services:
                    tenant_context += f"Products/Services: {tenant.products_services[:200]}...\n"
                if tenant.unique_selling_points:
                    tenant_context += f"USPs: {tenant.unique_selling_points[:200]}...\n"
            
            # Get prompt from database
            from app.services.ai_prompt_service import AIPromptService
            from app.models.ai_prompt import PromptCategory
            
            prompt_service = AIPromptService(self.db, tenant_id=self.tenant_id)
            prompt_obj = await prompt_service.get_prompt(
                category=PromptCategory.ACTIVITY_ENHANCEMENT.value,
                tenant_id=self.tenant_id
            )
            
            # Fallback to hardcoded prompt if database prompt not found
            if not prompt_obj:
                print("[ActivityService] Using fallback prompt - database prompt not found")
                user_prompt = f"""You are a sales assistant AI helping to process activity notes for a CRM system.

ACTIVITY TYPE: {activity.activity_type.value.upper()}
ORIGINAL NOTES (from salesperson):
{activity.notes}

{customer_context}
{tenant_context}
{activity_context}

TASKS:
1. Clean up and restructure the notes to be professional and clear
2. Extract key information (pain points, objections, requirements, commitments)
3. Suggest ONE specific next action that should be taken

IMPORTANT:
- Keep all factual information from the original notes
- Make it concise but complete
- Be specific in next actions (e.g., "Call back on Friday to discuss server room upgrade" not "Follow up later")
- Consider the customer's stage in the sales cycle
- Next action should be realistic and actionable

Respond in JSON format:
{{
  "cleaned_notes": "Professional, structured version of the notes",
  "next_action": "Specific action to take with date/context if mentioned",
  "key_points": ["point1", "point2", "point3"],
  "follow_up_priority": "high|medium|low",
  "suggested_follow_up_date": "YYYY-MM-DD or null"
}}"""
                system_prompt = "You are a sales assistant AI that helps clean up and analyze sales activity notes. Always respond with valid JSON."
                model = "gpt-5-mini"
                max_tokens = 10000
            else:
                # Render prompt with variables
                rendered = prompt_service.render_prompt(prompt_obj, {
                    "activity_type": activity.activity_type.value.upper(),
                    "notes": activity.notes,
                    "customer_context": customer_context,
                    "tenant_context": tenant_context,
                    "activity_context": activity_context
                })
                user_prompt = rendered['user_prompt']
                system_prompt = rendered['system_prompt']
                model = rendered['model']
                max_tokens = rendered['max_tokens']
            
            # Use AIProviderService to generate completion
            try:
                if prompt_obj:
                    # Render prompt to get temperature and max_tokens
                    rendered = prompt_service.render_prompt(prompt_obj, {
                        "activity_type": activity.activity_type.value.upper(),
                        "notes": activity.notes,
                        "customer_context": customer_context,
                        "tenant_context": tenant_context,
                        "activity_context": activity_context
                    })
                    # Use database prompt with provider service
                    provider_response = await self.provider_service.generate(
                        prompt=prompt_obj,
                        variables={
                            "activity_type": activity.activity_type.value.upper(),
                            "notes": activity.notes,
                            "customer_context": customer_context,
                            "tenant_context": tenant_context,
                            "activity_context": activity_context
                        },
                        temperature=rendered.get('temperature', 0.7),
                        max_tokens=max_tokens,
                        response_format={"type": "json_object"}
                    )
                    ai_response_text = provider_response.content
                else:
                    # Use fallback with rendered prompts
                    provider_response = await self.provider_service.generate_with_rendered_prompts(
                        prompt=None,  # No prompt object for fallback
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        temperature=0.7,
                        max_tokens=max_tokens,
                        response_format={"type": "json_object"}
                    )
                    ai_response_text = provider_response.content
                
                # Parse JSON response
                ai_response = json.loads(ai_response_text)
                
                # Update activity with AI enhancements
                activity.notes_cleaned = ai_response.get('cleaned_notes')
                activity.ai_suggested_action = ai_response.get('next_action')
                activity.ai_processing_date = datetime.now(timezone.utc)
                
                # Store additional AI context
                activity.ai_context = {
                    'key_points': ai_response.get('key_points', []),
                    'follow_up_priority': ai_response.get('follow_up_priority', 'medium'),
                    'suggested_follow_up_date': ai_response.get('suggested_follow_up_date')
                }
                
                # Set follow-up if AI suggested it
                if ai_response.get('suggested_follow_up_date'):
                    try:
                        follow_up_date = datetime.strptime(ai_response['suggested_follow_up_date'], '%Y-%m-%d')
                        activity.follow_up_required = True
                        activity.follow_up_date = follow_up_date
                    except:
                        pass
                
                print(f"✓ AI enhanced activity notes for {customer.company_name}")
                
            except Exception as e:
                print(f"[ERROR] Failed to enhance activity with AI: {e}")
                import traceback
                traceback.print_exc()
        
        except Exception as e:
            print(f"[ERROR] Failed to enhance activity with AI (outer): {e}")
            import traceback
            traceback.print_exc()
    
    async def generate_action_suggestions(self, customer_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Generate AI-powered action suggestions for a customer
        
        Returns suggestions for:
        - Calls to make (and what to discuss)
        - Emails to send (and topics)
        - Customer visits (and objectives)
        
        Based on:
        - Recent activity history
        - Customer status and stage
        - AI analysis data
        - Time since last contact
        - Quote history (when available)
        
        Args:
            customer_id: Customer ID
            force_refresh: If True, regenerate suggestions even if cached. If False, use cached suggestions if available.
        """
        try:
            # Get customer data
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id,
                Customer.tenant_id == self.tenant_id
            ).first()
            
            if not customer:
                return {'success': False, 'error': 'Customer not found'}
            
            # Check cache first (unless force_refresh is True)
            if not force_refresh and customer.ai_suggestions and customer.ai_suggestions_date:
                print(f"[SUGGESTIONS CACHE] Using cached suggestions from {customer.ai_suggestions_date}")
                return {
                    'success': True,
                    'suggestions': customer.ai_suggestions,
                    'generated_at': customer.ai_suggestions_date.isoformat(),
                    'cached': True
                }
            
            print(f"[SUGGESTIONS] Generating new suggestions (force_refresh={force_refresh})")
            
            # Get recent activities
            activities = self.db.query(SalesActivity).filter(
                SalesActivity.customer_id == customer_id,
                SalesActivity.tenant_id == self.tenant_id
            ).order_by(desc(SalesActivity.activity_date)).limit(10).all()
            
            # Check for pending follow-ups
            pending_follow_ups = self.db.query(SalesActivity).filter(
                SalesActivity.customer_id == customer_id,
                SalesActivity.tenant_id == self.tenant_id,
                SalesActivity.follow_up_required == True,
                SalesActivity.follow_up_date <= datetime.now(timezone.utc) + timedelta(days=7)
            ).all()
            
            # Get tenant for API keys and context
            from app.models.tenant import Tenant
            tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
            if not tenant:
                return {'success': False, 'error': 'Tenant not found', 'suggestions': None, 'generated_at': None}
            
            # Get API keys
            from app.core.api_keys import get_api_keys
            api_keys = get_api_keys(self.db, tenant)
            
            if not api_keys.openai:
                return {'success': False, 'error': 'No OpenAI API key configured', 'suggestions': None, 'generated_at': None}
            
            # Build comprehensive context
            activity_summary = ""
            if activities:
                activity_summary = "Recent Activity:\n"
                for act in activities[:5]:
                    activity_summary += f"- {act.activity_date.strftime('%Y-%m-%d')}: {act.activity_type.value.upper()}"
                    if act.notes_cleaned:
                        activity_summary += f" - {act.notes_cleaned[:100]}...\n"
                    else:
                        activity_summary += f" - {act.notes[:100]}...\n"
            
            days_since_contact = None
            if activities:
                days_since_contact = (datetime.now(timezone.utc) - activities[0].activity_date).days
            
            # Extract key information from AI analysis
            needs_assessment = ""
            business_opportunities = ""
            how_we_can_help = ""
            
            if customer.ai_analysis_raw:
                ai_data = customer.ai_analysis_raw
                print(f"[ACTION SUGGESTIONS] AI analysis keys: {ai_data.keys() if isinstance(ai_data, dict) else 'Not a dict'}")
                if isinstance(ai_data, dict):
                    # Try new format first (from lead generation)
                    needs_assessment = ai_data.get('needs_assessment', '')
                    business_opportunities = ai_data.get('business_opportunities', '')
                    how_we_can_help = ai_data.get('how_we_can_help', '')
                    
                    # Try older/alternative format (technology_needs, opportunities directly)
                    if not needs_assessment and 'technology_needs' in ai_data:
                        tech_needs = ai_data.get('technology_needs', '')
                        if isinstance(tech_needs, list):
                            needs_assessment = '\n'.join(f"- {need}" for need in tech_needs)
                        elif isinstance(tech_needs, str):
                            needs_assessment = tech_needs
                    
                    if not business_opportunities and 'opportunities' in ai_data:
                        opps = ai_data.get('opportunities', '')
                        if isinstance(opps, list):
                            business_opportunities = '\n'.join(f"- {opp}" for opp in opps)
                        elif isinstance(opps, str):
                            business_opportunities = opps
                    
                    # Also check for business_intelligence which might contain opportunities
                    if not business_opportunities and 'business_intelligence' in ai_data:
                        bi = ai_data['business_intelligence']
                        if isinstance(bi, dict):
                            business_opportunities = bi.get('opportunities', '')
                    
                    # Build "how we can help" from available data if not present
                    if not how_we_can_help:
                        help_parts = []
                        if 'primary_business_activities' in ai_data:
                            help_parts.append(f"Business Focus: {ai_data['primary_business_activities']}")
                        if 'technology_maturity' in ai_data:
                            help_parts.append(f"Technology Maturity: {ai_data['technology_maturity']}")
                        if 'growth_potential' in ai_data:
                            help_parts.append(f"Growth Potential: {ai_data['growth_potential']}")
                        if help_parts:
                            how_we_can_help = '\n'.join(help_parts)
                    
                    # Final fallback: use any available analysis text
                    if not needs_assessment and not business_opportunities:
                        for key in ['analysis', 'summary', 'insights', 'recommendations', 'risks']:
                            if key in ai_data and ai_data[key]:
                                val = ai_data[key]
                                if isinstance(val, list):
                                    needs_assessment = '\n'.join(f"- {item}" for item in val[:5])
                                else:
                                    needs_assessment = f"From AI analysis: {str(val)[:500]}"
                                break
                    
                    print(f"[ACTION SUGGESTIONS] Extracted - Needs: {len(needs_assessment)} chars, Opportunities: {len(business_opportunities)} chars, Help: {len(how_we_can_help)} chars")
            else:
                print(f"[ACTION SUGGESTIONS] WARNING: No AI analysis data for {customer.company_name}")
            
            # Build comprehensive tenant context
            tenant_context = f"""
YOUR COMPANY: {tenant.company_name if tenant else 'N/A'}

YOUR PRODUCTS & SERVICES:
{tenant.products_services if tenant and tenant.products_services else 'N/A'}

YOUR UNIQUE SELLING POINTS:
{tenant.unique_selling_points if tenant and tenant.unique_selling_points else 'N/A'}

YOUR TARGET MARKETS:
{tenant.target_markets if tenant and tenant.target_markets else 'N/A'}

HOW YOU HELP CUSTOMERS (B2C - Direct Services):
{tenant.sales_methodology if tenant and tenant.sales_methodology else 'N/A'}

B2B PARTNERSHIP OPPORTUNITIES (How to work WITH similar businesses):
{tenant.partnership_opportunities if tenant and tenant.partnership_opportunities else 'N/A'}
"""
            
            # Get prompt from database
            from app.services.ai_prompt_service import AIPromptService
            from app.models.ai_prompt import PromptCategory
            
            prompt_service = AIPromptService(self.db, tenant_id=self.tenant_id)
            prompt_obj = await prompt_service.get_prompt(
                category=PromptCategory.ACTION_SUGGESTIONS.value,
                tenant_id=self.tenant_id
            )
            
            # Fallback to hardcoded prompt if database prompt not found
            if not prompt_obj:
                print("[ActivityService] Using fallback prompt for action suggestions - database prompt not found")
                user_prompt = f"""You are a sales advisor AI helping prioritize customer engagement actions.

CUSTOMER INFORMATION:
Company: {customer.company_name}
Status: {customer.status.value}
Lead Score: {customer.lead_score or 'N/A'}
Sector: {customer.business_sector.value if customer.business_sector else 'Unknown'}
Days Since Last Contact: {days_since_contact if days_since_contact is not None else 'No previous contact'}

{activity_summary}

CUSTOMER'S IDENTIFIED NEEDS:
{needs_assessment if needs_assessment else 'Not assessed yet'}

CUSTOMER'S BUSINESS OPPORTUNITIES:
{business_opportunities if business_opportunities else 'Not identified yet'}

HOW YOUR COMPANY CAN HELP THIS CUSTOMER:
{how_we_can_help if how_we_can_help else 'Not analyzed yet'}

{tenant_context}

CRITICAL INSTRUCTIONS:
1. Base ALL suggestions on the customer's IDENTIFIED NEEDS and BUSINESS OPPORTUNITIES above
2. Match your company's products/services to their specific needs
3. Use the "How We Can Help" section to craft targeted value propositions
4. If they are in a similar industry, consider B2B partnership opportunities
5. Be SPECIFIC - reference actual needs and solutions, not generic sales talk
6. Each suggestion should have a clear business reason tied to their needs

TASK: Generate 3 prioritized action suggestions (call, email, visit) that directly address the customer's needs with your solutions.

Respond in JSON:
{{
  "call_suggestion": {{
    "priority": "high|medium|low",
    "reason": "Why call now",
    "talking_points": ["point1", "point2", "point3"],
    "best_time": "Suggested time/day"
  }},
  "email_suggestion": {{
    "priority": "high|medium|low",
    "reason": "Why email now",
    "subject": "Email subject line",
    "key_topics": ["topic1", "topic2"]
  }},
  "visit_suggestion": {{
    "priority": "high|medium|low",
    "reason": "Why visit now",
    "objectives": ["objective1", "objective2"],
    "timing": "When to schedule"
  }}
}}"""
                system_prompt = "You are a sales strategy AI that provides actionable customer engagement suggestions. Always respond with valid JSON."
                model = "gpt-5-mini"
                max_tokens = 20000
            else:
                # Render prompt with variables
                rendered = prompt_service.render_prompt(prompt_obj, {
                    "company_name": customer.company_name,
                    "status": customer.status.value,
                    "lead_score": str(customer.lead_score or 'N/A'),
                    "sector": customer.business_sector.value if customer.business_sector else 'Unknown',
                    "days_since_contact": str(days_since_contact) if days_since_contact is not None else 'No previous contact',
                    "activity_summary": activity_summary,
                    "needs_assessment": needs_assessment if needs_assessment else 'Not assessed yet',
                    "business_opportunities": business_opportunities if business_opportunities else 'Not identified yet',
                    "how_we_can_help": how_we_can_help if how_we_can_help else 'Not analyzed yet',
                    "tenant_context": tenant_context
                })
                user_prompt = rendered['user_prompt']
                system_prompt = rendered['system_prompt']
                model = rendered['model']
                max_tokens = rendered['max_tokens']
            
            # Call OpenAI (use longer timeout for complex analysis)
            async with httpx.AsyncClient(timeout=240.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_keys.openai}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": system_prompt
                            },
                            {
                                "role": "user",
                                "content": user_prompt
                            }
                        ],
                        "max_completion_tokens": max_tokens,
                        "response_format": {"type": "json_object"}
                    }
                )
            
            if response.status_code == 200:
                result = response.json()
                suggestions = json.loads(result['choices'][0]['message']['content'])
                generated_at = datetime.now(timezone.utc)
                
                # Cache the suggestions in the database
                customer.ai_suggestions = suggestions
                customer.ai_suggestions_date = generated_at
                self.db.commit()
                print(f"✓ Cached suggestions for customer {customer_id}")
                
                return {
                    'success': True,
                    'suggestions': suggestions,
                    'generated_at': generated_at.isoformat(),
                    'cached': False
                }
            else:
                print(f"✗ OpenAI API error: {response.status_code}")
                return {'success': False, 'error': 'API error'}
                
        except Exception as e:
            print(f"[ERROR] Failed to generate action suggestions: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def get_activities(
        self,
        customer_id: str,
        activity_type: Optional[ActivityType] = None,
        limit: int = 50
    ) -> List[SalesActivity]:
        """Get activities for a customer"""
        stmt = select(SalesActivity).where(
            and_(
                SalesActivity.customer_id == customer_id,
                SalesActivity.tenant_id == self.tenant_id
            )
        )
        
        if activity_type:
            stmt = stmt.where(SalesActivity.activity_type == activity_type)
        
        stmt = stmt.order_by(desc(SalesActivity.activity_date)).limit(limit)
        
        result = self.db.execute(stmt)
        return result.scalars().all()
    
    def get_pending_follow_ups(self, days_ahead: int = 7) -> List[SalesActivity]:
        """Get activities requiring follow-up in the next N days"""
        stmt = select(SalesActivity).where(
            and_(
                SalesActivity.tenant_id == self.tenant_id,
                SalesActivity.follow_up_required == True,
                SalesActivity.follow_up_date <= datetime.now(timezone.utc) + timedelta(days=days_ahead)
            )
        ).order_by(SalesActivity.follow_up_date)
        
        result = self.db.execute(stmt)
        return result.scalars().all()

