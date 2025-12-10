"""
API Key Resolution Helper

IMPORTANT: This module provides a centralized way to resolve API keys for multi-tenant applications.
It implements the fallback pattern: Tenant keys first, then system-wide keys.

PERFORMANCE: API keys are cached in Redis with TTL to avoid database queries on every request.
Cache is automatically invalidated when API keys are updated.

This pattern should be used everywhere API keys are needed:
- Customer analysis endpoints
- Dashboard AI queries
- Lead generation
- Any external API integration

Usage:
    from app.core.api_keys import get_api_keys, get_provider_api_key
    
    # Legacy usage (still supported)
    keys = get_api_keys(db, current_tenant)
    ai_service = AIAnalysisService(
        openai_api_key=keys.openai,
        companies_house_api_key=keys.companies_house,
        google_maps_api_key=keys.google_maps
    )
    
    # New provider-specific usage
    openai_key = get_provider_api_key(db, current_tenant, "openai")
"""

import json
import asyncio
from typing import Optional, NamedTuple
from sqlalchemy.orm import Session
from app.models.tenant import Tenant
from app.models.ai_provider import ProviderAPIKey, AIProvider
from app.core.config import settings
from app.core.encryption import decrypt_api_key, encrypt_api_key, is_encrypted

# Cache TTL: 1 hour (keys don't change frequently)
API_KEY_CACHE_TTL = 3600


class APIKeys(NamedTuple):
    """
    Container for resolved API keys
    
    Each key may be None if not configured at either tenant or system level.
    """
    openai: Optional[str]
    companies_house: Optional[str]
    google_maps: Optional[str]
    source: str  # "tenant" or "system" or "none"


def _get_api_keys_from_db(db: Session, tenant_id: str) -> APIKeys:
    """
    Internal function to resolve API keys from database (uncached)
    
    Resolution order for each key (consistent for all API keys):
    1. Tenant-specific key (ProviderAPIKey table with tenant_id OR legacy tenant field)
    2. System-level key (ProviderAPIKey table with tenant_id=None OR System tenant legacy field)
    
    IMPORTANT: System tenant keys act as fallbacks for all tenants when tenant-specific keys are not configured.
    This allows centralized API key management in the admin portal.
    """
    # Get tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return APIKeys(openai=None, companies_house=None, google_maps=None, source="none")
    
    # Get system tenant for fallback (system-wide keys stored here by admin portal)
    system_tenant = db.query(Tenant).filter(
        (Tenant.name == "System") | (Tenant.plan == "system")
    ).first()
    
    # Resolve OpenAI key: Check ProviderAPIKey table first, then legacy fields
    # get_provider_api_key already handles tenant → system fallback internally
    openai_key = get_provider_api_key(db, tenant, "openai", tenant_id)
    # Fallback to legacy tenant field
    if not openai_key:
        openai_key = tenant.openai_api_key
    # Fallback to legacy system tenant field (where admin portal stores system-wide keys)
    if not openai_key and system_tenant:
        openai_key = system_tenant.openai_api_key
    
    # Decrypt if encrypted
    if openai_key and is_encrypted(openai_key):
        openai_key = decrypt_api_key(openai_key)
    
    # Resolve Companies House key: Check ProviderAPIKey table first, then legacy fields
    companies_house_key = None
    # TODO: Add ProviderAPIKey support for Companies House when provider is added
    # For now, use legacy fields with system tenant fallback
    companies_house_key = tenant.companies_house_api_key or (system_tenant.companies_house_api_key if system_tenant else None)
    
    # Decrypt if encrypted
    if companies_house_key and is_encrypted(companies_house_key):
        companies_house_key = decrypt_api_key(companies_house_key)
    
    # Resolve Google Maps key: Check ProviderAPIKey table first, then legacy fields
    google_maps_key = None
    # TODO: Add ProviderAPIKey support for Google Maps when provider is added
    # For now, use legacy fields with system tenant fallback
    google_maps_key = tenant.google_maps_api_key or (system_tenant.google_maps_api_key if system_tenant else None)
    
    # Decrypt if encrypted
    if google_maps_key and is_encrypted(google_maps_key):
        google_maps_key = decrypt_api_key(google_maps_key)
    
    # Determine source for logging/debugging
    # Check where we got the keys from (tenant-specific vs system fallback)
    # Priority: tenant-specific > system fallback
    has_tenant_key = (
        (openai_key and tenant.openai_api_key == openai_key) or
        (companies_house_key and tenant.companies_house_api_key == companies_house_key) or
        (google_maps_key and tenant.google_maps_api_key == google_maps_key)
    )
    
    # Also check ProviderAPIKey table for tenant-specific keys
    if not has_tenant_key and openai_key:
        from app.models.ai_provider import ProviderAPIKey, AIProvider
        provider = db.query(AIProvider).filter(AIProvider.slug == "openai", AIProvider.is_active == True).first()
        if provider:
            tenant_provider_key = db.query(ProviderAPIKey).filter(
                ProviderAPIKey.provider_id == provider.id,
                ProviderAPIKey.tenant_id == tenant_id,
                ProviderAPIKey.is_valid == True
            ).first()
            if tenant_provider_key and tenant_provider_key.api_key == openai_key:
                has_tenant_key = True
    
    if has_tenant_key:
        source = "tenant"
    elif openai_key or companies_house_key or google_maps_key:
        # If we have any key and it's not tenant-specific, it must be from system
        source = "system"
    else:
        source = "none"
    
    return APIKeys(
        openai=openai_key,
        companies_house=companies_house_key,
        google_maps=google_maps_key,
        source=source
    )


def get_api_keys(db: Session, current_tenant: Tenant) -> APIKeys:
    """
    Resolve API keys with fallback logic and Redis caching
    
    PERFORMANCE: Results are cached in Redis with 1-hour TTL to avoid database queries.
    Cache key format: `api_keys:tenant:{tenant_id}`
    
    Resolution order:
    1. Check Redis cache
    2. If not cached, query database (tenant keys first, then system-wide keys)
    3. Cache result in Redis
    4. Return APIKeys object
    
    Args:
        db: Database session
        current_tenant: Current tenant object
        
    Returns:
        APIKeys object with resolved keys and source indicator
        
    Example:
        keys = get_api_keys(db, current_tenant)
        if keys.openai:
            print(f"Using OpenAI key from {keys.source}")
            # Use keys.openai for API calls
    """
    tenant_id = current_tenant.id
    
    # Try to get from cache (synchronous Redis access for sync function)
    try:
        from app.core.redis import redis_client
        if redis_client:
            # Use sync Redis client for sync function
            import redis
            sync_redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            cache_key = f"api_keys:tenant:{tenant_id}"
            cached = sync_redis.get(cache_key)
            
            if cached:
                try:
                    data = json.loads(cached)
                    return APIKeys(
                        openai=data.get("openai"),
                        companies_house=data.get("companies_house"),
                        google_maps=data.get("google_maps"),
                        source=data.get("source", "none")
                    )
                except (json.JSONDecodeError, KeyError):
                    # Cache corrupted, fall through to database lookup
                    pass
    except Exception:
        # Redis not available or error, fall through to database lookup
        pass
    
    # Cache miss or error - get from database
    api_keys = _get_api_keys_from_db(db, tenant_id)
    
    # Cache result (fire-and-forget, don't block on cache write)
    try:
        from app.core.redis import redis_client
        if redis_client:
            import redis
            sync_redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            cache_key = f"api_keys:tenant:{tenant_id}"
            cache_data = {
                "openai": api_keys.openai,
                "companies_house": api_keys.companies_house,
                "google_maps": api_keys.google_maps,
                "source": api_keys.source
            }
            sync_redis.setex(
                cache_key,
                API_KEY_CACHE_TTL,
                json.dumps(cache_data)
            )
    except Exception:
        # Cache write failed, but we have the keys from DB so continue
        pass
    
    return api_keys


def invalidate_api_key_cache(tenant_id: str):
    """
    Invalidate cached API keys for a tenant
    
    Call this when API keys are updated to ensure fresh data is fetched.
    
    Args:
        tenant_id: Tenant ID whose cache should be invalidated
    """
    try:
        from app.core.redis import redis_client
        if redis_client:
            import redis
            sync_redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            cache_key = f"api_keys:tenant:{tenant_id}"
            sync_redis.delete(cache_key)
    except Exception:
        # Cache invalidation failed, but that's okay
        pass


def get_resolved_key(db: Session, current_tenant: Tenant, key_name: str) -> Optional[str]:
    """
    Get a specific API key with fallback logic (legacy method)
    
    Args:
        db: Database session
        current_tenant: Current tenant object
        key_name: Name of the key ("openai", "companies_house", or "google_maps")
        
    Returns:
        The resolved API key or None
        
    Example:
        openai_key = get_resolved_key(db, current_tenant, "openai")
        if openai_key:
            # Make OpenAI API call
    """
    keys = get_api_keys(db, current_tenant)
    return getattr(keys, key_name.replace('_api_key', ''), None)


def get_provider_api_key(
    db: Session,
    current_tenant: Tenant,
    provider_slug: str,
    tenant_id: Optional[str] = None
) -> Optional[str]:
    """
    Get API key for a specific AI provider with fallback logic
    
    Resolution order (consistent for all API keys):
    1. Tenant-specific key (ProviderAPIKey table with tenant_id OR legacy tenant field)
    2. System-level key (ProviderAPIKey table with tenant_id=None OR System tenant legacy field)
    
    IMPORTANT: System tenant keys act as fallbacks for all tenants when tenant-specific keys are not configured.
    This allows centralized API key management in the admin portal.
    
    Args:
        db: Database session
        current_tenant: Current tenant object
        provider_slug: Provider slug (e.g., "openai", "google", "anthropic")
        tenant_id: Optional tenant ID (defaults to current_tenant.id)
        
    Returns:
        The resolved API key or None
        
    Example:
        openai_key = get_provider_api_key(db, current_tenant, "openai")
        if openai_key:
            # Use OpenAI API
    """
    try:
        tenant_id = tenant_id or current_tenant.id
        
        # Get system tenant for fallback (where admin portal stores system-wide keys)
        system_tenant = db.query(Tenant).filter(
            (Tenant.name == "System") | (Tenant.plan == "system")
        ).first()
        
        # Get provider by slug
        provider = db.query(AIProvider).filter(
            AIProvider.slug == provider_slug,
            AIProvider.is_active == True
        ).first()
        
        if not provider:
            # Fallback to legacy fields for OpenAI (when provider not in ProviderAPIKey table)
            if provider_slug == "openai":
                # Check tenant-specific first, then system tenant
                return current_tenant.openai_api_key or (
                    system_tenant.openai_api_key if system_tenant else None
                )
            return None
        
        # Try tenant-specific key from ProviderAPIKey table first
        tenant_key = db.query(ProviderAPIKey).filter(
            ProviderAPIKey.provider_id == provider.id,
            ProviderAPIKey.tenant_id == tenant_id,
            ProviderAPIKey.is_valid == True
        ).first()
        
        if tenant_key:
            # Decrypt if encrypted
            key = tenant_key.api_key
            if key and is_encrypted(key):
                key = decrypt_api_key(key)
            return key
        
        # Fallback to system-level key from ProviderAPIKey table
        system_key = db.query(ProviderAPIKey).filter(
            ProviderAPIKey.provider_id == provider.id,
            ProviderAPIKey.tenant_id.is_(None),
            ProviderAPIKey.is_valid == True
        ).first()
        
        if system_key:
            # Decrypt if encrypted
            key = system_key.api_key
            if key and is_encrypted(key):
                key = decrypt_api_key(key)
            return key
        
        # Final fallback: legacy fields (tenant-specific first, then system tenant)
        # This ensures system tenant is the fallback as expected
        if provider_slug == "openai":
            # Check tenant-specific legacy field
            if current_tenant.openai_api_key:
                key = current_tenant.openai_api_key
                if is_encrypted(key):
                    key = decrypt_api_key(key)
                return key
            # Then check system tenant (where admin portal stores system-wide keys)
            if system_tenant and system_tenant.openai_api_key:
                key = system_tenant.openai_api_key
                if is_encrypted(key):
                    key = decrypt_api_key(key)
                return key
        
        return None
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"[get_provider_api_key] Error: {e}", exc_info=True)
        return None

