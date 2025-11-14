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
from app.core.api_keys import get_api_keys
from app.models.tenant import Tenant


class ProductSearchService:
    """Service for AI-powered product search"""
    
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
            
            user_prompt = rendered['user_prompt']
            system_prompt = rendered['system_prompt']
            model = rendered['model']
            max_tokens = rendered['max_tokens']
            
            # Call OpenAI API
            async with httpx.AsyncClient(timeout=60.0) as client:
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
                return []
            
            result = response.json()
            response_text = result['choices'][0]['message']['content']
            
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


