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
    """Mixin for tenant-aware models"""
    tenant_id = Column(String(36), nullable=False, index=True)
    
    def __init__(self, **kwargs):
        if 'tenant_id' not in kwargs:
            kwargs['tenant_id'] = get_current_tenant_id()
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


def get_current_tenant_id() -> str:
    """Get current tenant ID from context"""
    # This will be implemented with dependency injection
    from app.core.dependencies import get_current_tenant
    tenant = get_current_tenant()
    return tenant.id if tenant else "system"


def generate_uuid() -> str:
    """Generate a new UUID string"""
    return str(uuid.uuid4())
