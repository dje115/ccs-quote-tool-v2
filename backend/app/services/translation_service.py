#!/usr/bin/env python3
"""
AI-powered translation service for multilingual support
"""

import json
from typing import Dict, Optional
import openai
from app.core.config import settings


class TranslationService:
    """Service for AI-powered translation"""
    
    def __init__(self):
        self.openai_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            if settings.OPENAI_API_KEY:
                self.openai_client = openai.OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    timeout=60
                )
        except Exception as e:
            print(f"[ERROR] Error initializing translation client: {e}")
    
    async def translate(self, text: str, target_language: str, source_language: str = "en") -> Dict[str, str]:
        """Translate text using GPT-5"""
        if not self.openai_client:
            return {'success': False, 'error': 'Translation service not available'}
        
        try:
            prompt = f"""Translate the following text from {source_language} to {target_language}.
Return ONLY the translated text, no explanations.

Text to translate:
{text}"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator. Translate accurately and naturally."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_completion_tokens=2000
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            return {
                'success': True,
                'translated_text': translated_text,
                'source_language': source_language,
                'target_language': target_language
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def detect_language(self, text: str) -> Dict[str, str]:
        """Detect language of text"""
        if not self.openai_client:
            return {'success': False, 'error': 'Translation service not available'}
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a language detection expert. Return ONLY the ISO 639-1 language code (e.g., 'en', 'es', 'fr')."
                    },
                    {
                        "role": "user",
                        "content": f"What language is this text in?\n\n{text[:500]}"
                    }
                ],
                max_completion_tokens=10
            )
            
            language_code = response.choices[0].message.content.strip().lower()
            
            return {
                'success': True,
                'language': language_code
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}



