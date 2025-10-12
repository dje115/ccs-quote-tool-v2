"""
API Key Resolution Helper

IMPORTANT: This module provides a centralized way to resolve API keys for multi-tenant applications.
It implements the fallback pattern: Tenant keys first, then system-wide keys.

This pattern should be used everywhere API keys are needed:
- Customer analysis endpoints
- Dashboard AI queries
- Lead generation
- Any external API integration

Usage:
    from app.core.api_keys import get_api_keys
    
    keys = get_api_keys(db, current_tenant)
    ai_service = AIAnalysisService(
        openai_api_key=keys.openai,
        companies_house_api_key=keys.companies_house,
        google_maps_api_key=keys.google_maps
    )
"""

from typing import Optional, NamedTuple
from sqlalchemy.orm import Session
from app.models.tenant import Tenant


class APIKeys(NamedTuple):
    """
    Container for resolved API keys
    
    Each key may be None if not configured at either tenant or system level.
    """
    openai: Optional[str]
    companies_house: Optional[str]
    google_maps: Optional[str]
    source: str  # "tenant" or "system" or "none"


def get_api_keys(db: Session, current_tenant: Tenant) -> APIKeys:
    """
    Resolve API keys with fallback logic
    
    Resolution order:
    1. Check tenant's own API keys
    2. If not found, fall back to system-wide keys (from admin portal)
    3. If still not found, return None
    
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
    
    # Get system tenant for fallback
    system_tenant = db.query(Tenant).filter(Tenant.name == "System").first()
    
    # Resolve each key individually with fallback logic
    # IMPORTANT: Each key is resolved independently - tenant key first, then system fallback
    openai_key = current_tenant.openai_api_key or (system_tenant.openai_api_key if system_tenant else None)
    companies_house_key = current_tenant.companies_house_api_key or (system_tenant.companies_house_api_key if system_tenant else None)
    google_maps_key = current_tenant.google_maps_api_key or (system_tenant.google_maps_api_key if system_tenant else None)
    
    # Determine source for logging/debugging
    if current_tenant.openai_api_key or current_tenant.companies_house_api_key or current_tenant.google_maps_api_key:
        source = "tenant"
    elif system_tenant and (system_tenant.openai_api_key or system_tenant.companies_house_api_key or system_tenant.google_maps_api_key):
        source = "system"
    else:
        source = "none"
    
    return APIKeys(
        openai=openai_key,
        companies_house=companies_house_key,
        google_maps=google_maps_key,
        source=source
    )


def get_resolved_key(db: Session, current_tenant: Tenant, key_name: str) -> Optional[str]:
    """
    Get a specific API key with fallback logic
    
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

