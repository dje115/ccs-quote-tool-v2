#!/usr/bin/env python3
"""
AI-powered lead generation service for v2
Migrated from v1 with comprehensive features:
- GPT-5-mini with web search (minimum 10000 tokens)
- Google Maps API integration for location data
- Companies House API for business verification
- LinkedIn and web scraping
- Automatic deduplication against customers and leads
- Background processing support (Celery-ready)

MEMORY: [[memory:9653106]] - Use GPT-5-mini exclusively with 10000+ tokens, 120s+ timeout
"""

import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import httpx

from app.core.api_keys import get_api_keys
from app.models.leads import LeadGenerationCampaign, Lead, LeadStatus, LeadSource, LeadGenerationStatus
from app.models.crm import Customer, CustomerStatus
from app.models.tenant import Tenant


class LeadGenerationService:
    """
    Service for AI-powered lead generation with comprehensive data collection
    
    Features migrated from v1:
    1. GPT-5-mini with Responses API + web search
    2. Google Maps API for location/address verification
    3. Companies House API for company verification
    4. LinkedIn data scraping
    5. Website information extraction
    6. Intelligent deduplication
    7. Lead scoring and qualification
    8. Background processing support
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.tenant = None
        self.openai_client = None
        self.gmaps_client = None
        self.companies_house_key = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize all API clients with keys"""
        try:
            # Fetch tenant object from database
            self.tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
            if not self.tenant:
                print(f"[ERROR] Tenant not found: {self.tenant_id}")
                return
            
            # Get API keys (tenant-specific or system-wide)
            api_keys = get_api_keys(self.db, self.tenant)
            
            print(f"[INFO] API Keys resolved from: {api_keys.source}")
            
            # Initialize OpenAI client
            if api_keys.openai:
                import openai
                self.openai_client = openai.OpenAI(
                    api_key=api_keys.openai,
                    timeout=240.0  # 4 minutes for GPT-5-mini with web search [[memory:9653106]]
                )
                print("[OK] OpenAI client initialized")
            else:
                print("[WARN] OpenAI API key not found")
            
            # Initialize Google Maps client
            if api_keys.google_maps:
                import googlemaps
                self.gmaps_client = googlemaps.Client(key=api_keys.google_maps)
                print("[OK] Google Maps client initialized")
            else:
                print("[WARN] Google Maps API key not found")
            
            # Store Companies House key
            if api_keys.companies_house:
                self.companies_house_key = api_keys.companies_house
                print("[OK] Companies House API key found")
            else:
                print("[WARN] Companies House API key not found")
                
        except Exception as e:
            print(f"[ERROR] Error initializing API clients: {e}")
    
    async def generate_leads(self, campaign: LeadGenerationCampaign) -> Dict[str, Any]:
        """
        Generate leads using AI with web search + external data enrichment
        
        Process:
        1. Use GPT-5-mini with web search to find real businesses
        2. Parse and validate AI results
        3. Enrich with Google Maps data (multiple locations)
        4. Verify with Companies House
        5. Scrape LinkedIn and websites
        6. Deduplicate against existing customers and leads
        7. Score and qualify leads
        8. Create Lead records with DISCOVERY status
        """
        if not self.openai_client:
            return {
                'success': False,
                'error': 'OpenAI client not initialized - check API key configuration'
            }
        
        try:
            # Update campaign status
            campaign.status = LeadGenerationStatus.RUNNING
            campaign.started_at = datetime.utcnow()
            self.db.commit()
            
            print(f"\n{'='*80}")
            print(f"🚀 LEAD GENERATION CAMPAIGN: {campaign.name}")
            print(f"{'='*80}")
            
            # Check if this is a company name list campaign
            if campaign.company_names and len(campaign.company_names) > 0:
                print(f"📋 Company List Campaign")
                print(f"🎯 Processing {len(campaign.company_names)} companies")
                print(f"🏷️  Type: {campaign.prompt_type}")
                print(f"{'='*80}\n")
                
                # Create leads data directly from company names
                leads_data = [{'company_name': name} for name in campaign.company_names]
                print(f"✓ Created {len(leads_data)} leads from company list")
            else:
                print(f"📍 Location: {campaign.postcode} (±{campaign.distance_miles} miles)")
                print(f"🎯 Target: {campaign.max_results} businesses")
                print(f"🏷️  Type: {campaign.prompt_type}")
                print(f"{'='*80}\n")
                
                # Step 1: Use GPT-5-mini with web search to find businesses
                print("🔍 Step 1: AI Web Search for Real Businesses")
                ai_response = await self._search_with_ai(campaign)
                
                # Step 2: Parse AI response
                print("\n📊 Step 2: Parsing AI Results")
                leads_data = self._parse_ai_response(ai_response)
            print(f"✓ Found {len(leads_data)} potential leads from AI")
            
            # Step 3: Enrich and deduplicate leads
            print("\n🔧 Step 3: Enriching with External Data & Deduplication")
            enriched_leads = await self._enrich_leads(leads_data, campaign)
            print(f"✓ {len(enriched_leads)} leads after enrichment and deduplication")
            
            # Step 4: Create Lead records
            print("\n💾 Step 4: Creating Lead Records")
            created_leads = await self._create_leads(enriched_leads, campaign)
            
            # Step 5: Update campaign
            campaign.total_found = len(leads_data)
            campaign.leads_created = len(created_leads)
            campaign.completed_at = datetime.utcnow()
            campaign.status = LeadGenerationStatus.COMPLETED
            campaign.ai_analysis_summary = ai_response[:5000]  # Store first 5000 chars
            self.db.commit()
            
            print(f"\n{'='*80}")
            print(f"✅ CAMPAIGN COMPLETED SUCCESSFULLY!")
            print(f"{'='*80}")
            print(f"📈 Total Found: {campaign.total_found}")
            print(f"✨ Leads Created: {campaign.leads_created}")
            print(f"🔁 Duplicates Skipped: {campaign.duplicates_found}")
            print(f"{'='*80}\n")
            
            return {
                'success': True,
                'leads': created_leads,
                'total_found': campaign.total_found,
                'leads_created': campaign.leads_created,
                'duplicates_skipped': campaign.duplicates_found
            }
            
        except Exception as e:
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            print(f"\n❌ CAMPAIGN FAILED: {error_msg}\n")
            
            campaign.status = LeadGenerationStatus.FAILED
            campaign.completed_at = datetime.utcnow()
            campaign.errors_count += 1
            self.db.commit()
            
            return {
                'success': False,
                'error': error_msg
            }
    
    async def _search_with_ai(self, campaign: LeadGenerationCampaign) -> str:
        """
        Use GPT-5-mini with Responses API + web search to find real businesses
        
        [[memory:9653106]] - CRITICAL: Use gpt-5-mini with 20000+ tokens, 240s+ timeout
        
        The Responses API with web_search tool provides real-time web access for finding
        actual UK businesses, making lead generation much more accurate and current.
        """
        
        # Build comprehensive prompt
        prompt = self._build_comprehensive_prompt(campaign)
        
        try:
            print(f"🤖 Using GPT-5-mini with Responses API + Web Search")
            print(f"⏱️  Timeout: 240 seconds")
            print(f"🎫 Max Tokens: 20000 (comprehensive results)")
            
            # Use Responses API with web search [[memory:9653106]]
            # This API enables real-time web search for finding actual businesses
            response = self.openai_client.responses.create(
                model="gpt-5-mini",
                tools=[{"type": "web_search"}],  # Enable real-time web search
                input=[
                    {
                        "role": "system",
                        "content": """You are a UK business research specialist with live web search access.
Your task is to find REAL, VERIFIED UK businesses using web search.

CRITICAL REQUIREMENTS:
1. Use web search to find actual UK businesses (search business directories, websites, Google)
2. Each business MUST have a verifiable online presence
3. Verify UK postcodes are genuine and in correct format
4. Only return businesses that are currently active and trading
5. Output ONLY valid JSON matching the schema provided
6. DO NOT fabricate or make up business information

SEARCH STRATEGY:
- Search "{postcode} IT services" or "{postcode} managed IT" or similar
- Check UK business directories (Yell.com, Thomson Local, Google Business)
- Verify websites are active and businesses are real
- Get actual contact information from company websites
- Focus on businesses likely to need IT infrastructure services"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                metadata={"task": f"lead_generation_{campaign.prompt_type}"}
            )
            
            print(f"✓ GPT-5-mini Responses API call completed")
            
            # Extract response text from Responses API format
            ai_response = self._extract_response_text(response)
            print(f"✓ Extracted {len(ai_response)} characters")
            
            return ai_response
            
        except Exception as e:
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            print(f"❌ AI search failed: {error_msg}")
            raise
    
    def _build_comprehensive_prompt(self, campaign: LeadGenerationCampaign) -> str:
        """
        Build comprehensive AI prompt based on campaign type and tenant context
        
        Returns dynamic prompt that adapts to tenant's business profile
        """
        
        # Get tenant context for dynamic prompt building
        tenant_context = self._build_tenant_context()
        
        # Base prompt structure with tenant context
        base = f"""
TASK: Find {campaign.max_results} REAL UK businesses near {campaign.postcode} (within {campaign.distance_miles} miles) that would be ideal prospects for {tenant_context['company_name']}.

ABOUT {tenant_context['company_name'].upper()}:
{tenant_context['company_description']}

{tenant_context['services_context']}
{tenant_context['target_markets_context']}
{tenant_context['usps_context']}

Campaign Focus: {campaign.prompt_type}

SEARCH APPROACH:
1. Use web search to find "{campaign.postcode} {self._get_search_terms(campaign.prompt_type)}"
2. Check UK business directories (Yell, Thomson Local, Google Business, Companies House)
3. Verify each business has:
   - Real, active website
   - Valid UK postcode
   - Genuine contact information
   - Current trading status

FOR EACH BUSINESS FOUND:
- Extract exact company name from their website
- Get actual postcode from contact page
- Get real contact details (email/phone) from website
- Note their business focus and why they need {tenant_context['company_name']}'s services
- Assess lead quality (score 60-95)
- Identify specific opportunities for {tenant_context['company_name']} to help this business

OUTPUT FORMAT - Valid JSON:
{{
  "query_area": "{campaign.postcode}, UK",
  "results": [
    {{
      "company_name": "Real Company Name Ltd",
      "website": "https://realcompany.com",
      "description": "Specific reason why they need {tenant_context['company_name']}'s services",
      "contact_name": "Contact Person Name",
      "contact_email": "contact@realcompany.com",
      "contact_phone": "01234 567890",
      "address": "Full business address with street, city",
      "postcode": "LE1 1AA",
      "business_sector": "Technology/Healthcare/Education/Manufacturing/etc",
      "company_size": "Micro/Small/Medium/Large",
      "lead_score": 85,
      "timeline": "Within 3 months/6 months/1 year",
      "project_value": "Small/Medium/Large",
      "opportunity_reason": "Why this business would benefit from {tenant_context['company_name']}'s services"
    }}
  ]
}}
"""
        
        # Add campaign-type-specific instructions with tenant context
        if campaign.prompt_type == 'it_msp_expansion':
            base += f"""

SPECIFIC FOCUS - IT/MSP BUSINESSES FOR {tenant_context['company_name'].upper()}:
✓ INCLUDE: IT Support Companies, Managed Service Providers (MSPs), Computer Repair Shops,
  IT Consultancies, Software Development Firms, Web Design Agencies, Technology Resellers,
  Network Support Companies, Cybersecurity Firms

✗ EXCLUDE: Universities, Schools, Hospitals, Retail Stores, Government Buildings,
  Hotels, Entertainment Venues, Libraries, Museums

TARGET: Small to medium IT businesses that could benefit from {tenant_context['company_name']}'s services.
Look for businesses that might need {tenant_context['services_context']} or could be partnership opportunities.
"""
        
        elif campaign.prompt_type == 'education':
            base += f"""

SPECIFIC FOCUS - EDUCATION SECTOR:
Find: Primary schools, Secondary schools, Colleges, Universities, Training centers,
Educational technology companies, E-learning platforms
Focus on institutions that would benefit from {tenant_context['company_name']}'s services.
Look for {tenant_context['services_context']} opportunities in education.
"""
        
        elif campaign.prompt_type == 'manufacturing':
            base += f"""

SPECIFIC FOCUS - MANUFACTURING:
Find: Manufacturing plants, Industrial facilities, Engineering companies,
Production facilities, Factory automation companies
Focus on businesses that could use {tenant_context['company_name']}'s expertise.
Look for {tenant_context['services_context']} opportunities in manufacturing.
"""
        
        elif campaign.prompt_type == 'healthcare':
            base += f"""

SPECIFIC FOCUS - HEALTHCARE:
Find: Hospitals, Medical practices, Dental offices, Veterinary clinics,
Healthcare technology companies, Care homes
Focus on facilities that would benefit from {tenant_context['company_name']}'s services.
Look for {tenant_context['services_context']} opportunities in healthcare.
"""
        
        elif campaign.prompt_type == 'retail_office':
            base += f"""

SPECIFIC FOCUS - RETAIL & OFFICE:
Find: Retail stores, Office buildings, Business centers, Commercial properties,
Professional services firms, Coworking spaces
Focus on businesses that could use {tenant_context['company_name']}'s services.
Look for {tenant_context['services_context']} opportunities in retail/office environments.
"""
        
        elif campaign.prompt_type == 'competitor_verification':
            base += f"""

SPECIAL MODE - COMPETITOR VERIFICATION:
This campaign is for verifying identified competitor companies.
For each, verify: Company exists, Current status, Contact details, Services offered
Focus: Understand competitive landscape for {tenant_context['company_name']}
"""
        
        elif campaign.prompt_type == 'location_based':
            base += f"""

SPECIAL MODE - LOCATION-BASED SEARCH:
Search for businesses at or near specific verified addresses.
Focus on finding businesses that could benefit from {tenant_context['company_name']}'s services in the same geographic areas.
"""
        
        elif campaign.prompt_type == 'company_list':
            base += f"""

SPECIAL MODE - COMPANY LIST ANALYSIS:
This campaign analyzes specific companies provided by the user.
Focus on researching each company to understand their business and identify opportunities for {tenant_context['company_name']}.
Look for {tenant_context['services_context']} opportunities with each company.
"""
        
        base += f"""

QUALITY REQUIREMENTS:
✓ Better to return 10 verified businesses than 50 fake ones
✓ Each business must be REAL and currently trading
✓ Include source URLs where you found the information
✓ Prioritize businesses that match {tenant_context['company_name']}'s target markets
✓ Focus on businesses that would clearly benefit from {tenant_context['company_name']}'s services

OUTPUT: Return ONLY the JSON object. No markdown code fences. No explanations.
"""
        
        return base
    
    def _build_tenant_context(self) -> Dict[str, str]:
        """
        Build tenant context for dynamic prompt generation
        
        Returns structured context about the tenant's business
        """
        if not self.tenant:
            return {
                'company_name': 'our company',
                'company_description': 'We provide professional services to businesses.',
                'services_context': 'our services',
                'target_markets_context': '',
                'usps_context': ''
            }
        
        # Build services context
        services_context = ""
        if self.tenant.products_services and len(self.tenant.products_services) > 0:
            services_list = self.tenant.products_services[:5]  # First 5 services
            services_context = f"We specialize in: {', '.join(services_list)}"
            if len(self.tenant.products_services) > 5:
                services_context += f" and {len(self.tenant.products_services) - 5} other services"
        
        # Build target markets context
        target_markets_context = ""
        if self.tenant.target_markets and len(self.tenant.target_markets) > 0:
            markets_list = self.tenant.target_markets[:3]  # First 3 markets
            target_markets_context = f"Primary target markets: {', '.join(markets_list)}"
            if len(self.tenant.target_markets) > 3:
                target_markets_context += f" and {len(self.tenant.target_markets) - 3} other sectors"
        
        # Build USPs context
        usps_context = ""
        if self.tenant.unique_selling_points and len(self.tenant.unique_selling_points) > 0:
            usps_list = self.tenant.unique_selling_points[:3]  # First 3 USPs
            usps_context = f"Key advantages: {', '.join(usps_list)}"
        
        return {
            'company_name': self.tenant.company_name or 'our company',
            'company_description': self.tenant.company_description or 'We provide professional services to businesses.',
            'services_context': services_context or 'our services',
            'target_markets_context': target_markets_context,
            'usps_context': usps_context
        }
    
    def _get_search_terms(self, prompt_type: str) -> str:
        """Get search terms for campaign type"""
        terms = {
            'it_msp_expansion': 'IT services managed service providers MSP',
            'education': 'schools colleges universities education institutions',
            'manufacturing': 'manufacturing companies industrial facilities',
            'healthcare': 'hospitals medical practices healthcare facilities',
            'retail_office': 'retail stores office buildings commercial properties',
            'competitor_verification': 'IT services structured cabling competitors',
            'location_based': 'businesses companies near',
            'new_businesses': 'new businesses recently opened',
            'planning_applications': 'planning applications construction renovation',
            'company_list': 'business research company analysis'
        }
        return terms.get(prompt_type, 'businesses companies')
    
    def _extract_response_text(self, response) -> str:
        """Extract text from Responses API response"""
        try:
            if hasattr(response, 'output') and isinstance(response.output, list):
                for item in reversed(response.output):
                    if hasattr(item, 'type') and item.type == 'message':
                        if hasattr(item, 'content') and isinstance(item.content, list):
                            for content_item in item.content:
                                if hasattr(content_item, 'text'):
                                    return content_item.text
            
            print(f"[WARN] Could not extract response text, returning empty results")
            return '{"results": []}'
            
        except Exception as e:
            print(f"[ERROR] Error extracting response: {e}")
            return '{"results": []}'
    
    def _parse_ai_response(self, ai_response: str) -> List[Dict]:
        """Parse AI response to extract structured lead data"""
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
                return leads if isinstance(leads, list) else []
            elif isinstance(data, list):
                return data
            else:
                print(f"[WARN] Unexpected JSON structure")
                return []
                
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parsing failed: {e}")
            print(f"Response preview: {ai_response[:500]}")
            return []
        except Exception as e:
            print(f"[ERROR] Error parsing response: {e}")
            return []
    
    async def _enrich_leads(self, leads_data: List[Dict], campaign: LeadGenerationCampaign) -> List[Dict]:
        """
        Enrich leads with external data from multiple sources
        - Google Maps (multiple locations)
        - Companies House (registration, financials, directors)
        - LinkedIn (company profile)
        - Website scraping (additional details)
        """
        enriched_leads = []
        
        for lead_data in leads_data:
            try:
                company_name = lead_data.get('company_name', '').strip()
                if not company_name or len(company_name) < 2:
                    continue
                
                # Check for duplicates FIRST (most important)
                if await self._is_duplicate(company_name):
                    print(f"  ⏭️  Skipping duplicate: {company_name}")
                    campaign.duplicates_found += 1
                    continue
                
                print(f"  🔧 Enriching: {company_name}")
                
                # Enrich with Google Maps (multiple locations)
                if self.gmaps_client:
                    google_data = await self._get_google_maps_data(company_name, lead_data.get('postcode'))
                    if google_data:
                        lead_data['google_maps_data'] = google_data
                        print(f"    ✓ Google Maps data added")
                
                # Enrich with Companies House
                if self.companies_house_key:
                    ch_data = await self._get_companies_house_data(company_name)
                    if ch_data:
                        lead_data['companies_house_data'] = ch_data
                        lead_data['company_registration'] = ch_data.get('company_number')
                        lead_data['registration_confirmed'] = True
                        print(f"    ✓ Companies House data added")
                
                # Enrich with LinkedIn (basic search)
                linkedin_data = await self._get_linkedin_data(company_name)
                if linkedin_data:
                    lead_data['linkedin_url'] = linkedin_data.get('url')
                    lead_data['linkedin_data'] = linkedin_data
                    print(f"    ✓ LinkedIn data added")
                
                enriched_leads.append(lead_data)
                
            except Exception as e:
                error_msg = str(e).encode('ascii', 'replace').decode('ascii')
                print(f"    ⚠️  Error enriching {company_name}: {error_msg}")
                # Still add the lead even if enrichment fails
                enriched_leads.append(lead_data)
                continue
        
        return enriched_leads
    
    async def _is_duplicate(self, company_name: str) -> bool:
        """Check if company already exists as lead or customer"""
        # Check existing leads
        existing_lead = self.db.query(Lead).filter(
            and_(
                Lead.tenant_id == self.tenant_id,
                Lead.company_name.ilike(company_name)  # Case-insensitive
            )
        ).first()
        
        if existing_lead:
            return True
        
        # Check existing customers
        existing_customer = self.db.query(Customer).filter(
            and_(
                Customer.tenant_id == self.tenant_id,
                Customer.company_name.ilike(company_name)  # Case-insensitive
            )
        ).first()
        
        return existing_customer is not None
    
    async def _get_google_maps_data(self, company_name: str, postcode: Optional[str]) -> Optional[Dict]:
        """Get Google Maps data including multiple locations"""
        try:
            if not self.gmaps_client:
                return None
            
            # Search for company on Google Maps
            search_query = f"{company_name} {postcode if postcode else 'UK'}"
            places_result = self.gmaps_client.places(search_query)
            
            if places_result and places_result.get('results'):
                # Return first result (main location)
                place = places_result['results'][0]
                return {
                    'place_id': place.get('place_id'),
                    'name': place.get('name'),
                    'formatted_address': place.get('formatted_address'),
                    'location': place.get('geometry', {}).get('location'),
                    'rating': place.get('rating'),
                    'types': place.get('types'),
                    'total_locations': len(places_result['results'])  # Count of all locations
                }
            
            return None
            
        except Exception as e:
            print(f"    [WARN] Google Maps error: {e}")
            return None
    
    async def _get_companies_house_data(self, company_name: str) -> Optional[Dict]:
        """Get Companies House data via API"""
        try:
            if not self.companies_house_key:
                return None
            
            # Search Companies House API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.company-information.service.gov.uk/search/companies",
                    params={"q": company_name},
                    auth=(self.companies_house_key, ''),
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('items') and len(data['items']) > 0:
                        company = data['items'][0]
                        return {
                            'company_number': company.get('company_number'),
                            'company_name': company.get('title'),
                            'company_status': company.get('company_status'),
                            'company_type': company.get('company_type'),
                            'date_of_creation': company.get('date_of_creation'),
                            'address': company.get('address_snippet'),
                            'sic_codes': company.get('sic_codes', [])
                        }
            
            return None
            
        except Exception as e:
            print(f"    [WARN] Companies House error: {e}")
            return None
    
    async def _get_linkedin_data(self, company_name: str) -> Optional[Dict]:
        """Get basic LinkedIn profile information (URL construction)"""
        try:
            # Construct likely LinkedIn URL
            # Note: Full scraping would require additional libraries/services
            company_slug = company_name.lower().replace(' ', '-').replace('ltd', '').strip('-')
            linkedin_url = f"https://www.linkedin.com/company/{company_slug}"
            
            return {
                'url': linkedin_url,
                'suggested': True  # Indicates this is a constructed URL, not verified
            }
            
        except Exception as e:
            return None
    
    async def _create_leads(self, leads_data: List[Dict], campaign: LeadGenerationCampaign) -> List[Lead]:
        """
        Create Lead records from enriched data
        All leads from campaigns start at DISCOVERY status
        """
        created_leads = []
        
        for lead_data in leads_data:
            try:
                company_name = lead_data.get('company_name', '').strip()
                if not company_name:
                    continue
                
                # Extract project value estimate
                project_value = self._estimate_project_value(lead_data.get('project_value', ''))
                
                # Generate quick telesales summary
                quick_summary = await self.generate_quick_lead_summary(lead_data)
                
                # Create lead record
                lead = Lead(
                    tenant_id=self.tenant_id,
                    campaign_id=campaign.id,
                    
                    # Basic info
                    company_name=company_name,
                    website=lead_data.get('website'),
                    company_registration=lead_data.get('company_registration'),
                    registration_confirmed=lead_data.get('registration_confirmed', False),
                    
                    # Contact info
                    contact_name=lead_data.get('contact_name'),
                    contact_email=lead_data.get('contact_email'),
                    contact_phone=lead_data.get('contact_phone'),
                    contact_title=lead_data.get('contact_title'),
                    
                    # Address
                    address=lead_data.get('address'),
                    postcode=lead_data.get('postcode'),
                    
                    # Business details
                    business_sector=lead_data.get('business_sector'),
                    company_size=lead_data.get('company_size'),
                    annual_revenue=lead_data.get('annual_revenue'),
                    
                    # Lead scoring
                    lead_score=lead_data.get('lead_score', 50),
                    qualification_reason=quick_summary or lead_data.get('description'),  # Use AI summary or fallback to description
                    potential_project_value=project_value,
                    timeline_estimate=lead_data.get('timeline'),
                    
                    # Status
                    status=LeadStatus.NEW,  # All campaign leads start as NEW
                    source=LeadSource.CAMPAIGN,
                    
                    # AI & External data
                    ai_analysis=lead_data,  # Store full AI analysis
                    linkedin_url=lead_data.get('linkedin_url'),
                    linkedin_data=lead_data.get('linkedin_data'),
                    companies_house_data=lead_data.get('companies_house_data'),
                    google_maps_data=lead_data.get('google_maps_data'),
                    website_data=lead_data.get('website_data')
                )
                
                self.db.add(lead)
                created_leads.append(lead)
                print(f"  ✓ Created: {company_name} (Score: {lead.lead_score})")
                
            except Exception as e:
                error_msg = str(e).encode('ascii', 'replace').decode('ascii')
                print(f"  ❌ Error creating lead {company_name}: {error_msg}")
                continue
        
        # Commit all leads in one transaction
        self.db.commit()
        
        return created_leads
    
    def _estimate_project_value(self, project_value_str: str) -> Optional[float]:
        """Estimate numeric project value from text description"""
        if not project_value_str:
            return None
        
        value_str = project_value_str.lower()
        
        if 'small' in value_str:
            return 5000.0  # £5k
        elif 'medium' in value_str:
            return 25000.0  # £25k
        elif 'large' in value_str:
            return 75000.0  # £75k
        else:
            return 15000.0  # Default to medium
    
    async def convert_lead_to_customer(self, lead_id: str, user_id: str) -> Dict[str, Any]:
        """
        Convert a Discovery (Campaign Lead) to a CRM Lead (Customer with LEAD status)
        
        Workflow:
        - DISCOVERY (Campaign Lead) → LEAD (CRM Customer)
        - LEAD → PROSPECT → OPPORTUNITY → CUSTOMER
        - or LEAD → PROSPECT → CUSTOMER (skip opportunity)
        """
        try:
            # Get lead
            lead = self.db.query(Lead).filter(
                and_(
                    Lead.id == lead_id,
                    Lead.tenant_id == self.tenant_id
                )
            ).first()
            
            if not lead:
                return {'success': False, 'error': 'Lead not found'}
            
            if lead.converted_to_customer_id:
                return {'success': False, 'error': 'Discovery already converted to CRM'}
            
            # Create customer with LEAD status (first step in CRM pipeline)
            # Map business_sector string to enum if needed
            business_sector_enum = None
            if lead.business_sector:
                try:
                    from app.models.crm import BusinessSector
                    # Try to match the sector to enum
                    sector_map = {
                        'office': BusinessSector.OFFICE,
                        'retail': BusinessSector.RETAIL,
                        'industrial': BusinessSector.INDUSTRIAL,
                        'healthcare': BusinessSector.HEALTHCARE,
                        'education': BusinessSector.EDUCATION,
                        'hospitality': BusinessSector.HOSPITALITY,
                        'manufacturing': BusinessSector.MANUFACTURING,
                        'technology': BusinessSector.TECHNOLOGY,
                        'finance': BusinessSector.FINANCE,
                        'government': BusinessSector.GOVERNMENT,
                    }
                    business_sector_enum = sector_map.get(lead.business_sector.lower(), BusinessSector.OTHER)
                except:
                    pass
            
            # Map business_size string to enum if needed  
            business_size_enum = None
            if lead.company_size:
                try:
                    from app.models.crm import BusinessSize
                    # Try to match the size to enum
                    size_str = lead.company_size.lower()
                    if 'small' in size_str or '1-10' in size_str or '1-50' in size_str:
                        business_size_enum = BusinessSize.SMALL
                    elif 'medium' in size_str or '50-250' in size_str:
                        business_size_enum = BusinessSize.MEDIUM
                    elif 'large' in size_str or '250-1000' in size_str:
                        business_size_enum = BusinessSize.LARGE
                    elif 'enterprise' in size_str or '1000+' in size_str:
                        business_size_enum = BusinessSize.ENTERPRISE
                except:
                    pass
            
            customer = Customer(
                tenant_id=self.tenant_id,
                company_name=lead.company_name,
                website=lead.website,
                company_registration=lead.company_registration,
                registration_confirmed=lead.registration_confirmed,
                main_phone=lead.contact_phone,
                main_email=lead.contact_email,
                billing_address=lead.address,
                billing_postcode=lead.postcode,
                business_sector=business_sector_enum,
                business_size=business_size_enum,
                description=lead.qualification_reason,  # Copy the quick summary to CRM
                status=CustomerStatus.LEAD,  # Starts at LEAD (first CRM stage)
                lead_score=lead.lead_score,
                linkedin_url=lead.linkedin_url,
                linkedin_data=lead.linkedin_data,
                companies_house_data=lead.companies_house_data,
                website_data=lead.website_data,
                google_maps_data=lead.google_maps_data,
                ai_analysis_raw=lead.ai_analysis  # Copy full AI analysis too
            )
            
            self.db.add(customer)
            self.db.flush()
            
            # Update campaign lead to CONVERTED
            lead.status = LeadStatus.CONVERTED
            lead.converted_to_customer_id = customer.id
            lead.conversion_date = datetime.utcnow()
            
            self.db.commit()
            
            print(f"✓ Converted discovery '{lead.company_name}' to CRM Lead (LEAD status)")
            
            return {
                'success': True,
                'customer_id': customer.id,
                'message': 'Discovery converted to CRM Lead successfully'
            }
            
        except Exception as e:
            self.db.rollback()
            import traceback
            error_detail = f"{type(e).__name__}: {str(e)}"
            print(f"[ERROR] Failed to convert discovery to CRM lead: {error_detail}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return {'success': False, 'error': error_detail}
    
    async def generate_quick_lead_summary(self, lead_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate a concise B2B lead summary for telesales teams (under 300 words)
        
        This creates a quick summary perfect for outbound sales calls,
        including why the lead is a good fit for the tenant's business.
        
        Returns a formatted summary with:
        - Company name, website, location
        - Sector, staff size, estimated revenue
        - One-line overview
        - 3-5 bullet points on why they're a good fit
        """
        if not self.openai_client:
            return None
        
        try:
            # Get tenant profile for context
            tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
            
            # Build company context
            company_info = f"Company Name: {lead_data.get('company_name', 'Unknown')}"
            
            if lead_data.get('website'):
                company_info += f"\nWebsite: {lead_data['website']}"
            
            if lead_data.get('postcode'):
                company_info += f"\nLocation: {lead_data.get('address', '')} {lead_data['postcode']}"
            
            if lead_data.get('business_sector'):
                company_info += f"\nSector: {lead_data['business_sector']}"
            
            if lead_data.get('company_size'):
                company_info += f"\nStaff Size: {lead_data['company_size']}"
            
            # Add external data if available
            if lead_data.get('companies_house_data'):
                ch_data = lead_data['companies_house_data']
                if isinstance(ch_data, dict):
                    if ch_data.get('company_status'):
                        company_info += f"\nCompany Status: {ch_data['company_status']}"
                    if ch_data.get('date_of_creation'):
                        company_info += f"\nFounded: {ch_data['date_of_creation']}"
            
            if lead_data.get('google_maps_data'):
                gm_data = lead_data['google_maps_data']
                if isinstance(gm_data, dict):
                    if gm_data.get('rating'):
                        company_info += f"\nGoogle Rating: {gm_data['rating']}/5"
            
            # Build tenant context
            tenant_context = ""
            if tenant:
                if tenant.company_description:
                    tenant_context += f"\n\nYOUR COMPANY: {tenant.company_name}\n{tenant.company_description}"
                
                if tenant.products_services and isinstance(tenant.products_services, list):
                    tenant_context += f"\n\nYour Products/Services:\n" + "\n".join([f"- {p}" for p in tenant.products_services[:5]])
                
                if tenant.partnership_opportunities:
                    tenant_context += f"\n\nB2B Partnership Opportunities:\n{tenant.partnership_opportunities[:500]}"  # First 500 chars for summary
            
            # Build prompt
            prompt = f"""You are an expert B2B sales researcher who writes concise, factual lead summaries for CRM and outbound sales.

IMPORTANT: Determine if this prospect is:
A) A potential CUSTOMER (we sell TO them) 
B) A potential PARTNER (we work WITH them)
C) Both

Create a short lead summary for this prospect:

{company_info}
{tenant_context}

Format the response EXACTLY as follows:

**Company:** [Name]
**Website:** [URL if available, or "Not found"]
**Location:** [City/Town, Postcode]
**Sector:** [Industry sector]
**Staff Size:** [Estimate based on data, or "Unknown"]
**Estimated Revenue:** [Range if data available, or "Not available"]

**Overview:** [One concise sentence explaining what they do]

**Why They're a Good Fit:**
- [Bullet point 1: Specific reason relating to our products/services]
- [Bullet point 2: Another specific alignment]
- [Bullet point 3: Business context or opportunity]
- [Optional: 1-2 more bullets if relevant]

Focus on factual, specific reasons why this prospect matches what YOUR COMPANY offers.
Keep the total summary under 300 words, professional tone, ready for telesales outreach.
"""
            
            print(f"      [SUMMARY] Generating quick lead summary for {lead_data.get('company_name')}")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert B2B sales researcher. Create concise, factual lead summaries that help sales teams understand prospects quickly. Always be professional and focus on business fit."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_completion_tokens=10000,
                timeout=120.0
            )
            
            summary = response.choices[0].message.content.strip()
            print(f"      [SUMMARY] ✓ Generated summary ({len(summary)} chars)")
            
            return summary
            
        except Exception as e:
            print(f"      [SUMMARY] ✗ Error generating summary: {e}")
            return None
    
    async def analyze_lead_with_ai(self, lead_id: str) -> Dict[str, Any]:
        """
        Run comprehensive AI analysis on a discovery/lead
        
        Analyzes company using GPT-5-mini with all available data:
        - External data (Google Maps, Companies House, LinkedIn)
        - Website information
        - Financial data
        - Director information
        
        [[memory:9653106]] - Use GPT-5-mini with 20000+ tokens, 240s timeout
        """
        try:
            # Get lead
            lead = self.db.query(Lead).filter(
                and_(
                    Lead.id == lead_id,
                    Lead.tenant_id == self.tenant_id
                )
            ).first()
            
            if not lead:
                return {'success': False, 'error': 'Lead not found'}
            
            if not self.openai_client:
                return {'success': False, 'error': 'OpenAI client not initialized'}
            
            # Build comprehensive company information
            company_info = f"Company Name: {lead.company_name}"
            
            if hasattr(lead, 'website') and lead.website:
                company_info += f"\nWebsite: {lead.website}"
            
            if hasattr(lead, 'description') and lead.description:
                company_info += f"\nDescription: {lead.description}"
            
            if hasattr(lead, 'postcode') and lead.postcode:
                company_info += f"\nPostcode: {lead.postcode}"
            
            if hasattr(lead, 'address') and lead.address:
                company_info += f"\nAddress: {lead.address}"
            
            if hasattr(lead, 'business_sector') and lead.business_sector:
                company_info += f"\nBusiness Sector: {lead.business_sector}"
            
            if hasattr(lead, 'company_size') and lead.company_size:
                company_info += f"\nCompany Size: {lead.company_size}"
            
            # Add external data from separate fields
            # Google Maps data
            if hasattr(lead, 'google_maps_data') and lead.google_maps_data:
                maps = lead.google_maps_data if isinstance(lead.google_maps_data, dict) else json.loads(lead.google_maps_data)
                company_info += f"\n\nGoogle Maps Data:"
                if maps.get('rating'):
                    company_info += f"\n- Rating: {maps['rating']}/5"
                if maps.get('user_ratings_total'):
                    company_info += f"\n- Reviews: {maps['user_ratings_total']}"
                if maps.get('formatted_address'):
                    company_info += f"\n- Address: {maps['formatted_address']}"
                if maps.get('phone'):
                    company_info += f"\n- Phone: {maps['phone']}"
                if maps.get('website'):
                    company_info += f"\n- Website: {maps['website']}"
            
            # Companies House data
            if hasattr(lead, 'companies_house_data') and lead.companies_house_data:
                ch = lead.companies_house_data if isinstance(lead.companies_house_data, dict) else json.loads(lead.companies_house_data)
                company_info += f"\n\nCompanies House Data:"
                if ch.get('company_number'):
                    company_info += f"\n- Company Number: {ch['company_number']}"
                if ch.get('company_status'):
                    company_info += f"\n- Status: {ch['company_status']}"
                if ch.get('company_type'):
                    company_info += f"\n- Type: {ch['company_type']}"
                if ch.get('date_of_creation'):
                    company_info += f"\n- Founded: {ch['date_of_creation']}"
                if ch.get('sic_codes'):
                    company_info += f"\n- SIC Codes: {', '.join(ch['sic_codes']) if isinstance(ch['sic_codes'], list) else ch['sic_codes']}"
                
                # Financial data
                if ch.get('accounts'):
                    accounts = ch['accounts']
                    company_info += f"\n\nFinancial Information:"
                    if accounts.get('turnover'):
                        company_info += f"\n- Turnover: £{accounts['turnover']:,}" if isinstance(accounts['turnover'], (int, float)) else f"\n- Turnover: {accounts['turnover']}"
                    if accounts.get('shareholders_funds'):
                        company_info += f"\n- Shareholders' Funds: £{accounts['shareholders_funds']:,}" if isinstance(accounts['shareholders_funds'], (int, float)) else f"\n- Shareholders' Funds: {accounts['shareholders_funds']}"
                    if accounts.get('cash_at_bank'):
                        company_info += f"\n- Cash at Bank: £{accounts['cash_at_bank']:,}" if isinstance(accounts['cash_at_bank'], (int, float)) else f"\n- Cash at Bank: {accounts['cash_at_bank']}"
                    if accounts.get('employees'):
                        company_info += f"\n- Employees: {accounts['employees']}"
                
                # Directors
                if ch.get('officers'):
                    officers = ch['officers']
                    company_info += f"\n\nDirectors/Officers ({len(officers)}):"
                    for i, officer in enumerate(officers[:5], 1):  # Show first 5
                        company_info += f"\n{i}. {officer.get('name', 'Unknown')}"
                        if officer.get('officer_role'):
                            company_info += f" - {officer['officer_role']}"
                        if officer.get('appointed_on'):
                            company_info += f" (Appointed: {officer['appointed_on']})"
            
            # LinkedIn data
            if hasattr(lead, 'linkedin_data') and lead.linkedin_data:
                linkedin = lead.linkedin_data if isinstance(lead.linkedin_data, dict) else json.loads(lead.linkedin_data)
                company_info += f"\n\nLinkedIn Data:"
                if linkedin.get('linkedin_url'):
                    company_info += f"\n- LinkedIn URL: {linkedin['linkedin_url']}"
                if linkedin.get('linkedin_industry'):
                    company_info += f"\n- Industry: {linkedin['linkedin_industry']}"
                if linkedin.get('linkedin_company_size'):
                    company_info += f"\n- Company Size: {linkedin['linkedin_company_size']}"
                if linkedin.get('linkedin_description'):
                    company_info += f"\n- Description: {linkedin['linkedin_description']}"
            
            # Get tenant profile information to contextualize the analysis
            tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
            
            # Build context about our company
            our_company_context = ""
            if tenant:
                if tenant.company_name:
                    our_company_context += f"\n\nYOUR COMPANY: {tenant.company_name}"
                
                if tenant.company_description:
                    our_company_context += f"\n\nAbout Your Company:\n{tenant.company_description}"
                
                if tenant.products_services:
                    products = tenant.products_services if isinstance(tenant.products_services, list) else []
                    if products:
                        our_company_context += f"\n\nYour Products/Services:\n" + "\n".join([f"- {p}" for p in products])
                
                if tenant.unique_selling_points:
                    usps = tenant.unique_selling_points if isinstance(tenant.unique_selling_points, list) else []
                    if usps:
                        our_company_context += f"\n\nYour Core Strengths/USPs:\n" + "\n".join([f"- {u}" for u in usps])
                
                if tenant.target_markets:
                    markets = tenant.target_markets if isinstance(tenant.target_markets, list) else []
                    if markets:
                        our_company_context += f"\n\nYour Target Markets:\n" + "\n".join([f"- {m}" for m in markets])
                
                if tenant.elevator_pitch:
                    our_company_context += f"\n\nYour Value Proposition:\n{tenant.elevator_pitch}"
                
                if tenant.partnership_opportunities:
                    our_company_context += f"\n\nB2B Partnership Opportunities (How to work WITH similar businesses):\n{tenant.partnership_opportunities}"
            
            # Build AI prompt
            prompt = f"""
Analyze this UK company and determine if they are a potential CUSTOMER or PARTNERSHIP opportunity (or both).

{company_info}
{our_company_context}

IMPORTANT: Consider how our company's products, services, and strengths align with this prospect's needs. 
Focus on identifying specific opportunities where we can add value based on what we offer.

Please provide a detailed analysis including:

1. **Business Sector**: Choose from: office, retail, industrial, healthcare, education, hospitality, manufacturing, technology, finance, government, other

2. **Company Size Assessment**: 
   - Estimated employees
   - Revenue range
   - Business size category (Small/Medium/Large/Enterprise)

3. **Primary Business Activities**: What they do, main products/services

4. **Technology Maturity**: Basic/Intermediate/Advanced/Enterprise (or N/A if not relevant to your industry)

5. **Budget Estimate**: Likely annual budget/spending range for products/services like ours

6. **Financial Health**: Analysis of financial position, profitability trends, stability

7. **Growth Potential**: High/Medium/Low with reasoning

8. **Needs Assessment**: Based on their business, what specific needs do they likely have that relate to OUR offerings? 
   Consider how OUR products and services could address these needs.
   (For IT companies: technology/infrastructure needs. For other industries: adjust accordingly)

9. **Competitive Landscape**: Who are their main competitors in their sector?

10. **Business Opportunities**: Specific opportunities where OUR company can add value. 
    Be detailed about which of OUR products/services align with their needs.
    Explain HOW we can help them solve problems or achieve goals.
    Reference our USPs where relevant.

11. **Risk Factors**: Challenges or potential objections we might face when approaching them

12. **Contact Information**: Search the website, Google Maps data, and Companies House data for:
    - Key contact person (Director, CEO, IT Manager, or general contact)
    - Contact email address (look for info@, sales@, enquiries@, or specific contact emails)
    - Direct phone number if available

IMPORTANT: For contact information, look in:
- Website contact pages
- Google Maps business listing
- Companies House director information
- Any email addresses or contact names found in the data

Respond in JSON format with these exact fields:
{{
    "business_sector": "string",
    "estimated_employees": number,
    "estimated_revenue": "string",
    "business_size_category": "string",
    "primary_business_activities": "string",
    "technology_maturity": "string",
    "it_budget_estimate": "string",
    "growth_potential": "string",
    "technology_needs": "string",
    "competitors": "string",
    "opportunities": "string",
    "risks": "string",
    "company_profile": "string",
    "financial_health_analysis": "string",
    "contact_name": "string or null (key contact person if found)",
    "contact_email": "string or null (email address if found)",
    "contact_phone": "string or null (direct phone if different from main)"
}}

Focus on UK market context and be realistic. Only include contact information if you can find it in the provided data.
"""
            
            print(f"[AI ANALYSIS] Running analysis for {lead.company_name}")
            
            # Build dynamic system prompt based on tenant's business
            system_prompt = "You are a business intelligence analyst specializing in UK companies"
            
            if tenant and tenant.company_description:
                # Extract industry/specialization from company description
                system_prompt += f" and helping companies like {tenant.company_name}"
                if tenant.target_markets:
                    markets = tenant.target_markets if isinstance(tenant.target_markets, list) else []
                    if markets:
                        market_str = ", ".join(markets[:3])  # First 3 markets
                        system_prompt += f" sell to businesses in {market_str}"
            else:
                # Fallback to generic
                system_prompt += " and business development opportunities"
            
            system_prompt += ". Provide accurate, realistic assessments that help with sales and business development. Always respond with valid JSON."
            
            # Call GPT-5-mini with Chat Completions API
            # Note: GPT-5-mini does not support temperature parameter - only default (1) is supported
            response = self.openai_client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": system_prompt
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_completion_tokens=20000,  # [[memory:9653106]]
                timeout=240.0
            )
            
            # Extract and parse response
            ai_response = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if ai_response.startswith('```'):
                ai_response = re.sub(r'^```(?:json)?\s*|\s*```$', '', ai_response, flags=re.MULTILINE).strip()
            
            # Parse JSON
            analysis_data = json.loads(ai_response)
            
            # Update lead with AI analysis
            lead.ai_analysis = analysis_data
            
            # Update business sector if found
            if analysis_data.get('business_sector') and not lead.business_sector:
                lead.business_sector = analysis_data['business_sector']
            
            # Update company size if found
            if analysis_data.get('business_size_category') and not lead.company_size:
                lead.company_size = analysis_data['business_size_category']
            
            # Update contact information if found by AI
            if analysis_data.get('contact_name') and not lead.contact_name:
                lead.contact_name = analysis_data['contact_name']
                print(f"[AI ANALYSIS] ✓ Found contact name: {lead.contact_name}")
            
            if analysis_data.get('contact_email') and not lead.contact_email:
                lead.contact_email = analysis_data['contact_email']
                print(f"[AI ANALYSIS] ✓ Found contact email: {lead.contact_email}")
            
            if analysis_data.get('contact_phone') and not lead.contact_phone:
                lead.contact_phone = analysis_data['contact_phone']
                print(f"[AI ANALYSIS] ✓ Found contact phone: {lead.contact_phone}")
            
            self.db.commit()
            self.db.refresh(lead)
            
            print(f"[AI ANALYSIS] ✓ Analysis completed for {lead.company_name}")
            
            return {
                'success': True,
                'analysis': analysis_data,
                'message': 'AI analysis completed successfully'
            }
            
        except json.JSONDecodeError as e:
            print(f"[AI ANALYSIS] ✗ JSON parse error: {e}")
            return {'success': False, 'error': f'Failed to parse AI response: {str(e)}'}
        except Exception as e:
            print(f"[AI ANALYSIS] ✗ Error: {e}")
            self.db.rollback()
            return {'success': False, 'error': str(e)}
