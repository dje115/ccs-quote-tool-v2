#!/usr/bin/env python3
"""
Quote and pricing models
"""

from sqlalchemy import Column, String, Boolean, Text, JSON, ForeignKey, Integer, Enum, DateTime, Float, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid
from .base import Base, BaseModel


class QuoteStatus(enum.Enum):
    """Quote status enumeration"""
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Quote(BaseModel):
    """Quote model"""
    __tablename__ = "quotes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    
    # Quote details
    quote_number = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Status and dates
    status = Column(Enum(QuoteStatus), default=QuoteStatus.DRAFT, nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    
    # Pricing
    subtotal = Column(Numeric(10, 2), default=0, nullable=False)
    tax_rate = Column(Float, default=0.20, nullable=False)  # 20% VAT
    tax_amount = Column(Numeric(10, 2), default=0, nullable=False)
    total_amount = Column(Numeric(10, 2), default=0, nullable=False)
    
    # Terms and conditions
    payment_terms = Column(String(100), nullable=True)
    delivery_terms = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Template and customization
    template_id = Column(String(36), ForeignKey("quote_templates.id"), nullable=True)
    custom_fields = Column(JSON, nullable=True)
    
    # Tracking
    viewed_at = Column(DateTime(timezone=True), nullable=True)
    viewed_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    template = relationship("QuoteTemplate")
    items = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Quote {self.quote_number} - {self.title}>"
    
    def calculate_totals(self):
        """Calculate quote totals"""
        self.subtotal = sum(item.total_price for item in self.items)
        self.tax_amount = self.subtotal * self.tax_rate
        self.total_amount = self.subtotal + self.tax_amount


class QuoteItem(BaseModel):
    """Quote item model"""
    __tablename__ = "quote_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_id = Column(String(36), ForeignKey("quotes.id"), nullable=False, index=True)
    
    # Item details
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    
    # Pricing
    quantity = Column(Numeric(10, 2), default=1, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_rate = Column(Float, default=0, nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0, nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # Additional details
    notes = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    
    # Relationships
    quote = relationship("Quote", back_populates="items")
    
    def __repr__(self):
        return f"<QuoteItem {self.description}>"
    
    def calculate_total(self):
        """Calculate item total"""
        subtotal = self.quantity * self.unit_price
        self.discount_amount = subtotal * self.discount_rate
        self.total_price = subtotal - self.discount_amount


class QuoteTemplate(BaseModel):
    """Quote template model"""
    __tablename__ = "quote_templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Template details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # HTML template content
    
    # Settings
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Template variables
    variables = Column(JSON, nullable=True)  # Available template variables
    default_values = Column(JSON, nullable=True)  # Default values for variables
    
    # Relationships
    quotes = relationship("Quote", back_populates="template")
    
    def __repr__(self):
        return f"<QuoteTemplate {self.name}>"


class PricingItem(BaseModel):
    """Pricing item model for catalog"""
    __tablename__ = "pricing_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Item details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    sku = Column(String(100), nullable=True)
    
    # Pricing
    base_price = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(50), default="each", nullable=False)
    
    # Settings
    is_active = Column(Boolean, default=True, nullable=False)
    is_service = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    pass  # No relationships needed for now
    
    def __repr__(self):
        return f"<PricingItem {self.name}>"
