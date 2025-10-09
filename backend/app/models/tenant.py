#!/usr/bin/env python3
"""
Tenant and user models for multi-tenant architecture
"""

from sqlalchemy import Column, String, Boolean, Text, JSON, ForeignKey, Integer, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid
from .base import Base, TimestampMixin


class TenantStatus(enum.Enum):
    """Tenant status enumeration"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    EXPIRED = "expired"


class UserRole(enum.Enum):
    """User role enumeration"""
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    MANAGER = "manager"
    SALES_REP = "sales_rep"
    USER = "user"


class Tenant(Base, TimestampMixin):
    """Tenant model for multi-tenant isolation"""
    __tablename__ = "tenants"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    domain = Column(String(255), unique=True, nullable=True)
    
    # Tenant settings
    status = Column(Enum(TenantStatus), default=TenantStatus.TRIAL, nullable=False)
    settings = Column(JSON, default=dict)
    
    # Branding
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), default="#1976d2")
    secondary_color = Column(String(7), default="#dc004e")
    
    # API Keys (tenant-specific)
    openai_api_key = Column(String(255), nullable=True)
    companies_house_api_key = Column(String(255), nullable=True)
    google_maps_api_key = Column(String(255), nullable=True)
    
    # Usage tracking
    api_calls_this_month = Column(Integer, default=0)
    api_limit_monthly = Column(Integer, default=10000)
    
    # Billing
    plan = Column(String(50), default="trial")
    billing_email = Column(String(255), nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant {self.name} ({self.slug})>"


class User(Base, TimestampMixin):
    """User model with tenant awareness"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # User details
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Role and permissions
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    permissions = Column(JSON, default=list)
    
    # Profile
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(20), nullable=True)
    timezone = Column(String(50), default="UTC")
    language = Column(String(5), default="en")
    
    # Settings
    preferences = Column(JSON, default=dict)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    
    def __repr__(self):
        return f"<User {self.username} ({self.email})>"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_admin(self):
        return self.role in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]
    
    @property
    def is_super_admin(self):
        return self.role == UserRole.SUPER_ADMIN
