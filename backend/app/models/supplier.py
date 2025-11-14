#!/usr/bin/env python3
"""
Supplier models for multi-tenant quote system
Migrated from v1 with enhancements
"""

from sqlalchemy import Column, String, Boolean, Text, ForeignKey, DateTime, Numeric, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.models.base import Base, TimestampMixin


class SupplierCategory(Base, TimestampMixin):
    """Supplier category model"""
    __tablename__ = "supplier_categories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="supplier_categories")
    suppliers = relationship("Supplier", back_populates="category", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SupplierCategory {self.name}>"


class Supplier(Base, TimestampMixin):
    """Supplier model"""
    __tablename__ = "suppliers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    category_id = Column(String(36), ForeignKey("supplier_categories.id"), nullable=False, index=True)
    
    name = Column(String(100), nullable=False)
    website = Column(String(200), nullable=True)
    pricing_url = Column(String(500), nullable=True)  # Specific URL for pricing API or page
    api_key = Column(String(200), nullable=True)  # For API-based pricing
    notes = Column(Text, nullable=True)
    
    is_preferred = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="suppliers")
    category = relationship("SupplierCategory", back_populates="suppliers")
    pricing_items = relationship("SupplierPricing", back_populates="supplier", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Supplier {self.name}>"


class SupplierPricing(Base, TimestampMixin):
    """Supplier pricing cache model"""
    __tablename__ = "supplier_pricing"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_id = Column(String(36), ForeignKey("suppliers.id"), nullable=False, index=True)
    
    product_name = Column(String(200), nullable=False, index=True)
    product_code = Column(String(100), nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="GBP", nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    last_updated = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="pricing_items")
    
    def __repr__(self):
        return f"<SupplierPricing {self.product_name} - £{self.price}>"


