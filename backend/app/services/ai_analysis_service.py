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


class AIAnalysisService:
    """Service for AI-powered company analysis and lead generation"""
    
    def __init__(self):
        self.openai_client = None
        self.companies_house_service = CompaniesHouseService()
        self.google_maps_service = GoogleMapsService()
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            if settings.OPENAI_API_KEY:
                self.openai_client = OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    timeout=300.0
                )
        except Exception as e:
            print(f"[ERROR] Error initializing AI analysis client: {e}")
    
    async def analyze_company(self, company_name: str, company_number: str = None) -> Dict[str, Any]:
        """Comprehensive company analysis using AI, Companies House, and Google Maps"""
        try:
            # Gather data from multiple sources
            companies_house_data = {}
            google_maps_data = {}
            
            if company_number:
                companies_house_data = await self.companies_house_service.get_company_profile(company_number)
            
            # Get Google Maps data for company locations
            google_maps_data = await self.google_maps_service.search_company_locations(company_name)
            
            # Combine all data for AI analysis
            analysis_data = {
                "company_name": company_name,
                "company_number": company_number,
                "companies_house_data": companies_house_data,
                "google_maps_data": google_maps_data,
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
                    "google_maps": google_maps_data
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
            system_prompt = """You are an expert business analyst specializing in structured cabling, IT infrastructure, and security systems. 
            Your role is to analyze companies and determine their potential as customers for structured cabling services.

            Analyze the provided company data and provide insights on:
            1. Company size and growth potential
            2. Industry and business type
            3. IT infrastructure needs assessment
            4. Lead scoring (1-100)
            5. Recommended approach strategy
            6. Key decision makers
            7. Competitive advantages
            8. Risk factors
            9. Next steps for engagement

            Be specific, actionable, and focus on structured cabling opportunities."""
            
            user_prompt = f"""
            Please analyze this company for structured cabling opportunities:

            Company: {data.get('company_name', 'Unknown')}
            Company Number: {data.get('company_number', 'Not provided')}

            Companies House Data:
            {json.dumps(data.get('companies_house_data', {}), indent=2)}

            Location Data:
            {json.dumps(data.get('google_maps_data', {}), indent=2)}

            Provide a comprehensive analysis in JSON format with these fields:
            - company_overview: Brief company description
            - industry_analysis: Industry type and characteristics
            - size_assessment: Company size (small/medium/large/enterprise)
            - growth_potential: Growth indicators and potential
            - it_needs_assessment: Likely IT infrastructure needs
            - lead_score: Score from 1-100 for lead quality
            - decision_makers: Likely decision makers and contacts
            - competitive_advantages: Our competitive advantages for this prospect
            - risk_factors: Potential risks or challenges
            - recommended_approach: Suggested engagement strategy
            - next_steps: Specific next steps for this lead
            - opportunities: Specific structured cabling opportunities
            - urgency: High/Medium/Low urgency level
            - budget_estimate: Estimated project budget range
            - timeline: Likely project timeline
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_completion_tokens=4000,
                temperature=0.3
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            
            # Try to extract JSON from response
            try:
                # Look for JSON in the response
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = ai_response[start_idx:end_idx]
                    parsed_analysis = json.loads(json_str)
                else:
                    # Fallback to text analysis
                    parsed_analysis = {"raw_analysis": ai_response}
            except json.JSONDecodeError:
                parsed_analysis = {"raw_analysis": ai_response}
            
            return parsed_analysis
            
        except Exception as e:
            return {"error": f"AI analysis failed: {str(e)}"}
    
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
                max_completion_tokens=2000,
                temperature=0.2
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
                max_completion_tokens=2000,
                temperature=0.4
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
                max_completion_tokens=1500,
                temperature=0.2
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
