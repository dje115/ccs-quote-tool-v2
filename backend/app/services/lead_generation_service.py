#!/usr/bin/env python3
"""
AI-powered lead generation service for v2
Migrated from v1 with multi-tenant support
"""

import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
import openai

from app.core.config import settings
from app.models.leads import LeadGenerationCampaign, Lead, LeadStatus, LeadSource, LeadGenerationStatus
from app.models.crm import Customer


class LeadGenerationService:
    """Service for AI-powered lead generation"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.openai_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client with API key"""
        try:
            # Get tenant-specific or system-wide API key
            api_key = self._get_api_key()
            if api_key:
                self.openai_client = openai.OpenAI(
                    api_key=api_key,
                    timeout=settings.OPENAI_TIMEOUT
                )
        except Exception as e:
            print(f"[ERROR] Error initializing OpenAI client: {e}")
    
    def _get_api_key(self) -> Optional[str]:
        """Get OpenAI API key (tenant-specific or system-wide)"""
        # For now, use system-wide key from settings
        # Later: Check tenant table for tenant-specific key
        return settings.OPENAI_API_KEY
    
    async def generate_leads(self, campaign: LeadGenerationCampaign) -> Dict[str, Any]:
        """Generate leads using AI with web search"""
        if not self.openai_client:
            return {
                'success': False,
                'error': 'OpenAI client not initialized'
            }
        
        try:
            # Update campaign status
            campaign.status = LeadGenerationStatus.RUNNING
            campaign.started_at = datetime.utcnow()
            self.db.commit()
            
            print(f"\n{'='*60}")
            print(f"[OK] Starting lead generation for campaign: {campaign.name}")
            print(f"[OK] Postcode: {campaign.postcode}")
            print(f"[OK] Distance: {campaign.distance_miles} miles")
            print(f"[OK] Max Results: {campaign.max_results}")
            print(f"{'='*60}\n")
            
            # Use GPT-5-mini with web search
            ai_response = await self._search_with_ai(campaign)
            
            # Parse AI response
            leads_data = self._parse_ai_response(ai_response)
            
            # Create leads from data
            created_leads = await self._create_leads(leads_data, campaign)
            
            # Update campaign
            campaign.total_found = len(leads_data)
            campaign.leads_created = len(created_leads)
            campaign.completed_at = datetime.utcnow()
            campaign.status = LeadGenerationStatus.COMPLETED
            self.db.commit()
            
            print(f"\n[OK] Campaign completed!")
            print(f"[OK] Total found: {campaign.total_found}")
            print(f"[OK] Leads created: {campaign.leads_created}")
            
            return {
                'success': True,
                'leads': created_leads,
                'total_found': campaign.total_found
            }
            
        except Exception as e:
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            print(f"[ERROR] Lead generation failed: {error_msg}")
            
            campaign.status = LeadGenerationStatus.FAILED
            campaign.completed_at = datetime.utcnow()
            campaign.errors_count = 1
            self.db.commit()
            
            return {
                'success': False,
                'error': error_msg
            }
    
    async def _search_with_ai(self, campaign: LeadGenerationCampaign) -> str:
        """Use AI with web search to find real businesses"""
        
        # Build prompt based on campaign type
        prompt = self._build_prompt(campaign)
        
        try:
            print(f"[OK] Using GPT-5-mini with Responses API and web search...")
            
            # Use Responses API with web search
            response = self.openai_client.responses.create(
                model="gpt-5-mini",
                tools=[{"type": "web_search"}],
                input=[
                    {
                        "role": "system",
                        "content": "You are a UK business research expert with web search access. Find REAL UK businesses only. Output valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                metadata={"task": f"lead_generation_{campaign.prompt_type}"}
            )
            
            print(f"[OK] GPT-5-mini response received")
            
            # Extract response text
            ai_response = self._extract_response_text(response)
            
            return ai_response
            
        except Exception as e:
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            print(f"[ERROR] AI search failed: {error_msg}")
            raise
    
    def _build_prompt(self, campaign: LeadGenerationCampaign) -> str:
        """Build AI prompt based on campaign type"""
        
        base_prompt = f"""
Find {campaign.max_results} REAL UK businesses near {campaign.postcode} (within {campaign.distance_miles} miles).

Campaign Type: {campaign.prompt_type}

REQUIREMENTS:
1. Use web search to find REAL, existing UK businesses
2. Verify each business has a real website
3. Get actual contact information from websites
4. Only return businesses that currently exist

OUTPUT FORMAT - Valid JSON:
{{
  "results": [
    {{
      "company_name": "Real Company Name Ltd",
      "website": "https://realcompany.com",
      "description": "Why they need IT/cabling services",
      "contact_email": "contact@realcompany.com",
      "contact_phone": "01234 567890",
      "address": "Full business address",
      "postcode": "{campaign.postcode}",
      "business_sector": "Technology/Healthcare/Education/etc",
      "company_size": "Micro/Small/Medium/Large",
      "lead_score": 85
    }}
  ]
}}

FOCUS: Find businesses that need IT infrastructure, structured cabling, WiFi, or network services.

Return ONLY the JSON object. No markdown fences. No additional text.
"""
        
        return base_prompt
    
    def _extract_response_text(self, response) -> str:
        """Extract text from Responses API response"""
        try:
            if hasattr(response, 'output') and isinstance(response.output, list):
                for item in reversed(response.output):
                    if hasattr(item, 'type') and item.type == 'message':
                        if hasattr(item, 'content') and isinstance(item.content, list):
                            for content_item in item.content:
                                if hasattr(content_item, 'text'):
                                    text = content_item.text
                                    print(f"[OK] Extracted {len(text)} characters")
                                    return text
            
            print(f"[ERROR] Could not extract response text")
            return '{"results": []}'
            
        except Exception as e:
            print(f"[ERROR] Error extracting response: {e}")
            return '{"results": []}'
    
    def _parse_ai_response(self, ai_response: str) -> List[Dict]:
        """Parse AI response to extract lead data"""
        try:
            # Clean markdown fences if present
            cleaned = ai_response.strip()
            if cleaned.startswith('```'):
                lines = cleaned.split('\n')
                if len(lines) > 2:
                    cleaned = '\n'.join(lines[1:-1]).strip()
            
            # Parse JSON
            data = json.loads(cleaned)
            
            if isinstance(data, dict) and 'results' in data:
                leads = data['results']
                print(f"[OK] Parsed {len(leads)} leads from AI response")
                return leads if isinstance(leads, list) else []
            elif isinstance(data, list):
                print(f"[OK] Parsed {len(data)} leads from array")
                return data
            else:
                print(f"[WARN] Unexpected JSON structure")
                return []
                
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parsing failed: {e}")
            return []
        except Exception as e:
            print(f"[ERROR] Error parsing response: {e}")
            return []
    
    async def _create_leads(self, leads_data: List[Dict], campaign: LeadGenerationCampaign) -> List[Lead]:
        """Create Lead records from parsed data"""
        created_leads = []
        duplicates = 0
        
        for lead_data in leads_data:
            try:
                company_name = lead_data.get('company_name', '').strip()
                if not company_name:
                    continue
                
                # Check for duplicates
                existing_lead = self.db.query(Lead).filter_by(
                    tenant_id=self.tenant_id,
                    company_name=company_name
                ).first()
                
                if existing_lead:
                    duplicates += 1
                    print(f"[DEDUP] Skipping duplicate: {company_name}")
                    continue
                
                # Check if already a customer
                existing_customer = self.db.query(Customer).filter_by(
                    tenant_id=self.tenant_id,
                    company_name=company_name
                ).first()
                
                if existing_customer:
                    duplicates += 1
                    print(f"[DEDUP] Skipping - already customer: {company_name}")
                    continue
                
                # Create new lead
                lead = Lead(
                    tenant_id=self.tenant_id,
                    campaign_id=campaign.id,
                    company_name=company_name,
                    website=lead_data.get('website'),
                    contact_email=lead_data.get('contact_email'),
                    contact_phone=lead_data.get('contact_phone'),
                    address=lead_data.get('address'),
                    postcode=lead_data.get('postcode'),
                    business_sector=lead_data.get('business_sector'),
                    company_size=lead_data.get('company_size'),
                    lead_score=lead_data.get('lead_score', 50),
                    status=LeadStatus.NEW,
                    source=LeadSource.AI_GENERATED,
                    ai_analysis=lead_data
                )
                
                self.db.add(lead)
                created_leads.append(lead)
                print(f"[OK] Created lead: {company_name}")
                
            except Exception as e:
                error_msg = str(e).encode('ascii', 'replace').decode('ascii')
                print(f"[ERROR] Error creating lead: {error_msg}")
                continue
        
        # Commit all leads
        self.db.commit()
        
        campaign.duplicates_found = duplicates
        self.db.commit()
        
        print(f"\n[OK] Created {len(created_leads)} leads, {duplicates} duplicates skipped")
        
        return created_leads

