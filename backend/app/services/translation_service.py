#!/usr/bin/env python3
"""
AI-powered translation service for multilingual support
"""

import json
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.services.ai_prompt_service import AIPromptService
from app.services.ai_provider_service import AIProviderService
from app.models.ai_prompt import PromptCategory


class TranslationService:
    """Service for AI-powered translation"""
    
    def __init__(self, db: Optional[Session] = None, tenant_id: Optional[str] = None):
        self.db = db
        self.tenant_id = tenant_id
        self.provider_service = AIProviderService(db, tenant_id=tenant_id) if db else None
    
    async def translate(self, text: str, target_language: str, source_language: str = "en") -> Dict[str, str]:
        """Translate text using AI provider"""
        if not self.provider_service or not self.db:
            return {'success': False, 'error': 'Translation service not available'}
        
        try:
            # Get prompt from database
            prompt_service = AIPromptService(self.db, tenant_id=self.tenant_id)
            prompt_obj = await prompt_service.get_prompt(
                category=PromptCategory.TRANSLATION.value,
                tenant_id=self.tenant_id
            )
            
            if prompt_obj:
                # Use database prompt with AIProviderService
                provider_response = await self.provider_service.generate(
                    prompt=prompt_obj,
                    variables={
                        "source_language": source_language,
                        "target_language": target_language,
                        "text": text
                    }
                )
                translated_text = provider_response.content.strip()
            else:
                # Fallback: use generate_with_rendered_prompts
                system_prompt = "You are a professional translator. Translate accurately and naturally."
                user_prompt = f"""Translate the following text from {source_language} to {target_language}.
Return ONLY the translated text, no explanations.

Text to translate:
{text}"""
                
                provider_response = await self.provider_service.generate_with_rendered_prompts(
                    prompt=None,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=2000
                )
                translated_text = provider_response.content.strip()
            
            return {
                'success': True,
                'translated_text': translated_text,
                'source_language': source_language,
                'target_language': target_language
            }
            
        except Exception as e:
            print(f"[TRANSLATION] Error: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    async def detect_language(self, text: str) -> Dict[str, str]:
        """Detect language of text"""
        if not self.provider_service or not self.db:
            return {'success': False, 'error': 'Translation service not available'}
        
        try:
            system_prompt = "You are a language detection expert. Return ONLY the ISO 639-1 language code (e.g., 'en', 'es', 'fr')."
            user_prompt = f"What language is this text in?\n\n{text[:500]}"
            
            provider_response = await self.provider_service.generate_with_rendered_prompts(
                prompt=None,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=10
            )
            
            language_code = provider_response.content.strip().lower()
            
            return {
                'success': True,
                'language': language_code
            }
            
        except Exception as e:
            print(f"[TRANSLATION] Language detection error: {e}")
            return {'success': False, 'error': str(e)}








