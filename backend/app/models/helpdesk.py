#!/usr/bin/env python3
"""
Helpdesk models for ticket management and customer service
"""

from sqlalchemy import Column, String, Boolean, Text, ForeignKey, DateTime, Integer, Enum, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from .base import Base, TimestampMixin


class TicketStatus(str, enum.Enum):
    """Ticket status enumeration"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class TicketPriority(str, enum.Enum):
    """Ticket priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketType(str, enum.Enum):
    """Ticket type enumeration"""
    SUPPORT = "support"
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    BILLING = "billing"
    TECHNICAL = "technical"
    GENERAL = "general"


class Ticket(Base, TimestampMixin):
    """Helpdesk ticket model"""
    __tablename__ = "tickets"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Ticket identification
    ticket_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Customer and contact
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=True, index=True)
    contact_id = Column(String(36), ForeignKey("contacts.id"), nullable=True, index=True)
    created_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # Internal user who created
    
    # Ticket details
    subject = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)  # This will be the improved version shown in portal
    original_description = Column(Text, nullable=True)  # Original description typed by agent
    improved_description = Column(Text, nullable=True)  # AI-improved description (shown in portal)
    ai_suggestions = Column(JSON, nullable=True)  # AI suggestions: {"next_actions": [], "questions": [], "solutions": []}
    ai_analysis_date = Column(DateTime(timezone=True), nullable=True)  # When AI analysis was performed
    ticket_type = Column(Enum(TicketType), default=TicketType.SUPPORT, nullable=False, index=True)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN, nullable=False, index=True)
    priority = Column(Enum(TicketPriority), default=TicketPriority.MEDIUM, nullable=False, index=True)
    
    # Assignment
    assigned_to_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    
    # SLA tracking
    sla_policy_id = Column(String(36), ForeignKey("sla_policies.id"), nullable=True, index=True)  # Applied SLA policy
    sla_target_hours = Column(Integer, nullable=True)  # Target resolution time in hours (calculated from policy)
    sla_first_response_hours = Column(Integer, nullable=True)  # Target first response time in hours
    first_response_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # SLA compliance tracking
    sla_first_response_breached = Column(Boolean, default=False, nullable=False)  # Did we breach first response SLA?
    sla_resolution_breached = Column(Boolean, default=False, nullable=False)  # Did we breach resolution SLA?
    sla_first_response_breached_at = Column(DateTime(timezone=True), nullable=True)  # When first response SLA was breached
    sla_resolution_breached_at = Column(DateTime(timezone=True), nullable=True)  # When resolution SLA was breached
    sla_first_response_met_at = Column(DateTime(timezone=True), nullable=True)  # When first response SLA was met
    sla_resolution_met_at = Column(DateTime(timezone=True), nullable=True)  # When resolution SLA was met
    
    # Related entities
    related_quote_id = Column(String(36), ForeignKey("quotes.id"), nullable=True)
    related_contract_id = Column(String(36), ForeignKey("support_contracts.id"), nullable=True)
    
    # Metadata
    tags = Column(JSON, nullable=True)  # Array of tag strings
    custom_fields = Column(JSON, nullable=True)  # Custom field values
    internal_notes = Column(Text, nullable=True)  # Internal notes not visible to customer
    
    # Satisfaction
    customer_satisfaction_rating = Column(Integer, nullable=True)  # 1-5
    customer_feedback = Column(Text, nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    customer = relationship("Customer")
    contact = relationship("Contact")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    related_quote = relationship("Quote", foreign_keys=[related_quote_id])
    related_contract = relationship("SupportContract", foreign_keys=[related_contract_id])
    sla_policy = relationship("SLAPolicy", foreign_keys=[sla_policy_id])
    comments = relationship("TicketComment", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketComment.created_at")
    attachments = relationship("TicketAttachment", back_populates="ticket", cascade="all, delete-orphan")
    history = relationship("TicketHistory", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketHistory.created_at")
    
    def __repr__(self):
        return f"<Ticket {self.ticket_number} - {self.subject}>"
    
    __table_args__ = (
        Index('idx_tickets_tenant_status', 'tenant_id', 'status'),
        Index('idx_tickets_tenant_priority', 'tenant_id', 'priority'),
        Index('idx_tickets_assigned', 'tenant_id', 'assigned_to_id', 'status'),
        Index('idx_tickets_customer', 'tenant_id', 'customer_id', 'status'),
    )


class TicketComment(Base, TimestampMixin):
    """Ticket comment/update model"""
    __tablename__ = "ticket_comments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String(36), ForeignKey("tickets.id"), nullable=False, index=True)
    
    # Comment details
    comment = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False, nullable=False)  # Internal notes not visible to customer
    is_system = Column(Boolean, default=False, nullable=False)  # System-generated comment
    
    # Author
    author_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # Null for customer comments
    author_name = Column(String(200), nullable=True)  # For customer comments
    author_email = Column(String(200), nullable=True)  # For customer comments
    
    # Status change
    status_change = Column(String(50), nullable=True)  # If this comment changed status
    
    # Relationships
    ticket = relationship("Ticket", back_populates="comments")
    author = relationship("User", foreign_keys=[author_id])
    attachments = relationship("TicketAttachment", back_populates="comment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TicketComment {self.id} on {self.ticket_id}>"


class TicketAttachment(Base, TimestampMixin):
    """Ticket attachment model"""
    __tablename__ = "ticket_attachments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String(36), ForeignKey("tickets.id"), nullable=False, index=True)
    comment_id = Column(String(36), ForeignKey("ticket_comments.id"), nullable=True, index=True)
    
    # File details
    filename = Column(String(500), nullable=False)
    file_path = Column(String(500), nullable=False)  # MinIO path
    file_size = Column(Integer, nullable=False)  # Size in bytes
    content_type = Column(String(100), nullable=True)
    
    # Relationships
    ticket = relationship("Ticket", back_populates="attachments")
    comment = relationship("TicketComment", back_populates="attachments")
    
    def __repr__(self):
        return f"<TicketAttachment {self.filename}>"


class TicketHistory(Base, TimestampMixin):
    """Ticket history/audit log"""
    __tablename__ = "ticket_history"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String(36), ForeignKey("tickets.id"), nullable=False, index=True)
    
    # Change details
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=False)
    
    # Who made the change
    changed_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    changed_by_name = Column(String(200), nullable=True)  # For system changes
    
    # Relationships
    ticket = relationship("Ticket", back_populates="history")
    changed_by = relationship("User", foreign_keys=[changed_by_id])
    
    def __repr__(self):
        return f"<TicketHistory {self.field_name} on {self.ticket_id}>"


class KnowledgeBaseArticle(Base, TimestampMixin):
    """Knowledge base article model"""
    __tablename__ = "knowledge_base_articles"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Article details
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    
    # Categorization
    category = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, nullable=True)  # Array of tag strings
    
    # Visibility
    is_published = Column(Boolean, default=False, nullable=False, index=True)
    is_featured = Column(Boolean, default=False, nullable=False)
    
    # Author
    author_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Metrics
    view_count = Column(Integer, default=0, nullable=False)
    helpful_count = Column(Integer, default=0, nullable=False)
    not_helpful_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant")
    author = relationship("User", foreign_keys=[author_id])
    
    def __repr__(self):
        return f"<KnowledgeBaseArticle {self.title}>"
    
    __table_args__ = (
        Index('idx_kb_tenant_published', 'tenant_id', 'is_published'),
        Index('idx_kb_category', 'tenant_id', 'category', 'is_published'),
    )


class SLAPolicy(Base, TimestampMixin):
    """Enhanced SLA policy model with comprehensive metrics"""
    __tablename__ = "sla_policies"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Policy details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    sla_level = Column(String(50), nullable=True)  # e.g., "Gold", "Silver", "Bronze", "24/7", "Business Hours"
    
    # Response Time SLAs (in hours)
    first_response_hours = Column(Integer, nullable=True)  # Target time for first response
    first_response_hours_urgent = Column(Integer, nullable=True)  # Override for urgent tickets
    first_response_hours_high = Column(Integer, nullable=True)  # Override for high priority
    first_response_hours_medium = Column(Integer, nullable=True)  # Override for medium priority
    first_response_hours_low = Column(Integer, nullable=True)  # Override for low priority
    
    # Resolution Time SLAs (in hours)
    resolution_hours = Column(Integer, nullable=True)  # Target time for resolution
    resolution_hours_urgent = Column(Integer, nullable=True)  # Override for urgent tickets
    resolution_hours_high = Column(Integer, nullable=True)  # Override for high priority
    resolution_hours_medium = Column(Integer, nullable=True)  # Override for medium priority
    resolution_hours_low = Column(Integer, nullable=True)  # Override for low priority
    
    # Availability/Uptime SLAs (percentage)
    uptime_target = Column(Integer, nullable=True)  # e.g., 99.9% stored as 9990 (99.90%)
    availability_hours = Column(String(50), nullable=True)  # e.g., "24/7", "Business Hours", "9-5 Mon-Fri"
    
    # Business Hours Configuration
    business_hours_start = Column(String(10), nullable=True)  # e.g., "09:00"
    business_hours_end = Column(String(10), nullable=True)  # e.g., "17:00"
    business_days = Column(JSON, nullable=True)  # e.g., ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    timezone = Column(String(50), default="Europe/London", nullable=False)
    
    # Escalation Rules
    escalation_warning_percent = Column(Integer, default=80, nullable=False)  # Warn at 80% of SLA time
    escalation_critical_percent = Column(Integer, default=95, nullable=False)  # Critical alert at 95%
    auto_escalate_on_breach = Column(Boolean, default=True, nullable=False)
    
    # Conditions for applying this SLA
    priority = Column(Enum(TicketPriority), nullable=True)  # Apply to specific priority (null = all)
    ticket_type = Column(Enum(TicketType), nullable=True)  # Apply to specific type (null = all)
    customer_ids = Column(JSON, nullable=True)  # Apply to specific customers (null = all)
    contract_type = Column(String(50), nullable=True)  # Apply to specific contract types
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_default = Column(Boolean, default=False, nullable=False)  # Default SLA for tenant
    
    # Relationships
    tenant = relationship("Tenant")
    
    def __repr__(self):
        return f"<SLAPolicy {self.name}>"
    
    __table_args__ = (
        Index('idx_sla_tenant_active', 'tenant_id', 'is_active'),
        Index('idx_sla_default', 'tenant_id', 'is_default'),
    )

