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
from app.models.supplier import Supplier, SupplierCategory
from app.services.ai_prompt_service import AIPromptService
from app.services.ai_provider_service import AIProviderService
from app.services.google_maps_service import GoogleMapsService
from app.services.quote_consistency_service import QuoteConsistencyService
from app.models.tenant import Tenant


class QuoteAnalysisService:
    """Service for AI-powered quote requirements analysis"""
    
    def __init__(self, db: Session, tenant_id: str, openai_api_key: Optional[str] = None):
        """
        Initialize quote analysis service
        
        Note: openai_api_key parameter is kept for backward compatibility but is no longer used.
        API keys are now resolved through AIProviderService.
        """
        self.db = db
        self.tenant_id = tenant_id
        self.provider_service = AIProviderService(db, tenant_id=tenant_id)
    
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
            # Get prompt from database - use quote_type if provided
            quote_type = quote_data.get('quote_type')
            prompt_service = AIPromptService(self.db, tenant_id=self.tenant_id)
            prompt_obj = await prompt_service.get_prompt(
                category=PromptCategory.QUOTE_ANALYSIS.value,
                tenant_id=self.tenant_id,
                quote_type=quote_type
            )
            
            # Build quote context for prompt (with supplier preferences)
            quote_context = self._build_quote_context(quote_data, clarification_answers)
            
            # Add supplier information and consistency context
            supplier_info = self._get_supplier_preferences()
            consistency_context = ""
            real_pricing_reference = ""
            
            if not questions_only:
                # Get consistency context for full analysis
                quote_obj = self.db.query(Quote).filter(
                    Quote.tenant_id == self.tenant_id
                ).first()  # This is a placeholder - in real usage, quote_id would be passed
                if quote_obj:
                    consistency_service = QuoteConsistencyService(self.db, self.tenant_id)
                    consistency_context = consistency_service.get_consistency_context_for_ai(quote_obj)
                
                # Get real pricing data for common products
                real_pricing_reference = self._get_real_pricing_data()
            
            # Build enhanced context with all additions
            enhanced_context = quote_context
            if supplier_info:
                enhanced_context += f"\n\n{supplier_info}"
            if consistency_context:
                enhanced_context += f"\n\n{consistency_context}"
            if real_pricing_reference:
                enhanced_context += f"\n\n**REAL PRICING REFERENCE (Use these exact prices):**\n{real_pricing_reference}"
                enhanced_context += "\n\n**CRITICAL:** Use the exact pricing above. Do not estimate or guess prices. All unit_price and total_price values must be real numbers, not text."
            
            # Get day rate info
            day_rate_info = self._get_day_rate_info()
            if day_rate_info:
                enhanced_context += f"\n\n{day_rate_info}"
            
            quote_context = enhanced_context
            
            # Require database prompt - no fallback hardcoded prompts
            if not prompt_obj:
                print(f"[QUOTE ANALYSIS] ERROR: No prompt found for category {PromptCategory.QUOTE_ANALYSIS.value}, quote_type={quote_type}")
                return {
                    "success": False,
                    "error": f"AI prompt not configured for quote analysis (quote_type: {quote_type or 'general'}). Please configure prompts in the admin section."
                }
            
            # Build variables for prompt rendering (base template variables)
            prompt_variables = {
                "project_title": quote_data.get('project_title', ''),
                "project_description": quote_data.get('project_description', ''),
                "building_type": quote_data.get('building_type', ''),
                "building_size": str(quote_data.get('building_size', 0)),
                "number_of_floors": str(quote_data.get('number_of_floors', 1)),
                "number_of_rooms": str(quote_data.get('number_of_rooms', 1)),
                "site_address": quote_data.get('site_address', ''),
                "wifi_requirements": str(quote_data.get('wifi_requirements', False)),
                "cctv_requirements": str(quote_data.get('cctv_requirements', False)),
                "door_entry_requirements": str(quote_data.get('door_entry_requirements', False)),
                "special_requirements": quote_data.get('special_requirements', '')
            }
            
            # Render base prompt template
            rendered = prompt_service.render_prompt(prompt_obj, prompt_variables)
            user_prompt = rendered['user_prompt']
            system_prompt = rendered['system_prompt']
            model = rendered['model']
            max_tokens = rendered['max_tokens']
            
            # Add additional context (like v1 does) - append to user_prompt
            if real_pricing_reference:
                user_prompt += f"\n\n**REAL PRICING REFERENCE (Use these exact prices):**\n{real_pricing_reference}"
                user_prompt += "\n\n**CRITICAL:** Use the exact pricing above. Do not estimate or guess prices. All unit_price and total_price values must be real numbers, not text."
            if consistency_context:
                user_prompt += f"\n\n{consistency_context}"
            if supplier_info:
                user_prompt += f"\n\n{supplier_info}"
            day_rate_info = self._get_day_rate_info()
            if day_rate_info:
                user_prompt += f"\n\n{day_rate_info}"
            
            # Add clarification answers if provided
            if clarification_answers:
                clarification_lines = []
                for idx, item in enumerate(clarification_answers, start=1):
                    question = item.get('question', '')
                    answer = item.get('answer', '')
                    clarification_lines.append(f"{idx}. Question: {question}\n   Answer: {answer if answer else 'Not provided'}")
                if clarification_lines:
                    user_prompt += "\n\nClarification Responses:\n" + "\n".join(clarification_lines)
            
            # Use AIProviderService to generate completion
            try:
                provider_response = await self.provider_service.generate(
                    prompt=prompt_obj,
                    variables=prompt_variables,
                    temperature=rendered.get('temperature', 0.7),
                    max_tokens=max_tokens
                )
                
                ai_response_text = provider_response.content
                
            except Exception as e:
                print(f"[QUOTE ANALYSIS] Error calling AI provider: {e}")
                import traceback
                traceback.print_exc()
                return {
                    "success": False,
                    "error": f"AI provider error: {str(e)}"
                }
            
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
    
    def _get_supplier_preferences(self) -> str:
        """Get supplier preferences information for AI prompts"""
        try:
            from app.models.supplier import Supplier, SupplierCategory
            
            suppliers_info = []
            categories = self.db.query(SupplierCategory).filter(
                SupplierCategory.tenant_id == self.tenant_id,
                SupplierCategory.is_active == True
            ).all()
            
            for category in categories:
                preferred_suppliers = self.db.query(Supplier).filter(
                    Supplier.tenant_id == self.tenant_id,
                    Supplier.category_id == category.id,
                    Supplier.is_preferred == True,
                    Supplier.is_active == True
                ).all()
                
                if preferred_suppliers:
                    suppliers_info.append(f"\n**{category.name} Suppliers:**")
                    for supplier in preferred_suppliers:
                        supplier_line = f"- {supplier.name}"
                        if supplier.website:
                            supplier_line += f" ({supplier.website})"
                        if supplier.notes:
                            supplier_line += f" - {supplier.notes}"
                        suppliers_info.append(supplier_line)
            
            if suppliers_info:
                return f"\n\n**Preferred Suppliers for Pricing Reference:**{''.join(suppliers_info)}\n\nWhen recommending products, prioritize these suppliers and try to get accurate pricing from their websites when possible."
            
            return ""
            
        except Exception as e:
            print(f"[QUOTE ANALYSIS] Error getting supplier preferences: {e}")
            return ""
    
    def _get_real_pricing_data(self) -> str:
        """Get real pricing data from actual suppliers to include in AI prompt"""
        try:
            from app.models.supplier import Supplier, SupplierPricing
            from app.models.product import Product
            
            pricing_lines = []
            
            # Get all active preferred suppliers for this tenant
            preferred_suppliers = self.db.query(Supplier).filter(
                Supplier.tenant_id == self.tenant_id,
                Supplier.is_preferred == True,
                Supplier.is_active == True
            ).all()
            
            # If no preferred suppliers, get all active suppliers
            if not preferred_suppliers:
                preferred_suppliers = self.db.query(Supplier).filter(
                    Supplier.tenant_id == self.tenant_id,
                    Supplier.is_active == True
                ).limit(5).all()  # Limit to 5 suppliers to avoid too much data
            
            for supplier in preferred_suppliers:
                supplier_products = []
                
                # Get products from products table linked to this supplier
                products = self.db.query(Product).filter(
                    Product.supplier_id == supplier.id,
                    Product.tenant_id == self.tenant_id,
                    Product.is_active == True
                ).limit(20).all()  # Limit to 20 products per supplier
                
                for product in products:
                    if product.base_price:
                        supplier_products.append({
                            'name': product.name,
                            'price': float(product.base_price),
                            'code': product.code or product.part_number,
                            'source': 'products_table'
                        })
                
                # Get cached pricing for this supplier
                cached_pricing = self.db.query(SupplierPricing).filter(
                    SupplierPricing.supplier_id == supplier.id,
                    SupplierPricing.is_active == True
                ).order_by(SupplierPricing.last_updated.desc()).limit(20).all()
                
                for pricing in cached_pricing:
                    # Avoid duplicates
                    if not any(p['name'].lower() == pricing.product_name.lower() for p in supplier_products):
                        supplier_products.append({
                            'name': pricing.product_name,
                            'price': float(pricing.price),
                            'code': pricing.product_code,
                            'source': 'cached_pricing'
                        })
                
                # Add supplier products to pricing lines
                if supplier_products:
                    pricing_lines.append(f"\n**{supplier.name} Products:**")
                    for product in supplier_products[:15]:  # Limit to 15 products per supplier
                        code_str = f" ({product['code']})" if product.get('code') else ""
                        pricing_lines.append(f"- {product['name']}{code_str}: £{product['price']:.2f}")
            
            if pricing_lines:
                return "\n".join(pricing_lines) + "\n\n**IMPORTANT:** Use the exact pricing above when recommending products. These are real prices from your configured suppliers."
            
            return ""
            
        except Exception as e:
            print(f"[QUOTE ANALYSIS] Error getting real pricing data: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _get_day_rate_info(self) -> str:
        """Get day rate information for AI prompt"""
        try:
            # Try to get from tenant settings or admin settings
            # For now, return default
            day_rate = 300  # Default day rate
            
            # TODO: Get from tenant settings or admin settings
            # tenant = self.db.query(Tenant).filter(Tenant.id == self.tenant_id).first()
            # if tenant and tenant.settings:
            #     day_rate = tenant.settings.get('day_rate', 300)
            
            return f"**Labour Rate:** £{day_rate} per pair of engineers per day (8-hour day)\n**CRITICAL: £{day_rate} is the TOTAL cost for BOTH engineers working together for one day**"
            
        except Exception as e:
            print(f"[QUOTE ANALYSIS] Error getting day rate info: {e}")
            return ""
    
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

