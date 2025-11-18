#!/usr/bin/env python3
"""
Pricing Configuration Models
Centralized configuration for tenant-specific pricing: day rates, bundles, managed services, etc.
"""

from sqlalchemy import Column, String, Boolean, Text, JSON, ForeignKey, Numeric, Integer, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid
from .base import Base, BaseModel, TimestampMixin


class PricingConfigType(str, enum.Enum):
    """Type of pricing configuration"""
    DAY_RATE = "day_rate"
    HOURLY_RATE = "hourly_rate"
    BUNDLE = "bundle"
    MANAGED_SERVICE = "managed_service"
    DISCOUNT_RULE = "discount_rule"
    VOLUME_PRICING = "volume_pricing"


class BundleType(str, enum.Enum):
    """Type of bundle"""
    PRODUCT_BUNDLE = "product_bundle"  # Multiple products together
    SERVICE_BUNDLE = "service_bundle"  # Multiple services together
    MIXED_BUNDLE = "mixed_bundle"  # Products + services


class TenantPricingConfig(BaseModel):
    """Tenant-specific pricing configuration"""
    __tablename__ = "tenant_pricing_configs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Configuration type
    config_type = Column(String(50), nullable=False, index=True)  # day_rate, hourly_rate, bundle, managed_service, etc.
    
    # Basic information
    name = Column(String(200), nullable=False)  # e.g., "Standard Day Rate", "Network Bundle", "Managed IT Support"
    description = Column(Text, nullable=True)
    code = Column(String(100), nullable=True, index=True)  # Short code for reference
    
    # Pricing details (varies by type)
    # For day rates: base_rate per day
    # For bundles: bundle_price
    # For managed services: monthly/annual rate
    base_rate = Column(Numeric(10, 2), nullable=True)  # Base rate/price
    unit = Column(String(50), nullable=True)  # "day", "hour", "month", "year", "bundle"
    
    # Configuration data (JSON for flexible structure)
    # For day rates: { "engineers": 2, "hours_per_day": 8, "includes_travel": false }
    # For bundles: { "products": [...], "services": [...], "discount_percentage": 10 }
    # For managed services: { "service_tier": "standard", "included_items": [...], "limits": {...} }
    config_data = Column(JSON, nullable=True)
    
    # Validity and conditions
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Priority/order (for multiple configs of same type)
    priority = Column(Integer, default=0, nullable=False)  # Higher priority = used first
    
    # Versioning
    version = Column(Integer, default=1, nullable=False)
    parent_config_id = Column(String(36), ForeignKey("tenant_pricing_configs.id"), nullable=True)  # For versioning
    
    # Relationships
    parent_config = relationship("TenantPricingConfig", remote_side=[id], backref="versions")
    
    def __repr__(self):
        return f"<TenantPricingConfig {self.name} ({self.config_type})>"
    
    __table_args__ = (
        Index('idx_pricing_config_tenant_type_active', 'tenant_id', 'config_type', 'is_active'),
    )


class PricingBundleItem(BaseModel):
    """Items included in a pricing bundle"""
    __tablename__ = "pricing_bundle_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bundle_config_id = Column(String(36), ForeignKey("tenant_pricing_configs.id"), nullable=False, index=True)
    
    # Item details
    item_type = Column(String(50), nullable=False)  # "product", "service", "day_rate", "custom"
    item_id = Column(String(36), nullable=True)  # Reference to product/service ID if applicable
    item_name = Column(String(200), nullable=False)  # Name/description
    item_code = Column(String(100), nullable=True)
    
    # Quantity and pricing
    quantity = Column(Numeric(10, 2), default=1, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=True)  # Individual price (for display)
    bundle_price = Column(Numeric(10, 2), nullable=True)  # Price within bundle (may be discounted)
    
    # Order within bundle
    display_order = Column(Integer, default=0, nullable=False)
    
    # Additional data
    item_data = Column(JSON, nullable=True)  # Additional item-specific data
    
    # Relationships
    bundle_config = relationship("TenantPricingConfig", foreign_keys=[bundle_config_id])
    
    def __repr__(self):
        return f"<PricingBundleItem {self.item_name} (x{self.quantity})>"
    
    __table_args__ = (
        Index('idx_bundle_items_bundle', 'bundle_config_id', 'display_order'),
    )



