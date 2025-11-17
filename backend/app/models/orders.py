#!/usr/bin/env python3
"""
Order models for customer orders
"""

from sqlalchemy import Column, String, Boolean, Text, JSON, ForeignKey, Integer, Enum, DateTime, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid
from .base import Base, BaseModel


class OrderStatus(enum.Enum):
    """Order status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(enum.Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"
    REFUNDED = "refunded"


class OrderPriority(enum.Enum):
    """Order priority enumeration"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Order(BaseModel):
    """Order model for customer orders"""
    __tablename__ = "orders"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    quote_id = Column(String(36), ForeignKey("quotes.id"), nullable=True, index=True)
    
    # Order identification
    order_number = Column(String(100), unique=True, nullable=False, index=True)
    order_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Order details
    status = Column(String(50), nullable=False, default="pending", index=True)
    priority = Column(String(50), default="normal")
    
    # Pricing
    subtotal = Column(Numeric(12, 2), nullable=False, default=0)
    tax_rate = Column(Numeric(5, 4), default=0.20)
    tax_amount = Column(Numeric(12, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(12, 2), nullable=False, default=0)
    currency = Column(String(3), default="GBP")
    
    # Shipping
    shipping_address = Column(Text, nullable=True)
    shipping_postcode = Column(String(20), nullable=True)
    shipping_method = Column(String(100), nullable=True)
    shipping_cost = Column(Numeric(12, 2), default=0)
    estimated_delivery_date = Column(DateTime(timezone=True), nullable=True)
    
    # Payment
    payment_status = Column(String(50), default="pending")
    payment_method = Column(String(100), nullable=True)
    payment_reference = Column(String(255), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Order items (stored as JSON for flexibility)
    items = Column(JSON, nullable=True)
    
    # Notes and metadata
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)  # Internal notes not visible to customer
    order_metadata = Column(JSON, nullable=True)
    
    # Created by
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", backref="orders")
    customer = relationship("Customer", backref="orders")
    quote = relationship("Quote", backref="orders")
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<Order {self.order_number}>"

