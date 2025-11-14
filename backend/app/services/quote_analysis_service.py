#!/usr/bin/env python3
"""
Quote Analysis Service for AI-powered quote requirements analysis
Migrated from v1 AIHelper.analyze_quote_requirements()
"""

import json
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import httpx

from app.models.quotes import Quote
from app.models.ai_prompt import PromptCategory
from app.services.ai_prompt_service import AIPromptService
from app.services.google_maps_service import GoogleMapsService
from app.core.api_keys import get_api_keys
from app.models.tenant import Tenant


class QuoteAnalysisService:
    """Service for AI-powered quote requirements analysis"""
    
    def __init__(self, db: Session, tenant_id: str, openai_api_key: Optional[str] = None):
        self.db = db
        self.tenant_id = tenant_id
        self.openai_api_key = openai_api_key
        
        # Resolve API keys if not provided
        if not self.openai_api_key:
            tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if tenant:
                api_keys = get_api_keys(self.db, tenant)
                self.openai_api_key = api_keys.openai
    
    async def analyze_requirements(
        self,
        quote_data: Dict[str, Any],
        clarification_answers: Optional[List[Dict[str, str]]] = None,
        questions_only: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze quote requirements using AI
        
        Args:
            quote_data: Quote data dictionary with project details
            clarification_answers: Optional list of {question, answer} dicts
            questions_only: If True, only return clarification questions
        
        Returns:
            Analysis result with recommended products, labour breakdown, etc.
        """
        try:
            # Get prompt from database
            prompt_service = AIPromptService(self.db, tenant_id=self.tenant_id)
            prompt_obj = await prompt_service.get_prompt(
                category=PromptCategory.QUOTE_ANALYSIS.value,
                tenant_id=self.tenant_id
            )
            
            # Build quote context for prompt
            quote_context = self._build_quote_context(quote_data, clarification_answers)
            
            # Fallback to hardcoded prompt if database prompt not found
            if not prompt_obj:
                print("[QUOTE ANALYSIS] Using fallback prompt - database prompt not found")
                user_prompt = self._build_fallback_prompt(quote_context, questions_only)
                system_prompt = """You are a seasoned structured cabling contractor and estimator. You produce practical, buildable quotations, highlight assumptions, and make sensible allowances for labour and materials."""
                model = "gpt-5-mini"
                max_tokens = 8000
            else:
                # Render prompt with variables
                rendered = prompt_service.render_prompt(prompt_obj, {
                    "quote_context": quote_context,
                    "questions_only": str(questions_only).lower()
                })
                user_prompt = rendered['user_prompt']
                system_prompt = rendered['system_prompt']
                model = rendered['model']
                max_tokens = rendered['max_tokens']
            
            # Call OpenAI API
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_completion_tokens": max_tokens,
                        "temperature": 0.7
                    }
                )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"OpenAI API error: {response.status_code}",
                    "response": response.text
                }
            
            result = response.json()
            ai_response_text = result['choices'][0]['message']['content']
            
            # Parse response
            if questions_only:
                # Extract clarification questions
                clarifications = self._extract_clarification_questions(ai_response_text)
                return {
                    "success": True,
                    "clarifications": clarifications
                }
            else:
                # Parse full analysis
                analysis = self._parse_analysis_response(ai_response_text, quote_data)
                
                # Calculate travel costs if site address provided
                if quote_data.get('site_address'):
                    travel_info = await self._calculate_travel_costs(quote_data['site_address'])
                    if travel_info:
                        analysis.update(travel_info)
                
                return {
                    "success": True,
                    "analysis": analysis,
                    "raw_response": ai_response_text
                }
        
        except Exception as e:
            print(f"[QUOTE ANALYSIS] Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_quote_context(
        self,
        quote_data: Dict[str, Any],
        clarification_answers: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Build quote context string for prompt"""
        context_parts = []
        
        context_parts.append(f"Project Title: {quote_data.get('project_title', 'N/A')}")
        context_parts.append(f"Description: {quote_data.get('project_description', 'N/A')}")
        context_parts.append(f"Site Address: {quote_data.get('site_address', 'N/A')}")
        context_parts.append(f"Building Type: {quote_data.get('building_type', 'N/A')}")
        context_parts.append(f"Building Size: {quote_data.get('building_size', 0)} sqm")
        context_parts.append(f"Number of Floors: {quote_data.get('number_of_floors', 1)}")
        context_parts.append(f"Number of Rooms/Areas: {quote_data.get('number_of_rooms', 1)}")
        
        # Requirements
        context_parts.append(f"\nSolution Requirements:")
        context_parts.append(f"- WiFi installation needed: {quote_data.get('wifi_requirements', False)}")
        context_parts.append(f"- CCTV installation needed: {quote_data.get('cctv_requirements', False)}")
        context_parts.append(f"- Door entry installation needed: {quote_data.get('door_entry_requirements', False)}")
        context_parts.append(f"- Cabling Type: {quote_data.get('cabling_type', 'Not specified')}")
        context_parts.append(f"- Special requirements: {quote_data.get('special_requirements', 'None')}")
        
        # Add clarification answers if provided
        if clarification_answers:
            context_parts.append(f"\nClarification Answers:")
            for qa in clarification_answers:
                context_parts.append(f"Q: {qa.get('question', '')}")
                context_parts.append(f"A: {qa.get('answer', '')}")
        
        return "\n".join(context_parts)
    
    def _build_fallback_prompt(self, quote_context: str, questions_only: bool) -> str:
        """Build fallback prompt if database prompt not available"""
        if questions_only:
            return f"""You are a structured cabling contractor. The client has supplied the information below.

{quote_context}

Review the information and identify any gaps or ambiguities that need clarification before creating an accurate quote.

Return ONLY a JSON array of clarification questions, each with:
- question: The question to ask
- why_needed: Why this information is needed

Example format:
[
  {{"question": "What is the ceiling height?", "why_needed": "Needed to determine cable routing method"}},
  {{"question": "Are there any access restrictions?", "why_needed": "Affects installation time and method"}}
]"""
        else:
            return f"""You are a structured cabling contractor. The client has supplied the information below.

{quote_context}

Analyze the requirements and provide:
1. Recommended products/materials with quantities
2. Labour breakdown with time estimates
3. Estimated total time and cost
4. Any assumptions or clarifications needed

Return in JSON format with:
- recommended_products: Array of {{name, quantity, unit, unit_price, total_price, category}}
- labour_breakdown: Array of {{task, hours, days, day_rate, cost}}
- estimated_time: Total hours
- estimated_cost: Total estimated cost
- assumptions: Array of assumptions made
- clarifications: Array of clarification questions if needed"""
    
    def _extract_clarification_questions(self, response_text: str) -> List[Dict[str, str]]:
        """Extract clarification questions from AI response"""
        try:
            # Try to parse as JSON
            if response_text.strip().startswith('[') or response_text.strip().startswith('{'):
                data = json.loads(response_text)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'questions' in data:
                    return data['questions']
        except:
            pass
        
        # Fallback: extract questions from text
        questions = []
        lines = response_text.split('\n')
        for line in lines:
            if '?' in line and ('question' in line.lower() or line.strip().startswith('-')):
                questions.append({"question": line.strip().lstrip('- '), "why_needed": ""})
        
        return questions
    
    def _parse_analysis_response(self, response_text: str, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI analysis response"""
        try:
            # Try to parse as JSON
            if response_text.strip().startswith('{'):
                data = json.loads(response_text)
                return data
        except json.JSONDecodeError:
            pass
        
        # Fallback: basic parsing
        return {
            "raw_analysis": response_text,
            "recommended_products": [],
            "labour_breakdown": [],
            "estimated_time": None,
            "estimated_cost": None
        }
    
    async def _calculate_travel_costs(self, site_address: str) -> Optional[Dict[str, Any]]:
        """Calculate travel costs using Google Maps API"""
        try:
            # Get tenant for API keys
            tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
            if not tenant:
                return None
            
            api_keys = get_api_keys(self.db, tenant)
            if not api_keys.google_maps:
                return None
            
            # Get office address from tenant settings
            # TODO: Get from tenant.settings or admin settings
            office_address = None  # Would come from tenant configuration
            
            if not office_address:
                return None
            
            # Use Google Maps service to calculate distance/time
            maps_service = GoogleMapsService(api_key=api_keys.google_maps)
            distance_data = await maps_service.calculate_distance(office_address, site_address)
            
            if distance_data and not distance_data.get('error'):
                distance_m = distance_data.get('distance', {}).get('value', 0)
                duration_s = distance_data.get('duration', {}).get('value', 0)
                
                distance_km = distance_m / 1000.0
                duration_minutes = duration_s / 60.0
                
                # Calculate travel cost (example: £0.50 per km)
                travel_cost = distance_km * 0.50  # Configurable rate
                
                return {
                    "travel_distance_km": round(distance_km, 2),
                    "travel_time_minutes": round(duration_minutes, 1),
                    "travel_cost": round(travel_cost, 2)
                }
        
        except Exception as e:
            print(f"[QUOTE ANALYSIS] Error calculating travel costs: {e}")
        
        return None

