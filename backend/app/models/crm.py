#!/usr/bin/env python3
"""
CRM models for customers, contacts, and interactions
"""

from sqlalchemy import Column, String, Boolean, Text, JSON, ForeignKey, Integer, Enum, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid
from .base import Base, BaseModel


class CustomerStatus(enum.Enum):
    """
    Customer status enumeration
    
    IMPORTANT: These enum values MUST match the PostgreSQL enum type 'customerstatus' exactly.
    The database enum is case-sensitive and uses UPPERCASE values.
    
    Database enum values (PostgreSQL):
    - DISCOVERY, LEAD, PROSPECT, OPPORTUNITY, CUSTOMER, COLD_LEAD, INACTIVE, LOST (uppercase - CURRENT/ACTIVE)
    - Legacy values also exist: ACTIVE, CHURNED, customer, cold_lead, lost (lowercase - DO NOT USE)
    
    Customer Lifecycle Flow:
    DISCOVERY → LEAD → PROSPECT → OPPORTUNITY → CUSTOMER
    
    DISCOVERY: Companies identified via campaigns but not yet contacted (shown in Leads section)
    LEAD: First contact made, gathering information
    PROSPECT: Qualified and actively engaging
    OPPORTUNITY: Active deal with quote/proposal
    CUSTOMER: Won deal, paying customer
    
    To add new status values:
    1. Add the value to this enum with UPPERCASE string value
    2. Run: ALTER TYPE customerstatus ADD VALUE IF NOT EXISTS 'NEW_VALUE';
    3. Restart the backend container to pick up the changes
    
    The enum value (right side) is what gets stored in the database.
    Always use UPPERCASE to match PostgreSQL enum.
    """
    DISCOVERY = "DISCOVERY"          # Identified via campaign, not yet contacted
    LEAD = "LEAD"                    # First contact made, gathering information
    PROSPECT = "PROSPECT"            # Qualified lead, actively engaging
    OPPORTUNITY = "OPPORTUNITY"      # Active sales opportunity with quote/proposal
    CUSTOMER = "CUSTOMER"            # Active paying customer
    COLD_LEAD = "COLD_LEAD"         # Lead that went cold
    INACTIVE = "INACTIVE"            # Customer no longer active
    LOST = "LOST"                    # Lost to competitor or decided not to buy


class BusinessSector(enum.Enum):
    """Business sector enumeration"""
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    FINANCE = "finance"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    HOSPITALITY = "hospitality"
    GOVERNMENT = "government"
    OTHER = "other"


class BusinessSize(enum.Enum):
    """Business size enumeration"""
    MICRO = "micro"        # 1-9 employees
    SMALL = "small"        # 10-49 employees
    MEDIUM = "medium"      # 50-249 employees
    LARGE = "large"        # 250+ employees


class ContactRole(enum.Enum):
    """Contact role enumeration"""
    DECISION_MAKER = "decision_maker"
    INFLUENCER = "influencer"
    USER = "user"
    TECHNICAL_CONTACT = "technical_contact"
    OTHER = "other"


class Customer(BaseModel):
    """Customer model"""
    __tablename__ = "customers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Basic information
    company_name = Column(String(255), nullable=False, index=True)
    status = Column(Enum(CustomerStatus), default=CustomerStatus.LEAD, nullable=False)
    
    # Business details
    business_sector = Column(Enum(BusinessSector), nullable=True)
    business_size = Column(Enum(BusinessSize), nullable=True)
    description = Column(Text, nullable=True)
    
    # Contact information
    website = Column(String(500), nullable=True)
    main_email = Column(String(255), nullable=True)
    main_phone = Column(String(50), nullable=True)
    
    # Address information
    billing_address = Column(Text, nullable=True)
    billing_postcode = Column(String(20), nullable=True)
    shipping_address = Column(Text, nullable=True)
    shipping_postcode = Column(String(20), nullable=True)
    primary_address = Column(Text, nullable=True)
    
    # Company registration
    company_registration = Column(String(50), nullable=True)
    registration_confirmed = Column(Boolean, default=False)
    
    # AI analysis and external data
    ai_analysis_raw = Column(JSON, nullable=True)
    lead_score = Column(Integer, nullable=True)
    companies_house_data = Column(JSON, nullable=True)
    google_maps_data = Column(JSON, nullable=True)
    website_data = Column(JSON, nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    linkedin_data = Column(JSON, nullable=True)
    known_facts = Column(Text, nullable=True)  # User-provided facts to improve AI analysis
    
    # Address management
    excluded_addresses = Column(JSON, nullable=True)
    manual_addresses = Column(JSON, nullable=True)
    
    # Relationships
    contacts = relationship("Contact", back_populates="customer", cascade="all, delete-orphan")
    interactions = relationship("CustomerInteraction", back_populates="customer", cascade="all, delete-orphan")
    sales_activities = relationship("SalesActivity", back_populates="customer", cascade="all, delete-orphan")
    sales_notes = relationship("SalesNote", back_populates="customer", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Customer {self.company_name}>"


class Contact(BaseModel):
    """Contact model"""
    __tablename__ = "contacts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    
    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    job_title = Column(String(200), nullable=True)
    role = Column(Enum(ContactRole), default=ContactRole.OTHER, nullable=False)
    
    # Contact information
    email = Column(String(255), nullable=True)  # Primary email
    phone = Column(String(50), nullable=True)   # Primary phone
    emails = Column(JSON, nullable=True)  # Additional emails: [{"email": "...", "type": "work/personal", "is_primary": bool}]
    phones = Column(JSON, nullable=True)  # Additional phones: [{"number": "...", "type": "mobile/work/home", "is_primary": bool}]
    
    # Additional details
    notes = Column(Text, nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    customer = relationship("Customer", back_populates="contacts")
    
    def __repr__(self):
        return f"<Contact {self.first_name} {self.last_name}>"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class InteractionType(enum.Enum):
    """Interaction type enumeration"""
    EMAIL = "email"
    PHONE = "phone"
    MEETING = "meeting"
    NOTE = "note"
    QUOTE_SENT = "quote_sent"
    QUOTE_ACCEPTED = "quote_accepted"
    QUOTE_REJECTED = "quote_rejected"
    FOLLOW_UP = "follow_up"
    OTHER = "other"


class CustomerInteraction(BaseModel):
    """Customer interaction model"""
    __tablename__ = "customer_interactions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    contact_id = Column(String(36), ForeignKey("contacts.id"), nullable=True)
    
    # Interaction details
    interaction_type = Column(Enum(InteractionType), nullable=False)
    subject = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Follow-up
    follow_up_date = Column(DateTime(timezone=True), nullable=True)
    follow_up_completed = Column(Boolean, default=False)
    
    # Metadata
    duration_minutes = Column(Integer, nullable=True)
    outcome = Column(String(100), nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="interactions")
    contact = relationship("Contact")
    
    def __repr__(self):
        return f"<CustomerInteraction {self.interaction_type} - {self.subject}>"
