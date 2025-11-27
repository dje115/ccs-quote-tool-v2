#!/usr/bin/env python3
"""
AI Analysis Service for Company Analysis and Lead Generation
"""

import json
import re
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import httpx

from app.core.config import settings
from app.services.companies_house_service import CompaniesHouseService
from app.services.google_maps_service import GoogleMapsService
from app.services.web_scraping_service import WebScrapingService
from app.services.ai_provider_service import AIProviderService
from app.services.ai_prompt_service import AIPromptService
from app.models.ai_prompt import PromptCategory


class AIAnalysisService:
    """Service for AI-powered company analysis and lead generation"""
    
    def __init__(self, openai_api_key: Optional[str] = None, 
                 companies_house_api_key: Optional[str] = None,
                 google_maps_api_key: Optional[str] = None,
                 tenant_id: Optional[str] = None,
                 db=None):
        # Set tenant_id and db FIRST (needed for API key resolution)
        self.tenant_id = tenant_id
        self.db = db
        
        # Use provided API keys or resolve from database with fallback
        if openai_api_key and companies_house_api_key and google_maps_api_key:
            # API keys provided directly (e.g., from endpoints that already resolved them)
            self.openai_api_key = openai_api_key  # Kept for backward compatibility
            self.companies_house_api_key = companies_house_api_key
            self.google_maps_api_key = google_maps_api_key
        else:
            # Resolve API keys from database with tenant → system fallback
            self._resolve_api_keys_from_db()
        
        # Initialize AI provider service
        self.provider_service = AIProviderService(db, tenant_id=tenant_id) if db else None
        
        self.companies_house_service = CompaniesHouseService(api_key=self.companies_house_api_key)
        self.google_maps_service = GoogleMapsService(api_key=self.google_maps_api_key)
        self.web_scraping_service = WebScrapingService()
    
    def _resolve_api_keys_from_db(self):
        """Resolve API keys from database with tenant → system fallback"""
        try:
            from app.core.api_keys import get_api_keys
            from app.models.tenant import Tenant
            
            if not self.db or not self.tenant_id:
                # Fallback to environment variables if no database context
                self.openai_api_key = settings.OPENAI_API_KEY
                self.companies_house_api_key = settings.COMPANIES_HOUSE_API_KEY
                self.google_maps_api_key = settings.GOOGLE_MAPS_API_KEY
                return
            
            # Get tenant
            tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
            if not tenant:
                # Fallback to environment variables if tenant not found
                self.openai_api_key = settings.OPENAI_API_KEY
                self.companies_house_api_key = settings.COMPANIES_HOUSE_API_KEY
                self.google_maps_api_key = settings.GOOGLE_MAPS_API_KEY
                return
            
            # Use the centralized API key resolution with fallback
            api_keys = get_api_keys(self.db, tenant)
            
            self.openai_api_key = api_keys.openai
            self.companies_house_api_key = api_keys.companies_house
            self.google_maps_api_key = api_keys.google_maps
            
            print(f"[AI ANALYSIS] API keys resolved from: {api_keys.source}")
            
        except Exception as e:
            print(f"[AI ANALYSIS] Error resolving API keys from database: {e}")
            # Fallback to environment variables
            self.openai_api_key = settings.OPENAI_API_KEY
            self.companies_house_api_key = settings.COMPANIES_HOUSE_API_KEY
            self.google_maps_api_key = settings.GOOGLE_MAPS_API_KEY
    
    
    def _build_dynamic_system_prompt(self, analysis_type: str = "general") -> str:
        """
        Build dynamic system prompt based on tenant's business
        
        Args:
            analysis_type: Type of analysis ('general', 'sales', 'lead_scoring')
        """
        prompt = "You are a business intelligence analyst specializing in UK companies"
        
        # Try to get tenant information if available
        if self.db and self.tenant_id:
            try:
                from app.models.tenant import Tenant
                tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
                
                if tenant:
                    if tenant.company_name:
                        prompt += f" and helping {tenant.company_name} identify sales opportunities"
                    
                    if tenant.target_markets and isinstance(tenant.target_markets, list) and len(tenant.target_markets) > 0:
                        markets = ", ".join(tenant.target_markets[:3])
                        prompt += f" in their target markets: {markets}"
                    
                    # Emphasize matching their specific offerings
                    prompt += ". You must carefully review the client's products, services, and capabilities, then identify specific ways they can help prospects based ONLY on what they actually offer"
            except Exception as e:
                print(f"[DEBUG] Could not load tenant info: {e}")
        
        # Add context based on analysis type
        if analysis_type == "sales":
            prompt += ". Focus on creating actionable, specific sales strategies"
        elif analysis_type == "lead_scoring":
            prompt += ". Focus on scoring sales leads accurately"
        else:
            prompt += ". Focus on practical business opportunities"
        
        prompt += ". Always respond with valid JSON. When listing companies, people, or specific entities, ONLY include real, verified information. Do NOT make up or hallucinate company names, people names, or details. If you cannot verify something is real, do NOT include it."
        
        return prompt
    
    async def _discover_website(self, company_name: str) -> str:
        """Use AI with web search to discover company website (same as campaign method)"""
        try:
            if not self.provider_service:
                return None
            
            print(f"[WEBSITE DISCOVERY] Using AI provider with web search for: {company_name}")
            
            if not self.provider_service:
                return None
            
            # Use AIProviderService with web search support
            system_message = "You are a helpful assistant that finds company websites. Respond only with the URL or NOT_FOUND."
            user_message = f"Find the official website URL for the company: {company_name}\n\nPlease respond with ONLY the website URL (e.g., https://example.com) or \"NOT_FOUND\" if you cannot find it.\nDo not include any explanation, just the URL or NOT_FOUND."
            
            provider_response = await self.provider_service.generate_with_rendered_prompts(
                prompt=None,
                system_prompt=system_message,
                user_prompt=user_message,
                use_responses_api=True,
                tools=[{"type": "web_search_preview"}],
                tool_choice="auto"
            )
            
            # Extract website from response
            response = provider_response.raw_response
            
            # Extract website from response (handle both responses.create and chat.completions formats)
            website = None
            
            # Try responses.create format first (output_text)
            if hasattr(response, 'output_text') and response.output_text:
                website = response.output_text.strip()
                print(f"[WEBSITE DISCOVERY] Using output_text: {website[:100]}...")
            
            # Try structured output format for web_search_preview
            elif hasattr(response, 'output') and isinstance(response.output, list):
                print(f"[WEBSITE DISCOVERY] Processing structured output with {len(response.output)} items")
                for item in response.output:
                    if isinstance(item, dict) and "content" in item:
                        for block in item["content"]:
                            if block.get("type") == "output_text" and not website:
                                website = block.get("text", "").strip()
                                print(f"[WEBSITE DISCOVERY] Found in structured output: {website[:100]}...")
                            elif block.get("type") == "tool_use" and block.get("tool") == "web_search_preview":
                                # Extract from web search results if needed
                                web_results = block.get("results", [])
                                print(f"[WEBSITE DISCOVERY] Found {len(web_results)} web search results")
            
            # Extract website from provider response content
            if provider_response.content:
                website = provider_response.content.strip()
                print(f"[WEBSITE DISCOVERY] Using provider response content: {website[:100]}...")
            else:
                # Fallback: try to extract from raw_response if available
                if hasattr(response, 'choices') and len(response.choices) > 0:
                    website = response.choices[0].message.content.strip()
                    print(f"[WEBSITE DISCOVERY] Using choices fallback: {website[:100]}...")
                elif hasattr(response, 'output'):
                    website = response.output.strip()
                    print(f"[WEBSITE DISCOVERY] Using output fallback: {website[:100]}...")
                else:
                    website = str(response).strip() if response else None
                    print(f"[WEBSITE DISCOVERY] Using string fallback: {website[:100] if website else 'None'}...")
            
            if website and website != "NOT_FOUND" and ("http://" in website or "https://" in website):
                # Clean up the URL
                website = website.strip().rstrip('/').split()[0]  # Take first URL if multiple
                print(f"[WEBSITE DISCOVERY] Found: {website}")
                return website
            
            print(f"[WEBSITE DISCOVERY] Not found for {company_name}")
            return None
            
        except Exception as e:
            print(f"[ERROR] Error discovering website: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def analyze_company(self, company_name: str, company_number: str = None, website: str = None, known_facts: str = None, excluded_addresses: list = None, update_financial_data: bool = True, update_addresses: bool = True, customer_id: str = None) -> Dict[str, Any]:
        """
        Comprehensive company analysis using AI, Companies House, Google Maps, and web scraping
        
        Args:
            company_name: Company name to analyze
            company_number: Optional Companies House company number
            website: Optional company website URL
            known_facts: Optional known facts about the company
            excluded_addresses: Optional list of excluded address place_ids
            update_financial_data: Whether to fetch/update Companies House data (default: True)
            update_addresses: Whether to fetch/update Google Maps address data (default: True)
            customer_id: Optional customer ID for storing accounts documents in MinIO
        """
        try:
            # If no website provided, try to find it via Google search
            if not website:
                print(f"[AI ANALYSIS] No website provided, attempting to discover via AI...")
                website = await self._discover_website(company_name)
                if website:
                    print(f"[AI ANALYSIS] Discovered website: {website}")
            
            # Gather data from multiple sources
            companies_house_data = {}
            google_maps_data = {}
            web_scraping_data = {}
            
            # Get Companies House data - only if update_financial_data is True
            if update_financial_data:
                if company_number:
                    print(f"[CH] Getting company profile for number: {company_number}")
                    companies_house_data = await self.companies_house_service.get_company_profile(company_number, customer_id, self.tenant_id)
                else:
                    print(f"[CH] Searching for company by name: {company_name}")
                    # Search for company first
                    search_result = await self.companies_house_service.search_companies(company_name)
                    print(f"[CH] Search result: {search_result}")
                    if search_result and not search_result.get('error'):
                        items = search_result.get('items', [])
                        if items and len(items) > 0:
                            # Use first result
                            first_company = items[0]
                            company_number = first_company.get('company_number')
                            if company_number:
                                print(f"[CH] Found company number: {company_number}, fetching full profile")
                                companies_house_data = await self.companies_house_service.get_company_profile(company_number, customer_id, self.tenant_id)
                    else:
                        print(f"[CH] Search failed or returned no results: {search_result.get('error', 'No companies found')}")
            else:
                print(f"[CH] Skipping Companies House data fetch (update_financial_data=False)")
            
            # Get Google Maps data for company locations - only if update_addresses is True
            if update_addresses:
                print(f"[GOOGLE MAPS] Fetching address data for: {company_name}")
                google_maps_data = await self.google_maps_service.search_company_locations(company_name)
            else:
                print(f"[GOOGLE MAPS] Skipping Google Maps data fetch (update_addresses=False)")
            
            # Get web scraping data (LinkedIn and website)
            if website:
                print(f"[WEB SCRAPING] Scraping website and LinkedIn for {company_name}")
                web_scraping_result = await self.web_scraping_service.scrape_comprehensive(company_name, website)
                if web_scraping_result.get('success'):
                    web_scraping_data = web_scraping_result.get('data', {})
                    print(f"[WEB SCRAPING] Successfully scraped data")
                else:
                    print(f"[WEB SCRAPING] Failed: {web_scraping_result.get('error')}")
            else:
                print(f"[WEB SCRAPING] Skipping - no website provided")
            
            # Combine all data for AI analysis
            analysis_data = {
                "company_name": company_name,
                "company_number": company_number,
                "website": website,
                "companies_house_data": companies_house_data,
                "google_maps_data": google_maps_data,
                "web_scraping_data": web_scraping_data,
                "known_facts": known_facts,
                "excluded_addresses": excluded_addresses or [],
                "analysis_timestamp": asyncio.get_event_loop().time()
            }
            
            # Perform AI analysis
            ai_analysis = await self._perform_ai_analysis(analysis_data)
            
            return {
                "success": True,
                "company_name": company_name,
                "analysis": ai_analysis,
                "source_data": {
                    "companies_house": companies_house_data,
                    "google_maps": google_maps_data,
                    "web_scraping": web_scraping_data
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "company_name": company_name
            }
    
    async def _search_competitors_gpt5(self, company_data: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """
        Use GPT-5 to search for and identify real competitors using web search.
        This is a dedicated, more powerful model just for competitor discovery.
        """
        try:
            company_name = company_data.get('company_name', 'Unknown')
            print(f"[COMPETITORS] Using GPT-5 with web search for competitor discovery: {company_name}")
            
            # Extract key company info for criteria
            ch = company_data.get('companies_house_data', {})
            maps = company_data.get('google_maps_data', {})
            
            company_size = analysis.get('business_size_category', 'Unknown')
            business_sector = analysis.get('business_sector', 'Unknown')
            business_activities = analysis.get('primary_business_activities', '')
            
            # Extract locations from Google Maps data
            locations = []
            postcodes = []
            if maps and maps.get('locations'):
                for loc in maps['locations'][:5]:
                    addr = loc.get('formatted_address', '')
                    if addr:
                        locations.append(addr)
                        # Try to extract postcode
                        parts = addr.split(',')
                        if parts:
                            postcode = parts[-2].strip() if len(parts) > 1 else ''
                            if postcode and len(postcode) <= 4:
                                postcodes.append(postcode)
            
            # Extract financial data for sizing
            turnover = None
            employees = None
            if ch and ch.get('accounts_detail'):
                accounts = ch['accounts_detail']
                turnover_raw = accounts.get('turnover')
                employees_raw = accounts.get('employees')
                
                # Convert to number if string
                if turnover_raw:
                    try:
                        turnover = float(turnover_raw) if isinstance(turnover_raw, str) else turnover_raw
                    except (ValueError, TypeError):
                        turnover = None
                
                if employees_raw:
                    try:
                        employees = int(employees_raw) if isinstance(employees_raw, str) else employees_raw
                    except (ValueError, TypeError):
                        employees = None
            
            locations_text = ', '.join(locations[:3]) if locations else 'Multiple UK locations'
            postcode_text = ', '.join(set(postcodes)) if postcodes else 'UK-wide'
            
            # Get prompt from database
            from app.services.ai_prompt_service import AIPromptService
            from app.models.ai_prompt import PromptCategory
            
            prompt_service = AIPromptService(self.db, tenant_id=self.tenant_id)
            prompt_obj = await prompt_service.get_prompt(
                category=PromptCategory.COMPETITOR_ANALYSIS.value,
                tenant_id=self.tenant_id
            )
            
            # Require database prompt - no fallbacks
            if not prompt_obj:
                error_msg = f"Competitor analysis prompt not found in database for tenant {self.tenant_id}. Please seed prompts using backend/scripts/seed_ai_prompts.py"
                print(f"[ERROR] {error_msg}")
                raise ValueError(error_msg)
            else:
                # Render prompt with variables
                rendered = prompt_service.render_prompt(prompt_obj, {
                    "company_name": company_name,
                    "business_activities": business_activities,
                    "business_sector": business_sector,
                    "company_size": company_size,
                    "locations_text": locations_text,
                    "postcode_text": postcode_text,
                    "turnover": turnover,
                    "employees": employees
                })
                competitor_prompt = rendered['user_prompt']
                system_prompt = rendered['system_prompt']
                model = rendered['model']
                max_tokens = rendered['max_tokens']
            
            # Use AIProviderService for competitor discovery
            if not self.provider_service:
                return []
            
            # Use database prompt (required - no fallback)
            provider_response = await self.provider_service.generate(
                prompt=prompt_obj,
                variables={
                    "company_name": company_name,
                    "business_sector": business_sector,
                    "company_size": company_size,
                    "locations_text": locations_text,
                    "postcode_text": postcode_text,
                    "turnover": turnover,
                    "employees": employees
                },
                max_tokens=max_tokens
            )
            
            result_text = provider_response.content
            print(f"[COMPETITORS] GPT-5 response:\n{result_text[:500]}")
            
            # Parse competitor names (one per line)
            lines = result_text.split('\n')
            competitors = []
            
            for line in lines:
                line = line.strip()
                # Skip empty lines and explanatory text
                if not line or len(line) < 3:
                    continue
                
                # Skip lines that are clearly explanatory
                skip_keywords = ['based on', 'similar to', 'type of', 'note:', 'example:', 'explanation', 
                               'verification', 'criteria', 'search', 'company must', 'competitor must']
                if any(keyword in line.lower() for keyword in skip_keywords):
                    continue
                
                # Try to extract company name (usually before URL or location details)
                # Format could be: "CompanyName (location)" or "CompanyName - why" or "1. CompanyName"
                company = line
                if '(' in line:
                    company = line.split('(')[0].strip()
                if '-' in line and not line.startswith('-'):
                    company = line.split('-')[0].strip()
                if '.' in line and line[0].isdigit():
                    company = line.split('.', 1)[1].strip() if len(line.split('.', 1)) > 1 else line
                
                # Remove markdown formatting
                company = company.replace('**', '').replace('##', '').strip()
                
                if company and len(company) > 3:
                    competitors.append(company)
            
            print(f"[COMPETITORS] Found {len(competitors)} verified competitors: {competitors}")
            return competitors[:10]  # Return top 10
            
        except Exception as e:
            print(f"[COMPETITORS] Error in GPT-5 competitor search: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def _perform_ai_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform AI analysis on company data"""
        if not self.provider_service:
            return {"error": "AI service not available"}
        
        try:
            # Prepare comprehensive company information (v1 approach)
            company_info = f"Company Name: {data.get('company_name', 'Unknown')}"
            
            # Add Companies House data
            ch = data.get('companies_house_data', {})
            if ch:
                company_info += f"\n\nCompanies House Data:"
                if ch.get('company_number'):
                    company_info += f"\n- Company Number: {ch['company_number']}"
                if ch.get('company_status'):
                    company_info += f"\n- Status: {ch['company_status']}"
                if ch.get('company_type'):
                    company_info += f"\n- Type: {ch['company_type']}"
                if ch.get('date_of_creation'):
                    company_info += f"\n- Founded: {ch['date_of_creation']}"
                if ch.get('registered_office_address'):
                    company_info += f"\n- Registered Address: {ch['registered_office_address']}"
                if ch.get('sic_codes'):
                    company_info += f"\n- SIC Codes: {ch['sic_codes']}"
                
                # Add detailed financial information
                if ch.get('accounts_detail'):
                    accounts = ch['accounts_detail']
                    company_info += f"\n\nFinancial Information (from Companies House):"
                    if accounts.get('company_size'):
                        company_info += f"\n- Company Size: {accounts['company_size']}"
                    if accounts.get('estimated_revenue'):
                        company_info += f"\n- Estimated Revenue Range: {accounts['estimated_revenue']}"
                    
                    # Enhanced financial data display
                    if accounts.get('shareholders_funds'):
                        company_info += f"\n- Shareholders' Funds: {accounts['shareholders_funds']}"
                    if accounts.get('cash_at_bank'):
                        company_info += f"\n- Cash at Bank: {accounts['cash_at_bank']}"
                    if accounts.get('turnover'):
                        company_info += f"\n- Turnover: {accounts['turnover']}"
                    if accounts.get('employees'):
                        company_info += f"\n- Estimated Employees: {accounts['employees']}"
                    if accounts.get('revenue_growth'):
                        company_info += f"\n- Revenue Growth Trend: {accounts['revenue_growth']}"
                    if accounts.get('profitability_trend'):
                        company_info += f"\n- Profitability Trend: {accounts['profitability_trend']}"
                    if accounts.get('financial_health_score'):
                        company_info += f"\n- Financial Health Score: {accounts['financial_health_score']}/100"
                    if accounts.get('years_of_data'):
                        company_info += f"\n- Years of Financial Data Available: {accounts['years_of_data']}"
                    
                    # Multi-year financial history
                    if accounts.get('detailed_financials'):
                        company_info += f"\n\nFinancial History (Last {len(accounts['detailed_financials'])} Years):"
                        for i, year_data in enumerate(accounts['detailed_financials'][:3]):  # Show last 3 years
                            year_label = "Current" if i == 0 else f"Year -{i}"
                            company_info += f"\n{year_label} Year ({year_data.get('filing_date', 'Unknown')}):"
                            if year_data.get('turnover'):
                                company_info += f"\n  - Turnover: £{year_data['turnover']:,.0f}" if isinstance(year_data['turnover'], (int, float)) else f"\n  - Turnover: {year_data['turnover']}"
                            if year_data.get('shareholders_funds'):
                                company_info += f"\n  - Shareholders' Funds: £{year_data['shareholders_funds']:,.0f}" if isinstance(year_data['shareholders_funds'], (int, float)) else f"\n  - Shareholders' Funds: {year_data['shareholders_funds']}"
                            if year_data.get('cash_at_bank'):
                                company_info += f"\n  - Cash at Bank: £{year_data['cash_at_bank']:,.0f}" if isinstance(year_data['cash_at_bank'], (int, float)) else f"\n  - Cash at Bank: {year_data['cash_at_bank']}"
                            if year_data.get('profit_before_tax'):
                                company_info += f"\n  - Profit Before Tax: £{year_data['profit_before_tax']:,.0f}" if isinstance(year_data['profit_before_tax'], (int, float)) else f"\n  - Profit Before Tax: {year_data['profit_before_tax']}"
                    
                    # Add active directors information
                    if accounts.get('active_directors'):
                        directors = accounts['active_directors']
                        company_info += f"\n\nActive Directors/Officers ({accounts.get('total_active_directors', len(directors))}):"
                        for i, director in enumerate(directors, 1):
                            company_info += f"\n\n{i}. {director.get('name', 'Unknown')}"
                            if director.get('role'):
                                company_info += f"\n   Role: {director['role']}"
                            if director.get('appointed_on'):
                                company_info += f"\n   Appointed: {director['appointed_on']}"
                            if director.get('occupation'):
                                company_info += f"\n   Occupation: {director['occupation']}"
                            if director.get('nationality'):
                                company_info += f"\n   Nationality: {director['nationality']}"
            
            # Add Google Maps data
            maps = data.get('google_maps_data', {})
            if maps:
                company_info += f"\n\nGoogle Maps Location Data:"
                if maps.get('locations'):
                    company_info += f"\n- Primary Locations: {len(maps['locations'])} found"
                    for i, location in enumerate(maps['locations'][:5]):  # Show first 5 locations
                        company_info += f"\n  Location {i+1}: {location.get('name', 'Unknown')}"
                        company_info += f"\n    Address: {location.get('formatted_address', 'N/A')}"
                        if location.get('formatted_phone_number'):
                            company_info += f"\n    Phone: {location['formatted_phone_number']}"
                        if location.get('rating'):
                            company_info += f"\n    Rating: {location['rating']}/5"
            
            # Add web scraping data (LinkedIn and Website)
            web_data = data.get('web_scraping_data', {})
            if web_data:
                # Add LinkedIn data
                linkedin = web_data.get('linkedin', {})
                if linkedin:
                    company_info += f"\n\nLinkedIn Data:"
                    if linkedin.get('linkedin_url'):
                        company_info += f"\n- LinkedIn URL: {linkedin['linkedin_url']}"
                    if linkedin.get('linkedin_industry'):
                        company_info += f"\n- Industry: {linkedin['linkedin_industry']}"
                    if linkedin.get('linkedin_company_size'):
                        company_info += f"\n- Company Size: {linkedin['linkedin_company_size']}"
                    if linkedin.get('linkedin_description'):
                        company_info += f"\n- Description: {linkedin['linkedin_description']}"
                    if linkedin.get('linkedin_headquarters'):
                        company_info += f"\n- Headquarters: {linkedin['linkedin_headquarters']}"
                    if linkedin.get('linkedin_founded'):
                        company_info += f"\n- Founded: {linkedin['linkedin_founded']}"
                
                # Add website scraping data
                website_data = web_data.get('website', {})
                if website_data:
                    company_info += f"\n\nWebsite Data:"
                    if website_data.get('website_title'):
                        company_info += f"\n- Title: {website_data['website_title']}"
                    if website_data.get('website_description'):
                        company_info += f"\n- Description: {website_data['website_description']}"
                    if website_data.get('contact_info') and website_data['contact_info']:
                        company_info += f"\n- Contact Info: {', '.join(str(c) for c in website_data['contact_info'][:5])}"
                    if website_data.get('key_phrases') and website_data['key_phrases']:
                        company_info += f"\n- Key Phrases: {', '.join(phrase[0] for phrase in website_data['key_phrases'][:10])}"
                    if website_data.get('locations') and website_data['locations']:
                        company_info += f"\n- Locations Mentioned on Website: {', '.join(website_data['locations'][:5])}"
                    if website_data.get('addresses') and website_data['addresses']:
                        company_info += f"\n- Addresses Found on Website ({len(website_data['addresses'])}):"
                        for addr in website_data['addresses'][:3]:
                            company_info += f"\n  • {addr}"
                    if website_data.get('additional_sites') and website_data['additional_sites']:
                        company_info += f"\n- Additional Sites/Offices: {', '.join(website_data['additional_sites'][:5])}"
            
            # Add user-provided known facts
            known_facts = data.get('known_facts', '')
            if known_facts:
                company_info += f"\n\n**IMPORTANT - Known Facts (User-Verified Information):**\n{known_facts}\n\nPlease take these user-provided facts into account when analyzing the company. They represent verified information that should take precedence over conflicting data from other sources."
            
            # Add excluded addresses (user has marked as "Not this business")
            excluded_addresses = data.get('excluded_addresses', [])
            if excluded_addresses and len(excluded_addresses) > 0:
                company_info += f"\n\n**EXCLUDED LOCATIONS (NOT this business):**"
                company_info += f"\nThe following {len(excluded_addresses)} locations have been verified as NOT belonging to this company:"
                
                # Look up the location details from Google Maps data
                maps_locations = data.get('google_maps_data', {}).get('locations', [])
                for excluded_id in excluded_addresses:
                    # Find the location details
                    excluded_location = next((loc for loc in maps_locations if loc.get('place_id') == excluded_id), None)
                    if excluded_location:
                        company_info += f"\n- {excluded_location.get('formatted_address', excluded_id)} (IGNORE THIS ADDRESS)"
                    else:
                        company_info += f"\n- Location ID: {excluded_id} (IGNORE THIS ADDRESS)"
                
                company_info += f"\n\n**CRITICAL:** Do NOT use the above excluded addresses in your analysis. Do NOT mention them as company locations. They have been verified as belonging to different businesses with similar names."
            
            # Get tenant profile information to contextualize the analysis
            tenant_context = ""
            if self.db and self.tenant_id:
                try:
                    from app.models.tenant import Tenant
                    tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
                    
                    if tenant:
                        if tenant.company_name:
                            tenant_context += f"\n\n**YOUR COMPANY: {tenant.company_name}**"
                        
                        if tenant.company_description:
                            tenant_context += f"\n\nAbout Your Company:\n{tenant.company_description}"
                        
                        if tenant.products_services and isinstance(tenant.products_services, list):
                            tenant_context += f"\n\nYour Products/Services:\n" + "\n".join([f"- {p}" for p in tenant.products_services])
                        
                        if tenant.unique_selling_points and isinstance(tenant.unique_selling_points, list):
                            tenant_context += f"\n\nYour Core Strengths/USPs:\n" + "\n".join([f"- {u}" for u in tenant.unique_selling_points])
                        
                        if tenant.target_markets and isinstance(tenant.target_markets, list):
                            tenant_context += f"\n\nYour Target Markets:\n" + "\n".join([f"- {m}" for m in tenant.target_markets])
                        
                        if tenant.elevator_pitch:
                            tenant_context += f"\n\nYour Value Proposition:\n{tenant.elevator_pitch}"
                        
                        if tenant.sales_methodology:
                            tenant_context += f"\n\nYour Sales Methodology (How you help customers):\n{tenant.sales_methodology}"
                        
                        if tenant.partnership_opportunities:
                            tenant_context += f"\n\nB2B Partnership Opportunities (How to work WITH similar businesses):\n{tenant.partnership_opportunities}"
                        
                        # Debug: Show what tenant context was loaded
                        print(f"[AI ANALYSIS] Loaded tenant context for: {tenant.company_name}")
                        print(f"[AI ANALYSIS] Tenant context length: {len(tenant_context)} chars")
                        if tenant_context:
                            print(f"[AI ANALYSIS] Tenant context preview: {tenant_context[:200]}...")
                except Exception as e:
                    print(f"[DEBUG] Could not load tenant context: {e}")
            
            # Get prompt from database
            from app.services.ai_prompt_service import AIPromptService
            from app.models.ai_prompt import PromptCategory
            
            prompt_service = AIPromptService(self.db, tenant_id=self.tenant_id)
            prompt_obj = await prompt_service.get_prompt(
                category=PromptCategory.CUSTOMER_ANALYSIS.value,
                tenant_id=self.tenant_id
            )
            
            # Require database prompt - no fallbacks
            if not prompt_obj:
                error_msg = f"Customer analysis prompt not found in database for tenant {self.tenant_id}. Please seed prompts using backend/scripts/seed_ai_prompts.py"
                print(f"[ERROR] {error_msg}")
                raise ValueError(error_msg)
            else:
                # Render prompt with variables
                rendered = prompt_service.render_prompt(prompt_obj, {
                    "tenant_context": tenant_context,
                    "company_info": company_info
                })
                user_prompt = rendered['user_prompt']
                system_prompt = rendered['system_prompt']
                model = rendered['model']
                max_tokens = rendered['max_tokens']
            
            prompt = user_prompt
            
            print(f"[AI] Making AI provider call for customer analysis...")
            print(f"[AI] System prompt: {system_prompt[:100]}...")
            
            if not self.provider_service:
                raise Exception("AI provider service not available")
            
            # Use database prompt (required - no fallback)
            provider_response = await self.provider_service.generate(
                prompt=prompt_obj,
                variables={
                    "tenant_context": tenant_context,
                    "company_info": company_info
                },
                max_tokens=max_tokens
            )
            
            print(f"[AI] AI provider call successful, processing response...")
            result_text = provider_response.content
            
            # Debug: Check if content is empty
            if not result_text or len(result_text.strip()) < 10:
                print(f"[AI] ⚠️ WARNING: Empty or very short content from provider_response")
                print(f"[AI] Content length: {len(result_text) if result_text else 0}")
                print(f"[AI] Content preview: {result_text[:200] if result_text else 'None'}")
                print(f"[AI] Provider response type: {type(provider_response)}")
                print(f"[AI] Provider response attributes: {[a for a in dir(provider_response) if not a.startswith('_')]}")
                
                # Try to get raw response
                if hasattr(provider_response, 'raw_response'):
                    raw = provider_response.raw_response
                    print(f"[AI] Raw response type: {type(raw)}")
                    if hasattr(raw, 'output'):
                        print(f"[AI] Raw response has 'output' attribute: {type(raw.output)}")
                        if isinstance(raw.output, dict):
                            print(f"[AI] Raw response.output keys: {list(raw.output.keys())}")
                            if 'text' in raw.output:
                                result_text = str(raw.output['text']).strip()
                                print(f"[AI] ✅ Extracted content from raw_response.output.text: {len(result_text)} chars")
                
                if not result_text or len(result_text.strip()) < 10:
                    raise Exception(f"No valid content extracted from AI provider response. Content length: {len(result_text) if result_text else 0}")
            
            # Parse JSON response
            # Remove markdown code blocks if present
            if result_text.strip().startswith('```'):
                result_text = result_text.strip()
                if result_text.startswith('```json'):
                    result_text = result_text[7:]
                elif result_text.startswith('```'):
                    result_text = result_text[3:]
                if result_text.endswith('```'):
                    result_text = result_text[:-3]
                result_text = result_text.strip()
            
            analysis = json.loads(result_text)
            
            # Normalize competitors field to always be an array
            if 'competitors' in analysis:
                competitors = analysis['competitors']
                # If competitors is a string (description), keep it as-is since the frontend handles both formats
                # If it's already an array, keep it as-is
                # This ensures consistent handling in the frontend
                if isinstance(competitors, str):
                    # If it looks like a single company name (no common description words), keep as array of one
                    if not any(word in competitors.lower() for word in ['contractor', 'firm', 'company', 'include', 'type', 'local', 'regional', 'national']):
                        analysis['competitors'] = [competitors]
                    # Otherwise keep as description string - frontend will display as-is
            
            # Calculate lead score based on AI analysis
            analysis['lead_score'] = self._calculate_lead_score(analysis)
            
            # Use GPT-5 to search for and identify real competitors
            analysis['competitors'] = await self._search_competitors_gpt5(data, analysis)
            
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parsing error: {e}")
            return {"error": f"AI returned invalid JSON: {str(e)}"}
        except Exception as e:
            print(f"[ERROR] Error in AI analysis: {e}")
            return {"error": str(e)}
    
    async def analyze_company_light(self, company_name: str, website: str = None, companies_house_data: dict = None, google_maps_data: dict = None) -> Dict[str, Any]:
        """
        Light AI analysis for campaign-generated leads
        Provides basic business intelligence and extracts contact information
        """
        try:
            print(f"[AI ANALYSIS LIGHT] Analyzing {company_name}")
            
            # Build comprehensive context from available data
            context_parts = [f"Company: {company_name}"]
            
            if website:
                context_parts.append(f"Website: {website}")
            
            # Add Companies House data with more detail
            if companies_house_data:
                context_parts.append(f"\nCompanies House Data:")
                if companies_house_data.get('company_number'):
                    context_parts.append(f"- Company Number: {companies_house_data.get('company_number')}")
                if companies_house_data.get('company_status'):
                    context_parts.append(f"- Status: {companies_house_data.get('company_status')}")
                if companies_house_data.get('company_type'):
                    context_parts.append(f"- Type: {companies_house_data.get('company_type')}")
                if companies_house_data.get('date_of_creation'):
                    context_parts.append(f"- Founded: {companies_house_data.get('date_of_creation')}")
                if companies_house_data.get('registered_office_address'):
                    context_parts.append(f"- Registered Address: {companies_house_data.get('registered_office_address')}")
                if companies_house_data.get('sic_codes'):
                    context_parts.append(f"- SIC Codes: {companies_house_data.get('sic_codes')}")
                
                # Add director information (potential contacts)
                if companies_house_data.get('officers'):
                    context_parts.append(f"- Directors: {companies_house_data.get('officers')}")
            
            # Add Google Maps data with contact info
            if google_maps_data:
                context_parts.append(f"\nGoogle Maps Data:")
                if google_maps_data.get('formatted_address'):
                    context_parts.append(f"- Address: {google_maps_data.get('formatted_address')}")
                if google_maps_data.get('rating'):
                    context_parts.append(f"- Rating: {google_maps_data.get('rating')}/5")
                if google_maps_data.get('types'):
                    business_types = [t.replace('_', ' ').title() for t in google_maps_data.get('types', [])]
                    context_parts.append(f"- Business Type: {', '.join(business_types[:3])}")
                if google_maps_data.get('formatted_phone_number'):
                    context_parts.append(f"- Phone: {google_maps_data.get('formatted_phone_number')}")
                if google_maps_data.get('website'):
                    context_parts.append(f"- Website: {google_maps_data.get('website')}")
                if google_maps_data.get('business_status'):
                    context_parts.append(f"- Status: {google_maps_data.get('business_status')}")
            
            context = "\n".join(context_parts)
            
            # Get tenant context for analysis
            tenant_context = await self._get_tenant_context()
            
            # Simplified light AI analysis prompt for business intelligence
            prompt = f"""
            Analyze this UK company and provide business intelligence:
            
            Company Data:
            {context}
            
            About {tenant_context['company_name']}:
            {tenant_context['company_description']}
            Services: {', '.join(tenant_context['products_services'][:5])}
            Target Markets: {', '.join(tenant_context['target_markets'][:3])}
            
            Provide a concise business analysis:
            - Business Overview (2-3 sentences about what they do)
            - Key Opportunities for {tenant_context['company_name']} (2-3 specific opportunities)
            - Potential Challenges (1-2 challenges or considerations)
            - Recommended Sales Approach (1-2 sentences on how to engage)
            
            Focus on factual, actionable insights based on the data provided.
            Be concise and professional. Keep the total response under 400 words.
            """
            
            # Use AIProviderService for light analysis
            if not self.provider_service:
                raise Exception("AI provider service not available")
            
            provider_response = await self.provider_service.generate_with_rendered_prompts(
                prompt=None,
                system_prompt="You are a business intelligence analyst specializing in UK companies. Extract contact information and provide actionable business insights.",
                user_prompt=prompt,
                max_tokens=10000  # High token limit for comprehensive analysis
            )
            
            analysis_text = provider_response.content
            print(f"[AI ANALYSIS LIGHT] Generated {len(analysis_text) if analysis_text else 0} characters")
            
            # Return simplified analysis
            return {
                "company_name": company_name,
                "light_analysis": analysis_text,
                "analysis_type": "light",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "data_sources": {
                    "website": bool(website),
                    "companies_house": bool(companies_house_data),
                    "google_maps": bool(google_maps_data)
                }
            }
            
        except Exception as e:
            print(f"[AI ANALYSIS LIGHT] Error: {e}")
            return {
                "company_name": company_name,
                "light_analysis": f"Quick analysis unavailable for {company_name}. Error: {str(e)}",
                "analysis_type": "light",
                "error": str(e)
            }
    
    async def _get_tenant_context(self) -> Dict[str, Any]:
        """
        Get tenant context for AI analysis
        
        Returns structured context about the tenant's business
        """
        try:
            from app.models.tenant import Tenant
            
            # Get tenant from database
            tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
            
            if not tenant:
                return {
                    'company_name': 'our company',
                    'company_description': 'We provide professional services to businesses.',
                    'products_services': ['Professional services'],
                    'target_markets': ['General business'],
                    'unique_selling_points': ['Quality service']
                }
            
            return {
                'company_name': tenant.company_name or 'our company',
                'company_description': tenant.company_description or 'We provide professional services to businesses.',
                'products_services': tenant.products_services or ['Professional services'],
                'target_markets': tenant.target_markets or ['General business'],
                'unique_selling_points': tenant.unique_selling_points or ['Quality service']
            }
            
        except Exception as e:
            print(f"[AI ANALYSIS] Error getting tenant context: {e}")
            return {
                'company_name': 'our company',
                'company_description': 'We provide professional services to businesses.',
                'products_services': ['Professional services'],
                'target_markets': ['General business'],
                'unique_selling_points': ['Quality service']
            }
    
    async def analyze_financial_data(self, company_number: str) -> Dict[str, Any]:
        """Analyze financial data from Companies House"""
        try:
            financial_data = await self.companies_house_service.get_financial_data(company_number)
            
            if not financial_data:
                return {"error": "No financial data available"}
            
            # AI analysis of financial health
            if self.provider_service:
                financial_analysis = await self._analyze_financial_health(financial_data)
                return {
                    "success": True,
                    "financial_data": financial_data,
                    "analysis": financial_analysis
                }
            else:
                return {
                    "success": True,
                    "financial_data": financial_data,
                    "analysis": {"error": "AI analysis not available"}
                }
                
        except Exception as e:
            return {"error": str(e)}
    
    async def _analyze_financial_health(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """AI analysis of financial health"""
        try:
            system_prompt = """You are a financial analyst specializing in assessing company financial health for B2B sales opportunities.
            
            Analyze the financial data and provide insights on:
            1. Financial stability and health
            2. Growth trends and patterns
            3. Ability to pay for services
            4. Risk assessment
            5. Budget estimation capabilities
            6. Payment terms recommendations
            """
            
            user_prompt = f"""
            Analyze this company's financial data for structured cabling sales:

            {json.dumps(financial_data, indent=2)}

            Provide analysis in JSON format with:
            - financial_health: Overall financial health assessment
            - growth_trends: Revenue and profit trends
            - payment_ability: Ability to pay for services
            - risk_level: Low/Medium/High risk assessment
            - budget_estimate: Estimated budget for IT projects
            - payment_terms: Recommended payment terms
            - financial_strengths: Key financial strengths
            - financial_concerns: Potential financial concerns
            """
            
            if not self.provider_service:
                raise Exception("AI provider service not available")
            
            provider_response = await self.provider_service.generate_with_rendered_prompts(
                prompt=None,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=10000
            )
            
            ai_response = provider_response.content
            
            # Try to extract JSON
            try:
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = ai_response[start_idx:end_idx]
                    return json.loads(json_str)
                else:
                    return {"raw_analysis": ai_response}
            except json.JSONDecodeError:
                return {"raw_analysis": ai_response}
                
        except Exception as e:
            return {"error": f"Financial analysis failed: {str(e)}"}
    
    async def generate_lead_strategy(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate lead engagement strategy"""
        if not self.provider_service:
            return {"error": "AI service not available"}
        
        try:
            system_prompt = self._build_dynamic_system_prompt("sales") + """
            
            Create a comprehensive engagement strategy including:
            1. Initial contact approach
            2. Key messaging and value propositions
            3. Decision maker identification
            4. Timeline and follow-up strategy
            5. Competitive positioning
            6. Risk mitigation
            """
            
            user_prompt = f"""
            Create an engagement strategy for this lead:

            {json.dumps(company_data, indent=2)}

            Provide strategy in JSON format with:
            - initial_approach: Recommended first contact method
            - key_messaging: Key value propositions to highlight
            - decision_makers: Identified decision makers and roles
            - timeline: Recommended engagement timeline
            - follow_up_strategy: Follow-up plan and cadence
            - competitive_positioning: How to position against competitors
            - risk_mitigation: Strategies to address potential risks
            - success_indicators: Signs of a successful engagement
            """
            
            if not self.provider_service:
                raise Exception("AI provider service not available")
            
            provider_response = await self.provider_service.generate_with_rendered_prompts(
                prompt=None,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=10000
            )
            
            ai_response = provider_response.content
            
            # Try to extract JSON
            try:
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = ai_response[start_idx:end_idx]
                    return json.loads(json_str)
                else:
                    return {"raw_strategy": ai_response}
            except json.JSONDecodeError:
                return {"raw_strategy": ai_response}
                
        except Exception as e:
            return {"error": f"Strategy generation failed: {str(e)}"}
    
    async def score_lead(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score lead quality using AI"""
        if not self.provider_service:
            return {"error": "AI service not available"}
        
        try:
            system_prompt = self._build_dynamic_system_prompt("lead_scoring") + """
            
            Score leads based on:
            1. Company size and growth
            2. Industry fit with our target markets
            3. Financial stability
            4. Needs alignment with our products/services
            5. Decision-making capability
            6. Timeline and urgency
            7. Budget availability
            
            Provide a score from 1-100 and detailed reasoning."""
            
            user_prompt = f"""
            Score this lead for structured cabling opportunities:

            {json.dumps(company_data, indent=2)}

            Provide scoring in JSON format with:
            - overall_score: Score from 1-100
            - score_breakdown: Individual factor scores
            - reasoning: Detailed reasoning for the score
            - recommendations: Actions to improve the lead
            - priority_level: High/Medium/Low priority
            """
            
            if not self.provider_service:
                raise Exception("AI provider service not available")
            
            provider_response = await self.provider_service.generate_with_rendered_prompts(
                prompt=None,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=10000
            )
            
            ai_response = provider_response.content
            
            # Try to extract JSON
            try:
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = ai_response[start_idx:end_idx]
                    return json.loads(json_str)
                else:
                    return {"raw_scoring": ai_response}
            except json.JSONDecodeError:
                return {"raw_scoring": ai_response}
                
        except Exception as e:
            return {"error": f"Lead scoring failed: {str(e)}"}
    
    def _calculate_lead_score(self, analysis: Dict[str, Any]) -> int:
        """Calculate lead score (0-100) based on AI analysis (matching v1 logic)"""
        try:
            score = 50  # Base score
            
            # Business size scoring
            size_category = str(analysis.get('business_size_category', '')).lower()
            if size_category in ['large', 'enterprise']:
                score += 20
            elif size_category == 'medium':
                score += 10
            
            # Technology maturity scoring
            tech_maturity = str(analysis.get('technology_maturity', '')).lower()
            if tech_maturity == 'enterprise':
                score += 15
            elif tech_maturity == 'advanced':
                score += 10
            elif tech_maturity == 'intermediate':
                score += 5
            
            # Growth potential scoring (improved to handle variations like "Medium-High")
            growth_potential = str(analysis.get('growth_potential', '')).lower()
            if 'high' in growth_potential:
                # Check for "high" first (handles "high", "medium-high", "high-medium", etc.)
                if growth_potential == 'high':
                    score += 15  # Pure high
                elif 'medium' in growth_potential:
                    score += 12  # Medium-High or High-Medium (between medium and high)
                else:
                    score += 15  # Contains "high" but not "medium"
            elif growth_potential == 'medium':
                score += 8
            
            # Service budget scoring (improved pattern matching)
            service_budget = str(analysis.get('service_budget_estimate', analysis.get('it_budget_estimate', ''))).lower()
            
            # Remove common formatting characters for easier matching
            budget_clean = service_budget.replace(',', '').replace('£', '').replace('$', '').replace(' ', '')
            
            # Check for high-value budgets (50k+, 100k+, 1m+)
            # Match patterns like: 50k, 50000, 50,000, £50k, etc.
            # Extract numbers and check for high-value ranges
            numbers = re.findall(r'\d+', budget_clean)
            has_high_budget = False
            has_medium_budget = False
            
            # Check text patterns first (more reliable)
            if '50k' in budget_clean or '100k' in budget_clean or '1m' in budget_clean or 'million' in budget_clean:
                has_high_budget = True
            elif '10k' in budget_clean or '25k' in budget_clean or '10,000' in service_budget or '25,000' in service_budget:
                has_medium_budget = True
            
            # Also check numeric values
            for num_str in numbers:
                try:
                    num = int(num_str)
                    # Check for high-value budgets (50k+)
                    if num >= 50000:
                        has_high_budget = True
                        break
                    # Check for medium budgets (10k-49k)
                    elif num >= 10000 and not has_high_budget:
                        has_medium_budget = True
                except ValueError:
                    continue
            
            if has_high_budget:
                score += 10
            elif has_medium_budget:
                score += 5
            
            return min(100, max(0, score))
            
        except Exception as e:
            print(f"[ERROR] Error calculating lead score: {e}")
            return 50
    
    async def get_dashboard_insight(self, context: str, query: str = "", tenant_context: str = "", user_context: str = "") -> str:
        """
        Get AI-powered dashboard insights based on CRM data
        
        IMPORTANT: Uses database prompt from dashboard_analytics category.
        Returns empty string if OpenAI client is not initialized or API call fails.
        
        Args:
            context: CRM data snapshot (customers, leads, trends, metrics)
            query: User's question (optional, can be extracted from context if needed)
            tenant_context: Tenant business profile (company description, products/services, USPs)
            user_context: User profile information (name, email) for personalization
        """
        if not self.provider_service:
            error_msg = "AI service is currently unavailable. Please check your API configuration."
            print(f"[ERROR] {error_msg}")
            return error_msg
        
        if not self.db or not self.tenant_id:
            error_msg = "Database connection or tenant ID not available."
            print(f"[ERROR] {error_msg}")
            return error_msg
        
        try:
            # Get prompt from database - REQUIRED, no fallback
            from app.services.ai_prompt_service import AIPromptService
            prompt_service = AIPromptService(self.db, tenant_id=self.tenant_id)
            
            prompt_obj = await prompt_service.get_prompt(
                category=PromptCategory.DASHBOARD_ANALYTICS.value,
                tenant_id=self.tenant_id
            )
            
            if not prompt_obj:
                error_msg = "Dashboard analytics prompt not configured. Please configure prompts in the admin section."
                print(f"[ERROR] {error_msg}")
                return error_msg
            
            # Extract query from context if not provided
            # The context contains the full prompt including the query at the end
            if not query:
                # Try to extract query from context (it's usually at the end after "=== USER QUESTION ===")
                if "=== USER QUESTION ===" in context:
                    parts = context.split("=== USER QUESTION ===")
                    if len(parts) > 1:
                        query = parts[-1].strip()
                else:
                    # Fallback: use a generic query
                    query = "Analyze the CRM data and provide insights"
            
            # Render prompt with variables (including tenant_context and user_context)
            rendered = prompt_service.render_prompt(prompt_obj, {
                "context": context,
                "query": query,
                "tenant_context": tenant_context or "No company profile information available.",
                "user_context": user_context or ""
            })
            
            system_prompt = rendered['system_prompt']
            user_prompt = rendered['user_prompt']
            max_tokens = rendered['max_tokens']
            
            print(f"[DEBUG] Using database prompt '{prompt_obj.name}' with max_tokens={max_tokens}")
            print(f"[DEBUG] Calling AI provider with context length: {len(context)} characters")
            
            # Use database prompt
            provider_response = await self.provider_service.generate_with_rendered_prompts(
                prompt=prompt_obj,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens
            )
            
            print(f"[DEBUG] AI provider response received")
            
            if provider_response and provider_response.content:
                answer = provider_response.content
                print(f"[DEBUG] Answer length: {len(answer)} characters")
                
                if not answer or not answer.strip():
                    return "I received your question but couldn't generate a response. Please try again."
                
                return answer.strip()
            else:
                print(f"[ERROR] No content in provider response!")
                return "I received your question but couldn't generate a response. Please try again."
            
        except Exception as e:
            error_msg = f"I'm unable to provide an answer at this time. Error: {str(e)}"
            print(f"[ERROR] Dashboard insight generation failed: {e}")
            import traceback
            print(traceback.format_exc())
            return error_msg

