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
    
    @staticmethod
    def normalize_model_parameters(
        model: str,
        provider_slug: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Normalize AI model parameters based on provider and model-specific requirements
        
        This ensures that parameters are adjusted according to each model's capabilities:
        - Some models don't support custom temperature (must use default)
        - Some models have token limits
        - Different providers use different parameter names
        - Temperature ranges are validated per provider
        
        Supported Providers:
        - OpenAI: Handles o1, o3, GPT-5 models (no custom temp), GPT-4/3.5 (token limits)
        - Anthropic: Handles Claude 3/3.5 models (token limits, temp 0.0-1.0)
        - Google: Handles Gemini models (token limits, temp 0.0-2.0)
        - Other: Generic validation (temp 0.0-2.0)
        
        Args:
            model: Model name (e.g., "o1-mini", "gpt-4", "claude-3-opus", "gemini-pro")
            provider_slug: Provider slug (e.g., "openai", "anthropic", "google")
            temperature: Requested temperature value
            max_tokens: Requested max tokens
            **kwargs: Additional parameters
        
        Returns:
            Dict with normalized parameters and flags indicating what was changed
        """
        normalized = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            "skip_temperature": False,
            "changes": []
        }
        
        model_lower = model.lower()
        
        # ===== OPENAI MODELS =====
        if provider_slug == "openai" or provider_slug == "openai_compatible":
            # OpenAI models that don't support custom temperature
            openai_no_temp_models = [
                "o1", "o1-mini", "o1-preview", "o1-2024-09-12",
                "o3", "o3-mini",  # Future-proofing
                "gpt-5-mini", "gpt-5", "gpt-5-turbo"  # GPT-5 models only support default temperature=1
            ]
            
            # Check if model doesn't support custom temperature
            if model_lower in [m.lower() for m in openai_no_temp_models]:
                if temperature != 1.0:
                    normalized["skip_temperature"] = True
                    normalized["changes"].append(f"Model {model} only supports temperature=1, skipping temperature parameter")
            
            # OpenAI o1 models have different token limits
            if model_lower.startswith("o1"):
                # o1 models have a max output of 16,384 tokens
                if max_tokens > 16384:
                    normalized["max_tokens"] = 16384
                    normalized["changes"].append(f"Model {model} max_tokens capped at 16,384")
            
            # OpenAI GPT-4 and GPT-3.5 models typically support up to 16,384 tokens
            elif model_lower.startswith("gpt-4") or model_lower.startswith("gpt-3.5"):
                if max_tokens > 16384:
                    normalized["max_tokens"] = 16384
                    normalized["changes"].append(f"Model {model} max_tokens capped at 16,384")
            
            # Validate temperature range for OpenAI (0.0-2.0)
            if not normalized["skip_temperature"]:
                if temperature < 0.0:
                    normalized["temperature"] = 0.0
                    normalized["changes"].append(f"Temperature clamped to minimum 0.0")
                elif temperature > 2.0:
                    normalized["temperature"] = 2.0
                    normalized["changes"].append(f"Temperature clamped to maximum 2.0")
        
        # ===== ANTHROPIC CLAUDE MODELS =====
        elif provider_slug == "anthropic":
            claude_models = ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku", 
                            "claude-3-5-sonnet", "claude-3-5-opus", "claude-3-5-haiku"]
            
            # Anthropic Claude models have max output token limits
            if any(model_lower.startswith(c.lower()) for c in claude_models):
                # Claude 3.5 models and opus/sonnet have max output of 8,192 tokens
                if "3.5" in model_lower or "opus" in model_lower or "sonnet" in model_lower:
                    max_output = 8192
                else:
                    max_output = 4096  # Claude 3 haiku
                
                if max_tokens > max_output:
                    normalized["max_tokens"] = max_output
                    normalized["changes"].append(f"Model {model} max_tokens capped at {max_output}")
            
            # Validate temperature range for Anthropic (0.0-1.0)
            if temperature < 0.0:
                normalized["temperature"] = 0.0
                normalized["changes"].append(f"Temperature clamped to minimum 0.0")
            elif temperature > 1.0:
                normalized["temperature"] = 1.0
                normalized["changes"].append(f"Temperature clamped to maximum 1.0 (Anthropic limit)")
        
        # ===== GOOGLE GEMINI MODELS =====
        elif provider_slug == "google":
            # Google Gemini models have max_output_tokens limits (handled by provider, but we validate here)
            # Gemini Pro: 8,192 tokens, Gemini 1.5 Pro: 8,192 tokens, Gemini 2.0: up to 32,768 tokens
            if "2.0" in model_lower or "flash-exp" in model_lower:
                max_output = 32768  # Gemini 2.0 supports up to 32K tokens
            elif "1.5" in model_lower:
                max_output = 8192  # Gemini 1.5 models
            else:
                max_output = 8192  # Default for other Gemini models
            
            if max_tokens > max_output:
                normalized["max_tokens"] = max_output
                normalized["changes"].append(f"Model {model} max_tokens capped at {max_output}")
            
            # Validate temperature range for Google (0.0-2.0)
            if temperature < 0.0:
                normalized["temperature"] = 0.0
                normalized["changes"].append(f"Temperature clamped to minimum 0.0")
            elif temperature > 2.0:
                normalized["temperature"] = 2.0
                normalized["changes"].append(f"Temperature clamped to maximum 2.0")
        
        # ===== OTHER PROVIDERS =====
        else:
            # Generic validation for other providers
            # Most providers support temperature 0.0-2.0
            if temperature < 0.0:
                normalized["temperature"] = 0.0
                normalized["changes"].append(f"Temperature clamped to minimum 0.0")
            elif temperature > 2.0:
                normalized["temperature"] = 2.0
                normalized["changes"].append(f"Temperature clamped to maximum 2.0")
        
        # Log changes if any
        if normalized["changes"]:
            print(f"[AIProviderService] Model parameter normalization for {provider_slug}/{model}:")
            for change in normalized["changes"]:
                print(f"  - {change}")
        
        return normalized
    
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
            # Handle max_completion_tokens (OpenAI) vs max_tokens (other providers)
            if "max_completion_tokens" in kwargs:
                max_tokens = kwargs["max_completion_tokens"]
            elif "max_tokens" in kwargs:
                max_tokens = kwargs["max_tokens"]
            
            # Normalize parameters based on model requirements
            # Filter out max_tokens and temperature from kwargs to avoid duplicate arguments
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ['max_tokens', 'temperature', 'max_completion_tokens']}
            normalized = self.normalize_model_parameters(
                model=model,
                provider_slug=provider_model.slug,
                temperature=temperature,
                max_tokens=max_tokens,
                **filtered_kwargs
            )
            temperature = normalized["temperature"]
            max_tokens = normalized["max_tokens"]
            
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
            
            # Prepare kwargs for provider (filter out handled parameters)
            provider_kwargs = {k: v for k, v in kwargs.items() if k not in [
                "use_responses_api", "tools", "temperature", "max_tokens", "max_completion_tokens"
            ]}
            
            # For OpenAI, pass max_completion_tokens; for others, use max_tokens
            if provider_model.slug == "openai" or provider_model.slug == "deepseek" or provider_model.slug == "grok" or provider_model.slug == "openai_compatible":
                provider_kwargs["max_completion_tokens"] = max_tokens
            else:
                provider_kwargs["max_tokens"] = max_tokens
            
            # Generate completion
            # Pass skip_temperature flag if model doesn't support it
            completion_kwargs = provider_kwargs.copy()
            if normalized.get("skip_temperature"):
                completion_kwargs["skip_temperature"] = True
            
            response = await provider_instance.generate_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,  # Base parameter (will be overridden by provider_kwargs for OpenAI)
                use_responses_api=use_responses_api,
                tools=tools,
                **completion_kwargs
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
        prompt: Optional[AIPrompt],
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
            prompt: AIPrompt object (for provider configuration) or None to use system default
            system_prompt: Pre-rendered system prompt
            user_prompt: Pre-rendered user prompt
            **kwargs: Additional provider-specific settings (model, temperature, max_tokens, etc.)
        
        Returns:
            AIProviderResponse with standardized format
        """
        try:
            # Resolve provider
            if prompt:
                provider_model = self._resolve_provider_for_prompt(prompt)
            else:
                # Use system default provider when prompt is None
                provider_model = self._get_system_default_provider()
            
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
            
            # Get model name (from kwargs, prompt, or provider default)
            model = kwargs.get("model")
            if not model and prompt:
                model = prompt.provider_model or prompt.model
            if not model:
                supported_models = provider_model.supported_models or []
                if supported_models:
                    model = supported_models[0]
                else:
                    model = provider_instance.get_supported_models()[0] if provider_instance.get_supported_models() else "default"
            
            # Get settings (from kwargs, prompt, or defaults)
            if prompt:
                settings = prompt.provider_settings or {}
                default_temperature = settings.get("temperature", prompt.temperature)
                default_max_tokens = settings.get("max_tokens", prompt.max_tokens)
            else:
                settings = {}
                default_temperature = 0.7
                default_max_tokens = 8000
            
            temperature = kwargs.get("temperature", default_temperature)
            # Handle max_completion_tokens (OpenAI) vs max_tokens (other providers)
            if "max_completion_tokens" in kwargs:
                max_tokens = kwargs["max_completion_tokens"]
            elif "max_tokens" in kwargs:
                max_tokens = kwargs["max_tokens"]
            else:
                max_tokens = default_max_tokens
            
            # Normalize parameters based on model requirements
            # Filter out max_tokens and temperature from kwargs to avoid duplicate arguments
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ['max_tokens', 'temperature', 'max_completion_tokens']}
            normalized = self.normalize_model_parameters(
                model=model,
                provider_slug=provider_model.slug,
                temperature=temperature,
                max_tokens=max_tokens,
                **filtered_kwargs
            )
            temperature = normalized["temperature"]
            max_tokens = normalized["max_tokens"]
            
            # Check if we need to use responses API (for OpenAI with web search)
            use_responses_api = kwargs.get("use_responses_api", False)
            tools = kwargs.get("tools", None)
            
            # Prepare kwargs for provider (filter out handled parameters)
            provider_kwargs = {k: v for k, v in kwargs.items() if k not in [
                "use_responses_api", "tools", "temperature", "max_tokens", "max_completion_tokens"
            ]}
            
            # For OpenAI, pass max_completion_tokens; for others, use max_tokens
            if provider_model.slug == "openai" or provider_model.slug == "deepseek" or provider_model.slug == "grok" or provider_model.slug == "openai_compatible":
                provider_kwargs["max_completion_tokens"] = max_tokens
            else:
                provider_kwargs["max_tokens"] = max_tokens
            
            # Generate completion with pre-rendered prompts
            # Add timeout to provider_kwargs if not already set
            if "timeout" not in provider_kwargs:
                provider_kwargs["timeout"] = 300  # 5 minutes default timeout
            
            # Pass skip_temperature flag if model doesn't support it
            completion_kwargs = provider_kwargs.copy()
            if normalized.get("skip_temperature"):
                completion_kwargs["skip_temperature"] = True
            
            response = await provider_instance.generate_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,  # Base parameter (will be overridden by provider_kwargs for OpenAI)
                use_responses_api=use_responses_api,
                tools=tools,
                **completion_kwargs
            )
            
            return response
        
        except Exception as e:
            print(f"[AIProviderService] Error generating completion: {e}")
            import traceback
            traceback.print_exc()
            raise

