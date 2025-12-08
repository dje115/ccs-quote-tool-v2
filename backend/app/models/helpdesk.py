#!/usr/bin/env python3
"""
Helpdesk models for ticket management and customer service
"""

from sqlalchemy import Column, String, Boolean, Text, ForeignKey, DateTime, Integer, Enum, JSON, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
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


class NPAState(str, enum.Enum):
    """Next Point of Action state enumeration"""
    INVESTIGATION = "investigation"
    WAITING_CUSTOMER = "waiting_customer"
    WAITING_VENDOR = "waiting_vendor"
    WAITING_PARTS = "waiting_parts"
    SOLUTION = "solution"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    OTHER = "other"


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
    improved_description = Column(Text, nullable=True)  # AI-improved description (deprecated - use cleaned_description)
    cleaned_description = Column(Text, nullable=True)  # AI-cleaned professional version (customer-facing)
    description_ai_cleanup_status = Column(String(50), default="pending", nullable=True)  # AI cleanup status: pending, processing, completed, failed, skipped
    description_ai_cleanup_task_id = Column(String(100), nullable=True)  # Celery task ID for description AI cleanup
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
    merged_into_ticket_id = Column(String(36), ForeignKey("tickets.id"), nullable=True, index=True)  # If this ticket was merged into another
    
    # Metadata
    tags = Column(JSON, nullable=True)  # Array of tag strings
    custom_fields = Column(JSON, nullable=True)  # Custom field values
    internal_notes = Column(Text, nullable=True)  # Internal notes not visible to customer
    
    # Satisfaction
    customer_satisfaction_rating = Column(Integer, nullable=True)  # 1-5
    customer_feedback = Column(Text, nullable=True)
    
    # Next Point of Action (NPA) - Every ticket must have an NPA unless closed/resolved
    next_point_of_action = Column(Text, nullable=True)  # What needs to happen next (deprecated - use npa_cleaned_text)
    next_point_of_action_due_date = Column(DateTime(timezone=True), nullable=True)  # When NPA is due
    next_point_of_action_assigned_to_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # Who should complete NPA
    npa_last_updated_at = Column(DateTime(timezone=True), nullable=True)  # When NPA was last updated
    
    # Enhanced NPA fields
    npa_state = Column(
        PG_ENUM('investigation', 'waiting_customer', 'waiting_vendor', 'waiting_parts', 'solution', 'implementation', 'testing', 'documentation', 'other', name='npastate', create_type=False),
        default='investigation',
        nullable=True
    )  # State of the NPA
    npa_original_text = Column(Text, nullable=True)  # Original text as typed by agent
    npa_cleaned_text = Column(Text, nullable=True)  # AI-cleaned professional version (customer-facing)
    npa_date_override = Column(Boolean, default=False, nullable=False)  # Whether date was manually overridden
    npa_exclude_from_sla = Column(Boolean, default=False, nullable=False)  # Exclude from SLA calculations
    npa_ai_cleanup_status = Column(String(50), default="pending", nullable=True)  # AI cleanup status: pending, processing, completed, failed, skipped
    npa_ai_cleanup_task_id = Column(String(100), nullable=True)  # Celery task ID for AI cleanup
    
    # NPA Answers AI cleanup (for answers to questions)
    npa_answers_original_text = Column(Text, nullable=True)  # Original answers text as typed by agent
    npa_answers_cleaned_text = Column(Text, nullable=True)  # AI-cleaned professional version
    npa_answers_ai_cleanup_status = Column(String(50), default="pending", nullable=True)  # AI cleanup status
    npa_answers_ai_cleanup_task_id = Column(String(100), nullable=True)  # Celery task ID for answers AI cleanup
    
    # Relationships
    tenant = relationship("Tenant")
    customer = relationship("Customer")
    contact = relationship("Contact")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    npa_assigned_to = relationship("User", foreign_keys=[next_point_of_action_assigned_to_id])
    related_quote = relationship("Quote", foreign_keys=[related_quote_id])
    related_contract = relationship("SupportContract", foreign_keys=[related_contract_id])
    sla_policy = relationship("SLAPolicy", foreign_keys=[sla_policy_id])
    comments = relationship("TicketComment", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketComment.created_at")
    attachments = relationship("TicketAttachment", back_populates="ticket", cascade="all, delete-orphan")
    history = relationship("TicketHistory", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketHistory.created_at")
    npa_history = relationship("NPAHistory", back_populates="ticket", cascade="all, delete-orphan", order_by="NPAHistory.created_at")
    agent_chat = relationship("TicketAgentChat", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketAgentChat.created_at")
    outgoing_links = relationship("TicketLink", foreign_keys="TicketLink.source_ticket_id", back_populates="source_ticket", cascade="all, delete-orphan")
    incoming_links = relationship("TicketLink", foreign_keys="TicketLink.target_ticket_id", back_populates="target_ticket", cascade="all, delete-orphan")
    time_entries = relationship("TicketTimeEntry", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketTimeEntry.created_at.desc()")
    
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


class NPAHistory(Base, TimestampMixin):
    """NPA History - Complete history of all NPAs for a ticket (call history)"""
    __tablename__ = "npa_history"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String(36), ForeignKey("tickets.id"), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # NPA content
    npa_original_text = Column(Text, nullable=False)
    npa_cleaned_text = Column(Text, nullable=True)
    npa_state = Column(String(50), nullable=False, index=True)  # investigation, waiting_customer, solution, etc.
    
    # Assignment and dates
    assigned_to_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    date_override = Column(Boolean, default=False, nullable=False)
    
    # SLA exclusion
    exclude_from_sla = Column(Boolean, default=False, nullable=False)
    
    # AI cleanup status
    ai_cleanup_status = Column(String(50), default="pending", nullable=True)
    ai_cleanup_task_id = Column(String(100), nullable=True)
    
    # Answers to questions in this NPA
    answers_to_questions = Column(Text, nullable=True)  # Answers provided to questions asked in this NPA (original as typed)
    answers_cleaned_text = Column(Text, nullable=True)  # AI-cleaned professional version of answers
    answers_ai_cleanup_status = Column(String(50), default="pending", nullable=True)  # AI cleanup status: pending, processing, completed, failed, skipped
    answers_ai_cleanup_task_id = Column(String(100), nullable=True)  # Celery task ID for answers AI cleanup
    
    # Completion tracking
    completed_at = Column(DateTime(timezone=True), nullable=True, index=True)  # When this NPA was completed
    completed_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    completion_notes = Column(Text, nullable=True)  # Notes on how/why it was completed
    
    # Relationships
    ticket = relationship("Ticket", back_populates="npa_history")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    completed_by = relationship("User", foreign_keys=[completed_by_id])
    
    def __repr__(self):
        return f"<NPAHistory {self.npa_state} for ticket {self.ticket_id}>"


class TicketAgentChat(Base, TimestampMixin):
    """Agent chat messages for tickets - persistent chat history"""
    __tablename__ = "ticket_agent_chat"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String(36), ForeignKey("tickets.id"), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)  # Agent who sent/received
    
    # Message details
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    
    # AI task tracking
    ai_task_id = Column(String(100), nullable=True)  # Celery task ID for AI response
    ai_status = Column(String(50), default="pending", nullable=True)  # pending, processing, completed, failed
    ai_model = Column(String(100), nullable=True)  # Model used for response
    ai_usage = Column(JSON, nullable=True)  # Token usage info
    
    # Attachments and logs
    attachments = Column(JSON, nullable=True)  # [{filename, content, type}]
    log_files = Column(JSON, nullable=True)  # Array of log file contents
    
    # NPA and solution tracking
    linked_to_npa_id = Column(String(36), ForeignKey("npa_history.id"), nullable=True)  # If saved to NPA
    is_solution = Column(Boolean, default=False, nullable=False)  # If marked as solution
    solution_notes = Column(Text, nullable=True)  # Notes when marked as solution
    
    # Relationships
    ticket = relationship("Ticket", back_populates="agent_chat")
    user = relationship("User", foreign_keys=[user_id])
    linked_npa = relationship("NPAHistory", foreign_keys=[linked_to_npa_id])
    
    def __repr__(self):
        return f"<TicketAgentChat {self.role} on {self.ticket_id}>"
    
    __table_args__ = (
        Index('idx_chat_ticket_created', 'ticket_id', 'created_at'),
        Index('idx_chat_user', 'user_id', 'created_at'),
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


class TicketTemplate(Base, TimestampMixin):
    """Ticket template for common ticket types"""
    __tablename__ = "ticket_templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Template details
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True, index=True)  # Support, Billing, Technical, etc.
    
    # Template content
    subject_template = Column(Text, nullable=True)  # Subject line template
    description_template = Column(Text, nullable=True)  # Description template
    npa_template = Column(Text, nullable=True)  # Next Point of Action template
    
    # Metadata
    tags = Column(JSON, nullable=True)  # Array of tag strings
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Relationships
    tenant = relationship("Tenant")
    created_by = relationship("User", foreign_keys="TicketTemplate.created_by_id")
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    def __repr__(self):
        return f"<TicketTemplate {self.name}>"
    
    __table_args__ = (
        Index('idx_template_tenant_active', 'tenant_id', 'is_active'),
        Index('idx_template_category', 'category'),
    )


class QuickReplyTemplate(Base, TimestampMixin):
    """Quick reply template for common responses"""
    __tablename__ = "quick_reply_templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Template details
    name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # The reply text
    category = Column(String(100), nullable=True, index=True)  # Support, Billing, Technical, etc.
    
    # Sharing
    is_shared = Column(Boolean, default=False, nullable=False)  # Shared with team or personal
    
    # Relationships
    tenant = relationship("Tenant")
    created_by = relationship("User", foreign_keys="QuickReplyTemplate.created_by_id")
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    def __repr__(self):
        return f"<QuickReplyTemplate {self.name}>"
    
    __table_args__ = (
        Index('idx_quick_reply_tenant_shared', 'tenant_id', 'is_shared'),
        Index('idx_quick_reply_category', 'category'),
    )


class TicketMacro(Base, TimestampMixin):
    """Ticket macro for automating common workflows"""
    __tablename__ = "ticket_macros"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Macro details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    actions = Column(JSON, nullable=False)  # Array of actions to execute
    
    # Sharing
    is_shared = Column(Boolean, default=False, nullable=False)  # Shared with team or personal
    
    # Relationships
    tenant = relationship("Tenant")
    created_by = relationship("User", foreign_keys="TicketMacro.created_by_id")
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    def __repr__(self):
        return f"<TicketMacro {self.name}>"
    
    __table_args__ = (
        Index('idx_macro_tenant_shared', 'tenant_id', 'is_shared'),
    )


class TicketLink(Base, TimestampMixin):
    """Links between related tickets"""
    __tablename__ = "ticket_links"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Link details
    source_ticket_id = Column(String(36), ForeignKey("tickets.id"), nullable=False, index=True)
    target_ticket_id = Column(String(36), ForeignKey("tickets.id"), nullable=False, index=True)
    link_type = Column(String(50), nullable=False, default='related', index=True)  # 'related', 'duplicate', 'blocks', 'blocked_by', 'follows', 'followed_by'
    
    # Relationships
    tenant = relationship("Tenant")
    source_ticket = relationship("Ticket", foreign_keys="TicketLink.source_ticket_id", back_populates="outgoing_links")
    target_ticket = relationship("Ticket", foreign_keys="TicketLink.target_ticket_id", back_populates="incoming_links")
    created_by = relationship("User", foreign_keys="TicketLink.created_by_id")
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    def __repr__(self):
        return f"<TicketLink {self.source_ticket_id} -> {self.target_ticket_id} ({self.link_type})>"
    
    __table_args__ = (
        UniqueConstraint('source_ticket_id', 'target_ticket_id', 'link_type', name='uq_ticket_link'),
    )


class TicketTimeEntry(Base, TimestampMixin):
    """Time tracking entries for tickets"""
    __tablename__ = "ticket_time_entries"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    ticket_id = Column(String(36), ForeignKey("tickets.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Time entry details
    description = Column(Text, nullable=True)
    hours = Column(String(20), nullable=False)  # Store as string to handle decimal precision
    billable = Column(Boolean, default=False, nullable=False)
    activity_type = Column(String(50), nullable=True)  # 'work', 'research', 'communication', 'meeting', 'other'
    started_at = Column(DateTime(timezone=True), nullable=True, index=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant")
    ticket = relationship("Ticket", back_populates="time_entries")
    user = relationship("User", foreign_keys="TicketTimeEntry.user_id")
    
    def __repr__(self):
        return f"<TicketTimeEntry {self.hours}h on ticket {self.ticket_id}>"
    
    __table_args__ = (
        Index('idx_time_entry_ticket_user', 'ticket_id', 'user_id'),
    )

