#!/usr/bin/env python3
"""
Base models for multi-tenant architecture
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid


class TenantMixin:
    """
    Mixin for tenant-aware models.
    
    SECURITY: tenant_id MUST be provided explicitly when creating model instances.
    Do not rely on automatic population - this ensures tenant isolation is explicit
    and prevents accidental cross-tenant data access.
    """
    tenant_id = Column(String(36), nullable=False, index=True)
    
    def __init__(self, **kwargs):
        # SECURITY: Require explicit tenant_id - do not auto-populate
        # This prevents async call issues and ensures tenant isolation is explicit
        if 'tenant_id' not in kwargs:
            raise ValueError(
                "tenant_id is required for tenant-aware models. "
                "Provide it explicitly when creating instances."
            )
        super().__init__(**kwargs)


class TimestampMixin:
    """Mixin for timestamp fields"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


# Create base class
Base = declarative_base()


class BaseModel(Base, TenantMixin, TimestampMixin, SoftDeleteMixin):
    """Base model with tenant isolation, timestamps, and soft delete"""
    __abstract__ = True  # This is an abstract base class


# DEPRECATED: Do not use this function - it causes async call issues
# Always provide tenant_id explicitly when creating model instances
# def get_current_tenant_id() -> str:
#     """Get current tenant ID from context"""
#     # This function is deprecated - tenant_id must be provided explicitly
#     # Using async dependencies synchronously causes errors
#     pass


def generate_uuid() -> str:
    """Generate a new UUID string"""
    return str(uuid.uuid4())
