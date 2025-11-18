#!/usr/bin/env python3
"""
Centralized AI Orchestration Service

Manages all AI operations with:
- Multi-provider support (OpenAI, Anthropic, Google, Microsoft Copilot, etc.)
- Tenant-aware prompt resolution
- Retry/backoff logic
- Safety filters
- Caching layer
- Observability and logging
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_prompt import AIPrompt, PromptCategory
from app.models.ai_provider import AIProvider, ProviderAPIKey, ProviderType
from app.services.ai_provider_service import AIProviderService
from app.services.ai_prompt_service import AIPromptService
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class AIOrchestrationService:
    """
    Centralized service for all AI operations
    
    Features:
    - Tenant-aware prompt resolution (tenant-specific → system fallback)
    - Multi-provider routing (OpenAI, Anthropic, Google, Microsoft Copilot, etc.)
    - Automatic retry with exponential backoff
    - Response caching (tenant-scoped cache keys)
    - Safety filters and content moderation
    - Comprehensive logging and observability
    """
    
    def __init__(self, db: Session, tenant_id: Optional[str] = None):
        self.db = db
        self.tenant_id = tenant_id
        self.provider_service = AIProviderService(db, tenant_id=tenant_id)
        self.prompt_service = AIPromptService(db, tenant_id=tenant_id)
        self._redis_client: Optional[redis.Redis] = None
        self._cache_ttl = 3600  # 1 hour default cache TTL
        
    async def _get_redis(self) -> Optional[redis.Redis]:
        """Get Redis client for caching"""
        try:
            if self._redis_client is None:
                from app.core.redis import get_redis
                self._redis_client = await get_redis()
            return self._redis_client
        except Exception as e:
            logger.warning(f"Redis not available for AI orchestration caching: {e}")
            return None
    
    def _get_cache_key(
        self,
        category: str,
        prompt_id: str,
        variables_hash: str,
        provider_slug: Optional[str] = None
    ) -> str:
        """Generate cache key for AI response"""
        tenant_key = self.tenant_id or "system"
        provider_key = f":{provider_slug}" if provider_slug else ""
        return f"ai_response:{category}:{prompt_id}:{variables_hash}:{tenant_key}{provider_key}"
    
    def _hash_variables(self, variables: Dict[str, Any]) -> str:
        """Create hash of variables for cache key"""
        import hashlib
        variables_str = json.dumps(variables, sort_keys=True)
        return hashlib.md5(variables_str.encode()).hexdigest()[:12]
    
    async def generate(
        self,
        category: str,
        variables: Dict[str, Any],
        quote_type: Optional[str] = None,
        provider_preference: Optional[str] = None,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate AI response with full orchestration
        
        Args:
            category: Prompt category (e.g., PromptCategory.CUSTOMER_ANALYSIS.value)
            variables: Template variables for prompt rendering
            quote_type: Optional quote type for quote_analysis category
            provider_preference: Preferred provider slug (e.g., "openai", "microsoft_copilot")
            use_cache: Whether to use cached responses
            cache_ttl: Cache TTL in seconds (default: 1 hour)
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay in seconds
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            Dict with:
            - content: AI-generated content
            - provider: Provider used
            - model: Model used
            - cached: Whether response was from cache
            - metadata: Additional metadata (tokens, latency, etc.)
        """
        start_time = datetime.now(timezone.utc)
        
        # 1. Resolve prompt (tenant-aware)
        prompt_obj = await self._resolve_prompt(category, quote_type)
        if not prompt_obj:
            error_msg = f"Prompt not found for category '{category}' (quote_type={quote_type}) for tenant {self.tenant_id}. Please seed prompts using backend/scripts/seed_ai_prompts.py"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 2. Check cache
        variables_hash = self._hash_variables(variables)
        cache_key = self._get_cache_key(category, prompt_obj.id, variables_hash, provider_preference)
        
        if use_cache:
            cached_response = await self._get_cached_response(cache_key)
            if cached_response:
                logger.info(f"AI response cache hit: {category} (tenant={self.tenant_id})")
                return {
                    **cached_response,
                    "cached": True,
                    "cache_key": cache_key
                }
        
        # 3. Resolve provider (tenant-aware)
        provider_slug = await self._resolve_provider(prompt_obj, provider_preference)
        if not provider_slug:
            error_msg = f"No valid AI provider found for tenant {self.tenant_id}. Please configure API keys in admin portal."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 4. Generate with retry logic
        response = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Render prompt
                rendered = self.prompt_service.render_prompt(prompt_obj, variables)
                
                # Generate via provider service
                provider_response = await self.provider_service.generate(
                    prompt=prompt_obj,
                    variables=variables,
                    **kwargs
                )
                
                # 5. Apply safety filters
                filtered_content = await self._apply_safety_filters(provider_response.content)
                
                # Build response
                response = {
                    "content": filtered_content,
                    "provider": provider_slug,
                    "model": prompt_obj.provider_model or prompt_obj.model,
                    "cached": False,
                    "metadata": {
                        "prompt_id": prompt_obj.id,
                        "prompt_version": prompt_obj.version,
                        "category": category,
                        "quote_type": quote_type,
                        "tenant_id": self.tenant_id,
                        "attempt": attempt + 1,
                        "latency_ms": (datetime.now(timezone.utc) - start_time).total_seconds() * 1000,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                }
                
                # 6. Cache response
                if use_cache:
                    await self._cache_response(cache_key, response, cache_ttl or self._cache_ttl)
                
                # 7. Log success
                logger.info(
                    f"AI generation successful: category={category}, provider={provider_slug}, "
                    f"tenant={self.tenant_id}, latency={response['metadata']['latency_ms']:.0f}ms"
                )
                
                break
                
            except Exception as e:
                last_error = e
                logger.warning(
                    f"AI generation attempt {attempt + 1}/{max_retries} failed: {e} "
                    f"(category={category}, provider={provider_slug}, tenant={self.tenant_id})"
                )
                
                if attempt < max_retries - 1:
                    # Exponential backoff
                    delay = retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    # Final attempt failed
                    logger.error(
                        f"AI generation failed after {max_retries} attempts: {e} "
                        f"(category={category}, provider={provider_slug}, tenant={self.tenant_id})"
                    )
                    raise
        
        if response is None:
            raise Exception(f"AI generation failed: {last_error}")
        
        return response
    
    async def _resolve_prompt(
        self,
        category: str,
        quote_type: Optional[str] = None
    ) -> Optional[AIPrompt]:
        """
        Resolve prompt with tenant-aware fallback hierarchy
        
        Priority:
        1. Tenant-specific prompt (with quote_type if applicable)
        2. Tenant-specific generic prompt
        3. System prompt (with quote_type if applicable)
        4. System generic prompt
        
        Returns:
            AIPrompt object or None if not found
        """
        return await self.prompt_service.get_prompt(
            category=category,
            tenant_id=self.tenant_id,
            quote_type=quote_type
        )
    
    async def _resolve_provider(
        self,
        prompt: AIPrompt,
        preference: Optional[str] = None
    ) -> Optional[str]:
        """
        Resolve AI provider with tenant-aware fallback
        
        Priority:
        1. Prompt-specific provider (if prompt.use_system_default == False)
        2. Preferred provider (if valid API key exists)
        3. Tenant default provider
        4. System default provider
        
        Returns:
            Provider slug (e.g., "openai", "microsoft_copilot") or None
        """
        # Check if prompt has specific provider
        if not prompt.use_system_default and prompt.provider_id:
            provider = self.db.query(AIProvider).filter(
                AIProvider.id == prompt.provider_id,
                AIProvider.is_active == True
            ).first()
            
            if provider:
                # Check if tenant or system has valid API key
                if await self._has_valid_api_key(provider.id, provider.slug):
                    return provider.slug
        
        # Check preferred provider
        if preference:
            provider = self.db.query(AIProvider).filter(
                AIProvider.slug == preference,
                AIProvider.is_active == True
            ).first()
            
            if provider and await self._has_valid_api_key(provider.id, provider.slug):
                return provider.slug
        
        # Check tenant default provider (TODO: implement tenant provider preferences)
        # For now, fall back to system default
        
        # Check system default provider
        default_provider = self.db.query(AIProvider).filter(
            AIProvider.is_active == True
        ).order_by(AIProvider.created_at).first()
        
        if default_provider and await self._has_valid_api_key(default_provider.id, default_provider.slug):
            return default_provider.slug
        
        return None
    
    async def _has_valid_api_key(self, provider_id: str, provider_slug: str) -> bool:
        """Check if tenant or system has valid API key for provider"""
        from sqlalchemy import select, and_, or_
        
        # Check tenant key
        if self.tenant_id:
            tenant_key_stmt = select(ProviderAPIKey).where(
                and_(
                    ProviderAPIKey.provider_id == provider_id,
                    ProviderAPIKey.tenant_id == self.tenant_id,
                    ProviderAPIKey.is_valid == True
                )
            )
            # Use sync query for now (provider service uses sync)
            tenant_key = self.db.query(ProviderAPIKey).filter(
                ProviderAPIKey.provider_id == provider_id,
                ProviderAPIKey.tenant_id == self.tenant_id,
                ProviderAPIKey.is_valid == True
            ).first()
            
            if tenant_key:
                return True
        
        # Check system key
        system_key = self.db.query(ProviderAPIKey).filter(
            ProviderAPIKey.provider_id == provider_id,
            ProviderAPIKey.tenant_id.is_(None),
            ProviderAPIKey.is_valid == True
        ).first()
        
        return system_key is not None
    
    async def _apply_safety_filters(self, content: str) -> str:
        """
        Apply safety filters to AI-generated content
        
        TODO: Implement content moderation, PII detection, etc.
        """
        # Basic safety: remove any obvious PII patterns (email, phone, etc.)
        # This is a placeholder - implement proper safety filters
        
        # For now, just return content as-is
        return content
    
    async def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached AI response"""
        redis_client = await self._get_redis()
        if not redis_client:
            return None
        
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
        
        return None
    
    async def _cache_response(self, cache_key: str, response: Dict[str, Any], ttl: int):
        """Cache AI response"""
        redis_client = await self._get_redis()
        if not redis_client:
            return
        
        try:
            # Remove metadata that shouldn't be cached
            cacheable_response = {
                "content": response["content"],
                "provider": response["provider"],
                "model": response["model"]
            }
            
            await redis_client.setex(
                cache_key,
                ttl,
                json.dumps(cacheable_response)
            )
        except Exception as e:
            logger.warning(f"Error caching response: {e}")
    
    async def invalidate_cache(
        self,
        category: Optional[str] = None,
        prompt_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ):
        """
        Invalidate cached AI responses
        
        Args:
            category: Invalidate all responses for this category
            prompt_id: Invalidate all responses for this prompt
            tenant_id: Invalidate all responses for this tenant
        """
        redis_client = await self._get_redis()
        if not redis_client:
            return
        
        try:
            if prompt_id:
                # Invalidate specific prompt
                pattern = f"ai_response:*:{prompt_id}:*"
            elif category:
                # Invalidate category
                tenant_key = tenant_id or self.tenant_id or "*"
                pattern = f"ai_response:{category}:*:*:{tenant_key}*"
            elif tenant_id:
                # Invalidate tenant
                pattern = f"ai_response:*:*:*:{tenant_id}*"
            else:
                # Invalidate all (use with caution)
                pattern = "ai_response:*"
            
            # Get all matching keys
            keys = []
            async for key in redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            # Delete keys
            if keys:
                await redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cached AI responses (pattern={pattern})")
        
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get AI orchestration metrics
        
        Returns:
            Dict with metrics (cache hit rate, average latency, etc.)
        """
        # TODO: Implement metrics collection
        # This would track:
        # - Cache hit/miss rates
        # - Average latency per provider
        # - Error rates per provider
        # - Token usage per tenant
        # - Cost tracking
        
        return {
            "cache_enabled": self._redis_client is not None,
            "default_cache_ttl": self._cache_ttl,
            "tenant_id": self.tenant_id
        }

