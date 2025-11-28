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


class QuoteApprovalState(enum.Enum):
    """Approval workflow state"""
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class OrderStatus(enum.Enum):
    """Customer order status"""
    DRAFT = "draft"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


class PurchaseOrderStatus(enum.Enum):
    """Supplier purchase order status"""
    DRAFT = "draft"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RECEIVED = "received"
    CLOSED = "closed"
    CANCELLED = "cancelled"


ENUM_KWARGS = {
    "values_callable": lambda enum_cls: [member.value for member in enum_cls]
}


class Quote(BaseModel):
    """Quote model"""
    __tablename__ = "quotes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=True, index=True)  # Nullable - can be for lead or customer
    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=True, index=True)  # For quotes created from leads
    
    # Quote details
    quote_number = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    quote_type = Column(String(100), nullable=True, index=True)  # e.g., 'cabling', 'network_build', 'server_build', 'software_dev', 'testing', 'design'
    
    # Project details (from v1)
    project_title = Column(String(200), nullable=True)
    project_description = Column(Text, nullable=True)
    site_address = Column(Text, nullable=True)
    
    # Building/project details (from v1)
    building_type = Column(String(100), nullable=True)
    building_size = Column(Float, nullable=True)  # in square meters
    number_of_floors = Column(Integer, default=1, nullable=True)
    number_of_rooms = Column(Integer, default=1, nullable=True)
    
    # Requirements (from v1)
    cabling_type = Column(String(50), nullable=True)  # cat5e, cat6, fiber
    wifi_requirements = Column(Boolean, default=False, nullable=True)
    cctv_requirements = Column(Boolean, default=False, nullable=True)
    door_entry_requirements = Column(Boolean, default=False, nullable=True)
    special_requirements = Column(Text, nullable=True)
    
    # Travel cost (from v1)
    travel_distance_km = Column(Float, nullable=True)
    travel_time_minutes = Column(Float, nullable=True)
    travel_cost = Column(Numeric(10, 2), nullable=True)
    
    # AI analysis fields (from v1, stored as JSON)
    ai_analysis = Column(JSON, nullable=True)
    recommended_products = Column(JSON, nullable=True)
    labour_breakdown = Column(JSON, nullable=True)
    quotation_details = Column(JSON, nullable=True)
    clarifications_log = Column(JSON, nullable=True)  # Array of {question, answer}
    ai_raw_response = Column(Text, nullable=True)  # Complete raw AI response
    
    # Estimated fields (from v1)
    estimated_time = Column(Integer, nullable=True)  # hours
    estimated_cost = Column(Numeric(10, 2), nullable=True)
    
    # Status and dates
    status = Column(Enum(QuoteStatus, **ENUM_KWARGS), default=QuoteStatus.DRAFT, nullable=False)
    approval_state = Column(Enum(QuoteApprovalState, **ENUM_KWARGS), default=QuoteApprovalState.NOT_REQUIRED, nullable=False)
    manual_mode = Column(Boolean, default=False, nullable=False)
    version_number = Column(Integer, default=1, nullable=False)
    parent_quote_id = Column(String(36), ForeignKey("quotes.id"), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancel_reason = Column(Text, nullable=True)
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
    
    # Customer Portal
    show_in_customer_portal = Column(Boolean, default=False, nullable=False)  # Show quote in customer portal
    
    # Multi-part quote system fields
    tier_type = Column(String(20), default="single", nullable=False)  # 'single' or 'three_tier'
    ai_generation_data = Column(JSON, nullable=True)  # AI generation metadata: industry detected, prompt used, etc.
    last_prompt_text = Column(Text, nullable=True)  # The last prompt text used to generate this quote
    
    # Created by
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    template = relationship("QuoteTemplate")
    items = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")
    created_by_user = relationship("User", foreign_keys=[created_by])
    documents = relationship("QuoteDocument", back_populates="quote", cascade="all, delete-orphan")
    parent_quote = relationship("Quote", remote_side=[id], backref="child_versions")
    workflow_logs = relationship("QuoteWorkflowLog", back_populates="quote", cascade="all, delete-orphan")
    customer_order = relationship("CustomerOrder", back_populates="quote", uselist=False)
    
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
    item_type = Column(String(50), default="standard", nullable=False)
    unit_type = Column(String(50), default="each", nullable=False)
    section_name = Column(String(255), nullable=True)
    
    # Pricing
    quantity = Column(Numeric(10, 2), default=1, nullable=False)
    unit_cost = Column(Numeric(10, 2), default=0, nullable=True)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_rate = Column(Float, default=0, nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0, nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    margin_percent = Column(Float, default=0, nullable=True)
    tax_rate = Column(Float, default=0, nullable=True)
    
    # Supplier / configuration details
    supplier_id = Column(String(36), ForeignKey("suppliers.id"), nullable=True)
    is_optional = Column(Boolean, default=False, nullable=False)
    is_alternate = Column(Boolean, default=False, nullable=False)
    alternate_group = Column(String(36), nullable=True)
    bundle_parent_id = Column(String(36), nullable=True)
    # Column name remains "metadata" in DB; attribute renamed to avoid SQLAlchemy reserved word
    item_metadata = Column("metadata", JSON, nullable=True, default=dict)
    
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


# Note: Product model moved to product.py for better organization
# PricingItem kept for backward compatibility but consider migrating to Product
class PricingItem(BaseModel):
    """Pricing item model for catalog (legacy - consider using Product instead)"""
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


class QuoteWorkflowLog(BaseModel):
    """Workflow transition history"""
    __tablename__ = "quote_workflow_log"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_id = Column(String(36), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(String(20), nullable=True)
    to_status = Column(String(20), nullable=True)
    action = Column(String(50), nullable=True)
    comment = Column(Text, nullable=True)
    workflow_metadata = Column("metadata", JSON, nullable=True, default=dict)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    quote = relationship("Quote", back_populates="workflow_logs")


class CustomerOrder(BaseModel):
    """Customer order generated from accepted quote"""
    __tablename__ = "customer_orders"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_id = Column(String(36), ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, unique=True)
    status = Column(Enum(OrderStatus, **ENUM_KWARGS), default=OrderStatus.DRAFT, nullable=False)
    customer_po_number = Column(String(100), nullable=True)
    internal_order_number = Column(String(100), nullable=True)
    billing_address = Column(Text, nullable=True)
    shipping_address = Column(Text, nullable=True)
    payment_terms = Column(Text, nullable=True)
    deposit_required = Column(Numeric(10, 2), nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=True)
    order_metadata = Column("metadata", JSON, nullable=True, default=dict)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    quote = relationship("Quote", back_populates="customer_order")
    purchase_orders = relationship("SupplierPurchaseOrder", back_populates="customer_order", cascade="all, delete-orphan")


class SupplierPurchaseOrder(BaseModel):
    """Purchase orders raised to suppliers for a customer order"""
    __tablename__ = "supplier_purchase_orders"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_order_id = Column(String(36), ForeignKey("customer_orders.id", ondelete="CASCADE"), nullable=True, index=True)
    supplier_id = Column(String(36), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(PurchaseOrderStatus, **ENUM_KWARGS), default=PurchaseOrderStatus.DRAFT, nullable=False)
    po_number = Column(String(100), nullable=True)
    expected_date = Column(DateTime(timezone=True), nullable=True)
    total_cost = Column(Numeric(12, 2), nullable=True)
    purchase_metadata = Column("metadata", JSON, nullable=True, default=dict)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    customer_order = relationship("CustomerOrder", back_populates="purchase_orders")
