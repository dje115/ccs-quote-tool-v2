"""
World-Class Lead Generation Service
Combines web search, Google Maps, Companies House, and AI analysis for comprehensive business discovery
"""

import json
import httpx
import googlemaps
import asyncio
import re
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
        Uses single AI call with web search for efficiency (same pattern as dynamic search)
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
            
            # Get sector data (use from campaign or default)
            sector_name = campaign_data.get('sector_name', 'General Business')
            sector_data = self._get_sector_data(sector_name)
            
            print(f"🔍 Executing comprehensive AI analysis with web search for {len(company_names)} companies...")
            
            # Build prompt for analyzing the company list (similar to dynamic search but with provided companies)
            prompt = self._build_company_list_prompt(campaign_data, tenant_context, sector_data, company_names)
            print(f"✅ Prompt built successfully, length: {len(prompt)}")
            
            print(f"🔍 About to call OpenAI API for company list analysis...")
            
            # Check if OpenAI client is properly initialized
            if not hasattr(self.ai_service, 'openai_client') or self.ai_service.openai_client is None:
                raise Exception("OpenAI client not initialized")
            print(f"✅ OpenAI client is initialized")
            
            # Call OpenAI using responses.create() with web search (same pattern as dynamic search)
            try:
                # Build input string (responses.create format)
                system_message = f"You are a UK business research specialist with access to live web search. Analyze the provided list of {len(company_names)} companies and return comprehensive business intelligence for each. Use online sources to verify and enhance company information. Return ONLY valid JSON matching the schema provided."
                input_string = f"{system_message}\n\n{prompt}"
                
                response = self.ai_service.openai_client.responses.create(
                    model="gpt-5-mini",
                    input=input_string,
                    tools=[{"type": "web_search_preview"}],
                    tool_choice="auto"
                )
                print(f"✅ OpenAI API call completed for company list, processing response...")
            except Exception as api_error:
                print(f"❌ OpenAI API call failed: {api_error}")
                print(f"❌ Error type: {type(api_error).__name__}")
                import traceback
                traceback.print_exc()
                raise api_error
            
            # Parse response from responses.create() API (same pattern as dynamic search)
            print(f"✅ AI search completed, processing response...")
            
            # Extract response content using exact format from dynamic search
            result_text = None
            sources = []
            
            # First, get the main summary from output_text (primary method)
            if hasattr(response, 'output_text') and response.output_text:
                result_text = response.output_text.strip()
                print(f"🔍 Using output_text: {len(result_text)} chars")
            elif hasattr(response, 'choices') and len(response.choices) > 0:
                result_text = response.choices[0].message.content.strip()
                print(f"🔍 Using choices[0].message.content (fallback): {len(result_text)} chars")
            
            # Extract structured web results as per dynamic search pattern
            if hasattr(response, 'output') and isinstance(response.output, list):
                print(f"🔍 Processing structured output with {len(response.output)} items")
                for item in response.output:
                    if isinstance(item, dict) and "content" in item:
                        for block in item["content"]:
                            if block.get("type") == "output_text" and not result_text:
                                result_text = block.get("text", "").strip()
                                print(f"🔍 Found text in structured output: {len(result_text)} chars")
                            elif block.get("type") == "tool_use" and block.get("tool") == "web_search_preview":
                                # Extract web search results
                                web_results = block.get("results", [])
                                print(f"🔍 Found {len(web_results)} web search results")
                                for r in web_results:
                                    sources.append({
                                        "title": r.get("title", "Untitled"),
                                        "url": r.get("url", ""),
                                        "snippet": r.get("snippet", "")
                                    })
            
            if not result_text:
                print(f"❌ No response content extracted")
                return []
            
            print(f"✅ AI response extracted, length: {len(result_text)}")
            print(f"🔍 First 500 chars: {result_text[:500]}...")
            
            # Parse JSON response with robust error handling (same as dynamic search)
            search_results = None
            
            try:
                search_results = json.loads(result_text)
                print(f"🔍 Successfully parsed JSON")
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error: {e}")
                print(f"❌ Attempting to fix malformed JSON...")
                
                try:
                    fixed_text = self._fix_malformed_json(result_text)
                    if fixed_text != result_text:
                        search_results = json.loads(fixed_text)
                        print(f"✅ Fixed JSON by truncating at complete object")
                    else:
                        raise json.JSONDecodeError("Could not fix JSON", result_text, e.pos)
                except json.JSONDecodeError:
                    try:
                        search_results = self._extract_json_from_response(result_text)
                        if search_results:
                            print(f"✅ Extracted JSON using fallback method")
                        else:
                            raise json.JSONDecodeError("Could not extract JSON", result_text, e.pos)
                    except Exception as fallback_error:
                        print(f"❌ All JSON recovery methods failed: {fallback_error}")
                        return []
            
            if not search_results:
                print(f"❌ No search results after parsing")
                return []
            
            # Extract businesses - same pattern as dynamic search
            businesses = []
            
            if isinstance(search_results, dict):
                if 'results' in search_results and isinstance(search_results['results'], list):
                    businesses = search_results['results']
                    print(f"✅ Found {len(businesses)} businesses in 'results' key")
                    
                    # Propagate top-level sector to each business record
                    if 'sector' in search_results:
                        for business in businesses:
                            business['business_sector'] = search_results['sector']
                else:
                    print(f"⚠️ No 'results' key or not a list. Available keys: {list(search_results.keys())}")
            elif isinstance(search_results, list):
                businesses = search_results
                print(f"✅ Using response as direct list with {len(businesses)} businesses")
            
            print(f"📊 Final business count: {len(businesses)}")
            if len(businesses) == 0:
                print(f"⚠️ No businesses found after parsing")
                return []
            
            # Enhance each business with additional data and ensure sector is populated (same as dynamic search)
            enhanced_businesses = []
            campaign_sector = campaign_data.get('sector_name', 'Unknown')
            
            for idx, business in enumerate(businesses, 1):
                try:
                    print(f"🔄 Processing business {idx}/{len(businesses)}: {business.get('company_name', 'Unknown')}")
                    
                    # Ensure sector is populated (fallback to campaign sector if missing)
                    if not business.get('business_sector') or business.get('business_sector', '').strip() in ['', 'N/A', 'None', 'null']:
                        business['business_sector'] = campaign_sector
                    
                    enhanced = await self._enhance_business_data(business, tenant_context)
                    # Ensure sector is populated, fallback to campaign sector if needed
                    if not enhanced.get('business_sector') or enhanced.get('business_sector', '').strip() in ['', 'N/A', 'None', 'null']:
                        enhanced['business_sector'] = campaign_sector
                    enhanced_businesses.append(enhanced)
                except Exception as e:
                    print(f"⚠️ Error enhancing business {idx}: {e}")
                    # Ensure sector is set even if enhancement fails
                    if not business.get('business_sector') or business.get('business_sector') == 'Unknown':
                        business['business_sector'] = campaign_sector
                    enhanced_businesses.append(business)  # Keep the original
            
            print(f"\n✅ Company list analysis complete: {len(enhanced_businesses)} companies analyzed")
            return enhanced_businesses
            
        except Exception as e:
            print(f"❌ Error in company list analysis: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    
    async def _generate_leads_from_sector_search(self, campaign_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate leads using dynamic business search by sector
        """
        try:
            print(f"🔍 Executing comprehensive AI search with web search enabled...")
            
            # Get tenant context
            print(f"🔍 Getting tenant context...")
            tenant_context = self._get_tenant_context()
            print(f"✅ Tenant context retrieved: {tenant_context.get('company_name', 'Unknown')}")
            
            # Get sector data
            print(f"🔍 Getting sector data for: {campaign_data.get('sector_name')}")
            sector_data = self._get_sector_data(campaign_data.get('sector_name'))
            print(f"✅ Sector data retrieved: {sector_data.get('sector_name', 'Unknown')}")
            
            # Build comprehensive prompt
            print(f"🔍 Building comprehensive prompt...")
            prompt = self._build_comprehensive_prompt(campaign_data, tenant_context, sector_data)
            print(f"✅ Prompt built successfully, length: {len(prompt)}")
            
            print(f"🔍 About to call OpenAI API...")
            
            # Check if OpenAI client is properly initialized
            if not hasattr(self.ai_service, 'openai_client') or self.ai_service.openai_client is None:
                raise Exception("OpenAI client not initialized")
            print(f"✅ OpenAI client is initialized")
            
            # Call OpenAI using responses.create() with web search (working format from ai_analysis_service)
            print(f"🔍 Calling OpenAI API with responses.create() and web search...")
            try:
                # Build input string (responses.create format from user example)
                max_results = campaign_data.get('max_results', 20)
                system_message = f"You are a UK business research specialist with access to live web search. Use online sources to find REAL, VERIFIED UK businesses. Focus on finding the top {max_results} most relevant results. Return ONLY valid JSON matching the schema provided."
                input_string = f"{system_message}\n\n{prompt}"
                
                response = self.ai_service.openai_client.responses.create(
                    model="gpt-5-mini",
                    input=input_string,
                    tools=[{"type": "web_search_preview"}],
                    tool_choice="auto"
                )
                print(f"✅ OpenAI API call completed, processing response...")
            except Exception as api_error:
                print(f"❌ OpenAI API call failed: {api_error}")
                print(f"❌ Error type: {type(api_error).__name__}")
                import traceback
                traceback.print_exc()
                raise api_error
            
            # Parse response from responses.create() API
            print(f"✅ AI search completed, processing response...")
            print(f"🔍 Response type: {type(response)}")
            print(f"🔍 Response attributes: {dir(response)}")
            
            # Extract response content using exact format from user example
            result_text = None
            sources = []
            
            # First, get the main summary from output_text (primary method from user example)
            if hasattr(response, 'output_text') and response.output_text:
                result_text = response.output_text.strip()
                print(f"🔍 Using output_text (responses.create format): {len(result_text)} chars")
            elif hasattr(response, 'choices') and len(response.choices) > 0:
                result_text = response.choices[0].message.content.strip()
                print(f"🔍 Using choices[0].message.content (fallback): {len(result_text)} chars")
            
            # Extract structured web results as per user example
            if hasattr(response, 'output') and isinstance(response.output, list):
                print(f"🔍 Processing structured output with {len(response.output)} items")
                for item in response.output:
                    if isinstance(item, dict) and "content" in item:
                        for block in item["content"]:
                            if block.get("type") == "output_text" and not result_text:
                                # Use this if we haven't found text yet
                                result_text = block.get("text", "").strip()
                                print(f"🔍 Found text in structured output: {len(result_text)} chars")
                            elif block.get("type") == "tool_use" and block.get("tool") == "web_search_preview":
                                # Extract web search results as per user example, limiting to max_results
                                web_results = block.get("results", [])
                                max_results = campaign_data.get('max_results', 20)  # Default to 20 if not set
                                print(f"🔍 Found {len(web_results)} web search results, limiting to {max_results}")
                                for r in web_results[:max_results]:  # Limit results like in user example
                                    sources.append({
                                        "title": r.get("title", "Untitled"),
                                        "url": r.get("url", ""),
                                        "snippet": r.get("snippet", "")
                                    })
                
                # If we still don't have text, try fallback
                if not result_text:
                    result_text = '\n'.join(str(item) for item in response.output).strip()
                    print(f"🔍 Using output list join (fallback): {len(result_text)} chars")
            elif hasattr(response, 'output'):
                result_text = str(response.output).strip()
                print(f"🔍 Using output string: {len(result_text)} chars")
            
            if not result_text:
                result_text = str(response).strip()
                print(f"🔍 Using str(response) fallback: {len(result_text)} chars")
            
            if not result_text:
                print(f"❌ No response content extracted")
                return []
            
            print(f"✅ AI response extracted, length: {len(result_text)}")
            print(f"🔍 Web sources found: {len(sources)}")
            if sources:
                for i, source in enumerate(sources[:3]):  # Show first 3 sources
                    print(f"🔍 Source {i+1}: {source.get('title', 'No title')}")
            print(f"🔍 First 500 chars: {result_text[:500]}...")
            
            # Parse JSON response with robust error handling
            search_results = None
            
            try:
                search_results = json.loads(result_text)
                print(f"🔍 Successfully parsed JSON")
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error: {e}")
                print(f"❌ Attempting to fix malformed JSON...")
                
                # Try to fix common JSON issues
                try:
                    # Method 1: Try to find the end of the last complete JSON object
                    fixed_text = self._fix_malformed_json(result_text)
                    if fixed_text != result_text:
                        search_results = json.loads(fixed_text)
                        print(f"✅ Fixed JSON by truncating at complete object")
                    else:
                        raise json.JSONDecodeError("Could not fix JSON", result_text, e.pos)
                except json.JSONDecodeError:
                    # Method 2: Try to extract JSON from around the results array
                    try:
                        search_results = self._extract_json_from_response(result_text)
                        if search_results:
                            print(f"✅ Extracted JSON using fallback method")
                        else:
                            raise json.JSONDecodeError("Could not extract JSON", result_text, e.pos)
                    except Exception as fallback_error:
                        print(f"❌ All JSON recovery methods failed: {fallback_error}")
                        print(f"❌ Raw response was: {result_text[:1000]}...")
                        return []
            
            if not search_results:
                print(f"❌ No search results after parsing")
                return []
                
            print(f"🔍 JSON type: {type(search_results)}")
            
            if isinstance(search_results, dict):
                print(f"🔍 JSON keys: {list(search_results.keys())}")
            elif isinstance(search_results, list):
                print(f"🔍 JSON is list with {len(search_results)} items")
            
            # Extract businesses - the API response has 'results' key containing the array
            businesses = []
            
            if isinstance(search_results, dict):
                # The working response format has a 'results' key with the business array
                if 'results' in search_results and isinstance(search_results['results'], list):
                    businesses = search_results['results']
                    print(f"✅ Found {len(businesses)} businesses in 'results' key")
                    
                    # Propagate top-level sector to each business record
                    if 'sector' in search_results:
                        for business in businesses:
                            business['business_sector'] = search_results['sector']
                else:
                    print(f"⚠️ No 'results' key or not a list. Available keys: {list(search_results.keys())}")
            elif isinstance(search_results, list):
                businesses = search_results
                print(f"✅ Using response as direct list with {len(businesses)} businesses")
            
            print(f"📊 Final business count: {len(businesses)}")
            if len(businesses) == 0:
                print(f"⚠️ No businesses found after parsing")
                print(f"⚠️ search_results type: {type(search_results)}")
                if isinstance(search_results, dict):
                    print(f"⚠️ search_results keys: {list(search_results.keys())}")
                print(f"⚠️ Full search_results: {search_results}")
                return []
            
            # Enhance each business with additional data and ensure sector is populated
            enhanced_businesses = []
            campaign_sector = campaign_data.get('sector_name', 'Unknown')
            
            for idx, business in enumerate(businesses, 1):
                try:
                    print(f"🔄 Processing business {idx}/{len(businesses)}: {business.get('company_name', 'Unknown')}")
                    
                    # Ensure sector is populated (fallback to campaign sector if missing)
                    if not business.get('business_sector') or business.get('business_sector', '').strip() in ['', 'N/A', 'None', 'null']:
                        business['business_sector'] = campaign_sector
                    
                    enhanced = await self._enhance_business_data(business, tenant_context)
                    # Ensure sector is populated, fallback to campaign sector if needed
                    if not enhanced.get('business_sector') or enhanced.get('business_sector', '').strip() in ['', 'N/A', 'None', 'null']:
                        enhanced['business_sector'] = campaign_sector
                    enhanced_businesses.append(enhanced)
                except Exception as e:
                    print(f"⚠️ Error enhancing business {idx}: {e}")
                    # Ensure sector is set even if enhancement fails
                    if not business.get('sector') or business.get('sector') == 'Unknown':
                        business['sector'] = campaign_sector
                    enhanced_businesses.append(business)  # Keep the original
            
            return enhanced_businesses
        
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
        
        print(f"🔍 Building prompt - determining installer status...")
        # Determine if tenant is installation provider
        is_installer = tenant_context.get('is_installation_provider', False)
        
        print(f"🔍 Building prompt - generating customer/partner types...")
        # Generate dynamic customer/partner recommendations
        customer_type = self._generate_customer_type(tenant_context, sector_data)
        partner_type = self._generate_partner_type(tenant_context, sector_data)
        print(f"✅ Customer/partner types generated")
        
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
    
    def _build_company_list_prompt(self, campaign_data: Dict, tenant_context: Dict, sector_data: Dict, company_names: List[str]) -> str:
        """Build the AI prompt for analyzing a provided list of companies"""
        
        print(f"🔍 Building company list prompt - determining installer status...")
        # Determine if tenant is installation provider
        is_installer = tenant_context.get('is_installation_provider', False)
        
        print(f"🔍 Building prompt - generating customer/partner types...")
        # Generate dynamic customer/partner recommendations
        customer_type = self._generate_customer_type(tenant_context, sector_data)
        partner_type = self._generate_partner_type(tenant_context, sector_data)
        print(f"✅ Customer/partner types generated")
        
        # Create company names list for the prompt
        company_names_list = "\n".join([f"- {name}" for name in company_names])
        
        prompt = f"""You are a UK business research specialist with access to live web search. 
Analyze the provided list of {len(company_names)} companies and return comprehensive business intelligence for each.
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
Campaign Type: Company List Import

---

## COMPANIES TO ANALYZE:
{company_names_list}

---

## OBJECTIVE
Analyze each of the {len(company_names)} companies listed above and provide comprehensive business intelligence for each.
Use web search to verify company information, find contact details, and gather current business intelligence.

IMPORTANT: You MUST analyze ALL companies in the list. Do not skip any companies.

---

## ANALYSIS APPROACH
1. Use web search to verify each company exists and gather current information
2. Find contact details (phone, email, website) for each company
3. Determine business sector, size, and activities for each company
4. Assess each company's fit as a potential customer or partner
5. Generate actionable business intelligence for sales teams

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
  "query_type": "company_list_analysis",
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
- Analyze ALL companies in the provided list
- Use web search to verify each company exists and gather current information
- Focus on finding real, verifiable contact information
- Provide comprehensive business intelligence for each company
- Never include fictional examples or template data
- If a company cannot be found or verified, mark it clearly in the analysis
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
    
    def _fix_malformed_json(self, json_text: str) -> str:
        """
        Attempt to fix malformed JSON by finding the end of the last complete object/array
        """
        try:
            # Look for common JSON termination issues and try to fix them
            original_text = json_text
            
            # Method 1: Find the last complete } or ] before the error
            if '"results"' in json_text:
                # Try to find the closing of the results array
                results_start = json_text.find('"results": [')
                if results_start != -1:
                    results_start = json_text.find('[', results_start)
                    bracket_count = 0
                    pos = results_start
                    
                    while pos < len(json_text):
                        if json_text[pos] == '[':
                            bracket_count += 1
                        elif json_text[pos] == ']':
                            bracket_count -= 1
                            if bracket_count == 0:
                                # Found end of results array, truncate there
                                end_pos = pos + 1
                                # Find the end of the main object
                                while end_pos < len(json_text) and json_text[end_pos] not in ['\n', '\r']:
                                    if json_text[end_pos] == '}':
                                        return json_text[:end_pos + 1] + '}'
                                    end_pos += 1
                                return json_text[:pos + 1] + '}'
                        pos += 1
            
            # Method 2: Find the last complete object by counting braces
            brace_count = 0
            last_valid_pos = -1
            in_string = False
            escape_next = False
            
            for i, char in enumerate(json_text):
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\' and in_string:
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            last_valid_pos = i
            
            if last_valid_pos > 0:
                return json_text[:last_valid_pos + 1]
                
            return original_text
            
        except Exception as e:
            print(f"⚠️ Error in _fix_malformed_json: {e}")
            return json_text
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Any]:
        """
        Fallback method to extract JSON from malformed responses
        """
        try:
            # Look for the JSON structure and try to extract it
            import re
            
            # Try to find JSON object boundaries
            json_match = re.search(r'\{.*"results".*\[.*\].*\}', response_text, re.DOTALL)
            if json_match:
                extracted = json_match.group(0)
                try:
                    return json.loads(extracted)
                except:
                    pass
            
            # Try to find just the results array
            results_match = re.search(r'"results"\s*:\s*\[(.*?)\]', response_text, re.DOTALL)
            if results_match:
                results_content = results_match.group(1)
                # Try to parse each object in the array
                # This is a simplified approach - would need more robust parsing for real use
                pass
                
            return None
            
        except Exception as e:
            print(f"⚠️ Error in _extract_json_from_response: {e}")
            return None