#!/usr/bin/env python3
"""
Supplier models for multi-tenant quote system
Migrated from v1 with enhancements
"""

from sqlalchemy import Column, String, Boolean, Text, ForeignKey, DateTime, Numeric, Integer, JSON
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
    
    # Scraping configuration (JSON)
    scraping_config = Column(JSON, nullable=True)  # Selectors, URLs, authentication, etc.
    scraping_enabled = Column(Boolean, default=True, nullable=False)
    scraping_method = Column(String(50), default="generic", nullable=False)  # 'generic', 'api', 'custom'
    
    is_preferred = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="suppliers")
    category = relationship("SupplierCategory", back_populates="suppliers")
    pricing_items = relationship("SupplierPricing", back_populates="supplier", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Supplier {self.name}>"


class SupplierPricing(Base, TimestampMixin):
    """Supplier pricing cache model with verification workflow"""
    __tablename__ = "supplier_pricing"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_id = Column(String(36), ForeignKey("suppliers.id"), nullable=False, index=True)
    
    product_name = Column(String(200), nullable=False, index=True)
    product_code = Column(String(100), nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="GBP", nullable=False)
    
    # Verification and confidence fields
    confidence_score = Column(Numeric(3, 2), default=1.0, nullable=False)  # 0.0-1.0
    verification_status = Column(String(20), default="pending", nullable=False)  # pending, verified, rejected, needs_review
    verified_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    source_url = Column(String(500), nullable=True)
    scraping_method = Column(String(50), nullable=True)  # direct_url, search, known_pricing, api
    scraping_metadata = Column(JSON, nullable=True)  # Selector used, retry count, etc.
    needs_manual_review = Column(Boolean, default=False, nullable=False)
    review_reason = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    last_updated = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="pricing_items")
    verifier = relationship("User", foreign_keys=[verified_by])
    
    def __repr__(self):
        return f"<SupplierPricing {self.product_name} - £{self.price} (confidence: {self.confidence_score})>"


class ProductContentHistory(Base, TimestampMixin):
    """Price history tracking for products with full content for price intelligence"""
    __tablename__ = "product_content_history"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    supplier_id = Column(String(36), ForeignKey("suppliers.id"), nullable=True, index=True)
    
    product_name = Column(String(500), nullable=False, index=True)
    product_code = Column(String(100), nullable=True, index=True)
    supplier_product_url = Column(Text, nullable=True)
    
    # Scraped content (full HTML/text for analysis)
    scraped_content = Column(Text, nullable=True)  # Full HTML/text content from supplier page
    
    # Extracted pricing
    price = Column(Numeric(10, 2), nullable=True)  # Made nullable as extraction may fail
    currency = Column(String(10), default="GBP", nullable=False)
    confidence_score = Column(Numeric(3, 2), default=0.5, nullable=False)  # 0.0-1.0
    
    # Scraping metadata
    scraping_method = Column(String(50), nullable=True)  # direct_url, search, api, cached, known_pricing
    scraping_timestamp = Column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)
    scraping_metadata = Column(JSON, nullable=True)  # Selector used, retry count, etc.
    
    # Verification
    is_verified = Column(Boolean, default=False, nullable=False, index=True)
    verified_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_notes = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Legacy field for backward compatibility
    recorded_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationships
    tenant = relationship("Tenant")
    supplier = relationship("Supplier")
    verifier = relationship("User", foreign_keys=[verified_by])
    
    def __repr__(self):
        return f"<ProductContentHistory {self.product_name} - £{self.price} @ {self.scraping_timestamp}>"


class PricingVerificationQueue(Base, TimestampMixin):
    """Queue for manual verification of low-confidence prices"""
    __tablename__ = "pricing_verification_queue"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    supplier_pricing_id = Column(String(36), ForeignKey("supplier_pricing.id"), nullable=False)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    priority = Column(Integer, default=0, nullable=False, index=True)  # Higher = more urgent
    reason = Column(Text, nullable=False)
    assigned_to = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    status = Column(String(20), default="pending", nullable=False)  # pending, in_progress, verified, rejected, ignored
    
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    supplier_pricing = relationship("SupplierPricing")
    tenant = relationship("Tenant")
    assignee = relationship("User", foreign_keys=[assigned_to])
    
    def __repr__(self):
        return f"<PricingVerificationQueue {self.supplier_pricing_id} - {self.status}>"


