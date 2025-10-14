#!/usr/bin/env python3
"""
Sales activity tracking models

IMPORTANT: These models track all sales interactions (calls, meetings, notes)
to provide comprehensive sales history and enable AI-powered sales assistance.
"""

from sqlalchemy import Column, String, Text, JSON, ForeignKey, Integer, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid
from .base import Base, TimestampMixin


class ActivityType(enum.Enum):
    """Type of sales activity"""
    CALL = "call"
    MEETING = "meeting"
    EMAIL = "email"
    NOTE = "note"
    TASK = "task"


class ActivityOutcome(enum.Enum):
    """Outcome of a sales activity"""
    SUCCESSFUL = "successful"
    NO_ANSWER = "no_answer"
    VOICEMAIL = "voicemail"
    FOLLOW_UP_REQUIRED = "follow_up_required"
    NOT_INTERESTED = "not_interested"
    MEETING_SCHEDULED = "meeting_scheduled"
    QUOTE_REQUESTED = "quote_requested"
    WON = "won"
    LOST = "lost"


class SalesActivity(Base, TimestampMixin):
    """
    Sales activity tracking
    
    Tracks all interactions with customers including calls, meetings, emails, and notes.
    This provides a complete audit trail and enables AI to understand the sales context.
    
    IMPORTANT: The 'notes' field should capture key details from interactions:
    - What was discussed
    - Customer pain points mentioned
    - Objections raised
    - Next steps agreed
    - Action items
    """
    __tablename__ = "sales_activities"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    contact_id = Column(String(36), ForeignKey("contacts.id"), nullable=True, index=True)  # Optional: which contact was involved
    
    # Activity details
    activity_type = Column(Enum(ActivityType), nullable=False)
    activity_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    duration_minutes = Column(Integer, nullable=True)  # For calls/meetings
    
    # Content
    subject = Column(String(255), nullable=True)  # e.g., "Follow-up call regarding structured cabling quote"
    notes = Column(Text, nullable=False)  # Original notes from user
    notes_cleaned = Column(Text, nullable=True)  # AI-cleaned/enhanced version
    ai_suggested_action = Column(Text, nullable=True)  # AI-suggested next action
    outcome = Column(Enum(ActivityOutcome), nullable=True)
    
    # AI assistance used
    ai_suggestions_used = Column(JSON, default=list)  # Track which AI suggestions were used
    ai_context = Column(JSON, default=dict)  # Store AI context that was provided
    ai_processing_date = Column(DateTime(timezone=True), nullable=True)  # When AI processed this
    
    # Follow-up
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime(timezone=True), nullable=True)
    follow_up_notes = Column(Text, nullable=True)
    
    # Additional metadata
    additional_data = Column(JSON, default=dict)  # Additional data (e.g., call recording URL, meeting link)
    
    # Relationships
    customer = relationship("Customer", back_populates="sales_activities")
    user = relationship("User")
    contact = relationship("Contact")
    
    def __repr__(self):
        return f"<SalesActivity {self.activity_type.value} for customer {self.customer_id}>"


class SalesNote(Base, TimestampMixin):
    """
    Quick sales notes
    
    Lightweight model for quick notes that don't fit into structured activities.
    Use this for:
    - Quick observations
    - Reminders
    - Strategic notes
    - Competitor intel
    """
    __tablename__ = "sales_notes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Note content
    note = Column(Text, nullable=False)
    is_important = Column(Boolean, default=False)  # Pin important notes
    
    # Relationships
    customer = relationship("Customer", back_populates="sales_notes")
    user = relationship("User")
    
    def __repr__(self):
        return f"<SalesNote for customer {self.customer_id}>"

