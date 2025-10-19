"""
World-Class Lead Generation Service
Combines web search, Google Maps, Companies House, and AI analysis for comprehensive business discovery
"""

import json
import httpx
import googlemaps
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models import Tenant, Sector, Lead
from app.services.ai_analysis_service import AIAnalysisService
from app.services.companies_house_service import CompaniesHouseService
from app.core.config import settings


class LeadGenerationService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
        self.ai_service = AIAnalysisService(tenant_id=str(tenant_id), db=db)
        self.companies_house_service = CompaniesHouseService(api_key=self._get_api_keys()['companies_house_api_key'])
        
        # Initialize Google Maps client
        api_keys = self._get_api_keys()
        self.gmaps = googlemaps.Client(key=api_keys['google_maps_api_key'])
    
    def _get_api_keys(self) -> Dict[str, str]:
        """Get API keys from tenant or system-wide fallback"""
        try:
            # Try tenant-specific keys first
            tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
            if tenant and tenant.openai_api_key and tenant.google_maps_api_key and tenant.companies_house_api_key:
                return {
                    'openai_api_key': tenant.openai_api_key,
                    'google_maps_api_key': tenant.google_maps_api_key,
                    'companies_house_api_key': tenant.companies_house_api_key
                }
        except Exception as e:
            print(f"⚠️ Error getting tenant API keys: {e}")
        
        # Fallback to system-wide keys
        try:
            print("🔍 Looking for system tenant...")
            system_tenant = self.db.query(Tenant).filter(Tenant.name == "System").first()
            print(f"🔍 System tenant found: {system_tenant is not None}")
            if system_tenant:
                print(f"🔑 OpenAI key exists: {bool(system_tenant.openai_api_key)} (length: {len(system_tenant.openai_api_key) if system_tenant.openai_api_key else 0})")
                print(f"🔑 Google Maps key exists: {bool(system_tenant.google_maps_api_key)} (length: {len(system_tenant.google_maps_api_key) if system_tenant.google_maps_api_key else 0})")
                print(f"🔑 Companies House key exists: {bool(system_tenant.companies_house_api_key)} (length: {len(system_tenant.companies_house_api_key) if system_tenant.companies_house_api_key else 0})")
                
                if system_tenant.openai_api_key and system_tenant.google_maps_api_key and system_tenant.companies_house_api_key:
                    print("✅ All system API keys found, returning them")
                    return {
                        'openai_api_key': system_tenant.openai_api_key,
                        'google_maps_api_key': system_tenant.google_maps_api_key,
                        'companies_house_api_key': system_tenant.companies_house_api_key
                    }
                else:
                    print("❌ Some system API keys are missing or empty")
                    print(f"❌ OpenAI: '{system_tenant.openai_api_key}'")
                    print(f"❌ Google Maps: '{system_tenant.google_maps_api_key}'")
                    print(f"❌ Companies House: '{system_tenant.companies_house_api_key}'")
            else:
                print("❌ System tenant not found")
        except Exception as e:
            print(f"⚠️ Error getting system API keys: {e}")
            import traceback
            traceback.print_exc()
        
        raise Exception("No API keys found for tenant or system")
    
    async def generate_leads(self, campaign_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Main lead generation method using comprehensive AI analysis with web search
        Supports both dynamic business search and company list import campaigns
        """
        try:
            print(f"🚀 Starting lead generation for campaign: {campaign_data.get('name', 'Unknown')}")
            
            # Route to appropriate handler based on campaign type
            prompt_type = campaign_data.get('prompt_type', 'sector_search')
            
            if prompt_type == 'company_list':
                print(f"📋 Routing to Company List Import handler...")
                return await self._generate_leads_from_company_list(campaign_data)
            else:
                print(f"🔍 Routing to Dynamic Business Search handler...")
                return await self._generate_leads_from_sector_search(campaign_data)
        
        except Exception as e:
            print(f"❌ Error in generate_leads: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def _generate_leads_from_company_list(self, campaign_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze pre-supplied companies from a company list import
        Uses AI to gather intelligence on each company
        """
        try:
            print(f"📋 Starting Company List Import analysis...")
            print(f"🏢 Companies to analyze: {campaign_data.get('company_names', [])}")
            
            # Get tenant context
            tenant_context = self._get_tenant_context()
            
            # Get companies from campaign data
            company_names = campaign_data.get('company_names', [])
            if not company_names or len(company_names) == 0:
                print(f"⚠️  No companies provided in campaign")
                return []
            
            businesses = []
            total_companies = len(company_names)
            
            # Analyze each company
            for idx, company_name in enumerate(company_names, 1):
                print(f"\n📊 Analyzing company {idx}/{total_companies}: {company_name}")
                
                try:
                    # Build prompt for this specific company
                    prompt = self._build_company_analysis_prompt(campaign_data, company_name, tenant_context)
                    
                    # Call OpenAI to analyze the company
                    response = self.ai_service.openai_client.chat.completions.create(
                        model="gpt-5-mini",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a UK business research specialist. Provide comprehensive business intelligence for UK companies. Return ONLY valid JSON matching the schema provided."
                            },
                            {"role": "user", "content": prompt}
                        ],
                        max_completion_tokens=20000,
                        timeout=180.0
                    )
                    
                    # Parse response
                    result_text = response.choices[0].message.content.strip()
                    print(f"✅ AI analysis received for {company_name}")
                    
                    # Parse JSON
                    try:
                        company_data = json.loads(result_text)
                        
                        # Ensure required fields
                        if not company_data.get('company_name'):
                            company_data['company_name'] = company_name
                        
                        # Add AI intelligence
                        company_data = await self._enhance_business_data(company_data, tenant_context)
                        
                        businesses.append(company_data)
                        print(f"✅ Successfully analyzed: {company_name}")
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON parsing error for {company_name}: {e}")
                        # Create minimal record
                        businesses.append({
                            'company_name': company_name,
                            'website': None,
                            'description': 'Company added from import list',
                            'contact_phone': None,
                            'contact_email': None,
                            'postcode': None,
                            'sector': 'Unknown',
                            'lead_score': 50,
                            'fit_reason': 'Imported from company list',
                            'source_url': None,
                            'quick_telesales_summary': f'Company from import list: {company_name}',
                            'ai_business_intelligence': 'Awaiting detailed analysis'
                        })
                    
                except Exception as e:
                    print(f"❌ Error analyzing {company_name}: {e}")
                    # Add basic record so campaign doesn't fail
                    businesses.append({
                        'company_name': company_name,
                        'description': 'Company added from import list',
                        'lead_score': 40,
                        'fit_reason': 'Imported from company list'
                    })
            
            print(f"\n✅ Company list analysis complete: {len(businesses)} companies analyzed")
            return businesses
            
        except Exception as e:
            print(f"❌ Error in company list analysis: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _build_company_analysis_prompt(self, campaign_data: Dict, company_name: str, tenant_context: Dict) -> str:
        """
        Build AI prompt for analyzing a single company from the import list
        """
        prompt = f"""Analyze this UK company and provide comprehensive business intelligence:

**COMPANY TO ANALYZE:** {company_name}

**YOUR COMPANY:** {tenant_context['company_name']}
- Services: {', '.join(tenant_context['services'][:5])}
- Target Markets: {tenant_context['target_markets']}
- USPs: {tenant_context['unique_selling_points']}

Please research this company and provide:

1. **Company Name**: Official name
2. **Business Sector**: Industry classification
3. **Estimated Employees**: Size estimate
4. **Estimated Revenue**: Revenue range estimate
5. **Website**: URL if you can find it
6. **Contact Information**: Phone/email if available
7. **Postcode**: Primary location postcode
8. **Lead Score**: 0-100 score for sales fit with our company
9. **Fit Reason**: Why they could be a good fit for our services
10. **Quick Sales Summary**: 2-3 sentences for telesales
11. **Business Intelligence**: 200+ word comprehensive analysis
12. **Contact Phone**: Direct contact number if available
13. **Contact Email**: Email address if available
14. **Opportunities**: How our services could help them

Return ONLY valid JSON in this exact format:
{{
  "company_name": "string",
  "website": "string or null",
  "description": "string",
  "contact_phone": "string or null",
  "contact_email": "string or null", 
  "postcode": "string or null",
  "sector": "string",
  "lead_score": 0-100,
  "fit_reason": "string",
  "source_url": "string or null",
  "quick_telesales_summary": "string",
  "ai_business_intelligence": "string"
}}"""
        return prompt
    
    async def _generate_leads_from_sector_search(self, campaign_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate leads using dynamic business search by sector
        """
        try:
            print(f"🔍 Executing comprehensive AI search with web search enabled...")
            
            # Get tenant context
            tenant_context = self._get_tenant_context()
            
            # Get sector data
            sector_data = self._get_sector_data(campaign_data.get('sector_name'))
            
            # Build comprehensive prompt
            prompt = self._build_comprehensive_prompt(campaign_data, tenant_context, sector_data)
            
            # Call OpenAI with web search
            response = self.ai_service.openai_client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a UK business research specialist with access to live web search. Use online sources to find REAL, VERIFIED UK businesses. Return ONLY valid JSON matching the schema provided."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=20000,
                timeout=180.0
            )
            
            # Parse response
            if hasattr(response, 'output'):
                result_text = response.output.strip()
            elif hasattr(response, 'choices') and len(response.choices) > 0:
                result_text = response.choices[0].message.content.strip()
            else:
                result_text = str(response).strip()
            
            print(f"✅ AI search completed, parsing results...")
            print(f"🔍 Raw AI response: {result_text[:500]}...")  # Show first 500 chars
            
            # Parse JSON response
            try:
                search_results = json.loads(result_text)
                print(f"🔍 Parsed JSON structure: {list(search_results.keys()) if isinstance(search_results, dict) else 'Not a dict'}")
                
                # Try different possible keys for the business list
                businesses = []
                
                if isinstance(search_results, dict):
                    # Check for 'results' key
                    if 'results' in search_results and isinstance(search_results['results'], list):
                        businesses = search_results['results']
                    # Check if the dict itself contains business-like keys
                    elif any(key in search_results for key in ['company_name', 'businesses', 'companies']):
                        businesses = [search_results]
                elif isinstance(search_results, list):
                    businesses = search_results
                
                print(f"📊 Found {len(businesses)} businesses from AI search")
                
                # Enhance each business with additional data
                enhanced_businesses = []
                for idx, business in enumerate(businesses, 1):
                    try:
                        print(f"🔄 Processing business {idx}/{len(businesses)}: {business.get('company_name', 'Unknown')}")
                        enhanced = await self._enhance_business_data(business, tenant_context)
                        enhanced_businesses.append(enhanced)
                    except Exception as e:
                        print(f"⚠️ Error enhancing business {idx}: {e}")
                        enhanced_businesses.append(business)  # Keep the original
                
                return enhanced_businesses
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error: {e}")
                print(f"❌ Raw response was: {result_text[:1000]}")
                return []
        
        except Exception as e:
            print(f"❌ Error in sector search: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _get_tenant_context(self) -> Dict[str, Any]:
        """Get comprehensive tenant context for AI prompts"""
        tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
        if not tenant:
            raise Exception("Tenant not found")
        
        return {
            'company_name': tenant.company_name or tenant.name,
            'company_description': tenant.company_description or '',
            'services': tenant.products_services or [],
            'target_markets': tenant.target_markets or [],
            'unique_selling_points': tenant.unique_selling_points or [],
            'is_installation_provider': tenant.company_description and 'installation' in tenant.company_description.lower(),
            'location': 'UK',  # Default to UK
            'primary_market': ', '.join(tenant.target_markets[:3]) if tenant.target_markets else 'General Business'
        }
    
    def _get_sector_data(self, sector_name: str) -> Dict[str, Any]:
        """Get sector data from database"""
        sector = self.db.query(Sector).filter(Sector.sector_name == sector_name).first()
        if not sector:
            # Fallback to default sector data
            return {
                'sector_name': sector_name or 'General Business',
                'sector_description': f'Businesses in the {sector_name or "general business"} sector',
                'sector_keywords': f'{sector_name or "business"} companies near',
                'example_companies': 'Various local businesses'
            }
        
        return {
            'sector_name': sector.sector_name,
            'sector_description': sector.prompt_ready_replacement_line,
            'sector_keywords': sector.example_keywords,
            'example_companies': sector.example_companies or 'Various local businesses'
        }
    
    def _build_comprehensive_prompt(self, campaign_data: Dict, tenant_context: Dict, sector_data: Dict) -> str:
        """Build the comprehensive AI prompt for business discovery"""
        
        # Determine if tenant is installation provider
        is_installer = tenant_context.get('is_installation_provider', False)
        
        # Generate dynamic customer/partner recommendations
        customer_type = self._generate_customer_type(tenant_context, sector_data)
        partner_type = self._generate_partner_type(tenant_context, sector_data)
        
        prompt = f"""You are a UK business research specialist. 
Find REAL, VERIFIED UK businesses based on your training data and knowledge. 
Return ONLY valid JSON matching the schema provided — do not include explanations or text outside the JSON.

---

## CONTEXT:
Company: {tenant_context['company_name']}
Description: {tenant_context['company_description']}
Services: {', '.join(tenant_context['services'][:5])}
Location: {tenant_context['location']}
Primary Market: {tenant_context['primary_market']}
Installation Provider: {is_installer}

Sector: {sector_data['sector_name']}
Sector Focus: {sector_data['sector_description']}
Search Area: {campaign_data.get('postcode', 'UK')} (within {campaign_data.get('distance_miles', 50)} miles)
Campaign Type: {campaign_data.get('prompt_type', 'sector_search')}
Maximum Results: {campaign_data.get('max_results', 20)}
{f"Target Company Size: {campaign_data.get('company_size_category', 'Any Size')}" if campaign_data.get('company_size_category') else "Target Company Size: Any Size"}

---

## OBJECTIVE
Generate a list of {campaign_data.get('max_results', 20)} REAL UK businesses in the {sector_data['sector_name']} sector.
Focus on well-known UK retail chains, independent stores, and e-commerce businesses.

IMPORTANT: You MUST provide actual UK businesses. Do not return an empty results array.
If you cannot find businesses in the specific area, provide UK businesses from your training data that match the sector.

---

## SEARCH APPROACH
1. Use your knowledge of UK businesses to find companies in the {sector_data['sector_name']} sector
2. Focus on businesses that would be located near {campaign_data.get('postcode', 'UK')} or in the surrounding area
3. Ensure each company is a real UK business with valid contact information
4. Use the keywords below to understand the sector focus
{f"5. Filter by company size: Prioritize {campaign_data.get('company_size_category')} companies ({self._get_company_size_description(campaign_data.get('company_size_category'))})" if campaign_data.get('company_size_category') else ""}

## KEYWORDS TO CONSIDER:
{sector_data.get('example_keywords', 'Industry-specific keywords')}

---

## DATA TO RETURN
For each business, extract:
- `company_name` (official name)
- `website` (URL, or null if not verifiable)
- `description` (short summary of services)
- `contact_phone` (or null)
- `contact_email` (or null)
- `postcode`
- `sector` (from context)
- `lead_score` (60–95, based on relevance)
- `fit_reason` (why this business fits as a customer or partner)
- `source_url` (where you found it)
- `quick_telesales_summary` (2-3 sentences for telesales team)
- `ai_business_intelligence` (comprehensive analysis, 300+ words)

---

## DYNAMIC INSIGHTS TO INCLUDE
Generate these automatically based on the sector and company data:

**Recommended Customer Type:**  
{customer_type}

**Recommended Partner Type:**  
{partner_type}

---

## OUTPUT FORMAT
Return only valid JSON in this structure:
{{
  "query_area": "{campaign_data.get('postcode', 'UK')} + {campaign_data.get('distance_miles', 50)} miles",
  "sector": "{sector_data['sector_name']}",
  "results": [
    {{
      "company_name": "string",
      "website": "string or null",
      "description": "string",
      "contact_phone": "string or null",
      "contact_email": "string or null",
      "postcode": "string",
      "lead_score": 60–95,
      "fit_reason": "string",
      "source_url": "string",
      "recommended_customer_type": "{customer_type}",
      "recommended_partner_type": "{partner_type}",
      "quick_telesales_summary": "string",
      "ai_business_intelligence": "string"
    }}
  ]
}}

---

## QUALITY RULES
- Prioritise *real, verifiable SMEs* over quantity.
- Skip duplicates and large national chains.
- Businesses must be **within {campaign_data.get('distance_miles', 50)} miles of {campaign_data.get('postcode', 'UK')}**.
- If fewer than {campaign_data.get('max_results', 20)} genuine businesses are found, return only verified ones.
{f"- Filter by company size: Prioritize {campaign_data.get('company_size_category')} companies ({self._get_company_size_description(campaign_data.get('company_size_category'))})" if campaign_data.get('company_size_category') else "- Prioritize SMEs and small-to-medium enterprises over large corporations."}
- Never include fictional examples or template data.
"""
        
        return prompt
    
    def _generate_customer_type(self, tenant_context: Dict, sector_data: Dict) -> str:
        """Generate dynamic customer type based on tenant profile"""
        company_name = tenant_context['company_name']
        services = tenant_context.get('services', [])
        
        if tenant_context.get('is_installation_provider', False):
            return f"Businesses that need professional installation services from {company_name} for their {sector_data['sector_name']} operations, including site surveys, certified installations, and ongoing maintenance support."
        else:
            return f"Businesses in the {sector_data['sector_name']} sector that would benefit from {company_name}'s {', '.join(services[:3])} services to enhance their operations and efficiency."
    
    def _generate_partner_type(self, tenant_context: Dict, sector_data: Dict) -> str:
        """Generate dynamic partner type based on tenant profile"""
        company_name = tenant_context['company_name']
        services = tenant_context.get('services', [])
        
        if tenant_context.get('is_installation_provider', False):
            return f"Technology providers, MSPs, and {sector_data['sector_name']} specialists who need reliable installation partners for client projects, offering white-label services and joint project delivery capabilities."
        else:
            return f"Complementary service providers in the {sector_data['sector_name']} sector who could resell {company_name}'s {', '.join(services[:3])} solutions or collaborate on integrated service offerings."
    
    def _get_company_size_description(self, size_category: str) -> str:
        """Get employee count description for company size category"""
        size_descriptions = {
            'Micro': '0-9 employees',
            'Small': '10-49 employees',
            'Medium': '50-249 employees',
            'Large': '250+ employees'
        }
        return size_descriptions.get(size_category, 'Any size')
    
    async def _enhance_business_data(self, business: Dict, tenant_context: Dict) -> Dict:
        """Enhance business data with Google Maps and Companies House verification"""
        try:
            company_name = business.get('company_name', '')
            postcode = business.get('postcode', '')
            
            # Google Maps verification
            if postcode and company_name:
                try:
                    gmaps_data = await self._get_google_maps_data(company_name, postcode)
                    business.update(gmaps_data)
                except Exception as e:
                    print(f"⚠️ Google Maps verification failed for {company_name}: {e}")
            
            # Companies House verification
            if company_name:
                try:
                    ch_data = await self._get_companies_house_data(company_name)
                    business.update(ch_data)
                except Exception as e:
                    print(f"⚠️ Companies House verification failed for {company_name}: {e}")
            
            return business
            
        except Exception as e:
            print(f"⚠️ Error enhancing business data: {e}")
            return business
    
    async def _get_google_maps_data(self, company_name: str, postcode: str) -> Dict:
        """Get Google Maps data for business verification"""
        try:
            # Search for the business
            search_result = self.gmaps.places_nearby(
                location=self.gmaps.geocode(f"{postcode}, UK")[0]['geometry']['location'],
                radius=5000,
                keyword=company_name,
                type='establishment'
            )
            
            if search_result.get('results'):
                place = search_result['results'][0]
                place_id = place['place_id']
                
                # Get detailed information
                place_details = self.gmaps.place(
                    place_id=place_id,
                    fields=['name', 'formatted_address', 'formatted_phone_number', 'website', 'rating', 'type']
                )
                
                details = place_details['result']
                
                return {
                    'verified_address': details.get('formatted_address', ''),
                    'verified_phone': details.get('formatted_phone_number', ''),
                    'verified_website': details.get('website', ''),
                    'google_rating': details.get('rating', 0),
                    'google_types': details.get('types', [])
                }
            
            return {}
            
        except Exception as e:
            print(f"⚠️ Google Maps API error: {e}")
            return {}
    
    async def _get_companies_house_data(self, company_name: str) -> Dict:
        """Get Companies House data for business verification"""
        try:
            # Use Companies House service to get company data
            ch_data = await self.companies_house_service.search_company(company_name)
            
            if ch_data:
                return {
                    'companies_house_number': ch_data.get('company_number', ''),
                    'companies_house_status': ch_data.get('company_status', ''),
                    'companies_house_type': ch_data.get('company_type', ''),
                    'companies_house_incorporated': ch_data.get('date_of_creation', ''),
                    'companies_house_address': ch_data.get('registered_office_address', {}).get('address_line_1', ''),
                    'companies_house_postcode': ch_data.get('registered_office_address', {}).get('postal_code', '')
                }
            
            return {}
            
        except Exception as e:
            print(f"⚠️ Companies House API error: {e}")
            return {}