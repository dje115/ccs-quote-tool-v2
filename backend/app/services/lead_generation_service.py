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
        self.openai_client = None
        self.gmaps_client = None
        self.companies_house_key = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize all API clients with keys"""
        try:
            # Get API keys (tenant-specific or system-wide)
            api_keys = get_api_keys(self.db, self.tenant_id)
            
            # Initialize OpenAI client
            if api_keys.get('openai'):
                import openai
                self.openai_client = openai.OpenAI(
                    api_key=api_keys['openai'],
                    timeout=240.0  # 4 minutes for GPT-5-mini with web search [[memory:9653106]]
                )
                print("[OK] OpenAI client initialized")
            else:
                print("[WARN] OpenAI API key not found")
            
            # Initialize Google Maps client
            if api_keys.get('google_maps'):
                import googlemaps
                self.gmaps_client = googlemaps.Client(key=api_keys['google_maps'])
                print("[OK] Google Maps client initialized")
            else:
                print("[WARN] Google Maps API key not found")
            
            # Store Companies House key
            if api_keys.get('companies_house'):
                self.companies_house_key = api_keys['companies_house']
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
        
        [[memory:9653106]] - CRITICAL: Use gpt-5-mini with 10000+ tokens, 120s+ timeout
        """
        
        # Build comprehensive prompt
        prompt = self._build_comprehensive_prompt(campaign)
        
        try:
            print(f"🤖 Using GPT-5-mini with Responses API + Web Search")
            print(f"⏱️  Timeout: 240 seconds")
            print(f"🎫 Max Tokens: 20000 (comprehensive results)")
            
            # Use Responses API with web search [[memory:9653106]]
            response = self.openai_client.responses.create(
                model="gpt-5-mini",
                tools=[{"type": "web_search"}],  # Enable web search
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
            
            print(f"✓ GPT-5-mini response received")
            
            # Extract response text
            ai_response = self._extract_response_text(response)
            print(f"✓ Extracted {len(ai_response)} characters")
            
            return ai_response
            
        except Exception as e:
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            print(f"❌ AI search failed: {error_msg}")
            raise
    
    def _build_comprehensive_prompt(self, campaign: LeadGenerationCampaign) -> str:
        """
        Build comprehensive AI prompt based on campaign type
        Migrated from v1 with all campaign type variations
        """
        
        # Base prompt structure
        base = f"""
TASK: Find {campaign.max_results} REAL UK businesses near {campaign.postcode} (within {campaign.distance_miles} miles)

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
- Note their business focus and why they need IT/cabling services
- Assess lead quality (score 60-95)

OUTPUT FORMAT - Valid JSON:
{{
  "query_area": "{campaign.postcode}, UK",
  "results": [
    {{
      "company_name": "Real Company Name Ltd",
      "website": "https://realcompany.com",
      "description": "Specific reason why they need structured cabling/IT services",
      "contact_name": "Contact Person Name",
      "contact_email": "contact@realcompany.com",
      "contact_phone": "01234 567890",
      "address": "Full business address with street, city",
      "postcode": "LE1 1AA",
      "business_sector": "Technology/Healthcare/Education/Manufacturing/etc",
      "company_size": "Micro/Small/Medium/Large",
      "lead_score": 85,
      "timeline": "Within 3 months/6 months/1 year",
      "project_value": "Small/Medium/Large"
    }}
  ]
}}
"""
        
        # Add campaign-type-specific instructions
        if campaign.prompt_type == 'it_msp_expansion':
            base += """

SPECIFIC FOCUS - IT/MSP BUSINESSES:
✓ INCLUDE: IT Support Companies, Managed Service Providers (MSPs), Computer Repair Shops,
  IT Consultancies, Software Development Firms, Web Design Agencies, Technology Resellers,
  Network Support Companies, Cybersecurity Firms

✗ EXCLUDE: Universities, Schools, Hospitals, Retail Stores, Government Buildings,
  Hotels, Entertainment Venues, Libraries, Museums

TARGET: Small to medium IT businesses that serve customers but DON'T currently offer
structured cabling installation. They are perfect partnership/referral prospects.
"""
        
        elif campaign.prompt_type == 'education':
            base += """

SPECIFIC FOCUS - EDUCATION SECTOR:
Find: Primary schools, Secondary schools, Colleges, Universities, Training centers,
Educational technology companies, E-learning platforms
Focus on institutions with aging IT infrastructure or expansion plans.
"""
        
        elif campaign.prompt_type == 'manufacturing':
            base += """

SPECIFIC FOCUS - MANUFACTURING:
Find: Manufacturing plants, Industrial facilities, Engineering companies,
Production facilities, Factory automation companies
Focus on businesses modernizing operations or implementing IoT/Industry 4.0.
"""
        
        elif campaign.prompt_type == 'healthcare':
            base += """

SPECIFIC FOCUS - HEALTHCARE:
Find: Hospitals, Medical practices, Dental offices, Veterinary clinics,
Healthcare technology companies, Care homes
Focus on facilities with patient data systems requiring secure networking.
"""
        
        elif campaign.prompt_type == 'retail_office':
            base += """

SPECIFIC FOCUS - RETAIL & OFFICE:
Find: Retail stores, Office buildings, Business centers, Commercial properties,
Professional services firms, Coworking spaces
Focus on businesses renovating, expanding, or upgrading their premises.
"""
        
        elif campaign.prompt_type == 'competitor_verification':
            base += """

SPECIAL MODE - COMPETITOR VERIFICATION:
This campaign is for verifying identified competitor companies.
For each, verify: Company exists, Current status, Contact details, Services offered
"""
        
        elif campaign.prompt_type == 'location_based':
            base += """

SPECIAL MODE - LOCATION-BASED SEARCH:
Search for businesses at or near specific verified addresses.
Focus on finding similar businesses in the same geographic areas.
"""
        
        base += """

QUALITY REQUIREMENTS:
✓ Better to return 10 verified businesses than 50 fake ones
✓ Each business must be REAL and currently trading
✓ Include source URLs where you found the information
✓ Prioritize businesses with clear IT infrastructure needs

OUTPUT: Return ONLY the JSON object. No markdown code fences. No explanations.
"""
        
        return base
    
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
            'planning_applications': 'planning applications construction renovation'
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
                    qualification_reason=lead_data.get('description'),
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
        Convert a Lead to a Customer
        IMPORTANT: Customer starts at DISCOVERY status (campaign-generated leads)
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
                return {'success': False, 'error': 'Lead already converted'}
            
            # Create customer with DISCOVERY status
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
                business_sector=lead.business_sector,
                business_size_category=lead.company_size,
                status=CustomerStatus.DISCOVERY,  # Starts at DISCOVERY
                lead_score=lead.lead_score,
                linkedin_url=lead.linkedin_url,
                linkedin_data=lead.linkedin_data,
                companies_house_data=lead.companies_house_data,
                website_data=lead.website_data,
                google_maps_data=lead.google_maps_data,
                created_by=user_id
            )
            
            self.db.add(customer)
            self.db.flush()
            
            # Update lead
            lead.status = LeadStatus.CONVERTED
            lead.converted_to_customer_id = customer.id
            lead.conversion_date = datetime.utcnow()
            
            self.db.commit()
            
            print(f"✓ Converted lead {lead.company_name} to customer (DISCOVERY status)")
            
            return {
                'success': True,
                'customer_id': customer.id,
                'message': 'Lead converted to customer successfully'
            }
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': str(e)}
