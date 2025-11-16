#!/usr/bin/env python3
"""
Product Search Service
AI-powered product search migrated from v1
"""

import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import httpx

from app.models.ai_prompt import PromptCategory
from app.services.ai_prompt_service import AIPromptService
from app.services.ai_provider_service import AIProviderService


class ProductSearchService:
    """Service for AI-powered product search"""
    
    def __init__(self, db: Session, tenant_id: str, openai_api_key: Optional[str] = None):
        self.db = db
        self.tenant_id = tenant_id
        self.provider_service = AIProviderService(db, tenant_id=tenant_id)
    
    async def search_products(
        self,
        query: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for products using AI
        
        Args:
            query: Search query
            category: Optional product category filter
        
        Returns:
            List of product recommendations
        """
        try:
            # Get prompt from database
            prompt_service = AIPromptService(self.db, tenant_id=self.tenant_id)
            prompt_obj = await prompt_service.get_prompt(
                category=PromptCategory.PRODUCT_SEARCH.value,
                tenant_id=self.tenant_id
            )
            
            if not prompt_obj:
                return []
            
            # Render prompt with variables
            rendered = prompt_service.render_prompt(prompt_obj, {
                "category": category or "general",
                "query": query
            })
            
            # Use AIProviderService
            provider_response = await self.provider_service.generate(
                prompt=prompt_obj,
                variables={
                    "category": category or "general",
                    "query": query
                }
            )
            
            response_text = provider_response.content
            
            # Try to parse JSON response
            try:
                if '[' in response_text and ']' in response_text:
                    json_start = response_text.find('[')
                    json_end = response_text.rfind(']') + 1
                    json_text = response_text[json_start:json_end]
                    return json.loads(json_text)
                elif '{' in response_text:
                    # Single object, wrap in array
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    json_text = response_text[json_start:json_end]
                    product = json.loads(json_text)
                    return [product]
            except json.JSONDecodeError:
                pass
            
            return []
            
        except Exception as e:
            print(f"[PRODUCT SEARCH] Error: {e}")
            import traceback
            traceback.print_exc()
            return []


