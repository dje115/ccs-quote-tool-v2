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
    """Customer status enumeration"""
    LEAD = "lead"
    PROSPECT = "prospect"
    ACTIVE = "active"
    INACTIVE = "inactive"
    CHURNED = "churned"


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
    companies_house_data = Column(JSON, nullable=True)
    google_maps_data = Column(JSON, nullable=True)
    website_data = Column(JSON, nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    linkedin_data = Column(JSON, nullable=True)
    
    # Address management
    excluded_addresses = Column(JSON, nullable=True)
    manual_addresses = Column(JSON, nullable=True)
    
    # Relationships
    contacts = relationship("Contact", back_populates="customer", cascade="all, delete-orphan")
    interactions = relationship("CustomerInteraction", back_populates="customer", cascade="all, delete-orphan")
    
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
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
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
