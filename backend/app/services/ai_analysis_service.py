#!/usr/bin/env python3
"""
AI Analysis Service for Company Analysis and Lead Generation
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from openai import OpenAI
import httpx

from app.core.config import settings
from app.services.companies_house_service import CompaniesHouseService
from app.services.google_maps_service import GoogleMapsService
from app.services.web_scraping_service import WebScrapingService


class AIAnalysisService:
    """Service for AI-powered company analysis and lead generation"""
    
    def __init__(self, openai_api_key: Optional[str] = None, 
                 companies_house_api_key: Optional[str] = None,
                 google_maps_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or settings.OPENAI_API_KEY
        self.companies_house_api_key = companies_house_api_key or settings.COMPANIES_HOUSE_API_KEY
        self.google_maps_api_key = google_maps_api_key or settings.GOOGLE_MAPS_API_KEY
        
        self.openai_client = None
        self.companies_house_service = CompaniesHouseService(api_key=self.companies_house_api_key)
        self.google_maps_service = GoogleMapsService(api_key=self.google_maps_api_key)
        self.web_scraping_service = WebScrapingService()
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            if self.openai_api_key:
                self.openai_client = OpenAI(
                    api_key=self.openai_api_key,
                    timeout=300.0
                )
        except Exception as e:
            print(f"[ERROR] Error initializing AI analysis client: {e}")
    
    async def _discover_website(self, company_name: str) -> str:
        """Use AI to discover company website via simple search"""
        try:
            if not self.openai_client:
                return None
            
            prompt = f"""Find the official website URL for the company: {company_name}

Please respond with ONLY the website URL (e.g., https://example.com) or "NOT_FOUND" if you cannot find it.
Do not include any explanation, just the URL or NOT_FOUND."""

            response = self.openai_client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that finds company websites. Respond only with the URL or NOT_FOUND."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=100,
                timeout=30.0
            )
            
            website = response.choices[0].message.content.strip()
            
            if website and website != "NOT_FOUND" and ("http://" in website or "https://" in website):
                # Clean up the URL
                website = website.strip().rstrip('/')
                return website
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Error discovering website: {e}")
            return None
    
    async def analyze_company(self, company_name: str, company_number: str = None, website: str = None, known_facts: str = None) -> Dict[str, Any]:
        """Comprehensive company analysis using AI, Companies House, Google Maps, and web scraping"""
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
            
            # Get Companies House data - search by name if no number provided
            if company_number:
                print(f"[CH] Getting company profile for number: {company_number}")
                companies_house_data = await self.companies_house_service.get_company_profile(company_number)
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
                            companies_house_data = await self.companies_house_service.get_company_profile(company_number)
                else:
                    print(f"[CH] Search failed or returned no results: {search_result.get('error', 'No companies found')}")
            
            # Get Google Maps data for company locations
            google_maps_data = await self.google_maps_service.search_company_locations(company_name)
            
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
    
    async def _perform_ai_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform AI analysis on company data"""
        if not self.openai_client:
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
            
            # V1 comprehensive prompt
            prompt = f"""
            Analyze this company and provide comprehensive business intelligence:
            
            {company_info}

            Please provide a detailed analysis including:

            1. **Business Sector Classification**: Choose the most appropriate sector from: office, retail, industrial, healthcare, education, hospitality, manufacturing, technology, finance, government, other

            2. **Company Size Assessment**: Use the Companies House financial data to provide accurate estimates:
               - Number of employees (use the employee estimates from Companies House data if available)
               - Revenue range (use actual turnover data from Companies House if available, otherwise estimate)
               - Business size category (Small, Medium, Large, Enterprise)

            3. **Primary Business Activities**: Describe what this company does, their main products/services

            4. **Technology Maturity**: Assess their likely technology sophistication based on company size and financial data:
               - Basic: Simple IT needs, basic infrastructure
               - Intermediate: Some advanced systems, growing IT requirements
               - Advanced: Sophisticated IT infrastructure, multiple systems
               - Enterprise: Complex, integrated systems, dedicated IT teams

            5. **IT Budget Estimate**: Based on their revenue and company size, estimate their likely annual IT spending range

            6. **Financial Health Analysis**: Analyze the financial data from Companies House:
               - Comment on their profitability trend (Growing/Stable/Declining)
               - Assess their financial stability based on shareholders' funds and cash position
               - Evaluate revenue growth trends
               - Identify any financial risks or opportunities

            7. **Growth Potential**: Assess potential for business growth and expansion based on financial trends and company size

            8. **Technology Needs Prediction**: What structured cabling, networking, and security needs might they have based on their size and financial position?

            9. **Competitive Landscape**: Identify potential competitors or similar companies

            10. **Business Opportunities**: What opportunities exist for IT infrastructure projects given their financial capacity and growth trajectory?

            11. **Risk Factors**: What challenges or risks might affect their IT projects based on their financial position?

            12. **Address and Location Analysis**: Based on the company information, identify:
                - Primary business address (if different from registered address)
                - ALL additional sites/locations mentioned
                - Geographic spread of operations

            Please respond in JSON format with these exact fields:
            {{
                "business_sector": "string (one of the sectors listed above)",
                "estimated_employees": number,
                "estimated_revenue": "string (revenue range)",
                "business_size_category": "string (Small/Medium/Large/Enterprise)",
                "primary_business_activities": "string (detailed description)",
                "technology_maturity": "string (Basic/Intermediate/Advanced/Enterprise)",
                "it_budget_estimate": "string (budget range)",
                "growth_potential": "string (High/Medium/Low)",
                "technology_needs": "string (predicted IT needs)",
                "competitors": "string (competitor analysis)",
                "opportunities": "string (business opportunities)",
                "risks": "string (risk factors)",
                "company_profile": "string (comprehensive company summary)",
                "primary_address": "string (main business address if different from registered)",
                "additional_sites": "string (list of additional locations/sites)",
                "location_analysis": "string (geographic spread and location requirements)",
                "financial_health_analysis": "string (detailed analysis of financial position, profitability trends, and stability)",
                "employee_analysis": "string (analysis of employee count and company size based on Companies House data)",
                "revenue_analysis": "string (analysis of turnover trends and revenue growth)",
                "profitability_assessment": "string (assessment of profitability trends and financial performance)"
            }}

            Focus on UK market context and be realistic in your assessments.
            """
            
            system_prompt = """You are a business intelligence analyst specializing in UK companies and IT infrastructure needs. Provide accurate, realistic assessments based on company information. Always respond with valid JSON format."""
            
            print(f"[AI] Making GPT-5-mini API call for customer analysis...")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=16000,
                timeout=180.0
            )
            
            print(f"[AI] GPT-5-mini API call successful, processing response...")
            result_text = response.choices[0].message.content
            
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
            
            # Calculate lead score based on AI analysis
            analysis['lead_score'] = self._calculate_lead_score(analysis)
            
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parsing error: {e}")
            return {"error": f"AI returned invalid JSON: {str(e)}"}
        except Exception as e:
            print(f"[ERROR] Error in AI analysis: {e}")
            return {"error": str(e)}
    
    async def analyze_financial_data(self, company_number: str) -> Dict[str, Any]:
        """Analyze financial data from Companies House"""
        try:
            financial_data = await self.companies_house_service.get_financial_data(company_number)
            
            if not financial_data:
                return {"error": "No financial data available"}
            
            # AI analysis of financial health
            if self.openai_client:
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
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_completion_tokens=2000
            )
            
            ai_response = response.choices[0].message.content
            
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
        if not self.openai_client:
            return {"error": "AI service not available"}
        
        try:
            system_prompt = """You are a sales strategist specializing in structured cabling and IT infrastructure sales.
            
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
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_completion_tokens=2000
            )
            
            ai_response = response.choices[0].message.content
            
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
        if not self.openai_client:
            return {"error": "AI service not available"}
        
        try:
            system_prompt = """You are a lead scoring expert for structured cabling sales.
            
            Score leads based on:
            1. Company size and growth
            2. Industry fit
            3. Financial stability
            4. IT infrastructure needs
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
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_completion_tokens=1500
            )
            
            ai_response = response.choices[0].message.content
            
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
            
            # Growth potential scoring
            growth_potential = str(analysis.get('growth_potential', '')).lower()
            if growth_potential == 'high':
                score += 15
            elif growth_potential == 'medium':
                score += 8
            
            # IT budget scoring (rough estimate)
            it_budget = str(analysis.get('it_budget_estimate', '')).lower()
            if '50k' in it_budget or '100k' in it_budget or '1m' in it_budget:
                score += 10
            elif '10k' in it_budget or '25k' in it_budget:
                score += 5
            
            return min(100, max(0, score))
            
        except Exception as e:
            print(f"[ERROR] Error calculating lead score: {e}")
            return 50

