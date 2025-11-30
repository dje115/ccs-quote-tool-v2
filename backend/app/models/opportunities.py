#!/usr/bin/env python3
"""
Opportunity models for CRM pipeline management
"""

from sqlalchemy import Column, String, Boolean, Text, JSON, ForeignKey, Integer, Enum, DateTime, Float, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid
from .base import Base, BaseModel


class OpportunityStage(enum.Enum):
    """Opportunity pipeline stage enumeration"""
    QUALIFIED = "qualified"
    SCOPING = "scoping"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    VERBAL_YES = "verbal_yes"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class Opportunity(BaseModel):
    """Opportunity model - represents sales opportunities with pipeline stages
    
    Opportunities track deals through the sales pipeline from qualification to close.
    They can be linked to quotes, support contracts, and have attachments/notes.
    """
    __tablename__ = "opportunities"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Basic information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Pipeline stage
    stage = Column(Enum(OpportunityStage), default=OpportunityStage.QUALIFIED, nullable=False, index=True)
    
    # Deal metrics
    conversion_probability = Column(Integer, default=20)  # 0-100 percentage
    potential_deal_date = Column(DateTime(timezone=True), nullable=True)  # Expected close date
    estimated_value = Column(Numeric(10, 2), nullable=True)  # Estimated deal value
    
    # Related entities (stored as JSON arrays of IDs)
    quote_ids = Column(JSON, nullable=True)  # Array of quote IDs linked to this opportunity
    support_contract_ids = Column(JSON, nullable=True)  # Array of support contract IDs
    
    # Attachments and notes
    attachments = Column(JSON, nullable=True)  # Array of file references: [{"name": "...", "url": "...", "uploaded_at": "..."}]
    notes = Column(Text, nullable=True)
    
    # Recurring quote schedule (for subscription/recurring deals)
    recurring_quote_schedule = Column(JSON, nullable=True)  # {"frequency": "monthly|quarterly|annually", "start_date": "...", "end_date": "..."}
    
    # User tracking
    created_by = Column(String(36), nullable=True)  # User ID who created the opportunity
    updated_by = Column(String(36), nullable=True)  # User ID who last updated the opportunity
    
    # Relationships
    customer = relationship("Customer", backref="opportunities")
    
    def __repr__(self):
        return f"<Opportunity {self.title} - {self.stage.value}>"

