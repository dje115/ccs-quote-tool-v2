#!/usr/bin/env python3
"""
Quote AI Generation Service

AI-powered quote generation that:
- Auto-detects industry from tenant context
- Generates 1-tier or 3-tier quotes
- Uses tenant's services, day rates, and suppliers
- Creates all 4 document types (parts list, technical, overview, build)
"""

import logging
import json
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.tenant import Tenant
from app.models.supplier import Supplier, SupplierPricing
from app.models.product import Product
from app.services.ai_orchestration_service import AIOrchestrationService
from app.models.ai_prompt import PromptCategory
from app.services.pricing_config_service import PricingConfigService
from app.models.pricing_config import PricingConfigType

logger = logging.getLogger(__name__)


class QuoteAIGenerationService:
    """
    AI-powered quote generation service
    
    Features:
    - Industry auto-detection from tenant context
    - 1-tier or 3-tier quote generation
    - Integration with tenant's services, day rates, suppliers
    - Multi-part document generation
    """
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.orchestration_service = AIOrchestrationService(db, tenant_id=tenant_id)
        self.pricing_service = PricingConfigService(db, tenant_id=tenant_id)
    
    async def generate_quote(
        self,
        customer_request: str,
        required_deadline: Optional[str] = None,
        location: Optional[str] = None,
        quantity: Optional[int] = None,
        user_id: Optional[str] = None,
        custom_prompt_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete quote using AI
        
        Args:
            customer_request: Plain English description of what the client wants
            required_deadline: Required deadline
            location: Project location
            quantity: Quantity if applicable
            user_id: User creating the quote
        
        Returns:
            Dict with generated quote data including all document types
        """
        try:
            # 1. Get tenant context
            tenant_context = await self._get_tenant_context()
            
            # 2. Get service catalogue (day rates, hour rates)
            service_catalogue = await self._get_service_catalogue()
            
            # 3. Get supplier catalogue (pricing)
            supplier_catalogue = await self._get_supplier_catalogue()
            
            # 4. Build variables for AI prompt
            variables = {
                "tenant_context": tenant_context,
                "service_catalogue": json.dumps(service_catalogue, indent=2),
                "supplier_catalogue": json.dumps(supplier_catalogue, indent=2),
                "customer_request": customer_request,
                "required_deadline": required_deadline or "Not specified",
                "location": location or "Not specified",
                "quantity": str(quantity) if quantity else "1"
            }
            
            # 5. Get prompt and render it to capture the actual prompt text
            prompt_obj = await self.orchestration_service._resolve_prompt(
                PromptCategory.QUOTE_GENERATION.value,
                None
            )
            rendered_prompt = self.orchestration_service.prompt_service.render_prompt(prompt_obj, variables)
            actual_prompt_text = custom_prompt_text or rendered_prompt.get('user_prompt', '')
            
            # If custom prompt is provided, use it directly with the AI provider
            if custom_prompt_text:
                # Use custom prompt directly
                from app.services.ai_provider_service import AIProviderService
                provider_service = AIProviderService(self.db, tenant_id=self.tenant_id)
                provider_response = await provider_service.generate_with_rendered_prompts(
                    prompt=prompt_obj,
                    system_prompt=rendered_prompt.get('system_prompt', ''),
                    user_prompt=custom_prompt_text
                )
                response = {
                    "content": provider_response.content,
                    "provider": "openai",  # Default, could be enhanced
                    "model": provider_response.model,
                    "cached": False,
                    "metadata": {
                        "prompt_id": prompt_obj.id,
                        "prompt_version": prompt_obj.version,
                        "category": PromptCategory.QUOTE_GENERATION.value,
                        "tenant_id": self.tenant_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                }
            else:
                logger.info(f"[Quote AI Generation] Calling OpenAI for quote generation - Category: {PromptCategory.QUOTE_GENERATION.value}, Tenant: {self.tenant_id}")
                logger.info(f"[Quote AI Generation] Request details - Customer request length: {len(customer_request)} chars")
                
                response = await self.orchestration_service.generate(
                    category=PromptCategory.QUOTE_GENERATION.value,
                    variables=variables,
                    use_cache=False  # Don't cache quote generation
                )
                
                logger.info(f"[Quote AI Generation] OpenAI response received - Provider: {response.get('provider')}, Model: {response.get('model')}, Cached: {response.get('cached', False)}")
            
            # 7. Parse AI response
            quote_data = self._parse_ai_response(response["content"])
            
            # 8. Add metadata
            quote_data["ai_generation_data"] = {
                "industry_detected": quote_data.get("industry_detected"),
                "prompt_category": PromptCategory.QUOTE_GENERATION.value,
                "generated_at": str(response.get("generated_at")),
                "model_used": response.get("model"),
                "tier_type": quote_data.get("quote_type", "single")
            }
            
            # 9. Store prompt and response metadata for return (will be saved by builder service)
            quote_data["_prompt_metadata"] = {
                "prompt_text": actual_prompt_text,
                "prompt_variables": variables,
                "ai_model": response.get("model"),
                "ai_provider": response.get("provider"),
                "temperature": rendered_prompt.get("temperature"),
                "max_tokens": rendered_prompt.get("max_tokens"),
                "generation_successful": True,
                "generated_quote_data": quote_data
            }
            
            return {
                "success": True,
                "quote_data": quote_data
            }
        
        except Exception as e:
            logger.error(f"Error generating quote: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_tenant_context(self) -> str:
        """Get tenant context for AI prompt"""
        tenant = self.db.query(Tenant).filter(
            Tenant.id == self.tenant_id
        ).first()
        
        if not tenant:
            raise ValueError(f"Tenant not found: {self.tenant_id}")
        
        context_parts = []
        
        # Company name
        if tenant.name:
            context_parts.append(f"Company Name: {tenant.name}")
        
        # Company description
        if tenant.company_description:
            context_parts.append(f"Description: {tenant.company_description}")
        
        # Products and services
        if tenant.products_services:
            services = tenant.products_services
            if isinstance(services, list):
                context_parts.append(f"Products/Services: {', '.join(services)}")
            elif isinstance(services, str):
                context_parts.append(f"Products/Services: {services}")
        
        # Unique selling points
        if tenant.unique_selling_points:
            usps = tenant.unique_selling_points
            if isinstance(usps, list):
                context_parts.append(f"Unique Selling Points: {', '.join(usps)}")
            elif isinstance(usps, str):
                context_parts.append(f"Unique Selling Points: {usps}")
        
        # Target markets
        if tenant.target_markets:
            markets = tenant.target_markets
            if isinstance(markets, list):
                context_parts.append(f"Target Markets: {', '.join(markets)}")
            elif isinstance(markets, str):
                context_parts.append(f"Target Markets: {markets}")
        
        # Brand voice (if available)
        brand_voice = getattr(tenant, 'brand_voice', None)
        if brand_voice:
            context_parts.append(f"Brand Voice: {brand_voice}")
        
        return "\n".join(context_parts) if context_parts else "No company profile information available."
    
    async def _get_service_catalogue(self) -> List[Dict[str, Any]]:
        """Get service catalogue with day rates and hour rates"""
        catalogue = []
        
        try:
            # Get day rate configurations
            day_rates = self.pricing_service.list_configs(
                config_type=PricingConfigType.DAY_RATE.value,
                include_inactive=False
            )
            
            for config in day_rates:
                config_data = config.config_data or {}
                hours_per_day = config_data.get("hours_per_day", 8)
                day_rate = float(config.base_rate or 0)
                hour_rate = day_rate / hours_per_day if hours_per_day > 0 else 0
                
                catalogue.append({
                    "service": config.name,
                    "internal_code": config.code or config.name.upper().replace(" ", "_"),
                    "day_rate": day_rate,
                    "hour_rate": hour_rate,
                    "hours_per_day": hours_per_day,
                    "engineers": config_data.get("engineers", 1),
                    "includes_travel": config_data.get("includes_travel", False),
                    "engineer_grades": config_data.get("engineer_grades", ["standard"])
                })
            
            # Get hourly rate configurations
            hourly_rates = self.pricing_service.list_configs(
                config_type=PricingConfigType.HOURLY_RATE.value,
                include_inactive=False
            )
            
            for config in hourly_rates:
                hour_rate = float(config.base_rate or 0)
                day_rate = hour_rate * 8  # Estimate day rate from hourly
                
                catalogue.append({
                    "service": config.name,
                    "internal_code": config.code or config.name.upper().replace(" ", "_"),
                    "day_rate": day_rate,
                    "hour_rate": hour_rate,
                    "hours_per_day": 1,  # Hourly rate
                    "engineers": 1,
                    "includes_travel": False,
                    "engineer_grades": ["standard"]
                })
            
        except Exception as e:
            logger.warning(f"Error getting service catalogue: {e}")
        
        return catalogue
    
    async def _get_supplier_catalogue(self) -> List[Dict[str, Any]]:
        """Get supplier catalogue with pricing"""
        catalogue = []
        
        try:
            # Get all active suppliers for tenant
            suppliers = self.db.query(Supplier).filter(
                Supplier.tenant_id == self.tenant_id,
                Supplier.is_active == True
            ).all()
            
            for supplier in suppliers:
                # Get pricing items for this supplier
                pricing_items = self.db.query(SupplierPricing).filter(
                    SupplierPricing.supplier_id == supplier.id,
                    SupplierPricing.is_active == True,
                    SupplierPricing.verification_status == "verified"  # Only verified pricing
                ).limit(100).all()  # Limit to prevent huge catalogues
                
                for item in pricing_items:
                    catalogue.append({
                        "supplier": supplier.name,
                        "item": item.product_name,
                        "product_code": item.product_code or "",
                        "cost_price": float(item.price),
                        "sell_price": float(item.price * 1.2)  # 20% markup default
                    })
        
        except Exception as e:
            logger.warning(f"Error getting supplier catalogue: {e}")
        
        return catalogue
    
    def _parse_ai_response(self, content: str) -> Dict[str, Any]:
        """Parse AI response JSON into structured quote data"""
        try:
            # Try to parse as JSON
            if isinstance(content, str):
                # Remove markdown code blocks if present
                if content.strip().startswith("```"):
                    # Extract JSON from code block
                    lines = content.strip().split("\n")
                    json_start = None
                    json_end = None
                    for i, line in enumerate(lines):
                        if line.strip().startswith("```json") or line.strip().startswith("```"):
                            json_start = i + 1
                        elif line.strip() == "```" and json_start is not None:
                            json_end = i
                            break
                    
                    if json_start is not None and json_end is not None:
                        content = "\n".join(lines[json_start:json_end])
                    else:
                        # Try to find JSON object
                        import re
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            content = json_match.group(0)
                
                quote_data = json.loads(content)
            else:
                quote_data = content
            
            # Ensure required fields exist
            if "quote_type" not in quote_data:
                quote_data["quote_type"] = "single"
            
            if "industry_detected" not in quote_data:
                quote_data["industry_detected"] = "Unknown"
            
            return quote_data
        
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing AI response JSON: {e}")
            logger.error(f"Response content: {content[:500]}")
            # Return basic structure on error
            return {
                "quote_type": "single",
                "industry_detected": "Unknown",
                "executive_summary": content[:500] if content else "Error parsing quote generation",
                "error": "Failed to parse AI response as JSON"
            }
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}", exc_info=True)
            return {
                "quote_type": "single",
                "industry_detected": "Unknown",
                "executive_summary": "Error generating quote",
                "error": str(e)
            }

