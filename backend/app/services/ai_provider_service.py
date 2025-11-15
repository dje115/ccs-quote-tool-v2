#!/usr/bin/env python3
"""
Unified AI Provider Service
Provides a single interface for all AI provider calls with automatic provider resolution
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.core.ai_providers import (
    AIProvider, AIProviderResponse, create_provider,
    OpenAIProvider, GoogleProvider, AnthropicProvider,
    OllamaProvider, OpenAICompatibleProvider
)
from app.models.ai_provider import AIProvider as AIProviderModel, ProviderAPIKey
from app.models.ai_prompt import AIPrompt
from app.models.tenant import Tenant


class AIProviderService:
    """Unified service for AI provider calls"""
    
    def __init__(self, db: Session, tenant_id: Optional[str] = None):
        self.db = db
        self.tenant_id = tenant_id
        self._provider_cache: Dict[str, AIProvider] = {}
    
    def _get_provider_api_key(self, provider_id: str, tenant_id: Optional[str] = None) -> Optional[str]:
        """
        Get API key for a provider with fallback logic:
        1. Check tenant-specific key
        2. Check system-level key (tenant_id=None)
        3. Return None if not found
        """
        try:
            # Try tenant-specific key first
            if tenant_id:
                tenant_key = self.db.query(ProviderAPIKey).filter(
                    ProviderAPIKey.provider_id == provider_id,
                    ProviderAPIKey.tenant_id == tenant_id,
                    ProviderAPIKey.is_valid == True
                ).first()
                
                if tenant_key:
                    return tenant_key.api_key
            
            # Fallback to system-level key
            system_key = self.db.query(ProviderAPIKey).filter(
                ProviderAPIKey.provider_id == provider_id,
                ProviderAPIKey.tenant_id.is_(None),
                ProviderAPIKey.is_valid == True
            ).first()
            
            if system_key:
                return system_key.api_key
            
            return None
        
        except Exception as e:
            print(f"[AIProviderService] Error getting API key: {e}")
            return None
    
    def _get_system_default_provider(self) -> Optional[AIProviderModel]:
        """Get the system default provider (first active provider, or OpenAI if available)"""
        try:
            # Try to get OpenAI first (most common)
            openai_provider = self.db.query(AIProviderModel).filter(
                AIProviderModel.slug == "openai",
                AIProviderModel.is_active == True
            ).first()
            
            if openai_provider:
                return openai_provider
            
            # Otherwise, get first active provider
            provider = self.db.query(AIProviderModel).filter(
                AIProviderModel.is_active == True
            ).first()
            
            return provider
        
        except Exception as e:
            print(f"[AIProviderService] Error getting system default provider: {e}")
            return None
    
    def _resolve_provider_for_prompt(self, prompt: AIPrompt) -> Optional[AIProviderModel]:
        """
        Resolve which provider to use for a prompt:
        1. If use_system_default=False and provider_id is set, use that provider
        2. Otherwise, use system default provider
        """
        try:
            # If prompt has specific provider and not using system default
            if not prompt.use_system_default and prompt.provider_id:
                provider = self.db.query(AIProviderModel).filter(
                    AIProviderModel.id == prompt.provider_id,
                    AIProviderModel.is_active == True
                ).first()
                
                if provider:
                    return provider
            
            # Use system default
            return self._get_system_default_provider()
        
        except Exception as e:
            print(f"[AIProviderService] Error resolving provider for prompt: {e}")
            return self._get_system_default_provider()
    
    def _get_provider_instance(self, provider: AIProviderModel, api_key: str) -> Optional[AIProvider]:
        """Get or create a provider instance (with caching)"""
        cache_key = f"{provider.slug}_{api_key[:10]}"
        
        if cache_key in self._provider_cache:
            return self._provider_cache[cache_key]
        
        # Create provider instance
        provider_instance = create_provider(
            provider_slug=provider.slug,
            api_key=api_key,
            base_url=provider.base_url
        )
        
        if provider_instance:
            self._provider_cache[cache_key] = provider_instance
        
        return provider_instance
    
    async def generate(
        self,
        prompt: AIPrompt,
        variables: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AIProviderResponse:
        """
        Generate AI completion using the appropriate provider
        
        Args:
            prompt: AIPrompt object with provider configuration
            variables: Template variables for prompt rendering
            **kwargs: Additional provider-specific settings
        
        Returns:
            AIProviderResponse with standardized format
        """
        try:
            # Resolve provider
            provider_model = self._resolve_provider_for_prompt(prompt)
            
            if not provider_model:
                raise Exception("No provider available")
            
            # Get API key with fallback
            api_key = self._get_provider_api_key(provider_model.id, self.tenant_id)
            
            if not api_key:
                raise Exception(f"No API key found for provider {provider_model.name}")
            
            # Get provider instance
            provider_instance = self._get_provider_instance(provider_model, api_key)
            
            if not provider_instance:
                raise Exception(f"Failed to create provider instance for {provider_model.slug}")
            
            # Get model name (use provider_model from prompt, or default from provider)
            model = prompt.provider_model or prompt.model
            if not model:
                # Get first supported model from provider
                supported_models = provider_model.supported_models or []
                if supported_models:
                    model = supported_models[0]
                else:
                    model = provider_instance.get_supported_models()[0] if provider_instance.get_supported_models() else "default"
            
            # Get settings (from prompt.provider_settings or prompt defaults)
            settings = prompt.provider_settings or {}
            temperature = settings.get("temperature", prompt.temperature)
            max_tokens = settings.get("max_tokens", prompt.max_tokens)
            
            # Merge with kwargs
            temperature = kwargs.get("temperature", temperature)
            max_tokens = kwargs.get("max_tokens", max_tokens)
            
            # Render prompts if variables provided
            system_prompt = prompt.system_prompt
            user_prompt = prompt.user_prompt_template
            
            if variables:
                # Simple variable substitution (can be enhanced with Jinja2)
                for key, value in variables.items():
                    user_prompt = user_prompt.replace(f"{{{key}}}", str(value))
                    system_prompt = system_prompt.replace(f"{{{key}}}", str(value))
            
            # Check if we need to use responses API (for OpenAI with web search)
            use_responses_api = kwargs.get("use_responses_api", False)
            tools = kwargs.get("tools", None)
            
            # Generate completion
            response = await provider_instance.generate_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                use_responses_api=use_responses_api,
                tools=tools,
                **{k: v for k, v in kwargs.items() if k not in ["use_responses_api", "tools", "temperature", "max_tokens"]}
            )
            
            return response
        
        except Exception as e:
            print(f"[AIProviderService] Error generating completion: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def test_provider(self, provider_id: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Test a provider connection
        
        Args:
            provider_id: Provider ID to test
            api_key: Optional API key (if not provided, will look up from database)
        
        Returns:
            Dict with success status and message/error
        """
        try:
            # Get provider model
            provider_model = self.db.query(AIProviderModel).filter(
                AIProviderModel.id == provider_id,
                AIProviderModel.is_active == True
            ).first()
            
            if not provider_model:
                return {"success": False, "error": "Provider not found"}
            
            # Get API key if not provided
            if not api_key:
                api_key = self._get_provider_api_key(provider_id, self.tenant_id)
            
            if not api_key:
                return {"success": False, "error": "No API key found"}
            
            # Create provider instance
            provider_instance = self._get_provider_instance(provider_model, api_key)
            
            if not provider_instance:
                return {"success": False, "error": "Failed to create provider instance"}
            
            # Test connection
            result = await provider_instance.test_connection()
            
            return result
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def generate_with_rendered_prompts(
        self,
        prompt: AIPrompt,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> AIProviderResponse:
        """
        Generate AI completion using pre-rendered prompts
        
        This method is useful when you need to add additional context
        to the prompts after initial rendering (e.g., adding pricing data,
        consistency context, etc.)
        
        Args:
            prompt: AIPrompt object (for provider configuration)
            system_prompt: Pre-rendered system prompt
            user_prompt: Pre-rendered user prompt
            **kwargs: Additional provider-specific settings
        
        Returns:
            AIProviderResponse with standardized format
        """
        try:
            # Resolve provider
            provider_model = self._resolve_provider_for_prompt(prompt)
            
            if not provider_model:
                raise Exception("No provider available")
            
            # Get API key with fallback
            api_key = self._get_provider_api_key(provider_model.id, self.tenant_id)
            
            if not api_key:
                raise Exception(f"No API key found for provider {provider_model.name}")
            
            # Get provider instance
            provider_instance = self._get_provider_instance(provider_model, api_key)
            
            if not provider_instance:
                raise Exception(f"Failed to create provider instance for {provider_model.slug}")
            
            # Get model name
            model = prompt.provider_model or prompt.model
            if not model:
                supported_models = provider_model.supported_models or []
                if supported_models:
                    model = supported_models[0]
                else:
                    model = provider_instance.get_supported_models()[0] if provider_instance.get_supported_models() else "default"
            
            # Get settings
            settings = prompt.provider_settings or {}
            temperature = kwargs.get("temperature", settings.get("temperature", prompt.temperature))
            max_tokens = kwargs.get("max_tokens", settings.get("max_tokens", prompt.max_tokens))
            
            # Check if we need to use responses API (for OpenAI with web search)
            use_responses_api = kwargs.get("use_responses_api", False)
            tools = kwargs.get("tools", None)
            
            # Generate completion with pre-rendered prompts
            response = await provider_instance.generate_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                use_responses_api=use_responses_api,
                tools=tools,
                **{k: v for k, v in kwargs.items() if k not in ["use_responses_api", "tools", "temperature", "max_tokens"]}
            )
            
            return response
        
        except Exception as e:
            print(f"[AIProviderService] Error generating completion: {e}")
            import traceback
            traceback.print_exc()
            raise

