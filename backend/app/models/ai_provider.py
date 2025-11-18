#!/usr/bin/env python3
"""
AI Provider models for multi-provider AI support
"""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, JSON, Index, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from .base import Base, TimestampMixin


class ProviderType(str, enum.Enum):
    """AI Provider type enumeration"""
    CLOUD = "cloud"
    ON_PREMISE = "on_premise"
    MICROSOFT_COPILOT = "microsoft_copilot"  # Microsoft Copilot (Microsoft Graph integration)


class AIProvider(Base, TimestampMixin):
    """AI Provider model - stores provider configurations"""
    __tablename__ = "ai_providers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Basic information
    name = Column(String(100), nullable=False, unique=True)  # e.g., "OpenAI", "Google", "Anthropic"
    slug = Column(String(50), nullable=False, unique=True, index=True)  # e.g., "openai", "google", "anthropic"
    provider_type = Column(String(20), nullable=False)  # "cloud" or "on_premise"
    
    # Configuration
    base_url = Column(String(500), nullable=True)  # For on-premise or custom endpoints
    supported_models = Column(JSON, nullable=True)  # List of supported model names
    default_settings = Column(JSON, nullable=True)  # Default settings like temperature, max_tokens
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Relationships
    api_keys = relationship("ProviderAPIKey", back_populates="provider", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AIProvider {self.name} ({self.slug})>"
    
    __table_args__ = (
        Index('idx_provider_slug_active', 'slug', 'is_active'),
    )


class ProviderAPIKey(Base, TimestampMixin):
    """Provider API Key model - stores API keys per provider per tenant/system"""
    __tablename__ = "provider_api_keys"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Provider and tenant association
    provider_id = Column(String(36), ForeignKey("ai_providers.id"), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)  # None = system-level key
    
    # API key (should be encrypted in production)
    api_key = Column(Text, nullable=False)  # TODO: Encrypt this in production
    
    # Testing and validation
    last_tested = Column(DateTime(timezone=True), nullable=True)
    is_valid = Column(Boolean, default=False, nullable=False, index=True)
    test_result = Column(Text, nullable=True)  # Success message or error details
    test_error = Column(Text, nullable=True)  # Error message if test failed
    
    # Relationships
    provider = relationship("AIProvider", back_populates="api_keys")
    tenant = relationship("Tenant", backref="provider_api_keys")
    
    def __repr__(self):
        tenant_str = self.tenant_id or "system"
        return f"<ProviderAPIKey {self.provider_id} ({tenant_str})>"
    
    __table_args__ = (
        Index('idx_provider_tenant', 'provider_id', 'tenant_id'),
        Index('idx_provider_valid', 'provider_id', 'is_valid'),
    )

