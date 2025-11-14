#!/usr/bin/env python3
"""
Product models for quote system
"""

from sqlalchemy import Column, String, Boolean, Text, Numeric, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from .base import Base, BaseModel


class Product(BaseModel):
    """Product model for catalog (migrated from v1 PricingItem)"""
    __tablename__ = "products"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Product details
    code = Column(String(100), nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    subcategory = Column(String(100), nullable=True)
    
    # Pricing
    unit = Column(String(50), default="each", nullable=False)  # meter, piece, hour, day, etc.
    base_price = Column(Numeric(10, 2), nullable=False)
    cost_price = Column(Numeric(10, 2), nullable=True)
    
    # Supplier information
    supplier = Column(String(100), nullable=True)
    part_number = Column(String(100), nullable=True)
    
    # Settings
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_service = Column(Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f"<Product {self.code or self.name}>"


class PricingRule(BaseModel):
    """Pricing rule model for discounts and bundles"""
    __tablename__ = "pricing_rules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Rule details
    name = Column(String(200), nullable=False)
    rule_type = Column(String(50), nullable=False)  # volume_discount, bundle, seasonal
    
    # Conditions (stored as JSON)
    conditions = Column(Text, nullable=False)  # JSON string
    
    # Discount
    discount_percentage = Column(Numeric(5, 2), nullable=True)
    discount_amount = Column(Numeric(10, 2), nullable=True)
    
    # Settings
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<PricingRule {self.name} ({self.rule_type})>"


class QuoteVersion(BaseModel):
    """Quote version model for versioning"""
    __tablename__ = "quote_versions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_id = Column(String(36), ForeignKey("quotes.id"), nullable=False, index=True)
    
    # Version information
    version = Column(String(10), nullable=False)  # e.g., "1.0", "2.1"
    
    # Full quote snapshot (JSON)
    quote_data = Column(Text, nullable=False)  # JSON string
    
    # Created by
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    quote = relationship("Quote", foreign_keys=[quote_id])
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<QuoteVersion {self.quote_id} v{self.version}>"

