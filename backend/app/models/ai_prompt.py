#!/usr/bin/env python3
"""
AI Prompt models for database-driven prompt management
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, Float, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from .base import Base, TimestampMixin


class PromptCategory(str, enum.Enum):
    """Prompt category enumeration"""
    CUSTOMER_ANALYSIS = "customer_analysis"
    LEAD_SCORING = "lead_scoring"
    ACTIVITY_ENHANCEMENT = "activity_enhancement"
    ACTION_SUGGESTIONS = "action_suggestions"
    LEAD_GENERATION = "lead_generation"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    FINANCIAL_ANALYSIS = "financial_analysis"
    PLANNING_ANALYSIS = "planning_analysis"
    TRANSLATION = "translation"
    QUOTE_ANALYSIS = "quote_analysis"
    PRODUCT_SEARCH = "product_search"
    BUILDING_ANALYSIS = "building_analysis"
    COMPANY_PROFILE_ANALYSIS = "company_profile_analysis"
    PRICING_ANALYSIS = "pricing_analysis"


class AIPrompt(Base, TimestampMixin):
    """AI Prompt model for database-driven prompt management"""
    __tablename__ = "ai_prompts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Basic information
    name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    quote_type = Column(String(100), nullable=True, index=True)  # For quote_analysis category: 'cabling', 'network_build', 'server_build', 'software_dev', 'testing', 'design', etc.
    
    # Prompt content
    system_prompt = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=False)
    
    # Model configuration (legacy - kept for backward compatibility)
    model = Column(String(50), default="gpt-5-mini", nullable=False)
    temperature = Column(Float, default=0.7, nullable=False)
    max_tokens = Column(Integer, default=8000, nullable=False)
    
    # Provider configuration (new multi-provider support)
    provider_id = Column(String(36), ForeignKey("ai_providers.id"), nullable=True, index=True)
    provider_model = Column(String(100), nullable=True)  # Specific model name for the provider
    provider_settings = Column(JSON, nullable=True)  # Provider-specific settings (temperature, max_tokens, top_p, etc.)
    use_system_default = Column(Boolean, default=True, nullable=False)  # If true, uses system default provider; if false, uses prompt-specific provider
    
    # Versioning and status
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_system = Column(Boolean, default=False, nullable=False)  # System vs tenant-specific
    
    # Tenant association (nullable for system prompts)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Template variables
    variables = Column(JSON, nullable=True)  # Available template variables with descriptions
    
    # Relationships
    tenant = relationship("Tenant", backref="ai_prompts")
    creator = relationship("User", backref="created_prompts")
    versions = relationship("AIPromptVersion", back_populates="prompt", cascade="all, delete-orphan")
    provider = relationship("AIProvider", backref="prompts")
    
    def __repr__(self):
        return f"<AIPrompt {self.name} ({self.category}) v{self.version}>"
    
    __table_args__ = (
        Index('idx_prompt_category_tenant', 'category', 'tenant_id', 'is_active'),
    )


class AIPromptVersion(Base, TimestampMixin):
    """AI Prompt version history"""
    __tablename__ = "ai_prompt_versions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prompt_id = Column(String(36), ForeignKey("ai_prompts.id"), nullable=False, index=True)
    
    # Version information
    version = Column(Integer, nullable=False)
    note = Column(String(255), nullable=True)  # Change note
    
    # Prompt content snapshot
    system_prompt = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=False)
    variables = Column(JSON, nullable=True)
    
    # Model configuration snapshot
    model = Column(String(50), nullable=False)
    temperature = Column(Float, nullable=False)
    max_tokens = Column(Integer, nullable=False)
    
    # Provider configuration snapshot
    provider_id = Column(String(36), nullable=True)
    provider_model = Column(String(100), nullable=True)
    provider_settings = Column(JSON, nullable=True)
    use_system_default = Column(Boolean, default=True, nullable=False)
    
    # Who created this version
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    prompt = relationship("AIPrompt", back_populates="versions")
    creator = relationship("User", backref="prompt_versions")
    
    def __repr__(self):
        return f"<AIPromptVersion {self.prompt_id} v{self.version}>"
    
    __table_args__ = (
        Index('idx_prompt_version', 'prompt_id', 'version'),
    )

